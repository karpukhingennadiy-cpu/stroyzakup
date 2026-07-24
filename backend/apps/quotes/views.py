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
