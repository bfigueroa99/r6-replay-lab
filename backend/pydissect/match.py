"""Lectura de una partida completa (carpeta Match-YYYY-MM-DD_hh-mm-ss-xxxx)."""

from __future__ import annotations

import logging
from pathlib import Path

from .constants import EVENT_NAMES
from .errors import InvalidFolder
from .header import (
    gamemode_name,
    map_name,
    map_slug,
    match_type_name,
    operator_label,
    operator_name,
)
from .reader import Reader
from .stats import opening_death, opening_kill, player_match_stats, player_round_stats, trades

log = logging.getLogger(__name__)


def list_replay_files(folder: str | Path) -> list[Path]:
    folder = Path(folder)
    files = sorted(p for p in folder.glob("*.rec") if p.is_file())
    if not files:
        raise InvalidFolder(f"{folder} no contiene archivos .rec")
    return files


class MatchReader:
    """Parsea todas las rondas de una carpeta de partida."""

    def __init__(self, folder: str | Path) -> None:
        self.folder = Path(folder)
        self.paths = list_replay_files(self.folder)
        self.rounds: list[Reader] = []

    def read(self) -> MatchReader:
        for path in self.paths:
            log.debug("leyendo %s", path.name)
            reader = Reader.from_path(path)
            reader.read()
            self.rounds.append(reader)
        return self

    # ------------------------------------------------------------------ export
    def to_dict(self) -> dict:
        """Estructura equivalente al JSON de r6-dissect, mas campos derivados."""
        rounds = []
        for reader, path in zip(self.rounds, self.paths, strict=True):
            rounds.append(round_to_dict(reader, path))
        return {
            "matchID": rounds[0]["matchID"] if rounds else "",
            "folder": self.folder.name,
            "rounds": rounds,
            "stats": player_match_stats([r["stats"] for r in rounds]),
        }


def round_to_dict(reader: Reader, path: Path | None = None) -> dict:
    """Serializa una ronda: metadata, jugadores, eventos y stats."""
    h = reader.header
    ok = opening_kill(reader)
    od = opening_death(reader)
    return {
        "file": path.name if path else "",
        "matchID": h.get("matchID", ""),
        "gameVersion": h.get("gameVersion", ""),
        "codeVersion": h.get("codeVersion", 0),
        "timestamp": h["timestamp"].isoformat() if h.get("timestamp") else None,
        "matchType": {"id": h.get("matchType", 0), "name": match_type_name(h.get("matchType", 0))},
        "gamemode": {"id": h.get("gamemode", 0), "name": gamemode_name(h.get("gamemode", 0))},
        "map": {
            "id": h.get("map", 0),
            "name": map_name(h.get("map", 0)),
            "slug": map_slug(h.get("map", 0)),
        },
        "site": h.get("site", ""),
        "clockStart": reader.clock_max,
        "clockEnd": reader.clock_last,
        "roundNumber": h.get("roundNumber", 0),
        "overtimeRoundNumber": h.get("overtimeRoundNumber", 0),
        "roundsPerMatch": h.get("roundsPerMatch", 0),
        "roundsPerMatchOvertime": h.get("roundsPerMatchOvertime", 0),
        "recordingPlayerID": h.get("recordingPlayerID", 0),
        "recordingProfileID": h.get("recordingProfileID", ""),
        "recordingPlayer": reader.recording_player().get("username", ""),
        "teams": [
            {
                "name": t.get("name", ""),
                "score": t.get("score", 0),
                "startingScore": t.get("startingScore", 0),
                "won": bool(t.get("won")),
                "winCondition": t.get("winCondition", ""),
                "role": t.get("role", ""),
            }
            for t in reader.teams
        ],
        "players": [
            {
                "id": p.get("id", 0),
                "profileID": p.get("profileID", ""),
                "username": p.get("username", ""),
                "teamIndex": p.get("teamIndex", 0),
                "operator": {
                    "id": p.get("operator", 0),
                    "name": operator_label(p),
                },
                "spawn": p.get("spawn", ""),
                "roleName": p.get("roleName", ""),
            }
            for p in reader.players
        ],
        "matchFeedback": [
            {
                "type": {"id": u["type"], "name": EVENT_NAMES.get(u["type"], "Other")},
                "username": u.get("username", ""),
                "target": u.get("target", ""),
                "headshot": u.get("headshot"),
                "time": u.get("time", ""),
                "timeInSeconds": u.get("timeInSeconds", 0.0),
                "message": u.get("message", ""),
                "operator": (
                    {"id": u["operator"], "name": operator_name(u["operator"])}
                    if u.get("operator")
                    else None
                ),
            }
            for u in reader.match_feedback
        ],
        "stats": player_round_stats(reader),
        "openingKill": ok,
        "openingDeath": od,
        "trades": [
            {
                "first": a.get("username", ""),
                "second": b.get("username", ""),
                "time": b.get("time", ""),
            }
            for a, b in trades(reader)
        ],
        "inferredOperatorSides": h.get("inferredOperatorSides", {}),
    }
