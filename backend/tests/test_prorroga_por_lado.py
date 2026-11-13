"""Prorroga partida por el lado de tu ronda (Tendencias, panel de mitades)."""

from __future__ import annotations

from django.test import TestCase

from replays.analytics import aggregates as agg

from .factories import make_match, make_round, make_round_player


def _partida_con_prorroga(*, index: int = 0, map_name: str = "Club House"):
    """Tres rondas normales y tres de prorroga: dos en ataque ganadas, una en defensa perdida."""
    match = make_match(index=index, map_name=map_name, my_score=5, opponent_score=4)
    for numero, lado in enumerate(["Attack", "Attack", "Defense"], start=1):
        make_round_player(make_round(match, numero, side=lado))
    prorroga = [("Attack", True), ("Attack", True), ("Defense", False)]
    for ot, (lado, gano) in enumerate(prorroga, start=1):
        make_round_player(make_round(match, 3 + ot, side=lado, won=gano, overtime_number=ot))
    return match


def _por_lado(filas: list[dict]) -> dict[str, dict]:
    return {fila["side"]: fila for fila in filas}


class ProrrogaPorLadoTests(TestCase):
    def test_parte_la_prorroga_por_lado(self):
        _partida_con_prorroga()
        filas = agg.by_overtime_side()
        self.assertEqual([f["side"] for f in filas], ["Attack", "Defense"])
        ataque, defensa = filas
        self.assertEqual((ataque["rounds"], ataque["winrate"]), (2, 100.0))
        self.assertEqual((defensa["rounds"], defensa["winrate"]), (1, 0.0))
        self.assertIsNotNone(ataque["rating"])
        self.assertIsNotNone(defensa["rating"])

    def test_las_rondas_sin_prorroga_no_entran(self):
        _partida_con_prorroga()
        filas = agg.by_overtime_side()
        # tres rondas normales (dos en ataque) quedan afuera
        self.assertEqual(sum(f["rounds"] for f in filas), 3)

    def test_by_half_no_cambia(self):
        _partida_con_prorroga()
        mitades = {f["half"]: f["rounds"] for f in agg.by_half()}
        self.assertEqual(mitades, {"first": 2, "second": 1, "overtime": 3})

    def test_by_half_no_cambia_ni_winrate_ni_rating(self):
        _partida_con_prorroga()
        filas = {f["half"]: f for f in agg.by_half()}
        winrates = {mitad: fila["winrate"] for mitad, fila in filas.items()}
        self.assertEqual(winrates, {"first": 100.0, "second": 100.0, "overtime": 66.7})
        # la fila de prorroga sigue juntando los dos lados, no es ninguna de las nuevas
        por_lado = agg.by_overtime_side()
        self.assertNotIn(filas["overtime"]["winrate"], [f["winrate"] for f in por_lado])
        self.assertTrue(all(fila["rating"] is not None for fila in filas.values()))

    def test_con_filtro_de_lado_sale_solo_ese(self):
        _partida_con_prorroga()
        data = self.client.get("/api/trends/?side=Defense").json()
        self.assertEqual([f["side"] for f in data["by_overtime_side"]], ["Defense"])
        self.assertEqual(data["by_overtime_side"][0]["rounds"], 1)

    def test_el_filtro_de_mapa_aplica(self):
        _partida_con_prorroga(index=0, map_name="Club House")
        _partida_con_prorroga(index=1, map_name="Oregon")
        data = self.client.get("/api/trends/?map=oregon").json()
        lados = _por_lado(data["by_overtime_side"])
        self.assertEqual((lados["Attack"]["rounds"], lados["Defense"]["rounds"]), (2, 1))

    def test_sin_prorroga_las_filas_salen_en_cero(self):
        match = make_match()
        make_round_player(make_round(match, 1, side="Attack"))
        filas = agg.by_overtime_side()
        self.assertEqual([(f["side"], f["rounds"]) for f in filas], [("Attack", 0), ("Defense", 0)])
        self.assertIsNone(filas[0]["winrate"])

    def test_la_api_sin_datos_devuelve_las_dos_filas_en_cero(self):
        data = self.client.get("/api/trends/").json()
        self.assertEqual([f["rounds"] for f in data["by_overtime_side"]], [0, 0])
