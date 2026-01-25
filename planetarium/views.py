from rest_framework import viewsets

from planetarium.models import Theme, Show, PlanetariumDome, Session, Order
from planetarium.serializers import (
    ThemeSerializer,

    ShowSerializer,
    ShowListSerializer,
    ShowRetrieveSerializer,

    PlanetariumDomeSerializer,

    SessionSerializer,
    SessionListSerializer,
    SessionRetrieveSerializer,

    OrderCreateSerializer, OrderListSerializer
)


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


class SessionViewSet(viewsets.ModelViewSet):
    queryset = Session.objects.all()
    serializer_class = SessionSerializer

    def get_serializer_class(self):
        serializer = self.serializer_class
        if self.action == "list":
            serializer = SessionListSerializer
        elif self.action == "retrieve":
            serializer = SessionRetrieveSerializer

        return serializer

    def get_queryset(self):
        queryset = self.queryset
        if self.action == "list":
            queryset = queryset.select_related(
                "dome", "show"
            )
        return queryset


class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all()
    serializer_class = OrderListSerializer

    def get_queryset(self):
        queryset = self.queryset
        queryset = queryset.filter(user=self.request.user)

        if self.action == "list":
            queryset = queryset.prefetch_related(
                "tickets",
                "tickets__session__show",
                "tickets__session__dome",
            )
        return queryset

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def get_serializer_class(self):
        serializer = self.serializer_class
        if self.action == "create":
            serializer = OrderCreateSerializer

        return serializer