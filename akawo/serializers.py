from rest_framework import serializers
from .models import (
    AkawoGroup,
    AkawoMember,
    AkawoContribution,
    AkawoPayout,
    WithdrawalCode,
)


class AkawoGroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = AkawoGroup
        fields = "__all__"
        read_only_fields = ("creator", "current_members")


class AkawoMemberSerializer(serializers.ModelSerializer):
    class Meta:
        model = AkawoMember


class ContributionSerializer(serializers.ModelSerializer):
    class Meta:
        model = AkawoContribution
        fields = "__all__"
       
class AkawoPayoutSerializer(serializers.ModelSerializer):
 class Meta:
        model = AkawoPayout
        fields = "__all__"


class WithdrawalCodeGenerateSerializer(serializers.Serializer):
    amount = serializers.DecimalField(max_digits=12, decimal_places=2, min_value=100)


class WithdrawalCodeSerializer(serializers.ModelSerializer):
    class Meta:
        model = WithdrawalCode
        fields = ['id', 'code', 'amount', 'status', 'created_at', 'expires_at', 'redeemed_at']


class WithdrawalCodeRedeemSerializer(serializers.Serializer):
    code = serializers.CharField(max_length=6)
    agent_id = serializers.CharField(max_length=100, required=False)

from .models import CorporateAccount, ReleaseRequest, ReleaseApproval


class ReleaseRequestInitSerializer(serializers.Serializer):
    amount = serializers.DecimalField(max_digits=12, decimal_places=2, min_value=100)
    reason = serializers.CharField(max_length=255, required=False, allow_blank=True)
    initiator_number = serializers.CharField(max_length=15)


class ReleaseApprovalSerializer(serializers.Serializer):
    request_id = serializers.IntegerField()
    phone_number = serializers.CharField(max_length=15)
    approved = serializers.BooleanField()


class ReleaseRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReleaseRequest
        fields = ['id', 'amount', 'reason', 'initiated_by', 'status', 'created_at', 'expires_at', 'resolved_at']


class CorporateAccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = CorporateAccount
        fields = ['id', 'business_name', 'authorized_number_1', 'authorized_number_2', 'authorized_number_3', 'created_at']