from django.db import models
from django.conf import settings


class Agent(models.Model):
    STATUS = (
        ("ACTIVE", "Active"),
        ("SUSPENDED", "Suspended"),
    )

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE
    )

    business_name = models.CharField(max_length=200)

    phone = models.CharField(max_length=15)

    address = models.TextField()

    commission_balance = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS,
        default="ACTIVE"
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.business_name