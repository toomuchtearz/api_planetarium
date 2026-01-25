from django.urls import path, include
from rest_framework.routers import DefaultRouter

from planetarium.views import ThemeViewSet, ShowViewSet, PlanetariumDomeViewSet

router = DefaultRouter()
router.register("themes", ThemeViewSet,)
router.register("shows", ShowViewSet,)
router.register("domes", PlanetariumDomeViewSet,)

urlpatterns = [
    path("", include(router.urls))
]
