from rest_framework import viewsets, permissions, decorators
from rest_framework.response import Response
from .models import Supplier, SupplierAddress
from .serializers import SupplierSerializer, SupplierListSerializer
import math

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
        return qs.distinct()

    def get_serializer_class(self):
        if self.action == 'list':
            return SupplierListSerializer
        return SupplierSerializer

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
