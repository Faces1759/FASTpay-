from decimal import Decimal

import os
import json
import qrcode

from io import BytesIO
from django.core.files import File

from django.db import models
from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver

class Wallet(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE
    )

    pin = models.CharField(
        max_length=128,
        blank=True,
        null=True
    )
    
    phone_number = models.CharField(
    max_length=15,
    blank=True,
    null=True
)

    pin_is_set = models.BooleanField(default=False)

    account_number = models.CharField(
        max_length=10,
        unique=True,
        blank=True,
        null=True
    )

    qr_code = models.ImageField(
        upload_to="qr_codes/",
        blank=True,
        null=True
    )

    transaction_pin = models.CharField(
        max_length=4,
        blank=True,
        null=True
    )

    balance = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal("0.00")
    )
    
    is_active = models.BooleanField(default=True)

    def save(self, *args, **kwargs):
        if not self.account_number:
            last_wallet = Wallet.objects.order_by("-id").first()

            if last_wallet and last_wallet.account_number:
                next_number = str(
                    int(last_wallet.account_number) + 1
                ).zfill(10)
            else:
                next_number = "1000000001"

            self.account_number = next_number

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.user.username} - {self.account_number}"

@receiver(post_save, sender=settings.AUTH_USER_MODEL)

def create_wallet(sender, instance, created, **kwargs):
    if created:
        Wallet.objects.create(user=instance)


class Transaction(models.Model):
    TRANSACTION_TYPES = (
    ("deposit", "Deposit"),
    ("withdraw", "Withdraw"),
    ("transfer", "Transfer"),
    ("airtime", "Airtime"),
    ("data", "Data"),
    ("card", "Card"),
    ("bill", "Bill Payment"),
)
   
    reference = models.CharField(
        max_length=20,
        unique=True,
        blank=True,
        null=True
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE
    )

    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2
    )

    transaction_type = models.CharField(
        max_length=10,
        choices=TRANSACTION_TYPES
    )

    narration = models.CharField(
        max_length=255,
        blank=True,
        null=True
    )

    timestamp = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.reference:
            last_transaction = Transaction.objects.order_by("-id").first()

            if last_transaction:
                next_id = last_transaction.id + 1
            else:
                next_id = 1

            self.reference = f"FP{next_id:08d}"

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.reference} - {self.user.username}"


class Beneficiary(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE
    )

    nickname = models.CharField(max_length=100)

    account_number = models.CharField(max_length=10)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.nickname}"


def deposit(wallet, amount, narration=""):
    amount = Decimal(str(amount))

    wallet.balance += amount
    wallet.save()

    transaction = Transaction.objects.create(
        user=wallet.user,
        amount=amount,
        transaction_type="deposit",
        narration=narration
    )

    return transaction


def withdraw(wallet, amount, narration=""):
    amount = Decimal(str(amount))

    if wallet.balance < amount:
        return None

    wallet.balance -= amount
    wallet.save()

    transaction = Transaction.objects.create(
        user=wallet.user,
        amount=amount,
        transaction_type="withdraw",
        narration=narration
    )

    return transaction

class Savings(models.Model):
    PLAN_TYPES = (
        ("daily", "Daily"),
        ("weekly", "Weekly"),
        ("monthly", "Monthly"),
        ("flexible", "Flexible"),
    )

    DURATION_TYPES = (
        ("1 Month", "1 Month"),
        ("3 Months", "3 Months"),
        ("6 Months", "6 Months"),
        ("12 Months", "12 Months"),
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE
    )

    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2
    )

    plan = models.CharField(
        max_length=20,
        choices=PLAN_TYPES
    )

    duration = models.CharField(
        max_length=20,
        choices=DURATION_TYPES
    )

    status = models.CharField(
        max_length=20,
        default="active"
    )

    created_at = models.DateTimeField(auto_now_add=True)

    maturity_date = models.DateTimeField(
        blank=True,
        null=True
    )

    def __str__(self):
        return f"{self.user.username} - ₦{self.amount}"