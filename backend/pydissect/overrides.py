"""Etiquetas para IDs que el juego agrega despues de esta version del parser.

Cada temporada Ubisoft cambia los IDs de mapas revampeados y agrega operadores.
En vez de dejar "Unknown(413779563590)" en la UI, el parser lee un JSON editable
y anota los IDs que no reconocio para que se puedan completar despues.

Ruta del JSON: variable de entorno ``PYDISSECT_OVERRIDES`` (Django la apunta a
``data/overrides.json``). Formato::

    {
      "maps": {"436375283234": "Coastline"},
      "operators": {"123456789": "NombreOperador"},
      "gamemodes": {"999": "NombreModo"},
      "match_types": {"999": "NombreTipo"}
    }

Las claves que falten (un JSON viejo con solo mapas y operadores) quedan vacias.
"""

from __future__ import annotations

import json
import logging
import os
from pathlib import Path

log = logging.getLogger(__name__)

ENV_VAR = "PYDISSECT_OVERRIDES"

CLAVES = ("maps", "operators", "gamemodes", "match_types")

_cache: dict | None = None
_unknown: dict[str, set[int]] = {clave: set() for clave in CLAVES}


def _path() -> Path | None:
    raw = os.environ.get(ENV_VAR, "").strip()
    return Path(raw) if raw else None


def leer_json(path: Path) -> dict | None:
    """El objeto JSON de `path`, o None si no se puede leer como tal.

    El archivo se edita a mano, asi que llega como lo deje el editor:
    `utf-8-sig` acepta el BOM que ponen el Bloc de notas viejo y PowerShell, y
    `ValueError` cubre tanto el JSON mal escrito como los bytes que no son
    UTF-8 (un archivo guardado en ANSI). Nada de eso puede tumbar un import.
    """
    try:
        raw = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, ValueError) as exc:
        log.warning("no se pudo leer %s: %s", path, exc)
        return None
    if not isinstance(raw, dict):
        log.warning("%s no trae un objeto JSON", path)
        return None
    return raw


def etiquetas(raw: dict, clave: str) -> dict[str, str]:
    """Los pares id -> nombre de una clave, solo los que son texto.

    Un `null` o un numero no son un nombre: con `str()` el mapa quedaba
    llamandose "None". El texto vacio se conserva: es el hueco que deja
    `unknown_ids --write` para rellenar.
    """
    valores = raw.get(clave)
    if not isinstance(valores, dict):
        return {}
    return {str(k): v for k, v in valores.items() if isinstance(v, str)}


def load(force: bool = False) -> dict:
    global _cache
    if _cache is not None and not force:
        return _cache
    _cache = {clave: {} for clave in CLAVES}
    path = _path()
    raw = leer_json(path) if path and path.exists() else None
    if raw is not None:
        for key in CLAVES:
            for k, v in etiquetas(raw, key).items():
                try:
                    _cache[key][int(k)] = v
                except ValueError:
                    log.warning("id invalido en %s: %r", path, k)
    return _cache


def extra_map(map_id: int) -> str | None:
    return load()["maps"].get(map_id)


def extra_operator(op_id: int) -> str | None:
    return load()["operators"].get(op_id)


def extra_gamemode(gamemode_id: int) -> str | None:
    return load()["gamemodes"].get(gamemode_id)


def extra_match_type(match_type_id: int) -> str | None:
    return load()["match_types"].get(match_type_id)


def record_unknown(kind: str, value: int) -> None:
    """Anota un ID no reconocido (se consulta con `manage.py unknown_ids`)."""
    if value:
        _unknown.setdefault(kind, set()).add(int(value))


def unknown_ids() -> dict[str, list[int]]:
    return {k: sorted(v) for k, v in _unknown.items() if v}


def reset_unknown() -> None:
    for value in _unknown.values():
        value.clear()
