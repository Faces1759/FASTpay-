from django.contrib import admin
from django.urls import path, include
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path("cards/", include("cards.urls")),
    path("agent/", include("agent.urls")),
    path("dashboard/", include("dashboard.urls")),
    path("akawo/", include("akawo.urls")),
    # JWT AUTH
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    # Apps
    path('api/', include('apps.users.urls')),
    path('wallet/', include('wallet.urls')),
    path('vtu/', include('vtu.urls')),
    path("notifications/", include("notifications.urls")),
    path("akawo/", include ("akawo.urls")),
    # path("savings/", include("savings.urls")),
]  

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    