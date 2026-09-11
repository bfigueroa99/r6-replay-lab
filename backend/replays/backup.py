"""Copia de seguridad de la base.

Rehacer el historial cuesta minutos de parseo y, peor, **puede ser imposible**:
el propio juego va borrando los replays viejos de `MatchReplay`. Lo que ya se
importo puede no existir mas en disco.

No se usa `shutil.copy`: copiar un SQLite mientras alguien escribe deja un
archivo roto a la mitad. Se usa la API de backup online de SQLite, que hace una
copia consistente aunque el server este corriendo.
"""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from django.conf import settings

#: Cuantas copias se conservan antes de ir borrando las mas viejas.
KEEP_DEFAULT = 10

PREFIX = "db-"
SUFFIX = ".sqlite3"


@dataclass
class BackupResult:
    path: Path
    size: int
    removed: list[Path]

    @property
    def size_mb(self) -> float:
        return round(self.size / (1024 * 1024), 2)


def database_path() -> Path:
    return Path(settings.DATABASES["default"]["NAME"])


def backups_dir() -> Path:
    return Path(settings.DATA_DIR) / "backups"


def existing_backups(carpeta: Path | str | None = None) -> list[Path]:
    """Copias que hay, de la mas nueva a la mas vieja.

    Se ordena por fecha del archivo y no por nombre: con el sufijo de colision
    (`...-2.sqlite3`) el orden alfabetico pone la mas nueva antes que la vieja,
    y la rotacion terminaria borrando la equivocada.
    """
    carpeta = Path(carpeta) if carpeta else backups_dir()
    if not carpeta.exists():
        return []
    copias = [p for p in carpeta.glob(f"{PREFIX}*{SUFFIX}") if p.is_file()]
    return sorted(copias, key=lambda p: (p.stat().st_mtime, p.name), reverse=True)


def backup_database(
    *, source: Path | None = None, dest_dir: Path | None = None, keep: int = KEEP_DEFAULT
) -> BackupResult:
    """Deja una copia con fecha y borra las que sobren.

    El nombre lleva la hora local y no UTC: se mira en el explorador de
    archivos, al lado de la hora en que uno se acuerda de haber jugado.
    """
    origen = Path(source) if source else database_path()
    if not origen.exists():
        raise FileNotFoundError(f"no existe la base en {origen}")

    carpeta = Path(dest_dir) if dest_dir else backups_dir()
    carpeta.mkdir(parents=True, exist_ok=True)
    destino = _nombre_libre(carpeta)

    conexion_origen = sqlite3.connect(f"file:{origen}?mode=ro", uri=True)
    try:
        conexion_destino = sqlite3.connect(destino)
        try:
            with conexion_destino:
                conexion_origen.backup(conexion_destino)
        finally:
            conexion_destino.close()
    finally:
        conexion_origen.close()

    return BackupResult(destino, destino.stat().st_size, _rotar(carpeta, keep))


def _nombre_libre(carpeta: Path) -> Path:
    """Nombre con fecha, y un sufijo si ya existe.

    El nombre llega al segundo: dos copias seguidas caen en el mismo, y sin esto
    la segunda pisaria a la primera en silencio.
    """
    sello = f"{datetime.now():%Y%m%d-%H%M%S}"
    destino = carpeta / f"{PREFIX}{sello}{SUFFIX}"
    intento = 2
    while destino.exists():
        destino = carpeta / f"{PREFIX}{sello}-{intento}{SUFFIX}"
        intento += 1
    return destino


def _rotar(carpeta: Path, keep: int) -> list[Path]:
    """Borra las copias mas viejas. `keep <= 0` las conserva todas."""
    if keep <= 0:
        return []
    sobran = existing_backups(carpeta)[keep:]
    for copia in sobran:
        copia.unlink(missing_ok=True)
    return sobran
