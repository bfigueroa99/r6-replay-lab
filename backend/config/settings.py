"""Configuracion de Django para R6 Replay Lab.

Todo lo configurable vive en el archivo .env (copia .env.example). SQLite y
listo; el unico servicio externo es la API de Ubisoft, y solo si el .env trae
una cuenta.

Corre de dos formas y hay que distinguirlas, porque los archivos van a lugares
distintos:

- **desde el repo** (desarrollo): todo cuelga de la raiz del repo.
- **empaquetado** con PyInstaller: los archivos de la app viven dentro del
  bundle, que es de solo lectura y se borra al cerrar, asi que la base, el .env
  y los overrides tienen que ir a la carpeta del usuario.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

from config import replay_dir

#: True cuando corre dentro del ejecutable empaquetado.
FROZEN = bool(getattr(sys, "frozen", False))

BASE_DIR = Path(__file__).resolve().parent.parent          # backend/
REPO_DIR = BASE_DIR.parent                                  # raiz del repo

if FROZEN:
    #: Archivos que viajan con la app (frontend compilado, plantillas).
    BUNDLE_DIR = Path(getattr(sys, "_MEIPASS", REPO_DIR))
    #: Donde el usuario tiene sus datos. Nunca dentro del bundle: se borra.
    USER_DIR = Path(
        os.environ.get("APPDATA") or Path.home() / ".local" / "share"
    ) / "r6-replay-lab"
else:
    BUNDLE_DIR = REPO_DIR
    USER_DIR = REPO_DIR

#: El build de React que sirve la vista del SPA.
FRONTEND_DIST = BUNDLE_DIR / "frontend" / "dist"


def _load_env() -> None:
    """Lector de .env minimo, para no depender de python-dotenv."""
    env_file = USER_DIR / ".env"
    if not env_file.exists():
        return
    for line in env_file.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


_load_env()


def env(key: str, default: str = "") -> str:
    return os.environ.get(key, default)


def env_bool(key: str, default: bool = False) -> bool:
    return env(key, str(default)).strip().lower() in ("1", "true", "yes", "si", "on")


def env_int(key: str, default: int) -> int:
    try:
        return int(env(key, str(default)))
    except ValueError:
        return default


# --------------------------------------------------------------------- basico

SECRET_KEY = env("DJANGO_SECRET_KEY", "dev-only-key-cambiala-si-la-expones")
DEBUG = env_bool("DJANGO_DEBUG", True)
ALLOWED_HOSTS = [h for h in env("DJANGO_ALLOWED_HOSTS", "127.0.0.1,localhost").split(",") if h]

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "replays",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"
WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

# --------------------------------------------------------------------- datos

DATA_DIR = Path(env("DATA_DIR", str(USER_DIR / "data")))
DATA_DIR.mkdir(parents=True, exist_ok=True)

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": Path(env("SQLITE_PATH", str(DATA_DIR / "db.sqlite3"))),
        "OPTIONS": {"timeout": 20},
    }
}

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
]

# --------------------------------------------------------------------- i18n

LANGUAGE_CODE = "es-cl"
TIME_ZONE = env("TIME_ZONE", "America/Santiago")
USE_I18N = True
# Los replays traen hora local sin zona; se guarda tal cual para que los
# graficos por dia coincidan con la sesion real de juego.
USE_TZ = False

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [d for d in [FRONTEND_DIST] if d.exists()]

# --------------------------------------------------------------------- app

#: JSON con nombres para IDs de mapas/operadores que el parser no conoce.
OVERRIDES_PATH = Path(env("OVERRIDES_PATH", str(DATA_DIR / "overrides.json")))
os.environ.setdefault("PYDISSECT_OVERRIDES", str(OVERRIDES_PATH))

#: Carpeta donde Siege deja los replays. Si el .env no la fija, se busca sola
#: (Steam, Ubisoft Connect y las rutas tipicas de cada unidad): la app instalada
#: tiene que mostrar partidas al primer doble clic, sin editar nada.
REPLAY_DIR = env("REPLAY_DIR") or str(
    replay_dir.detectar()
    or r"C:\Program Files (x86)\Steam\steamapps\common\Tom Clancy's Rainbow Six Siege\MatchReplay"
)

#: Segundos sin cambios en los .rec para considerar que la partida termino.
IMPORT_QUIET_SECONDS = env_int("IMPORT_QUIET_SECONDS", 60)

#: Cada cuanto revisa la carpeta el comando `watch_replays`.
WATCH_INTERVAL_SECONDS = env_int("WATCH_INTERVAL_SECONDS", 20)

#: Muestra minima por defecto para que un agregado aparezca en la UI.
MIN_ROUNDS_DEFAULT = env_int("MIN_ROUNDS_DEFAULT", 5)

#: Minutos sin jugar para considerar que empezo otra sesion.
SESSION_GAP_MINUTES = env_int("SESSION_GAP_MINUTES", 120)

#: Segundos para considerar que una muerte fue vengada. r6-dissect usa 3; las
#: planillas de Pro League usan hasta 10. Cambiarlo obliga a `manage.py
#: recompute`, porque los trades se guardan calculados al importar.
TRADE_WINDOW_SECONDS = float(env("TRADE_WINDOW_SECONDS", "3") or 3)

#: Cuenta de Ubisoft para consultar rango y MMR. Vacias = la app no sale a la
#: red. Solo se usan para pedir un ticket; lo que se guarda es el ticket.
UBI_EMAIL = env("UBI_EMAIL")
UBI_PASSWORD = env("UBI_PASSWORD")

#: Donde queda el ticket de Ubisoft entre consultas, para no loguear en cada una
#: (Ubisoft bloquea la IP si se loguea muy seguido).
UBI_SESION_PATH = Path(env("UBI_SESION_PATH", str(DATA_DIR / "ubisoft-sesion.json")))

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {"simple": {"format": "%(asctime)s %(levelname)-7s %(name)s: %(message)s"}},
    "handlers": {"console": {"class": "logging.StreamHandler", "formatter": "simple"}},
    "root": {"handlers": ["console"], "level": env("LOG_LEVEL", "INFO")},
    "loggers": {
        "django.db.backends": {"level": "WARNING", "handlers": ["console"], "propagate": False},
        "pydissect": {"level": env("PYDISSECT_LOG_LEVEL", "WARNING")},
    },
}
