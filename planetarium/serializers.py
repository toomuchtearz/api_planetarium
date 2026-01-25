from rest_framework import serializers

from planetarium.models import Theme, Show, PlanetariumDome, Session


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


class ShowRetrieveSerializer(serializers.ModelSerializer):
    themes = ThemeSerializer(many=True, read_only=True)
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
        fields = (
            "id",
            "show",
            "dome",
            "show_time"
        )


class SessionRetrieveSerializer(SessionSerializer):
    show = ShowListSerializer(read_only=True)
    dome = PlanetariumDomeSerializer(read_only=True)


class SessionListSerializer(serializers.ModelSerializer):
    show_title = serializers.StringRelatedField(source="show")
    dome_name = serializers.StringRelatedField(source="dome")
    dome_capacity = serializers.IntegerField(source="dome.capacity")

    class Meta:
        model = Session
        fields = (
            "id",
            "show_title",
            "dome_name",
            "dome_capacity",
            "show_time"
        )
