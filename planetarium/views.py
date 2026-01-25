from rest_framework import viewsets

from planetarium.models import Theme, Show
from planetarium.serializers import ThemeSerializer, ShowSerializer, ShowListSerializer


class ThemeViewSet(viewsets.ModelViewSet):
    queryset = Theme.objects.all()
    serializer_class = ThemeSerializer


class ShowViewSet(viewsets.ModelViewSet):
    queryset = Show.objects.all()
    serializer_class = ShowSerializer

    def get_serializer_class(self):
        if self.action == "list":
            return ShowListSerializer
        return self.serializer_class
