from django.urls import path
from .views import (
    CurrencyListView,
    MyCurrencyWalletsView,
    CurrencyDepositView,
    CurrencyWithdrawView,
    ExchangeNgnToForeignView,
    ExchangeForeignToNgnView,
    CurrencyTransactionHistoryView,
)

urlpatterns = [
    path("list/", CurrencyListView.as_view(), name="currency-list"),
    path("wallets/", MyCurrencyWalletsView.as_view(), name="currency-wallets"),
    path("deposit/", CurrencyDepositView.as_view(), name="currency-deposit"),
    path("withdraw/", CurrencyWithdrawView.as_view(), name="currency-withdraw"),
    path("exchange/to-foreign/", ExchangeNgnToForeignView.as_view(), name="exchange-to-foreign"),
    path("exchange/to-ngn/", ExchangeForeignToNgnView.as_view(), name="exchange-to-ngn"),
    path("transactions/", CurrencyTransactionHistoryView.as_view(), name="currency-transactions"),
]