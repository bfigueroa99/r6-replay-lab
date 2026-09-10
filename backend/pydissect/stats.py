"""Estadisticas por ronda y por partida, equivalentes a las de r6-dissect."""

from __future__ import annotations

from .constants import DEATH, KILL, PLAYER_LEAVE
from .header import operator_label


def kills_and_deaths(reader) -> list[dict]:
    return [u for u in reader.match_feedback if u["type"] in (KILL, DEATH)]


def opening_kill(reader) -> dict | None:
    for u in reader.match_feedback:
        if u["type"] == KILL:
            return u
    return None


def opening_death(reader) -> dict | None:
    for u in reader.match_feedback:
        if u["type"] in (KILL, DEATH):
            return u
    return None


def trades(reader, threshold: float = 3.0) -> list[tuple[dict, dict]]:
    """Pares de kills consecutivas que se consideran trade.

    Misma heuristica que r6-dissect: la segunda kill involucra a los mismos dos
    jugadores que la primera y ocurre dentro de `threshold` segundos.
    """
    out: list[tuple[dict, dict]] = []
    previous: dict = {}
    for u in reader.match_feedback:
        same_players = previous.get("target") == u.get("username") or previous.get(
            "username"
        ) == u.get("target")
        within = (previous.get("timeInSeconds", 0.0) - u.get("timeInSeconds", 0.0)) <= threshold
        if u["type"] == KILL and same_players and within and previous:
            out.append((previous, u))
        previous = u
    return out


def num_players(reader, team_index: int) -> int:
    return sum(1 for p in reader.players if p.get("teamIndex") == team_index)


def headshot_percentage(headshots: int, kills: int) -> float:
    return (headshots / kills * 100) if kills else 0.0


def player_round_stats(reader) -> list[dict]:
    """kills / muertes / asistencias / hs% / 1vX por jugador en la ronda."""
    stats: list[dict] = []
    index: dict[str, int] = {}
    winning_team = 1 if reader.teams[1].get("won") else 0

    for i, p in enumerate(reader.players):
        sb = reader.scoreboard[i] if i < len(reader.scoreboard) else {}
        stats.append(
            {
                "username": p.get("username", ""),
                "teamIndex": p.get("teamIndex", 0),
                "operator": operator_label(p),
                "operatorID": p.get("operator", 0),
                "spawn": p.get("spawn", ""),
                "score": int(sb.get("score", 0)),
                "assists": int(sb.get("assistsFromRound", 0)),
                "kills": 0,
                "died": False,
                "headshots": 0,
                "headshotPercentage": 0.0,
                "1vX": 0,
            }
        )
        index[p.get("username", "")] = i

    last_death = -1
    for u in reader.match_feedback:
        i = index.get(u.get("username", ""), -1)
        if u["type"] == KILL:
            if i > -1:
                stats[i]["kills"] += 1
                if u.get("headshot"):
                    stats[i]["headshots"] += 1
                stats[i]["headshotPercentage"] = headshot_percentage(
                    stats[i]["headshots"], stats[i]["kills"]
                )
            t = index.get(u.get("target", ""), -1)
            if t > -1:
                stats[t]["died"] = True
                last_death = t
        elif u["type"] == DEATH and i > -1:
            stats[i]["died"] = True
            last_death = i

    # --- 1vX del ultimo sobreviviente del equipo ganador
    winners_alive = [
        i
        for i, p in enumerate(reader.players)
        if p.get("teamIndex") == winning_team and not stats[i]["died"]
    ]
    last_death_was_winner = (
        0 <= last_death < len(reader.players)
        and reader.players[last_death].get("teamIndex") == winning_team
    )

    last_standing = -1
    if len(winners_alive) == 1:
        last_standing = winners_alive[0]
    elif not winners_alive and last_death_was_winner:
        last_standing = last_death

    if last_standing > -1:
        username = stats[last_standing]["username"]
        team_left = num_players(reader, winning_team)
        one_vx = 0
        for u in reader.match_feedback:
            kind = u["type"]
            if kind == KILL:
                t = index.get(u.get("target", ""), -1)
                if t > -1 and stats[t]["teamIndex"] == winning_team:
                    team_left -= 1
            elif kind in (DEATH, PLAYER_LEAVE):
                i = index.get(u.get("username", ""), -1)
                if i > -1 and stats[i]["teamIndex"] == winning_team:
                    team_left -= 1
            if u.get("username") != username:
                continue
            if kind == KILL and team_left < 2:
                one_vx += 1
        for s in stats:
            if s["teamIndex"] != winning_team and not s["died"]:
                one_vx += 1
        stats[last_standing]["1vX"] = one_vx

    return stats


def player_match_stats(rounds: list[list[dict]]) -> list[dict]:
    """Agrega las stats por ronda de una partida completa."""
    stats: list[dict] = []
    index: dict[str, int] = {}
    for round_stats in rounds:
        for p in round_stats:
            name = p["username"]
            if name not in index:
                index[name] = len(stats)
                stats.append(
                    {
                        "username": name,
                        "teamIndex": p["teamIndex"],
                        "rounds": 0,
                        "kills": 0,
                        "deaths": 0,
                        "assists": 0,
                        "headshots": 0,
                        "headshotPercentage": 0.0,
                    }
                )
            i = index[name]
            stats[i]["rounds"] += 1
            stats[i]["kills"] += p["kills"]
            stats[i]["deaths"] += 1 if p["died"] else 0
            stats[i]["assists"] += p["assists"]
            stats[i]["headshots"] += p["headshots"]
            stats[i]["headshotPercentage"] = headshot_percentage(
                stats[i]["headshots"], stats[i]["kills"]
            )
    return stats
