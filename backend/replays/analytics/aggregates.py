"""Agregaciones sobre las rondas del jugador para alimentar la API."""

from __future__ import annotations

from datetime import date

from django.db.models import Avg, Count, Q, QuerySet, Sum

from ..models import Match, Round, RoundPlayer

# --------------------------------------------------------------------- filtros

FILTER_KEYS = ("side", "map", "operator", "site", "match_type", "since", "until", "ranked_only")


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
    return qs


# --------------------------------------------------------------------- helpers

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
}


def _pct(part, whole) -> float | None:
    if not whole:
        return None
    return round(part / whole * 100, 1)


def _ratio(part, whole, digits: int = 2) -> float | None:
    if not whole:
        return None
    return round(part / whole, digits)


def derive(row: dict) -> dict:
    """Renombra los alias internos y agrega porcentajes y ratios."""
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
    return row


def totals(qs: QuerySet[RoundPlayer]) -> dict:
    row = dict(qs.aggregate(**AGGREGATES))
    row["matches"] = qs.values("round__match_id").distinct().count()
    return derive(row)


def group_by(qs: QuerySet[RoundPlayer], *fields: str, labels: tuple[str, ...] | None = None,
             min_rounds: int = 1, order: str = "-rounds") -> list[dict]:
    """Agrupa por uno o mas campos y devuelve filas con metricas derivadas."""
    labels = labels or fields
    rows = []
    for raw in qs.values(*fields).annotate(**AGGREGATES).order_by(order):
        if (raw.get("rounds") or 0) < min_rounds:
            continue
        row = dict(raw)
        for field, label in zip(fields, labels):
            row[label] = row.pop(field)
        rows.append(derive(row))
    return rows


# --------------------------------------------------------------------- vistas

def overview(**filters) -> dict:
    qs = base_queryset(**filters)
    attack = totals(qs.filter(side="Attack"))
    defense = totals(qs.filter(side="Defense"))
    return {
        "overall": totals(qs),
        "attack": attack,
        "defense": defense,
        "recent_form": recent_form(**filters),
    }


def recent_form(limit: int = 10, **filters) -> list[dict]:
    """Ultimas partidas: resultado y aporte propio."""
    qs = base_queryset(**filters)
    match_ids = list(
        qs.values_list("round__match_id", flat=True).order_by("-round__match__played_at").distinct()
    )[:limit]
    out = []
    for match in Match.objects.filter(id__in=match_ids).order_by("-played_at"):
        mine = qs.filter(round__match_id=match.id)
        row = totals(mine)
        out.append(
            {
                "id": match.id,
                "map": match.map_name,
                "played_at": match.played_at.isoformat(),
                "score": f"{match.my_score}-{match.opponent_score}",
                "result": match.result,
                "won": match.won,
                "kills": row["kills"],
                "deaths": row["deaths"],
                "kd": row["kd"],
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
    rows = []
    for raw in (
        qs.values("round__match__played_at__date").annotate(**AGGREGATES).order_by(
            "round__match__played_at__date"
        )
    ):
        row = dict(raw)
        day = row.pop("round__match__played_at__date")
        row["day"] = day.isoformat() if isinstance(day, date) else str(day)
        rows.append(derive(row))
    return rows


def trend_by_match(limit: int = 40, **filters) -> list[dict]:
    """Serie por partida, en orden cronologico, para ver evolucion."""
    qs = base_queryset(**filters)
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
        rows.append(derive(row))
    return list(reversed(rows))


def teammate_synergy(min_rounds: int = 10, **filters) -> list[dict]:
    """Winrate de rondas segun con quien las jugaste (solo companeros)."""
    mine = base_queryset(**filters)
    round_ids = list(mine.values_list("round_id", flat=True))
    my_teams = dict(mine.values_list("round_id", "team_index"))
    rows: dict[int, dict] = {}
    qs = (
        RoundPlayer.objects.filter(round_id__in=round_ids, is_me=False)
        .values("player_id", "username", "round_id", "team_index", "won")
    )
    for r in qs:
        if r["team_index"] != my_teams.get(r["round_id"]):
            continue
        row = rows.setdefault(
            r["player_id"], {"player_id": r["player_id"], "username": r["username"], "rounds": 0, "rounds_won": 0}
        )
        row["rounds"] += 1
        row["rounds_won"] += 1 if r["won"] else 0
    out = []
    for row in rows.values():
        if row["rounds"] < min_rounds:
            continue
        row["winrate"] = _pct(row["rounds_won"], row["rounds"])
        out.append(row)
    return sorted(out, key=lambda r: (-r["rounds"], r["username"]))


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


def data_health(**filters) -> dict:
    """Que tan completa es la data importada (para no mentirle a la UI)."""
    qs = base_queryset(**filters)
    rounds = Round.objects.filter(players__in=qs).distinct()
    return {
        "rounds": qs.count(),
        "matches": Match.objects.count(),
        "rounds_without_site": rounds.filter(site="").count(),
        "rounds_uncertain_win_condition": rounds.filter(win_condition_certain=False).count(),
        "rounds_possible_plant": rounds.filter(possible_plant=True).count(),
        "assists_available": qs.filter(assists__gt=0).exists(),
        "score_available": qs.filter(score__gt=0).exists(),
    }
