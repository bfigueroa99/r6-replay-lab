"""IDs que el parser no supo nombrar, y el archivo de etiquetas.

Los IDs salen de lo **ya importado**, no de los `.rec`: cuando el parser no
reconoce un mapa guarda `map_name = "Unknown(<id>)"` y deja el ID crudo en
`map_id`. Con eso basta para listarlos, etiquetarlos y reetiquetar (`retag.py`)
sin volver a tocar un replay. Modos y tipos de partida no tienen columna de ID:
el ID se lee del propio texto `Unknown(<id>)`.

Lo consumen `manage.py unknown_ids` y la pagina Datos.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

from django.conf import settings
from django.db.models import Count, Max, Min

from pydissect import overrides

from .models import Match, Round, RoundPlayer

UNKNOWN_PREFIX = "Unknown("

CLAVES = overrides.CLAVES

#: El mas corto de los dos campos que reciben la etiqueta: `RoundPlayer.operator`
#: es de 32 y `Match.map_name` de 64, asi que 32 sirve para ambos.
MAX_LABEL = 32


def _iso(value):
    return value.isoformat() if value else None


# --------------------------------------------------------------- descubrimiento


def unknown_maps() -> list[dict]:
    """Mapas sin nombre, con lo que sirve para identificarlos.

    Los sitios de bomba son la pista util: el juego los nombra igual aunque
    cambie el ID del mapa, asi que "2F Cigar Room, 2F Pool" delata cual es.
    """
    base = Match.objects.filter(map_name__startswith=UNKNOWN_PREFIX).exclude(map_id=0)
    rows = []
    for map_id in sorted(set(base.values_list("map_id", flat=True))):
        matches = base.filter(map_id=map_id)
        resumen = matches.aggregate(
            partidas=Count("id"), primera=Min("played_at"), ultima=Max("played_at")
        )
        # set y no .distinct(): Round tiene ordering en el Meta, y Django mete
        # esos campos en el SELECT, con lo que el DISTINCT deja de agrupar.
        sites = sorted(
            {s for s in Round.objects.filter(match__in=matches).values_list("site", flat=True) if s}
        )
        rows.append(
            {
                "id": str(map_id),
                "label": f"{UNKNOWN_PREFIX}{map_id})",
                "matches": resumen["partidas"],
                "rounds": Round.objects.filter(match__in=matches).count(),
                "sites": sites,
                "first_seen": _iso(resumen["primera"]),
                "last_seen": _iso(resumen["ultima"]),
                "pending": overrides.extra_map(map_id) or "",
            }
        )
    return rows


def unknown_operators() -> list[dict]:
    """Operadores sin nombre.

    Solo aparecen los que ademas no traen `rolename` en la cabecera del replay:
    cuando lo traen, el parser ya usa ese nombre y no hay nada que etiquetar.
    El lado es la pista principal, porque parte el universo en dos.
    """
    base = RoundPlayer.objects.filter(operator__startswith=UNKNOWN_PREFIX).exclude(operator_id=0)
    rows = []
    for op_id in sorted(set(base.values_list("operator_id", flat=True))):
        jugadas = base.filter(operator_id=op_id)
        sides = sorted({s for s in jugadas.values_list("side", flat=True) if s})
        maps = sorted({m for m in jugadas.values_list("round__match__map_name", flat=True) if m})
        rows.append(
            {
                "id": str(op_id),
                "label": f"{UNKNOWN_PREFIX}{op_id})",
                "rounds": jugadas.count(),
                "sides": sides,
                "maps": maps[:6],
                "mine": jugadas.filter(is_me=True).exists(),
                "first_seen": _iso(
                    jugadas.aggregate(v=Min("round__match__played_at"))["v"]
                ),
                "last_seen": _iso(jugadas.aggregate(v=Max("round__match__played_at"))["v"]),
                "pending": overrides.extra_operator(op_id) or "",
            }
        )
    return rows


def id_de_unknown(texto: str) -> int | None:
    """El ID dentro de `Unknown(<id>)`, o None si no tiene esa forma o es 0."""
    hallado = re.fullmatch(r"Unknown\((\d+)\)", texto or "")
    if not hallado:
        return None
    return int(hallado.group(1)) or None


def _desconocidos_de_partida(campo: str, extra, pista: str) -> list[dict]:
    """Valores `Unknown(<id>)` de un campo de texto de `Match`, agrupados por ID.

    `pista` es el otro campo (modo para el tipo, tipo para el modo): lo que si
    se sabe de esas partidas ayuda a adivinar lo que no.
    """
    por_id: dict[int, list[dict]] = {}
    filas = Match.objects.filter(**{f"{campo}__startswith": UNKNOWN_PREFIX}).values(
        campo, pista, "played_at"
    )
    for fila in filas:
        ident = id_de_unknown(fila[campo])
        if ident is not None:
            por_id.setdefault(ident, []).append(fila)
    rows = []
    for ident in sorted(por_id):
        partidas = por_id[ident]
        fechas = [p["played_at"] for p in partidas if p["played_at"]]
        rows.append(
            {
                "id": str(ident),
                "label": f"{UNKNOWN_PREFIX}{ident})",
                "matches": len(partidas),
                pista + "s": sorted({p[pista] for p in partidas if p[pista]}),
                "first_seen": _iso(min(fechas) if fechas else None),
                "last_seen": _iso(max(fechas) if fechas else None),
                "pending": extra(ident) or "",
            }
        )
    return rows


def unknown_gamemodes() -> list[dict]:
    """Modos de juego sin nombre; la pista son los tipos de partida vistos."""
    return _desconocidos_de_partida("gamemode", overrides.extra_gamemode, "match_type")


def unknown_match_types() -> list[dict]:
    """Tipos de partida sin nombre; la pista son los modos vistos."""
    return _desconocidos_de_partida("match_type", overrides.extra_match_type, "gamemode")


# ------------------------------------------------------------------- etiquetas


def overrides_path() -> Path:
    return Path(settings.OVERRIDES_PATH)


def read_overrides() -> dict:
    """El JSON en disco, siempre con todas las claves y sin reventar si esta roto."""
    path = overrides_path()
    data = {clave: {} for clave in CLAVES}
    if not path.exists():
        return data
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return data
    if not isinstance(raw, dict):
        return data
    for key in CLAVES:
        valores = raw.get(key)
        if isinstance(valores, dict):
            data[key] = {str(k): str(v) for k, v in valores.items()}
    return data


class LabelError(ValueError):
    """Etiqueta que no se puede guardar, con el motivo listo para la UI."""


def clean_labels(raw) -> dict[str, str]:
    """Valida `{id: nombre}` viniendo de la request.

    Un nombre vacio borra la entrada: no revierte lo ya etiquetado (eso lo
    garantiza `retag`), solo deja de aplicarse a lo que se importe despues.
    """
    if raw in (None, ""):
        return {}
    if not isinstance(raw, dict):
        raise LabelError("se esperaba un objeto {id: nombre}")

    limpio: dict[str, str] = {}
    for key, value in raw.items():
        ident = str(key).strip()
        if not ident.isdigit():
            raise LabelError(f"{ident!r} no es un ID valido")
        nombre = "" if value is None else str(value).strip()
        if len(nombre) > MAX_LABEL:
            raise LabelError(f"el nombre para {ident} pasa de {MAX_LABEL} caracteres")
        if nombre.startswith(UNKNOWN_PREFIX):
            raise LabelError(f"{nombre!r} es justamente lo que estamos tratando de sacar")
        limpio[ident] = nombre
    return limpio


def _save(data: dict) -> dict:
    path = overrides_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return data


def write_overrides(
    maps: dict[str, str],
    operators: dict[str, str],
    gamemodes: dict[str, str] | None = None,
    match_types: dict[str, str] | None = None,
) -> dict:
    """Mezcla las etiquetas nuevas con el archivo y lo deja escrito."""
    data = read_overrides()
    pares = (
        ("maps", maps),
        ("operators", operators),
        ("gamemodes", gamemodes or {}),
        ("match_types", match_types or {}),
    )
    for key, nuevos in pares:
        for ident, nombre in nuevos.items():
            if nombre:
                data[key][ident] = nombre
            else:
                data[key].pop(ident, None)
    return _save(data)


def add_placeholders(map_ids, operator_ids, gamemode_ids=(), match_type_ids=()) -> dict:
    """Deja entradas vacias en el archivo para rellenarlas a mano.

    Es `setdefault`: nunca pisa una etiqueta que ya este puesta. Lo usa
    `unknown_ids --write`, que quiere el hueco, no borrar lo que haya.
    """
    data = read_overrides()
    pares = (
        ("maps", map_ids),
        ("operators", operator_ids),
        ("gamemodes", gamemode_ids),
        ("match_types", match_type_ids),
    )
    for key, ids in pares:
        for ident in ids:
            data[key].setdefault(str(ident), "")
    return _save(data)
