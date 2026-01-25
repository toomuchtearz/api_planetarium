from django.db import models


class Theme(models.Model):
    name = models.CharField(max_length=64, unique=True)

    def __str__(self) -> str:
        return self.name


class Show(models.Model):
    title = models.CharField(max_length=64, unique=True)
    description = models.TextField()
    themes = models.ManyToManyField(Theme, related_name="shows")

    def __str__(self) -> str:
        return self.title


class PlanetariumDome(models.Model):
    name = models.CharField(max_length=64, unique=True)
    rows = models.IntegerField()
    seats_in_row = models.IntegerField()

    def __str__(self) -> str:
        return self.name


class Session(models.Model):
    show = models.ForeignKey(
        Show,
        on_delete=models.CASCADE,
        related_name="sessions",
    )
    dome = models.ForeignKey(
        PlanetariumDome, on_delete=models.CASCADE, related_name="sessions"
    )
    show_time = models.DateTimeField()

    class Meta:
        ordering = ["-show_time"]

    def __str__(self) -> str:
        return f"{self.show.title} {str(self.show_time)}"


class Order(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"Order dated {self.created_at}"
