"""Modelo de datos: partidas, rondas, jugadores por ronda y eventos."""

from __future__ import annotations

from django.db import models

ATTACK = "Attack"
DEFENSE = "Defense"

SIDE_CHOICES = [(ATTACK, "Ataque"), (DEFENSE, "Defensa")]


def match_result(won: bool | None, my_score: int, opponent_score: int) -> str:
    """Etiqueta del resultado. Fuera del modelo para poder usarla sobre filas
    de un `values()` sin instanciar el Match completo."""
    if won is None:
        return "incompleta"
    if my_score == opponent_score:
        return "empate"
    return "victoria" if won else "derrota"


class Player(models.Model):
    """Un jugador, identificado por su profileID de Ubisoft (estable)."""

    profile_id = models.CharField(max_length=64, unique=True)
    username = models.CharField(max_length=64, db_index=True)
    aliases = models.JSONField(default=list, blank=True)
    is_me = models.BooleanField(default=False, db_index=True)
    first_seen = models.DateTimeField(null=True, blank=True)
    last_seen = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["username"]

    def __str__(self) -> str:
        return self.username

    def note_alias(self, username: str) -> None:
        if username and username != self.username and username not in self.aliases:
            self.aliases.append(username)


class Match(models.Model):
    """Una partida completa (una carpeta Match-*)."""

    match_id = models.CharField(max_length=64, unique=True)
    folder = models.CharField(max_length=255)
    source_path = models.TextField(blank=True)
    played_at = models.DateTimeField(db_index=True)

    map_id = models.BigIntegerField(default=0)
    map_name = models.CharField(max_length=64, db_index=True)
    map_slug = models.CharField(max_length=64, db_index=True)
    match_type = models.CharField(max_length=32, blank=True)
    gamemode = models.CharField(max_length=32, blank=True)
    game_version = models.CharField(max_length=32, blank=True)
    code_version = models.BigIntegerField(default=0)

    rounds_count = models.IntegerField(default=0)
    my_team_index = models.IntegerField(default=0)
    my_score = models.IntegerField(default=0)
    opponent_score = models.IntegerField(default=0)
    # None cuando la partida quedo incompleta (replays faltantes)
    won = models.BooleanField(null=True, blank=True)

    parsed_at = models.DateTimeField(auto_now=True)
    parser_version = models.CharField(max_length=16, blank=True)
    warnings = models.JSONField(default=list, blank=True)

    class Meta:
        ordering = ["-played_at"]
        verbose_name_plural = "matches"

    def __str__(self) -> str:
        return f"{self.map_name} {self.my_score}-{self.opponent_score} ({self.played_at:%d-%m %H:%M})"

    @property
    def result(self) -> str:
        return match_result(self.won, self.my_score, self.opponent_score)


class Round(models.Model):
    """Una ronda (un archivo .rec)."""

    match = models.ForeignKey(Match, related_name="rounds", on_delete=models.CASCADE)
    number = models.IntegerField()
    overtime_number = models.IntegerField(default=0)
    file_name = models.CharField(max_length=255, blank=True)

    site = models.CharField(max_length=64, blank=True, db_index=True)
    my_side = models.CharField(max_length=8, choices=SIDE_CHOICES, blank=True, db_index=True)
    my_team_won = models.BooleanField(null=True, blank=True)
    win_condition = models.CharField(max_length=32, blank=True)
    win_condition_certain = models.BooleanField(default=True)

    score_before = models.JSONField(default=list, blank=True)  # [team0, team1]
    score_after = models.JSONField(default=list, blank=True)

    clock_start = models.FloatField(default=0)
    clock_end = models.FloatField(default=0)
    possible_plant = models.BooleanField(default=False)

    teams = models.JSONField(default=list, blank=True)

    class Meta:
        ordering = ["match__played_at", "number"]
        unique_together = [("match", "number")]

    def __str__(self) -> str:
        return f"{self.match.map_name} R{self.number + 1}"

    @property
    def duration(self) -> float:
        """Segundos jugados de la fase de accion."""
        return max(self.clock_start - self.clock_end, 0)


class RoundPlayer(models.Model):
    """Rendimiento de un jugador en una ronda, con las metricas derivadas."""

    round = models.ForeignKey(Round, related_name="players", on_delete=models.CASCADE)
    player = models.ForeignKey(Player, related_name="rounds", on_delete=models.CASCADE)
    username = models.CharField(max_length=64)
    team_index = models.IntegerField(default=0)
    side = models.CharField(max_length=8, choices=SIDE_CHOICES, blank=True, db_index=True)
    is_me = models.BooleanField(default=False, db_index=True)
    won = models.BooleanField(default=False)

    operator_id = models.BigIntegerField(default=0)
    operator = models.CharField(max_length=32, blank=True, db_index=True)
    spawn = models.CharField(max_length=64, blank=True)

    kills = models.IntegerField(default=0)
    died = models.BooleanField(default=False)
    headshots = models.IntegerField(default=0)
    assists = models.IntegerField(default=0)
    score = models.IntegerField(default=0)
    one_vx = models.IntegerField(default=0)

    # --- metricas derivadas
    opening_kill = models.BooleanField(default=False)
    opening_death = models.BooleanField(default=False)
    entry_kill = models.BooleanField(default=False)
    trade_kills = models.IntegerField(default=0)
    was_traded = models.BooleanField(default=False)
    untraded_death = models.BooleanField(default=False)
    death_clock = models.FloatField(null=True, blank=True)
    death_elapsed = models.FloatField(null=True, blank=True)
    survived = models.BooleanField(default=False)
    kst = models.BooleanField(default=False)  # kill, survive o trade

    class Meta:
        ordering = ["round", "team_index", "-kills"]
        unique_together = [("round", "player")]
        indexes = [
            models.Index(fields=["is_me", "side"]),
            models.Index(fields=["is_me", "operator"]),
        ]

    def __str__(self) -> str:
        return f"{self.username} @ {self.round}"

    @property
    def headshot_percentage(self) -> float:
        return (self.headshots / self.kills * 100) if self.kills else 0.0


class Event(models.Model):
    """Un evento del feed de la ronda (kill, muerte, cambio de operador...)."""

    KILL = "Kill"
    DEATH = "Death"

    round = models.ForeignKey(Round, related_name="events", on_delete=models.CASCADE)
    order = models.IntegerField(default=0)
    kind = models.CharField(max_length=32, db_index=True)
    clock = models.FloatField(default=0)
    clock_raw = models.CharField(max_length=16, blank=True)
    elapsed = models.FloatField(default=0)

    actor = models.ForeignKey(
        Player, null=True, blank=True, related_name="events_as_actor", on_delete=models.SET_NULL
    )
    actor_name = models.CharField(max_length=64, blank=True)
    target = models.ForeignKey(
        Player, null=True, blank=True, related_name="events_as_target", on_delete=models.SET_NULL
    )
    target_name = models.CharField(max_length=64, blank=True)

    headshot = models.BooleanField(null=True, blank=True)
    operator = models.CharField(max_length=32, blank=True)
    message = models.TextField(blank=True)
    traded = models.BooleanField(default=False)

    class Meta:
        ordering = ["round", "order"]

    def __str__(self) -> str:
        if self.kind == self.KILL:
            return f"{self.actor_name} -> {self.target_name} ({self.clock_raw})"
        return f"{self.kind} {self.actor_name} ({self.clock_raw})"


class ImportLog(models.Model):
    """Registro de cada intento de importacion, para el watcher y la UI."""

    folder = models.CharField(max_length=255, db_index=True)
    started_at = models.DateTimeField(auto_now_add=True)
    finished_at = models.DateTimeField(null=True, blank=True)
    ok = models.BooleanField(default=False)
    rounds_imported = models.IntegerField(default=0)
    message = models.TextField(blank=True)

    class Meta:
        ordering = ["-started_at"]

    def __str__(self) -> str:
        return f"{self.folder} {'ok' if self.ok else 'error'}"
