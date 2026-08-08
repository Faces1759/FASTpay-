from django.urls import path

from .views import (
    CreateSavingsPlanView,
    SavingsPlanListView,
    DepositToSavingsView,
    SavingsWithdrawView,
    SavingsPlanDetailView,
)

urlpatterns = [
    path(
        "create-plan/",
        CreateSavingsPlanView.as_view(),
        name="create-savings-plan",
    ),

    path(
        "plans/",
        SavingsPlanListView.as_view(),
        name="list-plans",
    ),

    path(
        "deposit/<int:plan_id>/",
        DepositToSavingsView.as_view(),
        name="deposit",
    ),

    path(
        "withdraw/<int:plan_id>/",
        SavingsWithdrawView.as_view(),
        name="withdraw",
    ),

    path(
        "plan/<int:plan_id>/",
        SavingsPlanDetailView.as_view(),
        name="plan-detail",
    ),
]