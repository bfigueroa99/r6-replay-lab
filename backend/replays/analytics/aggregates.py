"""Agregaciones sobre las rondas del jugador para alimentar la API."""

from __future__ import annotations

from datetime import date, timedelta

from django.conf import settings
from django.db.models import (
    Avg,
    Case,
    Count,
    Exists,
    ExpressionWrapper,
    F,
    FloatField,
    OuterRef,
    Q,
    QuerySet,
    Subquery,
    Sum,
    Value,
    When,
)

from ..models import Event, Match, Player, Round, RoundPlayer, match_result

# --------------------------------------------------------------------- filtros

FILTER_KEYS = (
    "side", "map", "operator", "site", "match_type", "since", "until", "ranked_only", "session",
)


def base_queryset(**filters) -> QuerySet[RoundPlayer]:
    """Rondas del jugador principal, con los filtros de la request aplicados."""
    qs = RoundPlayer.objects.filter(is_me=True).select_related("round", "round__match")

    if filters.get("side"):
        qs = qs.filter(side=filters["side"])
    if filters.get("map"):
        qs = qs.filter(round__match__map_slug=filters["map"])
    if filters.get("operator"):
        qs = qs.filter(operator=filters["operator"])
    if filters.get("site"):
        qs = qs.filter(round__site=filters["site"])
    if filters.get("match_type"):
        qs = qs.filter(round__match__match_type=filters["match_type"])
    if filters.get("ranked_only"):
        qs = qs.filter(round__match__match_type="Ranked")
    if filters.get("since"):
        qs = qs.filter(round__match__played_at__gte=filters["since"])
    if filters.get("until"):
        qs = qs.filter(round__match__played_at__lte=filters["until"])
    if filters.get("session") not in (None, ""):
        qs = qs.filter(round__match_id__in=session_match_ids(filters["session"]))
    return qs


# --------------------------------------------------------------------- helpers

# --------------------------------------------------------------------- rating

#: Puntos que aporta cada cosa en una ronda. Son un **juicio**, no una medicion:
#: estan puestos por el impacto que tiene cada evento en ganar la ronda, y se
#: dejan a la vista para que se puedan discutir y cambiar. La escala es relativa
#: a la baja, que vale 1.
RATING_WEIGHTS = {
    # piso para que una ronda mala no termine en negativo
    "base": 1.0,
    "kill": 1.0,
    # seguir vivo vale, pero mucho menos que una baja
    "survived": 0.3,
    # el primer duelo es el que mas mueve la ronda
    "opening_kill": 0.5,
    "opening_death": -0.5,
    # tradear es una baja que ademas deshace una perdida
    "trade_kill": 0.3,
    # la muerte mas cara: tu equipo queda con uno menos, gratis
    "untraded_death": -0.4,
    # cerrar la ronda solo es excepcional
    "clutch": 0.7,
}


def _peso(condicion: Q, peso: float):
    return Case(When(condicion, then=Value(peso)), default=Value(0.0), output_field=FloatField())


def rating_points_expr():
    """Puntos de una ronda, calculados en SQL.

    Es una funcion y no una constante a proposito: Django deja estado en las
    expresiones al resolverlas, y compartir una misma instancia entre dos
    consultas termina en "is an aggregate". Cada consulta arma la suya.
    """
    return ExpressionWrapper(
        Value(RATING_WEIGHTS["base"])
        + F("kills") * RATING_WEIGHTS["kill"]
        + F("trade_kills") * RATING_WEIGHTS["trade_kill"]
        + _peso(Q(survived=True), RATING_WEIGHTS["survived"])
        + _peso(Q(opening_kill=True), RATING_WEIGHTS["opening_kill"])
        + _peso(Q(opening_death=True), RATING_WEIGHTS["opening_death"])
        + _peso(Q(untraded_death=True), RATING_WEIGHTS["untraded_death"])
        + _peso(Q(one_vx__gt=0), RATING_WEIGHTS["clutch"]),
        output_field=FloatField(),
    )


def rating_baseline() -> float | None:
    """Los puntos promedio del jugador en **todo** su historial: el 1.00.

    Va sin filtros a proposito. Si el promedio se recalculara con cada filtro,
    el rating de un mapa y el de un operador no serian comparables entre si, que
    es justamente para lo unico que sirve este numero.
    """
    return RoundPlayer.objects.filter(is_me=True).aggregate(v=Avg(rating_points_expr()))["v"] or None


# Los alias no pueden repetir nombres de campos del modelo: si `kills` fuera a
# la vez alias y campo, Django no podria resolver los filtros que usan `kills`.
AGGREGATES = {
    "rounds": Count("id"),
    "rounds_won": Count("id", filter=Q(won=True)),
    "kills_sum": Sum("kills"),
    "deaths": Count("id", filter=Q(died=True)),
    "headshots_sum": Sum("headshots"),
    "survived_rounds": Count("id", filter=Q(survived=True)),
    "opening_kills": Count("id", filter=Q(opening_kill=True)),
    "opening_deaths": Count("id", filter=Q(opening_death=True)),
    "entry_kills": Count("id", filter=Q(entry_kill=True)),
    "trade_kills_sum": Sum("trade_kills"),
    "traded_deaths": Count("id", filter=Q(was_traded=True)),
    "untraded_deaths": Count("id", filter=Q(untraded_death=True)),
    "kst_rounds": Count("id", filter=Q(kst=True)),
    "clutch_rounds": Count("id", filter=Q(one_vx__gt=0)),
    "multikill_rounds": Count("id", filter=Q(kills__gte=2)),
    "triple_plus_rounds": Count("id", filter=Q(kills__gte=3)),
    "won_after_opening_kill": Count("id", filter=Q(opening_kill=True, won=True)),
    "won_after_opening_death": Count("id", filter=Q(opening_death=True, won=True)),
    "avg_death_elapsed": Avg("death_elapsed"),
    "rating_points": Avg(rating_points_expr()),
}


def _pct(part, whole) -> float | None:
    if not whole:
        return None
    return round(part / whole * 100, 1)


def _ratio(part, whole, digits: int = 2) -> float | None:
    if not whole:
        return None
    return round(part / whole, digits)


def derive(row: dict, baseline: float | None = None) -> dict:
    """Renombra los alias internos y agrega porcentajes, ratios y el rating."""
    rounds = row.get("rounds") or 0
    kills = row.pop("kills_sum", 0) or 0
    headshots = row.pop("headshots_sum", 0) or 0
    trade_kills = row.pop("trade_kills_sum", 0) or 0
    survived = row.pop("survived_rounds", 0) or 0
    traded = row.pop("traded_deaths", 0) or 0
    deaths = row.get("deaths") or 0
    ok = row.get("opening_kills") or 0
    od = row.get("opening_deaths") or 0
    duels = ok + od

    row.update(
        {
            "kills": kills,
            "deaths": deaths,
            "headshots": headshots,
            "trade_kills": trade_kills,
            "survived": survived,
            "traded": traded,
            "winrate": _pct(row.get("rounds_won") or 0, rounds),
            "kd": _ratio(kills, deaths),
            "kpr": _ratio(kills, rounds),
            "hs_pct": _pct(headshots, kills),
            "survival_pct": _pct(survived, rounds),
            "opening_duels": duels,
            "opening_winrate": _pct(ok, duels),
            "opening_duel_rate": _pct(duels, rounds),
            "kst_pct": _pct(row.get("kst_rounds") or 0, rounds),
            "untraded_death_pct": _pct(row.get("untraded_deaths") or 0, deaths),
            "traded_pct": _pct(traded, deaths),
            "multikill_pct": _pct(row.get("multikill_rounds") or 0, rounds),
            "clutch_pct": _pct(row.get("clutch_rounds") or 0, rounds),
            "winrate_after_opening_kill": _pct(row.get("won_after_opening_kill") or 0, ok),
            "winrate_after_opening_death": _pct(row.get("won_after_opening_death") or 0, od),
            "avg_death_elapsed": (
                round(row["avg_death_elapsed"], 1) if row.get("avg_death_elapsed") else None
            ),
        }
    )
    puntos = row.get("rating_points")
    row["rating_points"] = round(puntos, 3) if puntos is not None else None
    row["rating"] = _ratio(puntos, baseline) if (puntos is not None and baseline) else None
    return row


def totals(qs: QuerySet[RoundPlayer], baseline: float | None = None) -> dict:
    row = dict(qs.aggregate(**AGGREGATES))
    row["matches"] = qs.values("round__match_id").distinct().count()
    return derive(row, baseline if baseline is not None else rating_baseline())


def group_by(qs: QuerySet[RoundPlayer], *fields: str, labels: tuple[str, ...] | None = None,
             min_rounds: int = 1, order: str = "-rounds",
             baseline: float | None = None) -> list[dict]:
    """Agrupa por uno o mas campos y devuelve filas con metricas derivadas."""
    labels = labels or fields
    if baseline is None:
        baseline = rating_baseline()
    rows = []
    for raw in qs.values(*fields).annotate(**AGGREGATES).order_by(order):
        if (raw.get("rounds") or 0) < min_rounds:
            continue
        row = dict(raw)
        for field, label in zip(fields, labels):
            row[label] = row.pop(field)
        rows.append(derive(row, baseline))
    return rows


# --------------------------------------------------------------------- vistas

def overview(**filters) -> dict:
    qs = base_queryset(**filters)
    baseline = rating_baseline()
    attack = totals(qs.filter(side="Attack"), baseline)
    defense = totals(qs.filter(side="Defense"), baseline)
    return {
        "overall": totals(qs, baseline),
        "attack": attack,
        "defense": defense,
        "recent_form": recent_form(**filters),
    }


#: Campos de Match que viajan en el group by de `recent_form`. Todos dependen
#: funcionalmente del match, asi que agruparlos no cambia las filas.
_MATCH_FIELDS = (
    "round__match_id",
    "round__match__played_at",
    "round__match__map_name",
    "round__match__my_score",
    "round__match__opponent_score",
    "round__match__won",
)


def recent_form(limit: int = 10, **filters) -> list[dict]:
    """Ultimas partidas: resultado y aporte propio."""
    qs = base_queryset(**filters)
    baseline = rating_baseline()
    out = []
    for raw in (
        qs.values(*_MATCH_FIELDS).annotate(**AGGREGATES).order_by("-round__match__played_at")[:limit]
    ):
        row = derive(dict(raw), baseline)
        my_score = row["round__match__my_score"]
        opp_score = row["round__match__opponent_score"]
        won = row["round__match__won"]
        out.append(
            {
                "id": row["round__match_id"],
                "map": row["round__match__map_name"],
                "played_at": row["round__match__played_at"].isoformat(),
                "score": f"{my_score}-{opp_score}",
                "result": match_result(won, my_score, opp_score),
                "won": won,
                "kills": row["kills"],
                "deaths": row["deaths"],
                "kd": row["kd"],
                "rating": row["rating"],
                "rounds": row["rounds"],
            }
        )
    return out


def by_map(min_rounds: int = 1, **filters) -> list[dict]:
    qs = base_queryset(**filters)
    rows = group_by(
        qs,
        "round__match__map_name",
        "round__match__map_slug",
        labels=("map", "slug"),
        min_rounds=min_rounds,
    )
    # winrate por lado dentro de cada mapa
    sides = {
        (r["map"], r["side"]): r
        for r in group_by(qs, "round__match__map_name", "side", labels=("map", "side"))
    }
    for row in rows:
        for side in ("Attack", "Defense"):
            s = sides.get((row["map"], side))
            row[f"{side.lower()}_winrate"] = s["winrate"] if s else None
            row[f"{side.lower()}_rounds"] = s["rounds"] if s else 0
    return rows


def by_site(min_rounds: int = 1, **filters) -> list[dict]:
    qs = base_queryset(**filters).exclude(round__site="")
    return group_by(
        qs,
        "round__match__map_name",
        "round__site",
        labels=("map", "site"),
        min_rounds=min_rounds,
    )


def by_operator(min_rounds: int = 1, **filters) -> list[dict]:
    qs = base_queryset(**filters).exclude(operator="")
    return group_by(qs, "operator", "side", labels=("operator", "side"), min_rounds=min_rounds)


def by_spawn(min_rounds: int = 1, **filters) -> list[dict]:
    """Solo tiene sentido en ataque: el spawn es la posicion de inicio."""
    qs = base_queryset(**filters).filter(side="Attack").exclude(spawn="")
    return group_by(
        qs,
        "round__match__map_name",
        "spawn",
        labels=("map", "spawn"),
        min_rounds=min_rounds,
    )


def by_round_number(**filters) -> list[dict]:
    qs = base_queryset(**filters)
    return group_by(qs, "round__number", labels=("round_number",), order="round__number")


def trend_by_day(**filters) -> list[dict]:
    qs = base_queryset(**filters)
    baseline = rating_baseline()
    rows = []
    for raw in (
        qs.values("round__match__played_at__date").annotate(**AGGREGATES).order_by(
            "round__match__played_at__date"
        )
    ):
        row = dict(raw)
        day = row.pop("round__match__played_at__date")
        row["day"] = day.isoformat() if isinstance(day, date) else str(day)
        rows.append(derive(row, baseline))
    return rows


def trend_by_match(limit: int = 40, **filters) -> list[dict]:
    """Serie por partida, en orden cronologico, para ver evolucion."""
    qs = base_queryset(**filters)
    baseline = rating_baseline()
    rows = []
    for raw in (
        qs.values(
            "round__match_id", "round__match__played_at", "round__match__map_name"
        )
        .annotate(**AGGREGATES)
        .order_by("-round__match__played_at")[:limit]
    ):
        row = dict(raw)
        row["match_id"] = row.pop("round__match_id")
        row["played_at"] = row.pop("round__match__played_at").isoformat()
        row["map"] = row.pop("round__match__map_name")
        rows.append(derive(row, baseline))
    return list(reversed(rows))


def teammate_synergy(min_rounds: int = 10, **filters) -> list[dict]:
    """Winrate de rondas segun con quien las jugaste (solo companeros).

    El nombre sale de Player y no de RoundPlayer: si alguien se cambio el nick
    a mitad del historial sigue siendo una sola fila.
    """
    # Correlacionada en vez de un IN con todos los round_id: con un historial
    # largo esa lista se vuelve enorme y SQLite tiene tope de parametros.
    me_in_round = base_queryset(**filters).filter(
        round_id=OuterRef("round_id"), team_index=OuterRef("team_index")
    )
    rows = (
        RoundPlayer.objects.filter(is_me=False)
        .filter(Exists(me_in_round))
        .values("player_id", "player__username")
        .annotate(
            rounds=Count("id"),
            rounds_won=Count("id", filter=Q(won=True)),
            kills=Sum("kills"),
        )
        .filter(rounds__gte=min_rounds)
        .order_by("-rounds", "player__username")
    )
    return [
        {
            "player_id": r["player_id"],
            "username": r["player__username"],
            "rounds": r["rounds"],
            "rounds_won": r["rounds_won"],
            "kills": r["kills"] or 0,
            "kpr": _ratio(r["kills"] or 0, r["rounds"]),
            "winrate": _pct(r["rounds_won"], r["rounds"]),
        }
        for r in rows
    ]


def clutch_detail(**filters) -> list[dict]:
    qs = base_queryset(**filters).filter(one_vx__gt=0).order_by("-round__match__played_at")
    return [
        {
            "match_id": rp.round.match_id,
            "match": rp.round.match.map_name,
            "played_at": rp.round.match.played_at.isoformat(),
            "round": rp.round.number + 1,
            "site": rp.round.site,
            "side": rp.side,
            "operator": rp.operator,
            "vs": rp.one_vx,
            "kills": rp.kills,
        }
        for rp in qs[:50]
    ]


# --------------------------------------------------------------------- sesiones


def _sessions_raw() -> list[dict]:
    """Sesiones de juego, de la mas nueva a la mas vieja.

    Una sesion se corta cuando pasan mas de `SESSION_GAP_MINUTES` sin jugar. Se
    calcula sobre **todas** las partidas y no sobre las filtradas: si filtras por
    mapa, esa partida sigue siendo la tercera de su noche.
    """
    gap = timedelta(minutes=settings.SESSION_GAP_MINUTES)
    sesiones: list[dict] = []
    for match_id, played_at in Match.objects.order_by("played_at").values_list(
        "id", "played_at"
    ):
        if not sesiones or played_at - sesiones[-1]["end"] > gap:
            sesiones.append({"start": played_at, "end": played_at, "match_ids": []})
        sesiones[-1]["end"] = played_at
        sesiones[-1]["match_ids"].append(match_id)

    sesiones.reverse()  # la mas reciente primero: es la que interesa mirar
    for i, sesion in enumerate(sesiones):
        sesion["index"] = i
    return sesiones


def session_match_ids(index) -> list[int]:
    """Partidas de una sesion. 0 es la mas reciente."""
    try:
        index = int(index)
    except (TypeError, ValueError):
        return []
    sesiones = _sessions_raw()
    if 0 <= index < len(sesiones):
        return sesiones[index]["match_ids"]
    return []


def session_options(limit: int = 30) -> list[dict]:
    """Sesiones para el selector de la barra de filtros."""
    return [
        {"index": s["index"], "start": s["start"].isoformat(), "matches": len(s["match_ids"])}
        for s in _sessions_raw()[:limit]
    ]


def _position_map() -> dict[int, int]:
    """match_id -> si fue la 1a, 2a, 3a... partida de su sesion."""
    return {
        match_id: posicion
        for sesion in _sessions_raw()
        for posicion, match_id in enumerate(sesion["match_ids"], start=1)
    }


#: Claves de AGGREGATES que son promedios y no sumas: al plegar filas hay que
#: ponderarlas por su muestra en vez de sumarlas.
_PROMEDIOS = {"avg_death_elapsed": "deaths", "rating_points": "rounds"}


def _fold(rows: list[dict], baseline: float | None = None) -> dict:
    """Suma filas ya agregadas por partida en una sola.

    Todo es conteo o suma menos los promedios de `_PROMEDIOS`, que se ponderan
    por su muestra en vez de promediar promedios.
    """
    total = {clave: 0 for clave in AGGREGATES if clave not in _PROMEDIOS}
    acumulado = {clave: [0.0, 0.0] for clave in _PROMEDIOS}  # [suma, peso]
    for row in rows:
        for clave in total:
            total[clave] += row.get(clave) or 0
        for clave, campo_peso in _PROMEDIOS.items():
            peso = row.get(campo_peso) or 0
            if row.get(clave) is not None and peso:
                acumulado[clave][0] += row[clave] * peso
                acumulado[clave][1] += peso
    for clave, (suma, peso) in acumulado.items():
        total[clave] = (suma / peso) if peso else None
    return derive(total, baseline if baseline is not None else rating_baseline())


def _por_partida(**filters) -> dict[int, dict]:
    qs = base_queryset(**filters)
    return {
        row["round__match_id"]: row
        for row in qs.values("round__match_id").annotate(**AGGREGATES)
    }


def sessions(limit: int = 30, **filters) -> list[dict]:
    """Resumen de cada sesion de juego, de la mas reciente hacia atras."""
    por_partida = _por_partida(**filters)
    salida = []
    for sesion in _sessions_raw()[:limit]:
        filas = [por_partida[mid] for mid in sesion["match_ids"] if mid in por_partida]
        if not filas:
            continue
        fila = _fold(filas)
        fila.update(
            {
                "index": sesion["index"],
                "start": sesion["start"].isoformat(),
                "end": sesion["end"].isoformat(),
                "matches": len(filas),
                "hours": round(
                    (sesion["end"] - sesion["start"]).total_seconds() / 3600, 1
                ),
            }
        )
        salida.append(fila)
    return salida


def by_session_position(max_position: int = 5, **filters) -> list[dict]:
    """Rendimiento segun si fue tu 1a, 2a, 3a... partida de la sesion.

    De `max_position` en adelante se juntan en un solo tramo: las sesiones
    largas son pocas y cada posicion suelta no junta muestra.
    """
    posiciones = _position_map()
    buckets: dict[int, list[dict]] = {}
    for match_id, row in _por_partida(**filters).items():
        posicion = posiciones.get(match_id)
        if not posicion:
            continue
        buckets.setdefault(min(posicion, max_position), []).append(row)

    salida = []
    for posicion in sorted(buckets):
        fila = _fold(buckets[posicion])
        fila.update(
            {
                "position": posicion,
                "label": f"{posicion}a" if posicion < max_position else f"{max_position}a+",
                "matches": len(buckets[posicion]),
            }
        )
        salida.append(fila)
    return salida


# --------------------------------------------------------------------- duelos

#: El equipo del jugador en la ronda del evento.
_MI_EQUIPO = Subquery(
    RoundPlayer.objects.filter(round_id=OuterRef("round_id"), is_me=True).values("team_index")[:1]
)

#: Primer evento de baja de la ronda: el que define el duelo de apertura.
_PRIMER_EVENTO = Subquery(
    Event.objects.filter(
        kind__in=(Event.KILL, Event.DEATH), round_id=OuterRef("round_id")
    )
    .order_by("order")
    .values("id")[:1]
)


def _mis_bajas(mine: QuerySet[RoundPlayer]) -> QuerySet[Event]:
    """Eventos de baja de las rondas que pasan los filtros."""
    return Event.objects.filter(kind=Event.KILL).filter(
        Exists(mine.filter(round_id=OuterRef("round_id")))
    )


def _solo_rivales(qs: QuerySet[Event], campo: str) -> QuerySet[Event]:
    """Descarta los teamkills: el otro tiene que estar en el equipo contrario.

    Importa porque la misma persona puede ser companero en unas rondas y rival
    en otras, y matarte por error no es ganarte un duelo.
    """
    return (
        qs.annotate(
            mi_equipo=_MI_EQUIPO,
            equipo_rival=Subquery(
                RoundPlayer.objects.filter(
                    round_id=OuterRef("round_id"), player_id=OuterRef(campo)
                ).values("team_index")[:1]
            ),
            op_rival=Subquery(
                RoundPlayer.objects.filter(
                    round_id=OuterRef("round_id"), player_id=OuterRef(campo)
                ).values("operator")[:1]
            ),
        )
        .exclude(equipo_rival=None)
        .exclude(equipo_rival=F("mi_equipo"))
    )


def _me_ids() -> list[int]:
    return list(Player.objects.filter(is_me=True).values_list("id", flat=True))


def _duelos(mine: QuerySet[RoundPlayer], me_ids: list[int]):
    """Las dos direcciones del duelo: los que me matan y los que mato."""
    base = _mis_bajas(mine)
    contra_mi = _solo_rivales(base.filter(target_id__in=me_ids), "actor_id")
    a_favor = _solo_rivales(base.filter(actor_id__in=me_ids), "target_id")
    return contra_mi, a_favor


def nemesis(min_duels: int = 3, **filters) -> list[dict]:
    """Duelos contra cada rival: quien te gana, a quien le ganas.

    Se agrupa por jugador (profileID) y no por el nick de esa ronda. En ranked
    solo casi nadie se repite: con pocos duelos esto es anecdota, no patron, y
    por eso el coach pide mucha mas muestra que la tabla.
    """
    me_ids = _me_ids()
    if not me_ids:
        return []
    contra_mi, a_favor = _duelos(base_queryset(**filters), me_ids)

    rows: dict[int, dict] = {}

    def sumar(qs, id_field: str, name_field: str, clave: str) -> None:
        for raw in qs.values(id_field, name_field).annotate(n=Count("id")):
            pid = raw[id_field]
            if pid is None or pid in me_ids:
                continue
            fila = rows.setdefault(
                pid,
                {
                    "player_id": pid,
                    "username": raw[name_field],
                    "deaths": 0,
                    "kills": 0,
                    "opening_deaths": 0,
                    "opening_kills": 0,
                },
            )
            fila[clave] = raw["n"]

    sumar(contra_mi, "actor_id", "actor__username", "deaths")
    sumar(a_favor, "target_id", "target__username", "kills")
    sumar(contra_mi.filter(id=_PRIMER_EVENTO), "actor_id", "actor__username", "opening_deaths")
    sumar(a_favor.filter(id=_PRIMER_EVENTO), "target_id", "target__username", "opening_kills")

    salida = []
    for fila in rows.values():
        duels = fila["deaths"] + fila["kills"]
        if duels < min_duels:
            continue
        aperturas = fila["opening_deaths"] + fila["opening_kills"]
        fila.update(
            {
                "duels": duels,
                "balance": fila["kills"] - fila["deaths"],
                "winrate": _pct(fila["kills"], duels),
                "opening_duels": aperturas,
                "opening_winrate": _pct(fila["opening_kills"], aperturas),
                "maps": [],
            }
        )
        salida.append(fila)

    _agregar_mapas(salida, contra_mi, a_favor)
    return sorted(salida, key=lambda r: (-r["duels"], r["balance"], r["username"]))


def _agregar_mapas(salida: list[dict], contra_mi, a_favor) -> None:
    """En que mapas te cruzaste con cada rival. Solo para los que sobrevivieron."""
    if not salida:
        return
    ids = [fila["player_id"] for fila in salida]
    mapas: dict[int, set] = {pid: set() for pid in ids}
    for qs, campo in ((contra_mi, "actor_id"), (a_favor, "target_id")):
        for pid, nombre in qs.filter(**{f"{campo}__in": ids}).values_list(
            campo, "round__match__map_name"
        ):
            if nombre:
                mapas[pid].add(nombre)
    for fila in salida:
        fila["maps"] = sorted(mapas[fila["player_id"]])


def duel_totals(**filters) -> dict:
    """Tu balance global de duelos, que es la referencia de las tablas."""
    me_ids = _me_ids()
    if not me_ids:
        return {"kills": 0, "deaths": 0, "duels": 0, "winrate": None}
    contra_mi, a_favor = _duelos(base_queryset(**filters), me_ids)
    deaths = contra_mi.count()
    kills = a_favor.count()
    return {
        "kills": kills,
        "deaths": deaths,
        "duels": kills + deaths,
        "winrate": _pct(kills, kills + deaths),
    }


def duels_by_operator(min_duels: int = 3, **filters) -> list[dict]:
    """Contra que operadores pierdes y ganas los duelos.

    El operador sale del `RoundPlayer` del rival en esa ronda: el kill feed del
    `.rec` no trae el operador en el evento.
    """
    me_ids = _me_ids()
    if not me_ids:
        return []
    contra_mi, a_favor = _duelos(base_queryset(**filters), me_ids)

    rows: dict[str, dict] = {}

    def sumar(qs, clave: str) -> None:
        for raw in qs.exclude(op_rival="").values("op_rival").annotate(n=Count("id")):
            nombre = raw["op_rival"]
            if not nombre:
                continue
            fila = rows.setdefault(nombre, {"operator": nombre, "deaths": 0, "kills": 0})
            fila[clave] = raw["n"]

    sumar(contra_mi, "deaths")
    sumar(a_favor, "kills")

    salida = []
    for fila in rows.values():
        duels = fila["deaths"] + fila["kills"]
        if duels < min_duels:
            continue
        fila.update(
            {
                "duels": duels,
                "balance": fila["kills"] - fila["deaths"],
                "winrate": _pct(fila["kills"], duels),
            }
        )
        salida.append(fila)
    return sorted(salida, key=lambda r: (-r["duels"], r["operator"]))


def data_health(**filters) -> dict:
    """Que tan completa es la data importada (para no mentirle a la UI)."""
    qs = base_queryset(**filters)
    rounds = Round.objects.filter(players__in=qs).distinct()
    return {
        "rounds": qs.count(),
        # con filtros activos, contar todos los Match reportaria partidas
        # que no estan en la muestra que se esta mirando
        "matches": qs.values("round__match_id").distinct().count(),
        "rounds_without_site": rounds.filter(site="").count(),
        "rounds_uncertain_win_condition": rounds.filter(win_condition_certain=False).count(),
        "rounds_possible_plant": rounds.filter(possible_plant=True).count(),
        "assists_available": qs.filter(assists__gt=0).exists(),
        "score_available": qs.filter(score__gt=0).exists(),
    }
