"""Recalculo de trades y clutch sobre lo ya importado, sin reparsear los replays.

Los trades se guardan calculados al importar, asi que cambiar
`TRADE_WINDOW_SECONDS` no mueve nada por si solo. `clutch_vs` tambien se
rehace aca: las partidas importadas antes de que existiera la columna la
tienen en 0. Todo lo que hace falta para
rehacer el calculo esta en la base: los eventos con su reloj y los jugadores con
su equipo. No hay que abrir un solo `.rec`.

Las reglas no se reimplementan aca: se llama a las mismas
`metrics.annotate_trades` y `metrics.clutch_vs` que usa el import. Duplicarlas
significaria numeros distintos segun por donde pasaste.
"""

from __future__ import annotations

from dataclasses import dataclass

from django.db import transaction

from .analytics.metrics import KILL, annotate_trades, clutch_vs, trade_window
from .models import Event, Round, RoundPlayer

#: Campos que se recalculan: los que dependen de la ventana de trade y el clutch.
CAMPOS = ("was_traded", "trade_kills", "untraded_death", "kst", "clutch_vs")


@dataclass
class RecomputeResult:
    rounds: int = 0
    players_changed: int = 0
    events_changed: int = 0

    @property
    def changed(self) -> bool:
        return bool(self.players_changed or self.events_changed)


def _recompute_round(rnd: Round, window: float, dry_run: bool) -> tuple[int, int]:
    jugadores = list(rnd.players.all())
    eventos = list(rnd.events.all().order_by("order"))
    if not jugadores:
        return 0, 0

    team_of = {p.username: p.team_index for p in jugadores}
    metrics = {
        p.username: {
            "kills": p.kills,
            "died": p.died,
            "survived": p.survived,
            "was_traded": p.was_traded,
            "trade_kills": p.trade_kills,
        }
        for p in jugadores
    }
    kill_events = [
        {"actor": e.actor_name, "target": e.target_name, "clock": e.clock, "traded": e.traded}
        for e in eventos
        if e.kind == KILL
    ]

    annotate_trades(kill_events, team_of, metrics, window)
    clutch = clutch_vs(
        [{"kind": e.kind, "actor": e.actor_name, "target": e.target_name} for e in eventos],
        team_of,
    )
    for nick, vs in clutch.items():
        metrics[nick]["clutch_vs"] = vs

    cambiados = []
    for p in jugadores:
        nuevo = metrics[p.username]
        if any(getattr(p, campo) != nuevo[campo] for campo in CAMPOS):
            for campo in CAMPOS:
                setattr(p, campo, nuevo[campo])
            cambiados.append(p)

    eventos_kill = [e for e in eventos if e.kind == KILL]
    eventos_cambiados = [
        evento
        for evento, calculado in zip(eventos_kill, kill_events, strict=True)
        if evento.traded != calculado["traded"]
    ]
    for evento, calculado in zip(eventos_kill, kill_events, strict=True):
        evento.traded = calculado["traded"]

    if not dry_run:
        if cambiados:
            RoundPlayer.objects.bulk_update(cambiados, list(CAMPOS))
        if eventos_cambiados:
            Event.objects.bulk_update(eventos_cambiados, ["traded"])

    return len(cambiados), len(eventos_cambiados)


def recompute(*, window: float | None = None, dry_run: bool = False) -> RecomputeResult:
    """Rehace los trades y `clutch_vs` de todas las rondas importadas."""
    if window is None:
        window = trade_window()

    result = RecomputeResult()
    rondas = Round.objects.prefetch_related("players", "events")
    with transaction.atomic():
        for rnd in rondas.iterator(chunk_size=200):
            jugadores, eventos = _recompute_round(rnd, window, dry_run)
            result.rounds += 1
            result.players_changed += jugadores
            result.events_changed += eventos
    return result
