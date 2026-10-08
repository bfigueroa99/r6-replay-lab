"""Lo que se configura desde la pagina Ajustes.

Antes, cambiar la carpeta de replays pedia crear un `.env` a mano en
`%APPDATA%`, y quien usa el .exe no tenia por que saber eso. Ahora la pagina
escribe el mismo `.env` (ver `config/envfile.py`) y el cambio se aplica en
caliente, sin reiniciar la app.
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

from django.conf import settings

from config import envfile, replay_dir

from . import backup, vigilante
from .ingest import find_match_folders


class AjusteInvalido(ValueError):
    """Un ajuste que no se guarda. El mensaje lo lee el usuario tal cual."""


def estado() -> dict:
    carpeta = Path(settings.REPLAY_DIR)
    return {
        "replay_dir": settings.REPLAY_DIR,
        "replay_dir_source": settings.REPLAY_DIR_ORIGEN,
        "replay_dir_exists": carpeta.is_dir(),
        "replay_dir_folders": len(find_match_folders(carpeta)),
        "auto_import": vigilante.estado(),
        "env_file": str(settings.ENV_FILE),
        "data_dir": str(settings.DATA_DIR),
        "backups": copias(),
    }


def copias() -> dict:
    return {
        "dir": str(backup.backups_dir()),
        "keep": backup.KEEP_DEFAULT,
        "every_days": backup.DIAS_ENTRE_COPIAS,
        "items": [
            {
                "name": copia.name,
                "size": copia.stat().st_size,
                "created_at": datetime.fromtimestamp(copia.stat().st_mtime).isoformat(
                    timespec="seconds"
                ),
            }
            for copia in backup.existing_backups()
        ],
    }


def _carpeta(valor) -> str | None:
    """La carpeta a guardar. None es volver a buscarla sola."""
    if valor is None or (isinstance(valor, str) and not valor.strip()):
        return None
    if not isinstance(valor, str):
        raise AjusteInvalido("La carpeta tiene que ser una ruta.")
    ruta = Path(valor.strip()).expanduser()
    # relativa dependeria de desde donde se lanzo el backend, que el usuario no ve
    if not ruta.is_absolute():
        raise AjusteInvalido(f"Usa la ruta completa, con la unidad: {valor.strip()}")
    if not ruta.is_dir():
        raise AjusteInvalido(f"No existe la carpeta {valor.strip()}")
    return str(replay_dir.normalizar(ruta))


def aplicar(cambios: dict) -> None:
    """Valida todo, escribe el `.env` y aplica en caliente.

    Solo cambia lo que viene en `cambios`. Si algo no valida no se escribe
    nada: guardar la mitad dejaria al usuario sin saber que quedo.
    """
    if not isinstance(cambios, dict):
        raise AjusteInvalido("Se esperaba un objeto JSON.")

    escribir: dict[str, str | None] = {}
    if "replay_dir" in cambios:
        escribir["REPLAY_DIR"] = _carpeta(cambios["replay_dir"])
    if "auto_import" in cambios:
        if not isinstance(cambios["auto_import"], bool):
            raise AjusteInvalido("auto_import tiene que ser true o false.")
        escribir["AUTO_IMPORT"] = "true" if cambios["auto_import"] else "false"
    if not escribir:
        raise AjusteInvalido("No mandaste ningun ajuste.")

    try:
        envfile.escribir(settings.ENV_FILE, escribir)
    except envfile.ValorInvalido as exc:
        raise AjusteInvalido(str(exc)) from exc

    # settings se calcula una vez al arrancar: sin esto el cambio quedaria en el
    # archivo pero la app seguiria con lo viejo hasta reiniciarla
    if "REPLAY_DIR" in escribir:
        settings.REPLAY_DIR, settings.REPLAY_DIR_ORIGEN = replay_dir.resolver(
            escribir["REPLAY_DIR"]
        )
    if "AUTO_IMPORT" in escribir:
        settings.AUTO_IMPORT = escribir["AUTO_IMPORT"] == "true"
