"""Tests de la comparacion entre periodos."""

from __future__ import annotations

from datetime import datetime, timedelta

from django.test import TestCase

from replays.analytics import aggregates as agg

from .factories import make_match, make_round, make_round_player

AHORA = datetime.now()


def metrica(payload, key):
    return next(m for m in payload["metrics"] if m["key"] == key)


def partida(indice, *, cuando, rondas=6, ganadas=3, kills=1):
    match = make_match(
        index=indice, played_at=cuando, my_score=ganadas, opponent_score=rondas - ganadas
    )
    for n in range(rondas):
        rnd = make_round(match, n, won=n < ganadas)
        make_round_player(rnd, kills=kills)
    return match


class PorPartidasTests(TestCase):
    def setUp(self):
        # 4 partidas viejas flojas, 4 recientes buenas
        for i in range(4):
            partida(i, cuando=AHORA - timedelta(days=10, hours=i), ganadas=1)
        for i in range(4, 8):
            partida(i, cuando=AHORA - timedelta(days=1, hours=i), ganadas=5)

    def test_parte_el_historial_en_dos(self):
        d = agg.compare_periods(by="matches", n=4, min_rounds=1)
        self.assertEqual(d["current"]["rounds"], 24)
        self.assertEqual(d["previous"]["rounds"], 24)
        self.assertEqual(d["current"]["label"], "Ultimas 4 partidas")

    def test_calcula_el_delta_en_la_direccion_correcta(self):
        d = agg.compare_periods(by="matches", n=4, min_rounds=1)
        winrate = metrica(d, "winrate")
        self.assertGreater(winrate["delta"], 0)
        self.assertEqual(winrate["verdict"], "mejor")

    def test_una_metrica_donde_bajar_es_mejor(self):
        d = agg.compare_periods(by="matches", n=4, min_rounds=1)
        self.assertEqual(metrica(d, "untraded_death_pct")["direction"], "down")

    def test_morir_mas_tarde_no_se_juzga(self):
        """Subir puede ser sobrevivir mas o llegar tarde a todo: no se opina."""
        d = agg.compare_periods(by="matches", n=4, min_rounds=1)
        self.assertEqual(metrica(d, "avg_death_elapsed")["direction"], "neutral")
        self.assertIsNone(metrica(d, "avg_death_elapsed")["verdict"])

    def test_avisa_cuando_no_hay_muestra(self):
        d = agg.compare_periods(by="matches", n=4, min_rounds=100)
        self.assertFalse(d["enough_sample"])
        d = agg.compare_periods(by="matches", n=4, min_rounds=10)
        self.assertTrue(d["enough_sample"])

    def test_sin_periodo_anterior_no_revienta(self):
        d = agg.compare_periods(by="matches", n=100, min_rounds=1)
        self.assertEqual(d["previous"]["rounds"], 0)
        self.assertIsNone(metrica(d, "winrate")["delta"])
        self.assertFalse(d["enough_sample"])


class RuidoTests(TestCase):
    """La banda de ruido es lo que separa un cambio de una casualidad."""

    def test_un_cambio_chico_con_poca_muestra_es_ruido(self):
        for i in range(2):
            partida(i, cuando=AHORA - timedelta(days=10, hours=i), rondas=6, ganadas=3)
        for i in range(2, 4):
            partida(i, cuando=AHORA - timedelta(days=1, hours=i), rondas=6, ganadas=4)

        winrate = metrica(agg.compare_periods(by="matches", n=2, min_rounds=1), "winrate")
        self.assertAlmostEqual(winrate["delta"], 16.7, places=1)
        self.assertGreater(winrate["noise"], 16.7)  # con 12 rondas por lado, la banda es ~20
        self.assertEqual(winrate["verdict"], "ruido")

    def test_el_mismo_cambio_con_mucha_muestra_si_cuenta(self):
        for i in range(30):
            partida(i, cuando=AHORA - timedelta(days=10, hours=i), rondas=6, ganadas=3)
        for i in range(30, 60):
            partida(i, cuando=AHORA - timedelta(days=1, hours=i), rondas=6, ganadas=4)

        winrate = metrica(agg.compare_periods(by="matches", n=30, min_rounds=1), "winrate")
        self.assertAlmostEqual(winrate["delta"], 16.7, places=1)
        self.assertLess(winrate["noise"], 16.7)
        self.assertEqual(winrate["verdict"], "mejor")

    def test_las_metricas_sin_proporcion_no_traen_banda(self):
        partida(0, cuando=AHORA - timedelta(days=10))
        partida(1, cuando=AHORA - timedelta(days=1))
        d = agg.compare_periods(by="matches", n=1, min_rounds=1)
        self.assertIsNone(metrica(d, "kd")["noise"])
        self.assertIsNotNone(metrica(d, "winrate")["noise"])


class PorDiasTests(TestCase):
    def setUp(self):
        partida(0, cuando=AHORA - timedelta(days=40), ganadas=1)
        partida(1, cuando=AHORA - timedelta(days=2), ganadas=5)

    def test_ventana_de_dias(self):
        """Con 10 dias, la partida de hace 40 queda fuera de los dos periodos."""
        d = agg.compare_periods(by="days", n=10, min_rounds=1)
        self.assertEqual(d["current"]["rounds"], 6)
        self.assertEqual(d["previous"]["rounds"], 0)
        self.assertEqual(d["current"]["label"], "Ultimos 10 dias")

    def test_una_ventana_larga_agarra_las_dos(self):
        """Con 30, el periodo anterior llega a los 60 dias y la alcanza."""
        d = agg.compare_periods(by="days", n=30, min_rounds=1)
        self.assertEqual(d["current"]["rounds"], 6)
        self.assertEqual(d["previous"]["rounds"], 6)


class FiltrosTests(TestCase):
    def setUp(self):
        partida(0, cuando=AHORA - timedelta(days=10))
        match = make_match(map_name="Villa", index=1, played_at=AHORA - timedelta(days=1))
        make_round_player(make_round(match, 0))

    def test_respeta_los_filtros_de_contenido(self):
        d = agg.compare_periods(by="matches", n=1, min_rounds=1, map="villa")
        self.assertEqual(d["current"]["rounds"], 1)
        self.assertEqual(d["previous"]["rounds"], 0)

    def test_ignora_los_filtros_de_fecha(self):
        """El periodo lo define la comparacion, no la barra de filtros."""
        con = agg.compare_periods(by="matches", n=1, min_rounds=1, since=AHORA)
        sin = agg.compare_periods(by="matches", n=1, min_rounds=1)
        self.assertEqual(con["current"]["rounds"], sin["current"]["rounds"])


class ApiTests(TestCase):
    def setUp(self):
        for i in range(4):
            partida(i, cuando=AHORA - timedelta(days=i + 1))

    def test_endpoint(self):
        data = self.client.get("/api/compare/?n=2&min_rounds=1").json()
        self.assertEqual(data["by"], "matches")
        self.assertTrue(data["enough_sample"])
        self.assertEqual(len(data["metrics"]), len(agg.COMPARE_METRICS))

    def test_modo_dias(self):
        self.assertEqual(self.client.get("/api/compare/?by=days&n=7").json()["by"], "days")

    def test_parametros_absurdos_no_revientan(self):
        for url in ("/api/compare/?n=-5", "/api/compare/?n=abc", "/api/compare/?by=loquesea"):
            with self.subTest(url=url):
                self.assertEqual(self.client.get(url).status_code, 200)
