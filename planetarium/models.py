from django.db import models
from django.db.models.constraints import UniqueConstraint

from api_planetarium import settings


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

    @property
    def capacity(self) -> int:
        return self.rows * self.seats_in_row


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
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="orders"
    )

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"Order dated {self.created_at}"


class Ticket(models.Model):
    row = models.IntegerField()
    seat = models.IntegerField()
    session = models.ForeignKey(Session, on_delete=models.CASCADE, related_name="tickets")
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="tickets")

    class Meta:
        constraints = [
            UniqueConstraint(
                fields=["row", "seat", "session"],
                name="unique_row_seat_session_for_ticket"
            )
        ]

    def __str__(self) -> str:
        return f"Ticket for {self.session}"

    @staticmethod
    def validate_row_and_seat(
            row: int,
            num_rows: int,
            seat: int,
            num_seats: int,
            raised_error,
    ):
        if not (1 <= row <= num_rows):
            raise raised_error(
                {
                    "row": f"row must be in range [1, {num_rows}]"
                }
            )
        elif not (1 <= seat <= num_seats):
            raise raised_error(
                {
                    "seat": f"seat must be in range [1, {num_seats}]"
                }
            )
    def clean(self):
        self.validate_row_and_seat(
            row=self.row,
            num_rows=self.session.dome.rows,
            seat=self.seat,
            num_seats=self.session.dome.seats_in_row,
            raised_error=ValueError,
        )

    def save(
            self,
            *args,
            **kwargs,
    ):
        self.full_clean()
        return super().save()
