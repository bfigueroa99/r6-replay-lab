"""Tests de quien gana la ronda (`round_end`) y del reloj del defuser.

No usan .rec: un lector falso con la cabecera y el feed ya armados. Los
accesos se toman del `Reader` real para que el test ejercite la misma logica
de indices y propiedades, y no una copia que pueda divergir.
"""

from __future__ import annotations

from django.test import SimpleTestCase

from pydissect import Reader, events
from pydissect.constants import (
    ATTACK,
    BOMB,
    DEATH,
    DEFENSE,
    DEFUSED_BOMB,
    DEFUSER_DISABLE_COMPLETE,
    DEFUSER_DISABLE_START,
    DEFUSER_PLANT_COMPLETE,
    DEFUSER_PLANT_START,
    DISABLED_DEFUSER,
    KILL,
    KILLED_OPPONENTS,
    TIME,
    Y9S3,
    Y9S4,
)


def dissect_id(nombre: str) -> bytes:
    equipo = 0 if nombre[0] == "A" else 1
    return bytes([equipo, int(nombre[1:]), 0, 0])


class LectorFalso:
    players = Reader.players
    teams = Reader.teams
    code_version = Reader.code_version
    player_index_by_id = Reader.player_index_by_id
    player_index_by_username = Reader.player_index_by_username
    skip = Reader.skip
    bytes = Reader.bytes
    int = Reader.int
    string = Reader.string

    def __init__(self, version=Y9S3, roles=(ATTACK, DEFENSE), score=(0, 0), telemetria=b""):
        jugadores = [
            {"username": f"{letra}{n}", "teamIndex": equipo, "dissectID": dissect_id(f"{letra}{n}")}
            for equipo, letra in enumerate("AB")
            for n in range(5)
        ]
        equipos = [
            {"role": rol, "startingScore": 0, "score": puntos, "won": False, "winCondition": ""}
            for rol, puntos in zip(roles, score, strict=True)
        ]
        self.header = {
            "codeVersion": version,
            "gamemode": BOMB,
            "players": jugadores,
            "teams": equipos,
        }
        self.match_feedback = []
        self.time = 0.0
        self.time_raw = ""
        self.planted = False
        self.last_defuser_player_index = -1
        self.b = telemetria
        self.offset = 0


def kill(autor: str, victima: str, **extra) -> dict:
    return {"type": KILL, "username": autor, "target": victima, **extra}


def resultado(r: LectorFalso) -> list[tuple[bool, str]]:
    return [(t["won"], t["winCondition"]) for t in r.teams]


class RoundEndTests(SimpleTestCase):
    def test_previo_y9s4_cinco_muertes_da_la_ronda_al_rival_por_eliminacion(self):
        r = LectorFalso()
        r.match_feedback = [kill("B0", f"A{n}") for n in range(5)]
        events.round_end(r)
        self.assertEqual(resultado(r), [(False, ""), (True, KILLED_OPPONENTS)])

    def test_previo_y9s4_muertes_por_death_tambien_cuentan(self):
        r = LectorFalso()
        r.match_feedback = [{"type": DEATH, "username": f"A{n}"} for n in range(5)]
        events.round_end(r)
        self.assertEqual(resultado(r), [(False, ""), (True, KILLED_OPPONENTS)])

    def test_previo_y9s4_plant_sin_desactivar_gana_el_que_planto(self):
        r = LectorFalso()
        r.match_feedback = [{"type": DEFUSER_PLANT_COMPLETE, "username": "A0"}]
        events.round_end(r)
        self.assertEqual(resultado(r), [(True, DEFUSED_BOMB), (False, "")])

    def test_previo_y9s4_desactivar_despues_del_plant_gana_el_que_desactivo(self):
        r = LectorFalso()
        r.match_feedback = [
            {"type": DEFUSER_PLANT_COMPLETE, "username": "A0"},
            {"type": DEFUSER_DISABLE_COMPLETE, "username": "B0"},
        ]
        events.round_end(r)
        self.assertEqual(resultado(r), [(False, ""), (True, DISABLED_DEFUSER)])

    def test_previo_y9s4_sin_muertes_ni_defuser_gana_la_defensa_por_tiempo(self):
        # los dos ordenes de roles, para que no pase solo por ser el indice 1
        casos = [
            ((ATTACK, DEFENSE), [(False, ""), (True, TIME)]),
            ((DEFENSE, ATTACK), [(True, TIME), (False, "")]),
        ]
        for roles, esperado in casos:
            with self.subTest(roles=roles):
                r = LectorFalso(roles=roles)
                events.round_end(r)
                self.assertEqual(resultado(r), esperado)

    # En los tests de Y9S4 el feed apunta al otro equipo que el marcador: asi el
    # resultado solo puede salir del marcador y no de la logica previa a Y9S4.

    def test_y9s4_el_marcador_decide_y_la_eliminacion_da_la_condicion(self):
        # mueren los diez: antes de Y9S4 ganaria el equipo 1 por caer primero el 0
        r = LectorFalso(version=Y9S4, score=(1, 0))
        r.match_feedback = [kill("B0", f"A{n}") for n in range(5)]
        r.match_feedback += [{"type": DEATH, "username": f"B{n}"} for n in range(5)]
        events.round_end(r)
        self.assertEqual(resultado(r), [(True, KILLED_OPPONENTS), (False, "")])

    def test_y9s4_sin_eliminacion_la_condicion_es_tiempo(self):
        # antes de Y9S4 ganaria la defensa (equipo 1) por tiempo
        r = LectorFalso(version=Y9S4, roles=(ATTACK, DEFENSE), score=(1, 0))
        events.round_end(r)
        self.assertEqual(resultado(r), [(True, TIME), (False, "")])

    def test_y9s4_el_marcador_gana_aunque_el_feed_diga_eliminacion(self):
        r = LectorFalso(version=Y9S4, roles=(ATTACK, DEFENSE), score=(1, 0))
        r.match_feedback = [kill("B0", f"A{n}") for n in range(5)]
        events.round_end(r)
        self.assertEqual(resultado(r), [(True, TIME), (False, "")])

    def test_kill_corregida_por_el_marcador_toma_el_autor_del_marcador(self):
        r = LectorFalso()
        r.match_feedback = [kill("B0", "A0", usernameFromScoreboard="B1")]
        events.round_end(r)
        self.assertEqual(r.match_feedback[0]["username"], "B1")


def bloque_timer(timer: bytes, autor_id: bytes) -> bytes:
    return bytes([len(timer)]) + timer + b"\0" * 34 + autor_id


def feed(r: LectorFalso) -> list[tuple[int, str]]:
    return [(u["type"], u["username"]) for u in r.match_feedback]


class DefuserTimerTests(SimpleTestCase):
    def test_defuser_plant_y_despues_desactivar(self):
        telemetria = (
            bloque_timer(b"7.00", dissect_id("A0"))
            + bloque_timer(b"0.00", dissect_id("A0"))
            + bloque_timer(b"7.00", dissect_id("B1"))
            + bloque_timer(b"0.00", dissect_id("B1"))
            # Reader.skip corta con EndOfFile si el offset llega justo al final
            + b"\0"
        )
        r = LectorFalso(telemetria=telemetria)

        events.read_defuser_timer(r)
        events.read_defuser_timer(r)
        # cada lectura del timer agrega un START, por eso son dos antes del COMPLETE
        self.assertEqual(
            feed(r),
            [
                (DEFUSER_PLANT_START, "A0"),
                (DEFUSER_PLANT_START, "A0"),
                (DEFUSER_PLANT_COMPLETE, "A0"),
            ],
        )
        self.assertIs(r.planted, True)

        events.read_defuser_timer(r)
        events.read_defuser_timer(r)
        self.assertEqual(
            feed(r)[3:],
            [
                (DEFUSER_DISABLE_START, "B1"),
                (DEFUSER_DISABLE_START, "B1"),
                (DEFUSER_DISABLE_COMPLETE, "B1"),
            ],
        )

    def test_defuser_con_id_desconocido_no_agrega_eventos(self):
        r = LectorFalso(telemetria=bloque_timer(b"0.00", bytes([9, 9, 9, 9])) + b"\0")
        events.read_defuser_timer(r)
        self.assertEqual(r.match_feedback, [])
        # el plant existio aunque el autor no se pueda atribuir
        self.assertIs(r.planted, True)
