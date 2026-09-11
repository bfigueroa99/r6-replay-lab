"""Resumen en palabras de lo que paso en una ronda.

Toma el mismo dict que la API ya arma para el detalle de la partida y devuelve
dos o tres frases. **Todo sale de los eventos**: si un dato no esta, la frase no
se escribe. Nunca se rellena con suposiciones, que es justamente lo que haria
inutil un resumen automatico.

No se guarda en la base: es texto derivado y cambia si cambian las metricas.
"""

from __future__ import annotations

KILL = "Kill"
DEATH = "Death"
TRADE_WINDOW = 3.0


def _segundos(valor) -> str:
    return f"{round(valor)}s"


def _mi_equipo(players: list[dict]) -> int | None:
    for p in players:
        if p.get("is_me"):
            return p.get("team_index")
    return None


def _equipos(players: list[dict]) -> dict[str, int]:
    return {p["username"]: p.get("team_index", 0) for p in players}


def _bajas(events: list[dict]) -> list[dict]:
    return [e for e in events if e.get("kind") in (KILL, DEATH)]


def _apertura(rnd: dict, players: list[dict], events: list[dict]) -> str | None:
    """Quien se llevo el primer duelo, y si alguien lo vengo."""
    bajas = _bajas(events)
    if not bajas:
        return None

    primera = bajas[0]
    equipos = _equipos(players)
    mio = _mi_equipo(players)
    yo = next((p["username"] for p in players if p.get("is_me")), None)
    cuando = _segundos(primera.get("elapsed") or 0)

    victima = primera.get("target") if primera.get("kind") == KILL else primera.get("actor")
    asesino = primera.get("actor") if primera.get("kind") == KILL else None
    equipo_victima = equipos.get(victima)

    if equipo_victima is None or mio is None:
        return None

    perdio_mi_equipo = equipo_victima == mio
    if not asesino:
        # muerte sin asesino registrado: no inventamos quien fue
        quien = "Moriste" if victima == yo else f"Murio {victima}"
        lado = "tu equipo" if perdio_mi_equipo else "el rival"
        return f"{quien} a los {cuando} sin asesino registrado, y {lado} arranco con uno menos."

    if victima == yo:
        frase = f"A los {cuando} perdiste el primer duelo: te mato {asesino}."
    elif perdio_mi_equipo:
        frase = f"A los {cuando} tu equipo perdio el primer duelo: {asesino} mato a {victima}."
    else:
        frase = f"A los {cuando} tu equipo abrio la ronda: {asesino} mato a {victima}."

    return frase + _trade_de_la_apertura(primera, bajas, perdio_mi_equipo)


def _trade_de_la_apertura(primera: dict, bajas: list[dict], perdio_mi_equipo: bool) -> str:
    """Si la apertura se vengo, con cuanto margen.

    La frase cambia segun quien perdio el duelo: que nadie vengue una muerte
    propia es un problema, que el rival no vengue la suya es una ventaja.
    """
    if not primera.get("traded"):
        return " Nadie la vengo." if perdio_mi_equipo else " El rival no la vengo."

    asesino = primera.get("actor")
    for evento in bajas:
        if evento is primera or evento.get("kind") != KILL:
            continue
        if evento.get("target") != asesino:
            continue
        margen = (primera.get("clock") or 0) - (evento.get("clock") or 0)
        if 0 <= margen <= TRADE_WINDOW:
            quien = evento.get("actor") if perdio_mi_equipo else "El rival"
            return f" {quien} la vengo {_segundos(margen)} despues."
    return " Se vengo enseguida."


def _desventaja(rnd: dict, players: list[dict], events: list[dict]) -> str | None:
    """Cuantos segundos se jugaron con el equipo propio en inferioridad.

    Se recorre el feed llevando la cuenta de vivos por equipo. Es el numero que
    explica por que se pierde una ronda sin que nadie juegue mal despues.
    """
    mio = _mi_equipo(players)
    if mio is None:
        return None

    vivos: dict[int, int] = {}
    for p in players:
        vivos[p.get("team_index", 0)] = vivos.get(p.get("team_index", 0), 0) + 1
    if len(vivos) < 2:
        return None

    equipos = _equipos(players)
    fin = float(rnd.get("clock_end") or 0)
    reloj = float(rnd.get("clock_start") or 0)
    if not reloj:
        return None

    segundos_abajo = 0.0
    for evento in _bajas(events):
        siguiente = float(evento.get("clock") or 0)
        rival = 1 - mio if mio in (0, 1) else None
        if vivos.get(mio, 0) < vivos.get(rival, 0):
            segundos_abajo += max(reloj - siguiente, 0)
        reloj = siguiente

        victima = evento.get("target") if evento.get("kind") == KILL else evento.get("actor")
        equipo = equipos.get(victima)
        if equipo is not None:
            vivos[equipo] = max(vivos[equipo] - 1, 0)

    rival = 1 - mio if mio in (0, 1) else None
    if rival is not None and vivos.get(mio, 0) < vivos.get(rival, 0):
        segundos_abajo += max(reloj - fin, 0)

    if segundos_abajo < 5:
        return None
    duracion = max(float(rnd.get("duration") or 0), 1)
    return (
        f"De los {_segundos(duracion)} de accion, {_segundos(segundos_abajo)} se jugaron "
        "con tu equipo en inferioridad."
    )


def _mi_ronda(players: list[dict]) -> str | None:
    """Que hiciste tu, en una frase."""
    yo = next((p for p in players if p.get("is_me")), None)
    if not yo:
        return None

    partes = []
    kills = yo.get("kills") or 0
    if kills:
        partes.append(f"{kills} baja" if kills == 1 else f"{kills} bajas")
    if yo.get("trade_kills"):
        partes.append(f"{yo['trade_kills']} de trade")
    if yo.get("one_vx"):
        partes.append(f"cerraste un 1v{yo['one_vx']}")

    if yo.get("survived"):
        cola = "y sobreviviste" if partes else "Sobreviviste la ronda"
    elif yo.get("death_elapsed") is not None:
        cuando = _segundos(yo["death_elapsed"])
        trade = "sin que nadie te tradeara" if yo.get("untraded_death") else "y te tradearon"
        cola = f"y moriste a los {cuando} {trade}"
        if not partes:
            cola = f"Moriste a los {cuando} {trade}"
    else:
        cola = "y moriste" if partes else "Moriste en la ronda"

    if partes:
        return "Hiciste " + ", ".join(partes) + " " + cola + "."
    return cola + "."


def _cierre(rnd: dict) -> str | None:
    """Como termino, sin afirmar lo que el replay no dice."""
    if rnd.get("win_condition") == "KilledOpponents":
        return "La ronda se cerro por eliminacion."
    if not rnd.get("win_condition_certain"):
        texto = "El replay de esta temporada no expone como se cerro la ronda"
        if rnd.get("possible_plant"):
            texto += f", pero el reloj paro en {_segundos(rnd.get('clock_end') or 0)}: plant probable"
        return texto + "."
    return None


def describe_round(rnd: dict) -> list[str]:
    """Las frases de la ronda, en orden. Puede devolver una lista vacia."""
    players = rnd.get("players") or []
    events = rnd.get("events") or []
    frases = [
        _apertura(rnd, players, events),
        _desventaja(rnd, players, events),
        _mi_ronda(players),
        _cierre(rnd),
    ]
    return [f for f in frases if f]
