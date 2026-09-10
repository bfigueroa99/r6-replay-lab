"""Tests de las agregaciones que alimentan la API."""

from __future__ import annotations

from django.test import TestCase

from replays.analytics import aggregates as agg

from .factories import make_match, make_round, make_round_player


class DeriveTests(TestCase):
    def test_porcentajes_y_ratios(self):
        row = agg.derive(
            {
                "rounds": 10,
                "rounds_won": 6,
                "kills_sum": 8,
                "deaths": 4,
                "headshots_sum": 4,
                "survived_rounds": 6,
                "opening_kills": 3,
                "opening_deaths": 1,
                "trade_kills_sum": 2,
                "traded_deaths": 2,
                "untraded_deaths": 2,
                "kst_rounds": 9,
                "clutch_rounds": 1,
                "multikill_rounds": 2,
                "won_after_opening_kill": 3,
                "won_after_opening_death": 0,
                "avg_death_elapsed": 61.234,
            }
        )
        self.assertEqual(row["winrate"], 60.0)
        self.assertEqual(row["kd"], 2.0)
        self.assertEqual(row["kpr"], 0.8)
        self.assertEqual(row["hs_pct"], 50.0)
        self.assertEqual(row["survival_pct"], 60.0)
        self.assertEqual(row["opening_duels"], 4)
        self.assertEqual(row["opening_winrate"], 75.0)
        self.assertEqual(row["untraded_death_pct"], 50.0)
        self.assertEqual(row["kst_pct"], 90.0)
        self.assertEqual(row["winrate_after_opening_kill"], 100.0)
        self.assertEqual(row["winrate_after_opening_death"], 0.0)
        self.assertEqual(row["avg_death_elapsed"], 61.2)

    def test_division_por_cero_devuelve_none(self):
        row = agg.derive({"rounds": 0, "deaths": 0, "kills_sum": 0})
        self.assertIsNone(row["winrate"])
        self.assertIsNone(row["kd"])
        self.assertIsNone(row["hs_pct"])


class QuerysetTests(TestCase):
    def setUp(self):
        # 4 rondas de ataque ganadas, 2 de defensa perdidas
        self.match = make_match(map_name="Border", index=0, my_score=4, opponent_score=2)
        for n in range(4):
            rnd = make_round(self.match, n, side="Attack", won=True, site="1F Bathroom, 1F Tellers")
            make_round_player(rnd, kills=2, died=False, headshots=1, operator="Zofia")
        for n in range(4, 6):
            rnd = make_round(self.match, n, side="Defense", won=False, site="2F Armory, 2F Archives")
            make_round_player(rnd, kills=0, died=True, operator="Mute", was_traded=False)

    def test_solo_cuenta_mis_rondas(self):
        other = make_round(self.match, 9, side="Attack", won=True)
        make_round_player(other, username="alguien", is_me=False, kills=5)
        self.assertEqual(agg.base_queryset().count(), 6)

    def test_totales(self):
        row = agg.totals(agg.base_queryset())
        self.assertEqual(row["rounds"], 6)
        self.assertEqual(row["rounds_won"], 4)
        self.assertEqual(row["winrate"], 66.7)
        self.assertEqual(row["kills"], 8)
        self.assertEqual(row["deaths"], 2)
        self.assertEqual(row["kd"], 4.0)
        self.assertEqual(row["survival_pct"], 66.7)
        self.assertEqual(row["matches"], 1)

    def test_filtro_por_lado(self):
        self.assertEqual(agg.base_queryset(side="Defense").count(), 2)
        self.assertEqual(agg.totals(agg.base_queryset(side="Defense"))["winrate"], 0.0)

    def test_filtro_por_mapa_y_operador(self):
        self.assertEqual(agg.base_queryset(map="border").count(), 6)
        self.assertEqual(agg.base_queryset(map="villa").count(), 0)
        self.assertEqual(agg.base_queryset(operator="Mute").count(), 2)

    def test_agrupado_por_mapa_incluye_lados(self):
        rows = agg.by_map(min_rounds=1)
        self.assertEqual(len(rows), 1)
        row = rows[0]
        self.assertEqual(row["map"], "Border")
        self.assertEqual(row["attack_rounds"], 4)
        self.assertEqual(row["attack_winrate"], 100.0)
        self.assertEqual(row["defense_winrate"], 0.0)

    def test_agrupado_por_sitio(self):
        rows = {r["site"]: r for r in agg.by_site(min_rounds=1)}
        self.assertEqual(rows["1F Bathroom, 1F Tellers"]["winrate"], 100.0)
        self.assertEqual(rows["2F Armory, 2F Archives"]["winrate"], 0.0)

    def test_muestra_minima_filtra(self):
        self.assertEqual(agg.by_site(min_rounds=5), [])

    def test_spawn_solo_ataque(self):
        rows = agg.by_spawn(min_rounds=1)
        self.assertEqual(sum(r["rounds"] for r in rows), 4)

    def test_salud_de_datos(self):
        health = agg.data_health()
        self.assertEqual(health["rounds"], 6)
        self.assertFalse(health["assists_available"])


class TrendTests(TestCase):
    def setUp(self):
        for i in range(3):
            match = make_match(index=i, my_score=4, opponent_score=1)
            for n in range(3):
                rnd = make_round(match, n, won=(i > 0))
                make_round_player(rnd, kills=i)

    def test_serie_por_partida_va_en_orden(self):
        rows = agg.trend_by_match()
        self.assertEqual(len(rows), 3)
        self.assertLess(rows[0]["played_at"], rows[-1]["played_at"])

    def test_serie_por_dia(self):
        rows = agg.trend_by_day()
        self.assertTrue(rows)
        self.assertEqual(sum(r["rounds"] for r in rows), 9)

    def test_forma_reciente(self):
        rows = agg.recent_form(limit=2)
        self.assertEqual(len(rows), 2)
        self.assertIn(rows[0]["result"], ("victoria", "derrota", "empate"))


class SynergyTests(TestCase):
    def setUp(self):
        match = make_match(index=0)
        for n in range(4):
            rnd = make_round(match, n, won=n < 3)
            make_round_player(rnd)
            make_round_player(rnd, username="amigo", is_me=False, team_index=0, died=False)
            make_round_player(
                rnd, username="rival", is_me=False, team_index=1, died=True, won=n >= 3
            )

    def test_solo_incluye_companeros(self):
        rows = agg.teammate_synergy(min_rounds=1)
        names = {r["username"] for r in rows}
        self.assertIn("amigo", names)
        self.assertNotIn("rival", names)
        self.assertEqual(rows[0]["winrate"], 75.0)
