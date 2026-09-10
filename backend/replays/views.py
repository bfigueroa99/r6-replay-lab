"""API JSON. Sin DRF a proposito: son vistas de lectura y un POST de import."""

from __future__ import annotations

from datetime import datetime

from django.conf import settings
from django.db.models import Count, Q, Sum
from django.http import Http404, HttpRequest, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_POST

import pydissect

from .analytics import aggregates as agg
from .analytics.coach import build_insights
from .ingest import find_match_folders, scan_and_import
from .models import ImportLog, Match, Player, Round, RoundPlayer


# --------------------------------------------------------------------- helpers


def _filters(request: HttpRequest) -> dict:
    out: dict = {}
    for key in ("side", "map", "operator", "site", "match_type"):
        value = request.GET.get(key)
        if value:
            out[key] = value
    if request.GET.get("ranked_only"):
        out["ranked_only"] = request.GET["ranked_only"].lower() in ("1", "true", "si", "yes")
    for key in ("since", "until"):
        value = request.GET.get(key)
        if value:
            try:
                out[key] = datetime.fromisoformat(value)
            except ValueError:
                pass
    days = request.GET.get("days")
    if days and "since" not in out:
        try:
            from datetime import timedelta

            out["since"] = datetime.now() - timedelta(days=int(days))
        except ValueError:
            pass
    return out


def _min_rounds(request: HttpRequest, default: int | None = None) -> int:
    raw = request.GET.get("min_rounds")
    if raw:
        try:
            return max(int(raw), 1)
        except ValueError:
            pass
    return default if default is not None else settings.MIN_ROUNDS_DEFAULT


def _ok(payload: dict, status: int = 200) -> JsonResponse:
    return JsonResponse(payload, status=status, json_dumps_params={"ensure_ascii": False})


# --------------------------------------------------------------------- generales


@require_GET
def health(request: HttpRequest) -> JsonResponse:
    me = Player.objects.filter(is_me=True).first()
    return _ok(
        {
            "ok": True,
            "parser_version": pydissect.__version__,
            "replay_dir": settings.REPLAY_DIR,
            "replay_dir_folders": len(find_match_folders(settings.REPLAY_DIR)),
            "player": me.username if me else None,
            "matches": Match.objects.count(),
            "rounds": Round.objects.count(),
            "last_import": _import_log_row(ImportLog.objects.first()),
        }
    )


@require_GET
def filter_options(request: HttpRequest) -> JsonResponse:
    qs = agg.base_queryset()
    return _ok(
        {
            "maps": list(
                Match.objects.values("map_slug", "map_name")
                .distinct()
                .order_by("map_name")
            ),
            "operators": sorted(
                {o for o in qs.values_list("operator", flat=True).distinct() if o}
            ),
            "sites": sorted(
                {s for s in qs.values_list("round__site", flat=True).distinct() if s}
            ),
            "match_types": sorted(
                {m for m in Match.objects.values_list("match_type", flat=True).distinct() if m}
            ),
            "sides": ["Attack", "Defense"],
        }
    )


@require_GET
def overview(request: HttpRequest) -> JsonResponse:
    filters = _filters(request)
    payload = agg.overview(**filters)
    payload["data_health"] = agg.data_health(**filters)
    payload["filters"] = {k: str(v) for k, v in filters.items()}
    return _ok(payload)


@require_GET
def coach(request: HttpRequest) -> JsonResponse:
    return _ok(build_insights(**_filters(request)))


@require_GET
def maps(request: HttpRequest) -> JsonResponse:
    filters = _filters(request)
    min_rounds = _min_rounds(request, 1)
    return _ok(
        {
            "maps": agg.by_map(min_rounds=min_rounds, **filters),
            "sites": agg.by_site(min_rounds=min_rounds, **filters),
            "spawns": agg.by_spawn(min_rounds=min_rounds, **filters),
        }
    )


@require_GET
def operators(request: HttpRequest) -> JsonResponse:
    filters = _filters(request)
    return _ok({"operators": agg.by_operator(min_rounds=_min_rounds(request, 1), **filters)})


@require_GET
def trends(request: HttpRequest) -> JsonResponse:
    filters = _filters(request)
    try:
        limit = int(request.GET.get("limit", 40))
    except ValueError:
        limit = 40
    return _ok(
        {
            "by_day": agg.trend_by_day(**filters),
            "by_match": agg.trend_by_match(limit=limit, **filters),
            "by_round_number": agg.by_round_number(**filters),
        }
    )


@require_GET
def teammates(request: HttpRequest) -> JsonResponse:
    filters = _filters(request)
    return _ok(
        {
            "synergy": agg.teammate_synergy(min_rounds=_min_rounds(request, 10), **filters),
            "clutches": agg.clutch_detail(**filters),
        }
    )


# --------------------------------------------------------------------- partidas


@require_GET
def match_list(request: HttpRequest) -> JsonResponse:
    try:
        limit = min(int(request.GET.get("limit", 50)), 200)
        offset = max(int(request.GET.get("offset", 0)), 0)
    except ValueError:
        limit, offset = 50, 0

    qs = Match.objects.all()
    if request.GET.get("map"):
        qs = qs.filter(map_slug=request.GET["map"])
    if request.GET.get("match_type"):
        qs = qs.filter(match_type=request.GET["match_type"])
    total = qs.count()

    mine = {
        row["round__match_id"]: row
        for row in RoundPlayer.objects.filter(is_me=True)
        .values("round__match_id")
        .annotate(
            kills=Sum("kills"),
            deaths=Count("id", filter=Q(died=True)),
            rounds=Count("id"),
            opening_kills=Count("id", filter=Q(opening_kill=True)),
            opening_deaths=Count("id", filter=Q(opening_death=True)),
        )
    }

    rows = []
    for match in qs[offset : offset + limit]:
        stats = mine.get(match.id, {})
        rows.append(
            {
                "id": match.id,
                "match_id": match.match_id,
                "folder": match.folder,
                "played_at": match.played_at.isoformat(),
                "map": match.map_name,
                "map_slug": match.map_slug,
                "match_type": match.match_type,
                "gamemode": match.gamemode,
                "score": f"{match.my_score}-{match.opponent_score}",
                "my_score": match.my_score,
                "opponent_score": match.opponent_score,
                "won": match.won,
                "result": match.result,
                "rounds": match.rounds_count,
                "my_kills": stats.get("kills") or 0,
                "my_deaths": stats.get("deaths") or 0,
                "my_opening_kills": stats.get("opening_kills") or 0,
                "my_opening_deaths": stats.get("opening_deaths") or 0,
            }
        )
    return _ok({"total": total, "limit": limit, "offset": offset, "matches": rows})


@require_GET
def match_detail(request: HttpRequest, pk: int) -> JsonResponse:
    try:
        match = Match.objects.get(pk=pk)
    except Match.DoesNotExist as exc:
        raise Http404("partida no encontrada") from exc

    rounds = []
    for rnd in match.rounds.prefetch_related("players__player", "events").all():
        players = [
            {
                "username": rp.username,
                "player_id": rp.player_id,
                "team_index": rp.team_index,
                "side": rp.side,
                "is_me": rp.is_me,
                "operator": rp.operator,
                "spawn": rp.spawn,
                "kills": rp.kills,
                "died": rp.died,
                "headshots": rp.headshots,
                "hs_pct": round(rp.headshot_percentage, 1) if rp.kills else None,
                "one_vx": rp.one_vx,
                "opening_kill": rp.opening_kill,
                "opening_death": rp.opening_death,
                "entry_kill": rp.entry_kill,
                "trade_kills": rp.trade_kills,
                "was_traded": rp.was_traded,
                "untraded_death": rp.untraded_death,
                "death_clock": rp.death_clock,
                "death_elapsed": rp.death_elapsed,
                "survived": rp.survived,
                "kst": rp.kst,
                "won": rp.won,
            }
            for rp in rnd.players.all()
        ]
        events = [
            {
                "order": e.order,
                "kind": e.kind,
                "clock": e.clock,
                "clock_raw": e.clock_raw,
                "elapsed": e.elapsed,
                "actor": e.actor_name,
                "target": e.target_name,
                "headshot": e.headshot,
                "operator": e.operator,
                "message": e.message,
                "traded": e.traded,
            }
            for e in rnd.events.all()
        ]
        rounds.append(
            {
                "number": rnd.number,
                "label": f"R{rnd.number + 1}",
                "site": rnd.site,
                "my_side": rnd.my_side,
                "my_team_won": rnd.my_team_won,
                "win_condition": rnd.win_condition,
                "win_condition_certain": rnd.win_condition_certain,
                "score_before": rnd.score_before,
                "score_after": rnd.score_after,
                "clock_start": rnd.clock_start,
                "clock_end": rnd.clock_end,
                "duration": rnd.duration,
                "possible_plant": rnd.possible_plant,
                "teams": rnd.teams,
                "players": players,
                "events": events,
            }
        )

    scoreboard = _match_scoreboard(match)
    my_totals = agg.totals(agg.base_queryset().filter(round__match=match))

    return _ok(
        {
            "match": {
                "id": match.id,
                "match_id": match.match_id,
                "folder": match.folder,
                "played_at": match.played_at.isoformat(),
                "map": match.map_name,
                "match_type": match.match_type,
                "gamemode": match.gamemode,
                "game_version": match.game_version,
                "score": f"{match.my_score}-{match.opponent_score}",
                "my_score": match.my_score,
                "opponent_score": match.opponent_score,
                "won": match.won,
                "result": match.result,
                "my_team_index": match.my_team_index,
                "warnings": match.warnings,
            },
            "rounds": rounds,
            "scoreboard": scoreboard,
            "my_totals": my_totals,
        }
    )


def _match_scoreboard(match: Match) -> list[dict]:
    rows = (
        RoundPlayer.objects.filter(round__match=match)
        .values("player_id", "username", "team_index", "is_me")
        .annotate(
            rounds=Count("id"),
            kills=Sum("kills"),
            deaths=Count("id", filter=Q(died=True)),
            headshots=Sum("headshots"),
            opening_kills=Count("id", filter=Q(opening_kill=True)),
            opening_deaths=Count("id", filter=Q(opening_death=True)),
            trade_kills=Sum("trade_kills"),
            untraded_deaths=Count("id", filter=Q(untraded_death=True)),
            clutches=Count("id", filter=Q(one_vx__gt=0)),
            kst_rounds=Count("id", filter=Q(kst=True)),
        )
        .order_by("team_index", "-kills")
    )
    out = []
    for r in rows:
        row = dict(r)
        kills = row.get("kills") or 0
        row["kd"] = round(kills / row["deaths"], 2) if row["deaths"] else None
        row["hs_pct"] = round((row.get("headshots") or 0) / kills * 100, 1) if kills else None
        row["kst_pct"] = (
            round(row["kst_rounds"] / row["rounds"] * 100, 1) if row["rounds"] else None
        )
        out.append(row)
    return out


# --------------------------------------------------------------------- import


@csrf_exempt
@require_POST
def run_import(request: HttpRequest) -> JsonResponse:
    """Escanea la carpeta de replays e importa lo nuevo."""
    force = request.GET.get("force", "").lower() in ("1", "true", "si", "yes")
    try:
        limit = int(request.GET.get("limit", 0)) or None
    except ValueError:
        limit = None

    results = scan_and_import(
        settings.REPLAY_DIR,
        quiet_seconds=settings.IMPORT_QUIET_SECONDS,
        force=force,
        limit=limit,
    )
    return _ok(
        {
            "imported": [
                {"folder": r.folder, "ok": r.ok, "rounds": r.rounds, "message": r.message}
                for r in results
            ],
            "count": len([r for r in results if r.ok]),
            "errors": len([r for r in results if not r.ok]),
        }
    )


@require_GET
def import_status(request: HttpRequest) -> JsonResponse:
    folders = find_match_folders(settings.REPLAY_DIR)
    known = set(Match.objects.values_list("folder", flat=True))
    return _ok(
        {
            "replay_dir": settings.REPLAY_DIR,
            "folders_on_disk": len(folders),
            "folders_imported": len([f for f in folders if f.name in known]),
            "pending": [f.name for f in folders if f.name not in known][:50],
            "log": [_import_log_row(e) for e in ImportLog.objects.all()[:25]],
        }
    )


def _import_log_row(entry: ImportLog | None) -> dict | None:
    if not entry:
        return None
    return {
        "folder": entry.folder,
        "started_at": entry.started_at.isoformat(),
        "finished_at": entry.finished_at.isoformat() if entry.finished_at else None,
        "ok": entry.ok,
        "rounds": entry.rounds_imported,
        "message": entry.message,
    }
