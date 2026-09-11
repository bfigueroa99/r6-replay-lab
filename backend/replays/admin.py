"""Admin de Django: util para revisar datos crudos sin escribir SQL."""

from django.contrib import admin

from .models import Event, ImportLog, Match, Player, Round, RoundPlayer


@admin.register(Player)
class PlayerAdmin(admin.ModelAdmin):
    list_display = ("username", "profile_id", "is_me", "last_seen")
    list_filter = ("is_me",)
    search_fields = ("username", "profile_id")


@admin.register(Match)
class MatchAdmin(admin.ModelAdmin):
    list_display = ("played_at", "map_name", "match_type", "my_score", "opponent_score", "won")
    list_filter = ("map_name", "match_type", "won")
    date_hierarchy = "played_at"


class RoundPlayerInline(admin.TabularInline):
    model = RoundPlayer
    extra = 0
    fields = (
        "username", "side", "operator", "kills", "died",
        "opening_kill", "opening_death", "kst",
    )
    readonly_fields = fields


@admin.register(Round)
class RoundAdmin(admin.ModelAdmin):
    list_display = ("match", "number", "site", "my_side", "my_team_won", "win_condition")
    list_filter = ("my_side", "my_team_won", "site")
    inlines = [RoundPlayerInline]


@admin.register(RoundPlayer)
class RoundPlayerAdmin(admin.ModelAdmin):
    list_display = ("username", "round", "side", "operator", "kills", "died", "kst")
    list_filter = ("is_me", "side", "operator")
    search_fields = ("username",)


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ("round", "order", "kind", "clock_raw", "actor_name", "target_name", "headshot")
    list_filter = ("kind", "headshot")


@admin.register(ImportLog)
class ImportLogAdmin(admin.ModelAdmin):
    list_display = ("folder", "started_at", "ok", "rounds_imported")
    list_filter = ("ok",)
