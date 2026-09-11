"""Tests de la ventana de trade configurable y del recalculo."""

from __future__ import annotations

from io import StringIO

from django.core.management import call_command
from django.test import TestCase

from replays.analytics.metrics import analyse_round, trade_window
from replays.models import Event, RoundPlayer
from replays.recompute import recompute

from .factories import ME, make_event, make_match, make_round, make_round_player


def round_data(gap: float) -> dict:
    """Una ronda donde el trade llega `gap` segundos despues de la muerte."""
    return {
        "clockStart": 180.0,
        "players": [
            {"username": "yo", "teamIndex": 0},
            {"username": "amigo", "teamIndex": 0},
            {"username": "rival", "teamIndex": 1},
        ],
        "teams": [{"role": "Attack"}, {"role": "Defense"}],
        "stats": [
            {"username": "yo", "kills": 0, "died": True},
            {"username": "amigo", "kills": 1, "died": False},
            {"username": "rival", "kills": 1, "died": True},
        ],
        "matchFeedback": [
            {"type": {"name": "Kill"}, "username": "rival", "target": "yo", "timeInSeconds": 100.0},
            {
                "type": {"name": "Kill"},
                "username": "amigo",
                "target": "rival",
                "timeInSeconds": 100.0 - gap,
            },
        ],
    }


class VentanaTests(TestCase):
    def test_la_ventana_sale_de_settings(self):
        self.assertEqual(trade_window(), 3.0)
        with self.settings(TRADE_WINDOW_SECONDS=10):
            self.assertEqual(trade_window(), 10.0)

    def test_con_ventana_corta_la_venganza_tardia_no_cuenta(self):
        analisis = analyse_round(round_data(gap=6.0), window=3.0)
        self.assertFalse(analisis["players"]["yo"]["was_traded"])
        self.assertTrue(analisis["players"]["yo"]["untraded_death"])
        self.assertEqual(analisis["players"]["amigo"]["trade_kills"], 0)

    def test_con_ventana_larga_la_misma_venganza_si_cuenta(self):
        analisis = analyse_round(round_data(gap=6.0), window=10.0)
        self.assertTrue(analisis["players"]["yo"]["was_traded"])
        self.assertFalse(analisis["players"]["yo"]["untraded_death"])
        self.assertEqual(analisis["players"]["amigo"]["trade_kills"], 1)

    def test_sin_argumento_usa_la_de_settings(self):
        with self.settings(TRADE_WINDOW_SECONDS=10):
            analisis = analyse_round(round_data(gap=6.0))
        self.assertTrue(analisis["players"]["yo"]["was_traded"])

    def test_el_kst_sigue_a_la_ventana(self):
        """Morir sin aportar deja de contar si la muerte se vengo."""
        self.assertFalse(analyse_round(round_data(gap=6.0), window=3.0)["players"]["yo"]["kst"])
        self.assertTrue(analyse_round(round_data(gap=6.0), window=10.0)["players"]["yo"]["kst"])


class RecomputeTests(TestCase):
    def setUp(self):
        match = make_match(index=0)
        self.rnd = make_round(match, 0)
        make_round_player(self.rnd, username=ME, kills=0, died=True, was_traded=False)
        make_round_player(self.rnd, username="amigo", is_me=False, team_index=0, kills=1, died=False)
        make_round_player(self.rnd, username="rival", is_me=False, team_index=1, kills=1, died=True)
        # el rival me mata y mi amigo lo venga 6 segundos despues
        make_event(self.rnd, 0, "rival", ME, clock=100.0)
        make_event(self.rnd, 1, "amigo", "rival", clock=94.0)

    def _yo(self) -> RoundPlayer:
        return RoundPlayer.objects.get(username=ME)

    def test_con_ventana_larga_aparece_el_trade(self):
        result = recompute(window=10.0)
        self.assertEqual(result.rounds, 1)
        self.assertTrue(result.changed)

        yo = self._yo()
        self.assertTrue(yo.was_traded)
        self.assertFalse(yo.untraded_death)
        self.assertTrue(yo.kst)
        self.assertEqual(RoundPlayer.objects.get(username="amigo").trade_kills, 1)
        self.assertTrue(Event.objects.get(order=0).traded)

    def test_volver_atras_saca_el_trade(self):
        """Achicar la ventana tiene que poder **quitar** trades, no solo sumar."""
        recompute(window=10.0)
        recompute(window=3.0)

        yo = self._yo()
        self.assertFalse(yo.was_traded)
        self.assertTrue(yo.untraded_death)
        self.assertEqual(RoundPlayer.objects.get(username="amigo").trade_kills, 0)
        self.assertFalse(Event.objects.get(order=0).traded)

    def test_es_idempotente(self):
        self.assertTrue(recompute(window=10.0).changed)
        self.assertFalse(recompute(window=10.0).changed)

    def test_dry_run_no_escribe(self):
        result = recompute(window=10.0, dry_run=True)
        self.assertTrue(result.changed)
        self.assertFalse(self._yo().was_traded)

    def test_no_toca_lo_que_no_depende_de_la_ventana(self):
        antes = self._yo()
        kills, died, operator = antes.kills, antes.died, antes.operator
        recompute(window=10.0)
        despues = self._yo()
        self.assertEqual((despues.kills, despues.died, despues.operator), (kills, died, operator))

    def test_una_ronda_sin_jugadores_no_revienta(self):
        make_round(make_match(index=1), 0)
        self.assertEqual(recompute(window=3.0).rounds, 2)


class ComandoTests(TestCase):
    def setUp(self):
        match = make_match(index=0)
        rnd = make_round(match, 0)
        make_round_player(rnd, username=ME, kills=0, died=True)
        make_round_player(rnd, username="amigo", is_me=False, team_index=0, kills=1, died=False)
        make_round_player(rnd, username="rival", is_me=False, team_index=1, kills=1, died=True)
        make_event(rnd, 0, "rival", ME, clock=100.0)
        make_event(rnd, 1, "amigo", "rival", clock=94.0)

    def _correr(self, *args) -> str:
        out = StringIO()
        call_command("recompute", *args, stdout=out)
        return out.getvalue()

    def test_sin_cambios_lo_dice(self):
        self.assertIn("Nada que recalcular", self._correr())

    def test_reporta_el_cambio(self):
        salida = self._correr("--window", "10")
        self.assertIn("ventana de 10s", salida)
        self.assertIn("filas de jugador", salida)

    def test_dry_run_avisa_y_no_toca(self):
        self.assertIn("[dry-run]", self._correr("--dry-run", "--window", "10"))
        self.assertFalse(RoundPlayer.objects.get(username=ME).was_traded)

    def test_ventana_invalida(self):
        err = StringIO()
        call_command("recompute", "--window", "0", stderr=err)
        self.assertIn("mayor que cero", err.getvalue())


class ApiTests(TestCase):
    def test_la_ventana_se_ve_en_la_api(self):
        self.assertEqual(self.client.get("/api/health/").json()["trade_window"], 3.0)
        self.assertEqual(
            self.client.get("/api/overview/").json()["data_health"]["trade_window"], 3.0
        )
