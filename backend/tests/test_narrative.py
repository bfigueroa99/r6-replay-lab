"""Tests del resumen narrativo por ronda.

El resumen es texto derivado: lo que importa es que no afirme nada que los
eventos no digan, y que se calle cuando no hay dato.
"""

from __future__ import annotations

from django.test import TestCase

from replays.analytics.narrative import describe_round


def jugador(username, *, equipo=0, yo=False, **extra):
    base = {
        "username": username,
        "team_index": equipo,
        "is_me": yo,
        "kills": 0,
        "died": False,
        "survived": True,
        "trade_kills": 0,
        "one_vx": 0,
        "untraded_death": False,
        "death_elapsed": None,
    }
    base.update(extra)
    return base


def baja(actor, target, *, clock, elapsed, traded=False, kind="Kill"):
    return {
        "kind": kind,
        "actor": actor,
        "target": target,
        "clock": clock,
        "elapsed": elapsed,
        "traded": traded,
    }


def ronda(players, events, **extra):
    base = {
        "clock_start": 180.0,
        "clock_end": 20.0,
        "duration": 160.0,
        "win_condition": "KilledOpponents",
        "win_condition_certain": True,
        "possible_plant": False,
        "players": players,
        "events": events,
    }
    base.update(extra)
    return base


YO = "BearF99"


class AperturaTests(TestCase):
    def test_perder_el_primer_duelo_propio(self):
        r = ronda(
            [jugador(YO, yo=True, died=True, survived=False, untraded_death=True, death_elapsed=20.0),
             jugador("rival", equipo=1)],
            [baja("rival", YO, clock=160.0, elapsed=20.0)],
        )
        frases = describe_round(r)
        self.assertIn("perdiste el primer duelo: te mato rival", frases[0])
        self.assertIn("Nadie la vengo", frases[0])

    def test_ganar_el_primer_duelo_lo_dice_del_otro_lado(self):
        """Que el rival no vengue su muerte es una ventaja, no un reproche."""
        r = ronda(
            [jugador(YO, yo=True, kills=1), jugador("rival", equipo=1, died=True, survived=False)],
            [baja(YO, "rival", clock=160.0, elapsed=20.0)],
        )
        self.assertIn("El rival no la vengo", describe_round(r)[0])

    def test_el_trade_trae_el_margen(self):
        r = ronda(
            [jugador(YO, yo=True, died=True, survived=False, death_elapsed=20.0),
             jugador("amigo"), jugador("rival", equipo=1)],
            [
                baja("rival", YO, clock=160.0, elapsed=20.0, traded=True),
                baja("amigo", "rival", clock=158.0, elapsed=22.0),
            ],
        )
        self.assertIn("amigo la vengo 2s despues", describe_round(r)[0])

    def test_muerte_sin_asesino_no_inventa_uno(self):
        r = ronda(
            [jugador(YO, yo=True, died=True, survived=False, death_elapsed=15.0),
             jugador("rival", equipo=1)],
            [baja(YO, "", clock=165.0, elapsed=15.0, kind="Death")],
        )
        self.assertIn("sin asesino registrado", describe_round(r)[0])

    def test_sin_eventos_no_hay_frase_de_apertura(self):
        r = ronda([jugador(YO, yo=True)], [])
        self.assertFalse(any("primer duelo" in f for f in describe_round(r)))


class DesventajaTests(TestCase):
    def test_suma_los_segundos_en_inferioridad(self):
        """Dos bajas propias seguidas: 4v5 desde los 160 hasta el final."""
        r = ronda(
            [jugador(YO, yo=True, died=True, survived=False, death_elapsed=20.0),
             jugador("amigo"), jugador("rival", equipo=1), jugador("rival2", equipo=1)],
            [baja("rival", YO, clock=160.0, elapsed=20.0)],
        )
        frase = next(f for f in describe_round(r) if "inferioridad" in f)
        self.assertIn("140s se jugaron", frase)  # de 160 a clock_end 20

    def test_no_menciona_desventajas_irrelevantes(self):
        """Menos de 5 segundos abajo no es una frase que valga la pena."""
        r = ronda(
            [jugador(YO, yo=True), jugador("amigo", died=True, survived=False),
             jugador("rival", equipo=1)],
            [
                baja("rival", "amigo", clock=25.0, elapsed=155.0),
                baja(YO, "rival", clock=22.0, elapsed=158.0),
            ],
        )
        self.assertFalse(any("inferioridad" in f for f in describe_round(r)))

    def test_estar_arriba_no_se_menciona(self):
        r = ronda(
            [jugador(YO, yo=True, kills=1), jugador("rival", equipo=1, died=True, survived=False)],
            [baja(YO, "rival", clock=160.0, elapsed=20.0)],
        )
        self.assertFalse(any("inferioridad" in f for f in describe_round(r)))


class MiRondaTests(TestCase):
    def test_bajas_y_supervivencia(self):
        r = ronda([jugador(YO, yo=True, kills=2, one_vx=2)], [])
        self.assertIn("Hiciste 2 bajas, cerraste un 1v2 y sobreviviste.", describe_round(r))

    def test_una_baja_va_en_singular(self):
        r = ronda([jugador(YO, yo=True, kills=1)], [])
        self.assertIn("Hiciste 1 baja y sobreviviste.", describe_round(r))

    def test_muerte_sin_trade(self):
        r = ronda(
            [jugador(YO, yo=True, died=True, survived=False, untraded_death=True, death_elapsed=45.0)],
            [],
        )
        self.assertIn("Moriste a los 45s sin que nadie te tradeara.", describe_round(r))

    def test_muerte_tradeada(self):
        r = ronda(
            [jugador(YO, yo=True, died=True, survived=False, death_elapsed=45.0)],
            [],
        )
        self.assertIn("Moriste a los 45s y te tradearon.", describe_round(r))


class CierreTests(TestCase):
    def test_eliminacion(self):
        r = ronda([jugador(YO, yo=True)], [])
        self.assertIn("La ronda se cerro por eliminacion.", describe_round(r))

    def test_condicion_incierta_lo_dice(self):
        r = ronda([jugador(YO, yo=True)], [], win_condition="", win_condition_certain=False)
        self.assertIn("no expone como se cerro", describe_round(r)[-1])

    def test_plant_probable_se_marca_como_probable(self):
        r = ronda(
            [jugador(YO, yo=True)],
            [],
            win_condition="",
            win_condition_certain=False,
            possible_plant=True,
            clock_end=45.0,
        )
        self.assertIn("plant probable", describe_round(r)[-1])


class RondaVaciaTests(TestCase):
    def test_una_ronda_sin_nada_no_revienta(self):
        self.assertIsInstance(describe_round({}), list)

    def test_sin_jugador_propio_no_habla_en_primera_persona(self):
        r = ronda([jugador("otro")], [])
        self.assertFalse(any("Moriste" in f or "Hiciste" in f for f in describe_round(r)))


class ApiTests(TestCase):
    def test_el_detalle_de_partida_trae_el_resumen(self):
        from .factories import make_event, make_match, make_round, make_round_player

        match = make_match(index=0)
        rnd = make_round(match, 0)
        make_round_player(rnd, kills=1)
        make_round_player(rnd, username="rival", is_me=False, team_index=1)
        make_event(rnd, 0, "rival", YO, clock=150.0)

        data = self.client.get(f"/api/matches/{match.id}/").json()
        resumen = data["rounds"][0]["summary"]
        self.assertTrue(resumen)
        self.assertIn("primer duelo", " ".join(resumen))
