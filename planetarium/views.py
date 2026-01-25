from rest_framework import viewsets

from planetarium.models import Theme, Show, PlanetariumDome
from planetarium.serializers import ThemeSerializer, ShowSerializer, ShowListSerializer, ShowRetrieveSerializer, \
    PlanetariumDomeSerializer


class ThemeViewSet(viewsets.ModelViewSet):
    queryset = Theme.objects.all()
    serializer_class = ThemeSerializer


class ShowViewSet(viewsets.ModelViewSet):
    queryset = Show.objects.all()
    serializer_class = ShowSerializer

    def get_serializer_class(self):
        if self.action == "list":
            return ShowListSerializer
        elif self.action == "retrieve":
            return ShowRetrieveSerializer
        return self.serializer_class

    def get_queryset(self):
        queryset = self.queryset
        if self.action in ("list", "retrieve"):
            queryset = queryset.prefetch_related(
                "themes",
            )
        return queryset


class PlanetariumDomeViewSet(viewsets.ModelViewSet):
    queryset = PlanetariumDome.objects.all()
    serializer_class = PlanetariumDomeSerializer
