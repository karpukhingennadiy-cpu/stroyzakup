from rest_framework import generics, permissions, status
from rest_framework.throttling import AnonRateThrottle
from rest_framework.response import Response
from .serializers import RegisterSerializer, UserSerializer

class RegisterView(generics.CreateAPIView):
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]
    throttle_classes = [AnonRateThrottle]
    throttle_scope = "auth"
    def create(self, request, *args, **kwargs):
        s = self.get_serializer(data=request.data)
        s.is_valid(raise_exception=True)
        return Response(UserSerializer(s.save()).data, status=status.HTTP_201_CREATED)

class MeView(generics.RetrieveUpdateAPIView):
    serializer_class = UserSerializer
    def get_object(self):
        return self.request.user

class GeocodeView(generics.GenericAPIView):
    """Convert address text to coordinates via 2GIS Catalog API."""
    permission_classes = [permissions.IsAuthenticated]
    def post(self, request):
        from apps.requests.services.geocoder import geocode
        query = request.data.get("address", "")
        if not query:
            return Response({"error": "address required"}, status=400)
        result = geocode(query)
        if result is None:
            return Response({"error": "Geocoding failed. Check address."}, status=400)
        lat, lon, city, full = result
        return Response({
            "latitude": lat, "longitude": lon,
            "city": city, "full_address": full,
        })
