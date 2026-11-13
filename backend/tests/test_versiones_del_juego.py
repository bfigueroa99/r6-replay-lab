"""Partidas por version del juego en Datos (ficha 124)."""

from __future__ import annotations

from datetime import datetime

from django.test import TestCase

from replays.unknowns import partidas_por_version

from .factories import make_match

URL = "/api/import/status/"


def _partida(index: int, version: str, code: int, cuando: datetime):
    match = make_match(index=index, played_at=cuando)
    match.game_version = version
    match.code_version = code
    match.save()
    return match


class PartidasPorVersionTests(TestCase):
    def test_agrupa_por_version_con_primera_y_ultima(self):
        _partida(1, "Y10S3", 20, datetime(2026, 6, 1, 20))
        _partida(2, "Y10S3", 20, datetime(2026, 6, 9, 21))
        _partida(3, "Y10S4", 30, datetime(2026, 9, 2, 22))

        filas = partidas_por_version()

        self.assertEqual([f["game_version"] for f in filas], ["Y10S4", "Y10S3"])
        self.assertEqual(filas[0]["matches"], 1)
        self.assertEqual(filas[0]["code_version"], 30)
        self.assertEqual(filas[1]["matches"], 2)
        self.assertTrue(filas[1]["first"].startswith("2026-06-01"))
        self.assertTrue(filas[1]["last"].startswith("2026-06-09"))

    def test_sin_version_va_al_final(self):
        _partida(1, "", 99, datetime(2026, 9, 5, 20))
        _partida(2, "Y10S3", 20, datetime(2026, 6, 1, 20))

        filas = partidas_por_version()

        self.assertEqual([f["game_version"] for f in filas], ["Y10S3", ""])
        self.assertEqual(filas[1]["matches"], 1)

    def test_a_igual_codigo_va_primero_la_usada_mas_tarde(self):
        _partida(1, "Y10S3.1", 20, datetime(2026, 6, 1, 20))
        _partida(2, "Y10S3.2", 20, datetime(2026, 7, 1, 20))

        filas = partidas_por_version()

        self.assertEqual([f["game_version"] for f in filas], ["Y10S3.2", "Y10S3.1"])

    def test_el_orden_del_modelo_no_parte_las_filas(self):
        _partida(1, "Y10S3", 20, datetime(2026, 6, 1, 20))
        _partida(2, "Y10S3", 20, datetime(2026, 8, 1, 20))

        filas = partidas_por_version()

        self.assertEqual(len(filas), 1)
        self.assertEqual(filas[0]["matches"], 2)

    def test_import_status_trae_versions_y_base_vacia_da_lista_vacia(self):
        vacia = self.client.get(URL)
        self.assertEqual(vacia.status_code, 200)
        self.assertEqual(vacia.json()["versions"], [])

        _partida(1, "Y10S3", 20, datetime(2026, 6, 1, 20))
        filas = self.client.get(URL).json()["versions"]
        self.assertEqual(len(filas), 1)
        self.assertEqual(filas[0]["matches"], 1)
