"""Tests de los teamkills: a quien mataste y quien te mato de tu propio equipo."""

from __future__ import annotations

from django.test import TestCase

from replays.analytics import aggregates as agg
from replays.recompute import recompute

from .factories import ME, make_event, make_match, make_round, make_round_player


class TeamkillsTests(TestCase):
    def setUp(self):
        self.match = make_match(index=0)

    def _ronda(self, numero, *, side="Attack", won=True, amigo="amigo", rival="rival"):
        """Ronda con vos, un companero en tu equipo y un rival enfrente."""
        rnd = make_round(self.match, numero, side=side, won=won)
        make_round_player(rnd)
        make_round_player(rnd, username=amigo, is_me=False, team_index=0)
        make_round_player(
            rnd,
            username=rival,
            is_me=False,
            team_index=1,
            side="Defense" if side == "Attack" else "Attack",
        )
        return rnd

    def test_un_teamkill_tuyo_cuenta_como_hecho(self):
        rnd = self._ronda(0)
        make_event(rnd, 0, ME, "amigo")

        tk = agg.teamkills()
        self.assertEqual(tk["mine"], 1)
        self.assertEqual(tk["suffered"], 0)
        self.assertEqual(
            tk["by_teammate"],
            [{"player_id": tk["by_teammate"][0]["player_id"], "username": "amigo",
              "made": 1, "suffered": 0, "total": 1}],
        )

    def test_un_teamkill_sufrido_cuenta_como_sufrido(self):
        rnd = self._ronda(0)
        make_event(rnd, 0, "amigo", ME)

        tk = agg.teamkills()
        self.assertEqual(tk["mine"], 0)
        self.assertEqual(tk["suffered"], 1)
        self.assertEqual(tk["by_teammate"][0]["suffered"], 1)
        self.assertEqual(tk["by_teammate"][0]["made"], 0)

    def test_la_misma_persona_como_rival_no_suma(self):
        rnd = self._ronda(0)
        make_event(rnd, 0, "amigo", ME)
        # en otra ronda "amigo" juega enfrente: su baja sobre ti es un duelo
        otra = self._ronda(1, amigo="otro", rival="amigo")
        make_event(otra, 0, "amigo", ME)

        tk = agg.teamkills()
        self.assertEqual(tk["suffered"], 1)
        self.assertEqual(tk["rounds_with"], 1)
        self.assertEqual(tk["by_teammate"][0]["total"], 1)

    def test_las_rondas_con_teamkill_tienen_su_winrate_aparte(self):
        perdida = self._ronda(0, won=False)
        make_event(perdida, 0, ME, "amigo")
        self._ronda(1, won=True)
        self._ronda(2, won=False)

        tk = agg.teamkills()
        self.assertEqual(tk["rounds_with"], 1)
        self.assertEqual(tk["rounds_without"], 2)
        self.assertEqual(tk["winrate_with"], 0.0)
        self.assertEqual(tk["winrate_without"], 50.0)

    def test_un_teamkill_entre_companeros_cuenta_la_ronda_pero_no_la_tabla(self):
        rnd = self._ronda(0)
        make_round_player(rnd, username="tercero", is_me=False, team_index=0)
        make_event(rnd, 0, "tercero", "amigo")

        tk = agg.teamkills()
        self.assertEqual(tk["rounds_with"], 1)
        self.assertEqual(tk["mine"] + tk["suffered"], 0)
        self.assertEqual(tk["by_teammate"], [])

    def test_un_suicidio_no_es_teamkill(self):
        rnd = self._ronda(0)
        make_event(rnd, 0, ME, ME)

        self.assertEqual(agg.teamkills()["rounds_with"], 0)

    def test_las_bajas_sobre_rivales_no_cuentan(self):
        rnd = self._ronda(0)
        make_event(rnd, 0, ME, "rival")
        make_event(rnd, 1, "rival", ME)

        tk = agg.teamkills()
        self.assertEqual(tk["mine"] + tk["suffered"] + tk["rounds_with"], 0)

    def test_ordena_por_total_y_despues_por_nick(self):
        rnd = self._ronda(0, amigo="zeta")
        make_round_player(rnd, username="beto", is_me=False, team_index=0)
        make_round_player(rnd, username="alba", is_me=False, team_index=0)
        make_event(rnd, 0, ME, "zeta")
        make_event(rnd, 1, "zeta", ME)
        make_event(rnd, 2, ME, "beto")
        make_event(rnd, 3, ME, "alba")

        nicks = [f["username"] for f in agg.teamkills()["by_teammate"]]
        self.assertEqual(nicks, ["zeta", "alba", "beto"])

    def test_una_baja_sin_victima_o_sin_autor_no_es_teamkill(self):
        rnd = self._ronda(0)
        make_event(rnd, 0, ME, "")
        make_event(rnd, 1, "", ME)

        self.assertEqual(agg.teamkills()["rounds_with"], 0)

    def test_respeta_el_filtro_de_lado(self):
        rnd = self._ronda(0, side="Defense")
        make_event(rnd, 0, ME, "amigo")
        self._ronda(1, side="Attack")

        tk = self.client.get("/api/teammates/?side=Attack").json()["teamkills"]
        self.assertEqual(tk["mine"], 0)
        self.assertEqual(tk["rounds_with"], 0)
        self.assertEqual(tk["by_teammate"], [])
        todo = self.client.get("/api/teammates/").json()["teamkills"]
        self.assertEqual(todo["mine"], 1)

    def test_sin_teamkills_devuelve_ceros_y_lista_vacia(self):
        self._ronda(0)

        tk = agg.teamkills()
        self.assertEqual(tk["mine"], 0)
        self.assertEqual(tk["suffered"], 0)
        self.assertEqual(tk["rounds_with"], 0)
        self.assertEqual(tk["rounds_without"], 1)
        self.assertIsNone(tk["winrate_with"])
        self.assertEqual(tk["by_teammate"], [])

    def test_el_panel_de_teamkills_no_cambia_al_sacarlos_de_las_bajas(self):
        """El panel lee `Event`, no `kills`: recalcular las bajas no lo mueve."""
        rnd = self._ronda(0)
        make_event(rnd, 0, ME, "amigo")
        make_event(rnd, 1, "amigo", ME, clock=100.0)
        make_event(rnd, 2, ME, "rival", clock=90.0)
        antes = agg.teamkills()
        recompute(window=3.0)
        self.assertEqual(agg.teamkills(), antes)

    def test_con_base_vacia_no_falla(self):
        tk = self.client.get("/api/teammates/").json()["teamkills"]
        self.assertEqual(tk["mine"], 0)
        self.assertEqual(tk["by_teammate"], [])
