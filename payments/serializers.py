from rest_framework import serializers
from .models import Payment, Commission


class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = ['id', 'lease', 'reference', 'amount', 'status', 'created_at', 'confirmed_at']
        read_only_fields = ['reference', 'amount', 'status', 'created_at', 'confirmed_at']

class CommissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Commission
        fields = ['id', 'payment', 'amount', 'rate', 'created_at']