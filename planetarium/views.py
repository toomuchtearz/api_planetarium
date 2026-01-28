from datetime import datetime

from django.db.models import Prefetch, F, Count
from django.utils import timezone
from rest_framework import viewsets

from planetarium.models import Theme, Show, PlanetariumDome, Session, Order, Ticket
from planetarium.serializers import (
    ThemeSerializer,
    ShowListSerializer,
    ShowRetrieveSerializer,
    DomeSerializer,
    SessionListSerializer,
    SessionRetrieveSerializer,
    OrderCreateSerializer,
    OrderListSerializer,
    ThemeRetrieveSerializer,
    ShowCreateSerializer, DomeRetrieveSerializer, SessionCreateSerializer,
)


def str_ids_to_int(str_ids):
    return [int(str_id) for str_id in str_ids.split(",")]


class ThemeViewSet(viewsets.ModelViewSet):
    queryset = Theme.objects.all()
    serializer_class = ThemeSerializer

    def get_serializer_class(self):
        serializer = self.serializer_class
        if self.action == "retrieve":
            serializer = ThemeRetrieveSerializer

        return serializer


class ShowViewSet(viewsets.ModelViewSet):
    queryset = Show.objects.all()
    serializer_class = ShowCreateSerializer

    def get_serializer_class(self):
        serializer = self.serializer_class
        if self.action == "list":
            serializer = ShowListSerializer
        elif self.action == "retrieve":
            serializer = ShowRetrieveSerializer
        return serializer

    def get_queryset(self):
        queryset = self.queryset

        themes_id = self.request.query_params.get("themes")
        title = self.request.query_params.get("title")

        if themes_id:
            themes_ids = str_ids_to_int(str_ids=themes_id)
            queryset = queryset.filter(
                themes__id__in=themes_ids
            )

        if title:
            queryset = queryset.filter(
                title__icontains=title
            )

        if self.action == "list":
            queryset = queryset.prefetch_related(
                "themes"
            )

        elif self.action == "retrieve":
            queryset = queryset.prefetch_related(
                "themes",
                Prefetch(
                    "sessions",
                    queryset=Session.objects.filter(
                        show_time__gte=timezone.now()
                    ).select_related("dome"),
                    to_attr="future_sessions"
                )
            )

        return queryset.distinct()


class PlanetariumDomeViewSet(viewsets.ModelViewSet):
    queryset = PlanetariumDome.objects.all()
    serializer_class = DomeSerializer

    def get_queryset(self):
        queryset = self.queryset
        if self.action == "retrieve":
            queryset = queryset.prefetch_related(
                Prefetch(
                    "sessions",
                    queryset=Session.objects.filter(
                        show_time__gte=timezone.now()
                    ).select_related("show"),
                    to_attr="future_sessions"
                )
            )

        return queryset

    def get_serializer_class(self):
        serializer = self.serializer_class
        if self.action == "retrieve":
            serializer = DomeRetrieveSerializer

        return serializer


class SessionViewSet(viewsets.ModelViewSet):
    queryset = Session.objects.all()
    serializer_class = SessionCreateSerializer

    def get_serializer_class(self):
        serializer = self.serializer_class
        if self.action == "list":
            serializer = SessionListSerializer
        if self.action == "retrieve":
            serializer = SessionRetrieveSerializer

        return serializer

    def get_queryset(self):
        queryset = self.queryset

        date_str = self.request.query_params.get("date")
        shows_ids = self.request.query_params.get("shows")
        domes_ids =self.request.query_params.get("domes")

        if shows_ids:
            shows_id = str_ids_to_int(str_ids=shows_ids)
            queryset = queryset.filter(
                show_id__in=shows_id
            )

        if domes_ids:
            domes_ids = str_ids_to_int(str_ids=domes_ids)
            queryset = queryset.filter(
                dome_id__in=domes_ids
            )

        if date_str:
            date = datetime.strptime(
                date_str,
                "%Y-%m-%d"
            )
            queryset = queryset.filter(
                show_time__date=date
            )

        if self.action in ("list", "retrieve",):
            queryset = queryset.select_related("dome", "show").annotate(
                seats_left=(
                    (F("dome__rows") * F("dome__seats_in_row")) - Count("tickets")
                )
            )

        return queryset.distinct()


class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all()
    serializer_class = OrderListSerializer

    def get_queryset(self):
        queryset = self.queryset
        queryset = queryset.filter(user=self.request.user)

        if self.action == "list":
            queryset = queryset.prefetch_related(
                Prefetch(
                    "tickets",
                    queryset=Ticket.objects.select_related(
                        "session__show", "session__dome"
                    ),
                )
            )
        return queryset

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def get_serializer_class(self):
        serializer = self.serializer_class
        if self.action == "create":
            serializer = OrderCreateSerializer

        return serializer
