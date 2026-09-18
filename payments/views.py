from decimal import Decimal
from django.db import transaction
from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from .models import Payment, Commission, COMMISSION_RATE
from .serializers import PaymentSerializer


class PaymentInitiateView(generics.CreateAPIView):
    serializer_class = PaymentSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        lease = serializer.validated_data['lease']
        serializer.save(amount=lease.rent_amount)


class PaymentWebhookView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        reference = request.data.get('reference')
        event = request.data.get('event')

        if not reference:
            return Response({"detail": "reference is required."}, status=status.HTTP_400_BAD_REQUEST)

        if not Payment.objects.filter(reference=reference).exists():
            return Response({"detail": "Unknown payment reference."}, status=status.HTTP_404_NOT_FOUND)

        if event != 'payment.success':
            return Response({"detail": "Event ignored."}, status=status.HTTP_200_OK)

        from django.utils import timezone

        with transaction.atomic():
            payment = Payment.objects.select_for_update().get(reference=reference)

            if payment.status == Payment.Status.SUCCESSFUL:
                return Response({"detail": "Already processed."}, status=status.HTTP_200_OK)

            payment.status = Payment.Status.SUCCESSFUL
            payment.confirmed_at = timezone.now()
            payment.save()

            commission_amount = (payment.amount * Decimal(COMMISSION_RATE) / Decimal('100')).quantize(Decimal('0.01'))
            Commission.objects.create(
                payment=payment,
                amount=commission_amount,
                rate=Decimal(COMMISSION_RATE),
            )

        return Response({"detail": "Payment confirmed.", "reference": str(payment.reference)})