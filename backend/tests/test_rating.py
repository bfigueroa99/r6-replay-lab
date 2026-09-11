"""Tests del rating compuesto."""

from __future__ import annotations

from django.db.models import Avg
from django.test import TestCase

from replays.analytics import aggregates as agg
from replays.models import RoundPlayer

from .factories import make_match, make_round, make_round_player


def puntos_de(rp: RoundPlayer) -> float:
    return RoundPlayer.objects.filter(pk=rp.pk).aggregate(v=Avg(agg.rating_points_expr()))["v"]


class PuntosTests(TestCase):
    """La formula, ronda por ronda. Si cambian los pesos, estos numeros cambian."""

    def setUp(self):
        self.rnd = make_round(make_match(index=0), 0)

    def test_ronda_tipica(self):
        """1 baja y muerte sin trade: 1.0 base + 1.0 baja - 0.4 sin trade."""
        rp = make_round_player(self.rnd, kills=1, died=True, was_traded=False)
        self.assertAlmostEqual(puntos_de(rp), 1.6)

    def test_ronda_sin_nada(self):
        """Ni baja ni muerte propia: solo el piso, mas sobrevivir."""
        rp = make_round_player(self.rnd, kills=0, died=False)
        self.assertAlmostEqual(puntos_de(rp), 1.3)

    def test_peor_ronda_posible(self):
        """Apertura perdida y sin trade: 1.0 - 0.5 - 0.4. Nunca negativo."""
        rp = make_round_player(self.rnd, kills=0, died=True, opening_death=True, was_traded=False)
        self.assertAlmostEqual(puntos_de(rp), 0.1)
        self.assertGreater(puntos_de(rp), 0)

    def test_ronda_redonda(self):
        rp = make_round_player(
            self.rnd,
            kills=3,
            died=False,
            opening_kill=True,
            trade_kills=1,
            one_vx=2,
        )
        # 1.0 + 3.0 + 0.3 trade + 0.3 sobrevivir + 0.5 apertura + 0.7 clutch
        self.assertAlmostEqual(puntos_de(rp), 5.8)

    def test_la_muerte_tradeada_cuesta_menos_que_la_sola(self):
        tradeada = make_round_player(self.rnd, kills=0, died=True, was_traded=True)
        rnd2 = make_round(make_match(index=1), 0)
        sola = make_round_player(rnd2, kills=0, died=True, was_traded=False)
        self.assertGreater(puntos_de(tradeada), puntos_de(sola))


class RatingTests(TestCase):
    def setUp(self):
        match = make_match(index=0)
        # 4 rondas flojas y 2 buenas, para que el promedio no sea trivial
        for n in range(4):
            make_round_player(make_round(match, n), kills=0, died=True)
        for n in range(4, 6):
            make_round_player(make_round(match, n), kills=2, died=False)

    def test_el_historial_completo_vale_uno(self):
        """El 1.00 es, por definicion, tu propio promedio."""
        self.assertEqual(agg.totals(agg.base_queryset())["rating"], 1.0)

    def test_una_porcion_buena_pasa_de_uno(self):
        rating = agg.totals(agg.base_queryset().filter(kills__gt=0))["rating"]
        self.assertGreater(rating, 1.0)

    def test_una_porcion_mala_baja_de_uno(self):
        rating = agg.totals(agg.base_queryset().filter(kills=0))["rating"]
        self.assertLess(rating, 1.0)

    def test_la_referencia_no_depende_de_los_filtros(self):
        """Filtrar no puede mover el 1.00, o dos vistas no serian comparables."""
        base = agg.rating_baseline()
        with_filter = agg.totals(agg.base_queryset(operator="Zofia"))
        sin_filtro = agg.totals(agg.base_queryset())
        self.assertEqual(base, sin_filtro["rating_points"])
        self.assertEqual(with_filter["rating"], round(with_filter["rating_points"] / base, 2))

    def test_aparece_en_los_agrupados(self):
        filas = agg.by_operator(min_rounds=1)
        self.assertTrue(all(f["rating"] is not None for f in filas))

    def test_sin_datos_no_revienta(self):
        RoundPlayer.objects.all().delete()
        self.assertIsNone(agg.rating_baseline())
        self.assertIsNone(agg.totals(agg.base_queryset())["rating"])


class RatingPlegadoTests(TestCase):
    """Al plegar filas por partida, el rating se pondera por rondas."""

    def test_promedio_ponderado_por_rondas(self):
        una = make_match(index=0)
        for n in range(5):  # 5 rondas flojas
            make_round_player(make_round(una, n), kills=0, died=True)
        otra = make_match(index=1)
        make_round_player(make_round(otra, 0), kills=4, died=False)  # 1 ronda buenisima

        # las dos partidas caen en la misma sesion
        fila = agg.sessions()[0]
        esperado = agg.rating_baseline()  # son todas las rondas del historial
        self.assertEqual(fila["rating_points"], round(esperado, 3))
        self.assertEqual(fila["rating"], 1.0)


class RatingApiTests(TestCase):
    def setUp(self):
        match = make_match(index=0)
        for n in range(4):
            make_round_player(make_round(match, n), kills=n)

    def test_overview_y_partidas_traen_rating(self):
        overview = self.client.get("/api/overview/").json()
        self.assertEqual(overview["overall"]["rating"], 1.0)
        self.assertIsNotNone(overview["recent_form"][0]["rating"])

        partidas = self.client.get("/api/matches/").json()
        self.assertIsNotNone(partidas["matches"][0]["my_rating"])

    def test_los_pesos_estan_expuestos(self):
        """Los pesos son un juicio: tienen que poder leerse y discutirse."""
        self.assertEqual(agg.RATING_WEIGHTS["kill"], 1.0)
        self.assertLess(agg.RATING_WEIGHTS["untraded_death"], 0)
