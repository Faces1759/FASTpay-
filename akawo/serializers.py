from rest_framework import serializers
from .models import (
    AkawoGroup,
    AkawoMember,
    AkawoContribution,
    AkawoPayout,
)


class AkawoGroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = AkawoGroup
        fields = "__all__"
        read_only_fields = ("creator", "current_members")


class AkawoMemberSerializer(serializers.ModelSerializer):
    class Meta:
        model = AkawoMember
        fields = "__all__"


class ContributionSerializer(serializers.ModelSerializer):
    class Meta:
        model = AkawoContribution
        fields = "__all__"
        
class AkawoPayoutSerializer(serializers.ModelSerializer):
 class Meta:
        model = AkawoPayout
        fields = "__all__"