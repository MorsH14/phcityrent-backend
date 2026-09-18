from django.db import models
from django.conf import settings
from properties.models import Property


class Application(models.Model):
    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        APPROVED = "APPROVED", "Approved"
        REJECTED = "REJECTED", "Rejected"
        WITHDRAWN = "WITHDRAWN", "Withdrawn"

    tenant = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='applications',
    )
    property = models.ForeignKey(
        Property,
        on_delete=models.CASCADE,
        related_name='applications',
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
    )
    message = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.tenant} -> {self.property} ({self.status})"