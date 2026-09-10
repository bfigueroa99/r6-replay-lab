"""Tests del parser: se construyen .rec sinteticos byte a byte.

Asi se cubre el formato sin tener que meter un replay de 7 MB al repo. Si
apuntas la variable de entorno ``R6_TEST_REPLAY`` a un .rec real, el ultimo
test tambien corre contra ese archivo.
"""

from __future__ import annotations

import os
from pathlib import Path

import zstandard
from django.test import SimpleTestCase

from pydissect import Reader, stats
from pydissect.errors import InvalidFile
from pydissect.header import map_name, map_slug, operator_label, operator_side
from pydissect.reader import _decompress_chunks

HEADER_PREFIX = b"dissect" + b"\x00" * 7 + b"X" + b"\x00" * 7


def kv(key: str, value: str) -> bytes:
    """Un par clave/valor en el formato de la cabecera: [len][7x00][datos]."""
    out = b""
    for text in (key, value):
        raw = text.encode("utf-8")
        out += bytes([len(raw)]) + b"\x00" * 7 + raw
    return out


def build_header(props: dict[str, str], players: list[dict[str, str]]) -> bytes:
    """Arma una cabecera valida; `teamscore1` va al final porque cierra el loop."""
    body = HEADER_PREFIX
    for key, value in props.items():
        if key == "teamscore1":
            continue
        body += kv(key, value)
    for player in players:
        for key, value in player.items():
            body += kv(key, value)
    body += kv("id", props.get("id", "match-sintetico"))
    body += kv("teamscore1", props["teamscore1"])
    return body


DEFAULT_PROPS = {
    "version": "Y11S3_Test",
    "code": "9883691",
    "datetime": "2026-09-09-17-20-05",
    "matchtype": "2",
    "worldid": "407193663917",  # Club House
    "recordingplayerid": "12078186691623074564",
    "recordingprofileid": "afd4bfe2-0e37-40df-9029-2e6c65ebf62c",
    "additionaltags": "0",
    "gamemodeid": "327933806",
    "roundspermatch": "9",
    "roundspermatchovertime": "6",
    "roundnumber": "3",
    "overtimeroundnumber": "0",
    "playlistcategory": "2",
    "id": "abc-123",
    "teamname0": "ENEMY TEAM",
    "teamname1": "YOUR TEAM",
    "startingteamscore0": "1",
    "startingteamscore1": "2",
    "teamscore0": "1",
    "teamscore1": "3",
}

DEFAULT_PLAYERS = [
    {
        "playerid": "7547976154654522721",
        "profileid": "c6540b82-75d9-4679-ae75-852b534cc57f",
        "playername": "IrlanMoura",
        "team": "1",
        "heroname": "38576459494",
        "alliance": "4",
        "roleimage": "39149215517",
        "rolename": "LESION",
        "roleportrait": "39149215541",
    },
    {
        "playerid": "12366722704894588553",
        "profileid": "aa39147d-9a0a-43b6-83cf-e0fff38bbcf7",
        "playername": "Yotsumura",
        "team": "0",
        "heroname": "1",
        "alliance": "4",
        "roleimage": "2",
        "rolename": "NOOR",
        "roleportrait": "3",
    },
]


def build_rec(props=None, players=None, payload: bytes = b"telemetria-falsa") -> bytes:
    header = build_header({**DEFAULT_PROPS, **(props or {})}, players or DEFAULT_PLAYERS)
    frame = zstandard.ZstdCompressor().compress(payload)
    return header + frame


class DecompressionTests(SimpleTestCase):
    def test_concatena_varios_frames(self):
        c = zstandard.ZstdCompressor()
        raw = b"basura-inicial" + c.compress(b"uno-") + c.compress(b"dos-") + c.compress(b"tres")
        self.assertEqual(_decompress_chunks(raw, len(b"basura-inicial")), b"uno-dos-tres")

    def test_ignora_la_cola_no_comprimida(self):
        raw = zstandard.ZstdCompressor().compress(b"contenido") + b"\x00cola sin comprimir"
        self.assertEqual(_decompress_chunks(raw, 0), b"contenido")

    def test_sin_frames_devuelve_vacio(self):
        self.assertEqual(_decompress_chunks(b"nada de zstd aqui", 0), b"")


class HeaderTests(SimpleTestCase):
    def setUp(self):
        self.reader = Reader(build_rec())

    def test_archivo_invalido(self):
        with self.assertRaises(InvalidFile):
            Reader(b"esto no es un replay")

    def test_metadata(self):
        h = self.reader.header
        self.assertEqual(h["gameVersion"], "Y11S3_Test")
        self.assertEqual(h["codeVersion"], 9883691)
        self.assertEqual(h["timestamp"].isoformat(), "2026-09-09T17:20:05")
        self.assertEqual(h["matchType"], 2)
        self.assertEqual(h["map"], 407193663917)
        self.assertEqual(h["roundNumber"], 3)
        self.assertEqual(h["matchID"], "abc-123")
        self.assertEqual(h["recordingProfileID"], "afd4bfe2-0e37-40df-9029-2e6c65ebf62c")

    def test_equipos_y_marcador(self):
        teams = self.reader.teams
        self.assertEqual(teams[0]["name"], "ENEMY TEAM")
        self.assertEqual(teams[1]["name"], "YOUR TEAM")
        self.assertEqual([t["score"] for t in teams], [1, 3])
        self.assertEqual([t["startingScore"] for t in teams], [1, 2])

    def test_jugadores(self):
        players = self.reader.players
        self.assertEqual([p["username"] for p in players], ["IrlanMoura", "Yotsumura"])
        self.assertEqual(players[0]["teamIndex"], 1)
        self.assertEqual(players[0]["roleName"], "LESION")

    def test_telemetria_descomprimida(self):
        self.assertEqual(self.reader.b, b"telemetria-falsa")

    def test_versiones_viejas_no_traen_marcador_inicial(self):
        reader = Reader(build_rec({"code": "7408213"}))  # Y8S1
        self.assertEqual([t["startingScore"] for t in reader.teams], [0, 0])


class NameTests(SimpleTestCase):
    def test_mapa_conocido(self):
        self.assertEqual(map_name(407193663917), "Club House")
        self.assertEqual(map_slug(407193663917), "club-house")

    def test_variantes_de_temporada_comparten_slug(self):
        self.assertEqual(map_slug(837214085), map_slug(407193663917))

    def test_mapa_agregado_por_observacion(self):
        self.assertEqual(map_name(436375283234), "Coastline")

    def test_mapa_desconocido(self):
        self.assertTrue(map_name(1).startswith("Unknown("))

    def test_lado_del_operador(self):
        self.assertEqual(operator_side(92270642656), "Attack")   # Ash
        self.assertEqual(operator_side(92270642318), "Defense")  # Mute
        self.assertIsNone(operator_side(1))

    def test_operador_nuevo_usa_el_nombre_de_la_cabecera(self):
        self.assertEqual(operator_label({"operator": 456757346397, "roleName": "NOOR"}), "Noor")

    def test_operador_conocido_ignora_la_cabecera(self):
        self.assertEqual(operator_label({"operator": 92270642318, "roleName": "OTRO"}), "Mute")


class CompatTradeTests(SimpleTestCase):
    """La funcion `trades` mantiene la heuristica de r6-dissect."""

    class FakeReader:
        def __init__(self, feedback):
            self.match_feedback = feedback

    def test_par_de_kills_consecutivas(self):
        feedback = [
            {"type": 0, "username": "a", "target": "b", "timeInSeconds": 100.0, "time": "1:40"},
            {"type": 0, "username": "c", "target": "a", "timeInSeconds": 98.0, "time": "1:38"},
        ]
        result = stats.trades(self.FakeReader(feedback))
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0][1]["username"], "c")


class RealReplayTests(SimpleTestCase):
    """Corre solo si R6_TEST_REPLAY apunta a un .rec de verdad."""

    def setUp(self):
        path = os.environ.get("R6_TEST_REPLAY", "")
        if not path or not Path(path).exists():
            self.skipTest("define R6_TEST_REPLAY con la ruta de un .rec para correr este test")
        self.path = Path(path)

    def test_parsea_una_ronda_completa(self):
        reader = Reader.from_path(self.path)
        reader.read()
        self.assertTrue(reader.header["matchID"])
        self.assertGreaterEqual(len(reader.players), 2)
        self.assertTrue(all(p["username"] for p in reader.players))
        roles = {t["role"] for t in reader.teams}
        self.assertIn("Attack", roles)
        self.assertIn("Defense", roles)
        self.assertGreater(reader.clock_max, 0)
        for update in reader.match_feedback:
            self.assertIn("timeInSeconds", update)
