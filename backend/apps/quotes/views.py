from rest_framework.decorators import throttle_classes
from rest_framework import viewsets, permissions, decorators
from rest_framework.response import Response
from .models import Quote, QuoteItem, CompetitiveSheet
from .serializers import QuoteSerializer, CompetitiveSheetSerializer

class QuoteViewSet(viewsets.ModelViewSet):
    serializer_class = QuoteSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        # IDOR fix: a quote may only be attached to a request owned by the caller
        from rest_framework.exceptions import NotFound
        from apps.requests.models import Request as ReqModel
        req = serializer.validated_data.get("request")
        if req is not None and not ReqModel.objects.filter(
                id=req.id, customer=self.request.user).exists():
            raise NotFound({"error": "Request not found"})
        serializer.save()

    def get_queryset(self):
        # IDOR fix: always scope to the authenticated customer's requests
        qs = Quote.objects.filter(request__customer=self.request.user)
        request_id = self.request.query_params.get('request_id')
        if request_id:
            qs = qs.filter(request_id=request_id)
        return qs

    @decorators.action(detail=False, methods=['get'])
    def competitive_sheet(self, request):
        request_id = request.query_params.get('request_id')
        if not request_id:
            return Response({'error': 'request_id required'}, status=400)

        # IDOR fix: only the request owner may see its competitive sheet
        from apps.requests.models import Request as ReqModel
        if not ReqModel.objects.filter(id=request_id, customer=request.user).exists():
            return Response({'error': 'Request not found'}, status=404)

        quotes = Quote.objects.filter(
            request_id=request_id, request__customer=request.user,
            status__in=['received', 'valid'],
        ).select_related('supplier').prefetch_related('items__request_item')
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

    @decorators.action(detail=False, methods=['post'])
    def select_winner(self, request):
        """G2: выбор победителя — переводит Quote в selected, Request в ready."""
        quote_id = request.data.get("quote_id")
        if not quote_id:
            return Response({"error": "quote_id required"}, status=400)

        # IDOR fix: scope quote to the authenticated customer's requests
        try:
            quote = Quote.objects.select_related("request").get(
                id=quote_id, request__customer=request.user,
            )
        except (Quote.DoesNotExist, ValueError):
            return Response({"error": "Quote not found"}, status=404)

        req = quote.request
        if req.status not in ("collecting_quotes", "matched", "rfq_sent", "ready"):
            return Response(
                {"error": f"Cannot select winner in current request status: {req.status}"},
                status=400,
            )

        # Mark selected quote
        Quote.objects.filter(request=req).update(status="rejected")
        quote.status = "selected"
        quote.save(update_fields=["status"])

        # Move request to ready
        req.status = "ready"
        req.save(update_fields=["status"])

        return Response({
            "status": "ready",
            "request": {"id": req.id, "code": req.code, "status": req.status},
            "selected_quote": QuoteSerializer(quote).data,
        })

    def _get_owned_request(self, request):
        """Fetch the request scoped to the caller or return (None, Response)."""
        from apps.requests.models import Request as ReqModel
        request_id = request.query_params.get('request_id')
        if not request_id:
            return None, Response({'error': 'request_id required'}, status=400)
        try:
            req = ReqModel.objects.get(id=request_id, customer=request.user)
        except (ReqModel.DoesNotExist, ValueError):
            return None, Response({'error': 'Request not found'}, status=404)
        return req, None

    @decorators.action(detail=False, methods=['get'])
    def competitive_sheet_xlsx(self, request):
        """P1: download the competitive sheet as .xlsx (best offer highlighted)."""
        req, error = self._get_owned_request(request)
        if error:
            return error
        from django.http import HttpResponse
        from .exporters import build_competitive_sheet_xlsx
        payload = build_competitive_sheet_xlsx(req)
        response = HttpResponse(
            payload,
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        )
        response['Content-Disposition'] = (
            f'attachment; filename="competitive_sheet_RFQ-{req.code}.xlsx"')
        return response

    @decorators.action(detail=False, methods=['get'])
    def winner_protocol_pdf(self, request):
        """P1: download the winner-selection protocol as .pdf."""
        req, error = self._get_owned_request(request)
        if error:
            return error
        from django.http import HttpResponse
        from .exporters import build_winner_protocol_pdf
        payload = build_winner_protocol_pdf(req)
        response = HttpResponse(payload, content_type='application/pdf')
        response['Content-Disposition'] = (
            f'attachment; filename="winner_protocol_RFQ-{req.code}.pdf"')
        return response


# === Public API (no auth) ===

from rest_framework import status as http_status
from rest_framework.throttling import AnonRateThrottle
from rest_framework.decorators import api_view, permission_classes, throttle_classes
from rest_framework.permissions import AllowAny
from apps.requests.models import RequestItem
from .models import RfqInvitation

class PublicQuoteThrottle(AnonRateThrottle):
    rate = "30/minute"


@api_view(["GET", "POST"])
@throttle_classes([PublicQuoteThrottle])
@permission_classes([AllowAny])
def public_quote(request, token):
    try:
        invitation = RfqInvitation.objects.select_related("request", "supplier").get(quote_token=token)
    except RfqInvitation.DoesNotExist:
        return Response({"error": "Invalid or expired link"}, status=http_status.HTTP_404_NOT_FOUND)

    req = invitation.request

    if request.method == "GET":
        items = req.items.filter(is_confirmed=True)
        if not items.exists():
            # Fallback: unconfirmed items (low-confidence parse) — better than empty form
            items = req.items.all()
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
        # Validation: at least one item, all prices strictly positive
        items_payload = data.get("items") or []
        if not items_payload:
            return Response({"error": "items required"}, status=http_status.HTTP_400_BAD_REQUEST)
        for item_data in items_payload:
            try:
                price = float(item_data.get("price", 0))
            except (TypeError, ValueError):
                return Response({"error": "price must be a number"}, status=http_status.HTTP_400_BAD_REQUEST)
            if price <= 0:
                return Response({"error": "price must be positive"}, status=http_status.HTTP_400_BAD_REQUEST)
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
        # B7: notify the customer about the received quote
        try:
            from apps.emails.services import notify_customer_quote_received
            notify_customer_quote_received(quote)
        except Exception:
            import logging
            logging.getLogger(__name__).exception("Customer notification failed")
        return Response({"status": "ok", "quote_id": quote.id, "message": "Quote submitted successfully"})
