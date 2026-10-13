"""Importacion automatica dentro del propio servidor.

`manage.py watch_replays` hace lo mismo, pero pide una consola abierta, y la app
instalada no tiene consola: el backend que lanza el .exe (`serve.py`) vigila la
carpeta en un hilo propio. Abrir la app ya importa lo que jugaste desde la
ultima vez, y con la app abierta cada partida entra sola al terminar.

Usa el mismo trabajo de importacion que el boton (`ImportJob`), asi que nunca
corren dos a la vez y la UI ve el avance igual, venga de donde venga.
"""

from __future__ import annotations

import logging
import threading
from datetime import datetime
from pathlib import Path

from django.conf import settings
from django.db import connections

from . import ingest

log = logging.getLogger(__name__)

_hilo: threading.Thread | None = None
_parar = threading.Event()
_ultima_revision: datetime | None = None

#: Carpeta -> firma de cuando ya se intento. Una carpeta que no se puede leer
#: no queda en `Match`, y sin esto se reintentaria cada 20 segundos para
#: siempre: un `ImportLog` nuevo y un parseo entero en cada pasada.
_intentadas: dict[str, tuple[int, float]] = {}


def _firma(carpeta: Path) -> tuple[int, float]:
    """Cuantos .rec hay y el mas nuevo: si cambia, vale la pena reintentar."""
    fechas = [p.stat().st_mtime for p in carpeta.glob("*.rec")]
    return len(fechas), max(fechas, default=0.0)


def _ya_intentada(carpeta: Path) -> bool:
    return _intentadas.get(carpeta.name) == _firma(carpeta)


def revisar() -> int:
    """Una pasada: importa las partidas que ya terminaron. Sincrona.

    Devuelve cuantas carpetas tomo. Separada del hilo para poder probarla: en
    los tests un hilo abre otra conexion y no ve los datos de la transaccion.
    """
    global _ultima_revision
    _ultima_revision = datetime.now()
    if not settings.AUTO_IMPORT:
        return 0
    raiz = Path(settings.REPLAY_DIR)
    if not raiz.is_dir():
        return 0

    carpetas = ingest.reserve_import(
        raiz,
        quiet_seconds=settings.IMPORT_QUIET_SECONDS,
        origin="auto",
        even_if_empty=False,
        skip=_ya_intentada,
    )
    if carpetas is None:
        return 0

    for carpeta in carpetas:
        _intentadas[carpeta.name] = _firma(carpeta)
    ingest.run_import_job(carpetas)
    return len(carpetas)


def _bucle() -> None:
    while not _parar.is_set():
        try:
            tomadas = revisar()
            if tomadas:
                log.info("importacion automatica: %s carpeta(s)", tomadas)
        # amplio a proposito: un error en una pasada no puede matar al vigilante
        except Exception:
            log.exception("fallo una pasada de la importacion automatica")
        finally:
            # el hilo vive lo que la app: sin esto arrastra una conexion abierta
            connections.close_all()
        _parar.wait(max(1, settings.WATCH_INTERVAL_SECONDS))


def iniciar() -> bool:
    """Arranca el hilo, una sola vez. Devuelve False si ya estaba corriendo."""
    global _hilo
    if corriendo():
        return False
    _parar.clear()
    _hilo = threading.Thread(target=_bucle, daemon=True, name="r6-vigilante")
    _hilo.start()
    return True


def detener(timeout: float = 5.0) -> None:
    """Para el hilo. La app no lo necesita (es daemon); los tests si."""
    global _hilo
    _parar.set()
    if _hilo is not None:
        _hilo.join(timeout)
    _hilo = None


def corriendo() -> bool:
    return _hilo is not None and _hilo.is_alive()


def estado() -> dict:
    """Lo que muestra Ajustes: si esta prendido y si de verdad hay un hilo."""
    return {
        "enabled": settings.AUTO_IMPORT,
        "running": corriendo(),
        "interval": settings.WATCH_INTERVAL_SECONDS,
        "quiet_seconds": settings.IMPORT_QUIET_SECONDS,
        "last_check": _ultima_revision.isoformat(timespec="seconds") if _ultima_revision else None,
    }
