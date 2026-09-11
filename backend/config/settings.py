"""Configuracion de Django para R6 Replay Lab.

Todo lo configurable vive en el archivo .env de la raiz del repo (copia
.env.example). No hay servicios externos: SQLite y listo.
"""

from __future__ import annotations

import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent          # backend/
REPO_DIR = BASE_DIR.parent                                  # raiz del repo


def _load_env() -> None:
    """Lector de .env minimo, para no depender de python-dotenv."""
    env_file = REPO_DIR / ".env"
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

DATA_DIR = Path(env("DATA_DIR", str(REPO_DIR / "data")))
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
STATICFILES_DIRS = [d for d in [REPO_DIR / "frontend" / "dist"] if d.exists()]

# --------------------------------------------------------------------- app

#: JSON con nombres para IDs de mapas/operadores que el parser no conoce.
OVERRIDES_PATH = Path(env("OVERRIDES_PATH", str(DATA_DIR / "overrides.json")))
os.environ.setdefault("PYDISSECT_OVERRIDES", str(OVERRIDES_PATH))

#: Carpeta donde Siege deja los replays.
REPLAY_DIR = env(
    "REPLAY_DIR",
    r"D:\Program Files (x86)\Steam\steamapps\common\Tom Clancy's Rainbow Six Siege\MatchReplay",
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
