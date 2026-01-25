from rest_framework import serializers

from planetarium.models import Theme, Show, PlanetariumDome


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
        )
