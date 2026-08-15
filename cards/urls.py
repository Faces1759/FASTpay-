from django.urls import path
from .views import (
    CreateVirtualCardView,
    CardDetailsView,
    FundCardView,
    FreezeCardView,
    UnfreezeCardView,
    ToggleOnlineView,
    ToggleOfflineView,
    CardPOSTransactionView,
    CardTransactionHistoryView,
)

urlpatterns = [
    path("create/", CreateVirtualCardView.as_view()),
    path("details/", CardDetailsView.as_view()),
    path("fund/", FundCardView.as_view()),
    path("freeze/", FreezeCardView.as_view()),
    path("unfreeze/", UnfreezeCardView.as_view()),
    path("toggle-online/", ToggleOnlineView.as_view()),
    path("toggle-offline/", ToggleOfflineView.as_view()),
    path("pos-transaction/", CardPOSTransactionView.as_view()),
    path("transactions/", CardTransactionHistoryView.as_view()),
]