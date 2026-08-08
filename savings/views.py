from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

urlpatterns = [
    # Admin
    path("admin/", admin.site.urls),

    # Authentication
    path("api/", include("apps.users.urls")),
    path(
        "api/token/",
        TokenObtainPairView.as_view(),
        name="token_obtain_pair",
    ),
    path(
        "api/token/refresh/",
        TokenRefreshView.as_view(),
        name="token_refresh",
    ),

    # Wallet (includes FASTpay Akawo)
    path("wallet/", include("wallet.urls")),

    # Cards
    path("cards/", include("cards.urls")),

    # Agents
    path("agent/", include("agent.urls")),

    # Dashboard
    path("dashboard/", include("dashboard.urls")),

    # Notifications
    path("notifications/", include("notifications.urls")),

    # VTU
    path("vtu/", include("vtu.urls")),

    # Akawo
    path("akawo/", include("akawo.urls")),

    # NOTE:
    # We have removed the duplicate savings app to avoid
    # conflicts with the wallet savings system.
    #
    # path("savings/", include("savings.urls")),
]

if settings.DEBUG:
    urlpatterns += static(
        settings.MEDIA_URL,
        document_root=settings.MEDIA_ROOT,
    )