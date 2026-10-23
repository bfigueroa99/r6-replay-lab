"""Tests de la comparacion entre periodos."""

from __future__ import annotations

from datetime import datetime, timedelta

from django.test import TestCase

from replays.analytics import aggregates as agg

from .factories import make_match, make_round, make_round_player

AHORA = datetime.now()


def metrica(payload, key):
    return next(m for m in payload["metrics"] if m["key"] == key)


def partida(indice, *, cuando, rondas=6, ganadas=3, kills=1, mapa="Club House",
            operador="Zofia", lado="Attack"):
    match = make_match(
        index=indice,
        played_at=cuando,
        my_score=ganadas,
        opponent_score=rondas - ganadas,
        map_name=mapa,
    )
    for n in range(rondas):
        rnd = make_round(match, n, won=n < ganadas, side=lado)
        make_round_player(rnd, kills=kills, operator=operador)
    return match


def fila(filas, **clave):
    return next(f for f in filas if all(f[k] == v for k, v in clave.items()))


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


class CortesPorMapaYOperadorTests(TestCase):
    """Donde cambio: el mismo corte de periodos, partido por mapa y operador."""

    def test_un_mapa_que_sube_con_muestra_sale_mejor(self):
        partida(0, cuando=AHORA - timedelta(days=10), rondas=12, ganadas=3)
        partida(1, cuando=AHORA - timedelta(days=1), rondas=12, ganadas=10)
        d = agg.compare_periods(by="matches", n=1, min_rounds=1)
        club = fila(d["by_map"], slug="club-house")
        self.assertEqual(club["map"], "Club House")
        self.assertEqual((club["previous_rounds"], club["current_rounds"]), (12, 12))
        self.assertAlmostEqual(club["delta"], 58.3, places=1)
        self.assertIsNotNone(club["noise"])
        self.assertEqual(club["verdict"], "mejor")
        self.assertEqual(d["min_rows"], agg.COMPARE_MIN_ROUNDS_FILA)

    def test_un_mapa_sin_muestra_en_el_periodo_previo_no_sale(self):
        partida(0, cuando=AHORA - timedelta(days=10, hours=1), rondas=12, mapa="Bank")
        partida(1, cuando=AHORA - timedelta(days=10), rondas=4, mapa="Villa")
        partida(2, cuando=AHORA - timedelta(days=1, hours=1), rondas=12, mapa="Bank")
        partida(3, cuando=AHORA - timedelta(days=1), rondas=12, mapa="Villa")
        d = agg.compare_periods(by="matches", n=2, min_rounds=1)
        self.assertEqual([f["slug"] for f in d["by_map"]], ["bank"])

    def test_un_mapa_que_no_jugaste_antes_no_sale(self):
        partida(0, cuando=AHORA - timedelta(days=10), rondas=12, mapa="Bank")
        partida(1, cuando=AHORA - timedelta(days=1), rondas=12, mapa="Villa")
        d = agg.compare_periods(by="matches", n=1, min_rounds=1)
        self.assertEqual(d["by_map"], [])

    def test_las_filas_vienen_ordenadas_por_delta(self):
        partida(0, cuando=AHORA - timedelta(days=10, hours=3), rondas=12, ganadas=6, mapa="Bank")
        partida(1, cuando=AHORA - timedelta(days=10, hours=2), rondas=12, ganadas=6, mapa="Villa")
        partida(2, cuando=AHORA - timedelta(days=10, hours=1), rondas=12, ganadas=6, mapa="Oregon")
        partida(3, cuando=AHORA - timedelta(days=1, hours=3), rondas=12, ganadas=2, mapa="Bank")
        partida(4, cuando=AHORA - timedelta(days=1, hours=2), rondas=12, ganadas=11, mapa="Villa")
        partida(5, cuando=AHORA - timedelta(days=1, hours=1), rondas=12, ganadas=7, mapa="Oregon")
        d = agg.compare_periods(by="matches", n=3, min_rounds=1)
        self.assertEqual([f["slug"] for f in d["by_map"]], ["villa", "oregon", "bank"])
        deltas = [f["delta"] for f in d["by_map"]]
        self.assertEqual(deltas, sorted(deltas, reverse=True))
        self.assertEqual(fila(d["by_map"], slug="bank")["verdict"], "peor")
        self.assertEqual(fila(d["by_map"], slug="oregon")["verdict"], "ruido")

    def test_el_operador_se_parte_por_lado(self):
        partida(0, cuando=AHORA - timedelta(days=10, hours=1), rondas=12, operador="Ash")
        partida(1, cuando=AHORA - timedelta(days=10), rondas=12, operador="Ash", lado="Defense")
        partida(2, cuando=AHORA - timedelta(days=1, hours=1), rondas=12, operador="Ash")
        partida(3, cuando=AHORA - timedelta(days=1), rondas=12, operador="Ash", lado="Defense")
        d = agg.compare_periods(by="matches", n=2, min_rounds=1)
        self.assertEqual(
            sorted((f["operator"], f["side"]) for f in d["by_operator"]),
            [("Ash", "Attack"), ("Ash", "Defense")],
        )

    def test_las_rondas_sin_operador_no_forman_fila(self):
        partida(0, cuando=AHORA - timedelta(days=10), rondas=12, operador="")
        partida(1, cuando=AHORA - timedelta(days=1), rondas=12, operador="")
        d = agg.compare_periods(by="matches", n=1, min_rounds=1)
        self.assertEqual(d["by_operator"], [])
        self.assertEqual(len(d["by_map"]), 1)

    def test_trae_rating_de_cada_periodo(self):
        partida(0, cuando=AHORA - timedelta(days=10), rondas=12, kills=0)
        partida(1, cuando=AHORA - timedelta(days=1), rondas=12, kills=2)
        zofia = fila(agg.compare_periods(by="matches", n=1, min_rounds=1)["by_operator"],
                     operator="Zofia")
        self.assertGreater(zofia["current_rating"], zofia["previous_rating"])
        self.assertGreater(zofia["rating_delta"], 0)

    def test_base_vacia_devuelve_cortes_vacios(self):
        d = agg.compare_periods(by="matches", n=10)
        self.assertEqual(d["by_map"], [])
        self.assertEqual(d["by_operator"], [])

    def test_el_veredicto_del_total_no_cambia(self):
        """El veredicto se extrajo a una funcion: mismas reglas que antes."""
        self.assertIsNone(agg._veredicto(None, 1.0, "up"))
        self.assertIsNone(agg._veredicto(5.0, None, "neutral"))
        self.assertIsNone(agg._veredicto(0, None, "up"))
        self.assertEqual(agg._veredicto(5.0, 5.0, "up"), "ruido")
        self.assertEqual(agg._veredicto(-6.0, 5.0, "down"), "mejor")
        self.assertEqual(agg._veredicto(6.0, None, "down"), "peor")


class CortesApiTests(TestCase):
    def setUp(self):
        for lado, desfase in (("Attack", 0), ("Defense", 1)):
            partida(desfase, cuando=AHORA - timedelta(days=40, hours=desfase), rondas=12,
                    operador="Ash" if lado == "Attack" else "Mute", lado=lado)
            partida(2 + desfase, cuando=AHORA - timedelta(days=2, hours=desfase), rondas=12,
                    operador="Ash" if lado == "Attack" else "Mute", lado=lado)

    def test_respeta_by_days_y_el_filtro_de_lado(self):
        data = self.client.get("/api/compare/?by=days&n=30&side=Defense").json()
        self.assertEqual(data["by"], "days")
        self.assertEqual([(f["operator"], f["side"]) for f in data["by_operator"]],
                         [("Mute", "Defense")])
        self.assertEqual(data["by_map"][0]["current_rounds"], 12)

    def test_sin_filtro_de_lado_salen_los_dos(self):
        data = self.client.get("/api/compare/?by=days&n=30").json()
        self.assertEqual(len(data["by_operator"]), 2)

    def test_la_muestra_minima_por_fila_se_puede_pedir(self):
        data = self.client.get("/api/compare/?by=days&n=30&min_rows=13").json()
        self.assertEqual(data["min_rows"], 13)
        self.assertEqual(data["by_operator"], [])
        self.assertEqual(len(data["by_map"]), 1)  # el mapa junta 24 rondas por periodo
