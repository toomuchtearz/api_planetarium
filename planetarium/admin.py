from django.contrib import admin

from planetarium.models import (
    Theme,
    Show,
    PlanetariumDome,
    Session,
    Order,
    Ticket

)


@admin.register(Theme)
class ThemeAdmin(admin.ModelAdmin):
    pass


@admin.register(Show)
class ShowAdmin(admin.ModelAdmin):
    pass


@admin.register(PlanetariumDome)
class PlanetariumDomeAdmin(admin.ModelAdmin):
    pass


@admin.register(Session)
class SessionDomeAdmin(admin.ModelAdmin):
    pass

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    pass

@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    pass
