"""Lo que se sabe de un jugador fuera de tus replays: trackers y API de Ubisoft.

Abrir un perfil nunca sale a la red. Los enlaces los abre el navegador, y la
API de Ubisoft corre solo cuando el usuario aprieta el boton; lo que devuelve se
guarda en `PerfilUbisoft` y se muestra con su fecha.
"""

from __future__ import annotations

import json
import logging
import threading
from datetime import datetime

from django.conf import settings

from externo import enlaces, ubisoft

from .models import PerfilUbisoft, Player

log = logging.getLogger(__name__)

#: Se reemplaza en los tests: ninguno puede salir a internet.
abrir = ubisoft.abrir_red

# Dos clics seguidos harian dos logins, y Ubisoft corta la IP con pocos
_candado = threading.Lock()


def configurado() -> bool:
    return bool(settings.UBI_EMAIL and settings.UBI_PASSWORD)


def consultable(player: Player) -> bool:
    return enlaces.es_profile_id(player.profile_id)


def resumen(player: Player) -> dict:
    guardado = PerfilUbisoft.objects.filter(player=player).first()
    return {
        "enlaces": enlaces.enlaces(player.profile_id, player.username),
        "ubisoft": {
            "configurado": configurado(),
            "consultable": consultable(player),
            "datos": guardado.datos if guardado else None,
            "consultado": guardado.consultado.isoformat() if guardado else None,
        },
    }


def actualizar(player: Player) -> PerfilUbisoft:
    """Consulta a Ubisoft y guarda el resultado. Propaga `ubisoft.ErrorUbisoft`."""
    with _candado:
        datos = _consultar(player.profile_id)
    obj, _ = PerfilUbisoft.objects.update_or_create(
        player=player, defaults={"datos": datos, "consultado": datetime.now()}
    )
    return obj


def _consultar(profile_id: str) -> dict:
    guardada = _leer_sesion()
    if guardada and guardada.vigente():
        try:
            return ubisoft.perfil(guardada, profile_id, abrir=abrir)
        except ubisoft.SesionVencida:
            pass  # el ticket guardado murio antes de lo que decia
    sesion = ubisoft.iniciar_sesion(settings.UBI_EMAIL, settings.UBI_PASSWORD, abrir=abrir)
    _guardar_sesion(sesion)
    try:
        return ubisoft.perfil(sesion, profile_id, abrir=abrir)
    except ubisoft.SesionVencida as exc:
        # con un ticket recien emitido, otro login daria lo mismo
        raise ubisoft.ErrorUbisoft(
            "Ubisoft rechazó la consulta incluso con una sesión nueva (HTTP 401)."
        ) from exc


# --------------------------------------------------------------------- sesion


def _cuenta() -> str:
    return settings.UBI_EMAIL.strip().lower()


def _leer_sesion() -> ubisoft.Sesion | None:
    try:
        data = json.loads(settings.UBI_SESION_PATH.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    # un ticket de otra cuenta no sirve: el usuario cambio el .env
    if not isinstance(data, dict) or data.get("cuenta") != _cuenta():
        return None
    return ubisoft.Sesion.desde_dict(data)


def _guardar_sesion(sesion: ubisoft.Sesion) -> None:
    try:
        settings.UBI_SESION_PATH.parent.mkdir(parents=True, exist_ok=True)
        settings.UBI_SESION_PATH.write_text(
            json.dumps({"cuenta": _cuenta(), **sesion.como_dict()}), encoding="utf-8"
        )
    except OSError as exc:
        # sin cache se loguea en cada consulta, que es lento pero funciona
        log.warning("no pude guardar la sesion de Ubisoft en %s: %s", settings.UBI_SESION_PATH, exc)
