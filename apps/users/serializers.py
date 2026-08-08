from rest_framework import serializers
from .models import User, Business


class BusinessSerializer(serializers.ModelSerializer):
    class Meta:
        model = Business
        fields = [
            'company_name', 'rc_number', 'business_type',
            'industry', 'business_address', 'tin_number', 'website'
        ]


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=6)
    business = BusinessSerializer(required=False)

    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'account_type', 'business']

    def validate(self, data):
        account_type = data.get('account_type', 'personal')
        business_data = data.get('business')

        if account_type == 'business' and not business_data:
            raise serializers.ValidationError(
                {"business": "Business details are required when account_type is 'business'."}
            )
        if account_type == 'business' and business_data and not business_data.get('company_name'):
            raise serializers.ValidationError(
                {"company_name": "Company name is required for business accounts."}
            )
        return data

    def create(self, validated_data):
        business_data = validated_data.pop('business', None)
        account_type = validated_data.get('account_type', 'personal')

        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password'],
            account_type=account_type,
        )

        if account_type == 'business' and business_data:
            Business.objects.create(user=user, **business_data)

        return user