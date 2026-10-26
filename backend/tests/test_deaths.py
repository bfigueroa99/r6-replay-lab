"""Tests de la distribucion del momento de la muerte."""

from __future__ import annotations

from django.test import TestCase

from replays.analytics import aggregates as agg
from replays.analytics.coach import build_insights

from .factories import ME, make_event, make_match, make_round, make_round_player


def find(payload, key):
    return next((i for i in payload["insights"] if i["key"] == key), None)


class DistribucionTests(TestCase):
    def setUp(self):
        self.match = make_match(index=0)
        self.n = 0

    def muerte(self, elapsed, *, side="Attack", traded=False):
        rnd = make_round(self.match, self.n, side=side)
        self.n += 1
        return make_round_player(
            rnd, side=side, died=True, death_elapsed=elapsed, was_traded=traded
        )

    def test_arma_los_tramos_de_30(self):
        for elapsed in (5, 25, 35, 95):
            self.muerte(elapsed)
        filas = {f["label"]: f for f in agg.deaths_by_time()}
        self.assertEqual(filas["0-30s"]["deaths"], 2)
        self.assertEqual(filas["30-60s"]["deaths"], 1)
        self.assertEqual(filas["90-120s"]["deaths"], 1)

    def test_el_ultimo_tramo_junta_la_cola(self):
        """150s+ se lleva todo lo que pase del tope."""
        for elapsed in (155, 175, 200):
            self.muerte(elapsed)
        filas = {f["label"]: f for f in agg.deaths_by_time()}
        self.assertEqual(list(filas), ["150s+"])
        self.assertEqual(filas["150s+"]["deaths"], 3)
        self.assertIsNone(filas["150s+"]["end"])

    def test_separa_por_lado(self):
        self.muerte(10, side="Attack")
        self.muerte(15, side="Defense")
        fila = agg.deaths_by_time()[0]
        self.assertEqual(fila["attack"], 1)
        self.assertEqual(fila["defense"], 1)
        self.assertEqual(fila["deaths"], 2)

    def test_porcentaje_sobre_el_total_de_muertes(self):
        self.muerte(10)
        self.muerte(100)
        self.assertEqual([f["pct"] for f in agg.deaths_by_time()], [50.0, 50.0])

    def test_cruza_con_las_muertes_sin_trade(self):
        self.muerte(10, traded=True)
        self.muerte(15, traded=False)
        self.assertEqual(agg.deaths_by_time()[0]["untraded_pct"], 50.0)

    def test_las_rondas_sin_muerte_no_entran(self):
        rnd = make_round(self.match, 90)
        make_round_player(rnd, died=False)
        self.muerte(10)
        self.assertEqual(sum(f["deaths"] for f in agg.deaths_by_time()), 1)

    def test_sin_datos_devuelve_lista_vacia(self):
        self.assertEqual(agg.deaths_by_time(), [])


class CuandoMatasTests(TestCase):
    """Bajas a rivales por tramo de la fase de accion, leidas del feed."""

    def setUp(self):
        self.match = make_match(index=0)
        self.n = 0

    def _ronda(self, side="Attack"):
        rnd = make_round(self.match, self.n, side=side)
        self.n += 1
        make_round_player(rnd, side=side)
        make_round_player(rnd, username="companero", is_me=False, side=side)
        rival = "Defense" if side == "Attack" else "Attack"
        make_round_player(rnd, username="rival", is_me=False, team_index=1, side=rival)
        return rnd

    def _baja(self, elapsed, *, side="Attack", victima="rival"):
        rnd = self._ronda(side)
        # el factory deriva elapsed como clock_start - clock
        make_event(rnd, 0, ME, victima, clock=rnd.clock_start - elapsed)
        return rnd

    def test_bajas_a_los_10_45_y_200_caen_en_tres_tramos(self):
        for elapsed in (10, 45, 200):
            self._baja(elapsed)
        filas = {f["label"]: f for f in agg.kills_by_time()}
        self.assertEqual(list(filas), ["0-30s", "30-60s", "150s+"])
        self.assertEqual([f["kills"] for f in filas.values()], [1, 1, 1])
        self.assertIsNone(filas["150s+"]["end"])
        self.assertEqual(filas["30-60s"]["start"], 30)
        self.assertEqual(filas["30-60s"]["end"], 60)

    def test_un_teamkill_no_cuenta_en_ningun_tramo(self):
        self._baja(10, victima="companero")
        self._baja(100)
        filas = agg.kills_by_time()
        self.assertEqual([f["label"] for f in filas], ["90-120s"])
        self.assertEqual(filas[0]["kills"], 1)
        self.assertEqual(filas[0]["pct"], 100.0)

    def test_las_muertes_tuyas_no_cuentan_como_bajas(self):
        rnd = self._ronda()
        make_event(rnd, 0, "rival", ME, clock=170)
        self.assertEqual(agg.kills_by_time(), [])

    def test_la_suma_de_tramos_es_igual_a_las_bajas_de_duel_totals(self):
        for elapsed, side in ((5, "Attack"), (40, "Defense"), (70, "Attack"), (160, "Defense")):
            self._baja(elapsed, side=side)
        self._baja(20, victima="companero")
        for filtros in ({}, {"side": "Defense"}):
            with self.subTest(filtros=filtros):
                total = sum(f["kills"] for f in agg.kills_by_time(**filtros))
                self.assertEqual(total, agg.duel_totals(**filtros)["kills"])

    def test_separa_por_tu_lado_en_la_ronda(self):
        self._baja(10, side="Attack")
        self._baja(20, side="Defense")
        fila = agg.kills_by_time()[0]
        self.assertEqual((fila["kills"], fila["attack"], fila["defense"]), (2, 1, 1))

    def test_el_lado_sale_de_tu_fila_aunque_el_rival_este_primero(self):
        # qa: con el companero cargado antes que el rival, leer el lado de
        # cualquier fila ajena daba lo mismo y el test anterior no lo veia
        rnd = make_round(self.match, 0, side="Attack")
        make_round_player(rnd, username="rival", is_me=False, team_index=1, side="Defense")
        make_round_player(rnd, side="Attack")
        make_event(rnd, 0, ME, "rival", clock=rnd.clock_start - 10)
        fila = agg.kills_by_time()[0]
        self.assertEqual((fila["attack"], fila["defense"]), (1, 0))

    def test_el_porcentaje_es_sobre_el_total_de_tramos(self):
        for elapsed in (10, 15, 100):
            self._baja(elapsed)
        self.assertEqual([f["pct"] for f in agg.kills_by_time()], [66.7, 33.3])

    def test_con_side_defense_el_ataque_queda_en_cero(self):
        self._baja(10, side="Attack")
        self._baja(50, side="Defense")
        self._baja(100, side="Attack")
        filas = agg.kills_by_time(side="Defense")
        self.assertEqual([f["label"] for f in filas], ["30-60s"])
        self.assertTrue(all(f["attack"] == 0 for f in filas))

    def test_base_vacia_devuelve_lista_vacia_en_la_api(self):
        resp = self.client.get("/api/trends/")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["kills_by_time"], [])

    def test_la_api_de_tendencias_lo_expone(self):
        self._baja(10)
        datos = self.client.get("/api/trends/").json()
        self.assertEqual(datos["kills_by_time"][0]["label"], "0-30s")


class ExtremosTests(TestCase):
    """Los dos ejes que usa el coach: segundos jugados y reloj restante."""

    def setUp(self):
        self.match = make_match(index=0)

    def _muerte(self, numero, *, elapsed, side="Attack"):
        rnd = make_round(self.match, numero, side=side)
        return make_round_player(rnd, side=side, died=True, death_elapsed=elapsed)

    def test_first30_mira_los_segundos_jugados(self):
        self._muerte(0, elapsed=10)
        self._muerte(1, elapsed=100)
        timing = agg.death_timing()["attack"]
        self.assertEqual(timing["first30"], 1)
        self.assertEqual(timing["first30_pct"], 50.0)

    def test_last30_mira_el_reloj_que_quedaba(self):
        """clock_start es 180 en las factories: morir a los 160 deja 20 de reloj."""
        self._muerte(0, elapsed=160)
        self._muerte(1, elapsed=60)
        timing = agg.death_timing()["attack"]
        self.assertEqual(timing["last30"], 1)
        self.assertEqual(timing["last30_pct"], 50.0)

    def test_los_dos_lados_van_por_separado(self):
        self._muerte(0, elapsed=10, side="Attack")
        self._muerte(1, elapsed=10, side="Defense")
        timing = agg.death_timing()
        self.assertEqual(timing["attack"]["deaths"], 1)
        self.assertEqual(timing["defense"]["deaths"], 1)

    def test_sin_datos_no_revienta(self):
        timing = agg.death_timing()
        self.assertEqual(timing["attack"]["deaths"], 0)
        self.assertIsNone(timing["attack"]["first30_pct"])


class CoachMuertesTests(TestCase):
    def _historial(self, *, elapsed, side="Attack", cuantas=30):
        match = make_match(index=0)
        for n in range(cuantas):
            rnd = make_round(match, n, side=side)
            make_round_player(rnd, side=side, died=True, death_elapsed=elapsed)

    def test_avisa_si_sales_muy_temprano(self):
        self._historial(elapsed=10)
        insight = find(build_insights(), "muertes-tempranas-ataque")
        self.assertIsNotNone(insight)
        self.assertIn("primeros 30s", insight["title"])

    def test_avisa_si_te_quedas_sin_tiempo_en_ataque(self):
        self._historial(elapsed=165)  # deja 15s de reloj
        insight = find(build_insights(), "sin-tiempo-ataque")
        self.assertIsNotNone(insight)
        self.assertIn("reloj casi agotado", insight["title"])

    def test_morir_a_mitad_de_ronda_no_dispara_nada(self):
        self._historial(elapsed=90)
        payload = build_insights()
        self.assertIsNone(find(payload, "muertes-tempranas-ataque"))
        self.assertIsNone(find(payload, "sin-tiempo-ataque"))

    def test_no_opina_con_pocas_muertes(self):
        self._historial(elapsed=10, cuantas=20)
        self.assertIsNone(find(build_insights(), "muertes-tempranas-ataque"))

    def test_el_endpoint_de_tendencias_lo_expone(self):
        self._historial(elapsed=10)
        data = self.client.get("/api/trends/").json()
        self.assertTrue(data["deaths_by_time"])
        self.assertEqual(data["death_timing"]["attack"]["first30"], 30)
