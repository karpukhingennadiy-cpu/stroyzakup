from rest_framework import serializers
from .models import Request, RequestItem, Category, Unit, Address

class RequestItemSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)
    unit_name = serializers.CharField(source='unit.short_name', read_only=True)

    class Meta:
        model = RequestItem
        fields = ['id', 'raw_text', 'name', 'category', 'category_name', 'quantity',
                  'unit', 'unit_name', 'brand', 'spec', 'confidence', 'is_confirmed']
        read_only_fields = ['id', 'confidence', 'is_confirmed']

class AddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = Address
        fields = ['id', 'address', 'city', 'region', 'latitude', 'longitude']

class RequestSerializer(serializers.ModelSerializer):
    items = RequestItemSerializer(many=True, read_only=True)
    customer_email = serializers.CharField(source='customer.email', read_only=True)
    address_detail = AddressSerializer(source='address', read_only=True)
    delivery_address = serializers.CharField(write_only=True, required=False)

    class Meta:
        model = Request
        fields = ['id', 'code', 'status', 'raw_text', 'address', 'address_detail',
                  'delivery_address', 'source', 'comment', 'items',
                  'customer_email', 'created_at', 'updated_at']
        read_only_fields = ['id', 'code', 'status', 'created_at', 'updated_at', 'customer_email']

class RequestCreateSerializer(serializers.ModelSerializer):
    delivery_address = serializers.CharField(write_only=True, required=False)
    latitude = serializers.FloatField(write_only=True, required=False)
    longitude = serializers.FloatField(write_only=True, required=False)
    city = serializers.CharField(write_only=True, required=False)

    class Meta:
        model = Request
        fields = ['raw_text', 'address', 'delivery_address',
                  'latitude', 'longitude', 'city', 'comment']

    def create(self, validated_data):
        delivery_address = validated_data.pop('delivery_address', None)
        lat = validated_data.pop('latitude', None)
        lon = validated_data.pop('longitude', None)
        city = validated_data.pop('city', None)
        request = self.context['request']
        instance = super().create(validated_data)

        # If frontend already geocoded, use those coordinates
        if lat and lon:
            from .models import Address
            addr = Address.objects.create(
                customer=request.user,
                address=delivery_address or f"{city}",
                city=city or "",
                latitude=lat,
                longitude=lon,
            )
            instance.address = addr
            instance.save(update_fields=['address'])
        elif delivery_address:
            # Fallback: geocode on backend
            from .services.geocoder import geocode
            from .models import Address
            result = geocode(delivery_address)
            if result:
                glat, glon, gcity, full = result
                addr = Address.objects.create(
                    customer=request.user,
                    address=delivery_address,
                    city=gcity,
                    latitude=glat,
                    longitude=glon,
                )
                instance.address = addr
                instance.save(update_fields=['address'])
            else:
                # Geocoding failed but address text is still saved
                from .models import Address
                addr = Address.objects.create(
                    customer=request.user,
                    address=delivery_address,
                    city=city or "",
                )
                instance.address = addr
                instance.save(update_fields=['address'])
        return instance

class ItemConfirmSerializer(serializers.ModelSerializer):
    class Meta:
        model = RequestItem
        fields = ['id', 'name', 'category', 'quantity', 'unit', 'brand', 'spec', 'is_confirmed']
        extra_kwargs = {'is_confirmed': {'required': True}}
