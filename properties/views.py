from rest_framework import generics
from rest_framework.permissions import AllowAny
from .models import Property
from .serializers import PropertySerializer
from .filters import PropertyFilter


class PropertyListView(generics.ListAPIView):
    queryset = Property.objects.filter(is_available=True).select_related('landlord')
    serializer_class = PropertySerializer
    permission_classes = [AllowAny]
    filterset_class = PropertyFilter


class PropertyDetailView(generics.RetrieveAPIView):
    queryset = Property.objects.all().select_related('landlord')
    serializer_class = PropertySerializer
    permission_classes = [AllowAny]