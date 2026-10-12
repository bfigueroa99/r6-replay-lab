"""Enlaces a sitios de la comunidad: trackers por jugador y spawn peeks por mapa.

No hace ninguna request: arma la URL con lo que trae el replay (el profileID o
el mapa) y el navegador del usuario hace el resto. Por eso funciona aunque
stats.cc y R6 Tracker bloqueen a cualquier cliente que no sea un navegador, y
por eso peekabooR6, que no tiene API, entra como enlace y no como datos.
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


PEEKABOO = "https://peekaboor6.com/maps/"

#: Los mapas que tiene peekabooR6 (octubre de 2026), con la clave solo en letras.
#: La app arma el slug desde el nombre, y un mapa etiquetado a mano puede
#: llegar como "Club House" o como "Clubhouse": sin espacios ni guiones son el
#: mismo. Un mapa que el sitio no tiene se queda sin enlace en vez de llevar a
#: un 404.
_PEEKABOO_MAPAS = {
    re.sub(r"[^a-z0-9]", "", slug): slug
    for slug in (
        "bank", "border", "calypso-casino", "chalet", "clubhouse", "coastline", "consulate",
        "emerald-plains", "fortress", "kafe-dostoyevsky", "kanal", "lair", "nighthaven-labs",
        "oregon", "outback", "skyscraper", "theme-park", "villa",
    )
}


def spawn_peeks(mapa: str | None) -> str | None:
    """La pagina del mapa en peekabooR6, o None si el sitio no lo tiene.

    Acepta el slug o el nombre: el coach solo tiene el nombre a mano.
    """
    slug = _PEEKABOO_MAPAS.get(re.sub(r"[^a-z0-9]", "", (mapa or "").lower()))
    return f"{PEEKABOO}{slug}" if slug else None
