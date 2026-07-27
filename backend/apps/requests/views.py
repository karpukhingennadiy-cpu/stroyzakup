from rest_framework import viewsets, status, decorators, permissions
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from .models import Request, RequestItem
from .serializers import RequestSerializer, RequestCreateSerializer, ItemConfirmSerializer
from rest_framework import status
from .services.parser import parse_material_list
import secrets, string

def _generate_code(length=6):
    chars = string.ascii_uppercase + string.digits
    chars = chars.translate(str.maketrans('', '', '0O1IL'))
    return ''.join(secrets.choice(chars) for _ in range(length))

class RequestViewSet(viewsets.ModelViewSet):
    serializer_class = RequestSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Request.objects.filter(customer=self.request.user).order_by('-created_at')

    def get_serializer_class(self):
        if self.action == 'create':
            return RequestCreateSerializer
        return RequestSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return Response(RequestSerializer(serializer.instance).data, status=status.HTTP_201_CREATED)

    def perform_create(self, serializer):
        code = _generate_code()
        while Request.objects.filter(code=code).exists():
            code = _generate_code()
        serializer.save(customer=self.request.user, code=code)

    @decorators.action(detail=True, methods=['post'])
    def parse(self, request, pk=None):
        req = self.get_object()
        if req.status not in ('draft', 'parsing'):
            return Response({'error': 'Cannot parse in current status'}, status=400)
        req.status = 'parsing'
        req.save(update_fields=['status'])
        result = parse_material_list(req)
        req.refresh_from_db()
        response_data = RequestSerializer(req).data
        response_data['clarifications'] = result.get('clarifications', [])
        return Response(response_data)

    @decorators.action(detail=True, methods=['post'])
    def confirm(self, request, pk=None):
        req = self.get_object()
        req.status = 'confirmed'
        req.save(update_fields=['status'])
        # Auto-match suppliers if delivery address exists
        if req.address and req.address.latitude and req.address.longitude:
            from .services.matcher import match_suppliers
            matches = match_suppliers(req)
            req.status = 'matched'
            req.save(update_fields=['status'])
            return Response({
                'status': 'matched',
                'suppliers': matches,
                'count': len(matches),
                'request': RequestSerializer(req).data,
            })
        return Response(RequestSerializer(req).data)

    @decorators.action(detail=True, methods=['post'])
    def update_item(self, request, pk=None):
        item = get_object_or_404(RequestItem, id=request.data.get('item_id'), request_id=pk)
        serializer = ItemConfirmSerializer(item, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    @decorators.action(detail=True, methods=['get'])
    def items(self, request, pk=None):
        req = self.get_object()
        items = req.items.all()
        from .serializers import RequestItemSerializer
        return Response(RequestItemSerializer(items, many=True).data)
    @decorators.action(detail=True, methods=["post"])
    def match_suppliers(self, request, pk=None):
        """Score and rank suppliers for this request. Returns top 20 with scores.
        Also discovers new suppliers via web search."""
        from .services.matcher import match_suppliers
        from .services.websearch import discover_suppliers_for_request
        req = self.get_object()

        # Discover new suppliers from web (async-like, don't block on failure)
        try:
            new_count = discover_suppliers_for_request(req)
            if new_count:
                print(f"Discovered {new_count} new suppliers via web search")
        except Exception as e:
            print(f"Web search skipped: {e}")
        if req.status not in ("draft", "parsing", "confirmed", "matching", "matched"):
            return Response(
                {"error": "Cannot match in current status. Need: draft/parsing/confirmed/matching/matched"},
                status=400,
            )
        limit = int(request.data.get("limit", 20))
        results = match_suppliers(req, limit=limit)
        req.status = "matched"
        req.save(update_fields=["status"])
        return Response({
            "request_id": req.id,
            "request_code": req.code,
            "suppliers": results,
            "count": len(results),
        })

    @decorators.action(detail=True, methods=["post"])
    def send_rfq(self, request, pk=None):
        from .send_rfq import send_rfq_to_suppliers
        req = self.get_object()
        if req.status not in ("draft", "parsing", "confirmed", "matching", "matched", "rfq_sent"):
            return Response({"error": "Cannot send RFQ in current status"}, status=400)
        supplier_ids = request.data.get("supplier_ids")
        if not supplier_ids:
            return Response(
                {"error": "supplier_ids required. Use match_suppliers first to select suppliers."},
                status=400,
            )
        results = send_rfq_to_suppliers(req, supplier_ids)
        return Response({"sent": len([r for r in results if r["status"] == "sent"]), "results": results})

