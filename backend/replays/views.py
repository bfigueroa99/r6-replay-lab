"""API JSON. Sin DRF a proposito: son vistas de lectura y dos POST locales."""

from __future__ import annotations

import json
from datetime import date, datetime

from django.conf import settings
from django.db.models import Avg, Count, Q, Sum
from django.http import Http404, HttpRequest, HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_POST

import pydissect

from . import export as exportador
from . import unknowns
from .analytics import aggregates as agg
from .analytics.coach import build_insights
from .analytics.narrative import describe_round
from .ingest import find_match_folders, scan_and_import
from .models import ImportLog, Match, Player, Round, RoundPlayer
from .retag import retag


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
    session = request.GET.get("session")
    if session not in (None, ""):
        out["session"] = session
    days = request.GET.get("days")
    if days and "since" not in out:
        try:
            from datetime import timedelta

            out["since"] = datetime.now() - timedelta(days=int(days))
        except ValueError:
            pass
    return out


def _int_param(request: HttpRequest, key: str, default: int, *, minimum: int, maximum: int) -> int:
    """Entero de la query string, acotado al rango. Si no es valido, el default.

    El acotado no es cosmetico: sin el, un `?limit=-1` termina como slice
    negativo en el ORM y Django responde 500.
    """
    raw = request.GET.get(key)
    if raw:
        try:
            default = int(raw)
        except ValueError:
            pass
    return max(minimum, min(default, maximum))


def _min_rounds(request: HttpRequest, default: int | None = None) -> int:
    fallback = default if default is not None else settings.MIN_ROUNDS_DEFAULT
    return _int_param(request, "min_rounds", fallback, minimum=1, maximum=10_000)


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
            "sessions": agg.session_options(),
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
    limit = _int_param(request, "limit", 40, minimum=1, maximum=200)
    return _ok(
        {
            "by_day": agg.trend_by_day(**filters),
            "by_match": agg.trend_by_match(limit=limit, **filters),
            "by_round_number": agg.by_round_number(**filters),
            "deaths_by_time": agg.deaths_by_time(**filters),
            "death_timing": agg.death_timing(**filters),
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


@require_GET
def player_detail(request: HttpRequest, pk: int) -> JsonResponse:
    """Perfil de un companero o rival dentro de tus partidas."""
    payload = agg.player_profile(pk, **_filters(request))
    if payload is None:
        raise Http404("jugador no encontrado")
    return _ok(payload)


@require_GET
def sessions(request: HttpRequest) -> JsonResponse:
    """Sesiones de juego y como se mueve el rendimiento dentro de una."""
    filters = _filters(request)
    return _ok(
        {
            "gap_minutes": settings.SESSION_GAP_MINUTES,
            "sessions": agg.sessions(**filters),
            "by_position": agg.by_session_position(**filters),
        }
    )


@require_GET
def duels(request: HttpRequest) -> JsonResponse:
    """Duelos: contra quien y contra que operadores ganas y pierdes."""
    filters = _filters(request)
    min_duels = _int_param(request, "min_duels", 3, minimum=1, maximum=1000)
    return _ok(
        {
            "totals": agg.duel_totals(**filters),
            "nemesis": agg.nemesis(min_duels=min_duels, **filters),
            "operators": agg.duels_by_operator(min_duels=min_duels, **filters),
        }
    )


# --------------------------------------------------------------------- partidas


@require_GET
def match_list(request: HttpRequest) -> JsonResponse:
    limit = _int_param(request, "limit", 50, minimum=1, maximum=200)
    offset = _int_param(request, "offset", 0, minimum=0, maximum=1_000_000)

    qs = Match.objects.all()
    if request.GET.get("map"):
        qs = qs.filter(map_slug=request.GET["map"])
    if request.GET.get("match_type"):
        qs = qs.filter(match_type=request.GET["match_type"])
    total = qs.count()
    page = list(qs[offset : offset + limit])

    # Solo se agregan las partidas de esta pagina: agregar todo el historial
    # para mostrar 50 filas escanea la tabla entera en cada request.
    mine = {
        row["round__match_id"]: row
        for row in RoundPlayer.objects.filter(is_me=True, round__match__in=page)
        .values("round__match_id")
        # el alias no puede llamarse `kills`: el F("kills") del rating lo
        # resolveria contra la anotacion (un agregado) en vez del campo
        .annotate(
            kills_sum=Sum("kills"),
            deaths=Count("id", filter=Q(died=True)),
            rounds=Count("id"),
            opening_kills=Count("id", filter=Q(opening_kill=True)),
            opening_deaths=Count("id", filter=Q(opening_death=True)),
            rating_points=Avg(agg.rating_points_expr()),
        )
    }
    baseline = agg.rating_baseline()

    rows = []
    for match in page:
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
                "my_kills": stats.get("kills_sum") or 0,
                "my_deaths": stats.get("deaths") or 0,
                "my_opening_kills": stats.get("opening_kills") or 0,
                "my_opening_deaths": stats.get("opening_deaths") or 0,
                "my_rating": (
                    round(stats["rating_points"] / baseline, 2)
                    if baseline and stats.get("rating_points")
                    else None
                ),
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
        datos = {
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
        datos["summary"] = describe_round(datos)
        rounds.append(datos)

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


# --------------------------------------------------------------------- export


@require_GET
def export_table(request: HttpRequest) -> HttpResponse | JsonResponse:
    """Baja un agregado como CSV. Sin `table`, lista los disponibles.

    CSV estandar (coma, punto decimal, sin BOM) porque este es el camino de
    scripting; el boton de la UI arma el suyo pensado para Excel en espanol.
    `sep=;` fuerza punto y coma si hace falta.
    """
    table = request.GET.get("table", "")
    if not table:
        return _ok({"tables": exportador.table_names()})
    if table not in exportador.TABLES:
        return _ok(
            {"error": f"tabla desconocida: {table}", "tables": exportador.table_names()},
            status=400,
        )

    titulo, _ = exportador.TABLES[table]
    rows = exportador.export(table, **_filters(request))
    delimiter = ";" if request.GET.get("sep") == ";" else ","

    response = HttpResponse(
        exportador.to_csv(rows, delimiter), content_type="text/csv; charset=utf-8"
    )
    nombre = f"r6-{titulo}-{date.today():%Y%m%d}.csv"
    response["Content-Disposition"] = f'attachment; filename="{nombre}"'
    return response


# --------------------------------------------------------------------- etiquetas


@require_GET
def unknown(request: HttpRequest) -> JsonResponse:
    """IDs que el parser no supo nombrar, con las pistas para identificarlos."""
    return _ok(
        {
            "maps": unknowns.unknown_maps(),
            "operators": unknowns.unknown_operators(),
            "overrides_path": str(unknowns.overrides_path()),
        }
    )


@csrf_exempt
@require_POST
def save_overrides(request: HttpRequest) -> JsonResponse:
    """Guarda etiquetas en overrides.json y reetiqueta lo ya importado.

    Escribe un archivo del disco, asi que valida antes de tocar nada: la app es
    local, pero eso no es excusa para dejar entrar cualquier cosa.
    """
    try:
        payload = json.loads(request.body or b"{}")
    except json.JSONDecodeError:
        return _ok({"error": "el cuerpo no es JSON valido"}, status=400)
    if not isinstance(payload, dict):
        return _ok({"error": "se esperaba un objeto JSON"}, status=400)

    try:
        maps = unknowns.clean_labels(payload.get("maps"))
        operators = unknowns.clean_labels(payload.get("operators"))
    except unknowns.LabelError as exc:
        return _ok({"error": str(exc)}, status=400)

    if not maps and not operators:
        return _ok({"error": "no mandaste ninguna etiqueta"}, status=400)

    unknowns.write_overrides(maps, operators)
    # retag recarga el cache de overrides, que si no queda viejo hasta reiniciar
    result = retag()
    return _ok(
        {
            "saved": {"maps": maps, "operators": operators},
            "matches": result.matches,
            "round_players": result.round_players,
            "changes": [
                {"kind": c.kind, "old": c.old, "new": c.new, "rows": c.rows}
                for c in result.changes
            ],
        }
    )


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
