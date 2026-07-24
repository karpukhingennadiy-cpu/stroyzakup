from rest_framework import serializers
from .models import Quote, QuoteItem, CompetitiveSheet, RfqInvitation, EmailMessage

class QuoteItemSerializer(serializers.ModelSerializer):
    material_name = serializers.CharField(source='request_item.name', read_only=True)

    class Meta:
        model = QuoteItem
        fields = ['id', 'request_item', 'material_name', 'price', 'vat_included',
                  'is_analog', 'brand', 'confidence']
        read_only_fields = ['id']

class QuoteSerializer(serializers.ModelSerializer):
    items = QuoteItemSerializer(many=True, read_only=True)
    supplier_name = serializers.CharField(source='supplier.name', read_only=True)

    class Meta:
        model = Quote
        fields = ['id', 'request', 'supplier', 'supplier_name', 'status',
                  'delivery_cost', 'delivery_time', 'payment_terms',
                  'valid_until', 'comment', 'items', 'created_at']
        read_only_fields = ['id', 'created_at']

class CompetitiveSheetSerializer(serializers.ModelSerializer):
    class Meta:
        model = CompetitiveSheet
        fields = ['id', 'request', 'best_supplier', 'total_amount', 'created_at', 'updated_at']
