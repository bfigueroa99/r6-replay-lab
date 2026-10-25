"""Re-etiquetado de lo ya importado, sin volver a leer los replays.

Cuando Ubisoft revampea un mapa o agrega un operador, el parser guarda el ID
crudo y muestra `Unknown(<id>)`. Al completar `data/overrides.json` no hace
falta reparsear nada: los IDs (`Match.map_id`, `RoundPlayer.operator_id`) estan
guardados, asi que basta con volver a resolver el nombre. Reimportar la misma
partida significa descomprimir 5-9 MB por ronda para cambiar un string.

Sirve igual cuando la que cambia es la tabla de constantes del parser.

Modo y tipo de partida son la excepcion: `Match` guarda solo el texto, asi que
el ID se lee del propio `Unknown(<id>)`. Una vez etiquetada, la partida ya no
tiene el ID, y cambiar despues esa etiqueta no la reetiqueta.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from pydissect import overrides
from pydissect.header import gamemode_name, map_name, map_slug, match_type_name, operator_name

from .models import Match, RoundPlayer
from .unknowns import id_de_unknown

UNKNOWN_PREFIX = "Unknown("


@dataclass
class Change:
    """Una etiqueta que cambia, con cuantas filas afecta."""

    kind: str  # "mapa" | "operador" | "modo" | "tipo de partida"
    old: str
    new: str
    rows: int


@dataclass
class RetagResult:
    changes: list[Change] = field(default_factory=list)
    matches: int = 0
    round_players: int = 0
    # mapa, modo y tipo pueden cambiar en la misma partida: se cuenta una vez
    partidas: set[int] = field(default_factory=set, repr=False)

    @property
    def changed(self) -> bool:
        return bool(self.matches or self.round_players)


def _is_unknown(name: str) -> bool:
    return name.startswith(UNKNOWN_PREFIX)


def retag(*, dry_run: bool = False, reload: bool = True) -> RetagResult:
    """Vuelve a resolver nombres de mapa y operador de lo ya importado.

    Nunca degrada una etiqueta buena a `Unknown(...)`: si el override que le
    daba nombre a un ID desaparece, lo importado conserva el nombre que tenia.
    """
    if reload:
        overrides.load(force=True)

    result = RetagResult()
    _retag_maps(result, dry_run)
    _retag_operators(result, dry_run)
    _retag_texto(result, dry_run, "gamemode", gamemode_name, "modo")
    _retag_texto(result, dry_run, "match_type", match_type_name, "tipo de partida")
    result.matches = len(result.partidas)
    return result


def _retag_maps(result: RetagResult, dry_run: bool) -> None:
    map_ids = set(Match.objects.exclude(map_id=0).values_list("map_id", flat=True))
    for map_id in sorted(map_ids):
        name = map_name(map_id)
        if _is_unknown(name):
            continue
        slug = map_slug(map_id)
        qs = Match.objects.filter(map_id=map_id).exclude(map_name=name, map_slug=slug)
        old_names = sorted(set(qs.values_list("map_name", flat=True)))
        if not old_names:
            continue
        result.partidas.update(qs.values_list("id", flat=True))
        rows = qs.count() if dry_run else qs.update(map_name=name, map_slug=slug)
        for old in old_names:
            result.changes.append(Change("mapa", old, name, rows))


def _retag_operators(result: RetagResult, dry_run: bool) -> None:
    op_ids = set(RoundPlayer.objects.exclude(operator_id=0).values_list("operator_id", flat=True))
    for op_id in sorted(op_ids):
        name = operator_name(op_id)
        if _is_unknown(name):
            continue
        qs = RoundPlayer.objects.filter(operator_id=op_id).exclude(operator=name)
        old_names = sorted(set(qs.values_list("operator", flat=True)))
        if not old_names:
            continue
        rows = qs.count() if dry_run else qs.update(operator=name)
        result.round_players += rows
        for old in old_names:
            result.changes.append(Change("operador", old or "(vacio)", name, rows))


def _retag_texto(result: RetagResult, dry_run: bool, campo: str, nombrar, kind: str) -> None:
    viejos = Match.objects.filter(**{f"{campo}__startswith": UNKNOWN_PREFIX})
    for old in sorted(set(viejos.values_list(campo, flat=True))):
        ident = id_de_unknown(old)
        if ident is None:
            continue
        name = nombrar(ident)
        if _is_unknown(name):
            continue
        qs = Match.objects.filter(**{campo: old})
        result.partidas.update(qs.values_list("id", flat=True))
        rows = qs.count() if dry_run else qs.update(**{campo: name})
        result.changes.append(Change(kind, old, name, rows))
