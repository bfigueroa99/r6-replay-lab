"""Tests del perfil de un jugador dentro de tus partidas."""

from __future__ import annotations

from django.test import TestCase

from replays.analytics import aggregates as agg
from replays.models import Player

from .factories import ME, make_event, make_match, make_round, make_round_player


class PerfilTests(TestCase):
    def setUp(self):
        self.match = make_match(map_name="Bank", index=0)
        # 3 rondas con "amigo" en mi equipo, ganadas
        for n in range(3):
            rnd = make_round(self.match, n, won=True)
            make_round_player(rnd, kills=2)
            make_round_player(
                rnd, username="amigo", is_me=False, team_index=0, operator="Smoke", kills=1
            )
        # 2 rondas sin el, perdidas
        for n in range(3, 5):
            make_round_player(make_round(self.match, n, won=False), kills=0)

        self.amigo = Player.objects.get(username="amigo")

    def test_separa_con_y_sin(self):
        perfil = agg.player_profile(self.amigo.id)
        self.assertEqual(perfil["rounds_together"], 3)
        self.assertEqual(perfil["rounds_against"], 0)
        self.assertEqual(perfil["with"]["winrate"], 100.0)
        self.assertEqual(perfil["without"]["winrate"], 0.0)
        self.assertEqual(perfil["without"]["rounds"], 2)

    def test_sus_numeros_van_sin_rating(self):
        """El 1.00 es tu promedio: aplicado a otro no significa nada."""
        perfil = agg.player_profile(self.amigo.id)
        self.assertEqual(perfil["theirs"]["kills"], 3)
        self.assertIsNone(perfil["theirs"]["rating"])
        self.assertIsNone(perfil["theirs"]["rating_points"])
        self.assertIsNotNone(perfil["with"]["rating"])

    def test_sus_operadores(self):
        perfil = agg.player_profile(self.amigo.id)
        self.assertEqual(perfil["their_operators"][0]["operator"], "Smoke")
        self.assertEqual(perfil["their_operators"][0]["rounds"], 3)
        self.assertIsNone(perfil["their_operators"][0]["rating"])

    def test_partidas_compartidas(self):
        perfil = agg.player_profile(self.amigo.id)
        self.assertEqual(len(perfil["matches"]), 1)
        fila = perfil["matches"][0]
        self.assertEqual(fila["map"], "Bank")
        self.assertEqual(fila["role"], "companero")
        self.assertEqual(fila["rounds"], 3)

    def test_sin_duelos_no_inventa(self):
        self.assertIsNone(agg.player_profile(self.amigo.id)["duels"])

    def test_jugador_inexistente(self):
        self.assertIsNone(agg.player_profile(99999))

    def test_respeta_los_filtros(self):
        self.assertEqual(agg.player_profile(self.amigo.id, map="bank")["rounds_together"], 3)
        self.assertEqual(agg.player_profile(self.amigo.id, map="villa")["rounds_together"], 0)


class PerfilRivalTests(TestCase):
    def setUp(self):
        match = make_match(index=0)
        for n in range(4):
            rnd = make_round(match, n)
            make_round_player(rnd)
            make_round_player(
                rnd, username="rival", is_me=False, team_index=1, side="Defense", operator="Thorn"
            )
            make_event(rnd, 0, "rival", ME)
        self.rival = Player.objects.get(username="rival")

    def test_cuenta_las_rondas_en_contra(self):
        perfil = agg.player_profile(self.rival.id)
        self.assertEqual(perfil["rounds_together"], 0)
        self.assertEqual(perfil["rounds_against"], 4)
        self.assertEqual(perfil["against"]["rounds"], 4)

    def test_trae_los_duelos(self):
        duels = agg.player_profile(self.rival.id)["duels"]
        self.assertEqual(duels["deaths"], 4)
        self.assertEqual(duels["kills"], 0)
        self.assertEqual(duels["balance"], -4)

    def test_la_partida_queda_marcada_como_rival(self):
        self.assertEqual(agg.player_profile(self.rival.id)["matches"][0]["role"], "rival")


class PerfilMixtoTests(TestCase):
    """Alguien que fue companero en una partida y rival en otra."""

    def setUp(self):
        juntos = make_match(map_name="Bank", index=0)
        rnd = make_round(juntos, 0)
        make_round_player(rnd)
        make_round_player(rnd, username="mixto", is_me=False, team_index=0)

        aparte = make_match(map_name="Villa", index=1)
        rnd = make_round(aparte, 0)
        make_round_player(rnd)
        make_round_player(rnd, username="mixto", is_me=False, team_index=1)

        self.mixto = Player.objects.get(username="mixto")

    def test_cada_partida_dice_de_que_lado_estuvo(self):
        perfil = agg.player_profile(self.mixto.id)
        roles = {m["map"]: m["role"] for m in perfil["matches"]}
        self.assertEqual(roles, {"Bank": "companero", "Villa": "rival"})
        self.assertEqual(perfil["rounds_together"], 1)
        self.assertEqual(perfil["rounds_against"], 1)


class PerfilApiTests(TestCase):
    def setUp(self):
        match = make_match(index=0)
        rnd = make_round(match, 0)
        make_round_player(rnd)
        make_round_player(rnd, username="amigo", is_me=False, team_index=0)
        self.amigo = Player.objects.get(username="amigo")

    def test_endpoint(self):
        data = self.client.get(f"/api/players/{self.amigo.id}/").json()
        self.assertEqual(data["player"]["username"], "amigo")
        self.assertFalse(data["player"]["is_me"])
        self.assertEqual(data["rounds_together"], 1)

    def test_jugador_inexistente_da_404(self):
        self.assertEqual(self.client.get("/api/players/99999/").status_code, 404)

    def test_mi_propio_perfil_se_marca(self):
        yo = Player.objects.get(username=ME)
        data = self.client.get(f"/api/players/{yo.id}/").json()
        self.assertTrue(data["player"]["is_me"])
