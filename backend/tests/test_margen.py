"""Partidas cerradas y holgadas: winrate y rating segun el margen final."""

from __future__ import annotations

from django.test import SimpleTestCase, TestCase

from pydissect.constants import Y9S3, Y9S4
from replays.analytics import aggregates as agg
from replays.models import Match

from .factories import make_match, make_round, make_round_player


def _partida(mio: int, suyo: int, *, index: int = 0, code_version: int = Y9S4,
             map_name: str = "Club House", prorroga: bool = False, kills: int = 1):
    """Una partida con una ronda de ataque y una de defensa, mias."""
    match = make_match(index=index, code_version=code_version, map_name=map_name,
                       my_score=mio, opponent_score=suyo)
    for numero, lado in enumerate(("Attack", "Defense")):
        rnd = make_round(match, numero, side=lado)
        make_round_player(rnd, kills=kills)
    if prorroga:
        rnd = make_round(match, 2, side="Attack", overtime_number=1)
        make_round_player(rnd, kills=kills)
    return match


def _por_tramo(datos: dict) -> dict[str, tuple[int, int]]:
    return {f["margin"]: (f["matches"], f["wins"]) for f in datos["rows"]}


class TramoMargenTests(SimpleTestCase):
    def test_tres_o_mas_se_juntan_y_cero_no_tiene_tramo(self):
        self.assertEqual(agg._tramo_margen(1), "1")
        self.assertEqual(agg._tramo_margen(2), "2")
        self.assertEqual(agg._tramo_margen(3), "3+")
        self.assertEqual(agg._tramo_margen(7), "3+")
        self.assertIsNone(agg._tramo_margen(0))


class MargenTests(TestCase):
    def test_los_tramos_salen_en_orden_fijo_con_partidas_y_winrate(self):
        _partida(4, 3, index=0)
        _partida(3, 4, index=1)
        _partida(4, 2, index=2)
        _partida(4, 0, index=3)
        _partida(1, 4, index=4)
        datos = agg.by_margin()
        self.assertEqual([f["margin"] for f in datos["rows"]], ["overtime", "1", "2", "3+"])
        self.assertEqual(_por_tramo(datos), {
            "overtime": (0, 0), "1": (2, 1), "2": (1, 1), "3+": (2, 1),
        })
        fila_1 = datos["rows"][1]
        self.assertEqual(fila_1["winrate"], 50.0)
        self.assertEqual(fila_1["rounds"], 4)
        self.assertEqual(fila_1["kpr"], 1.0)
        self.assertIsNotNone(fila_1["rating"])
        self.assertEqual(datos["matches_known"], 5)
        self.assertEqual(datos["matches_excluded"], 0)

    def test_una_partida_con_prorroga_cae_en_prorroga_aunque_gane_por_dos(self):
        _partida(5, 3, prorroga=True)
        datos = agg.by_margin()
        self.assertEqual(_por_tramo(datos)["overtime"], (1, 1))
        self.assertEqual(_por_tramo(datos)["2"], (0, 0))
        self.assertEqual(datos["rows"][0]["rounds"], 3)

    def test_una_partida_anterior_a_y9s4_queda_fuera_y_se_cuenta(self):
        _partida(4, 3, index=0)
        _partida(4, 3, index=1, code_version=Y9S3)
        datos = agg.by_margin()
        self.assertEqual(_por_tramo(datos)["1"], (1, 1))
        self.assertEqual(datos["matches_known"], 1)
        self.assertEqual(datos["matches_excluded"], 1)

    def test_un_empate_queda_fuera_y_se_cuenta(self):
        _partida(3, 3)
        datos = agg.by_margin()
        self.assertEqual(datos["matches_known"], 0)
        self.assertEqual(datos["matches_excluded"], 1)

    def test_una_partida_sin_resultado_queda_fuera_aunque_tenga_margen(self):
        m = _partida(4, 2)
        Match.objects.filter(pk=m.pk).update(won=None)
        datos = agg.by_margin()
        self.assertEqual(datos["matches_known"], 0)
        self.assertEqual(datos["matches_excluded"], 1)

    def test_el_filtro_de_lado_no_parte_la_partida(self):
        _partida(4, 3, index=0)
        _partida(1, 4, index=1)
        self.assertEqual(agg.by_margin(side="Attack"), agg.by_margin())
        self.assertEqual(agg.by_margin(side="Attack")["rows"][1]["rounds"], 2)

    def test_el_filtro_de_mapa_recorta_partidas(self):
        _partida(4, 3, index=0, map_name="Club House")
        _partida(4, 1, index=1, map_name="Oregon")
        datos = agg.by_margin(map="oregon")
        self.assertEqual(_por_tramo(datos), {
            "overtime": (0, 0), "1": (0, 0), "2": (0, 0), "3+": (1, 1),
        })

    def test_el_rating_mira_todas_tus_rondas_aunque_filtres_operador(self):
        m = _partida(4, 3)
        rnd = make_round(m, 2, side="Attack")
        make_round_player(rnd, operator="Ash", kills=3)
        datos = agg.by_margin(operator="Ash")
        self.assertEqual(datos["rows"][1]["rounds"], 3)

    def test_base_vacia_devuelve_los_cuatro_tramos_en_cero(self):
        datos = agg.by_margin()
        self.assertEqual(len(datos["rows"]), 4)
        for fila in datos["rows"]:
            self.assertEqual(fila["matches"], 0)
            self.assertIsNone(fila["winrate"])
            self.assertIsNone(fila["rating"])
        self.assertEqual(datos["matches_known"], 0)
        self.assertEqual(datos["matches_excluded"], 0)
