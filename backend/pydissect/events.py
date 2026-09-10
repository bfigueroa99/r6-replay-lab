"""Listeners de telemetria: jugadores, tiempo, kills, plants y scoreboard.

Cada funcion se dispara cuando el escaner encuentra su patron de bytes; el
offset del reader queda apuntando al byte siguiente al patron.
"""

from __future__ import annotations

import logging

from .constants import (
    ATTACK,
    BATTLEYE,
    BOMB,
    DEATH,
    DEFENSE,
    DEFUSED_BOMB,
    DEFUSER_DISABLE_COMPLETE,
    DEFUSER_DISABLE_START,
    DEFUSER_PLANT_COMPLETE,
    DEFUSER_PLANT_START,
    DISABLED_DEFUSER,
    KILL,
    KILLED_OPPONENTS,
    LOCATE_OBJECTIVE,
    OPERATOR_SWAP,
    OTHER,
    PLAYER_LEAVE,
    RECRUIT,
    TIME,
    Y7S2,
    Y7S4,
    Y9S1,
    Y9S1_UPDATE3,
    Y9S3,
    Y9S4,
)
from .header import derive_team_roles, operator_side

log = logging.getLogger(__name__)

ID_INDICATOR = b"\x33\xd8\x3d\x4f\x23"
ID_INDICATOR_LEGACY = b"\xe6\xf9\x7d\x86"
SPAWN_INDICATOR = b"\xaf\x98\x99\xca"
PROFILE_ID_INDICATOR = b"\x8a\x50\x9b\xd0"
UI_ID_INDICATOR = b"\x38\xdf\xee\x88"
OP_SWAP_INDICATOR = b"\x22\xa9\x26\x0b\xe4"
ROLE_SWAP_INDICATOR = b"\x40\xf2\x15\x04"
CURRENT_SITE_PATTERN = b"\xfc\xc6\xa8\x60\x01"
ACTIVITY_2 = b"\x00\x00\x00\x22\xe3\x09\x00\x79"
KILL_INDICATOR = b"\x22\xd9\x13\x3c\xba"


# ------------------------------------------------------------------ jugadores


def read_player(r) -> None:
    id_indicator = ID_INDICATOR_LEGACY if r.code_version <= Y7S2 else ID_INDICATOR
    r.players_read += 1
    try:
        _read_player(r, id_indicator)
    finally:
        if r.players_read == 10:
            derive_team_roles(r)


def _read_player(r, id_indicator: bytes) -> None:
    username = r.string()

    if r.code_version >= Y7S4:
        r.seek(ROLE_SWAP_INDICATOR)
        r.skip(8)
        # a veces el indicador aparece dos veces; 0x9D marca la repeticion
        if r.bytes(1)[0] == 0x9D:
            return
    else:
        r.seek(OP_SWAP_INDICATOR)

    op = r.uint64()
    if op == 0:
        log.debug("slot de jugador vacio")
        return
    if r.bytes(1)[0] != 0x22:
        log.debug("jugador invalido (op=%s)", op)
        return

    r.seek(id_indicator)
    dissect_id = r.bytes(4)
    r.seek(SPAWN_INDICATOR)
    spawn = r.string()
    if spawn == "":
        r.skip(10)
        if r.bytes(1) != b"\x1b":
            return

    team_index = 1 if r.players_read > 5 else 0

    ui_id = 0
    if r.code_version >= Y9S3:
        r.seek(UI_ID_INDICATOR)
        r.skip(13)
        ui_id = r.uint64()

    profile_id = ""
    player_id = 0
    if r.header.get("recordingProfileID"):
        r.seek(PROFILE_ID_INDICATOR)
        profile_id = r.string()
        r.skip(5)  # 22 ee d4 45 c8
        player_id = r.uint64()

    player = {
        "id": player_id,
        "profileID": profile_id,
        "username": username,
        "teamIndex": team_index,
        "operator": op,
        "spawn": spawn,
        "dissectID": dissect_id,
        "uiID": ui_id,
    }
    if op != RECRUIT and operator_side(op) == DEFENSE:
        # en defensa el spawn es el sitio, no una posicion de exterior
        player["spawn"] = r.header.get("site", "")

    for existing in r.players:
        same = existing.get("username") == username
        if not same and r.code_version >= 7601998:  # Y8S2
            same = bool(dissect_id) and existing.get("dissectID") == dissect_id
        elif not same:
            same = bool(player_id) and existing.get("id") == player_id
        if same:
            existing.update(
                {
                    "profileID": profile_id or existing.get("profileID", ""),
                    "username": username,
                    "operator": op,
                    "spawn": player["spawn"],
                    "dissectID": dissect_id,
                    "uiID": ui_id,
                }
            )
            return

    if username:
        r.players.append(player)


def read_atk_op_swap(r) -> None:
    op = r.uint64()

    if r.code_version < Y9S3:
        r.skip(5)
        dissect_id = r.bytes(4)
        i = r.player_index_by_id(dissect_id)
        if i > -1:
            r.players[i]["operator"] = op
            _append(
                r,
                {
                    "type": OPERATOR_SWAP,
                    "username": r.players[i].get("username", ""),
                    "operator": op,
                },
            )
        return

    r.skip(402)
    ui_id = r.uint64()
    for p in r.players:
        if p.get("uiID") and p["uiID"] == ui_id:
            p["operator"] = op
            _append(r, {"type": OPERATOR_SWAP, "username": p.get("username", ""), "operator": op})
            break


def read_spawn(r) -> None:
    """Lee el sitio de defensa (viene como 'Piso, Cuarto' con un <br/>)."""
    location = r.string()
    r.skip(150)
    pattern = r.bytes(5)
    if "<br/>" not in location:
        return
    if r.header.get("site") and pattern != CURRENT_SITE_PATTERN:
        return

    formatted = location.replace("<br/>", ", ", 1)
    for p in r.players:
        team_role = r.teams[p.get("teamIndex", 0)].get("role")
        op = p.get("operator", 0)
        def_role = op not in (0, RECRUIT) and operator_side(op) == DEFENSE
        if team_role == DEFENSE or def_role:
            p["spawn"] = formatted
    r.header["site"] = formatted


# ------------------------------------------------------------------ tiempo


def read_time(r) -> None:
    seconds = r.uint32()
    r.time = float(seconds)
    r.time_raw = f"{seconds // 60}:{seconds % 60:02d}"
    _track_clock(r, r.time)


def _track_clock(r, value: float) -> None:
    """Guarda el reloj mas alto y el ultimo no nulo.

    El reloj arranca en 0, baja 45->0 en la fase de preparacion y despues salta
    al tiempo de la fase de accion. El ultimo valor no nulo marca el final de
    la ronda (o el momento del plant: ahi el juego cambia al timer del defuser
    y deja de emitir el reloj principal).
    """
    if value > 0:
        r.clock_last = value
        if value > r.clock_max:
            r.clock_max = value


def read_y7_time(r) -> None:
    raw = r.string()
    parts = raw.split(":")
    if len(parts) == 1:
        r.time = float(parts[0])
        r.time_raw = parts[0]
        _track_clock(r, r.time)
        return
    r.time = float(int(parts[0]) * 60 + int(parts[1]))
    r.time_raw = raw
    _track_clock(r, r.time)


# ------------------------------------------------------------------ kill feed


def _append(r, update: dict) -> None:
    update.setdefault("time", r.time_raw)
    update.setdefault("timeInSeconds", r.time)
    r.match_feedback.append(update)


def read_match_feedback(r) -> None:
    if r.code_version >= Y9S1_UPDATE3:
        r.skip(38)
    elif r.code_version >= Y9S1:
        r.skip(9)
        if r.int() != 4:
            return
        r.skip(24)
    else:
        r.skip(1)
        r.seek(ACTIVITY_2)

    size = r.int()

    if size == 0:
        if r.bytes(5) != KILL_INDICATOR:
            return
        username = r.string()
        empty = not username
        r.skip(15)  # tipo de kill? aun sin descifrar
        target = r.string()

        if empty and target:
            _append(r, {"type": DEATH, "username": target})
            return
        if empty:
            return

        for existing in r.match_feedback:
            if (
                existing["type"] == KILL
                and existing.get("username") == username
                and existing.get("target") == target
            ):
                return  # duplicado

        r.skip(56)
        headshot = r.int() == 1
        update = {
            "type": KILL,
            "username": username,
            "target": target,
            "headshot": headshot,
        }
        if r.last_killer_from_scoreboard and r.last_killer_from_scoreboard != username:
            update["usernameFromScoreboard"] = r.last_killer_from_scoreboard
        _append(r, update)
        return

    if r.code_version >= Y9S1:
        return  # Y9S1 dejo de emitir los mensajes de texto

    msg = r.bytes(size).decode("utf-8", errors="replace")
    kind = OTHER
    if "bombs" in msg or "objective" in msg:
        kind = LOCATE_OBJECTIVE
    if "BattlEye" in msg:
        kind = BATTLEYE
    if "left" in msg:
        kind = PLAYER_LEAVE
    username = msg.split(" ")[0] if kind != OTHER else ""
    _append(
        r,
        {
            "type": kind,
            "username": username,
            "message": "" if kind != OTHER else msg,
        },
    )


def read_defuser_timer(r) -> None:
    timer = r.string()
    r.skip(34)
    dissect_id = r.bytes(4)
    i = r.player_index_by_id(dissect_id)

    kind = DEFUSER_DISABLE_START if r.planted else DEFUSER_PLANT_START
    if i > -1:
        _append(r, {"type": kind, "username": r.players[i].get("username", "")})
        r.last_defuser_player_index = i

    if not timer.startswith("0.00"):
        return

    if r.planted:
        kind = DEFUSER_DISABLE_COMPLETE
    else:
        kind = DEFUSER_PLANT_COMPLETE
        r.planted = True

    if 0 <= r.last_defuser_player_index < len(r.players):
        username = r.players[r.last_defuser_player_index].get("username", "")
        _append(r, {"type": kind, "username": username})


# ------------------------------------------------------------------ scoreboard


def read_scoreboard_kills(r) -> None:
    """Corrige kills que el feed registro como eliminaciones."""
    r.uint32()
    r.skip(30)
    dissect_id = r.bytes(4)
    i = r.player_index_by_id(dissect_id)
    if i > -1:
        r.last_killer_from_scoreboard = r.players[i].get("username", "")


def read_scoreboard_assists(r) -> None:
    assists = r.uint32()
    if assists == 0:
        return
    r.skip(30)
    dissect_id = r.bytes(4)
    i = r.player_index_by_id(dissect_id)
    if 0 <= i < len(r.scoreboard):
        r.scoreboard[i]["assists"] = assists
        r.scoreboard[i]["assistsFromRound"] += 1


def read_scoreboard_score(r) -> None:
    score = r.uint32()
    if score == 0:
        return
    r.skip(13)
    dissect_id = r.bytes(4)
    i = r.player_index_by_id(dissect_id)
    if 0 <= i < len(r.scoreboard):
        r.scoreboard[i]["score"] = score


# ------------------------------------------------------------------ fin de ronda


def round_end(r) -> None:
    """Determina quien gano la ronda y por que condicion."""
    planter = -1
    deaths: dict[int, int] = {}
    sizes: dict[int, int] = {}
    roles: dict[int, str] = {}

    for p in r.players:
        idx = p.get("teamIndex", 0)
        sizes[idx] = sizes.get(idx, 0) + 1
        roles[idx] = r.teams[idx].get("role", "")

    if r.code_version >= Y9S4:
        team0_won = r.teams[0]["startingScore"] < r.teams[0]["score"]
        r.teams[0]["won"] = team0_won
        r.teams[1]["won"] = not team0_won

    for u in r.match_feedback:
        kind = u["type"]
        if kind == KILL:
            i = r.player_index_by_username(u.get("target", ""))
            if i > -1:
                t = r.players[i].get("teamIndex", 0)
                deaths[t] = deaths.get(t, 0) + 1
            if u.get("usernameFromScoreboard"):
                u["username"] = u["usernameFromScoreboard"]
        elif kind == DEATH:
            i = r.player_index_by_username(u.get("username", ""))
            if i > -1:
                t = r.players[i].get("teamIndex", 0)
                deaths[t] = deaths.get(t, 0) + 1
        elif kind == DEFUSER_PLANT_COMPLETE:
            planter = r.player_index_by_username(u.get("username", ""))
        elif kind == DEFUSER_DISABLE_COMPLETE:
            i = r.player_index_by_username(u.get("username", ""))
            if i > -1:
                t = r.players[i].get("teamIndex", 0)
                r.teams[t]["won"] = True
                r.teams[t]["winCondition"] = DISABLED_DEFUSER
                return

    if planter > -1:
        t = r.players[planter].get("teamIndex", 0)
        r.teams[t]["won"] = True
        r.teams[t]["winCondition"] = DEFUSED_BOMB
        return

    if r.code_version >= Y9S4:
        # desde Y9S4 la cabecera ya dice quien gano; la condicion queda abierta
        if r.header.get("gamemode") == BOMB and not any(t["winCondition"] for t in r.teams):
            winner = 0 if r.teams[0]["won"] else 1
            loser = winner ^ 1
            if deaths.get(loser, 0) >= sizes.get(loser, 5):
                r.teams[winner]["winCondition"] = KILLED_OPPONENTS
            else:
                r.teams[winner]["winCondition"] = TIME
        return

    if deaths.get(0, 0) == sizes.get(0, 0):
        if planter > -1 and roles.get(0) == ATTACK:
            return
        r.teams[1]["won"] = True
        r.teams[1]["winCondition"] = KILLED_OPPONENTS
        return
    if deaths.get(1, 0) == sizes.get(1, 0):
        if planter > -1 and roles.get(1) == ATTACK:
            return
        r.teams[0]["won"] = True
        r.teams[0]["winCondition"] = KILLED_OPPONENTS
        return

    i = 1 if roles.get(1) == DEFENSE else 0
    r.teams[i]["won"] = True
    r.teams[i]["winCondition"] = TIME
