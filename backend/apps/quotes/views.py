from rest_framework import viewsets, permissions, decorators
from rest_framework.response import Response
from .models import Quote, QuoteItem, CompetitiveSheet
from .serializers import QuoteSerializer, CompetitiveSheetSerializer

class QuoteViewSet(viewsets.ModelViewSet):
    serializer_class = QuoteSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        request_id = self.request.query_params.get('request_id')
        if request_id:
            return Quote.objects.filter(request_id=request_id)
        return Quote.objects.filter(request__customer=self.request.user)

    @decorators.action(detail=False, methods=['get'])
    def competitive_sheet(self, request):
        request_id = request.query_params.get('request_id')
        if not request_id:
            return Response({'error': 'request_id required'}, status=400)

        quotes = Quote.objects.filter(request_id=request_id, status__in=['received', 'valid'])
        items = []
        from decimal import Decimal
        for quote in quotes:
            total = sum(qi.price * qi.request_item.quantity for qi in quote.items.all())
            delivery = quote.delivery_cost or Decimal('0')
            items.append({
                'supplier_id': quote.supplier_id,
                'supplier_name': quote.supplier.name,
                'materials_total': float(total),
                'delivery': float(delivery),
                'grand_total': float(total + delivery),
                'payment_terms': quote.payment_terms,
                'delivery_time': quote.delivery_time,
                'valid_until': quote.valid_until,
            })

        best = min(items, key=lambda x: x['grand_total']) if items else None

        cs, _ = CompetitiveSheet.objects.update_or_create(
            request_id=request_id,
            defaults={'total_amount': best['grand_total'] if best else None,
                      'best_supplier_id': best['supplier_id'] if best else None}
        )

        return Response({'suppliers': sorted(items, key=lambda x: x['grand_total']),
                        'best': best, 'total_quotes': len(items)})


# === Public API (no auth) ===

from rest_framework import status as http_status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from apps.requests.models import RequestItem
from .models import RfqInvitation

@api_view(["GET", "POST"])
@permission_classes([AllowAny])
def public_quote(request, token):
    try:
        invitation = RfqInvitation.objects.select_related("request", "supplier").get(quote_token=token)
    except RfqInvitation.DoesNotExist:
        return Response({"error": "Invalid or expired link"}, status=http_status.HTTP_404_NOT_FOUND)

    req = invitation.request

    if request.method == "GET":
        items = req.items.filter(is_confirmed=True)
        items_data = [{
            "id": item.id, "name": item.name,
            "quantity": float(item.quantity),
            "unit": item.unit.short_name if item.unit else "",
            "category": item.category.name if item.category else "",
            "brand": item.brand, "spec": item.spec,
        } for item in items]

        existing = None
        try:
            quote = Quote.objects.get(request=req, supplier=invitation.supplier, invitation=invitation)
            existing = {
                "id": quote.id, "status": quote.status,
                "delivery_cost": float(quote.delivery_cost) if quote.delivery_cost else None,
                "delivery_time": quote.delivery_time, "payment_terms": quote.payment_terms,
                "comment": quote.comment,
                "items": [{"request_item_id": qi.request_item_id, "price": float(qi.price),
                           "is_analog": qi.is_analog, "brand": qi.brand} for qi in quote.items.all()],
            }
        except Quote.DoesNotExist:
            pass

        return Response({
            "request_code": req.code, "supplier_name": invitation.supplier.name,
            "delivery_address": req.address.address if req.address else "",
            "items": items_data, "existing_quote": existing, "quote_token": token,
        })

    elif request.method == "POST":
        data = request.data
        quote, created = Quote.objects.update_or_create(
            request=req, supplier=invitation.supplier, invitation=invitation,
            defaults={
                "status": "received", "delivery_cost": data.get("delivery_cost"),
                "delivery_time": data.get("delivery_time", ""),
                "payment_terms": data.get("payment_terms", ""),
                "comment": data.get("comment", ""),
            },
        )
        existing_ids = set(quote.items.values_list("id", flat=True))
        received_ids = set()
        for item_data in data.get("items", []):
            request_item_id = item_data.get("request_item_id")
            if not request_item_id:
                continue
            try:
                req_item = RequestItem.objects.get(id=request_item_id, request=req)
            except RequestItem.DoesNotExist:
                continue
            qi, _ = QuoteItem.objects.update_or_create(
                quote=quote, request_item=req_item,
                defaults={"price": item_data.get("price", 0),
                          "is_analog": item_data.get("is_analog", False),
                          "brand": item_data.get("brand", "")},
            )
            received_ids.add(qi.id)
        to_delete = existing_ids - received_ids
        if to_delete:
            QuoteItem.objects.filter(id__in=to_delete).delete()
        invitation.status = "replied"
        invitation.save(update_fields=["status"])
        return Response({"status": "ok", "quote_id": quote.id, "message": "Quote submitted successfully"})
