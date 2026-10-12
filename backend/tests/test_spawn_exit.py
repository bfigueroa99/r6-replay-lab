"""Tests de la salida del spawn y su cruce con peekabooR6."""

from __future__ import annotations

from django.test import TestCase

from replays.analytics import aggregates as agg
from replays.analytics.coach import build_insights
from replays.models import RoundPlayer

from .factories import ME, make_event, make_match, make_round, make_round_player


def find(payload, key):
    return next((i for i in payload["insights"] if i["key"] == key), None)


def fila(datos, mapa):
    return next(f for f in datos["maps"] if f["map"] == mapa)


class SalidaDelSpawnTests(TestCase):
    def setUp(self):
        self.partidas = {}
        self.n = 0

    def ronda(self, mapa="Club House", *, side="Attack", elapsed=None, rival=False):
        """Una ronda tuya; `elapsed` None es que sobreviviste."""
        if mapa not in self.partidas:
            self.partidas[mapa] = make_match(map_name=mapa, index=len(self.partidas))
        rnd = make_round(self.partidas[mapa], self.n, side=side)
        self.n += 1
        make_round_player(
            rnd, side=side, died=elapsed is not None, death_elapsed=elapsed, kills=0
        )
        if rival:
            make_round_player(
                rnd,
                username="rival",
                is_me=False,
                team_index=1,
                side="Defense" if side == "Attack" else "Attack",
            )
        return rnd

    def test_cuenta_las_muertes_tempranas_por_mapa_y_lado(self):
        self.ronda(side="Attack", elapsed=8)
        self.ronda(side="Attack", elapsed=40)
        self.ronda(side="Defense", elapsed=12)
        self.ronda(side="Defense")
        self.ronda("Border", side="Attack", elapsed=14.9)

        datos = agg.spawn_exit()
        self.assertEqual(datos["seconds"], 15)
        club = fila(datos, "Club House")
        self.assertEqual(club["slug"], "club-house")
        self.assertEqual((club["attack_rounds"], club["attack_early_deaths"]), (2, 1))
        self.assertEqual(club["attack_early_death_pct"], 50.0)
        self.assertEqual((club["defense_rounds"], club["defense_early_deaths"]), (2, 1))
        border = fila(datos, "Border")
        self.assertEqual(border["attack_early_death_pct"], 100.0)
        self.assertEqual(border["defense_rounds"], 0)
        self.assertIsNone(border["defense_early_death_pct"])

    def test_el_porcentaje_es_sobre_rondas_y_no_sobre_muertes(self):
        """Sobrevivir tambien es una ronda que pasaste la salida."""
        self.ronda(elapsed=5)
        self.ronda()
        self.ronda()
        self.ronda()
        self.assertEqual(fila(agg.spawn_exit(), "Club House")["attack_early_death_pct"], 25.0)

    def test_el_borde_de_la_ventana_no_entra(self):
        self.ronda(elapsed=15)
        self.assertEqual(fila(agg.spawn_exit(), "Club House")["attack_early_deaths"], 0)

    def test_una_muerte_sin_reloj_no_es_una_muerte_al_salir(self):
        """La ingesta deja elapsed 0 cuando el evento no traia reloj."""
        self.ronda(elapsed=5)
        RoundPlayer.objects.filter(is_me=True).update(death_clock=0.0, death_elapsed=0.0)
        self.assertEqual(fila(agg.spawn_exit(), "Club House")["attack_early_deaths"], 0)

    def test_cuenta_tus_bajas_tempranas_y_no_los_teamkills(self):
        rnd = self.ronda(side="Defense", rival=True)
        make_event(rnd, 0, ME, "rival", clock=172.0)  # 8s: tu spawnpeek salio
        otra = self.ronda(side="Defense", rival=True)
        make_event(otra, 0, ME, "rival", clock=120.0)  # 60s: ya no es la salida
        tk = self.ronda(side="Defense")
        make_round_player(tk, username="amigo", is_me=False, team_index=0)
        make_event(tk, 0, ME, "amigo", clock=175.0)

        club = fila(agg.spawn_exit(), "Club House")
        self.assertEqual(club["defense_early_kills"], 1)
        self.assertEqual(club["attack_early_kills"], 0)

    def test_el_total_junta_todos_los_mapas(self):
        self.ronda(elapsed=5)
        self.ronda("Border", elapsed=50)
        self.ronda("Border", side="Defense", elapsed=3)
        total = agg.spawn_exit()["overall"]
        self.assertEqual((total["attack_rounds"], total["attack_early_deaths"]), (2, 1))
        self.assertEqual(total["attack_early_death_pct"], 50.0)
        self.assertEqual(total["defense_early_death_pct"], 100.0)

    def test_el_mapa_con_mas_rondas_va_primero(self):
        self.ronda("Border")
        self.ronda()
        self.ronda()
        self.assertEqual([f["map"] for f in agg.spawn_exit()["maps"]], ["Club House", "Border"])

    def test_respeta_los_filtros(self):
        self.ronda(elapsed=5)
        self.ronda("Border", elapsed=5)
        datos = agg.spawn_exit(map="border")
        self.assertEqual([f["map"] for f in datos["maps"]], ["Border"])
        self.assertEqual(datos["overall"]["attack_rounds"], 1)

    def test_sin_datos_no_revienta(self):
        datos = agg.spawn_exit()
        self.assertEqual(datos["maps"], [])
        self.assertEqual(datos["overall"]["attack_rounds"], 0)
        self.assertIsNone(datos["overall"]["attack_early_death_pct"])


class SalidaDelSpawnApiTests(TestCase):
    def setUp(self):
        for i, mapa in enumerate(("Border", "Tower")):
            self.partida = make_match(map_name=mapa, index=i)
            make_round_player(make_round(self.partida, 0), death_elapsed=6)

    def test_tendencias_trae_la_salida_con_el_enlace_de_cada_mapa(self):
        datos = self.client.get("/api/trends/").json()["spawn_exit"]
        enlaces = {f["map"]: f["peeks_url"] for f in datos["maps"]}
        self.assertEqual(enlaces["Border"], "https://peekaboor6.com/maps/border")
        # peekabooR6 no tiene Tower: sin enlace antes que un 404
        self.assertIsNone(enlaces["Tower"])

    def test_el_detalle_de_la_partida_enlaza_a_su_mapa(self):
        border = self.client.get("/api/matches/").json()["matches"]
        ids = {m["map"]: m["id"] for m in border}
        match = self.client.get(f"/api/matches/{ids['Border']}/").json()["match"]
        self.assertEqual(match["peeks_url"], "https://peekaboor6.com/maps/border")
        tower = self.client.get(f"/api/matches/{ids['Tower']}/").json()["match"]
        self.assertIsNone(tower["peeks_url"])

    def test_se_exporta_a_csv(self):
        respuesta = self.client.get("/api/export/?table=spawn_exit")
        self.assertEqual(respuesta.status_code, 200)
        cabecera, *filas = respuesta.content.decode().strip().splitlines()
        self.assertTrue(cabecera.startswith("map,slug,"))
        self.assertIn("attack_early_death_pct", cabecera)
        self.assertEqual(len(filas), 2)


class CoachSalidaDelSpawnTests(TestCase):
    def historial(self, tempranas, *, side="Attack", rondas=20):
        """Rondas por mapa y cuantas de ellas mueres en la salida."""
        n = 0
        for i, (mapa, muertes) in enumerate(tempranas.items()):
            partida = make_match(map_name=mapa, index=i)
            for j in range(rondas):
                rnd = make_round(partida, n, side=side, won=j % 2 == 0)
                n += 1
                make_round_player(rnd, side=side, death_elapsed=6 if j < muertes else 90)

    def test_avisa_del_mapa_donde_la_ronda_se_corta_al_salir(self):
        self.historial({"Border": 10, "Club House": 1})
        insight = find(build_insights(), "salida-spawn-ataque")
        self.assertIsNotNone(insight)
        self.assertIn("Border", insight["title"])
        self.assertEqual(insight["value"], 50.0)
        self.assertEqual(insight["baseline"], 5.0)
        self.assertEqual(insight["sample"], 20)
        self.assertEqual(
            insight["link"],
            {
                "label": "Spawn peeks de Border en peekabooR6",
                "url": "https://peekaboor6.com/maps/border",
            },
        )

    def test_en_defensa_es_su_propia_regla(self):
        self.historial({"Border": 10, "Club House": 1}, side="Defense")
        payload = build_insights()
        self.assertIsNotNone(find(payload, "salida-spawn-defensa"))
        self.assertIsNone(find(payload, "salida-spawn-ataque"))

    def test_una_diferencia_dentro_del_ruido_no_dispara(self):
        self.historial({"Border": 5, "Club House": 3})
        self.assertIsNone(find(build_insights(), "salida-spawn-ataque"))

    def test_no_opina_con_pocas_rondas_en_el_mapa(self):
        self.historial({"Border": 8, "Club House": 0, "Bank": 0}, rondas=10)
        self.assertIsNone(find(build_insights(), "salida-spawn-ataque"))

    def test_un_mapa_sin_pagina_en_peekaboo_avisa_igual_sin_enlace(self):
        self.historial({"Tower": 10, "Club House": 1})
        insight = find(build_insights(), "salida-spawn-ataque")
        self.assertIn("Tower", insight["title"])
        self.assertIsNone(insight["link"])

    def test_spawn_debil_enlaza_a_los_peeks_del_mapa(self):
        partida = make_match(map_name="Club House", index=0)
        n = 0
        for spawn, gano in (("Warehouse", False), ("Muddy Road", True), ("Construction", True)):
            for _ in range(10):
                rnd = make_round(partida, n, won=gano)
                n += 1
                make_round_player(rnd, spawn=spawn)
        insight = find(build_insights(), "spawn-debil")
        self.assertEqual(insight["link"]["url"], "https://peekaboor6.com/maps/clubhouse")

    def test_las_reglas_sin_mapa_no_traen_enlace(self):
        insight = build_insights()["insights"][0]
        self.assertEqual(insight["key"], "sin-datos")
        self.assertIsNone(insight["link"])
