"""Tests de los duelos: quien te mata, a quien matas y contra que operadores."""

from __future__ import annotations

from django.test import TestCase

from replays.analytics import aggregates as agg
from replays.analytics.coach import build_insights

from .factories import ME, make_event, make_match, make_round, make_round_player


def find(payload, key):
    return next((i for i in payload["insights"] if i["key"] == key), None)


class DuelosTests(TestCase):
    def setUp(self):
        self.match = make_match(index=0)

    def _ronda(self, numero, *, operador_rival="Thorn", rival="rival"):
        rnd = make_round(self.match, numero)
        make_round_player(rnd, operator="Zofia")
        make_round_player(
            rnd,
            username=rival,
            is_me=False,
            team_index=1,
            side="Defense",
            operator=operador_rival,
        )
        return rnd

    def test_cuenta_las_dos_direcciones(self):
        rnd = self._ronda(0)
        make_event(rnd, 0, "rival", ME)  # me mata
        make_event(rnd, 1, ME, "rival")  # lo mato

        fila = agg.nemesis(min_duels=1)[0]
        self.assertEqual(fila["username"], "rival")
        self.assertEqual(fila["deaths"], 1)
        self.assertEqual(fila["kills"], 1)
        self.assertEqual(fila["duels"], 2)
        self.assertEqual(fila["balance"], 0)
        self.assertEqual(fila["winrate"], 50.0)

    def test_el_primer_evento_es_el_duelo_de_apertura(self):
        rnd = self._ronda(0)
        make_event(rnd, 0, "rival", ME, clock=150.0)
        make_event(rnd, 1, ME, "rival", clock=100.0)

        fila = agg.nemesis(min_duels=1)[0]
        self.assertEqual(fila["opening_deaths"], 1)
        self.assertEqual(fila["opening_kills"], 0)
        self.assertEqual(fila["opening_duels"], 1)

    def test_teamkill_no_es_duelo(self):
        """Un companero que te mata por error no te gano nada."""
        rnd = make_round(self.match, 0)
        make_round_player(rnd)
        make_round_player(rnd, username="amigo", is_me=False, team_index=0)
        make_event(rnd, 0, "amigo", ME)

        self.assertEqual(agg.nemesis(min_duels=1), [])
        self.assertEqual(agg.duel_totals()["duels"], 0)

    def test_muestra_minima(self):
        rnd = self._ronda(0)
        make_event(rnd, 0, "rival", ME)
        self.assertEqual(agg.nemesis(min_duels=1)[0]["duels"], 1)
        self.assertEqual(agg.nemesis(min_duels=2), [])

    def test_trae_los_mapas_del_cruce(self):
        rnd = self._ronda(0)
        make_event(rnd, 0, "rival", ME)
        self.assertEqual(agg.nemesis(min_duels=1)[0]["maps"], ["Club House"])

    def test_agrupa_por_operador_rival(self):
        for n in range(3):
            rnd = self._ronda(n, operador_rival="Thorn")
            make_event(rnd, 0, "rival", ME)
        rnd = self._ronda(3, operador_rival="Ash", rival="otro")
        make_event(rnd, 0, ME, "otro")

        filas = {r["operator"]: r for r in agg.duels_by_operator(min_duels=1)}
        self.assertEqual(filas["Thorn"]["deaths"], 3)
        self.assertEqual(filas["Thorn"]["kills"], 0)
        self.assertEqual(filas["Thorn"]["winrate"], 0.0)
        self.assertEqual(filas["Ash"]["kills"], 1)

    def test_totales(self):
        rnd = self._ronda(0)
        make_event(rnd, 0, "rival", ME)
        make_event(rnd, 1, ME, "rival")
        self.assertEqual(agg.duel_totals(), {"kills": 1, "deaths": 1, "duels": 2, "winrate": 50.0})

    def test_respeta_los_filtros(self):
        rnd = self._ronda(0)
        make_event(rnd, 0, "rival", ME)
        self.assertEqual(agg.duel_totals(side="Attack")["duels"], 1)
        self.assertEqual(agg.duel_totals(side="Defense")["duels"], 0)
        self.assertEqual(agg.duel_totals(map="villa")["duels"], 0)

    def test_sin_datos_no_revienta(self):
        self.assertEqual(agg.nemesis(), [])
        self.assertEqual(agg.duels_by_operator(), [])
        self.assertIsNone(agg.duel_totals()["winrate"])


class DuelosApiTests(TestCase):
    def setUp(self):
        match = make_match(index=0)
        rnd = make_round(match, 0)
        make_round_player(rnd)
        make_round_player(rnd, username="rival", is_me=False, team_index=1, operator="Thorn")
        make_event(rnd, 0, "rival", ME)

    def test_endpoint(self):
        data = self.client.get("/api/duels/?min_duels=1").json()
        self.assertEqual(data["totals"]["deaths"], 1)
        self.assertEqual(data["nemesis"][0]["username"], "rival")
        self.assertEqual(data["operators"][0]["operator"], "Thorn")

    def test_min_duels_invalido_no_revienta(self):
        self.assertEqual(self.client.get("/api/duels/?min_duels=-3").status_code, 200)


class CoachDuelosTests(TestCase):
    """Las dos reglas nuevas, con la muestra justa para que disparen."""

    def _historial(self, *, rival="rival", operador="Thorn", pierdo=10, gano=1):
        match = make_match(index=0, my_score=4, opponent_score=4)
        n = 0
        for _ in range(pierdo + gano):
            rnd = make_round(match, n)
            make_round_player(rnd)
            make_round_player(
                rnd, username=rival, is_me=False, team_index=1, operator=operador
            )
            n += 1
        rondas = list(match.rounds.order_by("number"))
        for rnd in rondas[:pierdo]:
            make_event(rnd, 0, rival, ME)
        for rnd in rondas[pierdo:]:
            make_event(rnd, 0, ME, rival)
        # relleno de duelos parejos contra otra gente, para que el promedio
        # general no sea el mismo numero que el del operador senalado
        otro = make_match(index=1)
        for i in range(60):
            rnd = make_round(otro, i)
            make_round_player(rnd)
            make_round_player(
                rnd, username=f"r{i}", is_me=False, team_index=1, operator="Ash"
            )
            if i % 2:
                make_event(rnd, 0, f"r{i}", ME)
            else:
                make_event(rnd, 0, ME, f"r{i}")

    def test_avisa_del_operador_que_te_gana(self):
        self._historial()
        insight = find(build_insights(), "operador-rival")
        self.assertIsNotNone(insight)
        self.assertIn("Thorn", insight["title"])
        self.assertEqual(insight["sample"], 11)

    def test_avisa_del_rival_que_te_gana(self):
        self._historial()
        insight = find(build_insights(), "nemesis")
        self.assertIsNotNone(insight)
        self.assertIn("rival", insight["title"])
        self.assertIn("primer duelo de la ronda", insight["detail"])

    def test_no_opina_con_pocos_duelos(self):
        self._historial(pierdo=3, gano=0)
        payload = build_insights()
        self.assertIsNone(find(payload, "nemesis"))
        self.assertIsNone(find(payload, "operador-rival"))
