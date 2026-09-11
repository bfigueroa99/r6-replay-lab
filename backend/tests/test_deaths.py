"""Tests de la distribucion del momento de la muerte."""

from __future__ import annotations

from django.test import TestCase

from replays.analytics import aggregates as agg
from replays.analytics.coach import build_insights

from .factories import make_match, make_round, make_round_player


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
