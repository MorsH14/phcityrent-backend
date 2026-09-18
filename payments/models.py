import uuid
from django.db import models
from leases.models import Lease


COMMISSION_RATE = 10  # percent


class Payment(models.Model):
    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        SUCCESSFUL = "SUCCESSFUL", "Successful"
        FAILED = "FAILED", "Failed"

    lease = models.ForeignKey(
        Lease,
        on_delete=models.CASCADE,
        related_name='payments',
    )
    reference = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    confirmed_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Payment {self.reference} ({self.status})"


class Commission(models.Model):
    payment = models.OneToOneField(
        Payment,
        on_delete=models.CASCADE,
        related_name='commission',
    )
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    rate = models.DecimalField(max_digits=5, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Commission {self.amount} for payment {self.payment_id}"