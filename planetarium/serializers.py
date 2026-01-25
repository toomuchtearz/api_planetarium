from rest_framework import serializers

from planetarium.models import Theme, Show


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
    themes = ThemeSerializer(many=True, read_only=True)
    class Meta:
        model = Show
        fields = (
            "id",
            "title",
            "description",
            "themes",
        )
