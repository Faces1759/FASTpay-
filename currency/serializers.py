from rest_framework import serializers
from .models import Currency, ExchangeRate, CurrencyWallet, CurrencyTransaction

class CurrencySerializer(serializers.ModelSerializer):
    rate_to_ngn = serializers.SerializerMethodField()
    rate_source = serializers.SerializerMethodField()

    class Meta:
        model = Currency
        fields = ['id', 'code', 'name', 'name_ar', 'symbol', 'rate_to_ngn', 'rate_source']

    def get_rate_to_ngn(self, obj):
        try:
            return str(obj.rate.rate_to_ngn)
        except ExchangeRate.DoesNotExist:
            return None

    def get_rate_source(self, obj):
        try:
            return obj.rate.source
        except ExchangeRate.DoesNotExist:
            return None

class CurrencyWalletSerializer(serializers.ModelSerializer):
    currency_code = serializers.CharField(source='currency.code', read_only=True)
    currency_symbol = serializers.CharField(source='currency.symbol', read_only=True)

    class Meta:
        model = CurrencyWallet
        fields = ['id', 'currency_code', 'currency_symbol', 'balance']

class CurrencyDepositSerializer(serializers.Serializer):
    currency_code = serializers.CharField(max_length=3)
    amount = serializers.DecimalField(max_digits=15, decimal_places=2, min_value=1)

class CurrencyWithdrawSerializer(serializers.Serializer):
    currency_code = serializers.CharField(max_length=3)
    amount = serializers.DecimalField(max_digits=15, decimal_places=2, min_value=1)

class ExchangeToForeignSerializer(serializers.Serializer):
    currency_code = serializers.CharField(max_length=3)
    ngn_amount = serializers.DecimalField(max_digits=15, decimal_places=2, min_value=1)

class ExchangeToNgnSerializer(serializers.Serializer):
    currency_code = serializers.CharField(max_length=3)
    foreign_amount = serializers.DecimalField(max_digits=15, decimal_places=2, min_value=1)

class CurrencyTransactionSerializer(serializers.ModelSerializer):
    currency_code = serializers.CharField(source='currency.code', read_only=True)

    class Meta:
        model = CurrencyTransaction
        fields = ['id', 'currency_code', 'transaction_type', 'amount', 'rate_used', 'narration', 'created_at']