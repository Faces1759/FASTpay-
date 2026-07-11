from rest_framework import serializers
from .models import (
    SavingsPlan,
    SavingsDeposit,
    SavingsWithdrawal,
)


class SavingsPlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = SavingsPlan
        fields = "__all__"
        read_only_fields = (
            "user",
            "current_balance",
            "status",
            "start_date",
            "maturity_date",
            "first_deposit_taken",
            "created_at",
        )


class SavingsDepositSerializer(serializers.ModelSerializer):
    class Meta:
        model = SavingsDeposit
        fields = "__all__"
        read_only_fields = (
            "plan",
            "deposited_at",
        )


class SavingsWithdrawalSerializer(serializers.ModelSerializer):
    class Meta:
        model = SavingsWithdrawal
        fields = "__all__"
        read_only_fields = (
            "plan",
            "withdrawn_at",
        )