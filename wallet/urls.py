from django.urls import path

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
    UpdatePhoneNumberView,

    # FASTpay Akawo (Savings)
    StartSavingsView,
    SavingsListView,
    SavingsHistoryView,
)

urlpatterns = [
    # Wallet
    path("deposit/", DepositView.as_view()),
    path("withdraw/", WithdrawView.as_view()),
    path("balance/", WalletBalanceView.as_view()),
    path("transfer/", TransferView.as_view()),
    path("account/", AccountDetailsView.as_view()),
    path("transactions/", TransactionHistoryView.as_view()),

    # FASTpay Akawo (Savings)
    path("savings/create/", StartSavingsView.as_view()),
    path("savings/", SavingsListView.as_view()),
    path("savings/history/", SavingsHistoryView.as_view()),

    # Beneficiaries
    path("beneficiary/add/", AddBeneficiaryView.as_view()),
    path("beneficiaries/", BeneficiaryListView.as_view()),
    path("beneficiary/delete/", DeleteBeneficiaryView.as_view()),

    # Settings
    path("set-pin/", SetPinView.as_view()),
    path("update-phone/", UpdatePhoneNumberView.as_view()),

    # QR Code & Banks
    path("qr-code/", QRCodeView.as_view()),
    path("banks/", BankListView.as_view()),
]