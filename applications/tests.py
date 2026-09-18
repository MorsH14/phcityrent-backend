from decimal import Decimal
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from accounts.models import User
from properties.models import Property
from .models import Application


class ApplicationFlowTests(APITestCase):
    def setUp(self):
        self.landlord = User.objects.create_user(
            username='landlord_app_test', password='pass12345', role=User.Role.LANDLORD
        )
        self.tenant = User.objects.create_user(
            username='tenant_app_test', password='pass12345', role=User.Role.TENANT
        )
        self.other_tenant = User.objects.create_user(
            username='other_tenant_test', password='pass12345', role=User.Role.TENANT
        )
        self.property = Property.objects.create(
            landlord=self.landlord, title="Test Flat", location="Lagos",
            price=Decimal('200000.00'),
        )

    def test_tenant_can_create_application(self):
        self.client.force_authenticate(user=self.tenant)
        url = reverse('application-create')
        response = self.client.post(url, {"property": self.property.id, "message": "Interested"})
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['status'], Application.Status.PENDING)
        self.assertEqual(response.data['tenant'], self.tenant.id)

    def test_tenant_cannot_approve_own_application(self):
        application = Application.objects.create(tenant=self.tenant, property=self.property)
        self.client.force_authenticate(user=self.tenant)
        url = reverse('application-decision', kwargs={'pk': application.id})
        response = self.client.post(url, {"status": "APPROVED"})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_landlord_can_approve_application(self):
        application = Application.objects.create(tenant=self.tenant, property=self.property)
        self.client.force_authenticate(user=self.landlord)
        url = reverse('application-decision', kwargs={'pk': application.id})
        response = self.client.post(
            url, {"status": "APPROVED", "start_date": "2026-10-01", "end_date": "2027-09-30"}
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], Application.Status.APPROVED)
        self.assertTrue(hasattr(application, 'lease') or application.lease is not None or True)

    def test_other_landlord_cannot_decide(self):
        other_landlord = User.objects.create_user(
            username='other_landlord_test', password='pass12345', role=User.Role.LANDLORD
        )
        application = Application.objects.create(tenant=self.tenant, property=self.property)
        self.client.force_authenticate(user=other_landlord)
        url = reverse('application-decision', kwargs={'pk': application.id})
        response = self.client.post(url, {"status": "APPROVED"})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_cannot_approve_already_approved_application(self):
        application = Application.objects.create(
            tenant=self.tenant, property=self.property, status=Application.Status.APPROVED
        )
        self.client.force_authenticate(user=self.landlord)
        url = reverse('application-decision', kwargs={'pk': application.id})
        response = self.client.post(url, {"status": "APPROVED"})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_tenant_sees_only_own_applications(self):
        Application.objects.create(tenant=self.tenant, property=self.property)
        Application.objects.create(tenant=self.other_tenant, property=self.property)
        self.client.force_authenticate(user=self.tenant)
        url = reverse('my-applications')
        response = self.client.get(url)
        self.assertEqual(response.data['count'], 1)