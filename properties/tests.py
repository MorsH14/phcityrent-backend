from decimal import Decimal
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from accounts.models import User
from .models import Property


class PropertyListTests(APITestCase):
    def setUp(self):
        self.landlord = User.objects.create_user(
            username='landlord_test', password='pass12345', role=User.Role.LANDLORD
        )
        Property.objects.create(
            landlord=self.landlord, title="Flat A", location="Lagos",
            price=Decimal('150000.00'), is_available=True,
        )
        Property.objects.create(
            landlord=self.landlord, title="Flat B", location="Abuja",
            price=Decimal('300000.00'), is_available=True,
        )

    def test_list_returns_all_available_properties(self):
        url = reverse('property-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 2)

    def test_filter_by_location_matches(self):
        url = reverse('property-list')
        response = self.client.get(url, {'location': 'lagos'})
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['title'], 'Flat A')

    def test_filter_by_location_excludes_non_matching(self):
        url = reverse('property-list')
        response = self.client.get(url, {'location': 'kano'})
        self.assertEqual(response.data['count'], 0)

    def test_filter_by_min_price_excludes_cheaper(self):
        url = reverse('property-list')
        response = self.client.get(url, {'min_price': 200000})
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['title'], 'Flat B')

    def test_empty_result_set(self):
        url = reverse('property-list')
        response = self.client.get(url, {'location': 'nowhere'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['results'], [])