"""Tests de las agregaciones que alimentan la API."""

from __future__ import annotations

from django.test import TestCase

from replays.analytics import aggregates as agg
from replays.models import Player, RoundPlayer

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

    def test_salud_de_datos_respeta_los_filtros(self):
        """Rondas y partidas tienen que hablar de la misma muestra."""
        otra = make_match(map_name="Villa", index=1)
        make_round_player(make_round(otra, 0))
        self.assertEqual(agg.data_health()["matches"], 2)
        filtrada = agg.data_health(map="villa")
        self.assertEqual(filtrada["matches"], 1)
        self.assertEqual(filtrada["rounds"], 1)


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
        self.assertEqual(rows[0]["rounds"], 4)
        self.assertEqual(rows[0]["kpr"], 1.0)

    def test_muestra_minima(self):
        self.assertEqual(agg.teammate_synergy(min_rounds=5), [])

    def test_un_cambio_de_nick_no_parte_la_fila(self):
        """Se agrupa por jugador, no por el nombre que tenia en esa ronda."""
        amigo = Player.objects.get(username="amigo")
        ids = list(RoundPlayer.objects.filter(player=amigo).order_by("id").values_list("id", flat=True))
        RoundPlayer.objects.filter(id__in=ids[2:]).update(username="amigo-nuevo")
        amigo.username = "amigo-nuevo"
        amigo.save()

        rows = agg.teammate_synergy(min_rounds=1)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["username"], "amigo-nuevo")
        self.assertEqual(rows[0]["rounds"], 4)


CONSULATE_Y7 = 2609221242
CONSULATE_Y10 = 418126004176


def _rondas(match, ganadas: int, total: int, *, side: str = "Attack", site: str = "1F Lobby",
            spawn: str = "Garage"):
    for n in range(total):
        rnd = make_round(match, n, side=side, won=n < ganadas, site=site)
        make_round_player(rnd, side=side, spawn=spawn)


class VersionesDeMapaTests(TestCase):
    def setUp(self):
        y7 = make_match(map_name="Consulate", map_id=CONSULATE_Y7, index=0)
        _rondas(y7, 3, 4)
        y10 = make_match(map_name="Consulate", map_id=CONSULATE_Y10, index=1)
        _rondas(y10, 0, 4)

    def test_by_map_separa_las_versiones_de_un_mapa(self):
        filas = {r["map"]: r for r in agg.by_map()}
        self.assertEqual(set(filas), {"Consulate (Y7)", "Consulate (Y10)"})
        self.assertEqual(filas["Consulate (Y7)"]["attack_winrate"], 75.0)
        self.assertEqual(filas["Consulate (Y10)"]["attack_winrate"], 0.0)
        self.assertEqual(filas["Consulate (Y10)"]["map_id"], CONSULATE_Y10)
        self.assertEqual({r["slug"] for r in filas.values()}, {"consulate"})

    def test_by_map_con_map_id_cero_no_junta_mapas_distintos(self):
        _rondas(make_match(map_name="Club House", index=2), 1, 2)
        _rondas(make_match(map_name="Border", index=3), 1, 2)
        nombres = sorted(r["map"] for r in agg.by_map())
        self.assertEqual(nombres, ["Border", "Club House", "Consulate (Y10)", "Consulate (Y7)"])

    def test_by_site_separa_el_mismo_sitio_en_dos_versiones(self):
        filas = {(r["map"], r["site"]): r["rounds"] for r in agg.by_site()}
        self.assertEqual(
            filas, {("Consulate (Y7)", "1F Lobby"): 4, ("Consulate (Y10)", "1F Lobby"): 4}
        )

    def test_by_spawn_separa_por_version(self):
        filas = {(r["map"], r["spawn"]): r["winrate"] for r in agg.by_spawn()}
        self.assertEqual(
            filas, {("Consulate (Y7)", "Garage"): 75.0, ("Consulate (Y10)", "Garage"): 0.0}
        )

    def test_el_filtro_por_slug_junta_las_versiones(self):
        self.assertEqual(agg.overview(map="consulate")["overall"]["rounds"], 8)
        self.assertEqual(len(agg.by_map(map="consulate")), 2)

    def test_el_filtro_por_map_id_elige_una_version(self):
        filas = agg.by_map(map=str(CONSULATE_Y10))
        self.assertEqual([r["map"] for r in filas], ["Consulate (Y10)"])
        self.assertEqual(agg.overview(map=str(CONSULATE_Y7))["overall"]["rounds"], 4)

    def test_clutch_por_sitio_separa_el_mismo_sitio_en_dos_versiones(self):
        for indice, map_id in ((2, CONSULATE_Y7), (3, CONSULATE_Y10)):
            match = make_match(map_name="Consulate", map_id=map_id, index=indice)
            rnd = make_round(match, 0, site="1F Lobby", won=True)
            make_round_player(rnd, clutch_vs=2)
        filas = agg.clutch_by_site()
        mapas = [(f["map"], f["map_id"], f["attempts"]) for f in filas if f["kind"] == "map"]
        sitios = [(f["map"], f["site"], f["attempts"]) for f in filas if f["kind"] == "site"]
        self.assertEqual(
            sorted(mapas), [("Consulate (Y10)", CONSULATE_Y10, 1), ("Consulate (Y7)", CONSULATE_Y7, 1)]
        )
        self.assertEqual(
            sorted(sitios), [("Consulate (Y10)", "1F Lobby", 1), ("Consulate (Y7)", "1F Lobby", 1)]
        )

    def test_un_id_nombrado_igual_que_una_version_lleva_el_id(self):
        # un rework que MAPS no conoce y que el usuario llamo "Consulate" en Datos
        conocido = make_match(map_name="Consulate", map_id=379218689149, index=2)
        _rondas(conocido, 1, 1)
        nuevo = make_match(map_name="Consulate", map_id=999, index=3)
        _rondas(nuevo, 1, 1)
        nombres = sorted(r["map"] for r in agg.by_map())
        self.assertEqual(
            nombres, ["Consulate", "Consulate (Y10)", "Consulate (Y7)", "Consulate (id 999)"]
        )


def _partidas(map_name: str, map_id: int, ganadas: int, total: int, desde: int):
    for n in range(total):
        gano = n < ganadas
        match = make_match(
            map_name=map_name, map_id=map_id, index=desde + n,
            my_score=4 if gano else 2, opponent_score=2 if gano else 4,
        )
        make_round_player(make_round(match, 0, won=gano))


class MejorYPeorMapaPorVersionTests(TestCase):
    """El Inicio cuenta por version, como Mapas: un rework no suma con el viejo."""

    def test_mejor_y_peor_mapa_separan_las_versiones(self):
        # juntas, Consulate seria 3/6 = 50 %: mejor Border y peor "Consulate"
        _partidas("Consulate", CONSULATE_Y7, 3, 3, desde=0)
        _partidas("Consulate", CONSULATE_Y10, 0, 3, desde=10)
        _partidas("Border", 0, 2, 3, desde=20)
        resumen = agg.matches_summary()
        mejor, peor = resumen["best_map"], resumen["worst_map"]
        self.assertEqual((mejor["map"], mejor["map_id"], mejor["winrate"]),
                         ("Consulate (Y7)", CONSULATE_Y7, 100.0))
        self.assertEqual((peor["map"], peor["map_id"], peor["winrate"]),
                         ("Consulate (Y10)", CONSULATE_Y10, 0.0))
        self.assertEqual(mejor["slug"], "consulate")

    def test_una_version_sin_muestra_minima_no_entra(self):
        self.assertEqual(agg.MIN_PARTIDAS_MAPA, 3)
        _partidas("Consulate", CONSULATE_Y7, 2, 2, desde=0)
        _partidas("Consulate", CONSULATE_Y10, 0, 2, desde=10)
        resumen = agg.matches_summary()
        self.assertIsNone(resumen["best_map"])
        self.assertIsNone(resumen["worst_map"])
