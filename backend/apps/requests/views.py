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
        return Response(RequestSerializer(req).data)

    @decorators.action(detail=True, methods=['post'])
    def confirm(self, request, pk=None):
        req = self.get_object()
        req.status = 'confirmed'
        req.save(update_fields=['status'])
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
