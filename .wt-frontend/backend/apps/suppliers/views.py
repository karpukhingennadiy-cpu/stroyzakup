from rest_framework import viewsets, permissions, decorators, status
from rest_framework.response import Response
from .models import Supplier, SupplierAddress, SupplierCategory
from .serializers import SupplierSerializer, SupplierListSerializer
import math

class IsStaff(permissions.BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.is_staff)

class SupplierViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        qs = Supplier.objects.filter(is_active=True).prefetch_related('addresses')
        city = self.request.query_params.get('city')
        category = self.request.query_params.get('category')
        if city:
            qs = qs.filter(addresses__city__icontains=city)
        if category:
            qs = qs.filter(supplier_categories__category_id=category)
        search = self.request.query_params.get('search')
        if search:
            qs = qs.filter(name__icontains=search)
        moderation = self.request.query_params.get('moderation_status')
        if moderation:
            qs = qs.filter(moderation_status=moderation)
        return qs.distinct()

    def get_serializer_class(self):
        if self.action == 'list':
            return SupplierListSerializer
        return SupplierSerializer

    def perform_create(self, serializer):
        # B5: manual add -> enrich catalog + geocode address best-effort
        supplier = serializer.save()
        self._enrich_supplier(supplier)

    def _enrich_supplier(self, supplier):
        import logging
        logger = logging.getLogger(__name__)
        try:
            from .services import fill_supplier_catalog
            fill_supplier_catalog(supplier)
        except Exception:
            logger.exception("Catalog fill failed for supplier %s", supplier.id)
        # Geocode addresses that have no coordinates yet
        for addr in supplier.addresses.filter(latitude__isnull=True):
            try:
                from apps.requests.services.geocoder import geocode
                result = geocode(addr.address)
                if result:
                    addr.latitude, addr.longitude, addr.city, _ = result
                    addr.save(update_fields=["latitude", "longitude", "city"])
            except Exception:
                logger.exception("Geocoding failed for address %s", addr.id)

    @decorators.action(detail=False, methods=['get'])
    def categories(self, request):
        """List all material categories (used by the manual-add form, B5)."""
        from apps.requests.models import Category
        data = [{"id": c.id, "name": c.name, "slug": c.slug}
                for c in Category.objects.filter(is_active=True).order_by("name")]
        return Response(data)

    @decorators.action(detail=True, methods=['post'], permission_classes=[IsStaff])
    def moderate(self, request, pk=None):
        """B4: staff-only moderation: {"status": "verified"|"rejected"|"unverified"}"""
        supplier = self.get_object()
        new_status = request.data.get('status')
        allowed = {'verified', 'rejected', 'unverified'}
        if new_status not in allowed:
            return Response({'error': f'status must be one of {sorted(allowed)}'},
                            status=status.HTTP_400_BAD_REQUEST)
        supplier.moderation_status = new_status
        supplier.save(update_fields=['moderation_status'])
        return Response({'id': supplier.id, 'moderation_status': supplier.moderation_status})

    @decorators.action(detail=False, methods=['post'], permission_classes=[IsStaff])
    def bulk_verify(self, request):
        """B4: bulk moderation: {"ids": [...], "status": "verified"}"""
        ids = request.data.get('ids') or []
        new_status = request.data.get('status', 'verified')
        if not ids:
            return Response({'error': 'ids required'}, status=status.HTTP_400_BAD_REQUEST)
        if new_status not in {'verified', 'rejected', 'unverified'}:
            return Response({'error': 'invalid status'}, status=status.HTTP_400_BAD_REQUEST)
        updated = Supplier.objects.filter(id__in=ids).update(moderation_status=new_status)
        return Response({'updated': updated, 'moderation_status': new_status})

    @decorators.action(detail=False, methods=['get'])
    def search_radius(self, request):
        lat = float(request.query_params.get('lat', 0))
        lon = float(request.query_params.get('lon', 0))
        radius_km = float(request.query_params.get('radius', 150))
        category = request.query_params.get('category')

        suppliers = Supplier.objects.filter(is_active=True, addresses__is_active=True)
        if category:
            suppliers = suppliers.filter(supplier_categories__category_id=category)

        results = []
        for s in suppliers.prefetch_related('addresses', 'supplier_categories'):
            for addr in s.addresses.all():
                if addr.latitude and addr.longitude:
                    dist = _haversine(lat, lon, addr.latitude, addr.longitude)
                    if dist <= radius_km:
                        results.append({
                            'supplier_id': s.id, 'name': s.name, 'email': s.email,
                            'phone': s.phone, 'city': addr.city, 'distance_km': round(dist, 1),
                        })
        results.sort(key=lambda x: x['distance_km'])
        return Response(results[:50])

def _haversine(lat1, lon1, lat2, lon2):
    R = 6371
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon/2)**2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
