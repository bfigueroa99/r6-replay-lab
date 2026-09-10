"""Etiquetas para IDs que el juego agrega despues de esta version del parser.

Cada temporada Ubisoft cambia los IDs de mapas revampeados y agrega operadores.
En vez de dejar "Unknown(413779563590)" en la UI, el parser lee un JSON editable
y anota los IDs que no reconocio para que se puedan completar despues.

Ruta del JSON: variable de entorno ``PYDISSECT_OVERRIDES`` (Django la apunta a
``data/overrides.json``). Formato::

    {
      "maps": {"436375283234": "Coastline"},
      "operators": {"123456789": "NombreOperador"}
    }
"""

from __future__ import annotations

import json
import logging
import os
from pathlib import Path

log = logging.getLogger(__name__)

ENV_VAR = "PYDISSECT_OVERRIDES"

_cache: dict | None = None
_unknown: dict[str, set[int]] = {"maps": set(), "operators": set()}


def _path() -> Path | None:
    raw = os.environ.get(ENV_VAR, "").strip()
    return Path(raw) if raw else None


def load(force: bool = False) -> dict:
    global _cache
    if _cache is not None and not force:
        return _cache
    _cache = {"maps": {}, "operators": {}}
    path = _path()
    if path and path.exists():
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
            for key in ("maps", "operators"):
                for k, v in (raw.get(key) or {}).items():
                    try:
                        _cache[key][int(k)] = str(v)
                    except (TypeError, ValueError):
                        log.warning("id invalido en %s: %r", path, k)
        except (OSError, json.JSONDecodeError) as exc:
            log.warning("no se pudo leer %s: %s", path, exc)
    return _cache


def extra_map(map_id: int) -> str | None:
    return load()["maps"].get(map_id)


def extra_operator(op_id: int) -> str | None:
    return load()["operators"].get(op_id)


def record_unknown(kind: str, value: int) -> None:
    """Anota un ID no reconocido (se consulta con `manage.py unknown_ids`)."""
    if value:
        _unknown.setdefault(kind, set()).add(int(value))


def unknown_ids() -> dict[str, list[int]]:
    return {k: sorted(v) for k, v in _unknown.items() if v}


def reset_unknown() -> None:
    for value in _unknown.values():
        value.clear()
