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


#: Lo que se muestra cuando no hay ninguna: la ruta de Steam por defecto, que
#: es la mas comun y la que el usuario reconoce al leer el aviso.
POR_DEFECTO = Path(r"C:\Program Files (x86)\Steam\steamapps\common") / NOMBRE_JUEGO / MATCH_REPLAY


def resolver(configurada: str | None) -> tuple[str, str]:
    """La carpeta a usar y de donde salio: `elegida`, `detectada` o `no_encontrada`.

    Lo que fijo el usuario (en el `.env` o en Ajustes) siempre gana, exista o
    no: si la eligio mal, se le avisa, pero no se la cambia por otra a escondidas.
    """
    if configurada and configurada.strip():
        return configurada.strip(), "elegida"
    detectada = detectar()
    if detectada:
        return str(detectada), "detectada"
    return str(POR_DEFECTO), "no_encontrada"


def _tiene_partidas(ruta: Path) -> bool:
    try:
        return any(p.is_dir() and p.name.startswith("Match-") for p in ruta.iterdir())
    except OSError:
        return False


def normalizar(ruta: Path) -> Path:
    """Corrige la confusion mas comun al elegir la carpeta a mano.

    En el selector es facil quedarse un nivel arriba: la carpeta del juego en
    vez de su `MatchReplay`, o la de la biblioteca en vez de la del juego. Si la
    elegida no tiene partidas y la de abajo si existe, se usa esa.
    """
    if _tiene_partidas(ruta):
        return ruta
    for abajo in (ruta / MATCH_REPLAY, ruta / NOMBRE_JUEGO / MATCH_REPLAY):
        if abajo.is_dir():
            return abajo
    return ruta
