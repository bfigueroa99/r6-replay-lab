"""Lectura de la cabecera en texto plano de un .rec."""

from __future__ import annotations

import logging
from datetime import datetime

from .constants import (
    ATTACK,
    DEFENSE,
    GAME_MODES,
    MAPS,
    MATCH_TYPES,
    OPERATOR_SIDES,
    OPERATORS,
    RECRUIT,
    Y9S4,
)
from .errors import EndOfFile, InvalidFile
from .overrides import extra_map, extra_operator, record_unknown

log = logging.getLogger(__name__)

def read_header_magic(r) -> None:
    """Valida la firma y salta el esquema de versionado desconocido.

    Se avanza hasta el final de la segunda secuencia de 7 bytes 0x00, que es
    donde empiezan los pares clave/valor.
    """
    if r.bytes(7) != b"dissect":
        raise InvalidFile("falta la firma 'dissect'")
    n = 0
    t = 0
    while t != 2:
        b = r.bytes(1)[0]
        if b == 0x00:
            if n != 6:
                n += 1
            else:
                n = 0
                t += 1
        elif n > 0:
            n = 0


def _int(props: dict, key: str, default: int = 0) -> int:
    raw = props.get(key)
    if raw in (None, ""):
        return default
    try:
        return int(raw)
    except ValueError:
        log.debug("no se pudo convertir %s=%r a int", key, raw)
        return default


def read_header(r) -> dict:
    """Lee los pares clave/valor de la cabecera y arma el dict de metadata."""
    props: dict[str, str] = {}
    gm_settings: list[int] = []
    players: list[dict] = []
    current: dict = {}
    player_data = False

    while "teamscore1" not in props:
        try:
            k = r.header_string()
            v = r.header_string()
        except EndOfFile:
            break

        if k == "playerid":
            if player_data:
                players.append(current)
            player_data = True
            current = {}
        if k in ("playlistcategory", "id") and player_data:
            players.append(current)
            player_data = False

        if not player_data:
            if k == "gmsetting":
                gm_settings.append(_int({"v": v}, "v"))
            else:
                props[k] = v
            continue

        if k == "playerid":
            current["id"] = int(v)
        elif k == "playername":
            current["username"] = v
        elif k == "team":
            current["teamIndex"] = int(v)
        elif k == "heroname":
            current["heroName"] = _int({"v": v}, "v")
        elif k == "alliance":
            current["alliance"] = _int({"v": v}, "v")
        elif k == "roleimage":
            current["roleImage"] = _int({"v": v}, "v")
        elif k == "rolename":
            current["roleName"] = v
        elif k == "roleportrait":
            current["rolePortrait"] = _int({"v": v}, "v")
        else:
            props[k] = v

    for p in players:
        p.setdefault("username", "")
        p.setdefault("teamIndex", 0)
        p.setdefault("operator", 0)
        p.setdefault("spawn", "")
        p.setdefault("profileID", "")
        p.setdefault("dissectID", b"")
        p.setdefault("uiID", 0)

    code_version = _int(props, "code")
    map_id = _int(props, "worldid")
    match_type_id = _int(props, "matchtype")
    gamemode_id = _int(props, "gamemodeid")

    timestamp = None
    if props.get("datetime"):
        try:
            timestamp = datetime.strptime(props["datetime"], "%Y-%m-%d-%H-%M-%S")
        except ValueError:
            log.debug("datetime invalido: %r", props.get("datetime"))

    teams = [
        {
            "name": props.get("teamname0", ""),
            "startingScore": _int(props, "startingteamscore0"),
            "score": _int(props, "teamscore0"),
            "won": False,
            "winCondition": "",
            "role": "",
        },
        {
            "name": props.get("teamname1", ""),
            "startingScore": _int(props, "startingteamscore1"),
            "score": _int(props, "teamscore1"),
            "won": False,
            "winCondition": "",
            "role": "",
        },
    ]
    if code_version < Y9S4:
        for t in teams:
            t["startingScore"] = 0

    return {
        "gameVersion": props.get("version", ""),
        "codeVersion": code_version,
        "timestamp": timestamp,
        "matchType": match_type_id,
        "map": map_id,
        "site": "",
        "recordingPlayerID": int(props["recordingplayerid"]) if props.get("recordingplayerid") else 0,
        "recordingProfileID": props.get("recordingprofileid", ""),
        "additionalTags": props.get("additionaltags", ""),
        "gamemode": gamemode_id,
        "roundsPerMatch": _int(props, "roundspermatch"),
        "roundsPerMatchOvertime": _int(props, "roundspermatchovertime"),
        "roundNumber": _int(props, "roundnumber"),
        "overtimeRoundNumber": _int(props, "overtimeroundnumber"),
        "playlistCategory": _int(props, "playlistcategory"),
        "matchID": props.get("id", ""),
        "teams": teams,
        "players": players,
        "gmSettings": gm_settings,
        "raw": props,
    }


# --------------------------------------------------------------------- nombres


def operator_name(op_id: int) -> str:
    if not op_id:
        return ""
    name = OPERATORS.get(op_id) or extra_operator(op_id)
    if name:
        return name
    record_unknown("operators", op_id)
    return f"Unknown({op_id})"


def operator_label(player: dict) -> str:
    """Nombre del operador de un jugador, con la cabecera como respaldo.

    Cuando el ID es de una temporada mas nueva que la tabla de constantes, la
    propia cabecera del replay trae el nombre en `rolename` (ej. "NOOR"), asi
    que se usa eso antes de mostrar un "Unknown(...)".
    """
    op_id = player.get("operator", 0)
    if op_id and (OPERATORS.get(op_id) or extra_operator(op_id)):
        return operator_name(op_id)
    role = (player.get("roleName") or "").strip()
    if role:
        return role.title()
    return operator_name(op_id)


def _map_entry(map_id: int):
    entry = MAPS.get(map_id)
    if entry:
        return entry
    name = extra_map(map_id)
    if name:
        return (name.replace(" ", ""), name)
    record_unknown("maps", map_id)
    return None


def map_name(map_id: int) -> str:
    entry = _map_entry(map_id)
    return entry[1] if entry else f"Unknown({map_id})"


def map_slug(map_id: int) -> str:
    """Identificador estable del mapa: las variantes por temporada colapsan al base."""
    entry = _map_entry(map_id)
    if not entry:
        return f"unknown-{map_id}"
    return entry[1].lower().replace(" ", "-").replace(".", "")


def match_type_name(match_type_id: int) -> str:
    return MATCH_TYPES.get(match_type_id, f"Unknown({match_type_id})")


def gamemode_name(gamemode_id: int) -> str:
    return GAME_MODES.get(gamemode_id, f"Unknown({gamemode_id})")


def operator_side(op_id: int) -> str | None:
    """Lado del operador, o None si no lo conocemos (operador nuevo)."""
    if op_id == RECRUIT or not op_id:
        return None
    return OPERATOR_SIDES.get(OPERATORS.get(op_id, ""))


def derive_team_roles(r) -> None:
    """Deduce que equipo ataca y cual defiende a partir de los operadores.

    Los operadores desconocidos (temporada mas nueva que esta libreria) heredan
    el lado del equipo, resuelto por mayoria de los operadores si conocidos.
    """
    kept = []
    for p in r.players:
        if p.get("operator"):
            kept.append(p)
        else:
            log.debug("descarto a %s: operator id 0", p.get("username"))
    r.header["players"] = kept
    r.scoreboard = [
        {"id": p.get("dissectID", b""), "score": 0, "assists": 0, "assistsFromRound": 0}
        for p in kept
    ]

    votes = {0: {ATTACK: 0, DEFENSE: 0}, 1: {ATTACK: 0, DEFENSE: 0}}
    for p in kept:
        side = operator_side(p.get("operator", 0))
        if side:
            votes[p.get("teamIndex", 0)][side] += 1

    total = {
        side: votes[0][side] + votes[1][side] for side in (ATTACK, DEFENSE)
    }
    if not total[ATTACK] and not total[DEFENSE]:
        log.warning("no se pudo deducir el lado de los equipos (operadores desconocidos)")
        return

    # el equipo con mas votos de ataque ataca; el otro defiende
    score0 = votes[0][ATTACK] - votes[0][DEFENSE]
    score1 = votes[1][ATTACK] - votes[1][DEFENSE]
    atk_team = 0 if score0 >= score1 else 1
    r.teams[atk_team]["role"] = ATTACK
    r.teams[atk_team ^ 1]["role"] = DEFENSE

    # los operadores sin lado conocido quedan registrados para aprenderlos
    unknown: dict[str, str] = {}
    for p in kept:
        if operator_side(p.get("operator", 0)) is None and p.get("operator") != RECRUIT:
            name = operator_name(p["operator"])
            if name:
                unknown[name] = r.teams[p.get("teamIndex", 0)].get("role", "")
    if unknown:
        r.header.setdefault("inferredOperatorSides", {}).update(unknown)
