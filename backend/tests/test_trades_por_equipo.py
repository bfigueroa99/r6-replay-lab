"""Trades por equipo en el detalle de partida: suma de las columnas que deja el import."""

from __future__ import annotations

from django.test import TestCase

from .factories import ME, make_event, make_match, make_round, make_round_player


class TradesPorEquipoTests(TestCase):
    def setUp(self):
        self.match = make_match()

    def _detalle(self) -> dict:
        resp = self.client.get(f"/api/matches/{self.match.pk}/")
        self.assertEqual(resp.status_code, 200)
        return resp.json()

    def _partida_de_dos_rondas(self):
        # Ronda 0: muero tradeado, mi companero hace el trade; un rival muere sin trade.
        r0 = make_round(self.match, 0)
        make_round_player(r0, kills=0, died=True, was_traded=True)
        make_round_player(r0, username="mate", is_me=False, kills=1, died=False, trade_kills=1)
        make_round_player(r0, username="rival1", is_me=False, team_index=1, kills=1,
                          died=True, won=False)
        make_round_player(r0, username="rival2", is_me=False, team_index=1, kills=0,
                          died=False, won=False)
        # Ronda 1: mi companero muere sin trade; los dos rivales mueren, uno tradeado.
        r1 = make_round(self.match, 1, side="Defense")
        make_round_player(r1, kills=2, died=False)
        make_round_player(r1, username="mate", is_me=False, kills=0, died=True)
        make_round_player(r1, username="rival1", is_me=False, team_index=1, kills=1,
                          died=True, was_traded=True, won=False)
        make_round_player(r1, username="rival2", is_me=False, team_index=1, kills=0,
                          died=True, trade_kills=1, won=False)

    def test_trades_por_equipo_suma_cada_equipo(self):
        self._partida_de_dos_rondas()
        trades = self._detalle()["team_trades"]
        self.assertEqual(
            trades["mine"],
            {"deaths": 2, "traded_deaths": 1, "untraded_deaths": 1, "trade_kills": 1,
             "untraded_pct": 50.0},
        )
        self.assertEqual(
            trades["rival"],
            {"deaths": 3, "traded_deaths": 1, "untraded_deaths": 2, "trade_kills": 1,
             "untraded_pct": 66.7},
        )

    def test_trades_por_equipo_cuadra_con_el_scoreboard(self):
        self._partida_de_dos_rondas()
        datos = self._detalle()
        mi_equipo = datos["match"]["my_team_index"]
        for lado, es_mio in (("mine", True), ("rival", False)):
            filas = [f for f in datos["scoreboard"] if (f["team_index"] == mi_equipo) == es_mio]
            equipo = datos["team_trades"][lado]
            self.assertEqual(equipo["deaths"], sum(f["deaths"] for f in filas))
            self.assertEqual(equipo["untraded_deaths"], sum(f["untraded_deaths"] for f in filas))
            self.assertEqual(equipo["trade_kills"], sum(f["trade_kills"] or 0 for f in filas))
            self.assertEqual(equipo["traded_deaths"] + equipo["untraded_deaths"], equipo["deaths"])

    def test_trades_por_equipo_usa_el_equipo_de_cada_ronda(self):
        # En esta ronda tu fila quedo con team_index 1 (no el de la partida):
        # tu companero de esa ronda cuenta como tuyo y el del indice 0 como rival.
        rnd = make_round(self.match, 0)
        make_round_player(rnd, team_index=1, kills=0, died=True)
        make_round_player(rnd, username="mate", is_me=False, team_index=1, kills=0, died=True,
                          was_traded=True)
        make_round_player(rnd, username="rival", is_me=False, team_index=0, kills=2,
                          died=False, trade_kills=1, won=False)
        trades = self._detalle()["team_trades"]
        self.assertEqual((trades["mine"]["deaths"], trades["mine"]["traded_deaths"]), (2, 1))
        self.assertEqual((trades["rival"]["deaths"], trades["rival"]["trade_kills"]), (0, 1))

    def test_sin_tu_fila_vale_el_equipo_de_la_partida(self):
        rnd = make_round(self.match, 0)
        make_round_player(rnd, username="mate", is_me=False, team_index=0, kills=0, died=True)
        make_round_player(rnd, username="rival", is_me=False, team_index=1, kills=1,
                          died=False, won=False)
        trades = self._detalle()["team_trades"]
        self.assertEqual(trades["mine"]["deaths"], 1)
        self.assertEqual(trades["rival"]["deaths"], 0)

    def test_sin_muertes_el_porcentaje_es_null(self):
        rnd = make_round(self.match, 0)
        make_round_player(rnd, kills=1, died=False)
        make_round_player(rnd, username="rival", is_me=False, team_index=1, kills=0,
                          died=False, won=False)
        trades = self._detalle()["team_trades"]
        self.assertIsNone(trades["mine"]["untraded_pct"])
        self.assertIsNone(trades["rival"]["untraded_pct"])
        self.assertEqual(trades["mine"]["deaths"], 0)

    def test_un_teamkill_cuenta_como_ya_lo_guarda_el_import(self):
        # El import deja una muerte por teamkill como untraded_death=True; aca
        # solo se suma, no se recalcula nada mirando los eventos.
        rnd = make_round(self.match, 0)
        make_round_player(rnd, kills=0, died=True)  # was_traded=False -> untraded_death=True
        make_round_player(rnd, username="mate", is_me=False, kills=1, died=False)
        make_event(rnd, 0, "mate", ME)  # el companero te mata: teamkill
        trades = self._detalle()["team_trades"]
        self.assertEqual(trades["mine"]["untraded_deaths"], 1)
        self.assertEqual(trades["mine"]["untraded_pct"], 100.0)

    def test_traded_sin_muerte_no_descuadra(self):
        rnd = make_round(self.match, 0)
        fila = make_round_player(rnd, kills=1, died=False)
        fila.was_traded = True
        fila.save()
        trades = self._detalle()["team_trades"]
        self.assertEqual(trades["mine"]["traded_deaths"], 0)
        self.assertEqual(trades["mine"]["deaths"], 0)
