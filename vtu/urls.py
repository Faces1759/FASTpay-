from django.urls import path
from .views import BuyAirtimeView, BuyDataView, PayBillView

urlpatterns = [
    path("airtime/", BuyAirtimeView.as_view()),
    path("data/", BuyDataView.as_view()),
    path("bill/", PayBillView.as_view()),
]