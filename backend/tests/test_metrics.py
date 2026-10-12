"""Tests de las metricas derivadas por ronda."""

from __future__ import annotations

from django.test import SimpleTestCase

from replays.analytics.metrics import analyse_round


def _kill(order: int, actor: str, target: str, clock: float, headshot: bool = False) -> dict:
    return {
        "type": {"id": 0, "name": "Kill"},
        "username": actor,
        "target": target,
        "headshot": headshot,
        "time": f"{int(clock) // 60}:{int(clock) % 60:02d}",
        "timeInSeconds": clock,
    }


def _round(events, *, won_team=0, stats=None, clock_start=180.0, clock_end=20.0, mode="Bomb",
           extra_players=None):
    """Ronda sintetica: 2 atacantes en el equipo 0, 2 defensores en el 1, mas `extra_players`."""
    players = [
        {"username": "atk1", "teamIndex": 0, "operator": {"id": 1, "name": "Ash"}, "spawn": "Main", "profileID": "p-atk1"},
        {"username": "atk2", "teamIndex": 0, "operator": {"id": 2, "name": "Thermite"}, "spawn": "Main", "profileID": "p-atk2"},
        {"username": "def1", "teamIndex": 1, "operator": {"id": 3, "name": "Mute"}, "spawn": "Site", "profileID": "p-def1"},
        {"username": "def2", "teamIndex": 1, "operator": {"id": 4, "name": "Rook"}, "spawn": "Site", "profileID": "p-def2"},
        *(extra_players or []),
    ]
    default_stats = [
        {"username": p["username"], "kills": 0, "died": False, "headshots": 0, "assists": 0,
         "score": 0, "1vX": 0, "teamIndex": p["teamIndex"]}
        for p in players
    ]
    return {
        "gamemode": {"id": 327933806, "name": mode},
        "clockStart": clock_start,
        "clockEnd": clock_end,
        "teams": [
            {"name": "A", "role": "Attack", "won": won_team == 0, "score": 1, "startingScore": 0},
            {"name": "B", "role": "Defense", "won": won_team == 1, "score": 0, "startingScore": 0},
        ],
        "players": players,
        "matchFeedback": events,
        "stats": stats or default_stats,
    }


class OpeningDuelTests(SimpleTestCase):
    def test_primera_baja_marca_apertura(self):
        data = _round([_kill(0, "atk1", "def1", 150.0)])
        result = analyse_round(data)
        self.assertTrue(result["players"]["atk1"]["opening_kill"])
        self.assertTrue(result["players"]["def1"]["opening_death"])
        self.assertFalse(result["players"]["atk2"]["opening_kill"])

    def test_entry_kill_es_la_primera_de_cada_equipo(self):
        data = _round(
            [
                _kill(0, "atk1", "def1", 150.0),
                _kill(1, "def2", "atk2", 140.0),
                _kill(2, "atk1", "def2", 130.0),
            ]
        )
        result = analyse_round(data)
        self.assertTrue(result["players"]["atk1"]["entry_kill"])
        self.assertTrue(result["players"]["def2"]["entry_kill"])
        self.assertFalse(result["players"]["atk2"]["entry_kill"])

    def test_muerte_sin_asesino_tambien_cuenta_como_apertura(self):
        death = {
            "type": {"id": 1, "name": "Death"},
            "username": "atk1",
            "time": "2:00",
            "timeInSeconds": 120.0,
        }
        result = analyse_round(_round([death]))
        self.assertTrue(result["players"]["atk1"]["opening_death"])


class TradeTests(SimpleTestCase):
    def test_trade_dentro_de_la_ventana(self):
        data = _round(
            [
                _kill(0, "def1", "atk1", 150.0),  # def1 mata a atk1
                _kill(1, "atk2", "def1", 148.0),  # atk2 lo venga 2s despues
            ]
        )
        result = analyse_round(data)
        self.assertTrue(result["players"]["atk1"]["was_traded"])
        self.assertFalse(result["players"]["atk1"]["untraded_death"])
        self.assertEqual(result["players"]["atk2"]["trade_kills"], 1)
        self.assertTrue(result["events"][0]["traded"])

    def test_fuera_de_la_ventana_no_es_trade(self):
        data = _round(
            [
                _kill(0, "def1", "atk1", 150.0),
                _kill(1, "atk2", "def1", 140.0),  # 10s despues
            ]
        )
        result = analyse_round(data)
        self.assertFalse(result["players"]["atk1"]["was_traded"])
        self.assertTrue(result["players"]["atk1"]["untraded_death"])
        self.assertEqual(result["players"]["atk2"]["trade_kills"], 0)

    def test_venganza_de_un_rival_no_es_trade(self):
        # def2 mata a def1 no tiene sentido; usamos un rival matando al asesino
        data = _round(
            [
                _kill(0, "def1", "atk1", 150.0),
                _kill(1, "def2", "atk2", 149.0),  # no mata al asesino
            ]
        )
        result = analyse_round(data)
        self.assertFalse(result["players"]["atk1"]["was_traded"])

    def test_una_baja_que_venga_a_dos_companeros_cuenta_una_vez(self):
        data = _round(
            [
                _kill(0, "def1", "atk1", 150.0),
                _kill(1, "def1", "atk2", 149.0),  # doble de def1
                _kill(2, "atk3", "def1", 148.0),  # una sola baja venga a los dos
            ],
            extra_players=[_atacante("atk3")],
        )
        result = analyse_round(data)
        self.assertEqual(result["players"]["atk3"]["trade_kills"], 1)
        self.assertTrue(result["players"]["atk1"]["was_traded"])
        self.assertTrue(result["players"]["atk2"]["was_traded"])
        self.assertTrue(result["events"][0]["traded"])
        self.assertTrue(result["events"][1]["traded"])

    def test_dos_venganzas_sobre_dos_asesinos_suman_dos(self):
        data = _round(
            [
                _kill(0, "def1", "atk1", 150.0),
                _kill(1, "atk3", "def1", 149.0),
                _kill(2, "def2", "atk2", 140.0),
                _kill(3, "atk3", "def2", 139.0),
            ],
            extra_players=[_atacante("atk3")],
        )
        result = analyse_round(data)
        self.assertEqual(result["players"]["atk3"]["trade_kills"], 2)

    def test_trade_kills_nunca_supera_a_kills(self):
        doble = (
            [_atacante("atk3")],
            [
                _kill(0, "def1", "atk1", 150.0),
                _kill(1, "def1", "atk2", 149.0),
                _kill(2, "atk3", "def1", 148.0),
            ],
        )
        triple = (
            [_atacante("atk3"), _atacante("atk4")],
            [
                _kill(0, "def1", "atk1", 150.0),
                _kill(1, "def1", "atk2", 149.0),
                _kill(2, "def1", "atk3", 148.0),
                _kill(3, "atk4", "def1", 147.0),
            ],
        )
        for nombre, (extra, events) in {"doble": doble, "triple": triple}.items():
            with self.subTest(nombre):
                data = _round(events, extra_players=extra, stats=_stats_del_guion(extra, events))
                result = analyse_round(data)
                for username, m in result["players"].items():
                    self.assertLessEqual(m["trade_kills"], m["kills"], username)
                if nombre == "triple":
                    self.assertEqual(result["players"]["atk4"]["trade_kills"], 1)


def _atacante(username: str) -> dict:
    return {"username": username, "teamIndex": 0, "operator": {"id": 5, "name": "Sledge"},
            "spawn": "Main", "profileID": f"p-{username}"}


def _stats_del_guion(extra_players: list[dict], events: list[dict]) -> list[dict]:
    """Stats coherentes con el kill feed: `analyse_round` saca `kills` de aca, no de los eventos."""
    nombres = ["atk1", "atk2", "def1", "def2", *(p["username"] for p in extra_players)]
    equipo = {"atk1": 0, "atk2": 0, "def1": 1, "def2": 1, **{p["username"]: 0 for p in extra_players}}
    return [
        {"username": n, "kills": sum(e["username"] == n for e in events),
         "died": any(e["target"] == n for e in events), "headshots": 0, "assists": 0,
         "score": 0, "1vX": 0, "teamIndex": equipo[n]}
        for n in nombres
    ]


class KstTests(SimpleTestCase):
    def test_sobrevivir_cuenta_como_aporte(self):
        result = analyse_round(_round([]))
        self.assertTrue(result["players"]["atk1"]["kst"])
        self.assertTrue(result["players"]["atk1"]["survived"])

    def test_morir_sin_matar_ni_trade_no_aporta(self):
        data = _round([_kill(0, "def1", "atk1", 100.0)])
        result = analyse_round(data)
        self.assertFalse(result["players"]["atk1"]["kst"])
        self.assertTrue(result["players"]["def1"]["kst"])

    def test_momento_de_la_muerte(self):
        data = _round([_kill(0, "def1", "atk1", 120.0)], clock_start=180.0)
        result = analyse_round(data)
        self.assertEqual(result["players"]["atk1"]["death_clock"], 120.0)
        self.assertEqual(result["players"]["atk1"]["death_elapsed"], 60.0)


class WinConditionTests(SimpleTestCase):
    def test_barrida_es_certera(self):
        stats = [
            {"username": "atk1", "kills": 2, "died": False, "headshots": 1, "assists": 0, "score": 0, "1vX": 0, "teamIndex": 0},
            {"username": "atk2", "kills": 0, "died": False, "headshots": 0, "assists": 0, "score": 0, "1vX": 0, "teamIndex": 0},
            {"username": "def1", "kills": 0, "died": True, "headshots": 0, "assists": 0, "score": 0, "1vX": 0, "teamIndex": 1},
            {"username": "def2", "kills": 0, "died": True, "headshots": 0, "assists": 0, "score": 0, "1vX": 0, "teamIndex": 1},
        ]
        data = _round(
            [_kill(0, "atk1", "def1", 150.0), _kill(1, "atk1", "def2", 140.0)],
            won_team=0,
            stats=stats,
        )
        result = analyse_round(data)
        self.assertEqual(result["win_condition"], "KilledOpponents")
        self.assertTrue(result["win_condition_certain"])
        self.assertFalse(result["possible_plant"])

    def test_sin_barrida_queda_como_objetivo_o_tiempo(self):
        data = _round([_kill(0, "atk1", "def1", 150.0)], won_team=0, clock_end=70.0)
        result = analyse_round(data)
        self.assertEqual(result["win_condition"], "ObjectiveOrTime")
        self.assertFalse(result["win_condition_certain"])
        self.assertTrue(result["possible_plant"])

    def test_ronda_hasta_el_final_no_sugiere_plant(self):
        data = _round([_kill(0, "atk1", "def1", 150.0)], won_team=0, clock_end=1.0)
        result = analyse_round(data)
        self.assertFalse(result["possible_plant"])
