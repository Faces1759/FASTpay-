from django.urls import path
from .views import DashboardView, UserListView

from .views import (
    DashboardView,
    UserListView,
    FreezeUserView,
    UnfreezeUserView,
    AgentListView,
    SuspendAgentView,
    ReactivateAgentView,
    TransactionListView,
)

urlpatterns = [
    path("", DashboardView.as_view()),
    path("users/", UserListView.as_view()),
    path("users/freeze/", FreezeUserView.as_view()),
    path("users/unfreeze/", UnfreezeUserView.as_view()),
    path("agents/", AgentListView.as_view()),
    path("agents/suspend/", SuspendAgentView.as_view()),
    path("agents/reactivate/", ReactivateAgentView.as_view()),
    path("transactions/", TransactionListView.as_view()),
]