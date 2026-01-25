from django.urls import path, include
from rest_framework.routers import DefaultRouter

from planetarium.views import ThemeViewSet, ShowViewSet

router = DefaultRouter()
router.register("themes", ThemeViewSet,)
router.register("shows", ShowViewSet,)

urlpatterns = [
    path("", include(router.urls))
]
