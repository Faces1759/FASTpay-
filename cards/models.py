from django.db import models
from django.conf import settings


class VirtualCard(models.Model):
    STATUS = (
        ("ACTIVE", "Active"),
        ("FROZEN", "Frozen"),
    )

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE
    )

    card_holder = models.CharField(max_length=100)

    card_number = models.CharField(
        max_length=19,
        unique=True
    )

    expiry = models.CharField(max_length=5)

    cvv = models.CharField(max_length=3)

    balance = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0
    )

    status = models.CharField(
        max_length=10,
        choices=STATUS,
        default="ACTIVE"
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.card_number