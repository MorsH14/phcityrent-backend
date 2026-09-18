from rest_framework import serializers
from .models import Application


class ApplicationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Application
        fields = ['id', 'tenant', 'property', 'status', 'message', 'created_at', 'updated_at']
        read_only_fields = ['tenant', 'status', 'created_at', 'updated_at']