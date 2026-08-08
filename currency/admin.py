from django.contrib import admin
from .models import Currency, ExchangeRate, CurrencyWallet, CurrencyTransaction

@admin.register(Currency)
class CurrencyAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'name_ar', 'symbol', 'is_active']
    search_fields = ['code', 'name', 'name_ar']

@admin.register(ExchangeRate)
class ExchangeRateAdmin(admin.ModelAdmin):
    list_display = ['currency', 'rate_to_ngn', 'source', 'updated_at']

@admin.register(CurrencyWallet)
class CurrencyWalletAdmin(admin.ModelAdmin):
    list_display = ['user', 'currency', 'balance']

@admin.register(CurrencyTransaction)
class CurrencyTransactionAdmin(admin.ModelAdmin):
    list_display = ['user', 'currency', 'transaction_type', 'amount', 'created_at']