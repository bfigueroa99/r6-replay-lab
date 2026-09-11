"""Export de los agregados a CSV.

Dos caminos a proposito, cada uno afinado para quien lo consume:

- **Este modulo** es el camino de scripting: CSV estandar (coma, punto decimal,
  sin BOM), el que espera pandas o cualquier parser.
- **El boton de la UI** genera el CSV en el navegador con punto y coma y coma
  decimal, que es lo que Excel en espanol abre sin preguntar nada.

Si se unificaran, uno de los dos quedaria incomodo.
"""

from __future__ import annotations

import csv
from io import StringIO

from .analytics import aggregates as agg

#: Tablas exportables: nombre -> (titulo, funcion que devuelve las filas).
#: Reciben los mismos filtros que el resto de la API.
TABLES = {
    "maps": ("mapas", lambda **f: agg.by_map(min_rounds=1, **f)),
    "sites": ("sitios", lambda **f: agg.by_site(min_rounds=1, **f)),
    "spawns": ("spawns", lambda **f: agg.by_spawn(min_rounds=1, **f)),
    "operators": ("operadores", lambda **f: agg.by_operator(min_rounds=1, **f)),
    "positioning_sites": (
        "posicion-sitios",
        lambda **f: agg.positioning(min_rounds=1, **f)["sites"],
    ),
    "positioning_spawns": (
        "posicion-spawns",
        lambda **f: agg.positioning(min_rounds=1, **f)["spawns"],
    ),
    "rounds": ("por-ronda", agg.by_round_number),
    "days": ("por-dia", agg.trend_by_day),
    "matches": ("por-partida", lambda **f: agg.trend_by_match(limit=1000, **f)),
    "sessions": ("sesiones", agg.sessions),
    "session_positions": ("curva-de-sesion", agg.by_session_position),
    "teammates": ("companeros", lambda **f: agg.teammate_synergy(min_rounds=1, **f)),
    "clutches": ("clutches", agg.clutch_detail),
    "nemesis": ("rivales", lambda **f: agg.nemesis(min_duels=1, **f)),
    "duel_operators": ("duelos-por-operador", lambda **f: agg.duels_by_operator(min_duels=1, **f)),
}


def table_names() -> list[str]:
    return sorted(TABLES)


#: Columnas que identifican la fila y sus numeros principales. Van primero y en
#: este orden: sin esto el CSV abre con los alias internos del agregado y el
#: nombre del mapa queda perdido en la columna 16.
_PRIMERAS = (
    "map", "slug", "site", "spawn", "operator", "side", "username", "player_id",
    "label", "position", "round_number", "day", "start", "end", "hours",
    "verdict", "caught_out_pct", "caught_out_delta", "noise",
    "match_id", "played_at", "matches", "rounds", "rounds_won", "winrate",
    "rating", "kills", "deaths", "kd", "kpr",
)


def _columnas(rows: list[dict]) -> list[str]:
    """Union de claves: primero las identificatorias, despues el resto."""
    vistas: list[str] = []
    for row in rows:
        for clave in row:
            if clave not in vistas:
                vistas.append(clave)
    primeras = [c for c in _PRIMERAS if c in vistas]
    return primeras + [c for c in vistas if c not in primeras]


def _valor(valor) -> str:
    if valor is None:
        return ""
    if isinstance(valor, bool):
        return "si" if valor else "no"
    if isinstance(valor, (list, tuple)):
        return " / ".join(str(v) for v in valor)
    return str(valor)


def to_csv(rows: list[dict], delimiter: str = ",") -> str:
    """CSV estandar. Sin filas, devuelve solo la cabecera vacia."""
    salida = StringIO()
    columnas = _columnas(rows)
    writer = csv.writer(salida, delimiter=delimiter, lineterminator="\r\n")
    writer.writerow(columnas)
    for row in rows:
        writer.writerow([_valor(row.get(col)) for col in columnas])
    return salida.getvalue()


def export(table: str, **filters) -> list[dict]:
    """Filas de una tabla. Lanza KeyError si el nombre no existe."""
    _, funcion = TABLES[table]
    return funcion(**filters)
