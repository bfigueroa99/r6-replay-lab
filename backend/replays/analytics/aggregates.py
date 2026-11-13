"""Agregaciones sobre las rondas del jugador para alimentar la API."""

from __future__ import annotations

import math
from collections import Counter
from collections.abc import Iterable
from datetime import date, datetime, timedelta
from itertools import combinations

from django.conf import settings
from django.db.models import (
    Avg,
    Case,
    Count,
    Exists,
    ExpressionWrapper,
    F,
    FloatField,
    IntegerField,
    Max,
    Min,
    OuterRef,
    Q,
    QuerySet,
    Subquery,
    Sum,
    Value,
    When,
)
from django.db.models.fields.json import KeyTransform
from django.db.models.functions import Cast, Floor

from pydissect.constants import MAPS, Y9S4
from pydissect.header import etiqueta_de_version

from .. import unknowns
from ..models import Event, Match, Player, Round, RoundPlayer, match_result
from . import reglas_partida
from .metrics import PLAYER_LEAVE, estado_al_morir, trade_window

# --------------------------------------------------------------------- filtros

FILTER_KEYS = (
    "side", "map", "operator", "site", "match_type", "gamemode", "since", "until", "ranked_only",
    "session",
)


def filtro_mapa(valor: str, prefijo: str = "round__match__") -> dict:
    """`?map=` con digitos es una version (`map_id`); si no, el slug con todas.

    Ningun slug es solo digitos (salen del nombre, y los desconocidos son
    `unknown-<id>`), asi que un solo parametro alcanza para los dos.
    """
    valor = str(valor)
    # isascii: "²" pasa isdigit pero int() lo rechaza; el tope evita el overflow
    # de SQLite. Lo que no es un id cae al slug y no coincide con nada.
    if valor.isascii() and valor.isdigit() and int(valor) < 2**63:
        return {f"{prefijo}map_id": int(valor)}
    return {f"{prefijo}map_slug": valor}


def base_queryset(**filters) -> QuerySet[RoundPlayer]:
    """Rondas del jugador principal, con los filtros de la request aplicados."""
    qs = RoundPlayer.objects.filter(is_me=True).select_related("round", "round__match")

    if filters.get("side"):
        qs = qs.filter(side=filters["side"])
    if filters.get("map"):
        qs = qs.filter(**filtro_mapa(filters["map"]))
    if filters.get("operator"):
        qs = qs.filter(operator=filters["operator"])
    if filters.get("site"):
        qs = qs.filter(round__site=filters["site"])
    if filters.get("match_type"):
        qs = qs.filter(round__match__match_type=filters["match_type"])
    if filters.get("gamemode"):
        qs = qs.filter(round__match__gamemode=filters["gamemode"])
    if filters.get("ranked_only"):
        qs = qs.filter(round__match__match_type="Ranked")
    if filters.get("since"):
        qs = qs.filter(round__match__played_at__gte=filters["since"])
    if filters.get("until"):
        qs = qs.filter(round__match__played_at__lte=filters["until"])
    if filters.get("session") not in (None, ""):
        qs = qs.filter(round__match_id__in=session_match_ids(filters["session"]))
    return qs


def match_queryset(**filters) -> QuerySet[Match]:
    """Partidas con los filtros de la barra, leidos igual que en `base_queryset`.

    Esta al lado de `base_queryset` para que un filtro nuevo de la barra entre
    a los dos. `side`, `operator` y `site` se ignoran a proposito: una partida
    tiene los dos lados, diez operadores y varios sitios, asi que no hay una
    partida "de ataque" que filtrar. Por eso, con esos filtros puestos, el
    conteo no coincide con el del Resumen, que cuenta partidas con rondas que
    los cumplen.
    """
    qs = Match.objects.all()
    if filters.get("map"):
        qs = qs.filter(**filtro_mapa(filters["map"], prefijo=""))
    if filters.get("match_type"):
        qs = qs.filter(match_type=filters["match_type"])
    if filters.get("gamemode"):
        qs = qs.filter(gamemode=filters["gamemode"])
    if filters.get("ranked_only"):
        qs = qs.filter(match_type="Ranked")
    if filters.get("since"):
        qs = qs.filter(played_at__gte=filters["since"])
    if filters.get("until"):
        qs = qs.filter(played_at__lte=filters["until"])
    if filters.get("session") not in (None, ""):
        qs = qs.filter(id__in=session_match_ids(filters["session"]))
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
    promedio = RoundPlayer.objects.filter(is_me=True).aggregate(v=Avg(rating_points_expr()))
    return promedio["v"] or None


#: Rondas por cantidad de bajas. Separado de AGGREGATES porque el scoreboard de
#: la partida tiene su propio annotate y tiene que contar exactamente igual.
#: Ace es 5 o mas y no 5 justo: un modo con respawn la pasa de 5.
MULTIKILLS = {
    "k2": Count("id", filter=Q(kills=2)),
    "k3": Count("id", filter=Q(kills=3)),
    "k4": Count("id", filter=Q(kills=4)),
    "aces": Count("id", filter=Q(kills__gte=5)),
    "multikill_rounds": Count("id", filter=Q(kills__gte=2)),
}

#: Fuera de posicion (ficha 80): moriste, no aportaste ninguna baja y nadie te
#: vengo. Ver `docs/metricas.md`. No se usa `untraded_death`: es lo mismo al
#: importar, pero una fila armada a mano puede no traerlo.
_FUERA_DE_POSICION = Q(died=True, kills=0, was_traded=False)

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
    "caught_out_rounds": Count("id", filter=_FUERA_DE_POSICION),
    **MULTIKILLS,
    "triple_plus_rounds": Count("id", filter=Q(kills__gte=3)),
    "won_after_opening_kill": Count("id", filter=Q(opening_kill=True, won=True)),
    "won_after_opening_death": Count("id", filter=Q(opening_death=True, won=True)),
    "avg_death_elapsed": Avg("death_elapsed"),
    "rating_points": Avg(rating_points_expr()),
}


#: Las aperturas partidas por trade (ficha 76). Aparte de AGGREGATES a proposito:
#: ahi cambiarian los CSV (columnas = union de claves) y cada agrupacion pagaria
#: ocho conteos que solo muestra el Inicio. Ojo con la `s`: `opening_kill_traded`
#: es el campo y no puede ser alias.
APERTURAS_CON_TRADE = {
    "opening_kills_clean": Count("id", filter=Q(opening_kill=True, opening_kill_traded=False)),
    "opening_kills_traded": Count("id", filter=Q(opening_kill=True, opening_kill_traded=True)),
    "opening_deaths_traded": Count("id", filter=Q(opening_death=True, was_traded=True)),
    "opening_deaths_untraded": Count("id", filter=Q(opening_death=True, was_traded=False)),
    "won_opening_kill_clean": Count(
        "id", filter=Q(opening_kill=True, opening_kill_traded=False, won=True)
    ),
    "won_opening_kill_traded": Count(
        "id", filter=Q(opening_kill=True, opening_kill_traded=True, won=True)
    ),
    "won_opening_death_traded": Count(
        "id", filter=Q(opening_death=True, was_traded=True, won=True)
    ),
    "won_opening_death_untraded": Count(
        "id", filter=Q(opening_death=True, was_traded=False, won=True)
    ),
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
    # Una fila armada a mano (tests, `_fold`) trae los conteos igual, en entero.
    for clave in MULTIKILLS:
        row[clave] = row.get(clave) or 0

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
            # Sobre rondas y no sobre muertes: la pregunta es cada cuanto te
            # pasa, y las rondas que sobreviviste tambien cuentan.
            "caught_out_pct": _pct(row.get("caught_out_rounds") or 0, rounds),
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
    # Las partidas van en el mismo aggregate y no en un `values().distinct()
    # .count()` aparte: esa segunda consulta recorria las mismas filas otra
    # vez, y Tendencias llama a totals() una vez por tramo (8 por hora, 7 por
    # dia...). Con 870 partidas /api/trends/ bajo de 2,1 s a 1,4 s (mejor de 7).
    row = dict(qs.aggregate(**AGGREGATES, matches=Count("round__match_id", distinct=True)))
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
        for field, label in zip(fields, labels, strict=True):
            row[label] = row.pop(field)
        rows.append(derive(row, baseline))
    return rows


def desglose_aperturas(qs: QuerySet[RoundPlayer]) -> dict:
    """Aperturas ganadas limpias o devueltas y perdidas vengadas o no, con su winrate."""
    fila = qs.aggregate(**APERTURAS_CON_TRADE)
    salida = {}
    for grupo in ("opening_kills_clean", "opening_kills_traded",
                  "opening_deaths_traded", "opening_deaths_untraded"):
        # opening_kills_clean -> winrate_opening_kill_clean
        sufijo = grupo.replace("opening_kills_", "opening_kill_").replace(
            "opening_deaths_", "opening_death_"
        )
        rondas = fila[grupo] or 0
        salida[grupo] = rondas
        salida[f"winrate_{sufijo}"] = _pct(fila[f"won_{sufijo}"] or 0, rondas)
    return salida


# --------------------------------------------------------------------- vistas

def overview(**filters) -> dict:
    qs = base_queryset(**filters)
    baseline = rating_baseline()
    attack = totals(qs.filter(side="Attack"), baseline)
    defense = totals(qs.filter(side="Defense"), baseline)
    overall = totals(qs, baseline)
    overall.update(desglose_aperturas(qs))
    return {
        "overall": overall,
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


#: Minimos de los records: una partida de 3 rondas o un dia de una sola
#: partida ganada 4-0 no son una marca.
RECORD_MIN_RONDAS_PARTIDA = 6
RECORD_MIN_RONDAS_DIA = 20


def _record_de_partida(fila: dict | None, valor: str) -> dict | None:
    if fila is None:
        return None
    return {
        "match_id": fila["round__match_id"],
        "played_at": fila["round__match__played_at"].isoformat(),
        "map": fila["round__match__map_name"],
        "value": fila[valor],
        "rounds": fila["rounds"],
    }


def _record_de_ronda(rp: RoundPlayer | None, valor: str) -> dict | None:
    if rp is None:
        return None
    return {
        "match_id": rp.round.match_id,
        "played_at": rp.round.match.played_at.isoformat(),
        "map": rp.round.match.map_name,
        "value": getattr(rp, valor),
        "round_label": f"R{rp.round.number + 1}",
        # el `number` del detalle: el enlace del record abre esa ronda
        "round_number": rp.round.number,
    }


def rachas_de_rondas(rondas: list[tuple[int, bool | None]]) -> dict:
    """Racha mas larga de rondas ganadas y de perdidas seguidas de una partida.

    Recibe pares `(number, my_team_won)`. Una ronda sin resultado o un hueco
    en la numeracion (falta un `.rec`) corta la racha: no se puede afirmar que
    siguio. A igual largo queda la primera de la partida.
    """
    mejores: dict[bool, dict | None] = {True: None, False: None}
    actual: dict | None = None
    anterior: tuple[int, bool | None] | None = None
    for numero, gano in sorted(rondas, key=lambda par: par[0]):
        sigue = (
            gano is not None
            and anterior is not None
            and anterior[1] is gano
            and numero == anterior[0] + 1
        )
        if not sigue:
            actual = None if gano is None else {"length": 0, "from_number": numero}
        if actual is not None:
            actual["length"] += 1
            mejor = mejores[gano]
            if mejor is None or actual["length"] > mejor["length"]:
                mejores[gano] = dict(actual)
        anterior = (numero, gano)
    return {"wins": mejores[True], "losses": mejores[False]}


def _record_de_racha(qs) -> dict | None:
    """La racha de rondas ganadas mas larga entre las partidas del filtro.

    Se mide sobre todas las rondas de cada partida: el filtro elige partidas,
    no rondas, y con un filtro de lado no habria rachas porque los lados
    alternan.
    """
    ids = set(qs.values_list("round__match_id", flat=True))
    if not ids:
        return None
    por_partida: dict[int, list[tuple[int, bool | None]]] = {}
    for match_id, numero, gano in Round.objects.filter(match_id__in=ids).values_list(
        "match_id", "number", "my_team_won"
    ):
        por_partida.setdefault(match_id, []).append((numero, gano))
    fechas = dict(Match.objects.filter(pk__in=por_partida).values_list("pk", "played_at"))
    candidatos = []
    for match_id, rondas in por_partida.items():
        racha = rachas_de_rondas(rondas)["wins"]
        if racha is not None:
            candidatos.append((racha["length"], fechas[match_id], match_id, racha))
    if not candidatos:
        return None
    _, _, match_id, racha = max(candidatos, key=lambda c: (c[0], c[1], c[2]))
    match = Match.objects.get(pk=match_id)
    return {
        "match_id": match.id,
        "played_at": match.played_at.isoformat(),
        "map": match.map_name,
        "value": racha["length"],
        "round_label": f"R{racha['from_number'] + 1}",
        "round_number": racha["from_number"],
    }


def personal_records(**filters) -> dict:
    """Tus mejores marcas con los filtros activos; `None` si no hay candidato.

    A igual valor gana lo mas reciente: igualar un record lo mueve a la
    partida nueva, que es la que el usuario quiere volver a mirar.
    """
    qs = base_queryset(**filters)
    baseline = rating_baseline()
    partidas = [
        derive(dict(raw), baseline)
        for raw in qs.values(*_MATCH_FIELDS).annotate(**AGGREGATES)
    ]
    # max() se queda con el primero de los empatados: ordenar de la mas
    # reciente a la mas vieja hace que el empate lo gane la mas reciente
    partidas.sort(key=lambda fila: fila["round__match__played_at"], reverse=True)

    con_rating = [
        fila for fila in partidas
        if fila["rounds"] >= RECORD_MIN_RONDAS_PARTIDA and fila["rating"] is not None
    ]
    mejor = max(con_rating, key=lambda fila: fila["rating"], default=None)
    con_bajas = [fila for fila in partidas if fila["kills"] > 0]
    mas_bajas = max(con_bajas, key=lambda fila: fila["kills"], default=None)

    orden_ronda = ("-round__match__played_at", "-round__number")
    ronda = qs.filter(kills__gt=0).order_by("-kills", *orden_ronda).first()
    clutch = qs.filter(one_vx__gt=0, won=True).order_by("-one_vx", *orden_ronda).first()

    dias = (
        qs.values(day=F("round__match__played_at__date"))
        .annotate(rounds=Count("id"), rounds_won=Count("id", filter=Q(won=True)))
        .filter(rounds__gte=RECORD_MIN_RONDAS_DIA)
    )
    dia = max(
        dias,
        key=lambda fila: (fila["rounds_won"] / fila["rounds"], fila["rounds_won"], fila["day"]),
        default=None,
    )

    return {
        "best_match_rating": _record_de_partida(mejor, "rating"),
        "most_kills_match": _record_de_partida(mas_bajas, "kills"),
        "most_kills_round": _record_de_ronda(ronda, "kills"),
        "biggest_clutch": _record_de_ronda(clutch, "one_vx"),
        "longest_round_streak": _record_de_racha(qs),
        "best_day": (
            {
                "day": dia["day"].isoformat(),
                "value": _pct(dia["rounds_won"], dia["rounds"]),
                "rounds": dia["rounds"],
                "rounds_won": dia["rounds_won"],
            }
            if dia
            else None
        ),
    }


#: Clave de un mapa en las tablas por mapa, sitio y spawn.
_MAPA = ("round__match__map_slug", "round__match__map_id", "round__match__map_name")
_MAPA_LABELS = ("slug", "map_id", "map_name")


def etiquetas_de_version(filas) -> dict[tuple[str, int], str]:
    """Etiqueta de cada `(slug, map_id)` de `filas` (dicts con map_slug/slug, map_id, map_name).

    Un id que `MAPS` no conoce y que el usuario nombro en Datos igual que la
    version conocida comparte slug y etiqueta con ella; ahi se le suma el id
    para que las dos filas se distingan.
    """
    etiquetas: dict[tuple[str, int], str] = {}
    for fila in filas:
        clave = (fila.get("slug", fila.get("map_slug")), fila["map_id"])
        etiquetas.setdefault(clave, etiqueta_de_version(fila["map_id"], fila["map_name"]))
    usos = Counter((slug, etiqueta) for (slug, _), etiqueta in etiquetas.items())
    for (slug, map_id), etiqueta in etiquetas.items():
        if usos[(slug, etiqueta)] > 1 and map_id not in MAPS:
            etiquetas[(slug, map_id)] = f"{etiqueta} (id {map_id})"
    return etiquetas


def etiquetas_de_mapas(slugs: Iterable[str] | None = None) -> dict[tuple[str, int], str]:
    """Etiqueta de cada `(map_slug, map_id)` guardado, la misma que usa Mapas.

    Mira todas las partidas del slug y no solo la fila pedida: el "(id N)" de
    `etiquetas_de_version` depende de que otra version del mismo slug lleve el
    mismo nombre, y una pagina del listado puede tener una sin la otra.
    Acotar por slug no cambia ninguna etiqueta, porque se desambigua dentro
    del slug; solo evita leer los mapas que la pagina no muestra.
    """
    qs = Match.objects.values("map_slug", "map_name", "map_id")
    if slugs is not None:
        qs = qs.filter(map_slug__in=list(slugs))
    return etiquetas_de_version(qs.distinct().order_by("map_name", "map_id"))


def _etiquetar(rows: list[dict]) -> list[dict]:
    etiquetas = etiquetas_de_version(rows)
    for row in rows:
        row.pop("map_name")
        row["map"] = etiquetas[(row["slug"], row["map_id"])]
    return rows


def by_map(min_rounds: int = 1, **filters) -> list[dict]:
    """Una fila por version de mapa.

    La clave es `(slug, map_id)` y no `map_id` solo: `seed_demo` y los tests
    dejan `map_id = 0` en todos los mapas, y el slug es lo que los separa.
    Dentro de un slug, el `map_id` separa el rework de la version vieja.
    """
    qs = base_queryset(**filters)
    rows = _etiquetar(group_by(qs, *_MAPA, labels=_MAPA_LABELS, min_rounds=min_rounds))
    # winrate por lado dentro de cada mapa
    sides = {
        (r["slug"], r["map_id"], r["side"]): r
        for r in group_by(qs, *_MAPA, "side", labels=(*_MAPA_LABELS, "side"))
    }
    for row in rows:
        for side in ("Attack", "Defense"):
            s = sides.get((row["slug"], row["map_id"], side))
            row[f"{side.lower()}_winrate"] = s["winrate"] if s else None
            row[f"{side.lower()}_rounds"] = s["rounds"] if s else 0
    return rows


def by_site(min_rounds: int = 1, **filters) -> list[dict]:
    qs = base_queryset(**filters).exclude(round__site="")
    return _etiquetar(group_by(
        qs,
        *_MAPA,
        "round__site",
        labels=(*_MAPA_LABELS, "site"),
        min_rounds=min_rounds,
    ))


def by_operator(min_rounds: int = 1, **filters) -> list[dict]:
    """Filas por operador y lado, con presencia y delta contra tu lado.

    La base del lado sale del queryset entero, antes de `min_rounds`: asi las
    presencias de un lado suman 100 % y ocultar una fila no mueve las demas.
    """
    qs = base_queryset(**filters).exclude(operator="")
    rows = group_by(qs, "operator", "side", labels=("operator", "side"), min_rounds=min_rounds)
    decidida = Q(round__my_team_won__isnull=False)
    lados = {
        r["side"]: r
        for r in qs.values("side").annotate(
            rounds=Count("id"),
            rounds_won=Count("id", filter=Q(won=True)),
        )
    }
    # Una ronda sin ganador cuenta como perdida en `won`; sin ninguna decidida
    # el delta no dice nada. Basta mirarlo en la fila: si el lado no tiene
    # ninguna, ninguna de sus filas la tiene.
    decididas = {
        (r["operator"], r["side"]): r["n"]
        for r in qs.filter(decidida).values("operator", "side").annotate(n=Count("id"))
    }
    for row in rows:
        lado = lados.get(row["side"]) or {}
        row["presence_pct"] = _pct(row["rounds"], lado.get("rounds"))
        base = _pct(lado.get("rounds_won") or 0, lado.get("rounds"))
        con_ganador = decididas.get((row["operator"], row["side"]))
        row["winrate_delta"] = _delta(row["winrate"], base) if con_ganador else None
    return rows


#: Rondas minimas del operador en un sitio, y del resto de tus operadores ahi,
#: para que la fila salga: con menos, la banda de ruido se come cualquier
#: diferencia y la tabla seria una lista de casualidades.
OPERADOR_SITIO_MIN_RONDAS = 10


def operator_by_site(min_rounds: int = OPERADOR_SITIO_MIN_RONDAS, **filters) -> dict:
    """Winrate con cada operador en un sitio contra el resto de tus operadores ahi.

    El resto es mismo mapa (por version), sitio y lado con otro operador; no
    el total del sitio, que contiene al operador (mismo motivo que
    `_contra_el_resto`). El filtro `operator` no entra a la base: dejaria el
    resto vacio. Recorta las filas al final.

    Solo cuentan rondas con ganador: una sin ganador no es derrota, asi que se
    lee `round__my_team_won` y no `won`, que la cuenta como perdida.
    """
    operador = filters.get("operator")
    base = {k: v for k, v in filters.items() if k != "operator"}
    qs = (
        base_queryset(**base)
        .exclude(operator="")
        .exclude(round__site="")
        .exclude(side="")
        .filter(round__my_team_won__isnull=False)
    )
    crudas = list(
        qs.order_by()
        .values(*_MAPA, "round__site", "side", "operator")
        .annotate(rounds=Count("id"), won=Count("id", filter=Q(round__my_team_won=True)))
    )
    # El total del sitio se suma antes del minimo: ocultar una fila no mueve
    # el resto de las demas.
    def clave(c: dict) -> tuple:
        return (*(c[campo] for campo in _MAPA), c["round__site"], c["side"])

    totales: dict[tuple, list[int]] = {}
    for c in crudas:
        total = totales.setdefault(clave(c), [0, 0])
        total[0] += c["rounds"]
        total[1] += c["won"]

    filas = []
    for c in crudas:
        total_rondas, total_ganadas = totales[clave(c)]
        rondas, ganadas = c["rounds"], c["won"]
        resto, resto_ganadas = total_rondas - rondas, total_ganadas - ganadas
        if rondas < min_rounds or resto < min_rounds:
            continue
        if operador and c["operator"] != operador:
            continue
        winrate = _pct(ganadas, rondas)
        resto_winrate = _pct(resto_ganadas, resto)
        delta = _delta(winrate, resto_winrate)
        margen, veredicto = _margen_y_veredicto(
            delta, ganadas, rondas, total_ganadas, total_rondas, ("rinde", "hunde"),
        )
        filas.append({
            **{etiqueta: c[campo] for campo, etiqueta in zip(_MAPA, _MAPA_LABELS, strict=True)},
            "site": c["round__site"],
            "side": c["side"],
            "operator": c["operator"],
            "rounds": rondas,
            "rounds_won": ganadas,
            "winrate": winrate,
            "rest_rounds": resto,
            "rest_winrate": resto_winrate,
            "winrate_delta": delta,
            "margin": margen,
            "verdict": veredicto,
        })
    filas = _etiquetar(filas)
    filas.sort(key=lambda f: (
        f["winrate_delta"] is None, -abs(f["winrate_delta"] or 0), -f["rounds"], f["operator"],
    ))
    return {"rows": filas, "min_rounds": min_rounds, "bands": POSICION_BANDAS}


#: Partidas que cuentan como "lo que jugas hoy" en el pool: suficientes para
#: que un operador de rotacion aparezca, pocas para que no pese lo de hace meses.
POOL_PARTIDAS_RECIENTES = 20

#: Dias sin un operador para decir que lo dejaste. Se cuentan desde tu partida
#: mas nueva y no desde hoy: quien no juega dos meses no lo dejo todo.
POOL_DIAS_SIN_JUGAR = 30


def operator_pool(catalogo: list[dict], **filters) -> dict:
    """Operadores distintos por lado, los que dejaste y los que nunca jugaste.

    El catalogo entra como argumento porque se arma en las vistas. `operator`
    no filtra (no hay "tu pool de Ash") y `side` tampoco: filtrar por lado
    dejaria el otro entero en `never`, asi que salen siempre los dos y la UI
    muestra el del filtro. `site` tampoco, por lo mismo: con un sitio puesto,
    todo operador que no jugaste ahi pasaria por "nunca jugado".
    """
    filtros = {k: v for k, v in filters.items() if k not in ("side", "operator", "site")}
    qs = (
        base_queryset(**filtros)
        .exclude(operator="")
        .exclude(operator__startswith=unknowns.UNKNOWN_PREFIX)
        .exclude(side="")
    )
    ids: list[int] = []
    referencia = None
    for fila in (
        qs.order_by("-round__match__played_at", "-round__match_id")
        .values_list("round__match_id", "round__match__played_at")
        .distinct()
        .iterator()
    ):
        if referencia is None:
            referencia = fila[1]
        ids.append(fila[0])
        if len(ids) >= POOL_PARTIDAS_RECIENTES:
            break
    partidas = qs.values("round__match_id").distinct().count()

    filas = list(
        qs.order_by()
        .values("operator", "side")
        .annotate(
            rounds=Count("id"),
            last=Max("round__match__played_at"),
            recent=Count("id", filter=Q(round__match_id__in=ids)),
        )
    )
    corte = referencia - timedelta(days=POOL_DIAS_SIN_JUGAR) if referencia else None

    lados = {}
    for lado in ("Attack", "Defense"):
        propias = [f for f in filas if f["side"] == lado]
        jugados = {f["operator"] for f in propias}
        # Por nombre primero y despues por fecha (sort estable): dos operadores
        # de la misma partida salen siempre en el mismo orden.
        viejos = sorted(
            (f for f in propias if corte is not None and f["last"] < corte),
            key=lambda f: f["operator"].lower(),
        )
        viejos.sort(key=lambda f: f["last"], reverse=True)
        lados[lado] = {
            "distinct_recent": sum(1 for f in propias if f["recent"] > 0),
            "distinct_all": len(jugados),
            "never": sorted(
                (
                    o["name"] for o in catalogo
                    if o["side"] == lado and o["name"] not in jugados
                    and o["name"] and not o["name"].startswith(unknowns.UNKNOWN_PREFIX)
                ),
                key=str.lower,
            ),
            "stale": [
                {"operator": f["operator"], "last_played": f["last"].isoformat(),
                 "rounds": f["rounds"]}
                for f in viejos
            ],
        }
    return {
        "matches": partidas,
        "recent_matches": len(ids),
        "reference": referencia.isoformat() if referencia else None,
        "recent_window": POOL_PARTIDAS_RECIENTES,
        "stale_days": POOL_DIAS_SIN_JUGAR,
        "sides": lados,
    }


#: La muestra minima de "Operador" (tabla de muestra minima): debajo se avisa
#: "pocas rondas" pero no se oculta, porque el par repetir/cambiar se lee junto.
OPERADOR_TRAS_RESULTADO_MIN_RONDAS = 12
OPERADOR_TRAS_RESULTADO = ("after_loss", "after_win")
OPERADOR_TRAS_RESULTADO_CASOS = ("repeat", "switch")


def _bloque_tras_resultado() -> dict:
    return {
        tras: {caso: {"rounds": 0, "decided": 0, "won": 0, "winrate": None}
               for caso in OPERADOR_TRAS_RESULTADO_CASOS}
        for tras in OPERADOR_TRAS_RESULTADO
    }


def operator_after_result(**filters) -> dict:
    """Tras una ronda tuya, si en la siguiente del mismo lado repetiste operador.

    El par es tu ronda y tu siguiente ronda del mismo lado en la partida: las
    del otro lado en medio no lo cortan (el medio tiempo separa ataque y
    defensa), pero un numero faltante si, porque no se sabe que jugaste ahi.
    `side` no filtra el queryset: sin las rondas del otro lado no se distingue
    un hueco de un cambio de lado; la UI elige el bloque. `operator` y `site`
    eligen la primera ronda del par: filtrar las filas dejaria solo los pares
    que repiten (o que vuelven al mismo sitio) y cortaria el resto.
    """
    operador = filters.get("operator")
    sitio = filters.get("site")
    base = {k: v for k, v in filters.items() if k not in ("side", "operator", "site")}
    filas = (
        base_queryset(**base)
        .order_by("round__match_id", "round__number")
        .values_list("round__match_id", "round__number", "side", "operator",
                     "round__site", "round__my_team_won")
    )
    lados = {lado: _bloque_tras_resultado() for lado in ("Attack", "Defense")}
    pendiente: dict[str, tuple] = {}
    anterior = None
    pares = 0
    for partida, numero, lado, op, sitio_ronda, gano in filas.iterator():
        if anterior is None or anterior[0] != partida or numero != anterior[1] + 1 or not lado:
            pendiente.clear()
        anterior = (partida, numero)
        if lado not in lados:
            continue
        if not op or op.startswith(unknowns.UNKNOWN_PREFIX):
            pendiente.pop(lado, None)
            continue
        previa = pendiente.pop(lado, None)
        if previa is not None:
            op_previo, gano_previo = previa
            caso = "repeat" if op == op_previo else "switch"
            tras = "after_win" if gano_previo else "after_loss"
            celda = lados[lado][tras][caso]
            celda["rounds"] += 1
            if gano is not None:
                celda["decided"] += 1
                celda["won"] += int(gano)
            pares += 1
        # Sin ganador no hay "tras perder" ni "tras ganar": no abre par.
        if gano is not None and (not operador or op == operador) \
                and (not sitio or sitio_ronda == sitio):
            pendiente[lado] = (op, gano)

    total = _bloque_tras_resultado()
    for bloque in lados.values():
        for tras in OPERADOR_TRAS_RESULTADO:
            for caso in OPERADOR_TRAS_RESULTADO_CASOS:
                for campo in ("rounds", "decided", "won"):
                    total[tras][caso][campo] += bloque[tras][caso][campo]
    for bloque in (*lados.values(), total):
        for tras in OPERADOR_TRAS_RESULTADO:
            for celda in bloque[tras].values():
                celda["winrate"] = _pct(celda["won"], celda["decided"])
    return {
        "min_rounds": OPERADOR_TRAS_RESULTADO_MIN_RONDAS,
        "pairs": pares,
        "sides": lados,
        "total": total,
    }


def by_spawn(min_rounds: int = 1, **filters) -> list[dict]:
    """Solo tiene sentido en ataque: el spawn es la posicion de inicio."""
    qs = base_queryset(**filters).filter(side="Attack").exclude(spawn="")
    return _etiquetar(group_by(
        qs,
        *_MAPA,
        "spawn",
        labels=(*_MAPA_LABELS, "spawn"),
        min_rounds=min_rounds,
    ))


# --------------------------------------------------------------------- posicion

#: Filas de la tabla de posicion: con menos rondas, el margen se come cualquier
#: diferencia.
POSICION_MIN_RONDAS = 5

#: Cuantos errores estandar tiene que pasar la diferencia para que la zona
#: tenga veredicto. Progreso usa uno porque mira 10 metricas fijas; aca hay una
#: fila por sitio y spawn (20 o mas en un historial real) y con uno solo un
#: tercio de las zonas saldria marcado por azar.
POSICION_BANDAS = 2

#: Segundos jugados de la fase de accion que cuentan como "salida del spawn".
#: Es la mitad del primer tramo de "Sales muy temprano" (30 s): a los 15 s el
#: atacante todavia esta saliendo del spawn o en el runout, y morir ahi no es
#: lo mismo que morir en el primer contacto armado.
SALIDA_SPAWN_SEGUNDOS = 15


def _totales_de_posicion(qs: QuerySet[RoundPlayer]) -> dict:
    fila = qs.aggregate(
        rounds=Count("id"),
        caught_out_rounds=Count("id", filter=_FUERA_DE_POSICION),
    )
    rondas = fila["rounds"] or 0
    fuera = fila["caught_out_rounds"] or 0
    return {
        "rounds": rondas,
        "caught_out_rounds": fuera,
        "caught_out_pct": _pct(fuera, rondas),
    }


def _ruido_combinado(parte: int, n: int, parte_total: int, n_total: int) -> float | None:
    """Error estandar de la diferencia zona - resto, con la proporcion combinada.

    No se usa `_ruido` (Wald, una varianza por muestra): con una zona en 0 % o
    100 % su varianza es cero, el margen se achica a casi nada y una zona de 5
    rondas sale con veredicto por azar. Con la proporcion de zona + resto (el
    total) el margen no colapsa en los bordes.
    """
    resto = n_total - n
    if not n or not resto:
        return None
    p = parte_total / n_total
    return round(math.sqrt(p * (1 - p) * (1 / n + 1 / resto)) * 100, 1)


def _margen_y_veredicto(delta: float | None, parte: int, n: int, parte_total: int,
                        n_total: int, nombres: tuple[str, str]) -> tuple[float | None, str]:
    """Margen de ruido de la zona y su veredicto: `nombres` es (delta positivo, delta negativo)."""
    se = _ruido_combinado(parte, n, parte_total, n_total)
    margen = round(POSICION_BANDAS * se, 1) if se is not None else None
    if delta is None or margen is None:
        return margen, "ruido"
    if delta > margen:
        return margen, nombres[0]
    if delta < -margen:
        return margen, nombres[1]
    return margen, "ruido"


def _contra_el_resto(filas: list[dict], total: dict) -> list[dict]:
    """Compara cada zona contra el resto del historial, no contra el total.

    La zona esta dentro del total: compararla con el la acerca a si misma, y
    la banda de ruido supone dos muestras independientes.
    """
    for fila in filas:
        rondas = fila["rounds"]
        resto = total["rounds"] - rondas
        resto_pct = _pct(total["caught_out_rounds"] - fila["caught_out_rounds"], resto)
        delta = _delta(fila["caught_out_pct"], resto_pct)
        margen, veredicto = _margen_y_veredicto(
            delta, fila["caught_out_rounds"], rondas,
            total["caught_out_rounds"], total["rounds"], ("dormidero", "solido"),
        )
        fila.update(
            {
                "rest_rounds": resto,
                "rest_caught_out_pct": resto_pct,
                "caught_out_delta": delta,
                "margin": margen,
                "verdict": veredicto,
            }
        )
    # Mayor diferencia primero; las que no tienen diferencia, al final.
    filas.sort(key=lambda f: (f["caught_out_delta"] is None, -(f["caught_out_delta"] or 0)))
    return filas


def _temprano(campo: str) -> Q:
    """Muerte o baja dentro de la salida del spawn.

    El 0 no cuenta: `metrics.py` escribe `elapsed = 0.0` cuando el feed no
    trae reloj, y en una ventana de 15 s ese 0 espurio pesaria mucho.
    """
    return Q(**{f"{campo}__gt": 0, f"{campo}__lt": SALIDA_SPAWN_SEGUNDOS})


def spawn_exits(ataque: QuerySet[RoundPlayer], min_rounds: int) -> tuple[list[dict], dict]:
    """Muertes y bajas en los primeros segundos de accion, por mapa y spawn de ataque.

    Mide si un spawn te cuesta rondas por salir a pelear antes de tiempo
    (runout o spawn peek que sale mal). Cada spawn va contra el resto de tu
    ataque, no contra el total: la zona esta dentro del total y la banda de
    ruido supone dos muestras independientes. Devuelve las filas y el total
    del ataque, que se calcula antes del minimo para que ocultar una fila no
    mueva las demas.
    """
    ataque = ataque.exclude(spawn="")
    # Las bajas se agrupan con la misma clave que las filas (mapa entero, con
    # nombre): si una version tiene dos nombres, cada fila suma solo las suyas.
    bajas: Counter = Counter()
    me_ids = _me_ids()
    if me_ids:
        _, a_favor = _duelos(ataque, me_ids)
        mi_spawn = Subquery(
            RoundPlayer.objects.filter(round_id=OuterRef("round_id"), is_me=True)
            .values("spawn")[:1]
        )
        tempranas = (
            a_favor.filter(_temprano("elapsed"))
            .annotate(mi_spawn=mi_spawn)
            .order_by()
            .values(*_MAPA, "mi_spawn")
            .annotate(n=Count("id"))
        )
        for t in tempranas:
            if t["mi_spawn"]:
                bajas[(*(t[c] for c in _MAPA), t["mi_spawn"])] += t["n"]

    crudas = ataque.order_by().values(*_MAPA, "spawn").annotate(
        rounds=Count("id"),
        early_deaths=Count("id", filter=Q(died=True) & _temprano("death_elapsed")),
    )
    filas = _etiquetar([
        {
            **{etiqueta: c[campo] for campo, etiqueta in zip(_MAPA, _MAPA_LABELS, strict=True)},
            "spawn": c["spawn"],
            "rounds": c["rounds"],
            "early_deaths": c["early_deaths"],
            "early_kills": bajas[(*(c[campo] for campo in _MAPA), c["spawn"])],
        }
        for c in crudas
    ])

    total_rondas = sum(f["rounds"] for f in filas)
    total_tempranas = sum(f["early_deaths"] for f in filas)
    total = {
        "rounds": total_rondas,
        "early_deaths": total_tempranas,
        "early_death_pct": _pct(total_tempranas, total_rondas),
        "early_kills": sum(bajas.values()),
    }

    for f in filas:
        rondas, tempranas_fila = f["rounds"], f["early_deaths"]
        kills = f["early_kills"]
        resto = total_rondas - rondas
        pct = _pct(tempranas_fila, rondas)
        resto_pct = _pct(total_tempranas - tempranas_fila, resto)
        delta = _delta(pct, resto_pct)
        margen, veredicto = _margen_y_veredicto(
            delta, tempranas_fila, rondas, total_tempranas, total_rondas, ("temprano", "aguanta"),
        )
        f.update(
            {
                "early_death_pct": pct,
                "early_kills_per_round": _ratio(kills, rondas),
                "rest_rounds": resto,
                "rest_early_death_pct": resto_pct,
                "early_death_delta": delta,
                "margin": margen,
                "verdict": veredicto,
            }
        )

    filas = [f for f in filas if f["rounds"] >= min_rounds]
    filas.sort(key=lambda f: (
        f["early_death_pct"] is None, -(f["early_death_pct"] or 0), -f["rounds"], f["spawn"],
    ))
    return filas, total


def positioning(min_rounds: int = POSICION_MIN_RONDAS, **filters) -> dict:
    """Donde quedas fuera de posicion: sitio contra el resto, spawn contra el resto del ataque.

    El spawn va contra el ataque y no contra todo porque solo existe en ataque,
    y en ataque se queda fuera de posicion mas seguido: compararlo con todo lo
    marcaria por el lado y no por el spawn. Las filas no se filtran por
    veredicto: la tabla tambien muestra las que son ruido.
    """
    qs = base_queryset(**filters)
    baseline = rating_baseline()
    ataque = qs.filter(side="Attack")
    sitios = _etiquetar(group_by(
        qs.exclude(round__site=""), *_MAPA, "round__site",
        labels=(*_MAPA_LABELS, "site"), min_rounds=min_rounds, baseline=baseline,
    ))
    spawns = _etiquetar(group_by(
        ataque.exclude(spawn=""), *_MAPA, "spawn",
        labels=(*_MAPA_LABELS, "spawn"), min_rounds=min_rounds, baseline=baseline,
    ))
    total = _totales_de_posicion(qs)
    total_ataque = _totales_de_posicion(ataque)
    salidas, salida_ataque = spawn_exits(ataque, min_rounds)
    return {
        "overall": total,
        "attack": total_ataque,
        "sites": _contra_el_resto(sitios, total),
        "spawns": _contra_el_resto(spawns, total_ataque),
        "min_rounds": min_rounds,
        "bands": POSICION_BANDAS,
        "spawn_exits": salidas,
        "spawn_exit_attack": salida_ataque,
        "spawn_exit_seconds": SALIDA_SPAWN_SEGUNDOS,
    }


#: Muestra minima de la tabla "Sitio / spawn" de metricas.md: debajo el winrate
#: se muestra con aviso, no se oculta.
REPETIR_SITIO_MIN_RONDAS = 8
REPETIR_SITIO_CASOS = ("repeat", "switch")


def _caso_vacio() -> dict:
    return {"rounds": 0, "decided": 0, "won": 0, "winrate": None}


def _sumar_caso(caso: dict, ganada: bool | None) -> None:
    caso["rounds"] += 1
    if ganada is not None:
        caso["decided"] += 1
        caso["won"] += int(ganada)


def site_after_loss(**filters) -> dict:
    """Tras perder una ronda de defensa, si tu equipo vuelve a ese sitio en la siguiente.

    El par son dos rondas de defensa seguidas de la misma partida; las de
    ataque entre medio no lo cortan, pero un numero que falta (ronda sin
    `.rec`, o una en la que no estas) o una ronda sin lado o sin sitio si:
    ahi no se sabe que defendio tu equipo. Se leen tus rondas de los dos
    lados para ver esos huecos. `side` y `operator` no filtran (el par es de
    la defensa y del equipo, no de tu operador) y `site` elige el sitio de la
    ronda perdida, no el de las dos.
    """
    sitio = filters.get("site")
    base = {k: v for k, v in filters.items() if k not in ("side", "site", "operator")}
    filas = (
        base_queryset(**base)
        .order_by("round__match_id", "round__number")
        .values("round__match_id", "round__number", "side", "round__site",
                "round__my_team_won", *_MAPA)
    )

    total = {caso: _caso_vacio() for caso in REPETIR_SITIO_CASOS}
    por_mapa: dict[tuple, dict] = {}
    pares = 0
    anterior = None  # ultima fila vista de la partida en curso
    perdida = None  # ultima ronda de defensa perdida, con sitio, sin hueco despues
    for fila in filas:
        if anterior is None or (
            fila["round__match_id"] != anterior["round__match_id"]
            or fila["round__number"] != anterior["round__number"] + 1
            or not fila["side"]
        ):
            perdida = None
        anterior = fila
        if fila["side"] != "Defense":
            continue
        if not fila["round__site"]:
            perdida = None
            continue
        if perdida is not None:
            caso = "repeat" if fila["round__site"] == perdida["round__site"] else "switch"
            clave = tuple(perdida[campo] for campo in _MAPA)
            mapa = por_mapa.setdefault(clave, {
                **{etiqueta: perdida[campo]
                   for campo, etiqueta in zip(_MAPA, _MAPA_LABELS, strict=True)},
                **{c: _caso_vacio() for c in REPETIR_SITIO_CASOS},
            })
            _sumar_caso(total[caso], fila["round__my_team_won"])
            _sumar_caso(mapa[caso], fila["round__my_team_won"])
            pares += 1
        # Sin ganador no es derrota: no abre par.
        perdio = fila["round__my_team_won"] is False
        perdida = fila if perdio and (not sitio or fila["round__site"] == sitio) else None

    mapas = list(por_mapa.values())
    for caso_dict in [total, *mapas]:
        for caso in REPETIR_SITIO_CASOS:
            c = caso_dict[caso]
            c["winrate"] = _pct(c["won"], c["decided"])
    mapas = _etiquetar(mapas)
    mapas.sort(key=lambda m: (-(m["repeat"]["rounds"] + m["switch"]["rounds"]), m["map"]))
    return {
        "min_rounds": REPETIR_SITIO_MIN_RONDAS,
        "pairs": pares,
        "total": total,
        "maps": mapas,
    }


def by_round_number(**filters) -> list[dict]:
    qs = base_queryset(**filters)
    return group_by(qs, "round__number", labels=("round_number",), order="round__number")


def _lado_inicial(match_ref: str) -> Subquery:
    """Lado de la ronda mas baja sin prorroga de la partida.

    Se lee de la partida entera y no del queryset filtrado: con `?side=` el
    filtro limita las rondas, pero la partida arranco donde arranco. No se
    exige `number=1` porque `seed_demo` numera desde 0.
    """
    return Subquery(
        Round.objects.filter(match_id=OuterRef(match_ref), overtime_number=0)
        .order_by("number")
        .values("my_side")[:1]
    )


#: Orden fijo de las filas de `by_half`.
MITADES = ("first", "second", "overtime")


def by_half(**filters) -> list[dict]:
    """Primera mitad, segunda mitad y prorroga, sin suponer rondas por modo."""
    qs = base_queryset(**filters)
    con_lado = (
        qs.filter(round__overtime_number=0)
        .annotate(lado_inicial=_lado_inicial("round__match_id"))
        .exclude(lado_inicial__isnull=True)
        .exclude(lado_inicial="")
        .exclude(round__my_side="")
    )
    tramos = {
        "first": con_lado.filter(round__my_side=F("lado_inicial")),
        "second": con_lado.exclude(round__my_side=F("lado_inicial")),
        "overtime": qs.filter(round__overtime_number__gt=0),
    }
    return _filas_por_tramo("half", {mitad: tramos[mitad] for mitad in MITADES})


#: Orden fijo de las filas de `by_overtime_side`.
PRORROGA_LADOS = ("Attack", "Defense")


def by_overtime_side(**filters) -> list[dict]:
    """Rondas de prorroga partidas por el lado que te toco en cada una.

    La fila `overtime` de `by_half` no se toca: esto la abre en dos. Se lee
    `round__my_side`, el mismo campo de `by_half`.
    """
    qs = base_queryset(**filters).filter(round__overtime_number__gt=0)
    # con ?side= la otra fila saldria siempre en cero: no se devuelve
    lados = (filters["side"],) if filters.get("side") in PRORROGA_LADOS else PRORROGA_LADOS
    return _filas_por_tramo("side", {lado: qs.filter(round__my_side=lado) for lado in lados})


#: Orden fijo de las filas de `by_half_opener`.
APERTURAS_DE_MITAD = ("match_start", "side_switch", "rest")


def _primera_ronda(match_ref: str) -> Subquery:
    """Numero de la ronda mas baja sin prorroga: la misma que lee `_lado_inicial`."""
    return Subquery(
        Round.objects.filter(match_id=OuterRef(match_ref), overtime_number=0)
        .order_by("number")
        .values("number")[:1]
    )


def _primera_tras_el_cambio(match_ref: str, lado_ref: str) -> Subquery:
    """Numero de la ronda mas baja sin prorroga jugada del lado que no es el inicial."""
    return Subquery(
        Round.objects.filter(match_id=OuterRef(match_ref), overtime_number=0)
        .exclude(my_side="")
        .exclude(my_side=OuterRef(lado_ref))
        .order_by("number")
        .values("number")[:1]
    )


def by_half_opener(**filters) -> list[dict]:
    """Ronda 1, primera ronda despues del cambio de lado y el resto, sin prorroga."""
    qs = base_queryset(**filters)
    # Dos annotate seguidos: la segunda subquery referencia `lado_inicial`.
    con_lado = (
        qs.filter(round__overtime_number=0)
        .annotate(lado_inicial=_lado_inicial("round__match_id"))
        .exclude(lado_inicial__isnull=True)
        .exclude(lado_inicial="")
        .exclude(round__my_side="")
        .annotate(
            primera=_primera_ronda("round__match_id"),
            cambio=_primera_tras_el_cambio("round__match_id", "lado_inicial"),
        )
    )
    tramos = {
        "match_start": con_lado.filter(round__number=F("primera")),
        "side_switch": con_lado.filter(round__number=F("cambio")),
        # Un exclude con F contra un nulo descarta la fila en SQL: sin el Q,
        # las partidas que nunca cambiaron de lado desaparecen del resto.
        "rest": con_lado.exclude(round__number=F("primera")).filter(
            ~Q(round__number=F("cambio")) | Q(cambio__isnull=True)
        ),
    }
    return _filas_por_tramo("opener", {t: tramos[t] for t in APERTURAS_DE_MITAD})


def _filas_por_tramo(campo: str, tramos: dict[str | int, QuerySet[RoundPlayer]]) -> list[dict]:
    """Una fila de `totals()` por tramo, en el orden del dict.

    El baseline del rating se calcula una sola vez: es el mismo para todas
    las filas y sale de toda la base, no del tramo.
    """
    baseline = rating_baseline()
    return [{campo: nombre, **totals(qs, baseline)} for nombre, qs in tramos.items()]


#: Orden fijo de las filas de `by_previous_round`.
RONDA_ANTERIOR = ("after_win", "after_loss", "no_previous")


def _resultado_anterior() -> Subquery:
    """Resultado de la ronda `number - 1` de la misma partida.

    Se lee de `Round` y no del queryset filtrado, como `_lado_inicial`: con
    `?side=Attack` la ronda anterior de defensa sigue existiendo y pesa igual.
    """
    return Subquery(
        Round.objects.filter(
            match_id=OuterRef("round__match_id"), number=OuterRef("round__number") - 1
        ).values("my_team_won")[:1]
    )


def by_previous_round(**filters) -> list[dict]:
    """Rondas despues de ganar, despues de perder y sin ronda anterior conocida."""
    qs = base_queryset(**filters).annotate(anterior=_resultado_anterior())
    # Nulo junta la primera ronda, la anterior que falta (sin su .rec) y la
    # anterior sin resultado: ninguna dice nada sobre la inercia.
    tramos = {
        "after_win": qs.filter(anterior=True),
        "after_loss": qs.filter(anterior=False),
        "no_previous": qs.filter(anterior__isnull=True),
    }
    return _filas_por_tramo("previous", {nombre: tramos[nombre] for nombre in RONDA_ANTERIOR})


#: Orden fijo de las filas de `by_score_state`.
MARCADOR = ("ahead", "tied", "behind", "unknown")


def _marcador_conocido(
    qs: QuerySet[RoundPlayer],
) -> tuple[QuerySet[RoundPlayer], QuerySet[RoundPlayer]]:
    """`qs` anotado con `mio`/`suyo` del marcador antes de la ronda, y sus filas legibles."""
    s0 = Cast(KeyTransform("0", "round__score_before"), IntegerField())
    s1 = Cast(KeyTransform("1", "round__score_before"), IntegerField())
    # Un marcador de mas de dos equipos no se puede leer como tuyo contra el
    # otro: el tercer elemento lo manda a `unknown`.
    qs = qs.annotate(s0=s0, s1=s1, s2=KeyTransform("2", "round__score_before"))
    # El queryset es de tus filas, asi que `team_index` es tu equipo; uno
    # fuera de 0/1 deja `mio` nulo y la ronda cae en `unknown`.
    qs = qs.annotate(
        mio=Case(When(team_index=0, then=F("s0")), When(team_index=1, then=F("s1"))),
        suyo=Case(When(team_index=0, then=F("s1")), When(team_index=1, then=F("s0"))),
    )
    # Antes de Y9S4 el parser pone `startingScore` en 0 y la ingesta guarda
    # [0, 0]: parece empatado pero no se sabe. Se lee de la partida y no de la
    # ronda para que una base ya importada se corrija sin reimportar.
    conocido = qs.filter(
        mio__isnull=False, suyo__isnull=False, s2__isnull=True,
        round__match__code_version__gte=Y9S4,
    )
    return qs, conocido


def by_score_state(**filters) -> list[dict]:
    """Rondas yendo adelante, empatado o atras en el marcador antes de jugarlas."""
    qs, conocido = _marcador_conocido(base_queryset(**filters))
    tramos = {
        "ahead": conocido.filter(mio__gt=F("suyo")),
        "tied": conocido.filter(mio=F("suyo")),
        "behind": conocido.filter(mio__lt=F("suyo")),
        "unknown": qs.exclude(pk__in=conocido.values("pk")),
    }
    return _filas_por_tramo("score_state", {nombre: tramos[nombre] for nombre in MARCADOR})


#: Orden fijo de las filas de `by_match_point`.
MATCH_POINT = ("mine", "theirs", "both", "normal", "unknown")


def by_match_point(**filters) -> list[dict]:
    """Rondas segun si alguien cerraba la partida ganandolas.

    A cuanto se gana sale de `reglas_partida.REGLAS`: un tipo o una version
    sin regla va a `unknown` junto con las rondas sin marcador, en vez de
    contarse como ronda sin match point.
    """
    qs, conocido = _marcador_conocido(base_queryset(**filters))
    con_regla_q = Q(pk__in=[])
    por_estado = {nombre: Q(pk__in=[]) for nombre in reglas_partida.ESTADOS}
    for tipo, reglas in reglas_partida.REGLAS.items():
        # el tramo de version de cada regla termina donde arranca la siguiente
        reglas = sorted(reglas, key=lambda r: r["desde"])
        for i, regla in enumerate(reglas):
            version = Q(
                round__match__match_type=tipo, round__match__code_version__gte=regla["desde"]
            )
            if i + 1 < len(reglas):
                version &= Q(round__match__code_version__lt=reglas[i + 1]["desde"])
            con_regla_q |= version
            for nombre, pares in reglas_partida.tramos(regla).items():
                if pares:
                    marcadores = Q(pk__in=[])
                    for mio, suyo in pares:
                        marcadores |= Q(mio=mio, suyo=suyo)
                    por_estado[nombre] |= version & marcadores
    con_regla = conocido.filter(con_regla_q)
    tramos = {nombre: con_regla.filter(por_estado[nombre]) for nombre in ("mine", "theirs", "both")}
    # `normal` es lo que queda: asi un marcador fuera de rango no se pierde.
    tramos["normal"] = con_regla.exclude(
        por_estado["mine"] | por_estado["theirs"] | por_estado["both"]
    )
    tramos["unknown"] = qs.exclude(pk__in=con_regla.values("pk"))
    return _filas_por_tramo("match_point", {nombre: tramos[nombre] for nombre in MATCH_POINT})


#: Rondas de diferencia para que una partida cuente como remontada o
#: derrumbe. Con 1 entra cualquier partida que perdiste la primera ronda: no
#: dice nada de como reaccionas al marcador.
UMBRAL_REMONTADA = 2
#: Tope de partidas por lista; `*_total` trae el conteo entero.
TOPE_LISTA = 20
#: Orden fijo de las filas de `by_side_change_diff`; los extremos juntan
#: todo lo que pasa de 2.
TRAMOS_CAMBIO = ("+2", "+1", "0", "-1", "-2")


def _marcador_de_ronda(score_before, team_index) -> tuple[int, int] | None:
    """`(mio, suyo)` antes de la ronda, con la misma regla que `_marcador_conocido`."""
    if not isinstance(score_before, list) or len(score_before) != 2:
        return None
    if not all(isinstance(s, int) and not isinstance(s, bool) for s in score_before):
        return None
    if team_index == 0:
        return score_before[0], score_before[1]
    if team_index == 1:
        return score_before[1], score_before[0]
    return None


def _tramo_cambio(diferencia: int) -> str:
    if diferencia >= 2:
        return "+2"
    if diferencia <= -2:
        return "-2"
    return f"{diferencia:+d}" if diferencia else "0"


def comebacks(**filters) -> dict:
    """Partidas ganadas yendo abajo, perdidas yendo arriba, y winrate segun el
    marcador al cambio de lado.

    Los filtros eligen partidas; cada partida se lee entera, como en
    `by_start_side`: con `?side=Attack` el pozo de la defensa sigue siendo
    parte de la remontada.
    """
    ids = base_queryset(**filters).values_list("round__match_id", flat=True).distinct()
    partidas = {
        p["id"]: p
        for p in Match.objects.filter(id__in=ids, code_version__gte=Y9S4).values(
            "id", "map_name", "played_at", "my_score", "opponent_score", "won"
        )
    }
    filas = (
        RoundPlayer.objects.filter(is_me=True, round__match_id__in=ids,
                                   round__match__code_version__gte=Y9S4)
        .values("round__match_id", "round__number", "round__overtime_number",
                "round__my_side", "round__score_before", "team_index")
        .order_by("round__match_id", "round__number", "id")
    )
    rondas: dict[int, dict[int, dict]] = {}
    for fila in filas:
        # Una fila tuya por ronda; si hubiera dos, manda la primera.
        rondas.setdefault(fila["round__match_id"], {}).setdefault(fila["round__number"], fila)

    remontadas, derrumbes = [], []
    por_tramo = {tramo: [0, 0] for tramo in TRAMOS_CAMBIO}
    conocidas = 0
    for match_id, por_numero in rondas.items():
        partida = partidas.get(match_id)
        if partida is None or partida["won"] is None:
            continue
        numeros = sorted(por_numero)
        orden = [por_numero[n] for n in numeros]
        marcadores = [_marcador_de_ronda(r["round__score_before"], r["team_index"]) for r in orden]
        # Una ronda ilegible o que falta (sin su `.rec`) puede esconder el pozo
        # o el cambio de lado: la partida entera queda afuera en vez de
        # medirse a medias. Los huecos del medio se ven en la numeracion; los
        # del principio no (se numera desde 0 o desde 1), pero si en que la
        # primera ronda no arranca 0-0.
        if (any(m is None for m in marcadores)
                or numeros[-1] - numeros[0] + 1 != len(numeros)
                or marcadores[0] != (0, 0)):
            continue
        conocidas += 1
        # El `score_before` de la ultima ronda es el marcador antes de
        # jugarla; el final no cuenta como ventaja ni desventaja.
        desventaja = max(suyo - mio for mio, suyo in marcadores)
        ventaja = max(mio - suyo for mio, suyo in marcadores)
        item = {
            "match_id": match_id,
            "map": partida["map_name"],
            "played_at": partida["played_at"].isoformat(),
            "score": f"{partida['my_score']}-{partida['opponent_score']}",
        }
        if partida["won"] and desventaja >= UMBRAL_REMONTADA:
            remontadas.append({**item, "max_deficit": desventaja})
        elif not partida["won"] and ventaja >= UMBRAL_REMONTADA:
            derrumbes.append({**item, "max_lead": ventaja})

        sin_prorroga = [
            (r["round__my_side"], m)
            for r, m in zip(orden, marcadores, strict=True)
            if r["round__overtime_number"] == 0
        ]
        if not sin_prorroga or not sin_prorroga[0][0]:
            continue
        lado_inicial = sin_prorroga[0][0]
        cambio = next((m for lado, m in sin_prorroga if lado and lado != lado_inicial), None)
        if cambio is None:
            continue
        cuenta = por_tramo[_tramo_cambio(cambio[0] - cambio[1])]
        cuenta[0] += 1
        cuenta[1] += 1 if partida["won"] else 0

    # Mayor diferencia primero y, a igual diferencia, la mas reciente.
    for lista, clave in ((remontadas, "max_deficit"), (derrumbes, "max_lead")):
        lista.sort(key=lambda p: (p[clave], p["played_at"]), reverse=True)
    return {
        "remontadas": remontadas[:TOPE_LISTA],
        "derrumbes": derrumbes[:TOPE_LISTA],
        "remontadas_total": len(remontadas),
        "derrumbes_total": len(derrumbes),
        "by_side_change_diff": [
            {"diff": tramo, "matches": n, "wins": g, "winrate": _pct(g, n)}
            for tramo, (n, g) in por_tramo.items()
        ],
        "matches_known": conocidas,
    }


#: Orden fijo de las filas de `by_margin`: la prorroga va primero porque gana
#: a cualquier margen (una partida a prorroga es cerrada aunque termine 2 arriba).
TRAMOS_MARGEN = ("overtime", "1", "2", "3+")


def _tramo_margen(margen: int) -> str | None:
    if margen >= 3:
        return "3+"
    return str(margen) if margen > 0 else None


def by_margin(**filters) -> dict:
    """Partidas segun el margen final del marcador: prorroga, 1, 2 o 3 o mas rondas.

    Los filtros eligen partidas y cada partida se lee entera, como en
    `comebacks`: el lado no parte una partida, asi que `side` se ignora.
    """
    filtros = {k: v for k, v in filters.items() if k != "side"}
    ids = base_queryset(**filtros).values_list("round__match_id", flat=True).distinct()
    partidas = Match.objects.filter(id__in=ids)
    # Antes de Y9S4 el marcador no es confiable (ver `_marcador_conocido`);
    # sin resultado (empate o desconocido) no hay margen que leer.
    conocidas = partidas.filter(code_version__gte=Y9S4).exclude(won__isnull=True)
    con_prorroga = set(
        Round.objects.filter(match_id__in=conocidas.values("id"), overtime_number__gt=0)
        .values_list("match_id", flat=True)
    )
    por_tramo: dict[str, list[int]] = {tramo: [] for tramo in TRAMOS_MARGEN}
    ganadas = dict.fromkeys(TRAMOS_MARGEN, 0)
    for p in conocidas.values("id", "my_score", "opponent_score", "won"):
        if p["id"] in con_prorroga:
            tramo = "overtime"
        else:
            tramo = _tramo_margen(abs(p["my_score"] - p["opponent_score"]))
        if tramo is None:
            continue
        por_tramo[tramo].append(p["id"])
        ganadas[tramo] += 1 if p["won"] else 0

    baseline = rating_baseline()
    filas = []
    for tramo in TRAMOS_MARGEN:
        n = len(por_tramo[tramo])
        # Todas tus rondas de esas partidas, sin recortar por operador o
        # sitio: la partida se lee entera.
        t = totals(RoundPlayer.objects.filter(is_me=True, round__match_id__in=por_tramo[tramo]),
                   baseline)
        filas.append({
            "margin": tramo,
            "matches": n,
            "wins": ganadas[tramo],
            "winrate": _pct(ganadas[tramo], n),
            "rounds": t["rounds"] or 0,
            "rating": t["rating"],
            "kpr": t["kpr"],
        })
    medidas = sum(len(v) for v in por_tramo.values())
    return {
        "rows": filas,
        "matches_known": medidas,
        "matches_excluded": partidas.count() - medidas,
    }


#: Partidas decididas en un mapa para que cuente como mejor o peor. Bajo a
#: proposito (un mapa por semana alcanza); calibrar con la base real.
MIN_PARTIDAS_MAPA = 3


def racha_actual_de_partidas(partidas: list[dict]) -> dict | None:
    """Partidas seguidas con el mismo resultado, contando hacia atras desde la ultima.

    `partidas` llega en orden cronologico (`played_at`, `id`). Las de `won`
    nulo (empate o incompleta, ficha 68) se saltan sin cortar: no son un
    resultado, y un `.rec` faltante no deberia romperte la racha.
    """
    racha: list[dict] = []
    for p in reversed(partidas):
        if p["won"] is None:
            continue
        if racha and p["won"] != racha[0]["won"]:
            break
        racha.append(p)
    if not racha:
        return None
    racha.reverse()
    return {
        "result": "win" if racha[0]["won"] else "loss",
        "length": len(racha),
        "since": racha[0]["played_at"].isoformat(),
        "match_ids": [p["id"] for p in racha],
    }


def matches_summary(**filters) -> dict:
    """Tus partidas en una linea: ganadas, rondas por partida y mejor y peor mapa.

    Las partidas se eligen como en `by_margin`: el lado no parte una partida.
    Lo que `won` deja en nulo (empate o incompleta) no entra al winrate.
    """
    filtros = {k: v for k, v in filters.items() if k != "side"}
    ids = list(base_queryset(**filtros).values_list("round__match_id", flat=True).distinct())
    partidas = list(
        Match.objects.filter(id__in=ids)
        .values("id", "map_slug", "map_id", "map_name", "played_at", "won")
        .order_by("played_at", "id")
    )
    ganadas = sum(1 for p in partidas if p["won"] is True)
    perdidas = sum(1 for p in partidas if p["won"] is False)
    decididas = ganadas + perdidas
    rondas = RoundPlayer.objects.filter(is_me=True, round__match_id__in=ids).count()

    # Por version (`slug`, `map_id`), como la pagina Mapas: un rework es otro
    # layout. Un renombre dentro de la misma version no la parte, y como las
    # partidas vienen en orden de fecha el nombre queda el mas reciente.
    por_mapa: dict[tuple[str, int], dict] = {}
    for p in partidas:
        if p["won"] is None:
            continue
        m = por_mapa.setdefault(
            (p["map_slug"], p["map_id"]),
            {"slug": p["map_slug"], "map_id": p["map_id"], "matches": 0, "wins": 0},
        )
        m["map_name"] = p["map_name"]
        m["matches"] += 1
        m["wins"] += 1 if p["won"] else 0
    # `etiquetas_de_version` y no `etiquetas_de_mapas`: esa ordena por nombre
    # y se quedaria con un nombre viejo en vez del mas reciente.
    etiquetas = etiquetas_de_version(por_mapa.values())
    for m in por_mapa.values():
        del m["map_name"]
        m["map"] = etiquetas[(m["slug"], m["map_id"])]
    candidatos = [
        {**m, "winrate": _pct(m["wins"], m["matches"])}
        for m in por_mapa.values() if m["matches"] >= MIN_PARTIDAS_MAPA
    ]
    mejor = min(candidatos, key=lambda m: (-m["winrate"], -m["matches"], m["map"]), default=None)
    peor = min(candidatos, key=lambda m: (m["winrate"], -m["matches"], m["map"]), default=None)
    # Con un solo mapa o todos empatados, el peor seria el mismo numero que el
    # mejor: no hay un mapa por debajo que mostrar.
    if peor is not None and peor["winrate"] >= mejor["winrate"]:
        peor = None

    return {
        "matches": len(partidas),
        "matches_won": ganadas,
        "matches_lost": perdidas,
        "matches_decided": decididas,
        "matches_undecided": len(partidas) - decididas,
        "match_winrate": _pct(ganadas, decididas),
        "rounds": rondas,
        "rounds_per_match": _ratio(rondas, len(partidas), 1),
        "min_matches_map": MIN_PARTIDAS_MAPA,
        "best_map": mejor,
        "worst_map": peor,
        "current_streak": racha_actual_de_partidas(partidas),
    }


#: Orden fijo de las filas de `round_endings`.
LADOS_CIERRE = ("Attack", "Defense")


def round_endings(**filters) -> list[dict]:
    """Tus rondas de cada lado segun como terminaron: por eliminacion o sin ella.

    "Sin eliminacion" es `ObjectiveOrTime`, que en temporadas nuevas se infiere
    del reloj: no se parte en plant, defuse o tiempo porque el `.rec` no lo dice.
    """
    # Se usa `round__my_team_won` y no `won`: `won` es False cuando la ronda
    # no tiene ganador y la mandaria a perdidas en vez de a `unknown`.
    def _cuenta(gano: bool, condicion: str) -> Count:
        return Count("id", filter=Q(round__my_team_won=gano, round__win_condition=condicion))

    por_lado = {
        fila["side"]: fila
        for fila in base_queryset(**filters)
        .filter(side__in=LADOS_CIERRE)
        .values("side")
        .annotate(
            rounds=Count("id"),
            won_elimination=_cuenta(True, "KilledOpponents"),
            won_other=_cuenta(True, "ObjectiveOrTime"),
            lost_elimination=_cuenta(False, "KilledOpponents"),
            lost_other=_cuenta(False, "ObjectiveOrTime"),
        )
    }
    filas = []
    for lado in LADOS_CIERRE:
        fila = por_lado.get(lado, {})
        cuentas = {
            clave: fila.get(clave, 0)
            for clave in ("won_elimination", "won_other", "lost_elimination", "lost_other")
        }
        rounds = fila.get("rounds", 0)
        filas.append(
            {
                "side": lado,
                "rounds": rounds,
                **cuentas,
                # Resta y no filtro propio: sin ganador, sin condicion o una
                # condicion que el parser agregue manana caen aca, y la fila
                # suma todas tus rondas por construccion.
                "unknown": rounds - sum(cuentas.values()),
                "won_elimination_pct": _pct(
                    cuentas["won_elimination"], cuentas["won_elimination"] + cuentas["won_other"]
                ),
                "lost_elimination_pct": _pct(
                    cuentas["lost_elimination"], cuentas["lost_elimination"] + cuentas["lost_other"]
                ),
            }
        )
    return filas


#: Tramos fijos de `by_round_length`: (nombre, desde, hasta) en segundos de la
#: fase de accion. Cuartos de los 180 s de ranked; un modo mas corto llena
#: menos el ultimo.
TRAMOS_DURACION = (("0-45", 0, 45), ("45-90", 45, 90), ("90-135", 90, 135), ("135+", 135, None))
FILA_PLANT = "plant"
LADOS_DURACION = ("Attack", "Defense")
CAMPOS_DURACION = (
    "rounds", "rounds_won", "winrate", "rating", "kpr", "avg_duration_won", "avg_duration_lost",
)


def _duracion() -> ExpressionWrapper:
    """`Round.duration` en SQL; funcion por lo mismo que `rating_points_expr`."""
    return ExpressionWrapper(
        F("round__clock_start") - F("round__clock_end"), output_field=FloatField()
    )


def _promedios_de_duracion() -> dict:
    # `round__my_team_won` y no `won`: una ronda sin ganador no es "lo que
    # tardas en perder" (misma razon que en `round_endings`).
    return {
        "avg_duration_won": Avg(_duracion(), filter=Q(round__my_team_won=True)),
        "avg_duration_lost": Avg(_duracion(), filter=Q(round__my_team_won=False)),
    }


def _celda(raw: dict | None, baseline: float | None, *, con_metricas: bool = True) -> dict:
    if not raw or not raw.get("rounds"):
        return {campo: 0 if campo in ("rounds", "rounds_won") else None
                for campo in CAMPOS_DURACION}
    if not con_metricas:
        # Fila de posible plant: solo el conteo. Un winrate sobre un plant
        # inferido seria una metrica de plant, que el `.rec` no sostiene.
        celda = dict.fromkeys(CAMPOS_DURACION)
        celda.update({"rounds": raw["rounds"], "rounds_won": 0})
        return celda
    fila = derive(dict(raw), baseline)
    for clave in ("avg_duration_won", "avg_duration_lost"):
        if fila.get(clave) is not None:
            fila[clave] = round(fila[clave], 1)
    return {campo: fila.get(campo) for campo in CAMPOS_DURACION}


def _celdas_por_lado(qs: QuerySet[RoundPlayer], baseline: float | None, *,
                     con_metricas: bool = True) -> dict:
    """Ataque, defensa y total. El total cuenta tambien las rondas sin lado."""
    por_lado = {
        fila["side"]: fila
        for fila in qs.filter(side__in=LADOS_DURACION)
        .values("side")
        .annotate(**AGGREGATES, **_promedios_de_duracion())
    }
    total = qs.aggregate(**AGGREGATES, **_promedios_de_duracion())
    celdas = {lado: _celda(por_lado.get(lado), baseline, con_metricas=con_metricas)
              for lado in LADOS_DURACION}
    celdas["total"] = _celda(total, baseline, con_metricas=con_metricas)
    return celdas


def by_round_length(**filters) -> dict:
    """Tus rondas por cuanto duro la fase de accion, por lado.

    Un posible plant va a su fila y no a un tramo: despues del plant el reloj
    principal deja de correr y la resta no mide lo mismo. Un plant que termina
    en barrida no se marca y entra a un tramo con la duracion hasta el plant;
    el `.rec` no deja separarlo.
    """
    qs = base_queryset(**filters)
    baseline = rating_baseline()
    # `clock_last` ignora ceros: un `clock_end` en 0 solo sale del fallback de
    # `metrics._clock_start` y la resta no seria una duracion.
    sin_reloj = Q(round__clock_start__lte=0) | Q(round__clock_end__lte=0)
    # `alias` y no `annotate`: una anotacion seleccionada entraria al GROUP BY
    # de `values("side")` y partiria las filas por duracion. Por eso los
    # promedios arman su propia expresion en vez de leer el alias.
    con_reloj = qs.exclude(sin_reloj).alias(duracion=_duracion())
    medibles = con_reloj.filter(round__possible_plant=False)

    filas = []
    for nombre, desde, hasta in TRAMOS_DURACION:
        tramo = medibles
        # Sin piso en el primero: una resta negativa cae en 0-45, como el
        # `max(..., 0)` de `Round.duration`.
        if desde:
            tramo = tramo.filter(duracion__gte=desde)
        if hasta is not None:
            tramo = tramo.filter(duracion__lt=hasta)
        filas.append({"length": nombre, **_celdas_por_lado(tramo, baseline)})
    filas.append({
        "length": FILA_PLANT,
        **_celdas_por_lado(con_reloj.filter(round__possible_plant=True), baseline,
                           con_metricas=False),
    })
    return {
        "rows": filas,
        "summary": _celdas_por_lado(medibles, baseline),
        "rounds_unknown_clock": qs.filter(sin_reloj).count(),
    }


def by_hour(**filters) -> list[dict]:
    """Ocho franjas fijas de 3 horas segun la hora de inicio de la partida.

    La hora es la que guardo el PC (`USE_TZ = False`): sin conversion, que es
    justamente la hora en que el usuario se sento a jugar.
    """
    qs = base_queryset(**filters)
    tramos = {
        h: qs.filter(round__match__played_at__hour__gte=h, round__match__played_at__hour__lt=h + 3)
        for h in range(0, 24, 3)
    }
    return _filas_por_tramo("hour_from", tramos)


def by_weekday(**filters) -> list[dict]:
    """Lunes a domingo segun el dia de inicio de la partida."""
    qs = base_queryset(**filters)
    # `iso_week_day` cuenta 1=lunes; `week_day` de Django cuenta 1=domingo y
    # correria el domingo al principio de la semana.
    tramos = {d: qs.filter(round__match__played_at__iso_week_day=d) for d in range(1, 8)}
    return _filas_por_tramo("weekday", tramos)


def by_start_side(**filters) -> list[dict]:
    """Partidas y winrate de partida segun el lado con que arrancaste."""
    ids = base_queryset(**filters).values_list("round__match_id", flat=True).distinct()
    partidas = Match.objects.filter(id__in=ids).annotate(lado=_lado_inicial("id"))
    filas = []
    for lado in ("Attack", "Defense"):
        suyas = partidas.filter(lado=lado)
        decididas = suyas.exclude(won__isnull=True)
        wins = decididas.filter(won=True).count()
        n_decididas = decididas.count()
        filas.append(
            {
                "side": lado,
                "matches": suyas.count(),
                "decided": n_decididas,
                "wins": wins,
                "winrate": _pct(wins, n_decididas),
            }
        )
    return filas


def by_gamemode(**filters) -> list[dict]:
    """Tus partidas agrupadas por el modo de juego de la cabecera del `.rec`.

    El modo es de la partida: con filtro de lado, el winrate de partida sigue
    siendo el de la partida entera, como `by_start_side`. Una partida sin modo
    (cabeceras viejas) queda en su propia fila con `gamemode` vacio.
    """
    por_partida = _por_partida(**filters)
    datos = {
        mid: (modo, won)
        for mid, modo, won in Match.objects.filter(id__in=list(por_partida))
        .values_list("id", "gamemode", "won")
    }
    baseline = rating_baseline()
    grupos: dict[str, list[int]] = {}
    for mid in por_partida:
        grupos.setdefault(datos[mid][0] or "", []).append(mid)

    filas = []
    for modo, mids in grupos.items():
        t = _fold([por_partida[m] for m in mids], baseline)
        decididas = [datos[m][1] for m in mids if datos[m][1] is not None]
        filas.append({
            "gamemode": modo,
            "matches": len(mids),
            "matches_decided": len(decididas),
            "matches_won": sum(decididas),
            "match_winrate": _pct(sum(decididas), len(decididas)),
            "rounds": t["rounds"] or 0,
            "rounds_won": t["rounds_won"] or 0,
            "winrate": t["winrate"],
            "kd": t["kd"],
            "rating": t["rating"],
        })
    filas.sort(key=lambda f: (-f["matches"], f["gamemode"]))
    return filas


#: Partidas decididas por lado inicial para que un mapa de veredicto. Es el
#: minimo de mapa de la ficha 64: con menos, un 100 % o un 0 % es lo normal.
MIN_PARTIDAS_LADO_INICIAL = MIN_PARTIDAS_MAPA


def _celda_lado_inicial(partidas: int, decididas: int, wins: int) -> dict:
    # Los conteos salen aunque no lleguen al minimo: la tabla muestra la
    # muestra que hay aunque todavia no tenga porcentaje.
    winrate = _pct(wins, decididas) if decididas >= MIN_PARTIDAS_LADO_INICIAL else None
    return {"matches": partidas, "decided": decididas, "wins": wins, "winrate": winrate}


def by_start_side_map(**filters) -> list[dict]:
    """`by_start_side` partido por version de mapa, con banda de ruido.

    La banda usa la proporcion combinada de los dos lados (`_ruido_combinado`)
    y no `_ruido` (Wald): con 3 a 5 partidas por lado un 100 % o un 0 % es lo
    normal, y Wald da varianza cero ahi y veredicto por azar.
    """
    ids = base_queryset(**filters).values_list("round__match_id", flat=True).distinct()
    partidas = (
        Match.objects.filter(id__in=ids)
        .annotate(lado=_lado_inicial("id"))
        .values("map_slug", "map_id", "lado", "won")
    )
    por_mapa: dict[tuple[str, int], dict] = {}
    for p in partidas:
        if p["lado"] not in ("Attack", "Defense"):
            continue
        clave = (p["map_slug"], p["map_id"])
        conteo = por_mapa.setdefault(
            clave, {lado: [0, 0, 0] for lado in ("Attack", "Defense")}
        )[p["lado"]]
        conteo[0] += 1
        if p["won"] is not None:
            conteo[1] += 1
            conteo[2] += int(p["won"])
    if not por_mapa:
        return []

    etiquetas = etiquetas_de_mapas({slug for slug, _ in por_mapa})
    filas = []
    for (slug, map_id), lados in por_mapa.items():
        ataque = _celda_lado_inicial(*lados["Attack"])
        defensa = _celda_lado_inicial(*lados["Defense"])
        delta = margen = veredicto = None
        if ataque["winrate"] is not None and defensa["winrate"] is not None:
            delta = _delta(ataque["winrate"], defensa["winrate"])
            margen, veredicto = _margen_y_veredicto(
                delta, ataque["wins"], ataque["decided"],
                ataque["wins"] + defensa["wins"],
                ataque["decided"] + defensa["decided"],
                ("ataque", "defensa"),
            )
        filas.append(
            {
                "slug": slug,
                "map_id": map_id,
                "map": etiquetas.get((slug, map_id), slug),
                "matches": ataque["matches"] + defensa["matches"],
                "attack": ataque,
                "defense": defensa,
                "delta": delta,
                "margin": margen,
                "verdict": veredicto,
            }
        )
    filas.sort(key=lambda f: (-f["matches"], f["map"]))
    return filas


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
            "round__match_id", "round__match__played_at", "round__match__map_name",
            "round__match__map_slug", "round__match__map_id",
        )
        .annotate(**AGGREGATES)
        .order_by("-round__match__played_at")[:limit]
    ):
        row = dict(raw)
        row["match_id"] = row.pop("round__match_id")
        row["played_at"] = row.pop("round__match__played_at").isoformat()
        row["map"] = row.pop("round__match__map_name")
        # `map_version` al final y no `map_id`: `map_id` esta entre las
        # primeras columnas del CSV y moveria las que ya existen.
        row["_version"] = (row.pop("round__match__map_slug"), row.pop("round__match__map_id"))
        rows.append(derive(row, baseline))
    etiquetas = etiquetas_de_mapas({r["_version"][0] for r in rows})
    for row in rows:
        clave = row.pop("_version")
        row["map_version"] = etiquetas.get(clave, row["map"])
    return list(reversed(rows))


#: Dos promedios de float que deberian ser iguales pueden diferir en el ultimo
#: bit segun el orden en que SQLite los sumo: por debajo de esto es empate.
EMPATE_RATING = 1e-9


def lobby_rank(**filters) -> dict:
    """En cuantas partidas fuiste el mejor, el mejor de tu equipo y el ultimo.

    Se compara el rating de la partida de cada jugador (promedio de sus puntos
    por ronda) en las rondas que dejan los filtros: un filtro de ronda (lado,
    operador, sitio) recorta las mismas rondas para todos. No se divide por
    `rating_baseline()`: no cambia el orden.
    """
    mias = base_queryset(**filters)
    # Correlacionadas en vez de un IN con los round_id, como `teammate_synergy`
    # (tope de parametros de SQLite).
    filas = (
        RoundPlayer.objects.filter(Exists(mias.filter(round_id=OuterRef("round_id"))))
        .values("round__match_id", "player_id")
        .annotate(points=Avg(rating_points_expr()), rounds=Count("id"))
    )
    companeros = set(
        RoundPlayer.objects.filter(is_me=False)
        .filter(Exists(mias.filter(round_id=OuterRef("round_id"),
                                   team_index=OuterRef("team_index"))))
        .values_list("round__match_id", "player_id")
        .distinct()
    )
    yo = set(Player.objects.filter(is_me=True).values_list("id", flat=True))

    por_partida: dict[int, list[dict]] = {}
    for fila in filas:
        por_partida.setdefault(fila["round__match_id"], []).append(fila)

    cuentas = Counter()
    for match_id, jugadores in por_partida.items():
        mios = [j for j in jugadores if j["player_id"] in yo]
        if not mios:
            continue
        # Dos filas "yo" en una partida no las produce el import; si pasara,
        # vale la de mas rondas y la otra es un jugador mas.
        mio = max(mios, key=lambda j: (j["rounds"], -j["player_id"]))
        otros = [j for j in jugadores if j is not mio]
        if not otros:
            continue
        puntos = mio["points"]
        cuentas["lobby"] += 1
        if all(o["points"] <= puntos + EMPATE_RATING for o in otros):
            cuentas["best_in_lobby"] += 1
        if all(o["points"] >= puntos - EMPATE_RATING for o in otros):
            cuentas["last_in_lobby"] += 1
        equipo = [o for o in otros if (match_id, o["player_id"]) in companeros]
        if equipo:
            cuentas["team"] += 1
            if all(o["points"] <= puntos + EMPATE_RATING for o in equipo):
                cuentas["best_in_team"] += 1

    def caso(clave: str, total: str) -> dict:
        return {
            "count": cuentas[clave],
            "matches": cuentas[total],
            "pct": _pct(cuentas[clave], cuentas[total]),
        }

    return {
        "best_in_lobby": caso("best_in_lobby", "lobby"),
        "best_in_team": caso("best_in_team", "team"),
        "last_in_lobby": caso("last_in_lobby", "lobby"),
    }


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


#: Partidas juntas en tu equipo para ser habitual. Se mide sobre todo el
#: historial y sin filtros: un filtro de mapa no cambia con quien jugas.
MIN_PARTIDAS_HABITUAL = 5

#: Orden fijo de `by_stack`; el indice es la cantidad de habituales (3 o mas = stack).
GRUPOS = ("solo", "duo", "trio", "stack")


def by_stack(**filters) -> dict:
    """Tus partidas segun cuantos companeros habituales jugaron en tu equipo.

    El grupo es un dato de la partida, no de la ronda: se cuenta sobre todas
    sus rondas, sin filtros. Los filtros solo eligen que partidas y que rondas
    entran a cada fila.
    """
    # Sin filtros y correlacionada, como `teammate_synergy` (tope de
    # parametros de SQLite con un IN de round_ids).
    mia = RoundPlayer.objects.filter(
        is_me=True, round_id=OuterRef("round_id"), team_index=OuterRef("team_index")
    )
    companeros = RoundPlayer.objects.filter(is_me=False).filter(Exists(mia))
    # El nombre sale de Player: un cambio de nick no parte al habitual.
    habituales = list(
        companeros.values("player_id", "player__username")
        .annotate(n=Count("round__match_id", distinct=True))
        .filter(n__gte=MIN_PARTIDAS_HABITUAL)
        .order_by("-n", "player__username")
    )
    ids_hab = [h["player_id"] for h in habituales]

    por_partida = _por_partida(**filters)
    ids = base_queryset(**filters).values("round__match_id")
    grupo: Counter[int] = Counter()
    if ids_hab:
        grupo = Counter(
            mid for mid, _ in companeros.filter(player_id__in=ids_hab, round__match_id__in=ids)
            .values_list("round__match_id", "player_id")
            # sin el orden del modelo: entraria al DISTINCT y repetiria pares
            .order_by()
            .distinct()
        )
    won = dict(Match.objects.filter(id__in=ids).values_list("id", "won"))
    baseline = rating_baseline()

    por_grupo: dict[str, list[int]] = {g: [] for g in GRUPOS}
    for mid in por_partida:
        por_grupo[GRUPOS[min(grupo.get(mid, 0), len(GRUPOS) - 1)]].append(mid)

    filas = []
    for i, g in enumerate(GRUPOS):
        mids = por_grupo[g]
        t = _fold([por_partida[m] for m in mids], baseline)
        # Resultado entero de la partida aunque un filtro de lado recorte sus
        # rondas, como `by_start_side`. Sin resultado (empate o incompleta)
        # no entra al winrate de partida.
        decididas = [won[m] for m in mids if won.get(m) is not None]
        filas.append({
            "group": g,
            "regulars": i,
            "matches": len(mids),
            "matches_decided": len(decididas),
            "matches_won": sum(decididas),
            "match_winrate": _pct(sum(decididas), len(decididas)),
            "rounds": t["rounds"] or 0,
            "rounds_won": t["rounds_won"] or 0,
            "winrate": t["winrate"],
            "rating": t["rating"],
        })
    return {
        "rows": filas,
        "regulars": [
            {"player_id": h["player_id"], "username": h["player__username"], "matches": h["n"]}
            for h in habituales
        ],
        "min_matches": MIN_PARTIDAS_HABITUAL,
    }


LADOS_PRIMERA_CAIDA = ("Attack", "Defense", "total")


def _quien_cae_primero(mi_elapsed: float | None, elapsed_companeros: list[float]) -> str:
    """Clasifica una ronda segun quien de tu equipo cayo primero.

    `"tie"` queda para que lo resuelva el feed: el elapsed sale del reloj en
    segundos y un doble kill empata seguido. Un elapsed 0 tambien va al feed:
    `metrics` lo pone cuando el evento no trae reloj (o el reloj ya marcaba
    0:00 al cierre), asi que no prueba que esa muerte fuera la primera.
    """
    muertes = [e for e in elapsed_companeros if e is not None]
    if mi_elapsed is None:
        return "mate" if muertes else "none"
    if not muertes:
        return "me"
    menor = min(muertes)
    if mi_elapsed == 0 or menor == 0:
        return "tie"
    if mi_elapsed < menor:
        return "me"
    if mi_elapsed > menor:
        return "mate"
    return "tie"


def _primer_orden_de_muerte(mias, round_ids: set[int]) -> dict[tuple[int, int], int]:
    """(round_id, player_id) -> `order` del primer evento de muerte del jugador.

    Misma eleccion que `metrics.analyse_round`: la primera muerte del feed.
    """
    primero: dict[tuple[int, int], int] = {}
    # Correlacionada en vez de `round_id__in`: con muchas rondas empatadas la
    # lista pasaria el tope de parametros de SQLite. Se filtra en Python.
    eventos = (
        Event.objects.filter(
            Exists(mias.filter(round_id=OuterRef("round_id"))),
            kind__in=(Event.KILL, Event.DEATH),
        )
        .order_by("order")
        .values("round_id", "order", "kind", "actor_id", "target_id")
    )
    for e in eventos:
        if e["round_id"] not in round_ids:
            continue
        victima = e["target_id"] if e["kind"] == Event.KILL else e["actor_id"]
        if victima is not None:
            primero.setdefault((e["round_id"], victima), e["order"])
    return primero


def first_teammate_death(**filters) -> list[dict]:
    """Rondas en que fuiste el primero de tu equipo en caer, y su winrate.

    Distinto de `opening_death`, que es la primera baja de toda la ronda: aca
    una muerte rival anterior no cuenta. En un empate de `death_elapsed`
    decide el orden del feed; si falta el evento de alguno, va al companero,
    para no cargarte una muerte que no se puede probar.
    """
    mias = base_queryset(**filters)
    # Correlacionada por el tope de parametros de SQLite, como teammate_synergy.
    mismo_equipo = mias.filter(round_id=OuterRef("round_id"), team_index=OuterRef("team_index"))
    equipo = (
        RoundPlayer.objects.filter(Exists(mismo_equipo))
        .values("round_id", "player_id", "is_me", "death_elapsed")
    )
    por_ronda: dict[int, dict] = {}
    for fila in equipo:
        ronda = por_ronda.setdefault(fila["round_id"], {"me": None, "mates": []})
        if fila["is_me"]:
            ronda["me"] = fila
        else:
            ronda["mates"].append(fila)

    clases: dict[int, str] = {}
    empates: list[int] = []
    for round_id, ronda in por_ronda.items():
        if ronda["me"] is None:
            continue
        clase = _quien_cae_primero(
            ronda["me"]["death_elapsed"], [m["death_elapsed"] for m in ronda["mates"]]
        )
        clases[round_id] = clase
        if clase == "tie":
            empates.append(round_id)

    if empates:
        orden = _primer_orden_de_muerte(mias, set(empates))
        for round_id in empates:
            ronda = por_ronda[round_id]
            mio = orden.get((round_id, ronda["me"]["player_id"]))
            mi_elapsed = ronda["me"]["death_elapsed"]
            # Con un reloj en 0 de por medio el elapsed no ordena nada: se compara
            # contra todos los companeros que murieron, no solo los empatados.
            sin_reloj = mi_elapsed == 0 or any(m["death_elapsed"] == 0 for m in ronda["mates"])
            suyos = [
                orden.get((round_id, m["player_id"]))
                for m in ronda["mates"]
                if m["death_elapsed"] is not None
                and (sin_reloj or m["death_elapsed"] == mi_elapsed)
            ]
            if mio is None or any(o is None for o in suyos):
                clases[round_id] = "mate"
            else:
                clases[round_id] = "me" if mio < min(suyos) else "mate"

    grupos = {"me": "me_first", "mate": "mate_first", "none": "no_deaths"}
    cuentas = {lado: {g: [0, 0] for g in grupos.values()} for lado in LADOS_PRIMERA_CAIDA}
    for fila in mias.values("round_id", "side", "won"):
        clase = clases.get(fila["round_id"])
        if clase is None:
            continue
        lados = ["total"] + ([fila["side"]] if fila["side"] in ("Attack", "Defense") else [])
        for lado in lados:
            par = cuentas[lado][grupos[clase]]
            par[0] += 1
            par[1] += 1 if fila["won"] else 0

    salida = []
    for lado in LADOS_PRIMERA_CAIDA:
        fila = {"side": lado, "rounds": sum(n for n, _ in cuentas[lado].values())}
        for grupo, (n, ganadas) in cuentas[lado].items():
            fila[grupo] = n
            fila[f"{grupo}_won"] = ganadas
            fila[f"{grupo}_winrate"] = _pct(ganadas, n)
        salida.append(fila)
    return salida


ESTADO_AL_MORIR_GRUPOS = ("ahead", "even", "behind")


def death_state(**filters) -> dict:
    """Tus muertes por estado de vivos (tuyos contra rivales) justo antes de caer.

    Se calcula al consultar sobre el feed, como `nemesis`: guardarlo en
    `RoundPlayer` pediria migracion y `recompute`. El algoritmo vive en
    `metrics.estado_al_morir` para que pasarlo a columna sea mecanico. Sin
    normalizar a 5v5: se cuentan los jugadores que tiene la ronda.
    """
    mias = base_queryset(**filters).filter(died=True)
    filas = list(mias.values("round_id", "player_id", "round__my_team_won"))

    # Correlacionadas por el tope de parametros de SQLite, como first_teammate_death.
    en_mis_rondas = Exists(mias.filter(round_id=OuterRef("round_id")))
    equipos: dict[int, dict[int, int]] = {}
    for fila in RoundPlayer.objects.filter(en_mis_rondas).values(
        "round_id", "player_id", "team_index"
    ):
        equipos.setdefault(fila["round_id"], {})[fila["player_id"]] = fila["team_index"]
    feeds: dict[int, list[dict]] = {}
    for ev in (
        Event.objects.filter(en_mis_rondas, kind__in=(Event.KILL, Event.DEATH, PLAYER_LEAVE))
        .order_by("round_id", "order")
        .values("round_id", "kind", "actor_id", "target_id")
    ):
        feeds.setdefault(ev["round_id"], []).append(
            {"kind": ev["kind"], "actor": ev["actor_id"], "target": ev["target_id"]}
        )

    estados: dict[tuple[int, int], dict] = {}
    grupos = {g: _caso_vacio() for g in ESTADO_AL_MORIR_GRUPOS}
    sin_feed = 0
    for fila in filas:
        round_id = fila["round_id"]
        par = estado_al_morir(feeds.get(round_id, []), equipos.get(round_id, {})).get(
            fila["player_id"]
        )
        if par is None:
            sin_feed += 1
            continue
        aliados, rivales = par
        grupo = "ahead" if aliados > rivales else "even" if aliados == rivales else "behind"
        caso = estados.setdefault(par, {
            "state": f"{aliados}v{rivales}", "allies": aliados, "enemies": rivales,
            "group": grupo, **_caso_vacio(),
        })
        _sumar_caso(caso, fila["round__my_team_won"])
        _sumar_caso(grupos[grupo], fila["round__my_team_won"])

    salida_grupos = [{"group": g, **grupos[g]} for g in ESTADO_AL_MORIR_GRUPOS]
    salida_estados = sorted(estados.values(), key=lambda f: (-f["allies"], f["enemies"]))
    for caso in [*salida_grupos, *salida_estados]:
        caso["winrate"] = _pct(caso["won"], caso["decided"])
    return {
        "deaths": sum(g["rounds"] for g in salida_grupos),
        "sin_feed": sin_feed,
        "states": salida_estados,
        "groups": salida_grupos,
    }


#: Desde aca los clutches se agrupan: 1v5 y lo que pase de ahi (rondas con
#: mas de cinco por lado, modos raros) van a la misma fila.
CLUTCH_X_MAX = 5

# el % de silenciosos es sobre los ganados de la fila, asi que el corte de
# muestra chica tambien: a diferencia de sitio y operador, que cortan sobre
# intentos. Es semantica nueva en esta tabla, que antes no marcaba muestra chica
CLUTCH_SILENCIOSO_MIN = 5


def clutch_conversion(**filters) -> list[dict]:
    """Intentos y ganados por cantidad de rivales cuando quedaste ultimo.

    Lee `clutch_vs`, no `one_vx`: `one_vx` solo existe cuando ganaste, asi que
    con el no hay denominador.
    """
    # una ronda sin ganador conocido (.rec cortado justo al final, que es donde
    # esta el clutch) tiene won=False: contarla seria sumar un intento perdido
    filas = (
        base_queryset(**filters)
        .filter(clutch_vs__gt=0, round__my_team_won__isnull=False)
        .values("clutch_vs", "side")
        .annotate(
            attempts=Count("id"),
            won=Count("id", filter=Q(round__my_team_won=True)),
            silent=Count("id", filter=Q(round__my_team_won=True, clutch_kills=0)),
        )
    )
    por_x: dict[int, dict] = {}
    for f in filas:
        vs = min(f["clutch_vs"], CLUTCH_X_MAX)
        fila = por_x.setdefault(
            vs, {"attempts": 0, "won": 0, "silent": 0, "Attack": [0, 0, 0], "Defense": [0, 0, 0]}
        )
        fila["attempts"] += f["attempts"]
        fila["won"] += f["won"]
        fila["silent"] += f["silent"]
        if f["side"] in ("Attack", "Defense"):
            fila[f["side"]][0] += f["attempts"]
            fila[f["side"]][1] += f["won"]
            fila[f["side"]][2] += f["silent"]

    def _lado(par):
        return {"attempts": par[0], "won": par[1], "silent": par[2], "pct": _pct(par[1], par[0])}

    return [
        {
            "vs": vs,
            "label": f"1v{vs}+" if vs == CLUTCH_X_MAX else f"1v{vs}",
            "attempts": fila["attempts"],
            "won": fila["won"],
            "pct": _pct(fila["won"], fila["attempts"]),
            "silent": fila["silent"],
            "silent_pct": _pct(fila["silent"], fila["won"]),
            "silent_low_sample": 0 < fila["won"] < CLUTCH_SILENCIOSO_MIN,
            "attack": _lado(fila["Attack"]),
            "defense": _lado(fila["Defense"]),
        }
        for vs, fila in sorted(por_x.items())
    ]


def clutch_silent(**filters) -> dict:
    """Clutches ganados sin bajas tuyas desde que quedaste solo, por condicion de victoria.

    `other` es `ObjectiveOrTime`, que en temporadas nuevas se infiere del reloj
    (`docs/formato-rec.md`) y no se parte en plant, defuse o tiempo. Se usa
    `win_condition` y no `win_condition_certain` para cuadrar con "Como se
    cierran tus rondas" (hoy son equivalentes); una condicion certera nueva del
    parser caeria en `unknown` hasta decidir donde va.
    """
    silencioso = Q(clutch_kills=0)
    totales = (
        base_queryset(**filters)
        .filter(clutch_vs__gt=0, round__my_team_won=True)
        .aggregate(
            won=Count("id"),
            silent=Count("id", filter=silencioso),
            elimination=Count("id", filter=silencioso & Q(round__win_condition="KilledOpponents")),
            other=Count("id", filter=silencioso & Q(round__win_condition="ObjectiveOrTime")),
        )
    )
    # por resta, como round_endings: lo que no es ninguna de las dos es sin dato
    unknown = totales["silent"] - totales["elimination"] - totales["other"]
    return {
        "won": totales["won"],
        "silent": totales["silent"],
        "silent_pct": _pct(totales["silent"], totales["won"]),
        "by_condition": {
            "elimination": totales["elimination"],
            "other": totales["other"],
            "unknown": unknown,
        },
    }


# por debajo de esto el % de un sitio es anecdota: la fila sale igual, marcada
CLUTCH_SITIO_MIN = 5


def clutch_by_site(**filters) -> list[dict]:
    """Intentos y ganados de clutch por mapa y sitio de bomba.

    Por mapa, primero la fila total y despues sus sitios; mismo intento y
    ganado que `clutch_conversion`.
    """
    # mismo motivo que en clutch_conversion: sin ganador conocido no es intento
    filas = (
        base_queryset(**filters)
        .filter(clutch_vs__gt=0, round__my_team_won__isnull=False)
        .values("round__match__map_slug", "round__match__map_id", "round__site")
        .annotate(attempts=Count("id"), won=Count("id", filter=Q(round__my_team_won=True)))
    )
    # Por version, como Mapas: un rework cambia los sitios aunque se llamen
    # igual. Sin `map_name` en la agrupacion, asi un renombre no parte la fila.
    filas = list(filas)
    etiquetas = etiquetas_de_mapas({f["round__match__map_slug"] for f in filas})
    mapas: dict[tuple[str, int], dict] = {}
    for f in filas:
        clave = (f["round__match__map_slug"], f["round__match__map_id"])
        mapa = mapas.setdefault(clave, {"map": etiquetas.get(clave, clave[0]), "sitios": {}})
        sitio = mapa["sitios"].setdefault(f["round__site"], [0, 0])
        sitio[0] += f["attempts"]
        sitio[1] += f["won"]

    def _fila(kind, clave, nombre, site, attempts, won):
        return {
            "kind": kind,
            "slug": clave[0],
            "map_id": clave[1],
            "map": nombre,
            "site": site,
            "attempts": attempts,
            "won": won,
            "pct": _pct(won, attempts),
            "low_sample": attempts < CLUTCH_SITIO_MIN,
        }

    salida = []
    for clave, mapa in sorted(mapas.items(), key=lambda par: (par[1]["map"], par[0])):
        sitios = mapa["sitios"]
        # "Sin sitio" va ultima: no es un lugar del mapa al que volver a mirar
        orden = sorted(sitios.items(), key=lambda par: (par[0] == "", -par[1][0], par[0]))
        salida.append(
            _fila(
                "map",
                clave,
                mapa["map"],
                None,
                sum(a for a, _ in sitios.values()),
                sum(w for _, w in sitios.values()),
            )
        )
        salida.extend(
            _fila("site", clave, mapa["map"], site or "Sin sitio", a, w) for site, (a, w) in orden
        )
    return salida


# propio y no CLUTCH_SITIO_MIN: son cortes distintos que se calibran por separado;
# por debajo de esto el % de un operador es anecdota y la fila sale marcada
CLUTCH_OPERADOR_MIN = 5


def clutch_by_operator(**filters) -> list[dict]:
    """Intentos y ganados de clutch por operador y lado.

    Mismo intento y ganado que `clutch_conversion`; las rondas sin operador o
    sin lado no salen, asi que la suma puede quedar por debajo de la de la
    conversion.
    """
    # mismo motivo que en clutch_conversion: sin ganador conocido no es intento
    filas = (
        base_queryset(**filters)
        .filter(clutch_vs__gt=0, round__my_team_won__isnull=False)
        .exclude(operator="")
        .values("operator", "side")
        .annotate(attempts=Count("id"), won=Count("id", filter=Q(round__my_team_won=True)))
    )
    salida = [
        {
            "operator": f["operator"],
            "side": f["side"],
            "attempts": f["attempts"],
            "won": f["won"],
            "pct": _pct(f["won"], f["attempts"]),
            "low_sample": f["attempts"] < CLUTCH_OPERADOR_MIN,
        }
        # el lado es parte de la clave: una fila sin lado no dice nada aca
        for f in filas
        if f["side"] in ("Attack", "Defense")
    ]
    salida.sort(key=lambda f: (-f["attempts"], f["operator"], f["side"]))
    return salida


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


def _extremos_de_sesion(ids: list[int], por_partida: dict[int, dict], info: dict[int, dict],
                        etiquetas: dict[tuple[str, int], str],
                        baseline: float | None) -> tuple[dict | None, dict | None]:
    """Mejor y peor partida de una sesion por el rating de tus rondas en ella.

    Con una sola partida no hay extremos: "mejor" y "peor" serian la misma.
    """
    candidatas = []
    for mid in ids:
        # Copia: `derive` hace pop de los alias y la fila de `por_partida` es compartida.
        rating = derive(dict(por_partida[mid]), baseline)["rating"]
        if rating is not None:
            candidatas.append((rating, info[mid]))
    if len(candidatas) < 2:
        return None, None
    # Empate: gana la jugada antes, asi el resultado no depende del orden de la query.
    candidatas.sort(key=lambda c: (c[1]["played_at"], c[1]["id"]))
    mejor = max(candidatas, key=lambda c: c[0])
    peor = min(candidatas, key=lambda c: c[0])

    def resumen(rating, m):
        return {
            "id": m["id"],
            "map": etiquetas.get((m["map_slug"], m["map_id"]), m["map_name"]),
            "score": f"{m['my_score']}-{m['opponent_score']}",
            "won": m["won"],
            "rating": round(rating, 2),
        }

    # Todas con el mismo rating: no hay una peor que senalar (igual que el peor
    # mapa de `matches_summary`).
    return resumen(*mejor), (resumen(*peor) if peor[0] != mejor[0] else None)


def sessions(limit: int = 30, **filters) -> list[dict]:
    """Resumen de cada sesion de juego, de la mas reciente hacia atras."""
    por_partida = _por_partida(**filters)
    baseline = rating_baseline()  # una vez por request, no una por sesion
    info = {
        m["id"]: m
        for m in Match.objects.filter(id__in=list(por_partida)).values(
            "id", "map_slug", "map_id", "map_name", "my_score", "opponent_score", "won",
            "played_at",
        )
    }
    etiquetas = etiquetas_de_mapas({m["map_slug"] for m in info.values()})
    salida = []
    for sesion in _sessions_raw()[:limit]:
        ids = [mid for mid in sesion["match_ids"] if mid in por_partida]
        if not ids:
            continue
        fila = _fold([por_partida[mid] for mid in ids], baseline)
        # `won=None` (partida sin cerrar, ficha 68) no es ni ganada ni perdida.
        wins = sum(1 for mid in ids if info[mid]["won"] is True)
        losses = sum(1 for mid in ids if info[mid]["won"] is False)
        mejor, peor = _extremos_de_sesion(ids, por_partida, info, etiquetas, baseline)
        fila.update(
            {
                "index": sesion["index"],
                "start": sesion["start"].isoformat(),
                "end": sesion["end"].isoformat(),
                "matches": len(ids),
                "hours": round(
                    (sesion["end"] - sesion["start"]).total_seconds() / 3600, 1
                ),
                "wins": wins,
                "losses": losses,
                "decided": wins + losses,
                "undecided": len(ids) - wins - losses,
                "best_match": mejor,
                "worst_match": peor,
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


def _equipo_de(campo: str) -> Subquery:
    """El equipo, en la ronda del evento, del jugador que nombra `campo`."""
    return Subquery(
        RoundPlayer.objects.filter(
            round_id=OuterRef("round_id"), player_id=OuterRef(campo)
        ).values("team_index")[:1]
    )


def _solo_rivales(qs: QuerySet[Event], campo: str) -> QuerySet[Event]:
    """Descarta los teamkills: el otro tiene que estar en el equipo contrario.

    Importa porque la misma persona puede ser companero en unas rondas y rival
    en otras, y matarte por error no es ganarte un duelo.
    """
    return (
        qs.annotate(
            mi_equipo=_MI_EQUIPO,
            equipo_rival=_equipo_de(campo),
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


def _teamkills(mine: QuerySet[RoundPlayer]) -> QuerySet[Event]:
    """Bajas entre companeros de tu equipo, el espejo de `_solo_rivales`.

    El equipo se lee por ronda: la misma persona como rival en otra ronda no
    es un teamkill. Un suicidio tampoco, aunque autor y victima coincidan.
    """
    return (
        _mis_bajas(mine)
        .annotate(
            mi_equipo=_MI_EQUIPO,
            eq_autor=_equipo_de("actor_id"),
            eq_victima=_equipo_de("target_id"),
        )
        .exclude(mi_equipo=None)
        .filter(eq_autor=F("mi_equipo"), eq_victima=F("mi_equipo"))
        .exclude(actor_id=F("target_id"))
    )


def teamkills(**filters) -> dict:
    """Teamkills hechos y sufridos, con quien, y que pasa con esas rondas.

    No se restan de Bajas ni del Rating: aca solo se hacen visibles.
    """
    vacio = {
        "mine": 0,
        "suffered": 0,
        "rounds_with": 0,
        "rounds_without": 0,
        "winrate_with": None,
        "winrate_without": None,
        "by_teammate": [],
    }
    me_ids = _me_ids()
    if not me_ids:
        return vacio
    mine = base_queryset(**filters)
    tks = _teamkills(mine)
    rondas = set(tks.values_list("round_id", flat=True))
    con = mine.filter(round_id__in=rondas)
    sin = mine.exclude(round_id__in=rondas)
    rounds_with, rounds_without = con.count(), sin.count()

    rows: dict[int, dict] = {}

    def sumar(qs, id_field: str, name_field: str, clave: str) -> None:
        for raw in qs.values(id_field, name_field).annotate(n=Count("id")):
            pid = raw[id_field]
            if pid is None or pid in me_ids:
                continue
            fila = rows.setdefault(
                pid, {"player_id": pid, "username": raw[name_field], "made": 0, "suffered": 0}
            )
            fila[clave] += raw["n"]

    hechos = tks.filter(actor_id__in=me_ids)
    sufridos = tks.filter(target_id__in=me_ids)
    sumar(hechos, "target_id", "target__username", "made")
    sumar(sufridos, "actor_id", "actor__username", "suffered")
    for fila in rows.values():
        fila["total"] = fila["made"] + fila["suffered"]

    return {
        "mine": hechos.count(),
        "suffered": sufridos.count(),
        "rounds_with": rounds_with,
        "rounds_without": rounds_without,
        "winrate_with": _pct(con.filter(won=True).count(), rounds_with),
        "winrate_without": _pct(sin.filter(won=True).count(), rounds_without),
        "by_teammate": sorted(rows.values(), key=lambda r: (-r["total"], r["username"])),
    }


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


def _rivales_por_ronda(me_ids: list[int], **filters) -> dict[tuple[int, int], set[int]]:
    """(match_id, round_id) -> Player.id de quienes estuvieron en el equipo
    contrario en esa ronda tuya filtrada.

    El equipo se lee por ronda, como en el perfil, porque la misma persona
    puede ser companero en una partida y rival en otra.
    """
    mine = base_queryset(**filters)
    cruces = (
        RoundPlayer.objects.filter(Exists(mine.filter(round_id=OuterRef("round_id"))))
        .exclude(player_id__in=me_ids)
        .annotate(mi_equipo=_MI_EQUIPO)
        .exclude(mi_equipo=None)
        .exclude(team_index=F("mi_equipo"))
        .values_list("player_id", "round__match_id", "round_id")
        .distinct()
    )
    por_ronda: dict[tuple[int, int], set[int]] = {}
    for pid, match_id, round_id in cruces:
        por_ronda.setdefault((match_id, round_id), set()).add(pid)
    return por_ronda


# Un equipo tiene 5 por ronda; mas que esto es un dato raro y los subconjuntos
# crecen como 2^n, asi que esa ronda no arma grupos.
_MAX_RIVALES_POR_RONDA = 10


def _record(ids: set[int], resultado: dict[int, bool | None]) -> dict:
    wins = sum(1 for mid in ids if resultado.get(mid) is True)
    losses = sum(1 for mid in ids if resultado.get(mid) is False)
    return {
        "matches": len(ids),
        "wins": wins,
        "losses": losses,
        # las partidas sin resultado no ensucian el winrate
        "winrate": _pct(wins, wins + losses),
    }


def repeated_rivals(min_matches: int = 2, **filters) -> list[dict]:
    """Record de partidas contra cada persona que te toco de rival varias veces.

    Se agrupa por profileID para que un cambio de nick no parta la fila.
    """
    me_ids = _me_ids()
    if not me_ids:
        return []
    partidas: dict[int, set[int]] = {}
    for (match_id, _), rivales in _rivales_por_ronda(me_ids, **filters).items():
        for pid in rivales:
            partidas.setdefault(pid, set()).add(match_id)
    partidas = {pid: ids for pid, ids in partidas.items() if len(ids) >= min_matches}
    if not partidas:
        return []

    match_ids = set().union(*partidas.values())
    resultado = dict(Match.objects.filter(id__in=match_ids).values_list("id", "won"))
    nicks = dict(Player.objects.filter(id__in=partidas).values_list("id", "username"))

    salida = [
        {"player_id": pid, "username": nicks.get(pid, ""), **_record(ids, resultado)}
        for pid, ids in partidas.items()
    ]
    return sorted(salida, key=lambda r: (-r["matches"], -r["losses"], r["username"]))


def rival_stacks(min_matches: int = 2, **filters) -> list[dict]:
    """Grupos de 2 o mas rivales que te tocaron juntos en varias partidas.

    Los grupos se arman por ronda: un rival que se fue y el que entro en su
    lugar no estuvieron juntos. Una partida suma a un grupo si estuvo entero
    en al menos una de sus rondas. Por cada conjunto de partidas queda solo el
    grupo mas grande: si A, B y C se repiten juntos, A+B no sale aparte salvo
    que sume alguna partida propia.
    """
    return _filas_de_stacks(_stacks_rivales(min_matches, **filters))


def rival_stacks_de_partida(match_id: int, min_matches: int = 2) -> list[dict]:
    """Los stacks rivales repetidos que jugaron en esta partida.

    Sin filtros: el aviso del detalle habla de todo tu historial contra ese
    grupo, no de lo que la pagina anterior tenia filtrado. La maximalidad de
    Duelos es por conjunto de partidas, y aca no alcanza: si A+B se repite en
    3 partidas y A+B+C en 2, las dos filas existen, pero en una partida donde
    estuvieron los tres decir tambien "A y B" es repetir lo mismo. Se queda el
    grupo mas grande que aplica a esta partida; el record sale de la misma
    funcion que la fila de Duelos, asi los numeros coinciden.
    """
    pares = [(ids, g) for ids, g in _stacks_rivales(min_matches) if match_id in ids]
    pares = [(ids, g) for ids, g in pares if not any(g < otro for _, otro in pares)]
    return _filas_de_stacks(pares)


def _stacks_rivales(min_matches: int, **filters) -> list[tuple[frozenset[int], frozenset[int]]]:
    """Pares (partidas, grupo) de los stacks rivales, ya sin grupos redundantes."""
    me_ids = _me_ids()
    if not me_ids:
        return []
    soporte: dict[frozenset[int], set[int]] = {}
    for (match_id, _), rivales in _rivales_por_ronda(me_ids, **filters).items():
        if len(rivales) > _MAX_RIVALES_POR_RONDA:
            continue
        orden = sorted(rivales)
        for k in range(2, len(orden) + 1):
            for grupo in combinations(orden, k):
                soporte.setdefault(frozenset(grupo), set()).add(match_id)

    por_partidas: dict[frozenset[int], list[frozenset[int]]] = {}
    for grupo, ids in soporte.items():
        if len(ids) >= min_matches:
            por_partidas.setdefault(frozenset(ids), []).append(grupo)
    # un grupo contenido en otro con las mismas partidas no dice nada nuevo
    mejor = [
        (ids, grupo)
        for ids, grupos in por_partidas.items()
        for grupo in grupos
        if not any(grupo < otro for otro in grupos)
    ]
    return mejor


def _filas_de_stacks(mejor: list[tuple[frozenset[int], frozenset[int]]]) -> list[dict]:
    """Nicks y record de cada grupo, en el orden de la tabla de Duelos."""
    if not mejor:
        return []

    match_ids = set().union(*(ids for ids, _ in mejor))
    resultado = dict(Match.objects.filter(id__in=match_ids).values_list("id", "won"))
    nicks = dict(
        Player.objects.filter(id__in=set().union(*(g for _, g in mejor))).values_list(
            "id", "username"
        )
    )

    salida = []
    for ids, grupo in mejor:
        jugadores = sorted(
            ({"player_id": pid, "username": nicks.get(pid, "")} for pid in grupo),
            key=lambda j: (j["username"].lower(), j["player_id"]),
        )
        salida.append({"players": jugadores, "size": len(grupo), **_record(set(ids), resultado)})
    return sorted(
        salida,
        key=lambda r: (
            -r["matches"],
            -r["size"],
            -r["losses"],
            ", ".join(j["username"] for j in r["players"]),
        ),
    )


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


def openings_by_operator(min_openings: int = 3, **filters) -> list[dict]:
    """Que operadores rivales te sacan en el primer duelo de la ronda, por tu lado.

    `duels_by_operator` cuenta todos los duelos; esta solo la apertura, que es
    la que decide a quien le tienes que aprender a jugar la entrada.
    """
    me_ids = _me_ids()
    if not me_ids:
        return []
    contra_mi, a_favor = _duelos(base_queryset(**filters), me_ids)
    contra_mi = contra_mi.filter(id=_PRIMER_EVENTO)
    a_favor = a_favor.filter(id=_PRIMER_EVENTO)

    # el denominador incluye las aperturas de operador vacio o desconocido:
    # sin fila propia, pero te abrieron igual, asi un lado nunca pasa de 100
    perdidas_por_lado = {
        raw["round__my_side"]: raw["n"]
        for raw in contra_mi.values("round__my_side").annotate(n=Count("id"))
    }

    rows: dict[tuple[str, str], dict] = {}

    def sumar(qs, clave: str) -> None:
        for raw in qs.values("op_rival", "round__my_side").annotate(n=Count("id")):
            nombre, lado = raw["op_rival"], raw["round__my_side"]
            if not nombre or not lado or nombre.startswith(unknowns.UNKNOWN_PREFIX):
                continue
            fila = rows.setdefault(
                (nombre, lado),
                {"operator": nombre, "side": lado, "opened_you": 0, "you_opened": 0},
            )
            fila[clave] += raw["n"]

    sumar(contra_mi, "opened_you")
    sumar(a_favor, "you_opened")

    salida = []
    for fila in rows.values():
        aperturas = fila["opened_you"] + fila["you_opened"]
        if aperturas < min_openings:
            continue
        fila.update(
            {
                "openings": aperturas,
                "balance": fila["you_opened"] - fila["opened_you"],
                "winrate": _pct(fila["you_opened"], aperturas),
                "share": _pct(fila["opened_you"], perdidas_por_lado.get(fila["side"], 0)),
            }
        )
        salida.append(fila)
    return sorted(
        salida, key=lambda r: (-r["opened_you"], -r["openings"], r["operator"], r["side"])
    )


def rounds_vs_operator(min_rounds: int = 10, **filters) -> dict:
    """Cuanto mueres y cuanto ganas en las rondas con cada operador del otro lado.

    Es la otra mitad de `duels_by_operator`: aquella mira los tiroteos que ya
    pasaron, esta mira la ronda entera. Un operador que te condiciona sin
    matarte (un Mira que te corta la entrada, un Jager que te come la utilidad)
    solo aparece aca. La referencia son las mismas rondas filtradas, para que
    la diferencia contra tu promedio sea sobre la misma base.
    """
    mias = {
        rid: (died, won, equipo)
        for rid, died, won, equipo in base_queryset(**filters).values_list(
            "round_id", "died", "won", "team_index"
        )
    }
    total = len(mias)
    base = {
        "rounds": total,
        "deaths": sum(1 for died, _, _ in mias.values() if died),
        "rounds_won": sum(1 for _, won, _ in mias.values() if won),
    }
    base["death_rate"] = _pct(base["deaths"], total)
    base["winrate"] = _pct(base["rounds_won"], total)
    if not mias:
        return {"base": base, "operators": []}

    # un operador por equipo y ronda, pero un set evita contar dos veces si un
    # modo casual lo repite
    rondas_por_op: dict[str, set[int]] = {}
    rivales = (
        RoundPlayer.objects.filter(round_id__in=list(mias), is_me=False)
        .exclude(operator="")
        .values_list("round_id", "team_index", "operator")
    )
    for rid, equipo, operador in rivales:
        if equipo == mias[rid][2]:
            continue
        rondas_por_op.setdefault(operador, set()).add(rid)

    salida = []
    for operador, rids in rondas_por_op.items():
        rondas = len(rids)
        if rondas < min_rounds:
            continue
        muertes = sum(1 for rid in rids if mias[rid][0])
        ganadas = sum(1 for rid in rids if mias[rid][1])
        death_rate = _pct(muertes, rondas)
        winrate = _pct(ganadas, rondas)
        salida.append(
            {
                "operator": operador,
                "rounds": rondas,
                "deaths": muertes,
                "death_rate": death_rate,
                "death_rate_delta": _delta(death_rate, base["death_rate"]),
                "rounds_won": ganadas,
                "winrate": winrate,
                "winrate_delta": _delta(winrate, base["winrate"]),
            }
        )
    return {
        "base": base,
        "operators": sorted(salida, key=lambda r: (-r["rounds"], r["operator"])),
    }


def _delta(valor: float | None, referencia: float | None) -> float | None:
    if valor is None or referencia is None:
        return None
    return round(valor - referencia, 1)


# --------------------------------------------------------------------- progreso

#: Metricas que se comparan entre periodos, con hacia donde es mejor.
#: `neutral` significa que subir no es ni bueno ni malo: morir mas tarde puede
#: ser que sobrevivas mas o que llegues tarde a todo (ver item #9).
#: (clave, etiqueta, sufijo, direccion, campo con el tamano de muestra).
#: El ultimo campo solo lo tienen las proporciones: con el se calcula la banda
#: de ruido. En las demas no se puede con esta informacion y queda en None.
COMPARE_METRICS = (
    ("winrate", "Rondas ganadas", "%", "up", "rounds"),
    ("rating", "Rating", "", "up", None),
    ("kd", "K/D", "", "up", None),
    ("kpr", "KPR", "", "up", None),
    ("opening_winrate", "Duelos de apertura", "%", "up", "opening_duels"),
    ("kst_pct", "KST", "%", "up", "rounds"),
    ("hs_pct", "Headshots", "%", "up", "kills"),
    ("survival_pct", "Sobrevives", "%", "up", "rounds"),
    ("untraded_death_pct", "Muertes sin trade", "%", "down", "deaths"),
    ("avg_death_elapsed", "Mueres a los", "s", "neutral", None),
)

#: Rondas minimas por lado para que la comparacion diga algo.
COMPARE_MIN_ROUNDS = 20

#: Rondas minimas por fila y por periodo en los cortes por mapa y operador.
#: Mas baja que la del total porque con 10 partidas por periodo un operador
#: rara vez junta 20 rondas de un mismo lado y la tabla quedaria siempre vacia;
#: la banda de ruido de cada fila ya avisa cuando 10 rondas no alcanzan.
COMPARE_MIN_ROUNDS_FILA = 10

#: Las fechas y la sesion las define la propia comparacion.
_FILTROS_DE_TIEMPO = ("since", "until", "session")


def _sin_filtros_de_tiempo(filters: dict) -> dict:
    return {k: v for k, v in filters.items() if k not in _FILTROS_DE_TIEMPO}


def _ruido(p_actual, n_actual, p_previo, n_previo) -> float | None:
    """Error estandar de la diferencia entre dos proporciones, en puntos.

    Es el tamano tipico de una diferencia que **no significa nada**. Sin este
    numero, un salto de 9 puntos de winrate con 50 rondas por lado se lee como
    progreso cuando esta dentro de lo que se mueve solo.
    """
    if p_actual is None or p_previo is None or not n_actual or not n_previo:
        return None
    varianza = 0.0
    for p, n in ((p_actual / 100, n_actual), (p_previo / 100, n_previo)):
        varianza += p * (1 - p) / n
    return round(math.sqrt(varianza) * 100, 1)


def _veredicto(delta, ruido, direccion) -> str | None:
    if delta is None or direccion == "neutral" or delta == 0:
        return None
    if ruido is not None and abs(delta) <= ruido:
        # se movio menos de lo que se mueve solo: no es un cambio
        return "ruido"
    mejoro = delta > 0 if direccion == "up" else delta < 0
    return "mejor" if mejoro else "peor"


def _corte_por_periodo(actual, previo, baseline, campos, labels, min_rows) -> list[dict]:
    """Winrate y rating de cada grupo en los dos periodos, con su veredicto.

    Solo entran los grupos con muestra en los dos periodos: un mapa que no
    jugaste antes no tiene contra que compararse.
    """
    def indexar(qs):
        return {
            tuple(fila[label] for label in labels): fila
            for fila in group_by(qs, *campos, labels=labels, min_rounds=min_rows, baseline=baseline)
        }

    ahora, antes = indexar(actual), indexar(previo)
    filas = []
    for clave in ahora.keys() & antes.keys():
        cur, prev = ahora[clave], antes[clave]
        delta = (
            None
            if cur["winrate"] is None or prev["winrate"] is None
            else round(cur["winrate"] - prev["winrate"], 1)
        )
        ruido = _ruido(cur["winrate"], cur["rounds"], prev["winrate"], prev["rounds"])
        rating_delta = (
            None
            if cur["rating"] is None or prev["rating"] is None
            else round(cur["rating"] - prev["rating"], 2)
        )
        filas.append(
            {
                **dict(zip(labels, clave, strict=True)),
                "current_rounds": cur["rounds"],
                "previous_rounds": prev["rounds"],
                "current_winrate": cur["winrate"],
                "previous_winrate": prev["winrate"],
                "delta": delta,
                "noise": ruido,
                "verdict": _veredicto(delta, ruido, "up"),
                "current_rating": cur["rating"],
                "previous_rating": prev["rating"],
                "rating_delta": rating_delta,
                "suffix": "%",
                "direction": "up",
            }
        )
    # la clave desempata para que el orden sea estable entre corridas
    filas.sort(key=lambda f: tuple(str(f[label]) for label in labels))
    filas.sort(key=lambda f: (f["delta"] is None, -(f["delta"] or 0)))
    return filas


def _periodo_por_partidas(
    filters: dict, n: int, resto: bool = False
) -> tuple[list[int], list[int]]:
    """Ultimas n partidas y las n anteriores, o todas las anteriores con `resto`."""
    ids = list(
        base_queryset(**filters)
        .values_list("round__match_id", flat=True)
        .order_by("-round__match__played_at")
        .distinct()
    )
    # distinct() sobre un values_list ordenado por otra columna no garantiza
    # unicidad en SQLite, asi que se deduplica aca conservando el orden
    vistos, ordenados = set(), []
    for match_id in ids:
        if match_id not in vistos:
            vistos.add(match_id)
            ordenados.append(match_id)
    return ordenados[:n], (ordenados[n:] if resto else ordenados[n : n * 2])


def _resumen(qs, baseline, etiqueta: str) -> dict:
    fila = totals(qs, baseline)
    fila["label"] = etiqueta
    rango = qs.aggregate(desde=Min("round__match__played_at"), hasta=Max("round__match__played_at"))
    fila["from"] = rango["desde"].isoformat() if rango["desde"] else None
    fila["to"] = rango["hasta"].isoformat() if rango["hasta"] else None
    return fila


def _etiquetar_corte(filas: list[dict]) -> list[dict]:
    """Pone en cada fila por version la etiqueta de Mapas.

    Se agrupa por `(slug, map_id)` sin el nombre para que un renombre dentro de
    la misma version no parta la fila entre los dos periodos.
    """
    etiquetas = etiquetas_de_mapas({f["slug"] for f in filas})
    for f in filas:
        f["map"] = etiquetas.get((f["slug"], f["map_id"]), f["slug"])
    return filas


def compare_periods(
    by: str = "matches",
    n: int = 10,
    min_rounds: int = COMPARE_MIN_ROUNDS,
    min_rows: int = COMPARE_MIN_ROUNDS_FILA,
    against: str = "previous",
    **filters,
) -> dict:
    """Compara el periodo reciente contra el inmediatamente anterior.

    Dos modos porque sirven para cosas distintas: `matches` (ultimas n partidas
    contra las n anteriores) siempre tiene muestra de los dos lados si jugaste
    2n partidas, y `days` responde "como vengo este mes" cuando se juega
    seguido. Los filtros de fecha que vengan en la request se ignoran: el
    periodo lo define esta funcion.

    Con `against="rest"` la referencia es todo el historial anterior y no un
    periodo del mismo largo: el Inicio pregunta si tu forma se sale de lo
    tuyo de siempre, no de lo del mes pasado.
    """
    resto = against == "rest"
    against = "rest" if resto else "previous"
    filters = _sin_filtros_de_tiempo(filters)
    baseline = rating_baseline()

    if by == "days":
        corte = datetime.now()
        inicio_actual = corte - timedelta(days=n)
        inicio_previo = corte - timedelta(days=n * 2)
        actual = base_queryset(since=inicio_actual, **filters)
        if resto:
            previo = base_queryset(until=inicio_actual, **filters)
            etiquetas = (f"Últimos {n} días", f"Antes de los últimos {n} días")
        else:
            previo = base_queryset(since=inicio_previo, until=inicio_actual, **filters)
            etiquetas = (f"Últimos {n} días", f"Los {n} días anteriores")
    else:
        recientes, anteriores = _periodo_por_partidas(filters, n, resto=resto)
        actual = base_queryset(**filters).filter(round__match_id__in=recientes)
        if resto:
            # exclude y no IN: el resto puede pasar el limite de variables de SQLite
            previo = base_queryset(**filters).exclude(round__match_id__in=recientes)
        else:
            previo = base_queryset(**filters).filter(round__match_id__in=anteriores)
        if resto:
            previa = f"El resto ({len(anteriores)} partidas)"
        else:
            previa = f"Las {len(anteriores)} anteriores"
        etiquetas = (f"Últimas {len(recientes)} partidas", previa)

    fila_actual = _resumen(actual, baseline, etiquetas[0])
    fila_previa = _resumen(previo, baseline, etiquetas[1])
    suficiente = min(fila_actual["rounds"], fila_previa["rounds"]) >= min_rounds

    metricas = []
    for clave, label, sufijo, direccion, campo_muestra in COMPARE_METRICS:
        ahora, antes = fila_actual.get(clave), fila_previa.get(clave)
        delta = None if (ahora is None or antes is None) else round(ahora - antes, 2)
        ruido = (
            _ruido(ahora, fila_actual.get(campo_muestra), antes, fila_previa.get(campo_muestra))
            if campo_muestra
            else None
        )
        metricas.append(
            {
                "key": clave,
                "label": label,
                "suffix": sufijo,
                "direction": direccion,
                "current": ahora,
                "previous": antes,
                "delta": delta,
                "noise": ruido,
                "verdict": _veredicto(delta, ruido, direccion),
            }
        )

    return {
        "by": by,
        "n": n,
        "against": against,
        "min_rounds": min_rounds,
        "enough_sample": suficiente,
        "current": fila_actual,
        "previous": fila_previa,
        "metrics": metricas,
        "min_rows": min_rows,
        "by_map": _etiquetar_corte(
            _corte_por_periodo(
                actual,
                previo,
                baseline,
                ("round__match__map_slug", "round__match__map_id"),
                ("slug", "map_id"),
                min_rows,
            )
        ),
        "by_operator": _corte_por_periodo(
            actual.exclude(operator=""),
            previo.exclude(operator=""),
            baseline,
            ("operator", "side"),
            ("operator", "side"),
            min_rows,
        ),
    }


# --------------------------------------------------------------------- muertes

#: Ancho de los tramos del histograma y desde donde se juntan en el ultimo.
DEATH_BUCKET = 30
DEATH_CAP = 150


def _tramo_vacio(inicio: int, bucket: int, cap: int) -> dict:
    """Limites y etiqueta de un tramo del histograma; el ultimo queda abierto."""
    return {
        "start": inicio,
        "end": None if inicio >= cap else inicio + bucket,
        "label": f"{inicio}s+" if inicio >= cap else f"{inicio}-{inicio + bucket}s",
    }


def deaths_by_time(bucket: int = DEATH_BUCKET, cap: int = DEATH_CAP, **filters) -> list[dict]:
    """En que momento de la ronda mueres, en tramos de `bucket` segundos.

    El promedio esconde la forma: morir siempre a los 100s no es lo mismo que
    morir la mitad de las veces a los 20 y la otra mitad a los 170, y las dos
    cosas se arreglan distinto.
    """
    qs = base_queryset(**filters).exclude(death_elapsed=None)
    crudas = (
        qs.annotate(
            tramo=ExpressionWrapper(
                Floor(F("death_elapsed") / bucket) * bucket, output_field=IntegerField()
            )
        )
        .values("tramo", "side")
        .annotate(deaths=Count("id"), untraded=Count("id", filter=Q(untraded_death=True)))
        .order_by("tramo")
    )

    tramos: dict[int, dict] = {}
    for cruda in crudas:
        # todo lo que pasa del tope se junta en el ultimo tramo: son pocas
        # muertes y separadas no dicen nada
        inicio = min(int(cruda["tramo"] or 0), cap)
        fila = tramos.setdefault(
            inicio,
            {
                **_tramo_vacio(inicio, bucket, cap),
                "deaths": 0,
                "untraded": 0,
                "attack": 0,
                "defense": 0,
            },
        )
        fila["deaths"] += cruda["deaths"]
        fila["untraded"] += cruda["untraded"]
        if cruda["side"] == "Attack":
            fila["attack"] += cruda["deaths"]
        elif cruda["side"] == "Defense":
            fila["defense"] += cruda["deaths"]

    total = sum(f["deaths"] for f in tramos.values())
    salida = []
    for inicio in sorted(tramos):
        fila = tramos[inicio]
        fila["pct"] = _pct(fila["deaths"], total)
        fila["untraded_pct"] = _pct(fila["untraded"], fila["deaths"])
        salida.append(fila)
    return salida


def kills_by_time(bucket: int = DEATH_BUCKET, cap: int = DEATH_CAP, **filters) -> list[dict]:
    """En que momento de la ronda sacas tus bajas a rivales, el espejo de
    `deaths_by_time`.

    El promedio de cuando matas esconde si tu impacto esta en la apertura o en
    el cierre. Sale del feed como Duelos: `RoundPlayer` no guarda el segundo de
    cada baja, y los teamkills quedan afuera por `_duelos`.
    """
    me_ids = _me_ids()
    if not me_ids:
        return []
    _, a_favor = _duelos(base_queryset(**filters), me_ids)
    crudas = (
        a_favor.annotate(
            mi_lado=Subquery(
                RoundPlayer.objects.filter(round_id=OuterRef("round_id"), is_me=True).values(
                    "side"
                )[:1]
            ),
            tramo=ExpressionWrapper(
                Floor(F("elapsed") / bucket) * bucket, output_field=IntegerField()
            ),
        )
        .values("tramo", "mi_lado")
        .annotate(kills=Count("id"))
        .order_by("tramo")
    )

    tramos: dict[int, dict] = {}
    for cruda in crudas:
        inicio = min(int(cruda["tramo"] or 0), cap)
        fila = tramos.setdefault(
            inicio, {**_tramo_vacio(inicio, bucket, cap), "kills": 0, "attack": 0, "defense": 0}
        )
        fila["kills"] += cruda["kills"]
        if cruda["mi_lado"] == "Attack":
            fila["attack"] += cruda["kills"]
        elif cruda["mi_lado"] == "Defense":
            fila["defense"] += cruda["kills"]

    total = sum(f["kills"] for f in tramos.values())
    salida = []
    for inicio in sorted(tramos):
        fila = tramos[inicio]
        fila["pct"] = _pct(fila["kills"], total)
        salida.append(fila)
    return salida


#: Segundos de reloj que quedan para considerar que la ronda ya estaba decidida.
#: Es un sexto de los 180s: morir ahi en ataque significa que la ejecucion nunca
#: llego a pasar.
CLOCK_TAIL = 30


def death_timing(**filters) -> dict:
    """Los dos extremos de la distribucion, que son los que se pueden accionar.

    `first30` mira los segundos **jugados** (saliste muy temprano) y `last30`
    los segundos **que quedaban en el reloj** (la ronda ya estaba decidida). Son
    ejes distintos a proposito: el mismo promedio puede esconder los dos.
    """
    qs = base_queryset(**filters).exclude(death_elapsed=None)
    salida = {}
    for lado, clave in (("Attack", "attack"), ("Defense", "defense")):
        fila = qs.filter(side=lado).aggregate(
            deaths=Count("id"),
            first30=Count("id", filter=Q(death_elapsed__lt=DEATH_BUCKET)),
            last30=Count("id", filter=Q(death_clock__lt=CLOCK_TAIL, death_clock__isnull=False)),
        )
        fila["first30_pct"] = _pct(fila["first30"], fila["deaths"])
        fila["last30_pct"] = _pct(fila["last30"], fila["deaths"])
        salida[clave] = fila
    return salida


#: Cortes de cuando llega la primera baja de la ronda. 30 es el mismo tramo de
#: "sales muy temprano" de `death_timing`; 90 es la mitad de los 180 s de accion.
APERTURA_TEMPRANA = 30
APERTURA_TARDIA = 90

_TRAMOS_APERTURA = (
    ("temprano", "Temprano (<30 s)"),
    ("medio", "Medio (30–90 s)"),
    ("tarde", "Tarde (90 s o más)"),
    ("sin_bajas", "Sin bajas"),
)


def _tramo_apertura(elapsed: float | None) -> str:
    if elapsed is None:
        return "sin_bajas"
    if elapsed < APERTURA_TEMPRANA:
        return "temprano"
    if elapsed < APERTURA_TARDIA:
        return "medio"
    return "tarde"


def opening_timing(**filters) -> dict:
    """En que segundo llega la primera baja de la ronda y como te va segun eso.

    Las aperturas de hoy dicen quien gana el primer duelo; esto dice cuando
    llega. La primera baja es la de menor `order`, la misma que marca
    `opening_kill` en `metrics.py`, y "tuya" es de cualquiera de tu equipo para
    que cuadre con Duelos de apertura.
    """
    filas = (
        base_queryset(**filters)
        .filter(round__my_team_won__isnull=False)
        .annotate(
            t_apertura=Subquery(
                Event.objects.filter(
                    kind__in=(Event.KILL, Event.DEATH), round_id=OuterRef("round_id")
                )
                .order_by("order")
                .values("elapsed")[:1]
            ),
            apertura_mia=Exists(
                RoundPlayer.objects.filter(
                    round_id=OuterRef("round_id"),
                    team_index=OuterRef("team_index"),
                    opening_kill=True,
                )
            ),
        )
        .values("side", "t_apertura", "apertura_mia", "round__my_team_won")
    )

    cuentas = {
        lado: {clave: Counter() for clave, _ in _TRAMOS_APERTURA}
        for lado in ("Attack", "Defense")
    }
    for fila in filas:
        if fila["side"] not in cuentas:
            continue
        tramo = _tramo_apertura(fila["t_apertura"])
        cuenta = cuentas[fila["side"]][tramo]
        cuenta["rounds"] += 1
        cuenta["won"] += bool(fila["round__my_team_won"])
        # sin bajas no hay primera baja que ganar, aunque alguien quede marcado
        if tramo != "sin_bajas":
            cuenta["opening_won"] += bool(fila["apertura_mia"])

    salida = {}
    for lado, clave_lado in (("Attack", "attack"), ("Defense", "defense")):
        salida[clave_lado] = [
            {
                "key": clave,
                "label": etiqueta,
                "rounds": cuentas[lado][clave]["rounds"],
                "won": cuentas[lado][clave]["won"],
                "winrate": _pct(cuentas[lado][clave]["won"], cuentas[lado][clave]["rounds"]),
                "opening_won": cuentas[lado][clave]["opening_won"],
                # sin bajas no hay primera baja: un 0 % ahi se leeria como aperturas perdidas
                "opening_won_pct": None
                if clave == "sin_bajas"
                else _pct(cuentas[lado][clave]["opening_won"], cuentas[lado][clave]["rounds"]),
            }
            for clave, etiqueta in _TRAMOS_APERTURA
        ]
    return salida


#: Cortes de las fases de la ronda, en segundos jugados de la fase de accion.
#: 30 es el mismo corte de "sales muy temprano" y de la apertura temprana; 120
#: deja el ultimo minuto de los 180 s como cierre. No se usa el 90 de
#: `APERTURA_TARDIA`: ese habla de cuando llega la primera baja, no de en que
#: momento de la ronda se pelea.
FASE_MEDIA = APERTURA_TEMPRANA
FASE_TARDIA = 120

FASES = (
    ("temprano", "Temprano (<30 s)", 0, FASE_MEDIA),
    ("medio", "Medio (30–120 s)", FASE_MEDIA, FASE_TARDIA),
    ("tarde", "Tarde (120 s o más)", FASE_TARDIA, None),
)


def _fase_de(elapsed: float) -> str:
    if elapsed < FASE_MEDIA:
        return "temprano"
    if elapsed < FASE_TARDIA:
        return "medio"
    return "tarde"


def fases_de_partida(rondas: list[dict], my_team_index: int) -> dict:
    """Bajas de cada equipo en temprano, medio y tarde, y rondas dominadas por fase.

    Recibe las rondas ya armadas de `match_detail` (cero queries). "Tu equipo"
    se lee por ronda desde tu fila, como en Trades por equipo. El feed nombra
    por nick: si un nick se repitiera en los dos equipos de una ronda (no
    deberia pasar), el dict se queda con la ultima fila.
    """
    claves = [clave for clave, *_ in FASES]
    bajas = {clave: Counter() for clave in claves}
    rondas_por_fase = {clave: Counter() for clave in claves}
    untimed = unknown = teamkills = 0

    for ronda in rondas:
        jugadores = ronda["players"]
        yo = next((p for p in jugadores if p["is_me"]), None)
        mio = yo["team_index"] if yo else my_team_index
        equipo = {p["username"]: p["team_index"] for p in jugadores}
        en_ronda = {clave: Counter() for clave in claves}
        for evento in ronda["events"]:
            # Un Death sin autor no es baja de ningun equipo.
            if evento["kind"] != "Kill":
                continue
            # elapsed 0 es "sin reloj" (el feed no trajo el segundo), no el segundo 0.
            if not evento["elapsed"]:
                untimed += 1
                continue
            autor = equipo.get(evento["actor"])
            victima = equipo.get(evento["target"])
            if autor is None:
                unknown += 1
                continue
            if victima is not None and autor == victima:
                teamkills += 1
                continue
            lado = "mine" if autor == mio else "rival"
            fase = _fase_de(evento["elapsed"])
            bajas[fase][lado] += 1
            en_ronda[fase][lado] += 1

        gano = ronda["my_team_won"]
        if gano is None:
            continue
        for fase, cuenta in en_ronda.items():
            if cuenta["mine"] > cuenta["rival"]:
                rondas_por_fase[fase]["ahead"] += 1
                rondas_por_fase[fase]["ahead_won"] += bool(gano)
            elif cuenta["rival"] > cuenta["mine"]:
                rondas_por_fase[fase]["behind"] += 1
                rondas_por_fase[fase]["behind_won"] += bool(gano)

    filas = []
    for clave, etiqueta, inicio, fin in FASES:
        r = rondas_por_fase[clave]
        filas.append(
            {
                "key": clave,
                "label": etiqueta,
                "start": inicio,
                "end": fin,
                "mine": bajas[clave]["mine"],
                "rival": bajas[clave]["rival"],
                "rounds_ahead": r["ahead"],
                "rounds_ahead_won": r["ahead_won"],
                "rounds_ahead_winrate": _pct(r["ahead_won"], r["ahead"]),
                "rounds_behind": r["behind"],
                "rounds_behind_won": r["behind_won"],
                "rounds_behind_winrate": _pct(r["behind_won"], r["behind"]),
            }
        )
    return {
        "rows": filas,
        "untimed_kills": untimed,
        "unknown_team_kills": unknown,
        "teamkills": teamkills,
    }


# --------------------------------------------------------------------- jugador


def _sin_rating(fila: dict) -> dict:
    """Le saca el rating a las filas de otra persona.

    El 1.00 es el promedio del jugador principal; aplicado a otro no significa
    nada, asi que es mejor no mostrarlo que mostrarlo mal.
    """
    fila["rating"] = None
    fila["rating_points"] = None
    return fila


def player_profile(player_id: int, **filters) -> dict | None:
    """Todo lo que sabemos de una persona dentro de tus partidas."""
    player = Player.objects.filter(pk=player_id).first()
    if not player:
        return None

    mine = base_queryset(**filters)
    baseline = rating_baseline()

    en_mi_ronda = RoundPlayer.objects.filter(player_id=player_id, round_id=OuterRef("round_id"))
    de_companero = en_mi_ronda.filter(team_index=OuterRef("team_index"))

    con = mine.filter(Exists(de_companero))
    sin = mine.exclude(Exists(de_companero))
    contra = mine.filter(Exists(en_mi_ronda)).exclude(Exists(de_companero))

    # sus propias filas, limitadas a las rondas que yo jugue
    suyas = RoundPlayer.objects.filter(player_id=player_id).filter(
        Exists(mine.filter(round_id=OuterRef("round_id")))
    )

    duelos = next(
        (d for d in nemesis(min_duels=1, **filters) if d["player_id"] == player_id), None
    )

    return {
        "player": {
            "id": player.id,
            "username": player.username,
            "aliases": player.aliases,
            "is_me": player.is_me,
            "first_seen": player.first_seen.isoformat() if player.first_seen else None,
            "last_seen": player.last_seen.isoformat() if player.last_seen else None,
        },
        "rounds_together": con.count(),
        "rounds_against": contra.count(),
        "with": totals(con, baseline),
        "without": totals(sin, baseline),
        "against": totals(contra, baseline),
        "theirs": _sin_rating(totals(suyas, baseline)),
        "their_operators": [
            _sin_rating(fila)
            for fila in group_by(
                suyas.exclude(operator=""),
                "operator",
                "side",
                labels=("operator", "side"),
                min_rounds=1,
                baseline=baseline,
            )
        ],
        "duels": duelos,
        "matches": _partidas_compartidas(suyas),
    }


def _partidas_compartidas(suyas: QuerySet[RoundPlayer]) -> list[dict]:
    """Partidas donde se cruzaron, y de que lado estuvo en cada una."""
    partidas: dict[int, dict] = {}
    for row in suyas.annotate(mi_equipo=_MI_EQUIPO).values(
        "round__match_id",
        "round__match__map_name",
        "round__match__played_at",
        "round__match__my_score",
        "round__match__opponent_score",
        "round__match__won",
        "team_index",
        "mi_equipo",
    ):
        match_id = row["round__match_id"]
        fila = partidas.get(match_id)
        if fila is None:
            my_score = row["round__match__my_score"]
            opp_score = row["round__match__opponent_score"]
            fila = partidas[match_id] = {
                "id": match_id,
                "map": row["round__match__map_name"],
                "played_at": row["round__match__played_at"].isoformat(),
                "score": f"{my_score}-{opp_score}",
                "won": row["round__match__won"],
                "result": match_result(row["round__match__won"], my_score, opp_score),
                "rounds": 0,
                "as_teammate": 0,
                "as_rival": 0,
            }
        fila["rounds"] += 1
        if row["team_index"] == row["mi_equipo"]:
            fila["as_teammate"] += 1
        else:
            fila["as_rival"] += 1

    for fila in partidas.values():
        # los equipos se dan vuelta entre mitades, pero el equipo no cambia:
        # si aparece de los dos lados es que entro por un abandono
        fila["role"] = (
            "companero"
            if fila["as_rival"] == 0
            else "rival"
            if fila["as_teammate"] == 0
            else "ambos"
        )
    return sorted(partidas.values(), key=lambda f: f["played_at"], reverse=True)


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
        "trade_window": trade_window(),
        "assists_available": qs.filter(assists__gt=0).exists(),
        "score_available": qs.filter(score__gt=0).exists(),
    }
