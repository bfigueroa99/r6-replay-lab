"""Enlaces al perfil de un jugador en los trackers web.

No hace ninguna request: arma la URL con el profileID que trae el replay y el
navegador del usuario hace el resto. Por eso funciona aunque stats.cc y R6
Tracker bloqueen a cualquier cliente que no sea un navegador.
"""

from __future__ import annotations

import re
from urllib.parse import quote

# El replay trae el profileID de Ubisoft. Cuando falta, la ingesta guarda
# `name:<nick>` y con eso no hay perfil al que apuntar.
_PROFILE_ID = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$", re.I)


def es_profile_id(valor: str | None) -> bool:
    return bool(valor and _PROFILE_ID.match(valor.strip()))


def enlaces(profile_id: str | None, username: str | None) -> list[dict]:
    """Un enlace por sitio, o ninguno si el jugador no tiene profileID."""
    if not es_profile_id(profile_id):
        return []
    pid = profile_id.strip().lower()
    # stats.cc usa el nick solo de adorno en la URL; el que manda es el id
    nick = quote((username or "").strip() or pid, safe="")
    return [
        {"sitio": "stats.cc", "url": f"https://stats.cc/siege/{nick}/{pid}"},
        {
            "sitio": "R6 Tracker",
            "url": f"https://r6.tracker.network/r6siege/profile/ubi/{pid}/overview",
        },
    ]
