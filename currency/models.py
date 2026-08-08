from decimal import Decimal
from django.db import models
from django.conf import settings
from django.utils import timezone

class Currency(models.Model):
    code = models.CharField(max_length=3, unique=True, help_text="e.g. USD, GBP, EUR")
    name = models.CharField(max_length=50)
    name_ar = models.CharField(max_length=50, blank=True, default="", help_text="Arabic name")
    symbol = models.CharField(max_length=5, default="$")
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.code

class ExchangeRate(models.Model):
    SOURCE_CHOICES = (
        ('live', 'Live API'),
        ('manual', 'Manual Override'),
        ('fixed', 'Fixed Fallback'),
    )
    currency = models.OneToOneField(Currency, on_delete=models.CASCADE, related_name='rate')
    rate_to_ngn = models.DecimalField(
        max_digits=15,
        decimal_places=4,
        help_text="How many NGN for 1 unit of this currency"
    )
    source = models.CharField(max_length=10, choices=SOURCE_CHOICES, default='fixed')
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"1 {self.currency.code} = ₦{self.rate_to_ngn} ({self.source})"

class CurrencyWallet(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='currency_wallets')
    currency = models.ForeignKey(Currency, on_delete=models.CASCADE)
    balance = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal("0.00"))

    class Meta:
        unique_together = ('user', 'currency')

    def __str__(self):
        return f"{self.user.username} - {self.currency.code} {self.balance}"

class CurrencyTransaction(models.Model):
    TYPE_CHOICES = (
        ('deposit', 'Deposit'),
        ('withdraw', 'Withdraw'),
        ('exchange_in', 'Exchange In'),
        ('exchange_out', 'Exchange Out'),
    )
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    currency = models.ForeignKey(Currency, on_delete=models.CASCADE)
    transaction_type = models.CharField(max_length=15, choices=TYPE_CHOICES)
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    rate_used = models.DecimalField(max_digits=15, decimal_places=4, null=True, blank=True)
    narration = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.transaction_type} - {self.currency.code} {self.amount}"