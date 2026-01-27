from django.db import transaction
from django.db.models import Prefetch
from rest_framework import serializers

from planetarium.models import Theme, Show, PlanetariumDome, Session, Order, Ticket


class ThemeSerializer(serializers.ModelSerializer):

    class Meta:
        model = Theme
        fields = (
            "id",
            "name",
        )


class ShowSerializer(serializers.ModelSerializer):
    class Meta:
        model = Show
        fields = (
            "id",
            "title",
            "description",
            "themes",
        )


class ShowListSerializer(serializers.ModelSerializer):
    themes = serializers.StringRelatedField(many=True)

    class Meta:
        model = Show
        fields = (
            "id",
            "title",
            "description",
            "themes",
        )


class PlanetariumDomeSerializer(serializers.ModelSerializer):

    class Meta:
        model = PlanetariumDome
        fields = (
            "id",
            "name",
            "rows",
            "seats_in_row",
            "capacity",
        )


class SessionSerializer(serializers.ModelSerializer):

    class Meta:
        model = Session
        fields = ("id", "show", "dome", "show_time")


class SessionRetrieveSerializer(SessionSerializer):
    show = ShowListSerializer(read_only=True)
    dome = PlanetariumDomeSerializer(read_only=True)


class SessionListSerializer(serializers.ModelSerializer):
    show_title = serializers.StringRelatedField(source="show")
    dome_name = serializers.StringRelatedField(source="dome")
    dome_capacity = serializers.IntegerField(source="dome.capacity")

    class Meta:
        model = Session
        fields = ("id", "show_title", "dome_name", "dome_capacity", "show_time")


class TicketCreateSerializer(serializers.ModelSerializer):
    session = serializers.PrimaryKeyRelatedField(
        queryset=Session.objects.select_related("dome")
    )

    class Meta:
        model = Ticket
        fields = ("row", "seat", "session")

    def validate(self, attrs):
        Ticket.validate_row_and_seat(
            row=attrs["row"],
            num_rows=attrs["session"].dome.rows,
            seat=attrs["seat"],
            num_seats=attrs["session"].dome.seats_in_row,
            raised_error=serializers.ValidationError,
        )

        return super().validate(attrs)


class TicketListSerializer(serializers.ModelSerializer):
    show_title = serializers.StringRelatedField(source="session.show")
    dome = serializers.StringRelatedField(source="session.dome")
    show_time = serializers.DateTimeField(source="session.show_time")

    class Meta:
        model = Ticket
        fields = (
            "row",
            "seat",
            "show_title",
            "dome",
            "show_time",
        )


class OrderCreateSerializer(serializers.ModelSerializer):
    tickets = TicketCreateSerializer(many=True, read_only=False, allow_empty=False)

    class Meta:
        model = Order
        fields = (
            "id",
            "tickets",
            "created_at",
        )

    def validate(self, attrs):
        seat_set = set()
        for ticket in attrs["tickets"]:
            identifier = (ticket["session"].id, ticket["row"], ticket["seat"])
            if identifier in seat_set:
                raise serializers.ValidationError(
                    f"Duplicate ticket in order: Row {ticket['row']}, Seat {ticket['seat']}"
                )
            seat_set.add(identifier)

        return super().validate(attrs)

    def create(self, validated_data):
        with transaction.atomic():
            tickets_data = validated_data.pop("tickets")
            new_order = Order.objects.create(**validated_data)
            Ticket.objects.bulk_create(
                [Ticket(order=new_order, **ticket_data) for ticket_data in tickets_data]
            )

            return Order.objects.prefetch_related(
                Prefetch(
                    "tickets",
                    queryset=Ticket.objects.select_related(
                        "session__show", "session__dome"
                    ),
                )
            ).get(pk=new_order.pk)


class OrderListSerializer(serializers.ModelSerializer):
    tickets = TicketListSerializer(many=True, read_only=True)

    class Meta:
        model = Order
        fields = (
            "id",
            "tickets",
            "created_at",
        )


class SessionInlineSerializer(serializers.ModelSerializer):
    dome_name = serializers.StringRelatedField(source="dome")
    dome_capacity = serializers.IntegerField(source="dome.capacity")

    class Meta:
        model = Session
        fields = ("id", "dome_name", "dome_capacity", "show_time")


class ShowRetrieveSerializer(serializers.ModelSerializer):
    themes = ThemeSerializer(many=True, read_only=True)
    future_sessions = SessionInlineSerializer(many=True, read_only=True)

    class Meta:
        model = Show
        fields = (
            "id",
            "title",
            "description",
            "themes",
            "future_sessions",
        )
