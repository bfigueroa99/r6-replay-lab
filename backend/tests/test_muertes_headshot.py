"""Muertes por headshot: de tus muertes a manos de rivales, cuantas fueron headshot."""

from __future__ import annotations

from django.test import TestCase

from replays.analytics import aggregates as agg

from .factories import ME, make_event, make_match, make_round, make_round_player

MATES = [f"mate{i}" for i in range(4)]
RIVALES = [f"rival{i}" for i in range(5)]


class MuertesHeadshotTests(TestCase):
    def setUp(self):
        self.match = make_match()
        self.numero = 0

    def _ronda(self, eventos, *, side="Attack"):
        """Ronda 5v5 con tu fila; `eventos` es (actor, target, headshot), todos `Kill`."""
        rnd = make_round(self.match, self.numero, side=side)
        self.numero += 1
        rival_side = "Defense" if side == "Attack" else "Attack"
        make_round_player(rnd, kills=0)
        for nick in MATES:
            make_round_player(rnd, username=nick, is_me=False)
        for nick in RIVALES:
            make_round_player(rnd, username=nick, is_me=False, team_index=1, side=rival_side)
        for orden, (actor, target, headshot) in enumerate(eventos):
            make_event(rnd, orden, actor, target, headshot=headshot)
        return rnd

    def _celda(self, data, quien="me", lado="total"):
        celda = data[quien][lado]
        return (celda["deaths"], celda["with_data"], celda["headshots"], celda["pct"])

    def test_cuenta_tus_muertes_headshot_sobre_las_que_tienen_dato(self):
        self._ronda([("rival0", ME, True)])
        self._ronda([("rival1", ME, False)])
        self._ronda([("rival2", ME, True)])
        self.assertEqual(self._celda(agg.headshot_deaths()), (3, 3, 2, 66.7))

    def test_headshot_nulo_cuenta_en_muertes_y_no_en_el_porcentaje(self):
        self._ronda([("rival0", ME, True)])
        self._ronda([("rival1", ME, None)])
        self.assertEqual(self._celda(agg.headshot_deaths()), (2, 1, 1, 100.0))

    def test_un_teamkill_no_cuenta_ni_para_ti_ni_para_tus_companeros(self):
        self._ronda([("mate0", ME, True), ("mate1", "mate2", True)])
        data = agg.headshot_deaths()
        self.assertEqual(self._celda(data), (0, 0, 0, None))
        self.assertEqual(self._celda(data, "teammates"), (0, 0, 0, None))

    def test_muerte_sin_autor_no_cuenta(self):
        self._ronda([("", ME, True), ("", "mate0", True)])
        data = agg.headshot_deaths()
        self.assertEqual(self._celda(data), (0, 0, 0, None))
        self.assertEqual(self._celda(data, "teammates"), (0, 0, 0, None))

    def test_las_muertes_de_tus_companeros_van_aparte(self):
        self._ronda([("rival0", "mate0", True), ("rival1", "mate1", False), ("rival2", ME, True)])
        self._ronda([("rival0", "mate2", None)])
        data = agg.headshot_deaths()
        self.assertEqual(self._celda(data), (1, 1, 1, 100.0))
        self.assertEqual(self._celda(data, "teammates"), (3, 2, 1, 50.0))

    def test_un_rival_no_cuenta_como_companero(self):
        # tus bajas y las bajas entre rivales no son muertes de tu equipo
        self._ronda([(ME, "rival0", True), ("rival1", "rival2", True), ("mate0", "rival3", True)])
        data = agg.headshot_deaths()
        self.assertEqual(self._celda(data), (0, 0, 0, None))
        self.assertEqual(self._celda(data, "teammates"), (0, 0, 0, None))

    def test_una_victima_sin_fila_en_la_ronda_no_cuenta(self):
        self._ronda([("rival0", "espectador", True)])
        self.assertEqual(self._celda(agg.headshot_deaths(), "teammates"), (0, 0, 0, None))

    def test_parte_por_tu_lado_y_suma_el_total(self):
        self._ronda([("rival0", ME, True), ("rival1", "mate0", True)], side="Attack")
        self._ronda([("rival0", ME, False), ("rival1", "mate0", None)], side="Defense")
        self._ronda([("rival2", ME, False)], side="Defense")
        data = agg.headshot_deaths()
        self.assertEqual(self._celda(data, "me", "Attack"), (1, 1, 1, 100.0))
        self.assertEqual(self._celda(data, "me", "Defense"), (2, 2, 0, 0.0))
        self.assertEqual(self._celda(data, "me", "total"), (3, 3, 1, 33.3))
        self.assertEqual(self._celda(data, "teammates", "Attack"), (1, 1, 1, 100.0))
        self.assertEqual(self._celda(data, "teammates", "Defense"), (1, 0, 0, None))
        self.assertEqual(self._celda(data, "teammates", "total"), (2, 1, 1, 100.0))

    def test_un_lado_desconocido_solo_suma_al_total(self):
        self._ronda([("rival0", ME, True)], side="Unknown")
        data = agg.headshot_deaths()
        self.assertEqual(self._celda(data, "me", "total"), (1, 1, 1, 100.0))
        self.assertEqual(self._celda(data, "me", "Attack"), (0, 0, 0, None))
        self.assertEqual(self._celda(data, "me", "Defense"), (0, 0, 0, None))
        self.assertNotIn("Unknown", data["me"])

    def test_filtro_de_lado_deja_solo_ese_lado(self):
        self._ronda([("rival0", ME, True)], side="Attack")
        self._ronda([("rival0", ME, False)], side="Defense")
        data = agg.headshot_deaths(side="Attack")
        self.assertEqual(self._celda(data, "me", "Attack"), (1, 1, 1, 100.0))
        self.assertEqual(self._celda(data, "me", "Defense"), (0, 0, 0, None))
        self.assertEqual(self._celda(data, "me", "total"), (1, 1, 1, 100.0))

    def test_el_filtro_de_mapa_aplica_sobre_tus_rondas(self):
        self._ronda([("rival0", ME, True)])
        otra = make_match(map_name="Border", index=1)
        rnd = make_round(otra, 0)
        make_round_player(rnd, kills=0)
        make_round_player(rnd, username="rival0", is_me=False, team_index=1, side="Defense")
        make_event(rnd, 0, "rival0", ME, headshot=False)
        self.assertEqual(self._celda(agg.headshot_deaths(map="border")), (1, 1, 0, 0.0))

    def test_sin_dato_el_porcentaje_es_nulo(self):
        data = agg.headshot_deaths()
        for quien in ("me", "teammates"):
            for lado in ("Attack", "Defense", "total"):
                self.assertEqual(self._celda(data, quien, lado), (0, 0, 0, None))

    def test_consultas_constantes(self):
        self._ronda([("rival0", ME, True)])
        with self.assertNumQueries(2):
            agg.headshot_deaths()
        for _ in range(4):
            self._ronda([("rival0", ME, True), ("rival1", "mate0", False)])
        with self.assertNumQueries(2):
            agg.headshot_deaths()

    def test_api_duels_trae_headshot_deaths(self):
        self._ronda([("rival0", ME, True)], side="Attack")
        self._ronda([("rival0", ME, False)], side="Defense")
        data = self.client.get("/api/duels/", {"side": "Defense"}).json()["headshot_deaths"]
        self.assertEqual(self._celda(data), (1, 1, 0, 0.0))
        self.assertEqual(set(data), {"me", "teammates"})
        self.assertEqual(set(data["me"]), {"Attack", "Defense", "total"})
