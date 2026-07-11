from django.urls import path
from .views import CreateAkawoGroupView
from .views import CreateAkawoGroupView, JoinAkawoGroupView, AkawoGroupListView, MyGroupsView, ContributionView, ContributionHistoryView, GroupBalanceView, CurrentReceiverView, PayoutView, PayoutHistoryView

urlpatterns = [
    path(
        "create/",
        CreateAkawoGroupView.as_view(),
        name="create-akawo-group",
    ),
    
    path(
    "join/",
    JoinAkawoGroupView.as_view(),
    name="join-akawo-group",
),
    
    path(
    "groups/",
    AkawoGroupListView.as_view(),
    name="akawo-groups",
),
    
    path(
    "my-groups/",
    MyGroupsView.as_view(),
    name="my-groups",
),
    
    path(
    "contribute/",
    ContributionView.as_view(),
    name="contribute",
),
    
    path("group/<int:group_id>/contributions/",  ContributionHistoryView.as_view()
),
    
    path(
    "balance/<int:group_id>/",
    GroupBalanceView.as_view(),
    name="group-balance",
),
    
    path(
    "current-receiver/<int:group_id>/",
    CurrentReceiverView.as_view(),
    name="current-receiver",
),
    
    path(
    "payout/<int:group_id>/",
    PayoutView.as_view(),
    name="payout",
),
    
    path(
    "payout-history/<int:group_id>/",
    PayoutHistoryView.as_view(),
    name="payout-history",
),
    
]