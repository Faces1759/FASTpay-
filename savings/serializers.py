from rest_framework import serializers
from .models import SavingsPlan


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