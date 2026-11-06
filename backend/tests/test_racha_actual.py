"""Racha actual de partidas del Inicio (ficha 94)."""

from __future__ import annotations

from datetime import datetime

from django.test import SimpleTestCase, TestCase

from replays.analytics import aggregates as agg
from replays.models import Match

from .factories import make_match, make_round, make_round_player


def _partida(*, index: int, ganada: bool | None = True, map_name: str = "Club House",
             lados: tuple[str, ...] = ("Attack",)):
    """Una partida con una ronda tuya por lado pedido; `ganada=None` es sin resultado."""
    match = make_match(index=index, map_name=map_name,
                       my_score=4 if ganada is not False else 2,
                       opponent_score=2 if ganada is not False else 4)
    if ganada is None:
        Match.objects.filter(pk=match.pk).update(won=None)
    for numero, lado in enumerate(lados):
        rnd = make_round(match, numero, side=lado)
        make_round_player(rnd, side=lado)
    return match


def _fila(id_: int, won: bool | None, dia: int = 1) -> dict:
    return {"id": id_, "won": won, "played_at": datetime(2026, 11, dia, 20, 0)}


class RachaActualPuraTests(SimpleTestCase):
    def test_lista_vacia_da_nula(self):
        self.assertIsNone(agg.racha_actual_de_partidas([]))

    def test_cuenta_desde_la_ultima_y_corta_en_el_otro_resultado(self):
        filas = [_fila(1, True, 1), _fila(2, False, 2), _fila(3, False, 3), _fila(4, False, 4)]
        racha = agg.racha_actual_de_partidas(filas)
        self.assertEqual(racha, {
            "result": "loss",
            "length": 3,
            "since": "2026-11-02T20:00:00",
            "match_ids": [2, 3, 4],
        })

    def test_las_sin_resultado_no_entran_en_los_ids(self):
        filas = [_fila(1, True, 1), _fila(2, None, 2), _fila(3, True, 3), _fila(4, None, 4)]
        racha = agg.racha_actual_de_partidas(filas)
        self.assertEqual((racha["length"], racha["match_ids"]), (2, [1, 3]))
        self.assertEqual(racha["since"], "2026-11-01T20:00:00")


class RachaActualTests(TestCase):
    def test_sin_partidas_la_racha_es_nula(self):
        self.assertIsNone(agg.matches_summary()["current_streak"])

    def test_tres_ganadas_al_final_dan_racha_de_tres(self):
        _partida(index=0, ganada=False)
        ganadas = [_partida(index=i) for i in (1, 2, 3)]
        racha = agg.matches_summary()["current_streak"]
        self.assertEqual(racha["result"], "win")
        self.assertEqual(racha["length"], 3)
        self.assertEqual(racha["since"], ganadas[0].played_at.isoformat())
        self.assertEqual(racha["match_ids"], [m.id for m in ganadas])

    def test_una_partida_sin_resultado_no_corta_ni_suma(self):
        _partida(index=0)
        _partida(index=1, ganada=None)
        _partida(index=2)
        racha = agg.matches_summary()["current_streak"]
        self.assertEqual((racha["result"], racha["length"]), ("win", 2))

    def test_solo_partidas_sin_resultado_dan_nula(self):
        _partida(index=0, ganada=None)
        _partida(index=1, ganada=None)
        self.assertIsNone(agg.matches_summary()["current_streak"])

    def test_la_ultima_perdida_da_racha_de_una_derrota(self):
        _partida(index=0)
        _partida(index=1)
        ultima = _partida(index=2, ganada=False)
        racha = agg.matches_summary()["current_streak"]
        self.assertEqual((racha["result"], racha["length"]), ("loss", 1))
        self.assertEqual(racha["match_ids"], [ultima.id])

    def test_el_filtro_de_mapa_cambia_la_racha(self):
        _partida(index=0, map_name="Club House")
        _partida(index=1, map_name="Border", ganada=False)
        _partida(index=2, map_name="Club House")
        sin_filtro = agg.matches_summary()["current_streak"]
        self.assertEqual((sin_filtro["result"], sin_filtro["length"]), ("win", 1))
        con_mapa = agg.matches_summary(map="club-house")["current_streak"]
        self.assertEqual((con_mapa["result"], con_mapa["length"]), ("win", 2))

    def test_el_filtro_de_lado_no_parte_la_partida(self):
        # La ultima perdida solo tiene rondas tuyas en defensa: si el lado
        # filtrara partidas, `side=Attack` la saltaria y daria racha de victorias.
        _partida(index=0, lados=("Attack", "Defense"))
        _partida(index=1, ganada=False, lados=("Defense",))
        sin_filtro = agg.matches_summary()["current_streak"]
        con_lado = agg.matches_summary(side="Attack")["current_streak"]
        self.assertEqual(con_lado, sin_filtro)
        self.assertEqual((con_lado["result"], con_lado["length"]), ("loss", 1))

    def test_la_api_del_resumen_trae_la_racha(self):
        _partida(index=0)
        _partida(index=1)
        resumen = self.client.get("/api/overview/").json()["matches_summary"]
        self.assertEqual(resumen["current_streak"]["length"], 2)
        self.assertEqual(resumen["current_streak"]["result"], "win")
