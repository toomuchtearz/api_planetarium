from django.urls import path, include
from rest_framework.routers import DefaultRouter

from planetarium.views import ThemeViewSet, ShowViewSet, PlanetariumDomeViewSet, SessionViewSet

router = DefaultRouter()
router.register("themes", ThemeViewSet,)
router.register("shows", ShowViewSet,)
router.register("domes", PlanetariumDomeViewSet,)
router.register("sessions", SessionViewSet,)

urlpatterns = [
    path("", include(router.urls))
]
