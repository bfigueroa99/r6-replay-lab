"""Tests del motor de insights: cada regla se dispara solo cuando corresponde."""

from __future__ import annotations

from django.test import TestCase

from replays.analytics.coach import build_insights

from .factories import make_match, make_round, make_round_player


def keys(payload: dict) -> set[str]:
    return {i["key"] for i in payload["insights"]}


def find(payload: dict, key: str) -> dict | None:
    for insight in payload["insights"]:
        if insight["key"] == key:
            return insight
    return None


def seed(rounds: int, *, index: int = 0, **player_kwargs):
    """Crea `rounds` rondas identicas y devuelve la partida."""
    won = player_kwargs.pop("won_round", True)
    side = player_kwargs.pop("side", "Attack")
    map_name = player_kwargs.pop("map_name", "Club House")
    match = make_match(map_name=map_name, index=index)
    for n in range(rounds):
        rnd = make_round(match, n, side=side, won=won)
        make_round_player(rnd, side=side, **player_kwargs)
    return match


class SampleSizeTests(TestCase):
    def test_menos_de_20_rondas_no_saca_conclusiones(self):
        seed(10)
        payload = build_insights()
        self.assertEqual(keys(payload), {"sin-datos"})

    def test_sin_datos_no_revienta(self):
        payload = build_insights()
        self.assertEqual(keys(payload), {"sin-datos"})
        self.assertEqual(payload["totals"]["rounds"], 0)


class OpeningDuelRuleTests(TestCase):
    def test_perder_las_aperturas_dispara_alerta(self):
        seed(24, opening_death=True, kills=0, died=True)
        insight = find(build_insights(), "duelos-apertura")
        self.assertIsNotNone(insight)
        self.assertEqual(insight["severity"], "alta")
        self.assertEqual(insight["value"], 0.0)
        self.assertGreaterEqual(insight["sample"], 20)

    def test_ganarlas_sale_como_positivo(self):
        seed(24, opening_kill=True, kills=2, died=False)
        insight = find(build_insights(), "duelos-apertura-fuerte")
        self.assertIsNotNone(insight)
        self.assertEqual(insight["severity"], "positivo")

    def test_sin_duelos_suficientes_no_opina(self):
        seed(24, opening_kill=False, opening_death=False)
        self.assertIsNone(find(build_insights(), "duelos-apertura"))


class TradeRuleTests(TestCase):
    def test_muertes_sin_trade(self):
        seed(40, died=True, was_traded=False, kills=1)
        insight = find(build_insights(), "muertes-sin-trade")
        self.assertIsNotNone(insight)
        self.assertEqual(insight["value"], 100.0)

    def test_muertes_tradeadas_es_positivo(self):
        seed(40, died=True, was_traded=True, kills=1)
        insight = find(build_insights(), "muertes-tradeadas")
        self.assertIsNotNone(insight)
        self.assertEqual(insight["severity"], "positivo")


class DeathTimingRuleTests(TestCase):
    def test_morir_temprano_en_ataque(self):
        seed(24, side="Attack", died=True, death_elapsed=20.0)
        insight = find(build_insights(), "muerte-temprana-ataque")
        self.assertIsNotNone(insight)
        self.assertEqual(insight["value"], 20.0)

    def test_morir_tarde_no_alerta(self):
        seed(24, side="Attack", died=True, death_elapsed=150.0)
        self.assertIsNone(find(build_insights(), "muerte-temprana-ataque"))


class SideBalanceRuleTests(TestCase):
    def test_desbalance_entre_lados(self):
        match = make_match(index=0)
        for n in range(30):
            rnd = make_round(match, n, side="Attack", won=False)
            make_round_player(rnd, side="Attack")
        for n in range(30, 60):
            rnd = make_round(match, n, side="Defense", won=True)
            make_round_player(rnd, side="Defense")
        insight = find(build_insights(), "desbalance-lados")
        self.assertIsNotNone(insight)
        self.assertEqual(insight["scope"], "ataque")

    def test_lados_parejos_no_alertan(self):
        match = make_match(index=0)
        for n in range(60):
            side = "Attack" if n % 2 == 0 else "Defense"
            rnd = make_round(match, n, side=side, won=n % 4 < 2)
            make_round_player(rnd, side=side)
        self.assertIsNone(find(build_insights(), "desbalance-lados"))


class AimRuleTests(TestCase):
    def test_pocos_headshots(self):
        seed(45, kills=1, headshots=0)
        insight = find(build_insights(), "headshots")
        self.assertIsNotNone(insight)
        self.assertEqual(insight["value"], 0.0)

    def test_muchos_headshots_es_positivo(self):
        seed(45, kills=1, headshots=1)
        insight = find(build_insights(), "headshots-fuerte")
        self.assertIsNotNone(insight)


class ImpactRuleTests(TestCase):
    def test_kst_bajo(self):
        seed(45, kills=0, died=True, was_traded=False)
        insight = find(build_insights(), "kst")
        self.assertIsNotNone(insight)
        self.assertEqual(insight["value"], 0.0)

    def test_sin_clutches(self):
        seed(45, kills=0, died=True, one_vx=0)
        self.assertIsNotNone(find(build_insights(), "sin-clutches"))


class MapRuleTests(TestCase):
    def setUp(self):
        # 18 rondas ganadas en Club House, 18 perdidas en Border
        good = make_match(map_name="Club House", index=0)
        for n in range(18):
            rnd = make_round(good, n, won=True)
            make_round_player(rnd)
        bad = make_match(map_name="Border", index=1)
        for n in range(18):
            rnd = make_round(bad, n, won=False)
            make_round_player(rnd)

    def test_detecta_el_peor_mapa(self):
        insight = find(build_insights(), "mapa-debil")
        self.assertIsNotNone(insight)
        self.assertEqual(insight["scope"], "Border")

    def test_detecta_el_mejor_mapa(self):
        insight = find(build_insights(), "mapa-fuerte")
        self.assertIsNotNone(insight)
        self.assertEqual(insight["scope"], "Club House")

    def test_filtro_por_mapa_deja_un_solo_mapa_y_no_compara(self):
        payload = build_insights(map="border")
        self.assertIsNone(find(payload, "mapa-debil"))


class OperatorRuleTests(TestCase):
    def setUp(self):
        good = make_match(index=0)
        for n in range(15):
            rnd = make_round(good, n, won=True)
            make_round_player(rnd, operator="Ela", kills=2)
        bad = make_match(index=1)
        for n in range(15):
            rnd = make_round(bad, n, won=False)
            make_round_player(rnd, operator="Kaid", kills=0)

    def test_operador_debil_y_fuerte(self):
        payload = build_insights()
        weak = find(payload, "operador-debil")
        strong = find(payload, "operador-fuerte")
        self.assertEqual(weak["scope"], "Kaid")
        self.assertEqual(strong["scope"], "Ela")


class OrderingTests(TestCase):
    def test_los_positivos_van_al_final(self):
        seed(45, kills=1, headshots=1, died=True, was_traded=False, opening_death=True)
        insights = build_insights()["insights"]
        order = {"alta": 0, "media": 1, "baja": 2, "positivo": 3}
        severities = [i["severity"] for i in insights]
        self.assertEqual(severities, sorted(severities, key=lambda s: order[s]))
        self.assertIn("alta", severities)
        self.assertEqual(severities[-1], "positivo")

    def test_todo_insight_trae_accion(self):
        seed(45, kills=1, died=True)
        for insight in build_insights()["insights"]:
            self.assertTrue(insight["action"], insight["key"])
            self.assertTrue(insight["title"], insight["key"])
