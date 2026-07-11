from django.urls import path
from .views import DepositView, WithdrawView, BankListView

from .views import (
    DepositView,
    WithdrawView,
    BankListView,
    WalletBalanceView,
    TransactionHistoryView,
    TransferView,
    AccountDetailsView,
    SetPinView,
    AddBeneficiaryView,
    BeneficiaryListView,
    DeleteBeneficiaryView,
    QRCodeView,
    UpdatePhoneNumberView
)

urlpatterns = [
    path('deposit/', DepositView.as_view()),
    path('withdraw/', WithdrawView.as_view()),
    path("balance/", WalletBalanceView.as_view()),
    path('transactions/', TransactionHistoryView.as_view()),
    path('transfer/', TransferView.as_view()),
    path('account/', AccountDetailsView.as_view()),

    path('beneficiary/add/', AddBeneficiaryView.as_view()),
    path('beneficiaries/', BeneficiaryListView.as_view()),
    path('beneficiary/delete/', DeleteBeneficiaryView.as_view()),
    path("set-pin/", SetPinView.as_view()),
    path("qr-code/", QRCodeView.as_view()),
    path("banks/", BankListView.as_view()),
path( "update-phone/", UpdatePhoneNumberView.as_view(),name="update-phone",),
     
]