# Empaqueta el backend en un solo ejecutable con su propio Python adentro.
#
#   .\.venv\Scripts\pyinstaller.exe packaging\backend.spec --noconfirm
#
# Sale en dist\r6-backend\r6-backend.exe. Es lo que lanza la app de escritorio
# cuando esta instalada; en desarrollo sigue lanzando manage.py del venv.
#
# Django importa un monton de cosas por nombre (apps, migraciones, backends de
# base y de plantillas), y nada de eso se ve siguiendo los `import` del codigo:
# por eso van explicitos aca abajo.

from pathlib import Path

from PyInstaller.utils.hooks import collect_submodules

REPO = Path(SPECPATH).parent
BACKEND = REPO / "backend"

hiddenimports = [
    # las apps de Django que usa el proyecto y sus dependencias internas
    *collect_submodules("django.contrib.admin"),
    *collect_submodules("django.contrib.auth"),
    *collect_submodules("django.contrib.contenttypes"),
    *collect_submodules("django.contrib.messages"),
    *collect_submodules("django.contrib.sessions"),
    *collect_submodules("django.contrib.staticfiles"),
    "django.db.backends.sqlite3",
    "django.template.backends.django",
    # las migraciones y los comandos se cargan por nombre, no por import
    *collect_submodules("replays"),
    *collect_submodules("pydissect"),
    "config.settings",
    "config.urls",
    "config.wsgi",
]

datas = [
    # el SPA compilado: lo sirve Django, igual que corriendo desde el repo
    (str(REPO / "frontend" / "dist"), "frontend/dist"),
]

a = Analysis(
    [str(BACKEND / "serve.py")],
    pathex=[str(BACKEND)],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    # el admin de Django arrastra cosas que esta app no usa; se dejan igual
    # porque sacarlas rompe el registro de apps y el ahorro no vale el riesgo
    excludes=["tkinter", "test", "unittest.test"],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="r6-backend",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=True,
    disable_windowed_traceback=False,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    name="r6-backend",
)
