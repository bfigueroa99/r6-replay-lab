"""Punto de entrada del backend empaquetado.

`manage.py` sirve para desarrollo; esto es lo que corre dentro del `.exe`:
prepara la carpeta del usuario, aplica las migraciones que falten, hace la
copia semanal de la base, deja vigilando la carpeta de replays y levanta el
servidor. La app de escritorio lo lanza y espera a que `/api/health/` responda.

Todo lo que antes pedia una consola (`migrate`, `backup`, `watch_replays`) pasa
aca solo: quien baja el .exe no tiene por que saber que existe `manage.py`.

Se puede correr igual desde el repo (`python backend/serve.py`), y es lo que
usan `npm run desktop` y `scripts/start.ps1`: el camino es el mismo que el
del .exe, sin empaquetar.
"""

from __future__ import annotations

import logging
import os
import sys
from pathlib import Path

HOST = "127.0.0.1"
PORT = 8000


def _preparar_entorno() -> None:
    """Deja el proyecto importable y apunta Django a su configuracion."""
    if not getattr(sys, "frozen", False):
        sys.path.insert(0, str(Path(__file__).resolve().parent))
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
    # el servidor de desarrollo de Django refusa arrancar con DEBUG en una app
    # empaquetada sin esto, y ademas no queremos tracebacks en pantalla. Solo
    # empaquetada: desde el repo (npm run desktop, start.ps1) decide el .env
    if getattr(sys, "frozen", False):
        os.environ.setdefault("DJANGO_DEBUG", "false")


def copia_semanal() -> None:
    """Copia de la base si la ultima tiene mas de una semana.

    Nunca frena el arranque: si falla, se anota y la app abre igual. Sin
    partidas no hay nada que valga la pena copiar, y copiar la base vacia del
    primer arranque correria la siguiente copia una semana.
    """
    from replays.backup import backup_database, hace_falta_copia
    from replays.models import Match

    try:
        if Match.objects.exists() and hace_falta_copia():
            result = backup_database()
            print(f"[r6] copia semanal de la base: {result.path}", flush=True)
    # amplio a proposito: un backup que falla no puede dejar la app sin abrir
    except Exception:
        logging.getLogger(__name__).exception("no se pudo hacer la copia semanal")


def main(argv: list[str] | None = None) -> int:
    _preparar_entorno()

    import django
    from django.conf import settings
    from django.core.management import call_command

    django.setup()

    settings.DATA_DIR.mkdir(parents=True, exist_ok=True)
    print(f"[r6] datos en {settings.DATA_DIR}", flush=True)

    # migrate es idempotente: en el primer arranque crea la base, despues no
    # hace nada. Sin esto la app empaquetada arrancaria sin tablas.
    call_command("migrate", interactive=False, verbosity=0)

    copia_semanal()

    from replays import vigilante

    vigilante.iniciar()
    estado = "prendida" if settings.AUTO_IMPORT else "apagada (se prende en Ajustes)"
    print(f"[r6] replays en {settings.REPLAY_DIR}; importacion automatica {estado}", flush=True)

    host = os.environ.get("R6_HOST", HOST)
    port = os.environ.get("R6_PORT", str(PORT))
    print(f"[r6] sirviendo en http://{host}:{port}", flush=True)

    # runserver y no un WSGI de produccion: es un solo usuario en su propia
    # maquina, y meter gunicorn/waitress seria una dependencia mas para nada.
    # --noreload es obligatorio: el autoreloader relanza el proceso, y dentro de
    # un ejecutable empaquetado eso significa arrancar la app entera de nuevo.
    call_command("runserver", f"{host}:{port}", use_reloader=False)
    return 0


if __name__ == "__main__":
    sys.exit(main())
