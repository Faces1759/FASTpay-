from django.db import models
from django.conf import settings


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