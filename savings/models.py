from django.db import models
from django.conf import settings
from datetime import timedelta
from dateutil.relativedelta import relativedelta


FREQUENCY = [
    ("daily", "Daily"),
    ("weekly", "Weekly"),
    ("monthly", "Monthly"),
    ("yearly", "Yearly"),
]

STATUS = [
    ("active", "Active"),
    ("completed", "Completed"),
    ("cancelled", "Cancelled"),
]


class SavingsPlan(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE
    )

    name = models.CharField(max_length=100)

    target_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2
    )

    amount_per_deposit = models.DecimalField(
        max_digits=12,
        decimal_places=2
    )

    duration = models.PositiveIntegerField(
        help_text="Number of days/weeks/months/years depending on frequency"
    )

    frequency = models.CharField(
        max_length=10,
        choices=FREQUENCY
    )

    current_balance = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS,
        default="active"
    )

    # ==========================
    # AutoSave Fields
    # ==========================
    auto_save = models.BooleanField(default=True)

    last_auto_save = models.DateField(
        blank=True,
        null=True
    )

    next_auto_save = models.DateField(
        blank=True,
        null=True
    )

    start_date = models.DateField(auto_now_add=True)

    maturity_date = models.DateField(
        blank=True,
        null=True
    )

    first_deposit_taken = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if self.start_date:
            if self.frequency == "daily":
                self.maturity_date = self.start_date + timedelta(days=self.duration)
            elif self.frequency == "weekly":
                self.maturity_date = self.start_date + timedelta(weeks=self.duration)
            elif self.frequency == "monthly":
                self.maturity_date = self.start_date + relativedelta(months=self.duration)
            elif self.frequency == "yearly":
                self.maturity_date = self.start_date + relativedelta(years=self.duration)

            # Set the first automatic savings date
            if self.next_auto_save is None:
                if self.frequency == "daily":
                    self.next_auto_save = self.start_date + timedelta(days=1)

                elif self.frequency == "weekly":
                    self.next_auto_save = self.start_date + timedelta(weeks=1)

                elif self.frequency == "monthly":
                    self.next_auto_save = self.start_date + relativedelta(months=1)

                elif self.frequency == "yearly":
                    self.next_auto_save = self.start_date + relativedelta(years=1)

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.user.username} - {self.name}"
    
class SavingsDeposit(models.Model):
    plan = models.ForeignKey(
        SavingsPlan,
        on_delete=models.CASCADE,
        related_name="deposits"
    )

    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2
    )

    deposited_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.plan.name} - {self.amount}"


class SavingsWithdrawal(models.Model):
    plan = models.ForeignKey(
        SavingsPlan,
        on_delete=models.CASCADE,
        related_name="withdrawals"
    )

    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2
    )

    withdrawn_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.plan.name} - {self.amount}"
class SavingsDeposit(models.Model):
    plan = models.ForeignKey(
        SavingsPlan,
        on_delete=models.CASCADE,
        related_name="deposits"
    )

    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2
    )

    deposited_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.plan.name} - {self.amount}"


class SavingsWithdrawal(models.Model):
    plan = models.ForeignKey(
        SavingsPlan,
        on_delete=models.CASCADE,
        related_name="withdrawals"
    )

    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2
    )

    withdrawn_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.plan.name} - {self.amount}"