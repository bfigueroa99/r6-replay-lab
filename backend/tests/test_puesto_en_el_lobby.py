"""Puesto en el lobby: tu rating en cada partida contra el de los demas."""

from __future__ import annotations

from django.test import TestCase

from replays.analytics import aggregates as agg
from replays.models import Match

from .factories import ME, make_match, make_round, make_round_player


def partida(kills: dict[str, int], *, rivales: tuple[str, ...] = (), index: int = 0,
            map_name: str = "Club House", rondas: int = 2, side: str = "Attack"):
    """Una partida con los jugadores de `kills` (nick -> bajas por ronda).

    Todos mueren en todas las rondas y nadie abre: los puntos solo cambian por
    las bajas, asi el orden del rating es el de `kills`. Los nicks de
    `rivales` van al otro equipo; el resto juega con vos.
    """
    match = make_match(map_name=map_name, index=index)
    for n in range(rondas):
        rnd = make_round(match, n, side=side)
        for nick, k in kills.items():
            rival = nick in rivales
            make_round_player(
                rnd,
                username=nick,
                is_me=nick == ME,
                kills=k,
                team_index=1 if rival else 0,
                side=("Defense" if side == "Attack" else "Attack") if rival else side,
            )
    return match


def diez(yo: int, companeros: list[int], rivales: list[int], **kwargs):
    kills = {ME: yo}
    kills.update({f"Comp{i}": k for i, k in enumerate(companeros)})
    kills.update({f"Rival{i}": k for i, k in enumerate(rivales)})
    return partida(kills, rivales=tuple(f"Rival{i}" for i in range(len(rivales))), **kwargs)


def conteos(data: dict) -> tuple:
    return tuple(
        (data[k]["count"], data[k]["matches"])
        for k in ("best_in_lobby", "best_in_team", "last_in_lobby")
    )


class PuestoEnElLobbyTests(TestCase):
    def test_mejor_de_la_partida_y_de_tu_equipo(self):
        diez(5, [1, 2, 3, 0], [1, 2, 3, 4, 0])
        data = agg.lobby_rank()
        self.assertEqual(conteos(data), ((1, 1), (1, 1), (0, 1)))
        self.assertEqual(data["best_in_lobby"]["pct"], 100.0)

    def test_mejor_de_tu_equipo_sin_ser_mejor_de_la_partida(self):
        diez(3, [1, 2, 0, 0], [4, 1, 1, 1, 1])
        self.assertEqual(conteos(agg.lobby_rank()), ((0, 1), (1, 1), (0, 1)))

    def test_ultimo_de_la_partida(self):
        diez(0, [1, 1, 1, 1], [1, 2, 3, 4, 5])
        data = agg.lobby_rank()
        self.assertEqual(conteos(data), ((0, 1), (0, 1), (1, 1)))
        self.assertEqual(data["best_in_lobby"]["pct"], 0.0)

    def test_empatar_con_el_mejor_cuenta_como_mejor(self):
        diez(4, [4, 1, 1, 1], [4, 1, 1, 1, 1])
        self.assertEqual(conteos(agg.lobby_rank()), ((1, 1), (1, 1), (0, 1)))

    def test_empatar_con_todos_es_mejor_y_ultimo(self):
        partida({ME: 2, "Rival0": 2}, rivales=("Rival0",))
        self.assertEqual(conteos(agg.lobby_rank()), ((1, 1), (0, 0), (1, 1)))

    def test_partida_con_menos_de_diez_entra_con_los_que_hay(self):
        partida({ME: 2, "Comp0": 1, "Rival0": 3}, rivales=("Rival0",))
        self.assertEqual(conteos(agg.lobby_rank()), ((0, 1), (1, 1), (0, 1)))

    def test_partida_solo_con_vos_no_cuenta(self):
        partida({ME: 3})
        data = agg.lobby_rank()
        self.assertEqual(conteos(data), ((0, 0), (0, 0), (0, 0)))
        for caso in data.values():
            self.assertIsNone(caso["pct"])

    def test_sin_companeros_no_entra_en_mejor_de_tu_equipo(self):
        partida({ME: 3, "Rival0": 1}, rivales=("Rival0",))
        self.assertEqual(conteos(agg.lobby_rank()), ((1, 1), (0, 0), (0, 1)))

    def test_filtro_de_mapa_aplica(self):
        diez(5, [1, 1, 1, 1], [1, 1, 1, 1, 1], index=0, map_name="Club House")
        diez(0, [1, 1, 1, 1], [1, 1, 1, 1, 1], index=1, map_name="Border")
        self.assertEqual(conteos(agg.lobby_rank()), ((1, 2), (1, 2), (1, 2)))
        self.assertEqual(conteos(agg.lobby_rank(map="border")), ((0, 1), (0, 1), (1, 1)))

    def test_filtro_de_lado_recorta_las_rondas_de_todos(self):
        # En ataque ganas por poco; en defensa un rival te pasa por mucho.
        partida({ME: 2, "Comp0": 1, "Rival0": 1}, rivales=("Rival0",), side="Attack")
        match = Match.objects.get()
        for n in range(10, 12):
            rnd = make_round(match, n, side="Defense")
            make_round_player(rnd, username=ME, side="Defense", kills=0)
            make_round_player(rnd, username="Comp0", is_me=False, side="Defense", kills=0)
            make_round_player(rnd, username="Rival0", is_me=False, team_index=1,
                              side="Attack", kills=5)
        self.assertEqual(conteos(agg.lobby_rank()), ((0, 1), (1, 1), (0, 1)))
        self.assertEqual(conteos(agg.lobby_rank(side="Attack")), ((1, 1), (1, 1), (0, 1)))

    def test_un_rival_que_te_supera_no_te_quita_el_mejor_de_tu_equipo(self):
        partida({ME: 2, "Comp0": 1, "Rival0": 4}, rivales=("Rival0",))
        self.assertEqual(agg.lobby_rank()["best_in_team"]["count"], 1)

    def test_consultas_acotadas(self):
        for i in range(2):
            diez(i, [1, 1, 1, 1], [1, 1, 1, 1, 1], index=i)
        with self.assertNumQueries(3):
            agg.lobby_rank()
        for i in range(2, 5):
            diez(i, [1, 1, 1, 1], [1, 1, 1, 1, 1], index=i)
        with self.assertNumQueries(3):
            agg.lobby_rank()

    def test_trends_trae_lobby_rank(self):
        data = self.client.get("/api/trends/").json()["lobby_rank"]
        self.assertEqual(conteos(data), ((0, 0), (0, 0), (0, 0)))
