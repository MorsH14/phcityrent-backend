from rest_framework import serializers
from .models import Property


class PropertySerializer(serializers.ModelSerializer):
    class Meta:
        model = Property
        fields = [
            'id', 'landlord', 'title', 'description',
            'location', 'price', 'is_available', 'created_at',
        ]
        read_only_fields = ['landlord', 'created_at']