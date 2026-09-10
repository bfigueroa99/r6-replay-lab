"""Tests de la API: contratos de respuesta y filtros."""

from __future__ import annotations

import json

from django.test import TestCase

from replays.models import Match

from .factories import make_event, make_match, make_round, make_round_player


class EmptyApiTests(TestCase):
    """Con la base vacia todo tiene que responder 200, no reventar."""

    ENDPOINTS = [
        "/api/health/",
        "/api/filters/",
        "/api/overview/",
        "/api/coach/",
        "/api/maps/",
        "/api/operators/",
        "/api/trends/",
        "/api/teammates/",
        "/api/matches/",
        "/api/import/status/",
    ]

    def test_todos_responden(self):
        for url in self.ENDPOINTS:
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertEqual(response.status_code, 200)
                self.assertIsInstance(json.loads(response.content), dict)

    def test_partida_inexistente_da_404(self):
        self.assertEqual(self.client.get("/api/matches/999/").status_code, 404)


class PopulatedApiTests(TestCase):
    def setUp(self):
        self.match = make_match(map_name="Club House", index=0, my_score=4, opponent_score=2)
        for n in range(6):
            side = "Attack" if n % 2 == 0 else "Defense"
            rnd = make_round(self.match, n, side=side, won=n < 4)
            make_round_player(rnd, side=side, kills=1, headshots=1, opening_kill=n == 0)
            make_round_player(rnd, username="rival", is_me=False, team_index=1, side=side)
            make_event(rnd, 0, "BearF99", "rival", clock=140.0, headshot=True)

        other = make_match(map_name="Border", index=1, my_score=2, opponent_score=4)
        rnd = make_round(other, 0, side="Defense", won=False, site="1F Bathroom, 1F Tellers")
        make_round_player(rnd, side="Defense", operator="Mute", kills=0)

    def test_health_reporta_el_jugador(self):
        data = self.client.get("/api/health/").json()
        self.assertEqual(data["player"], "BearF99")
        self.assertEqual(data["matches"], 2)
        self.assertEqual(data["rounds"], 7)

    def test_overview_trae_general_ataque_y_defensa(self):
        data = self.client.get("/api/overview/").json()
        self.assertEqual(data["overall"]["rounds"], 7)
        self.assertEqual(data["attack"]["rounds"], 3)
        self.assertEqual(data["defense"]["rounds"], 4)
        self.assertIn("data_health", data)
        self.assertIn("recent_form", data)

    def test_overview_respeta_el_filtro_de_lado(self):
        data = self.client.get("/api/overview/?side=Attack").json()
        self.assertEqual(data["overall"]["rounds"], 3)

    def test_overview_respeta_el_filtro_de_mapa(self):
        data = self.client.get("/api/overview/?map=border").json()
        self.assertEqual(data["overall"]["rounds"], 1)

    def test_filters_lista_opciones_reales(self):
        data = self.client.get("/api/filters/").json()
        self.assertIn("Mute", data["operators"])
        slugs = {m["map_slug"] for m in data["maps"]}
        self.assertEqual(slugs, {"club-house", "border"})
        self.assertEqual(data["match_types"], ["Ranked"])

    def test_lista_de_partidas(self):
        data = self.client.get("/api/matches/").json()
        self.assertEqual(data["total"], 2)
        first = data["matches"][0]
        self.assertIn(first["result"], ("victoria", "derrota", "empate"))
        self.assertEqual(first["score"], f"{first['my_score']}-{first['opponent_score']}")

    def test_lista_pagina(self):
        data = self.client.get("/api/matches/?limit=1&offset=1").json()
        self.assertEqual(len(data["matches"]), 1)
        self.assertEqual(data["offset"], 1)

    def test_detalle_de_partida(self):
        data = self.client.get(f"/api/matches/{self.match.id}/").json()
        self.assertEqual(data["match"]["map"], "Club House")
        self.assertEqual(len(data["rounds"]), 6)
        first = data["rounds"][0]
        self.assertEqual(first["label"], "R1")
        self.assertEqual(len(first["events"]), 1)
        self.assertEqual(first["events"][0]["actor"], "BearF99")
        self.assertTrue(any(p["is_me"] for p in first["players"]))
        self.assertTrue(data["scoreboard"])
        self.assertEqual(data["my_totals"]["rounds"], 6)

    def test_mapas_sitios_y_spawns(self):
        data = self.client.get("/api/maps/?min_rounds=1").json()
        self.assertEqual({r["map"] for r in data["maps"]}, {"Club House", "Border"})
        self.assertTrue(data["sites"])
        self.assertTrue(data["spawns"])

    def test_trends(self):
        data = self.client.get("/api/trends/").json()
        self.assertTrue(data["by_match"])
        self.assertTrue(data["by_day"])
        self.assertTrue(data["by_round_number"])

    def test_coach_devuelve_estructura_estable(self):
        data = self.client.get("/api/coach/").json()
        self.assertIn("insights", data)
        self.assertIn("totals", data)
        for insight in data["insights"]:
            self.assertEqual(
                set(insight) >= {"key", "severity", "title", "detail", "action"}, True
            )


class ImportEndpointTests(TestCase):
    def test_import_status_no_falla_sin_carpeta(self):
        with self.settings(REPLAY_DIR="/ruta/que/no/existe"):
            data = self.client.get("/api/import/status/").json()
            self.assertEqual(data["folders_on_disk"], 0)
            self.assertEqual(data["pending"], [])

    def test_import_requiere_post(self):
        self.assertEqual(self.client.get("/api/import/").status_code, 405)

    def test_import_sin_replays_no_importa_nada(self):
        with self.settings(REPLAY_DIR="/ruta/que/no/existe"):
            data = self.client.post("/api/import/").json()
            self.assertEqual(data["count"], 0)
            self.assertEqual(Match.objects.count(), 0)


class SpaTests(TestCase):
    def test_la_raiz_sirve_algo_util(self):
        """Con el front compilado devuelve index.html; sin compilar, instrucciones."""
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        body = (
            b"".join(response.streaming_content)
            if response.streaming
            else response.content
        )
        self.assertIn(b"R6 Replay Lab", body)

    def test_no_se_puede_salir_del_dist(self):
        response = self.client.get("/../backend/config/settings.py")
        self.assertEqual(response.status_code, 200)  # cae al index del SPA
        body = (
            b"".join(response.streaming_content)
            if response.streaming
            else response.content
        )
        self.assertNotIn(b"SECRET_KEY", body)
