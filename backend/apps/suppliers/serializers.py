from rest_framework import serializers
from .models import Supplier, SupplierAddress, SupplierCategory

class SupplierAddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = SupplierAddress
        fields = ['id', 'address', 'city', 'region', 'latitude', 'longitude', 'is_active']

class SupplierSerializer(serializers.ModelSerializer):
    addresses = SupplierAddressSerializer(many=True, read_only=True)

    class Meta:
        model = Supplier
        fields = ['id', 'name', 'legal_name', 'inn', 'site', 'phone', 'email',
                  'is_active', 'hidden_rating', 'addresses', 'created_at']
        read_only_fields = ['id', 'created_at', 'hidden_rating']

class SupplierListSerializer(serializers.ModelSerializer):
    city = serializers.SerializerMethodField()

    class Meta:
        model = Supplier
        fields = ['id', 'name', 'email', 'phone', 'city', 'is_active']

    def get_city(self, obj):
        addr = obj.addresses.first()
        return addr.city if addr else ''
