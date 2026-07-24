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

class RequestSerializer(serializers.ModelSerializer):
    items = RequestItemSerializer(many=True, read_only=True)
    customer_email = serializers.CharField(source='customer.email', read_only=True)

    class Meta:
        model = Request
        fields = ['id', 'code', 'status', 'raw_text', 'address', 'source',
                  'comment', 'items', 'customer_email', 'created_at', 'updated_at']
        read_only_fields = ['id', 'code', 'status', 'created_at', 'updated_at', 'customer_email']

class RequestCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Request
        fields = ['raw_text', 'address', 'comment']

class ItemConfirmSerializer(serializers.ModelSerializer):
    class Meta:
        model = RequestItem
        fields = ['id', 'name', 'category', 'quantity', 'unit', 'brand', 'spec', 'is_confirmed']
        extra_kwargs = {'is_confirmed': {'required': True}}
