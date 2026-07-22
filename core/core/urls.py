from django.contrib import admin
from django.urls import path, include
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

from django.conf import settings
from django.conf.urls.static import static


urlpatterns = [
    # Admin
    path("admin/", admin.site.urls),

    # Authentication (JWT)
    path("api/token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("api/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),

    # Users
    path("api/", include("apps.users.urls")),

    # Wallet
    path("wallet/", include("wallet.urls")),

    # VTU (Airtime, Data & Bills)
    path("vtu/", include("vtu.urls")),

    # Dashboard
    path("dashboard/", include("dashboard.urls")),

    # Notifications
    path("notifications/", include("notifications.urls")),

    # FASTpay Akawo
    path("akawo/", include("akawo.urls")),

    # Cards
    path("cards/", include("cards.urls")),

    # Agents
    path("agent/", include("agent.urls")),

    # Savings (Enable this when your savings URLs are ready)
    # path("savings/", include("savings.urls")),
]


if settings.DEBUG:
    urlpatterns += static(
        settings.MEDIA_URL,
        document_root=settings.MEDIA_ROOT,
    )