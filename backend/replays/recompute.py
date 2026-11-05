"""Recalculo de bajas, trades, clutch y 1vX sobre lo ya importado, sin reparsear los replays.

Los trades se guardan calculados al importar, asi que cambiar
`TRADE_WINDOW_SECONDS` no mueve nada por si solo. `clutch_vs` tambien se
rehace aca: las partidas importadas antes de que existiera la columna la
tienen en 0. `one_vx` se rehace porque quien se fue (`PlayerLeave`) ya no
cuenta como vivo (ficha 69); `Round.teams` guarda quien gano. Todo lo que hace falta para
rehacer el calculo esta en la base: los eventos con su reloj y los jugadores con
su equipo. No hay que abrir un solo `.rec`.

Tambien rehace `Match.won` con la regla del tipo de partida: una partida
importada con un `.rec` faltante pudo quedar como victoria o derrota con un
marcador que la regla no cierra. Marcador, tipo y version estan en `Match`.

Las reglas no se reimplementan aca: se llama a las mismas
`metrics.bajas_a_rivales`, `metrics.annotate_trades` (tambien marca la
apertura devuelta), `metrics.clutch_vs`, `metrics.one_vx` y
`reglas_partida.resultado` que usa el import. Duplicarlas significaria
numeros distintos segun por donde pasaste.
"""

from __future__ import annotations

from dataclasses import dataclass

from django.db import transaction

from .analytics.metrics import (
    KILL,
    annotate_trades,
    bajas_a_rivales,
    clutch_vs,
    equipo_ganador,
    one_vx,
    trade_window,
)
from .analytics.reglas_partida import regla_para, resultado
from .models import Event, Match, Round, RoundPlayer

#: Campos que se recalculan: bajas, los que dependen de la ventana de trade (con la
#: apertura devuelta) y el clutch.
CAMPOS = (
    "kills", "headshots", "was_traded", "trade_kills", "untraded_death", "kst", "clutch_vs",
    "one_vx", "opening_kill_traded",
)


@dataclass
class RecomputeResult:
    rounds: int = 0
    players_changed: int = 0
    events_changed: int = 0
    matches_changed: int = 0

    @property
    def changed(self) -> bool:
        return bool(self.players_changed or self.events_changed or self.matches_changed)


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
            "opening_kill": p.opening_kill,
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

    planos = [
        {"kind": e.kind, "actor": e.actor_name, "target": e.target_name, "headshot": e.headshot}
        for e in eventos
    ]
    # antes de los trades: `kst` sale de `kills`
    for nick, bajas in bajas_a_rivales(planos, team_of).items():
        metrics[nick].update(bajas)

    annotate_trades(kill_events, team_of, metrics, window)
    clutch = clutch_vs(planos, team_of)
    for nick, vs in clutch.items():
        metrics[nick]["clutch_vs"] = vs
    for nick, vx in one_vx(planos, team_of, equipo_ganador(rnd.teams)).items():
        metrics[nick]["one_vx"] = vx

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


def _recompute_resultados(dry_run: bool) -> int:
    partidas = Match.objects.only(
        "id", "match_type", "code_version", "my_score", "opponent_score", "won"
    )
    cambiadas = []
    for m in partidas.iterator(chunk_size=500):
        won = resultado(m.my_score, m.opponent_score, regla_para(m.match_type, m.code_version))
        if won != m.won:
            m.won = won
            cambiadas.append(m)
    if cambiadas and not dry_run:
        Match.objects.bulk_update(cambiadas, ["won"])
    return len(cambiadas)


def recompute(*, window: float | None = None, dry_run: bool = False) -> RecomputeResult:
    """Rehace las bajas, los trades, `clutch_vs` y `one_vx` de todas las rondas importadas.

    Tambien saca los teamkills de `kills` y `headshots` y rehace `Match.won`.
    """
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
        result.matches_changed = _recompute_resultados(dry_run)
    return result
