"""Importacion de replays a la base de datos."""

from __future__ import annotations

import logging
import threading
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

from django.db import transaction
from django.utils import timezone

import pydissect
from pydissect import MatchReader

from .analytics.metrics import analyse_round
from .models import Event, ImportLog, Match, Player, Round, RoundPlayer

log = logging.getLogger(__name__)

MATCH_FOLDER_PREFIX = "Match-"


@dataclass
class ImportResult:
    folder: str
    ok: bool
    rounds: int = 0
    message: str = ""
    match_id: str = ""
    created: bool = False


# --------------------------------------------------------------------- utilidades


def find_match_folders(root: str | Path) -> list[Path]:
    """Carpetas Match-* que contienen al menos un .rec."""
    root = Path(root)
    if not root.exists():
        return []
    out = []
    for child in sorted(root.iterdir()):
        if child.is_dir() and child.name.startswith(MATCH_FOLDER_PREFIX):
            if any(child.glob("*.rec")):
                out.append(child)
    return out


def folder_is_settled(folder: Path, quiet_seconds: float = 60.0) -> bool:
    """True si ningun .rec fue modificado en los ultimos `quiet_seconds`.

    Evita importar una partida que todavia se esta jugando.
    """
    newest = max((p.stat().st_mtime for p in folder.glob("*.rec")), default=0)
    return (time.time() - newest) >= quiet_seconds


def _profile_key(player: dict) -> str:
    pid = (player.get("profileID") or "").strip()
    if pid:
        return pid
    return f"name:{player.get('username', '')}"


def _get_player(cache: dict, profile_key: str, username: str, seen_at) -> Player:
    if profile_key in cache:
        obj = cache[profile_key]
    else:
        obj, _ = Player.objects.get_or_create(
            profile_id=profile_key, defaults={"username": username or profile_key}
        )
        cache[profile_key] = obj
    changed = False
    if username and obj.username != username:
        obj.note_alias(username)
        obj.username = username
        changed = True
    if seen_at:
        if not obj.first_seen or seen_at < obj.first_seen:
            obj.first_seen = seen_at
            changed = True
        if not obj.last_seen or seen_at > obj.last_seen:
            obj.last_seen = seen_at
            changed = True
    if changed:
        obj.save()
    return obj


# --------------------------------------------------------------------- importacion


def import_match_folder(folder: str | Path, *, force: bool = False) -> ImportResult:
    """Parsea una carpeta de partida y la guarda (idempotente por match_id)."""
    folder = Path(folder)
    entry = ImportLog.objects.create(folder=folder.name)
    try:
        result = _import(folder, force=force)
    except Exception as exc:  # noqa: BLE001 - se registra y se sigue
        log.exception("fallo importando %s", folder)
        entry.ok = False
        entry.message = f"{type(exc).__name__}: {exc}"
        entry.finished_at = timezone.now()
        entry.save()
        return ImportResult(folder.name, False, message=entry.message)

    entry.ok = result.ok
    entry.rounds_imported = result.rounds
    entry.message = result.message
    entry.finished_at = timezone.now()
    entry.save()
    return result


def _import(folder: Path, *, force: bool) -> ImportResult:
    reader = MatchReader(folder).read()
    data = reader.to_dict()
    rounds = data["rounds"]
    if not rounds:
        return ImportResult(folder.name, False, message="sin rondas legibles")

    first = rounds[0]
    last = rounds[-1]
    match_id = first.get("matchID") or folder.name

    existing = Match.objects.filter(match_id=match_id).first()
    if existing and not force:
        if existing.rounds_count >= len(rounds):
            return ImportResult(
                folder.name, True, existing.rounds_count, "ya estaba importada", match_id
            )

    my_profile = (first.get("recordingProfileID") or "").strip()
    warnings: list[str] = []
    if not my_profile:
        warnings.append("el replay no trae recordingProfileID; se usa el nombre del grabador")

    played_at = _parse_ts(first.get("timestamp"))

    # equipo propio y marcador final
    my_team_index = _find_my_team(first, my_profile, first.get("recordingPlayer", ""))
    final_scores = [t.get("score", 0) for t in last.get("teams", [{}, {}])]
    my_score = final_scores[my_team_index] if len(final_scores) > my_team_index else 0
    opp_score = final_scores[my_team_index ^ 1] if len(final_scores) > 1 else 0

    with transaction.atomic():
        match, created = Match.objects.update_or_create(
            match_id=match_id,
            defaults={
                "folder": folder.name,
                "source_path": str(folder),
                "played_at": played_at,
                "map_id": (first.get("map") or {}).get("id", 0),
                "map_name": (first.get("map") or {}).get("name", ""),
                "map_slug": (first.get("map") or {}).get("slug", ""),
                "match_type": (first.get("matchType") or {}).get("name", ""),
                "gamemode": (first.get("gamemode") or {}).get("name", ""),
                "game_version": first.get("gameVersion", ""),
                "code_version": first.get("codeVersion", 0),
                "rounds_count": len(rounds),
                "my_team_index": my_team_index,
                "my_score": my_score,
                "opponent_score": opp_score,
                "won": None if my_score == opp_score else my_score > opp_score,
                "parser_version": pydissect.__version__,
                "warnings": warnings,
            },
        )
        match.rounds.all().delete()

        cache: dict[str, Player] = {}
        imported = 0
        for round_data in rounds:
            _import_round(match, round_data, my_profile, cache, played_at)
            imported += 1

        # marca quien soy
        me_key = my_profile or f"name:{first.get('recordingPlayer', '')}"
        if me_key in cache and not cache[me_key].is_me:
            Player.objects.filter(pk=cache[me_key].pk).update(is_me=True)

    return ImportResult(folder.name, True, imported, "ok", match_id, created)


def _import_round(match: Match, round_data: dict, my_profile: str, cache: dict, seen_at) -> None:
    analysis = analyse_round(round_data)
    teams = round_data.get("teams", [{}, {}])

    my_team_index = _find_my_team(round_data, my_profile, round_data.get("recordingPlayer", ""))
    my_side = (teams[my_team_index].get("role") or "") if len(teams) > my_team_index else ""
    winner = analysis["winner"]

    round_obj = Round.objects.create(
        match=match,
        number=round_data.get("roundNumber", 0),
        overtime_number=round_data.get("overtimeRoundNumber", 0),
        file_name=round_data.get("file", ""),
        site=round_data.get("site", ""),
        my_side=my_side,
        my_team_won=None if winner is None else winner == my_team_index,
        win_condition=analysis["win_condition"],
        win_condition_certain=analysis["win_condition_certain"],
        score_before=[t.get("startingScore", 0) for t in teams],
        score_after=[t.get("score", 0) for t in teams],
        clock_start=analysis["clock_start"],
        clock_end=analysis["clock_end"],
        possible_plant=analysis["possible_plant"],
        teams=[
            {
                "name": t.get("name", ""),
                "role": t.get("role", ""),
                "won": bool(t.get("won")),
                "score": t.get("score", 0),
                "mine": i == my_team_index,
            }
            for i, t in enumerate(teams)
        ],
    )

    players_by_name: dict[str, Player] = {}
    round_players = []
    for raw in round_data.get("players", []):
        name = raw.get("username", "")
        m = analysis["players"].get(name)
        if not m:
            continue
        key = _profile_key(raw)
        player = _get_player(cache, key, name, seen_at)
        players_by_name[name] = player
        is_me = bool(my_profile) and raw.get("profileID") == my_profile
        if not my_profile:
            is_me = name == round_data.get("recordingPlayer", "")
        round_players.append(
            RoundPlayer(
                round=round_obj,
                player=player,
                username=name,
                team_index=m["team_index"],
                side=m["side"],
                is_me=is_me,
                won=m["won"],
                operator_id=m["operator_id"],
                operator=m["operator"],
                spawn=m["spawn"],
                kills=m["kills"],
                died=m["died"],
                headshots=m["headshots"],
                assists=m["assists"],
                score=m["score"],
                one_vx=m["one_vx"],
                opening_kill=m["opening_kill"],
                opening_death=m["opening_death"],
                entry_kill=m["entry_kill"],
                trade_kills=m["trade_kills"],
                was_traded=m["was_traded"],
                untraded_death=m["untraded_death"],
                death_clock=m["death_clock"],
                death_elapsed=m["death_elapsed"],
                survived=m["survived"],
                kst=m["kst"],
            )
        )
    RoundPlayer.objects.bulk_create(round_players)

    events = [
        Event(
            round=round_obj,
            order=e["order"],
            kind=e["kind"],
            clock=e["clock"],
            clock_raw=e["clock_raw"],
            elapsed=e["elapsed"],
            actor=players_by_name.get(e["actor"]),
            actor_name=e["actor"],
            target=players_by_name.get(e["target"]),
            target_name=e["target"],
            headshot=e["headshot"],
            operator=e["operator"],
            message=e["message"],
            traded=e["traded"],
        )
        for e in analysis["events"]
    ]
    Event.objects.bulk_create(events)


def _find_my_team(round_data: dict, my_profile: str, recording_name: str) -> int:
    for p in round_data.get("players", []):
        if my_profile and p.get("profileID") == my_profile:
            return p.get("teamIndex", 0)
        if not my_profile and p.get("username") == recording_name:
            return p.get("teamIndex", 0)
    # ultimo recurso: el juego llama "YOUR TEAM" al equipo del grabador
    for i, t in enumerate(round_data.get("teams", [])):
        if (t.get("name") or "").upper().startswith("YOUR"):
            return i
    return 0


def _parse_ts(value) -> datetime:
    if isinstance(value, datetime):
        return value
    if isinstance(value, str) and value:
        try:
            return datetime.fromisoformat(value)
        except ValueError:
            pass
    return datetime.now()


# --------------------------------------------------------------------- escaneo


def pending_folders(
    root: str | Path, *, quiet_seconds: float = 60.0, force: bool = False, limit: int | None = None
) -> list[Path]:
    """Carpetas que se van a importar. Se calcula antes para saber el total.

    Sin esto no se puede decir "3 de 12": el total solo se sabria al terminar.
    """
    known = set(Match.objects.values_list("folder", flat=True))
    out: list[Path] = []
    for folder in find_match_folders(root):
        if folder.name in known and not force:
            continue
        if not folder_is_settled(folder, quiet_seconds):
            log.info("%s todavia se esta escribiendo, se salta", folder.name)
            continue
        out.append(folder)
        if limit and len(out) >= limit:
            break
    return out


def import_folders(
    folders: list[Path],
    *,
    force: bool = False,
    on_progress: Callable[[int, int, str], None] | None = None,
) -> list[ImportResult]:
    """Importa una lista ya decidida de carpetas.

    `on_progress(hechas, total, carpeta)` se llama **antes** de cada una, que es
    lo que permite mostrar cual se esta leyendo y no solo cuantas van.
    """
    results: list[ImportResult] = []
    for i, folder in enumerate(folders):
        if on_progress:
            on_progress(i, len(folders), folder.name)
        results.append(import_match_folder(folder, force=force))
    if on_progress:
        on_progress(len(folders), len(folders), "")
    return results


def scan_and_import(
    root: str | Path,
    *,
    quiet_seconds: float = 60.0,
    force: bool = False,
    limit: int | None = None,
    on_progress: Callable[[int, int, str], None] | None = None,
) -> list[ImportResult]:
    """Importa todas las carpetas nuevas de `root`.

    `on_progress(hechas, total, carpeta)` se llama **antes** de cada carpeta, que
    es lo que permite mostrar cual se esta leyendo y no solo cuantas van.
    """
    folders = pending_folders(root, quiet_seconds=quiet_seconds, force=force, limit=limit)
    return import_folders(folders, force=force, on_progress=on_progress)


# --------------------------------------------------------------------- en segundo plano


@dataclass
class ImportJob:
    """Estado de una importacion, para poder mirarla mientras corre."""

    running: bool = False
    total: int = 0
    done: int = 0
    current: str = ""
    started_at: datetime | None = None
    finished_at: datetime | None = None
    error: str = ""
    results: list[ImportResult] = field(default_factory=list)

    def as_dict(self) -> dict:
        return {
            "running": self.running,
            "total": self.total,
            "done": self.done,
            "current": self.current,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "finished_at": self.finished_at.isoformat() if self.finished_at else None,
            "error": self.error,
            "imported": [
                {"folder": r.folder, "ok": r.ok, "rounds": r.rounds, "message": r.message}
                for r in self.results
            ],
            "count": len([r for r in self.results if r.ok]),
            "errors": len([r for r in self.results if not r.ok]),
        }


_job = ImportJob()
_job_lock = threading.Lock()


def import_job() -> ImportJob:
    """El estado de la ultima importacion lanzada desde la API."""
    return _job


def run_import_job(folders: list[Path], *, force: bool = False) -> ImportJob:
    """Importa las carpetas actualizando el estado global. Sincrono.

    Separado de `start_import` para poder probarlo sin hilos: en los tests de
    Django un hilo abre otra conexion y no ve los datos de la transaccion.
    """

    def progreso(done: int, total: int, folder: str) -> None:
        _job.done, _job.total, _job.current = done, total, folder

    try:
        _job.results = import_folders(folders, force=force, on_progress=progreso)
    except Exception as exc:  # noqa: BLE001 - queda en el estado, no tumba el hilo
        log.exception("fallo la importacion en segundo plano")
        _job.error = f"{type(exc).__name__}: {exc}"
    finally:
        _job.running = False
        _job.current = ""
        _job.finished_at = timezone.now()
    return _job


def start_import(
    root: str | Path,
    *,
    quiet_seconds: float = 60.0,
    force: bool = False,
    limit: int | None = None,
) -> ImportJob:
    """Lanza la importacion en un hilo y vuelve enseguida.

    Con 30 carpetas el POST tardaba minutos y el boton quedaba colgado sin decir
    nada. Si ya hay una corriendo, no se lanza otra.

    La lista de carpetas se arma **aca** y no en el hilo, para que el POST ya
    vuelva con el total: si no, el boton muestra "importando..." sin numero
    hasta que el hilo alcance a calcularlo.
    """
    global _job
    with _job_lock:
        if _job.running:
            return _job
        folders = pending_folders(root, quiet_seconds=quiet_seconds, force=force, limit=limit)
        _job = ImportJob(running=True, started_at=timezone.now(), total=len(folders))

    hilo = threading.Thread(
        target=run_import_job,
        args=(folders,),
        kwargs={"force": force},
        daemon=True,
        name="r6-import",
    )
    hilo.start()
    return _job
