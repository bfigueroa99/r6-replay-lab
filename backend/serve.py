"""Punto de entrada del backend empaquetado.

`manage.py` sirve para desarrollo; esto es lo que corre dentro del `.exe`:
prepara la carpeta del usuario, aplica las migraciones que falten y levanta el
servidor. La app de escritorio lo lanza y espera a que `/api/health/` responda.

Se puede correr igual desde el repo (`python backend/serve.py`), que es la unica
forma de probar este camino sin empaquetar.
"""

from __future__ import annotations

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
    # empaquetada sin esto, y ademas no queremos tracebacks en pantalla
    os.environ.setdefault("DJANGO_DEBUG", "false")


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
