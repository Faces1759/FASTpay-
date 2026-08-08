from django.urls import path
from .views import CreateVirtualCardView, CardDetailsView

from .views import (
    CreateVirtualCardView,
    CardDetailsView,
    FundCardView,
    FreezeCardView,
    UnfreezeCardView,
)

urlpatterns = [
    path("create/", CreateVirtualCardView.as_view()),
    path("details/", CardDetailsView.as_view()),
    path("fund/", FundCardView.as_view()),
    path("freeze/", FreezeCardView.as_view()),
    path("unfreeze/", UnfreezeCardView.as_view()),
    
]