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
    online_enabled = models.BooleanField(default=True)
    offline_enabled = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.card_number


class CardTransaction(models.Model):
    ACCOUNT_TYPE = (
        ("savings", "Savings"),
        ("current", "Current"),
    )
    STATUS = (
        ("success", "Success"),
        ("failed", "Failed"),
    )
    card = models.ForeignKey(
        VirtualCard,
        on_delete=models.CASCADE,
        related_name="transactions"
    )
    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2
    )
    account_type = models.CharField(
        max_length=10,
        choices=ACCOUNT_TYPE,
        default="savings"
    )
    channel = models.CharField(
        max_length=10,
        default="pos"
    )
    status = models.CharField(
        max_length=10,
        choices=STATUS,
        default="success"
    )
    reference = models.CharField(
        max_length=50,
        unique=True
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.card.card_number} - {self.amount}"