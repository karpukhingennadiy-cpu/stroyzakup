# backend/apps/requests/views.py
from rest_framework import viewsets, status, decorators, permissions
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from .models import Request, RequestItem
from .serializers import (
    RequestSerializer, RequestCreateSerializer,
    ItemConfirmSerializer, RequestItemSerializer,
)
from .services.parser import parse_material_list
import secrets
import string


def _generate_code(length=6):
    chars = string.ascii_uppercase + string.digits
    chars = chars.translate(str.maketrans("", "", "0O1IL"))
    while True:
        code = "".join(secrets.choice(chars) for _ in range(length))
        if not Request.objects.filter(code=code).exists():
            return code


class RequestViewSet(viewsets.ModelViewSet):
    serializer_class = RequestSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return (
            Request.objects.filter(customer=self.request.user)
            .select_related("address", "customer")
            .prefetch_related("items__category", "items__unit")
            .order_by("-created_at")
        )

    def get_serializer_class(self):
        if self.action == "create":
            return RequestCreateSerializer
        return RequestSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return Response(
            RequestSerializer(serializer.instance).data,
            status=status.HTTP_201_CREATED,
        )

    def perform_create(self, serializer):
        code = _generate_code()
        serializer.save(customer=self.request.user, code=code)

    @decorators.action(detail=True, methods=["post"])
    def parse(self, request, pk=None):
        req = self.get_object()
        if req.status not in ("draft", "parsing"):
            return Response(
                {"error": "Cannot parse in current status"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        req.status = "parsing"
        req.save(update_fields=["status"])

        # Sync-only in dev: no Celery async, immediate result
        result = parse_material_list(req)
        if "error" in result:
            # FIX-K1: 'parse_failed' → 'draft' (такого статуса нет в модели)
            req.status = "draft"
            req.save(update_fields=["status"])
            return Response({"error": result["error"]}, status=422)
        req.status = "confirmed"
        req.save(update_fields=["status"])
        return Response(RequestSerializer(req).data)

    @decorators.action(detail=True, methods=["post"])
    def confirm(self, request, pk=None):
        req = self.get_object()
        req.status = "confirmed"
        req.save(update_fields=["status"])

        if req.address and req.address.latitude and req.address.longitude:
            # Sync-only in dev
            from .services.matcher import match_suppliers
            matches = match_suppliers(req)
            req.status = "matched"
            req.save(update_fields=["status"])
            return Response(
                {
                    "status": "matched",
                    "suppliers": matches,
                    "count": len(matches),
                    "request": RequestSerializer(req).data,
                }
            )

        # FIX-M1: понятное сообщение, если адреса нет
        return Response(
            {
                "status": "confirmed",
                "message": "Заявка подтверждена. Укажите адрес доставки, чтобы начать подбор поставщиков.",
                "request": RequestSerializer(req).data,
            }
        )

    @decorators.action(detail=True, methods=["post"])
    def update_item(self, request, pk=None):
        item = get_object_or_404(
            RequestItem, id=request.data.get("item_id"), request_id=pk
        )
        serializer = ItemConfirmSerializer(item, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    @decorators.action(detail=True, methods=["get"])
    def items(self, request, pk=None):
        req = self.get_object()
        items = req.items.all()
        return Response(RequestItemSerializer(items, many=True).data)

    @decorators.action(detail=True, methods=["post"])
    def match_suppliers(self, request, pk=None):
        req = self.get_object()
        limit = request.data.get("limit", 20)
        if req.status not in ("parsed", "confirmed", "matched", "matching", "parsing", "draft", "rfq_sent", "rfq_failed"):
            return Response(
                {"error": "Cannot match in current status"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        req.status = "matching"
        req.save(update_fields=["status"])

        # Sync-only in dev: no Celery async, immediate result
        from .services.matcher import match_suppliers
        matches = match_suppliers(req, limit)
        req.status = "matched"
        req.save(update_fields=["status"])
        return Response(
            {
                "status": "matched",
                "suppliers": matches,
                "count": len(matches),
                "request": RequestSerializer(req).data,
            }
        )

    @decorators.action(detail=True, methods=["post"])
    def send_rfq(self, request, pk=None):
        req = self.get_object()
        supplier_ids = request.data.get("supplier_ids", [])
        if not supplier_ids:
            return Response(
                {"error": "supplier_ids required"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if req.status not in ("matched", "rfq_sent", "matching"):
            return Response(
                {"error": "Cannot send RFQ in current status"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Sync-only in dev: no Celery async, immediate result
        from .services.send_rfq import send_rfq_to_suppliers
        results = send_rfq_to_suppliers(req, supplier_ids)
        # FIX-K2: статус не обновлялся при синхронном фолбэке
        req.status = "rfq_sent"
        req.save(update_fields=["status"])
        return Response({"status": req.status, "results": results})