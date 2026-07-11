from decimal import Decimal
from django.db import models
from django.conf import settings

class AirtimeTransaction(models.Model):
    NETWORKS = (
        ("MTN", "MTN"),
        ("AIRTEL", "Airtel"),
        ("GLO", "Glo"),
        ("9MOBILE", "9mobile"),
    )

    STATUSS = (
        ("PENDING", "Pending"),
        ("SUCCESS", "Success"),
        ("FAILED", "Failed"),
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE
    )

    network = models.CharField(
        max_length=20,
        choices=NETWORKS
    )

    phone_number = models.CharField(
        max_length=15
    )

    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2
    )

    reference = models.CharField(
        max_length=30,
        unique=True
    )

    status = models.CharField(
        max_length=20,
        choices=STATUSS,
        default="PENDING"
    )

    provider_response = models.TextField(
        blank=True,
        null=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return f"{self.reference} - {self.network}"
    
class DataTransaction(models.Model):
    NETWORKS = (
        ("MTN", "MTN"),
        ("AIRTEL", "Airtel"),
        ("GLO", "Glo"),
        ("9MOBILE", "9mobile"),
    )

    STATUSS = (
        ("PENDING", "Pending"),
        ("SUCCESS", "Success"),
        ("FAILED", "Failed"),
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE
    )

    network = models.CharField(
        max_length=20,
        choices=NETWORKS
    )

    plan = models.CharField(
        max_length=100
    )

    phone_number = models.CharField(
        max_length=15
    )

    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2
    )

    reference = models.CharField(
        max_length=30,
        unique=True
    )

    status = models.CharField(
        max_length=20,
        choices=STATUSS,
        default="PENDING"
    )

    provider_response = models.TextField(
        blank=True,
        null=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return f"{self.network} - {self.plan}"

class BillPayment(models.Model):

    BILL_TYPES = (
        ("electricity", "Electricity"),
        ("cable_tv", "Cable TV"),
        ("internet", "Internet"),
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE
    )

    bill_type = models.CharField(
        max_length=20,
        choices=BILL_TYPES
    )

    provider = models.CharField(max_length=100)

    customer_number = models.CharField(max_length=100)

    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2
    )

    reference = models.CharField(
        max_length=20,
        unique=True
    )

    status = models.CharField(
        max_length=20,
        default="SUCCESS"
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.reference