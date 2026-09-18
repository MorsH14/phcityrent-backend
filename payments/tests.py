from decimal import Decimal
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from accounts.models import User
from properties.models import Property
from applications.models import Application
from leases.models import Lease
from .models import Payment, Commission


class PaymentFlowTests(APITestCase):
    def setUp(self):
        self.landlord = User.objects.create_user(
            username='landlord_pay_test', password='pass12345', role=User.Role.LANDLORD
        )
        self.tenant = User.objects.create_user(
            username='tenant_pay_test', password='pass12345', role=User.Role.TENANT
        )
        self.property = Property.objects.create(
            landlord=self.landlord, title="Pay Test Flat", location="Lagos",
            price=Decimal('200000.00'),
        )
        self.application = Application.objects.create(
            tenant=self.tenant, property=self.property, status=Application.Status.APPROVED,
        )
        self.lease = Lease.objects.create(
            application=self.application,
            rent_amount=Decimal('200000.00'),
            start_date="2026-10-01",
            end_date="2027-09-30",
        )

    def test_initiate_payment(self):
        self.client.force_authenticate(user=self.tenant)
        url = reverse('payment-initiate')
        response = self.client.post(url, {"lease": self.lease.id})
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['status'], Payment.Status.PENDING)
        self.assertEqual(response.data['amount'], '200000.00')

    def test_webhook_confirms_payment_and_creates_commission(self):
        payment = Payment.objects.create(lease=self.lease, amount=Decimal('200000.00'))
        url = reverse('payment-webhook')
        response = self.client.post(url, {
            "reference": str(payment.reference),
            "event": "payment.success",
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        payment.refresh_from_db()
        self.assertEqual(payment.status, Payment.Status.SUCCESSFUL)
        self.assertIsNotNone(payment.confirmed_at)

        commission = Commission.objects.get(payment=payment)
        self.assertEqual(commission.amount, Decimal('20000.00'))
        self.assertEqual(commission.rate, Decimal('10.00'))

    def test_duplicate_webhook_does_not_create_second_commission(self):
        payment = Payment.objects.create(lease=self.lease, amount=Decimal('200000.00'))
        url = reverse('payment-webhook')
        data = {"reference": str(payment.reference), "event": "payment.success"}

        first_response = self.client.post(url, data)
        second_response = self.client.post(url, data)

        self.assertEqual(first_response.status_code, status.HTTP_200_OK)
        self.assertEqual(second_response.status_code, status.HTTP_200_OK)
        self.assertEqual(second_response.data['detail'], 'Already processed.')
        self.assertEqual(Commission.objects.filter(payment=payment).count(), 1)

    def test_webhook_unknown_reference_returns_404(self):
        url = reverse('payment-webhook')
        response = self.client.post(url, {
            "reference": "00000000-0000-0000-0000-000000000000",
            "event": "payment.success",
        })
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)