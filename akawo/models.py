import random
import string
from django.db import models
from django.conf import settings
from django.utils import timezone
from datetime import timedelta


class AkawoGroup(models.Model):
    FREQUENCY = [
        ("daily", "Daily"),
        ("weekly", "Weekly"),
        ("monthly", "Monthly"),
    ]

    name = models.CharField(max_length=100)

    creator = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="created_groups"
    )

    current_receiver_index = models.PositiveIntegerField(default=0)
    current_cycle = models.PositiveIntegerField(default=1)

    contribution_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2
    )

    frequency = models.CharField(
        max_length=10,
        choices=FREQUENCY
    )

    max_members = models.PositiveIntegerField()

    current_members = models.PositiveIntegerField(default=1)

    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class AkawoMember(models.Model):
    group = models.ForeignKey(
        AkawoGroup,
        on_delete=models.CASCADE,
        related_name="members"
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE
    )

    joined_at = models.DateTimeField(auto_now_add=True)

    has_paid_registration = models.BooleanField(default=False)

    has_paid_first_contribution = models.BooleanField(default=False)

    def contributions_total(self):
        return sum(
            c.amount
            for c in self.akawocontribution_set.filter(
                status="successful",
                cycle_number=self.group.current_cycle
            )
        )

    def __str__(self):
        return f"{self.user.username} - {self.group.name}"


class AkawoContribution(models.Model):
    member = models.ForeignKey(
        AkawoMember,
        on_delete=models.CASCADE
    )

    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2
    )

    cycle_number = models.PositiveIntegerField(default=1)

    paid_at = models.DateTimeField(auto_now_add=True)

    status = models.CharField(
        max_length=20,
        default="successful"
    )

    def __str__(self):
        return str(self.amount)


class AkawoPayout(models.Model):
    group = models.ForeignKey(
        AkawoGroup,
        on_delete=models.CASCADE
    )

    member = models.ForeignKey(
        AkawoMember,
        on_delete=models.CASCADE
    )

    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2
    )

    paid_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.member.user.username}"


def generate_code():
    return ''.join(random.choices(string.digits, k=6))


class WithdrawalCode(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('used', 'Used'),
        ('expired', 'Expired'),
        ('cancelled', 'Cancelled'),
    )

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='withdrawal_codes')
    code = models.CharField(max_length=6, unique=True, default=generate_code)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    redeemed_at = models.DateTimeField(null=True, blank=True)
    redeemed_by_agent = models.CharField(max_length=100, null=True, blank=True)

    def save(self, *args, **kwargs):
        if not self.expires_at:
            self.expires_at = timezone.now() + timedelta(minutes=15)
        super().save(*args, **kwargs)

    def is_expired(self):
        return timezone.now() > self.expires_at and self.status == 'pending'

    def __str__(self):
        return f"{self.code} - {self.user} - ₦{self.amount} - {self.status}"

class CorporateAccount(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='corporate_account')
    business_name = models.CharField(max_length=150)
    authorized_number_1 = models.CharField(max_length=15)
    authorized_number_2 = models.CharField(max_length=15)
    authorized_number_3 = models.CharField(max_length=15)
    created_at = models.DateTimeField(auto_now_add=True)

    def is_authorized(self, phone_number):
        return phone_number in [
            self.authorized_number_1,
            self.authorized_number_2,
            self.authorized_number_3,
        ]

    def __str__(self):
        return self.business_name


class ReleaseRequest(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('expired', 'Expired'),
    )

    corporate_account = models.ForeignKey(CorporateAccount, on_delete=models.CASCADE, related_name='release_requests')
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    reason = models.CharField(max_length=255, blank=True)
    initiated_by = models.CharField(max_length=15)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    resolved_at = models.DateTimeField(null=True, blank=True)

    def save(self, *args, **kwargs):
        if not self.expires_at:
            self.expires_at = timezone.now() + timedelta(minutes=30)
        super().save(*args, **kwargs)

    def is_expired(self):
        return timezone.now() > self.expires_at and self.status == 'pending'

    def __str__(self):
        return f"{self.corporate_account.business_name} - ₦{self.amount} - {self.status}"


class ReleaseApproval(models.Model):
    request = models.ForeignKey(ReleaseRequest, on_delete=models.CASCADE, related_name='approvals')
    phone_number = models.CharField(max_length=15)
    approved = models.BooleanField()
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('request', 'phone_number')

    def __str__(self):
        return f"{self.phone_number} - {'Approved' if self.approved else 'Rejected'}"