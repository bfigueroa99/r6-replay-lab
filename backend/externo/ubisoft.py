"""Cliente minimo de la API de Ubisoft: rango, MMR y las tablas de stats.cc.

Es la misma API que leen stats.cc y R6 Tracker, sin pasar por ellos: el rango
sale de `full_profiles`, y las pestanas de operadores, mapas, armas y
temporadas de stats.cc, de `playerstats`. No es una API publica documentada: el
AppId y los endpoints salen de siegeapi (github.com/CNDRD/siegeapi), que los
sigue temporada a temporada. Si Ubisoft los cambia, esto falla con un error que dice que paso;
nunca devuelve numeros inventados.

Solo usa la libreria estandar. `abrir` se pasa como argumento para que los
tests corran sin red: recibe un `urllib.request.Request` y devuelve
`(status, cuerpo)`.
"""

from __future__ import annotations

import base64
import json
import re
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
#: Pide el userId; en PC es el mismo valor que el profileID del replay, que es
#: justo lo que hace siegeapi (`player_uid if PC`). Sin fechas, Ubisoft elige la
#: ventana y la devuelve en `startDate` / `endDate`.
URL_ESTADISTICAS = (
    "https://prod.datadev.ubisoft.com/v1/profiles/{pid}/playerstats"
    "?spaceId={espacio}&view=current&aggregation={agregacion}"
    "&gameMode=all,ranked,casual,unranked&platformGroup=PC&teamRole=all,Attacker,Defender"
)

#: El historial por temporada vive en el mismo servicio pero bajo `/users/`; las
#: temporadas no tienen ventana de fechas, cada fila es una temporada entera.
URL_TEMPORADAS = (
    "https://prod.datadev.ubisoft.com/v1/users/{pid}/playerstats"
    "?spaceId={espacio}&view=seasonal&aggregation=summary"
    "&gameMode=all,ranked,casual,unranked&platformGroup=PC&teamRole=all"
)

TIMEOUT = 15
#: Un ticket que vence en menos de esto se descarta: la consulta son ocho
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


# ----------------------------------------------------- operadores y mapas

#: Los lados con el nombre que usa el replay, para poder cruzar las dos fuentes.
LADOS = {"Attacker": "Attack", "Defender": "Defense"}


def _modos(data: dict) -> dict:
    """Los `gameModes` de una respuesta de `playerstats`, sea cual sea su envoltorio.

    siegeapi los lee en `platforms` al primer nivel, pero el endpoint hermano de
    resumenes por temporada los anida en `profileData.<id>`. Se aceptan las dos
    formas para no romper si Ubisoft unifica una con la otra.
    """
    plataformas = data.get("platforms")
    if not isinstance(plataformas, dict):
        perfiles = data.get("profileData")
        perfil_ = next(iter(perfiles.values()), None) if isinstance(perfiles, dict) else None
        plataformas = perfil_.get("platforms") if isinstance(perfil_, dict) else None
    if not isinstance(plataformas, dict) or not plataformas:
        return {}
    plataforma = plataformas.get("PC") or next(iter(plataformas.values()))
    modos = plataforma.get("gameModes") if isinstance(plataforma, dict) else None
    return modos if isinstance(modos, dict) else {}


def _roles(modo) -> dict[str, list[dict]]:
    roles = modo.get("teamRoles") if isinstance(modo, dict) else None
    if not isinstance(roles, dict):
        return {}
    return {
        rol: [fila for fila in filas if isinstance(fila, dict)]
        for rol, filas in roles.items()
        if isinstance(filas, list)
    }


def _numeros(stats: dict) -> dict:
    """Los numeros de una fila, calculados desde los conteos y no desde los ratios.

    Ubisoft tambien manda `killDeathRatio` y compania ya hechos, pero
    recalcularlos con la misma formula que usan los replays es lo que hace
    comparables las dos columnas de la tabla.
    """
    rondas = _entero(stats.get("roundsPlayed"))
    ganadas = _entero(stats.get("roundsWon"))
    bajas = _entero(stats.get("kills"))
    muertes = _entero(stats.get("death"))
    headshots = _entero(stats.get("headshots"))
    return {
        "partidas": _entero(stats.get("matchesPlayed")),
        "rondas": rondas,
        "winrate": round(100 * ganadas / rondas, 1) if rondas else None,
        "bajas": bajas,
        "muertes": muertes,
        "kd": round(bajas / muertes, 2) if muertes else None,
        "kpr": round(bajas / rondas, 2) if rondas else None,
        "hs_pct": round(100 * headshots / bajas, 1) if bajas else None,
    }


def _nombre(stats: dict) -> str:
    return str(stats.get("statsDetail") or "").strip()


def _nombre_mapa(stats: dict) -> str:
    nombre = _nombre(stats)
    # vienen en mayusculas ("KAFE DOSTOYEVSKY"); los operadores no, y "IQ" no se toca
    return nombre.title() if nombre.isupper() else nombre


def operadores(data: dict) -> dict[str, list[dict]]:
    """Una lista por playlist con cada operador y su lado, solo los que jugo."""
    salida: dict[str, list[dict]] = {}
    for modo, contenido in _modos(data).items():
        roles = _roles(contenido)
        filas = [
            {"operador": _nombre(stats), "lado": lado, **_numeros(stats)}
            for rol, lado in LADOS.items()
            for stats in roles.get(rol, [])
            if _nombre(stats) and _entero(stats.get("roundsPlayed")) > 0
        ]
        if filas:
            salida[modo] = filas
    return salida


def mapas(data: dict) -> dict[str, list[dict]]:
    """Una lista por playlist con cada mapa, y el winrate de rondas de cada lado."""
    salida: dict[str, list[dict]] = {}
    for modo, contenido in _modos(data).items():
        roles = _roles(contenido)
        por_lado = {
            lado: {_nombre_mapa(stats): _numeros(stats) for stats in roles.get(rol, [])}
            for rol, lado in LADOS.items()
        }
        filas = []
        for stats in roles.get("all", []):
            nombre = _nombre_mapa(stats)
            if not nombre or _entero(stats.get("roundsPlayed")) <= 0:
                continue
            fila = {"mapa": nombre, **_numeros(stats)}
            for lado, indice in por_lado.items():
                fila[f"winrate_{lado.lower()}"] = (indice.get(nombre) or {}).get("winrate")
            filas.append(fila)
        if filas:
            salida[modo] = filas
    return salida


#: Las dos ranuras, con el nombre que ve el usuario.
RANURAS = {"primaryWeapons": "Principal", "secondaryWeapons": "Secundaria"}


def _numeros_arma(stats: dict) -> dict:
    """Como `_numeros`, pero un arma no tiene muertes: no hay K/D que calcular."""
    rondas = _entero(stats.get("roundsPlayed"))
    ganadas = _entero(stats.get("roundsWon"))
    bajas = _entero(stats.get("kills"))
    headshots = _entero(stats.get("headshots"))
    return {
        "rondas": rondas,
        "winrate": round(100 * ganadas / rondas, 1) if rondas else None,
        "bajas": bajas,
        "kpr": round(bajas / rondas, 2) if rondas else None,
        "hs_pct": round(100 * headshots / bajas, 1) if bajas else None,
    }


def _lista(contenedor, clave: str) -> list[dict]:
    valor = contenedor.get(clave) if isinstance(contenedor, dict) else None
    return [fila for fila in valor if isinstance(fila, dict)] if isinstance(valor, list) else []


def _filas_armas(ranuras: dict) -> list[dict]:
    filas = []
    for clave, ranura in RANURAS.items():
        # siegeapi lee solo el primer tipo de cada ranura; cada tipo (fusil,
        # subfusil, escopeta...) es una lista aparte, asi que se recorren todos
        for tipo in _lista(ranuras.get(clave), "weaponTypes"):
            for stats in _lista(tipo, "weapons"):
                nombre = str(stats.get("weaponName") or "").strip()
                if nombre and _entero(stats.get("roundsPlayed")) > 0:
                    filas.append(
                        {
                            "arma": nombre,
                            "ranura": ranura,
                            "tipo": str(tipo.get("weaponType") or "").strip() or None,
                            **_numeros_arma(stats),
                        }
                    )
    return filas


def armas(data: dict) -> dict[str, list[dict]]:
    """Una lista por playlist con cada arma usada, de los dos lados juntos."""
    salida: dict[str, list[dict]] = {}
    for modo, contenido in _modos(data).items():
        roles = contenido.get("teamRoles") if isinstance(contenido, dict) else None
        todos = roles.get("all") if isinstance(roles, dict) else None
        ranuras = todos.get("weaponSlots") if isinstance(todos, dict) else None
        filas = _filas_armas(ranuras) if isinstance(ranuras, dict) else []
        if filas:
            salida[modo] = filas
    return salida


_CODIGO = re.compile(r"Y\d+S\d+")


def _codigo(stats: dict) -> str | None:
    """`seasonYear` "Y9" + `seasonNumber` "S2" -> Y9S2; con numeros sueltos tambien."""
    anio = str(stats.get("seasonYear") or "").strip().upper()
    numero = str(stats.get("seasonNumber") or "").strip().upper()
    anio = f"Y{anio}" if anio.isdigit() else anio
    numero = f"S{numero}" if numero.isdigit() else numero
    codigo = anio + numero
    return codigo if _CODIGO.fullmatch(codigo) else None


def orden_temporada(codigo: str) -> tuple[int, int]:
    """Y10S1 va despues de Y9S4: el orden alfabetico las pone al reves."""
    anio, _, numero = codigo[1:].partition("S")
    return int(anio), int(numero)


def temporadas(data: dict) -> dict[str, list[dict]]:
    """Una lista por playlist con cada temporada jugada, la mas nueva primero."""
    salida: dict[str, list[dict]] = {}
    for modo, contenido in _modos(data).items():
        filas = {}
        for stats in _roles(contenido).get("all", []):
            codigo = _codigo(stats)
            if not codigo or _entero(stats.get("matchesPlayed")) <= 0:
                continue
            ganadas = _entero(stats.get("matchesWon"))
            perdidas = _entero(stats.get("matchesLost"))
            filas[codigo] = {
                "temporada": codigo,
                **_numeros(stats),
                "partidas_ganadas": ganadas,
                "partidas_perdidas": perdidas,
                "winrate_partidas": (
                    round(100 * ganadas / (ganadas + perdidas), 1) if ganadas + perdidas else None
                ),
            }
        if filas:
            salida[modo] = sorted(
                filas.values(), key=lambda f: orden_temporada(f["temporada"]), reverse=True
            )
    return salida


def _fecha(valor) -> str | None:
    """20260601 -> 2026-06-01; cualquier otra cosa no se adivina."""
    texto = str(valor or "")
    if len(texto) != 8 or not texto.isdigit():
        return None
    return f"{texto[:4]}-{texto[4:6]}-{texto[6:]}"


def _periodo(*respuestas: dict) -> tuple[str | None, str | None]:
    """El primer periodo completo; mezclar el inicio de una con el fin de otra no vale."""
    for respuesta in respuestas:
        desde, hasta = _fecha(respuesta.get("startDate")), _fecha(respuesta.get("endDate"))
        if desde and hasta:
            return desde, hasta
    return None, None


def resumir(de_operadores: dict, de_mapas: dict, de_armas: dict) -> dict:
    """Lo que se guarda a partir de las tres respuestas de `playerstats` del periodo."""
    desde, hasta = _periodo(de_operadores, de_mapas, de_armas)
    return {
        "desde": desde,
        "hasta": hasta,
        "operadores": operadores(de_operadores),
        "mapas": mapas(de_mapas),
        "armas": armas(de_armas),
    }


def estadisticas(sesion: Sesion, profile_id: str, *, abrir: Abridor = abrir_red) -> dict:
    """Lo que stats.cc muestra en sus pestanas de operadores, mapas y armas."""
    pid = quote(profile_id.strip().lower(), safe="")

    def pedir(agregacion: str) -> dict:
        url = URL_ESTADISTICAS.format(pid=pid, espacio=ESPACIO, agregacion=agregacion)
        return _get(sesion, url, abrir)

    return resumir(pedir("operators"), pedir("maps"), pedir("weapons"))


def historial(sesion: Sesion, profile_id: str, *, abrir: Abridor = abrir_red) -> dict:
    """Lo que stats.cc muestra en su pestana de temporadas, sin el rango de cada una."""
    pid = quote(profile_id.strip().lower(), safe="")
    data = _get(sesion, URL_TEMPORADAS.format(pid=pid, espacio=ESPACIO), abrir)
    return {"temporadas": temporadas(data)}


def _seccion(consulta: Callable[[], dict], nombre: str) -> dict:
    """Una seccion de `playerstats`, o el motivo por el que no vino.

    No tumba el perfil: el rango ya llego, y perderlo porque fallo un endpoint
    distinto seria peor que mostrarlo sin tablas. Tampoco se calla, como el
    nivel: una tabla que no aparece sin explicacion parece un bug. Cada seccion
    falla por su cuenta porque el historial vive en otra ruta del servicio.
    Un 401 aca no es un ticket vencido (`full_profiles` acaba de aceptarlo), asi
    que tampoco vale la pena loguear de nuevo.
    """
    try:
        return consulta()
    except SesionVencida:
        return {"error": f"Ubisoft rechazó la consulta de {nombre} (HTTP 401)."}
    except ErrorUbisoft as exc:
        return {"error": f"Ubisoft no devolvió {nombre}: {exc}"}


def perfil(sesion: Sesion, profile_id: str, *, abrir: Abridor = abrir_red) -> dict:
    """Rango y temporada actual, nivel, horas y las tablas de stats.cc."""
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
    return {
        "tableros": por_tablero,
        "nivel": nivel,
        "horas": horas,
        "estadisticas": _seccion(
            lambda: estadisticas(sesion, profile_id, abrir=abrir), "operadores, mapas y armas"
        ),
        "historial": _seccion(
            lambda: historial(sesion, profile_id, abrir=abrir), "el historial por temporada"
        ),
    }
