"""Primero de tu equipo en caer: quien de tu equipo muere primero y el winrate de esas rondas."""

from __future__ import annotations

import sqlite3

from django.db import connection
from django.test import SimpleTestCase, TestCase

from replays.analytics import aggregates as agg

from .factories import ME, make_event, make_match, make_round, make_round_player


def _total(filas: list[dict]) -> dict:
    return next(f for f in filas if f["side"] == "total")


def _lado(filas: list[dict], lado: str) -> dict:
    return next(f for f in filas if f["side"] == lado)


class QuienCaePrimeroTests(SimpleTestCase):
    def test_clasifica_cada_caso(self):
        self.assertEqual(agg._quien_cae_primero(30.0, [50.0]), "me")
        self.assertEqual(agg._quien_cae_primero(50.0, [30.0]), "mate")
        self.assertEqual(agg._quien_cae_primero(None, [30.0]), "mate")
        self.assertEqual(agg._quien_cae_primero(None, [None]), "none")
        self.assertEqual(agg._quien_cae_primero(30.0, []), "me")
        self.assertEqual(agg._quien_cae_primero(30.0, [30.0, 60.0]), "tie")
        self.assertEqual(agg._quien_cae_primero(0.0, [40.0]), "tie")
        self.assertEqual(agg._quien_cae_primero(40.0, [0.0]), "tie")


class PrimeroEnCaerTests(TestCase):
    def setUp(self):
        self.match = make_match()
        self.numero = 0

    def _ronda(self, mio, companeros=(), *, side="Attack", won=True, rivales=()):
        """Una ronda con tu fila, la de tus companeros y la de los rivales (elapsed o None)."""
        rnd = make_round(self.match, self.numero, side=side, won=won)
        self.numero += 1
        make_round_player(rnd, died=mio is not None, death_elapsed=mio)
        for i, elapsed in enumerate(companeros):
            make_round_player(rnd, username=f"mate{i}", is_me=False,
                              died=elapsed is not None, death_elapsed=elapsed)
        for i, elapsed in enumerate(rivales):
            make_round_player(rnd, username=f"rival{i}", is_me=False, team_index=1,
                              side="Defense" if side == "Attack" else "Attack",
                              died=elapsed is not None, death_elapsed=elapsed, won=not won)
        return rnd

    def test_caiste_primero_aunque_antes_muriera_un_rival(self):
        self._ronda(30.0, [50.0], rivales=[20.0])
        total = _total(agg.first_teammate_death())
        self.assertEqual((total["me_first"], total["mate_first"]), (1, 0))

    def test_cayo_primero_un_companero(self):
        self._ronda(50.0, [30.0, None])
        total = _total(agg.first_teammate_death())
        self.assertEqual((total["me_first"], total["mate_first"]), (0, 1))

    def test_ronda_sin_muertes_de_tu_equipo(self):
        self._ronda(None, [None, None], rivales=[20.0])
        total = _total(agg.first_teammate_death())
        self.assertEqual((total["rounds"], total["no_deaths"]), (1, 1))

    def test_no_moriste_y_murio_un_companero_es_companero(self):
        self._ronda(None, [40.0])
        self.assertEqual(_total(agg.first_teammate_death())["mate_first"], 1)

    def test_elapsed_nulo_nunca_es_primera_muerte(self):
        rnd = make_round(self.match, 0)
        make_round_player(rnd, died=True, death_elapsed=None)
        make_round_player(rnd, username="mate0", is_me=False, death_elapsed=70.0)
        total = _total(agg.first_teammate_death())
        self.assertEqual((total["me_first"], total["mate_first"]), (0, 1))

    def test_empate_lo_decide_el_orden_del_feed(self):
        gano = self._ronda(30.0, [30.0])
        make_event(gano, 1, "mate0", ME)
        make_event(gano, 2, "rival0", "mate0")
        pierdo = self._ronda(30.0, [30.0])
        make_event(pierdo, 1, "rival0", "mate0")
        make_event(pierdo, 2, "rival0", ME)
        total = _total(agg.first_teammate_death())
        self.assertEqual((total["me_first"], total["mate_first"]), (1, 1))

    def test_empate_cuenta_las_muertes_sin_asesino(self):
        rnd = self._ronda(30.0, [30.0])
        make_event(rnd, 1, ME, kind="Death")
        make_event(rnd, 2, "rival0", "mate0")
        self.assertEqual(_total(agg.first_teammate_death())["me_first"], 1)

    def test_reloj_en_cero_lo_decide_el_feed(self):
        # moriste con el reloj en 0:00, despues del companero que cayo a los 40 s
        rnd = self._ronda(0.0, [40.0])
        make_event(rnd, 1, "rival0", "mate0")
        make_event(rnd, 2, "rival0", ME)
        self.assertEqual(_total(agg.first_teammate_death())["mate_first"], 1)

    def test_reloj_en_cero_y_feed_a_tu_favor_es_tuya(self):
        rnd = self._ronda(0.0, [40.0])
        make_event(rnd, 1, "rival0", ME)
        make_event(rnd, 2, "rival0", "mate0")
        self.assertEqual(_total(agg.first_teammate_death())["me_first"], 1)

    def test_empate_sin_eventos_va_al_companero(self):
        rnd = self._ronda(30.0, [30.0])
        make_event(rnd, 1, "rival0", ME)
        total = _total(agg.first_teammate_death())
        self.assertEqual((total["me_first"], total["mate_first"]), (0, 1))

    def test_los_rivales_no_cuentan_como_companeros(self):
        self._ronda(40.0, [None], rivales=[10.0])
        self.assertEqual(_total(agg.first_teammate_death())["me_first"], 1)

    def test_separa_por_lado_y_suma_el_total(self):
        self._ronda(30.0, [50.0], side="Attack")
        self._ronda(50.0, [30.0], side="Defense")
        self._ronda(None, [None], side="Defense")
        filas = agg.first_teammate_death()
        self.assertEqual([f["side"] for f in filas], ["Attack", "Defense", "total"])
        self.assertEqual(_lado(filas, "Attack")["me_first"], 1)
        self.assertEqual(_lado(filas, "Defense")["rounds"], 2)
        self.assertEqual(_lado(filas, "Defense")["mate_first"], 1)
        self.assertEqual(_total(filas)["rounds"], 3)

    def test_fila_sin_lado_cuenta_solo_en_el_total(self):
        rnd = self._ronda(30.0, [50.0], side="Attack")
        rnd.players.filter(is_me=True).update(side="")
        filas = agg.first_teammate_death()
        self.assertEqual(_lado(filas, "Attack")["rounds"], 0)
        self.assertEqual(_lado(filas, "Defense")["rounds"], 0)
        self.assertEqual(_total(filas)["me_first"], 1)

    def test_winrate_por_grupo(self):
        self._ronda(30.0, [50.0], won=True)
        self._ronda(30.0, [50.0], won=False)
        self._ronda(30.0, [50.0], won=False)
        self._ronda(None, [40.0], won=True)
        total = _total(agg.first_teammate_death())
        self.assertEqual((total["me_first"], total["me_first_won"]), (3, 1))
        self.assertEqual(total["me_first_winrate"], 33.3)
        self.assertEqual(total["mate_first_winrate"], 100.0)
        self.assertIsNone(total["no_deaths_winrate"])

    def test_muchos_empates_no_pasan_el_tope_de_parametros(self):
        for _ in range(60):
            rnd = self._ronda(30.0, [30.0])
            make_event(rnd, 1, "rival0", ME)
            make_event(rnd, 2, "rival0", "mate0")
        connection.ensure_connection()
        crudo = connection.connection
        tope = crudo.getlimit(sqlite3.SQLITE_LIMIT_VARIABLE_NUMBER)
        crudo.setlimit(sqlite3.SQLITE_LIMIT_VARIABLE_NUMBER, 50)
        try:
            total = _total(agg.first_teammate_death())
        finally:
            crudo.setlimit(sqlite3.SQLITE_LIMIT_VARIABLE_NUMBER, tope)
        self.assertEqual((total["me_first"], total["mate_first"]), (60, 0))

    def test_respeta_el_filtro_de_lado(self):
        self._ronda(30.0, [50.0], side="Attack")
        self._ronda(30.0, [50.0], side="Defense")
        filas = agg.first_teammate_death(side="Defense")
        self.assertEqual(_total(filas)["rounds"], 1)
        self.assertEqual(_lado(filas, "Attack")["rounds"], 0)


class PrimeroEnCaerApiTests(TestCase):
    def test_teammates_trae_first_down_con_base_vacia(self):
        res = self.client.get("/api/teammates/")
        self.assertEqual(res.status_code, 200)
        filas = res.json()["first_down"]
        self.assertEqual(len(filas), 3)
        self.assertTrue(all(f["rounds"] == 0 and f["me_first_winrate"] is None for f in filas))

    def test_teammates_con_filtros_raros_da_200(self):
        rnd = make_round(make_match(), 0)
        make_round_player(rnd, death_elapsed=30.0)
        make_round_player(rnd, username="mate0", is_me=False, death_elapsed=50.0)
        for url in ("/api/teammates/?until=foo", "/api/teammates/?session=-1",
                    "/api/teammates/?side=Attack", "/api/teammates/?map=%00"):
            with self.subTest(url=url):
                self.assertEqual(self.client.get(url).status_code, 200)
        filas = self.client.get("/api/teammates/?side=Attack").json()["first_down"]
        self.assertEqual(_total(filas)["me_first"], 1)
