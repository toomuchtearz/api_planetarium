from datetime import datetime

from django.db.models import Prefetch, F, Count
from django.utils import timezone
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema, OpenApiParameter
from rest_framework import viewsets, status
from rest_framework.decorators import action, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from planetarium.models import (
    Theme,
    Show,
    PlanetariumDome,
    Session,
    Order,
    Ticket
)
from planetarium.permissions import IsAdminOrIfAuthenticatedReadOnly

from planetarium.serializers import (
    ThemeSerializer,
    ShowListSerializer,
    ShowRetrieveSerializer,
    DomeSerializer,
    SessionListSerializer,
    SessionRetrieveSerializer,
    OrderCreateSerializer,
    OrderSerializer,
    ThemeRetrieveSerializer,
    ShowCreateSerializer,
    DomeRetrieveSerializer,
    SessionCreateSerializer,
    ShowImageSerializer,
)


def str_ids_to_int(str_ids):
    try:
        return [int(str_id) for str_id in str_ids.split(",")]
    except ValueError:
        return []


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
        elif self.action == "upload_image":
            serializer = ShowImageSerializer
        return serializer

    def get_queryset(self):
        queryset = self.queryset

        themes_id = self.request.query_params.get("themes")
        title = self.request.query_params.get("title")

        if themes_id:
            themes_ids = str_ids_to_int(str_ids=themes_id)
            queryset = queryset.filter(themes__id__in=themes_ids)

        if title:
            queryset = queryset.filter(title__icontains=title)

        if self.action == "list":
            queryset = queryset.prefetch_related("themes")

        elif self.action == "retrieve":
            queryset = queryset.prefetch_related(
                "themes",
                Prefetch(
                    "sessions",
                    queryset=Session.objects.filter(
                        show_time__gte=timezone.now()
                    ).select_related("dome"),
                    to_attr="future_sessions",
                ),
            )

        return queryset.distinct()

    @extend_schema(
        description="Upload an image for a specific show.",
        request={
            "multipart/form-data": {
                "type": "object",
                "properties": {
                    "image": {
                        "type": "string",
                        "format": "binary",
                    }
                },
            }
        },
    )
    @action(
        methods=["POST"],
        detail=True,
        url_path="upload-image",
    )
    def upload_image(self, request, pk=None):
        show = self.get_object()
        serializer = self.get_serializer(show, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(data=serializer.data, status=status.HTTP_200_OK)

    @extend_schema(
        parameters=[
            OpenApiParameter(
                "title",
                type=OpenApiTypes.STR,
                description="Filter by show title (ex. ?title=abc)",
            ),
            OpenApiParameter(
                "themes",
                type=OpenApiTypes.INT,
                many=True,
                description="Filter by theme IDs (ex. ?themes=1,2)",
                explode=False,
            ),
        ]
    )
    def list(self, request, *args, **kwargs):
        """Get list of shows."""
        return super().list(request, *args, **kwargs)

class PlanetariumDomeViewSet(viewsets.ModelViewSet):
    queryset = PlanetariumDome.objects.all()
    serializer_class = DomeSerializer

    def get_queryset(self):
        queryset = self.queryset

        name = self.request.query_params.get("name")

        if name:
            queryset = queryset.filter(name__icontains=name)

        if self.action == "retrieve":
            queryset = queryset.prefetch_related(
                Prefetch(
                    "sessions",
                    queryset=Session.objects.filter(
                        show_time__gte=timezone.now()
                    ).select_related("show"),
                    to_attr="future_sessions",
                )
            )

        return queryset

    def get_serializer_class(self):
        serializer = self.serializer_class
        if self.action == "retrieve":
            serializer = DomeRetrieveSerializer

        return serializer

    @extend_schema(
        parameters=[
            OpenApiParameter(
                "name",
                type=OpenApiTypes.STR,
                description="Filter by dome name (ex. ?title=alpha)",
            ),
        ]
    )
    def list(self, request, *args, **kwargs):
        """Get list of domes."""
        return super().list(request, *args, **kwargs)


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
        domes_ids = self.request.query_params.get("domes")

        if shows_ids:
            shows_id = str_ids_to_int(str_ids=shows_ids)
            queryset = queryset.filter(show_id__in=shows_id)

        if domes_ids:
            domes_ids = str_ids_to_int(str_ids=domes_ids)
            queryset = queryset.filter(dome_id__in=domes_ids)

        if date_str:
            try:
                date = datetime.strptime(date_str, "%Y-%m-%d").date()
                queryset = queryset.filter(show_time__date=date)
            except ValueError:
                pass

        if self.action in (
            "list",
            "retrieve",
        ):
            queryset = (
                queryset.select_related("dome", "show")
                .prefetch_related("show__themes")
                .annotate(
                    seats_left=(
                        (
                            F("dome__rows")
                            * F("dome__seats_in_row")
                        )
                        - Count("tickets")
                    )
                )
            )

        return queryset.distinct()

    @extend_schema(
        parameters=[
            OpenApiParameter(
                "date",
                type=OpenApiTypes.DATE,
                description="Filter by session date (ex. ?date=2022-12-12)",
            ),

            OpenApiParameter(
                "shows",
                type=OpenApiTypes.INT,
                many=True,
                description="Filter by show IDs (ex. ?shows=1,2)",
                explode=False,
            ),

            OpenApiParameter(
                "domes",
                type=OpenApiTypes.INT,
                many=True,
                description="Filter by dome IDs (ex. ?domes=1,2)",
                explode=False,
            )
        ]
    )
    def list(self, request, *args, **kwargs):
        """Get list of sessions."""
        return super().list(request, *args, **kwargs)


class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        queryset = self.queryset
        queryset = queryset.filter(user=self.request.user)

        creation_date_str = self.request.query_params.get("creation_date")

        if creation_date_str:
            try:
                creation_date = datetime.strptime(
                    creation_date_str, "%Y-%m-%d"
                ).date()
                queryset = queryset.filter(created_at__date=creation_date)
            except ValueError:
                pass

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

    @extend_schema(
        parameters=[
            OpenApiParameter(
                "creation_date",
                type=OpenApiTypes.DATE,
                description=(
                        "Filter by order creation date "
                        "(ex. ?creation_date=2022-12-12)"
                ),
            ),
        ]
    )
    def list(self, request, *args, **kwargs):
        """Get list of orders."""
        return super().list(request, *args, **kwargs)
