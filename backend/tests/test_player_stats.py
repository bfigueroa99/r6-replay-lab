"""Tests de las stats por jugador: 1vX, headshots y agregado por partida.

Sin .rec: un lector falso con la cabecera, el marcador y el feed ya armados.
`players` y `teams` se toman del `Reader` real para no copiar su logica.
"""

from __future__ import annotations

import random

from django.test import SimpleTestCase

from pydissect import Reader, stats
from pydissect.constants import DEATH, EVENT_NAMES, KILL, OPERATOR_SWAP, PLAYER_LEAVE
from replays.analytics import metrics

NOMBRES = [f"{letra}{n}" for letra in "AB" for n in range(5)]


class LectorFalso:
    players = Reader.players
    teams = Reader.teams

    def __init__(self, ganador: int | None = 0):
        self.header = {
            "players": [
                {"username": nombre, "teamIndex": i // 5} for i, nombre in enumerate(NOMBRES)
            ],
            "teams": [{"won": i == ganador} for i in range(2)],
        }
        self.match_feedback = []
        self.scoreboard = [{"score": 0, "assistsFromRound": 0} for _ in NOMBRES]


def kill(autor: str, victima: str, headshot: bool = False) -> dict:
    return {"type": KILL, "username": autor, "target": victima, "headshot": headshot}


def de(filas: list[dict], username: str) -> dict:
    return next(f for f in filas if f["username"] == username)


def con_1vx(filas: list[dict]) -> dict[str, int]:
    return {f["username"]: f["1vX"] for f in filas if f["1vX"]}


class PlayerRoundStatsTests(SimpleTestCase):
    def test_un_teamkill_suma_a_las_bajas_del_autor(self):
        # El parser sigue a r6-dissect y cuenta el teamkill; la app los saca en
        # `metrics.bajas_a_rivales` (ficha 67, test_metrics).
        r = LectorFalso(ganador=0)
        r.match_feedback = [kill("A0", "A1"), kill("A0", "B0")]
        self.assertEqual(de(stats.player_round_stats(r), "A0")["kills"], 2)

    def test_sin_bajas_en_el_ganador_no_hay_1vx(self):
        r = LectorFalso(ganador=0)
        r.match_feedback = [kill("A0", f"B{n}") for n in range(5)]
        self.assertEqual(con_1vx(stats.player_round_stats(r)), {})

    def test_ultimo_vivo_que_gana_suma_sus_kills_y_los_rivales_vivos(self):
        r = LectorFalso(ganador=1)
        r.match_feedback = [kill("A0", f"B{n}") for n in range(4)]
        r.match_feedback += [kill("B4", f"A{n}") for n in range(3)]
        filas = stats.player_round_stats(r)

        # 3 kills con el equipo ya reducido a el, mas A3 y A4 vivos
        self.assertEqual(con_1vx(filas), {"B4": 5})
        self.assertEqual(de(filas, "B4")["kills"], 3)
        self.assertIs(de(filas, "B4")["died"], False)

    def test_las_kills_antes_de_quedar_solo_no_cuentan_para_el_1vx(self):
        r = LectorFalso(ganador=1)
        r.match_feedback = [kill("B4", "A0")]
        r.match_feedback += [kill("A1", f"B{n}") for n in range(4)]
        r.match_feedback.append(kill("B4", "A2"))

        # solo la kill a A2 llega con B4 solo, mas A1, A3 y A4 vivos
        self.assertEqual(con_1vx(stats.player_round_stats(r)), {"B4": 4})

    def test_la_kill_con_un_companero_vivo_no_cuenta_para_el_1vx(self):
        r = LectorFalso(ganador=1)
        r.match_feedback = [kill("A1", f"B{n}") for n in range(3)]
        r.match_feedback.append(kill("B4", "A0"))
        r.match_feedback += [kill("A1", "B3"), kill("B4", "A1")]
        filas = stats.player_round_stats(r)

        # la kill a A0 llega con B3 todavia vivo: solo cuenta la de A1, mas A2..A4
        self.assertEqual(con_1vx(filas), {"B4": 4})
        self.assertEqual(de(filas, "B4")["kills"], 2)

    def test_un_companero_muerto_sin_asesino_tambien_deja_solo_al_clutcher(self):
        r = LectorFalso(ganador=1)
        r.match_feedback = [kill("A0", f"B{n}") for n in range(3)]
        r.match_feedback.append({"type": DEATH, "username": "B3"})
        r.match_feedback += [kill("B4", f"A{n}") for n in range(5)]

        # B3 muere sin KILL (suicidio o caida): las 5 kills de B4 ya son con el solo
        self.assertEqual(con_1vx(stats.player_round_stats(r)), {"B4": 5})

    def test_uno_contra_uno_ganado_vale_uno(self):
        r = LectorFalso(ganador=0)
        r.match_feedback = [kill("A0", f"B{n}") for n in range(4)]
        r.match_feedback += [kill("B4", f"A{n}") for n in range(4)]
        r.match_feedback.append(kill("A4", "B4"))
        self.assertEqual(con_1vx(stats.player_round_stats(r)), {"A4": 1})

    def test_el_ultimo_del_ganador_que_muere_igual_cobra_el_1vx(self):
        # ronda ganada por plant: el ultimo atacante muere pero su equipo gana
        r = LectorFalso(ganador=0)
        r.match_feedback = [kill("B0", f"A{n}") for n in range(4)]
        r.match_feedback += [kill("A4", "B0"), kill("B1", "A4")]
        filas = stats.player_round_stats(r)

        # 1 kill mas B1..B4 vivos
        self.assertEqual(con_1vx(filas), {"A4": 5})
        self.assertIs(de(filas, "A4")["died"], True)

    def test_porcentaje_de_headshots_por_ronda(self):
        r = LectorFalso()
        r.match_feedback = [kill("A0", "B0", headshot=True), kill("A0", "B1")]
        filas = stats.player_round_stats(r)

        self.assertEqual(de(filas, "A0")["headshotPercentage"], 50.0)

    def test_porcentaje_de_headshots_sin_kills_no_divide_por_cero(self):
        self.assertEqual(stats.headshot_percentage(0, 0), 0.0)

    def test_las_asistencias_salen_del_marcador(self):
        r = LectorFalso()
        r.scoreboard[0]["assistsFromRound"] = 2
        self.assertEqual(de(stats.player_round_stats(r), "A0")["assists"], 2)


def planos(feed: list[dict]) -> list[dict]:
    """El feed del parser como lo guarda `Event`: nombre del tipo, autor y victima."""
    return [
        {"kind": EVENT_NAMES[u["type"]], "actor": u.get("username", ""),
         "target": u.get("target", "")}
        for u in feed
    ]


class OneVxParidadTests(SimpleTestCase):
    """`metrics.one_vx` es el 1vX de r6-dissect salvo con abandonos (ficha 69)."""

    def test_sin_abandonos_da_lo_mismo_que_el_parser(self):
        azar = random.Random(69)
        diferencias = []
        con_1vx_mayor_a_cero = 0
        for _ in range(3000):
            ganador = azar.choice([0, 1, None])
            r = LectorFalso(ganador=ganador)
            feed = []
            for _ in range(azar.randint(0, 14)):
                tirada = azar.random()
                if tirada < 0.75:
                    autor, victima = azar.choice(NOMBRES), azar.choice(NOMBRES)
                    feed.append(kill(autor, victima))
                    if azar.random() < 0.1:
                        # la misma baja dos veces sobre el mismo jugador
                        feed.append(kill(autor, victima))
                elif tirada < 0.9:
                    feed.append({"type": DEATH, "username": azar.choice([*NOMBRES, "nadie"])})
                else:
                    feed.append({"type": OPERATOR_SWAP, "username": azar.choice(NOMBRES)})
            r.match_feedback = feed

            parser = {f["username"]: f["1vX"] for f in stats.player_round_stats(r)}
            team_of = {p["username"]: p["teamIndex"] for p in r.players}
            app = metrics.one_vx(planos(feed), team_of, metrics.equipo_ganador(r.teams))
            if app != parser:
                diferencias.append((ganador, feed, parser, app))
            con_1vx_mayor_a_cero += any(parser.values())

        self.assertEqual(diferencias[:1], [])
        # que el test no pase vacio: una buena parte de las rondas tiene clutch
        self.assertGreater(con_1vx_mayor_a_cero, 300)

    def test_el_parser_sigue_contando_al_que_se_fue_como_vivo(self):
        # el parser sigue a r6-dissect; sacar al que se fue lo decide la app
        r = LectorFalso(ganador=0)
        r.match_feedback = (
            [kill(f"A{n}", f"B{n}") for n in range(3)]
            + [kill("B3", f"A{n}") for n in range(3)]
            + [{"type": PLAYER_LEAVE, "username": "A3"}, kill("A4", "B3"), kill("A4", "B4")]
        )
        self.assertEqual(con_1vx(stats.player_round_stats(r)), {})


class PlayerMatchStatsTests(SimpleTestCase):
    def test_agregado_de_dos_rondas(self):
        r1 = LectorFalso()
        r1.match_feedback = [kill("A0", "B0", headshot=True)]
        r2 = LectorFalso()
        r2.match_feedback = [kill("A0", f"B{n}") for n in range(3)]
        rondas = [stats.player_round_stats(r) for r in (r1, r2)]
        a0 = de(stats.player_match_stats(rondas), "A0")

        self.assertEqual(a0["rounds"], 2)
        self.assertEqual(a0["kills"], 4)
        self.assertEqual(a0["headshots"], 1)
        # sobre el total de kills, no el promedio de las rondas (que daria 50)
        self.assertEqual(a0["headshotPercentage"], 25.0)
        self.assertEqual(a0["deaths"], 0)

    def test_agregado_cuenta_muertes_y_asistencias(self):
        base = {"username": "A0", "teamIndex": 0, "kills": 0, "headshots": 0}
        rondas = [
            [{**base, "died": True, "assists": 1}],
            [{**base, "died": False, "assists": 2}],
        ]
        a0 = de(stats.player_match_stats(rondas), "A0")

        self.assertEqual(a0["deaths"], 1)
        self.assertEqual(a0["assists"], 3)
