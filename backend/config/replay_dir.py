"""Autodeteccion de la carpeta MatchReplay de Siege.

Instalada en otro PC, la app no puede pedir que alguien edite un `.env` antes
de ver nada: tiene que encontrar la carpeta sola. Siege se instala por Steam o
por Ubisoft Connect, y los dos dejan rastro de donde ponen sus juegos:

- Steam lista todas sus bibliotecas en `steamapps/libraryfolders.vdf`.
- Ubisoft Connect guarda la carpeta de juegos en `settings.yml`.

Ademas se prueban las rutas tipicas en cada unidad, por si el launcher esta en
un lado raro o el archivo de configuracion cambio de formato. Todo es
`Path.is_dir()`: unas decenas de stats, nada que se note al arrancar.

Sin Django a proposito: lo importa `settings.py` y no al reves.
"""

from __future__ import annotations

import os
import re
from pathlib import Path

NOMBRE_JUEGO = "Tom Clancy's Rainbow Six Siege"
MATCH_REPLAY = "MatchReplay"

#: Rutas relativas a la raiz de una unidad donde suelen vivir los launchers.
_RELATIVAS_POR_UNIDAD = (
    Path("Program Files (x86)/Steam/steamapps/common"),
    Path("Program Files/Steam/steamapps/common"),
    Path("Steam/steamapps/common"),
    Path("SteamLibrary/steamapps/common"),
    Path("Games/Steam/steamapps/common"),
    Path("Program Files (x86)/Ubisoft/Ubisoft Game Launcher/games"),
    Path("Program Files/Ubisoft/Ubisoft Game Launcher/games"),
    Path("Ubisoft/Ubisoft Game Launcher/games"),
    Path("Games/Ubisoft/Ubisoft Game Launcher/games"),
    Path("Games"),
)

_VDF_PATH = re.compile(r'"path"\s+"([^"]+)"')
_UBI_PATH = re.compile(r"^\s*game_installation_path:\s*(.+?)\s*$", re.MULTILINE)


def unidades_windows() -> list[Path]:
    """Raices de unidad que existen (C:\\, D:\\ ...). Vacio fuera de Windows."""
    if os.name != "nt":
        return []
    return [p for letra in "CDEFGHIJKLMNOPQRSTUVWXYZ" if (p := Path(f"{letra}:\\")).is_dir()]


def bibliotecas_steam(vdf: Path) -> list[Path]:
    """Carpetas de biblioteca de Steam listadas en `libraryfolders.vdf`.

    El archivo es VDF (parecido a JSON sin comas) y las rutas van con las
    barras escapadas. Con una regex basta: solo interesa la clave `path`.
    """
    try:
        texto = vdf.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return []
    return [Path(ruta.replace("\\\\", "\\")) for ruta in _VDF_PATH.findall(texto)]


def carpeta_juegos_ubisoft(settings_yml: Path) -> Path | None:
    """Carpeta donde Ubisoft Connect instala sus juegos, segun su `settings.yml`."""
    try:
        texto = settings_yml.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return None
    match = _UBI_PATH.search(texto)
    if not match:
        return None
    return Path(match.group(1).strip("'\""))


def candidatos(env: dict | None = None, unidades: list[Path] | None = None) -> list[Path]:
    """Rutas posibles de MatchReplay, de mas a menos probable, sin repetir.

    `env` y `unidades` se inyectan para poder probar esto en cualquier sistema.
    """
    env = os.environ if env is None else env
    unidades = unidades_windows() if unidades is None else unidades
    juego = Path(NOMBRE_JUEGO) / MATCH_REPLAY

    raices: list[Path] = []

    # 1. lo que dicen los propios launchers
    program_files_x86 = env.get("ProgramFiles(x86)") or env.get("PROGRAMFILES(X86)")
    if program_files_x86:
        steam = Path(program_files_x86) / "Steam"
        raices.append(steam / "steamapps" / "common")
        for biblioteca in bibliotecas_steam(steam / "steamapps" / "libraryfolders.vdf"):
            raices.append(biblioteca / "steamapps" / "common")
    local_app_data = env.get("LOCALAPPDATA")
    if local_app_data:
        ubisoft = carpeta_juegos_ubisoft(
            Path(local_app_data) / "Ubisoft Game Launcher" / "settings.yml"
        )
        if ubisoft:
            raices.append(ubisoft)

    # 2. las rutas tipicas, unidad por unidad
    for unidad in unidades:
        raices.extend(unidad / relativa for relativa in _RELATIVAS_POR_UNIDAD)

    vistos: set[str] = set()
    salida: list[Path] = []
    for raiz in raices:
        ruta = raiz / juego
        clave = os.path.normcase(str(ruta))
        if clave not in vistos:
            vistos.add(clave)
            salida.append(ruta)
    return salida


def detectar(env: dict | None = None, unidades: list[Path] | None = None) -> Path | None:
    """Primera carpeta MatchReplay que existe, o None si no hay ninguna."""
    for ruta in candidatos(env, unidades):
        if ruta.is_dir():
            return ruta
    return None
