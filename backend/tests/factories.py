"""Constructores de datos sinteticos para los tests."""

from __future__ import annotations

from datetime import datetime, timedelta

from replays.models import Event, Match, Player, Round, RoundPlayer

ME = "BearF99"


def make_player(username: str = ME, *, is_me: bool = False) -> Player:
    player, _ = Player.objects.get_or_create(
        profile_id=f"pid-{username}", defaults={"username": username, "is_me": is_me}
    )
    if is_me and not player.is_me:
        player.is_me = True
        player.save()
    return player


def make_match(
    *,
    map_name: str = "Club House",
    played_at: datetime | None = None,
    my_score: int = 4,
    opponent_score: int = 2,
    match_type: str = "Ranked",
    index: int = 0,
    map_id: int = 0,
) -> Match:
    played_at = played_at or datetime(2026, 9, 1, 20, 0) + timedelta(hours=index)
    return Match.objects.create(
        match_id=f"match-{index}-{map_name}",
        folder=f"Match-{index}",
        played_at=played_at,
        map_id=map_id,
        map_name=map_name,
        map_slug=map_name.lower().replace(" ", "-"),
        match_type=match_type,
        gamemode="Bomb",
        rounds_count=my_score + opponent_score,
        my_team_index=0,
        my_score=my_score,
        opponent_score=opponent_score,
        won=my_score > opponent_score,
    )


def make_round(
    match: Match,
    number: int,
    *,
    side: str = "Attack",
    site: str = "B Church, B Arsenal Room",
    won: bool = True,
) -> Round:
    return Round.objects.create(
        match=match,
        number=number,
        site=site,
        my_side=side,
        my_team_won=won,
        win_condition="KilledOpponents",
        clock_start=180,
        clock_end=30,
        teams=[{"name": "YOUR TEAM", "mine": True}, {"name": "ENEMY TEAM", "mine": False}],
    )


def make_round_player(
    rnd: Round,
    *,
    username: str = ME,
    is_me: bool = True,
    side: str | None = None,
    operator: str = "Zofia",
    operator_id: int = 0,
    kills: int = 1,
    died: bool = True,
    headshots: int = 0,
    opening_kill: bool = False,
    opening_death: bool = False,
    was_traded: bool = False,
    trade_kills: int = 0,
    one_vx: int = 0,
    death_elapsed: float | None = 60.0,
    spawn: str = "Warehouse",
    team_index: int = 0,
    won: bool | None = None,
) -> RoundPlayer:
    player = make_player(username, is_me=is_me)
    return RoundPlayer.objects.create(
        round=rnd,
        player=player,
        username=username,
        team_index=team_index,
        side=side or rnd.my_side,
        is_me=is_me,
        won=rnd.my_team_won if won is None else won,
        operator=operator,
        operator_id=operator_id,
        spawn=spawn,
        kills=kills,
        died=died,
        headshots=headshots,
        one_vx=one_vx,
        opening_kill=opening_kill,
        opening_death=opening_death,
        entry_kill=opening_kill,
        trade_kills=trade_kills,
        was_traded=was_traded,
        untraded_death=died and not was_traded,
        death_clock=(rnd.clock_start - death_elapsed) if (died and death_elapsed) else None,
        death_elapsed=death_elapsed if died else None,
        survived=not died,
        kst=bool(kills or not died or was_traded),
    )


def make_event(rnd: Round, order: int, actor: str, target: str = "", *, kind: str = "Kill",
               clock: float = 120.0, headshot: bool | None = False) -> Event:
    return Event.objects.create(
        round=rnd,
        order=order,
        kind=kind,
        clock=clock,
        clock_raw=f"{int(clock) // 60}:{int(clock) % 60:02d}",
        elapsed=rnd.clock_start - clock,
        actor=make_player(actor) if actor else None,
        actor_name=actor,
        target=make_player(target) if target else None,
        target_name=target,
        headshot=headshot,
    )


def build_dataset(
    *,
    matches: int = 6,
    rounds_per_match: int = 6,
    my_winrate: float = 0.5,
    opening_win_ratio: float = 0.5,
    traded_ratio: float = 0.5,
    hs_ratio: float = 0.3,
    maps: tuple[str, ...] = ("Club House", "Border"),
) -> list[Match]:
    """Crea un set de partidas con las proporciones pedidas.

    Sirve para probar que las reglas del coach se disparan con los umbrales
    esperados sin depender de replays reales.
    """
    created = []
    round_counter = 0
    for i in range(matches):
        map_name = maps[i % len(maps)]
        won_rounds = round(rounds_per_match * my_winrate)
        match = make_match(
            map_name=map_name,
            index=i,
            my_score=won_rounds,
            opponent_score=rounds_per_match - won_rounds,
        )
        for n in range(rounds_per_match):
            side = "Attack" if n % 2 == 0 else "Defense"
            won = n < won_rounds
            rnd = make_round(match, n, side=side, won=won)
            opening_kill = (round_counter % 2 == 0) and (
                (round_counter / 2) % (1 / max(opening_win_ratio, 0.01)) < 1
            )
            make_round_player(
                rnd,
                side=side,
                kills=1 if round_counter % 2 == 0 else 0,
                headshots=1 if round_counter % max(int(1 / max(hs_ratio, 0.01)), 1) == 0 else 0,
                died=True,
                opening_kill=opening_kill,
                opening_death=not opening_kill and round_counter % 3 == 0,
                was_traded=round_counter % max(int(1 / max(traded_ratio, 0.01)), 1) == 0,
                death_elapsed=40.0 + (round_counter % 5) * 10,
                operator="Zofia" if side == "Attack" else "Mute",
            )
            # un compañero y un rival, para probar sinergia y scoreboard
            make_round_player(
                rnd,
                username="companero",
                is_me=False,
                side=side,
                team_index=0,
                kills=1,
                died=False,
                death_elapsed=None,
            )
            make_round_player(
                rnd,
                username="rival",
                is_me=False,
                side="Defense" if side == "Attack" else "Attack",
                team_index=1,
                kills=1,
                died=True,
                won=not won,
                death_elapsed=50.0,
            )
            round_counter += 1
        created.append(match)
    return created
