"""Resumen de partidas del Inicio: ganadas, rondas por partida y mejor y peor mapa."""

from __future__ import annotations

from django.test import TestCase

from replays.analytics import aggregates as agg
from replays.models import Match

from .factories import make_match, make_round, make_round_player


def _partida(*, index: int, ganada: bool | None = True, rondas: int = 2,
             map_name: str = "Club House"):
    """Una partida con `rondas` rondas tuyas alternando lado; `ganada=None` es sin resultado."""
    match = make_match(index=index, map_name=map_name,
                       my_score=4 if ganada is not False else 2,
                       opponent_score=2 if ganada is not False else 4)
    if ganada is None:
        Match.objects.filter(pk=match.pk).update(won=None)
    for numero in range(rondas):
        rnd = make_round(match, numero, side="Attack" if numero % 2 == 0 else "Defense")
        make_round_player(rnd)
    return match


def _mapas(datos: dict) -> tuple:
    def _uno(m):
        return None if m is None else (m["map"], m["matches"], m["winrate"])
    return _uno(datos["best_map"]), _uno(datos["worst_map"])


class ResumenPartidasTests(TestCase):
    def test_partidas_ganadas_sobre_decididas(self):
        for i in range(3):
            _partida(index=i)
        _partida(index=3, ganada=False)
        _partida(index=4, ganada=None)
        datos = agg.matches_summary()
        self.assertEqual(datos["matches"], 5)
        self.assertEqual(datos["matches_won"], 3)
        self.assertEqual(datos["matches_lost"], 1)
        self.assertEqual(datos["matches_decided"], 4)
        self.assertEqual(datos["matches_undecided"], 1)
        self.assertEqual(datos["match_winrate"], 75.0)

    def test_rondas_por_partida(self):
        _partida(index=0, rondas=7)
        _partida(index=1, rondas=9)
        datos = agg.matches_summary()
        self.assertEqual(datos["rounds"], 16)
        self.assertEqual(datos["rounds_per_match"], 8.0)

    def test_las_sin_resultado_cuentan_en_rondas_por_partida(self):
        # El winrate deja fuera las `won` nulas; las rondas por partida no.
        _partida(index=0, rondas=6)
        _partida(index=1, rondas=9, ganada=None)
        datos = agg.matches_summary()
        self.assertEqual(datos["rounds"], 15)
        self.assertEqual(datos["rounds_per_match"], 7.5)

    def test_mejor_y_peor_mapa(self):
        for i in range(3):
            _partida(index=i, map_name="Bank")
        for i in range(3, 7):
            _partida(index=i, map_name="Border", ganada=i % 2 == 0)
        self.assertEqual(_mapas(agg.matches_summary()), (("Bank", 3, 100.0), ("Border", 4, 50.0)))

    def test_mapa_bajo_la_muestra_no_cuenta(self):
        for i in range(3):
            _partida(index=i, map_name="Bank", ganada=i != 0)
        _partida(index=3, map_name="Border", ganada=False)
        _partida(index=4, map_name="Border", ganada=False)
        mejor, peor = _mapas(agg.matches_summary())
        self.assertEqual(mejor, ("Bank", 3, 66.7))
        self.assertIsNone(peor)

    def test_las_sin_resultado_no_llegan_a_la_muestra_del_mapa(self):
        _partida(index=0, map_name="Bank")
        _partida(index=1, map_name="Bank")
        _partida(index=2, map_name="Bank", ganada=None)
        self.assertEqual(_mapas(agg.matches_summary()), (None, None))

    def test_un_solo_mapa_no_es_mejor_y_peor(self):
        for i in range(4):
            _partida(index=i, map_name="Bank", ganada=i < 2)
        mejor, peor = _mapas(agg.matches_summary())
        self.assertEqual(mejor, ("Bank", 4, 50.0))
        self.assertIsNone(peor)

    def test_mapas_empatados_no_tienen_peor(self):
        for i in range(3):
            _partida(index=i, map_name="Bank")
        for i in range(3, 7):
            _partida(index=i, map_name="Border")
        mejor, peor = _mapas(agg.matches_summary())
        # a igual winrate gana el de mas partidas
        self.assertEqual(mejor, ("Border", 4, 100.0))
        self.assertIsNone(peor)

    def test_variantes_del_mapa_cuentan_juntas(self):
        _partida(index=0, map_name="Club House")
        _partida(index=1, map_name="Club House")
        nueva = _partida(index=2, map_name="Club House (Rework)")
        Match.objects.filter(pk=nueva.pk).update(map_slug="club-house")
        datos = agg.matches_summary()
        self.assertEqual(_mapas(datos)[0], ("Club House (Rework)", 3, 100.0))
        self.assertEqual(datos["best_map"]["slug"], "club-house")

    def test_el_lado_no_parte_la_partida(self):
        _partida(index=0, rondas=7)
        _partida(index=1, ganada=False, rondas=9)
        self.assertEqual(agg.matches_summary(side="Defense"), agg.matches_summary())

    def test_una_partida_sin_rondas_del_lado_filtrado_igual_cuenta(self):
        _partida(index=0, rondas=7)
        _partida(index=1, rondas=1)  # solo una ronda de ataque
        datos = agg.matches_summary(side="Defense")
        self.assertEqual((datos["matches"], datos["rounds"]), (2, 8))

    def test_los_filtros_eligen_las_partidas(self):
        for i in range(3):
            _partida(index=i, map_name="Bank")
        _partida(index=3, map_name="Border", ganada=False)
        datos = agg.matches_summary(map="border")
        self.assertEqual((datos["matches"], datos["matches_won"], datos["match_winrate"]),
                         (1, 0, 0.0))
        self.assertEqual(_mapas(datos), (None, None))


class ResumenPartidasApiTests(TestCase):
    def test_overview_trae_resumen_de_partidas(self):
        _partida(index=0)
        resp = self.client.get("/api/overview/")
        self.assertEqual(resp.status_code, 200)
        resumen = resp.json()["matches_summary"]
        self.assertEqual((resumen["matches"], resumen["match_winrate"]), (1, 100.0))
        self.assertEqual(resumen["min_matches_map"], agg.MIN_PARTIDAS_MAPA)

    def test_base_vacia_y_filtro_sin_partidas(self):
        vacio = {
            "matches": 0, "matches_won": 0, "matches_lost": 0, "matches_decided": 0,
            "matches_undecided": 0, "match_winrate": None, "rounds": 0,
            "rounds_per_match": None, "best_map": None, "worst_map": None,
        }
        resp = self.client.get("/api/overview/")
        self.assertEqual(resp.status_code, 200)
        self.assertLessEqual(vacio.items(), resp.json()["matches_summary"].items())

        _partida(index=0)
        resp = self.client.get("/api/overview/?since=2030-01-01")
        self.assertEqual(resp.status_code, 200)
        self.assertLessEqual(vacio.items(), resp.json()["matches_summary"].items())
