from debug_toolbar.toolbar import debug_toolbar_urls
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include
from drf_spectacular.views import (
        SpectacularAPIView,
        SpectacularRedocView,
        SpectacularSwaggerView,
)
from rest_framework_simplejwt.views import (
        TokenObtainPairView,
        TokenRefreshView
)

from api_planetarium import settings

urlpatterns = (
    [
        path("admin/", admin.site.urls),
        path(
                "api/planetarium/",
                include("planetarium.urls", namespace="planetarium")
        ),
        path(
                "api/user/",
                include("user.urls", namespace="user")
        ),
        path(
                "api/token/",
                TokenObtainPairView.as_view(),
                name="token_obtain_pair"
        ),
        path(
                "api/token/refresh/",
                TokenRefreshView.as_view(),
                name="token_refresh"
        ),
            path("api/doc/", SpectacularAPIView.as_view(), name="schema"),
            path("api/doc/swagger/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
            path("api/doc/redoc/", SpectacularRedocView.as_view(url_name="schema"), name="redoc"),
    ]
    + debug_toolbar_urls()
    + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
)
