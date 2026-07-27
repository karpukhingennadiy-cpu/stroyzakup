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
        return Request.objects.filter(customer=self.request.user)            .select_related("address", "customer")            .prefetch_related("items__category", "items__unit").order_by('-created_at')

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
        try:
            from .tasks import parse_request_task
            parse_request_task.delay(req.id)
        except Exception:
            # Fallback: run synchronously
            result = parse_material_list(req)
            if 'error' in result:
                req.status = 'parse_failed'
                req.save(update_fields=['status'])
                return Response({'error': result['error']}, status=422)
            req.status = 'parsed'
            req.save(update_fields=['status'])
        return Response({
            'status': 'accepted',
            'message': 'Parsing started',
            'request_id': req.id,
        }, status=202)

    @decorators.action(detail=True, methods=['post'])
    def confirm(self, request, pk=None):
        req = self.get_object()
        req.status = 'confirmed'
        req.save(update_fields=['status'])
        # Auto-match suppliers if delivery address exists
        if req.address and req.address.latitude and req.address.longitude:
            try:
                from .tasks import match_suppliers_task
                match_suppliers_task.delay(req.id)
            except Exception:
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
        req = self.get_object()
        limit = request.data.get('limit', 20)
        if req.status not in ('parsed', 'confirmed', 'matched', 'matching'):
            return Response({'error': 'Cannot match in current status'}, status=400)
        req.status = "matching"
        req.save(update_fields=["status"])
        try:
            from .tasks import match_suppliers_task
            match_suppliers_task.delay(req.id, limit)
        except Exception:
            from .services.matcher import match_suppliers
            matches = match_suppliers(req)
            req.status = "matched"
            req.save(update_fields=["status"])
            return Response({
                'status': 'matched',
                'suppliers': matches,
                'count': len(matches),
                'request': RequestSerializer(req).data,
            })
        return Response({
            'status': 'accepted',
            'message': 'Matching started',
            'request_id': req.id,
        }, status=202)

    @decorators.action(detail=True, methods=["post"])
    def send_rfq(self, request, pk=None):
        req = self.get_object()
        supplier_ids = request.data.get('supplier_ids', [])
        if not supplier_ids:
            return Response({'error': 'supplier_ids required'}, status=400)
        if req.status not in ('matched', 'rfq_sent'):
            return Response({'error': 'Cannot send RFQ in current status'}, status=400)
        try:
            from .tasks import send_rfq_task
            send_rfq_task.delay(req.id, supplier_ids)
        except Exception:
            from .send_rfq import send_rfq_to_suppliers
            results = send_rfq_to_suppliers(req, supplier_ids)
            return Response({'status': req.status, 'results': results})
        return Response({
            'status': 'accepted',
            'message': f'RFQ sending started for {len(supplier_ids)} suppliers',
            'request_id': req.id,
        }, status=202)
