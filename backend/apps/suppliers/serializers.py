from rest_framework import serializers
from .models import Supplier, SupplierAddress, SupplierCategory

class SupplierAddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = SupplierAddress
        fields = ['id', 'address', 'city', 'region', 'latitude', 'longitude', 'is_active']

class SupplierSerializer(serializers.ModelSerializer):
    addresses = SupplierAddressSerializer(many=True, read_only=True)
    address = serializers.CharField(
        write_only=True, required=False, allow_blank=True,
        help_text="Адрес текстом — будет создан SupplierAddress и геокодирован",
    )
    categories = serializers.ListField(
        child=serializers.IntegerField(), write_only=True, required=False,
        help_text="ID категорий (requests.Category)",
    )

    class Meta:
        model = Supplier
        fields = ['id', 'name', 'legal_name', 'inn', 'site', 'phone', 'email',
                  'is_active', 'hidden_rating', 'moderation_status', 'source',
                  'supplier_type', 'material_types', 'addresses', 'address',
                  'categories', 'created_at']
        read_only_fields = ['id', 'created_at', 'hidden_rating', 'source']

    def create(self, validated_data):
        category_ids = validated_data.pop('categories', [])
        address_text = (validated_data.pop('address', '') or '').strip()
        # B5: manually added suppliers are verified and usable immediately
        validated_data.setdefault('source', 'manual')
        validated_data.setdefault('moderation_status', 'verified')
        supplier = super().create(validated_data)
        if category_ids:
            SupplierCategory.objects.bulk_create([
                SupplierCategory(supplier=supplier, category_id=cid, is_main=(i == 0))
                for i, cid in enumerate(dict.fromkeys(category_ids))
            ])
        if address_text:
            city = address_text.split(",")[0].strip()[:200]
            SupplierAddress.objects.create(supplier=supplier, address=address_text, city=city)
        return supplier

class SupplierListSerializer(serializers.ModelSerializer):
    city = serializers.SerializerMethodField()

    class Meta:
        model = Supplier
        fields = ['id', 'name', 'email', 'phone', 'city', 'is_active',
                  'moderation_status', 'supplier_type', 'source']

    def get_city(self, obj):
        addr = obj.addresses.first()
        return addr.city if addr else ''
