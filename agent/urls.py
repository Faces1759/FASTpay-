from django.urls import path
from .views import RegisterAgentView, AgentProfileView, AgentDepositView
from .views import (
    RegisterAgentView,
    AgentProfileView,
    AgentDepositView,
    AgentWithdrawalView,
)

urlpatterns = [
    path("register/", RegisterAgentView.as_view()),
    path("profile/", AgentProfileView.as_view()),
    path("deposit/", AgentDepositView.as_view()),
    path("withdraw/", AgentWithdrawalView.as_view()),
    
    
]