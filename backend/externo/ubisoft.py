"""Cliente minimo de la API de Ubisoft: rango, MMR y temporada de un jugador.

Es la misma API que leen stats.cc y R6 Tracker, sin pasar por ellos. No es una
API publica documentada: el AppId y los endpoints salen de siegeapi
(github.com/CNDRD/siegeapi), que los sigue temporada a temporada. Si Ubisoft los
cambia, esto falla con un error que dice que paso; nunca devuelve numeros
inventados.

Solo usa la libreria estandar. `abrir` se pasa como argumento para que los
tests corran sin red: recibe un `urllib.request.Request` y devuelve
`(status, cuerpo)`.
"""

from __future__ import annotations

import base64
import json
import urllib.error
import urllib.request
from collections.abc import Callable
from dataclasses import asdict, dataclass
from datetime import UTC, datetime, timedelta
from urllib.parse import quote

Abridor = Callable[[urllib.request.Request], tuple[int, bytes]]

APP_ID = "e3d5ea9e-50bd-43b7-88bf-39794f4e3d40"
#: Espacio de crossplay: ahi viven el rango, el nivel y el tiempo jugado de PC.
ESPACIO = "0d2ae42d-4c27-4cb7-af6c-2099062302bb"
USER_AGENT = "UbiServices_SDK_2020.Release.58_PC64_ansi_static"

URL_SESION = "https://public-ubiservices.ubi.com/v3/profiles/sessions"
URL_PERFILES = (
    "https://public-ubiservices.ubi.com/v2/spaces/{espacio}/title/r6s/skill/full_profiles"
    "?profile_ids={pid}&platform_families=pc"
)
URL_NIVEL = (
    "https://public-ubiservices.ubi.com/v1/spaces/{espacio}/title/r6s/rewards/public_profile"
    "?profile_id={pid}"
)
URL_TIEMPO = (
    "https://public-ubiservices.ubi.com/v1/profiles/stats"
    "?profileIds={pid}&spaceId={espacio}&statNames=PTotalTimePlayed"
)

TIMEOUT = 15
#: Un ticket que vence en menos de esto se descarta: la consulta son tres
#: requests y no conviene que el ultimo llegue con el ticket ya muerto.
MARGEN = timedelta(minutes=5)

# Ranked 2.0 (Y7S4 en adelante): el id del rango es el indice en esta lista.
_DIVISIONES = ("Cobre", "Bronce", "Plata", "Oro", "Platino", "Esmeralda", "Diamante")
RANGOS = (
    "Sin rango",
    *(f"{division} {nivel}" for division in _DIVISIONES for nivel in range(5, 0, -1)),
    "Campeones",
)


class ErrorUbisoft(Exception):
    """Cualquier cosa que impida traer el perfil. El mensaje va tal cual a la UI."""


class CredencialesInvalidas(ErrorUbisoft):
    pass


class DosPasos(ErrorUbisoft):
    pass


class SesionVencida(ErrorUbisoft):
    pass


class Limite(ErrorUbisoft):
    pass


class SinConexion(ErrorUbisoft):
    pass


@dataclass(frozen=True)
class Sesion:
    ticket: str
    session_id: str
    #: Tal cual la manda Ubisoft: vuelve en un header de cada request.
    expiracion: str

    def vence(self) -> datetime | None:
        # Ubisoft manda siete decimales y `fromisoformat` no siempre los acepta
        try:
            return datetime.fromisoformat(self.expiracion[:19]).replace(tzinfo=UTC)
        except ValueError:
            return None

    def vigente(self, ahora: datetime | None = None) -> bool:
        vence = self.vence()
        if vence is None:
            return False
        return vence - MARGEN > (ahora or datetime.now(UTC))

    def como_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def desde_dict(cls, data: dict) -> Sesion | None:
        try:
            return cls(str(data["ticket"]), str(data["session_id"]), str(data["expiracion"]))
        except (KeyError, TypeError):
            return None


# --------------------------------------------------------------------- red


def abrir_red(request: urllib.request.Request) -> tuple[int, bytes]:
    try:
        with urllib.request.urlopen(request, timeout=TIMEOUT) as respuesta:
            return respuesta.status, respuesta.read()
    except urllib.error.HTTPError as exc:
        # Ubisoft explica el error en el cuerpo; urlopen lo esconde en la excepcion
        return exc.code, exc.read()
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        motivo = getattr(exc, "reason", exc)
        raise SinConexion(f"No pude conectar con Ubisoft: {motivo}") from exc


def _json(status: int, cuerpo: bytes) -> dict:
    if status == 204 or not cuerpo:
        return {}
    try:
        data = json.loads(cuerpo)
    except (json.JSONDecodeError, UnicodeDecodeError):
        raise ErrorUbisoft(f"Ubisoft respondió algo que no es JSON (HTTP {status}).") from None
    return data if isinstance(data, dict) else {"datos": data}


def _detalle(data: dict, status: int) -> str:
    mensaje = data.get("message") or data.get("errorMessage") or ""
    codigo = data.get("httpCode") or status
    return f"HTTP {codigo}: {mensaje}" if mensaje else f"HTTP {codigo}"


def _revisar(status: int, data: dict) -> None:
    """Convierte los errores de Ubisoft en excepciones con un mensaje util."""
    codigo = data.get("httpCode") or (status if status >= 400 else None)
    if codigo is None:
        return
    if codigo == 429:
        raise Limite("Ubisoft está limitando las consultas. Espera unos minutos y reintenta.")
    if codigo == 401:
        raise SesionVencida("La sesión de Ubisoft venció.")
    if codigo == 404:
        raise ErrorUbisoft("Ubisoft no tiene ese perfil (¿juega en consola?).")
    raise ErrorUbisoft(f"Ubisoft devolvió un error ({_detalle(data, status)}).")


# --------------------------------------------------------------------- sesion


def iniciar_sesion(email: str, password: str, *, abrir: Abridor = abrir_red) -> Sesion:
    """Login con usuario y clave de Ubisoft. Devuelve el ticket para las consultas."""
    basico = base64.b64encode(f"{email}:{password}".encode()).decode()
    request = urllib.request.Request(
        URL_SESION,
        data=json.dumps({"rememberMe": True}).encode(),
        method="POST",
        headers={
            "Authorization": f"Basic {basico}",
            "Ubi-AppId": APP_ID,
            "User-Agent": USER_AGENT,
            "Content-Type": "application/json; charset=UTF-8",
        },
    )
    status, cuerpo = abrir(request)
    data = _json(status, cuerpo)

    if data.get("twoFactorAuthenticationTicket") and not data.get("ticket"):
        raise DosPasos(
            "La cuenta tiene verificación en dos pasos y la API no la acepta. "
            "Usa una cuenta secundaria de Ubisoft sin 2FA solo para consultar."
        )
    codigo = data.get("httpCode") or status
    if codigo == 401:
        raise CredencialesInvalidas("Ubisoft rechazó el email o la contraseña.")
    if codigo == 429:
        raise Limite(
            "Ubisoft bloqueó el login por demasiados intentos. Espera unos minutos."
        )
    if not data.get("ticket"):
        raise ErrorUbisoft(f"Ubisoft no devolvió una sesión ({_detalle(data, status)}).")
    return Sesion(
        ticket=data["ticket"],
        session_id=data.get("sessionId") or "",
        expiracion=data.get("expiration") or "",
    )


def _get(sesion: Sesion, url: str, abrir: Abridor) -> dict:
    request = urllib.request.Request(
        url,
        headers={
            "Authorization": f"Ubi_v1 t={sesion.ticket}",
            "Ubi-AppId": APP_ID,
            "Ubi-SessionId": sesion.session_id,
            "Ubi-LocaleCode": "en-us",
            "User-Agent": USER_AGENT,
            "expiration": sesion.expiracion,
        },
    )
    status, cuerpo = abrir(request)
    data = _json(status, cuerpo)
    _revisar(status, data)
    return data


# --------------------------------------------------------------------- perfil


def nombre_rango(rango_id) -> str | None:
    if not isinstance(rango_id, int) or rango_id < 0:
        return None
    return RANGOS[rango_id] if rango_id < len(RANGOS) else f"Rango {rango_id}"


def codigo_temporada(season_id) -> str | None:
    """34 -> Y9S2. Ubisoft numera las temporadas de corrido desde la Y1S1."""
    if not isinstance(season_id, int) or season_id < 1:
        return None
    return f"Y{(season_id - 1) // 4 + 1}S{(season_id - 1) % 4 + 1}"


def _entero(valor) -> int:
    try:
        return int(valor or 0)
    except (TypeError, ValueError):
        return 0


def _tablero(entrada: dict) -> dict:
    perfil = entrada.get("profile") or {}
    temporada = entrada.get("season_statistics") or {}
    resultados = temporada.get("match_outcomes") or {}

    bajas = _entero(temporada.get("kills"))
    muertes = _entero(temporada.get("deaths"))
    ganadas = _entero(resultados.get("wins"))
    perdidas = _entero(resultados.get("losses"))
    abandonos = _entero(resultados.get("abandons"))
    return {
        "temporada": codigo_temporada(perfil.get("season_id")),
        "rango": nombre_rango(perfil.get("rank")),
        "mmr": perfil.get("rank_points"),
        "rango_maximo": nombre_rango(perfil.get("max_rank")),
        "mmr_maximo": perfil.get("max_rank_points"),
        "top": perfil.get("top_rank_position") or None,
        "bajas": bajas,
        "muertes": muertes,
        # mismo criterio que `aggregates._ratio`: sin muertes no hay K/D
        "kd": round(bajas / muertes, 2) if muertes else None,
        "ganadas": ganadas,
        "perdidas": perdidas,
        "abandonos": abandonos,
        "partidas": ganadas + perdidas + abandonos,
        "winrate": round(100 * ganadas / (ganadas + perdidas), 1) if ganadas + perdidas else None,
    }


def tableros(data: dict) -> dict[str, dict]:
    """Un dict por playlist (`ranked`, `standard`, `casual`, ...) de la temporada actual."""
    familias = data.get("platform_families_full_profiles") or []
    if not familias:
        return {}
    salida: dict[str, dict] = {}
    for tablero in familias[0].get("board_ids_full_profiles") or []:
        perfiles = tablero.get("full_profiles") or []
        if tablero.get("board_id") and perfiles:
            salida[tablero["board_id"]] = _tablero(perfiles[0])
    return salida


def _opcional(consulta: Callable[[], dict], extraer: Callable[[dict], int | None]) -> int | None:
    """El nivel y las horas son adorno: si fallan, el perfil sale igual."""
    try:
        return extraer(consulta())
    except SesionVencida:
        raise
    except (ErrorUbisoft, AttributeError, IndexError, TypeError, ValueError):
        return None


def _horas(data: dict) -> int | None:
    stats = (data.get("profiles") or [{}])[0].get("stats") or {}
    segundos = (stats.get("PTotalTimePlayed") or {}).get("value")
    return round(int(segundos) / 3600) if segundos is not None else None


def perfil(sesion: Sesion, profile_id: str, *, abrir: Abridor = abrir_red) -> dict:
    """Rango, MMR, K/D y partidas de la temporada actual, mas nivel y horas."""
    pid = quote(profile_id.strip().lower(), safe="")
    completo = _get(sesion, URL_PERFILES.format(espacio=ESPACIO, pid=pid), abrir)
    por_tablero = tableros(completo)
    if not por_tablero:
        raise ErrorUbisoft("Ubisoft no devolvió datos de temporada para ese jugador.")

    nivel = _opcional(
        lambda: _get(sesion, URL_NIVEL.format(espacio=ESPACIO, pid=pid), abrir),
        lambda data: int(data["level"]) if data.get("level") is not None else None,
    )
    horas = _opcional(
        lambda: _get(sesion, URL_TIEMPO.format(espacio=ESPACIO, pid=pid), abrir),
        _horas,
    )
    return {"tableros": por_tablero, "nivel": nivel, "horas": horas}
