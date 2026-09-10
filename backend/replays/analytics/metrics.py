"""Metricas derivadas de una ronda parseada.

Toma el dict que devuelve `pydissect.round_to_dict` y calcula todo lo que el
formato .rec no entrega masticado: duelos de apertura, trades, muertes sin
trade, momento de la muerte, KST y la condicion de victoria.

Definiciones (documentadas a proposito, para que los numeros se puedan auditar)
-------------------------------------------------------------------------------
opening_kill   la primera baja de la ronda la hizo este jugador
opening_death  este jugador fue la primera baja de la ronda
entry_kill     la primera baja de su equipo la hizo este jugador
trade_kills    mato al asesino de un compañero dentro de TRADE_WINDOW segundos
was_traded     un compañero vengo su muerte dentro de TRADE_WINDOW segundos
untraded_death murio y nadie lo vengo (la muerte mas caras del juego)
death_elapsed  segundos jugados de la fase de accion hasta su muerte
kst            aporto en la ronda: mato, sobrevivio o su muerte fue tradeada
"""

from __future__ import annotations

TRADE_WINDOW = 3.0  # segundos, igual que r6-dissect

KILL = "Kill"
DEATH = "Death"
ATTACK = "Attack"
DEFENSE = "Defense"

BOMB_MODE = "Bomb"


def _clock_start(round_data: dict, events: list[dict]) -> float:
    start = float(round_data.get("clockStart") or 0)
    if start:
        return start
    # fallback: el reloj mas alto que aparezca en los eventos
    return max((e["clock"] for e in events), default=0.0)


def analyse_round(round_data: dict) -> dict:
    """Devuelve eventos anotados + metricas por jugador para una ronda."""
    players = round_data.get("players", [])
    teams = round_data.get("teams", [{}, {}])
    team_of = {p["username"]: p.get("teamIndex", 0) for p in players}

    roles = {i: (t.get("role") or "") for i, t in enumerate(teams)}
    if not roles.get(0) and not roles.get(1):
        roles = {0: "", 1: ""}

    # ---------------------------------------------------------------- eventos
    events: list[dict] = []
    for i, u in enumerate(round_data.get("matchFeedback", [])):
        kind = u["type"]["name"] if isinstance(u.get("type"), dict) else str(u.get("type"))
        events.append(
            {
                "order": i,
                "kind": kind,
                "clock": float(u.get("timeInSeconds") or 0),
                "clock_raw": u.get("time") or "",
                "actor": u.get("username") or "",
                "target": u.get("target") or "",
                "headshot": u.get("headshot"),
                "operator": (u.get("operator") or {}).get("name", "") if u.get("operator") else "",
                "message": u.get("message") or "",
                "traded": False,
            }
        )

    clock_start = _clock_start(round_data, events)
    for e in events:
        e["elapsed"] = round(max(clock_start - e["clock"], 0.0), 2) if e["clock"] else 0.0

    kill_events = [e for e in events if e["kind"] == KILL]
    death_events = [e for e in events if e["kind"] in (KILL, DEATH)]

    # ---------------------------------------------------------------- base
    stats = {}
    for s in round_data.get("stats", []):
        stats[s["username"]] = s

    metrics: dict[str, dict] = {}
    for p in players:
        name = p["username"]
        s = stats.get(name, {})
        team = p.get("teamIndex", 0)
        metrics[name] = {
            "username": name,
            "team_index": team,
            "side": roles.get(team, ""),
            "operator": (p.get("operator") or {}).get("name", ""),
            "operator_id": (p.get("operator") or {}).get("id", 0),
            "spawn": p.get("spawn", ""),
            "profile_id": p.get("profileID", ""),
            "kills": int(s.get("kills", 0)),
            "died": bool(s.get("died", False)),
            "headshots": int(s.get("headshots", 0)),
            "assists": int(s.get("assists", 0)),
            "score": int(s.get("score", 0)),
            "one_vx": int(s.get("1vX", 0)),
            "opening_kill": False,
            "opening_death": False,
            "entry_kill": False,
            "trade_kills": 0,
            "was_traded": False,
            "untraded_death": False,
            "death_clock": None,
            "death_elapsed": None,
            "survived": not bool(s.get("died", False)),
            "kst": False,
        }

    # ---------------------------------------------------------------- aperturas
    if death_events:
        first = death_events[0]
        if first["kind"] == KILL:
            if first["actor"] in metrics:
                metrics[first["actor"]]["opening_kill"] = True
            if first["target"] in metrics:
                metrics[first["target"]]["opening_death"] = True
        elif first["actor"] in metrics:
            metrics[first["actor"]]["opening_death"] = True

    seen_team_kill: set[int] = set()
    for e in kill_events:
        team = team_of.get(e["actor"])
        if team is None or team in seen_team_kill:
            continue
        seen_team_kill.add(team)
        if e["actor"] in metrics:
            metrics[e["actor"]]["entry_kill"] = True

    # ---------------------------------------------------------------- muertes
    for e in death_events:
        victim = e["target"] if e["kind"] == KILL else e["actor"]
        m = metrics.get(victim)
        if not m:
            continue
        # se guarda la primera muerte registrada del jugador
        if m["death_clock"] is None:
            m["death_clock"] = e["clock"]
            m["death_elapsed"] = e["elapsed"]
        m["died"] = True
        m["survived"] = False

    # ---------------------------------------------------------------- trades
    for i, e in enumerate(kill_events):
        killer, victim = e["actor"], e["target"]
        victim_team = team_of.get(victim)
        if victim_team is None:
            continue
        for later in kill_events[i + 1 :]:
            gap = e["clock"] - later["clock"]  # el reloj baja: gap >= 0 es "despues"
            if gap < 0 or gap > TRADE_WINDOW:
                if gap > TRADE_WINDOW:
                    break
                continue
            if later["target"] != killer:
                continue
            if team_of.get(later["actor"]) != victim_team:
                continue
            e["traded"] = True
            if victim in metrics:
                metrics[victim]["was_traded"] = True
            if later["actor"] in metrics:
                metrics[later["actor"]]["trade_kills"] += 1
            break

    for m in metrics.values():
        m["untraded_death"] = m["died"] and not m["was_traded"]
        m["kst"] = bool(m["kills"] or m["survived"] or m["was_traded"])

    # ---------------------------------------------------------------- resultado
    winner = None
    for i, t in enumerate(teams):
        if t.get("won"):
            winner = i
    loser = None if winner is None else winner ^ 1

    team_sizes: dict[int, int] = {}
    team_deaths: dict[int, int] = {}
    for m in metrics.values():
        t = m["team_index"]
        team_sizes[t] = team_sizes.get(t, 0) + 1
        if m["died"]:
            team_deaths[t] = team_deaths.get(t, 0) + 1

    wiped = (
        loser is not None
        and team_sizes.get(loser, 0) > 0
        and team_deaths.get(loser, 0) >= team_sizes.get(loser, 0)
    )
    clock_end = float(round_data.get("clockEnd") or 0)
    is_bomb = (round_data.get("gamemode") or {}).get("name") == BOMB_MODE

    if wiped:
        win_condition, certain = "KilledOpponents", True
    elif winner is None:
        win_condition, certain = "", False
    else:
        # sin datos del defuser en las temporadas nuevas no podemos separar
        # plant/defuse de tiempo agotado; se marca como no certero.
        win_condition, certain = "ObjectiveOrTime", False

    possible_plant = bool(is_bomb and not wiped and clock_end > 5 and winner is not None)

    for m in metrics.values():
        m["won"] = winner is not None and m["team_index"] == winner

    return {
        "events": events,
        "players": metrics,
        "winner": winner,
        "win_condition": win_condition,
        "win_condition_certain": certain,
        "possible_plant": possible_plant,
        "clock_start": clock_start,
        "clock_end": clock_end,
        "team_sizes": team_sizes,
        "team_deaths": team_deaths,
    }
