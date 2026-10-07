"""Tests de la racha actual: partidas seguidas con el mismo resultado."""

from __future__ import annotations

from django.test import TestCase

from replays.analytics import aggregates as agg

from .factories import make_match, make_round, make_round_player


def partida(index: int, *, ganada: bool | None, map_name: str = "Bank"):
    """Una partida con dos rondas mias. `ganada=None` es un empate."""
    if ganada is None:
        match = make_match(index=index, my_score=3, opponent_score=3, map_name=map_name)
    else:
        match = make_match(
            index=index,
            my_score=4 if ganada else 2,
            opponent_score=2 if ganada else 4,
            map_name=map_name,
        )
    match.won = ganada
    match.save()
    for n in range(2):
        make_round_player(make_round(match, n, won=bool(ganada)))
    return match


class RachaTests(TestCase):
    def test_sin_partidas_no_hay_racha(self):
        self.assertEqual(agg.streak(), {"result": None, "length": 0})

    def test_cuenta_las_victorias_seguidas_desde_la_mas_reciente(self):
        partida(0, ganada=False)
        partida(1, ganada=True)
        partida(2, ganada=True)
        partida(3, ganada=True)
        self.assertEqual(agg.streak(), {"result": "victoria", "length": 3})

    def test_la_racha_puede_ser_de_derrotas(self):
        partida(0, ganada=True)
        partida(1, ganada=False)
        partida(2, ganada=False)
        self.assertEqual(agg.streak(), {"result": "derrota", "length": 2})

    def test_un_empate_reciente_corta_la_racha(self):
        partida(0, ganada=True)
        partida(1, ganada=True)
        partida(2, ganada=None)
        self.assertEqual(agg.streak(), {"result": None, "length": 0})

    def test_un_empate_viejo_frena_la_cuenta(self):
        partida(0, ganada=True)
        partida(1, ganada=None)
        partida(2, ganada=True)
        partida(3, ganada=True)
        self.assertEqual(agg.streak(), {"result": "victoria", "length": 2})

    def test_respeta_los_filtros(self):
        partida(0, ganada=True, map_name="Bank")
        partida(1, ganada=True, map_name="Bank")
        partida(2, ganada=False, map_name="Border")
        self.assertEqual(agg.streak()["result"], "derrota")
        self.assertEqual(agg.streak(map="bank"), {"result": "victoria", "length": 2})

    def test_viaja_en_el_overview(self):
        partida(0, ganada=True)
        data = self.client.get("/api/overview/").json()
        self.assertEqual(data["streak"], {"result": "victoria", "length": 1})
