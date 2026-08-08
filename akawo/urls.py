from django.urls import path
from .views import (
    CreateAkawoGroupView, JoinAkawoGroupView, AkawoGroupListView, MyGroupsView,
    ContributionView, ContributionHistoryView, GroupBalanceView, CurrentReceiverView,
    PayoutView, PayoutHistoryView,
    GenerateWithdrawalCodeView, RedeemWithdrawalCodeView, MyWithdrawalCodesView,
    CreateCorporateAccountView, InitiateReleaseView, ApproveReleaseView, ReleaseRequestStatusView,
)

urlpatterns = [
    path("create/", CreateAkawoGroupView.as_view(), name="create-akawo-group"),
    path("join/", JoinAkawoGroupView.as_view(), name="join-akawo-group"),
    path("groups/", AkawoGroupListView.as_view(), name="akawo-groups"),
    path("my-groups/", MyGroupsView.as_view(), name="my-groups"),
    path("contribute/", ContributionView.as_view(), name="contribute"),
    path("group/<int:group_id>/contributions/", ContributionHistoryView.as_view()),
    path("balance/<int:group_id>/", GroupBalanceView.as_view(), name="group-balance"),
    path("current-receiver/<int:group_id>/", CurrentReceiverView.as_view(), name="current-receiver"),
    path("payout/<int:group_id>/", PayoutView.as_view(), name="payout"),
    path("payout-history/<int:group_id>/", PayoutHistoryView.as_view(), name="payout-history"),

    path("withdrawal-code/generate/", GenerateWithdrawalCodeView.as_view(), name="akawo-generate"),
    path("withdrawal-code/redeem/", RedeemWithdrawalCodeView.as_view(), name="akawo-redeem"),
    path("withdrawal-code/mine/", MyWithdrawalCodesView.as_view(), name="akawo-mine"),
    path("corporate/create/", CreateCorporateAccountView.as_view(), name="corporate-create"),
    path("corporate/release/initiate/", InitiateReleaseView.as_view(), name="corporate-release-initiate"),
    path("corporate/release/approve/", ApproveReleaseView.as_view(), name="corporate-release-approve"),
    path("corporate/release/<int:request_id>/status/", ReleaseRequestStatusView.as_view(), name="corporate-release-status"),

]