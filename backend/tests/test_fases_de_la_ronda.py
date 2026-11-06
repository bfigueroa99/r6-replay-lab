"""Fases de la ronda en el detalle de partida: bajas de cada equipo por tramo de la ronda."""

from __future__ import annotations

from django.test import TestCase

from replays.analytics.aggregates import fases_de_partida

from .factories import ME, make_event, make_match, make_round, make_round_player


def _baja(rnd, order, actor, target, segundos):
    # make_event toma el reloj, no los segundos jugados.
    return make_event(rnd, order, actor, target, clock=rnd.clock_start - segundos)


class FasesDeLaRondaTests(TestCase):
    def setUp(self):
        self.match = make_match()

    def _fases(self) -> dict:
        resp = self.client.get(f"/api/matches/{self.match.pk}/")
        self.assertEqual(resp.status_code, 200)
        return resp.json()["phases"]

    def _ronda(self, number, *, won=True, mi_equipo=0):
        rnd = make_round(self.match, number, won=won)
        make_round_player(rnd, team_index=mi_equipo)
        make_round_player(rnd, username="mate", is_me=False, team_index=mi_equipo)
        make_round_player(rnd, username="rival1", is_me=False, team_index=1 - mi_equipo,
                          won=not won)
        make_round_player(rnd, username="rival2", is_me=False, team_index=1 - mi_equipo,
                          won=not won)
        return rnd

    def _fila(self, fases, clave):
        return next(f for f in fases["rows"] if f["key"] == clave)

    def test_los_cortes_de_las_fases_caen_donde_dicen(self):
        rnd = self._ronda(0)
        _baja(rnd, 0, ME, "rival1", 29.9)
        _baja(rnd, 1, ME, "rival2", 30.0)
        _baja(rnd, 2, "mate", "rival1", 119.9)
        _baja(rnd, 3, "mate", "rival2", 120.0)
        fases = self._fases()
        self.assertEqual([f["key"] for f in fases["rows"]], ["temprano", "medio", "tarde"])
        self.assertEqual([f["mine"] for f in fases["rows"]], [1, 2, 1])
        self.assertEqual([f["rival"] for f in fases["rows"]], [0, 0, 0])

    def test_las_bajas_se_reparten_entre_tu_equipo_y_el_rival(self):
        rnd = self._ronda(0)
        _baja(rnd, 0, "rival1", "mate", 10)
        _baja(rnd, 1, ME, "rival1", 45)
        _baja(rnd, 2, "rival2", ME, 50)
        _baja(rnd, 3, "rival2", "mate", 150)
        fases = self._fases()
        self.assertEqual(
            [(f["mine"], f["rival"]) for f in fases["rows"]], [(0, 1), (1, 1), (0, 1)]
        )

    def test_un_teamkill_no_suma_a_ningun_equipo(self):
        rnd = self._ronda(0)
        _baja(rnd, 0, ME, "mate", 40)
        _baja(rnd, 1, "rival1", "rival1", 50)  # suicidio
        fases = self._fases()
        self.assertEqual(sum(f["mine"] + f["rival"] for f in fases["rows"]), 0)
        self.assertEqual(fases["teamkills"], 2)

    def test_una_baja_de_un_jugador_sin_fila_no_suma_ni_rompe(self):
        rnd = self._ronda(0)
        _baja(rnd, 0, "fantasma", "rival1", 40)
        _baja(rnd, 1, ME, "rival2", 40)
        fases = self._fases()
        self.assertEqual(self._fila(fases, "medio")["mine"], 1)
        self.assertEqual(self._fila(fases, "medio")["rival"], 0)
        self.assertEqual(fases["unknown_team_kills"], 1)

    def test_una_baja_sin_reloj_queda_fuera_de_las_fases(self):
        rnd = self._ronda(0)
        _baja(rnd, 0, ME, "rival1", 0)
        _baja(rnd, 1, ME, "rival2", 70)
        fases = self._fases()
        self.assertEqual(sum(f["mine"] for f in fases["rows"]), 1)
        self.assertEqual(fases["untimed_kills"], 1)

    def test_las_muertes_sin_autor_no_son_bajas_de_nadie(self):
        rnd = self._ronda(0)
        make_event(rnd, 0, "", "rival1", kind="Death", clock=rnd.clock_start - 40)
        fases = self._fases()
        self.assertEqual(sum(f["mine"] + f["rival"] for f in fases["rows"]), 0)
        self.assertEqual(
            (fases["untimed_kills"], fases["unknown_team_kills"], fases["teamkills"]), (0, 0, 0)
        )

    def test_rondas_dominadas_y_ganadas_por_fase(self):
        ganada = self._ronda(0, won=True)
        _baja(ganada, 0, ME, "rival1", 10)
        _baja(ganada, 1, "mate", "rival2", 20)
        perdida = self._ronda(1, won=False)
        _baja(perdida, 0, ME, "rival1", 15)
        _baja(perdida, 1, "rival2", ME, 60)
        _baja(perdida, 2, "rival2", "mate", 70)
        fases = self._fases()
        temprano = self._fila(fases, "temprano")
        self.assertEqual(
            (temprano["rounds_ahead"], temprano["rounds_ahead_won"],
             temprano["rounds_ahead_winrate"]),
            (2, 1, 50.0),
        )
        self.assertEqual((temprano["rounds_behind"], temprano["rounds_behind_winrate"]),
                         (0, None))
        medio = self._fila(fases, "medio")
        self.assertEqual(
            (medio["rounds_ahead"], medio["rounds_behind"], medio["rounds_behind_won"],
             medio["rounds_behind_winrate"]),
            (0, 1, 0, 0.0),
        )

    def test_un_empate_en_la_fase_no_cuenta_para_ningun_lado(self):
        rnd = self._ronda(0)
        _baja(rnd, 0, ME, "rival1", 40)
        _baja(rnd, 1, "rival2", "mate", 50)
        medio = self._fila(self._fases(), "medio")
        self.assertEqual((medio["rounds_ahead"], medio["rounds_behind"]), (0, 0))

    def test_una_ronda_sin_resultado_no_entra_al_denominador(self):
        rnd = self._ronda(0)
        rnd.my_team_won = None
        rnd.save()
        _baja(rnd, 0, ME, "rival1", 10)
        temprano = self._fila(self._fases(), "temprano")
        self.assertEqual(temprano["mine"], 1)
        self.assertEqual((temprano["rounds_ahead"], temprano["rounds_ahead_winrate"]), (0, None))

    def test_tu_equipo_se_lee_por_ronda(self):
        r0 = self._ronda(0, mi_equipo=0)
        _baja(r0, 0, ME, "rival1", 40)
        r1 = self._ronda(1, mi_equipo=1)
        _baja(r1, 0, "mate", "rival1", 40)
        _baja(r1, 1, "rival2", ME, 45)
        medio = self._fila(self._fases(), "medio")
        self.assertEqual((medio["mine"], medio["rival"]), (2, 1))

    def test_partida_sin_bajas_trae_tres_fases_en_cero(self):
        self._ronda(0)
        fases = self._fases()
        self.assertEqual(len(fases["rows"]), 3)
        for fila in fases["rows"]:
            self.assertEqual((fila["mine"], fila["rival"], fila["rounds_ahead"]), (0, 0, 0))
            self.assertIsNone(fila["rounds_ahead_winrate"])

    def test_sin_rondas_la_funcion_devuelve_tres_filas(self):
        fases = fases_de_partida([], 0)
        self.assertEqual([f["key"] for f in fases["rows"]], ["temprano", "medio", "tarde"])
        self.assertEqual(fases["rows"][2]["end"], None)

    def test_cambiar_de_lado_en_la_ronda_no_confunde_a_los_equipos(self):
        # Bajas asimetricas: con el indice de la partida fijo, la baja de "mate"
        # en la segunda ronda contaria como del rival.
        r0 = self._ronda(0, mi_equipo=0)
        _baja(r0, 0, ME, "rival1", 40)
        r1 = self._ronda(1, mi_equipo=1)
        _baja(r1, 0, "mate", "rival1", 40)
        medio = self._fila(self._fases(), "medio")
        self.assertEqual((medio["mine"], medio["rival"]), (2, 0))

    def test_una_ronda_dominada_por_el_rival_que_ganaste_igual(self):
        rnd = self._ronda(0, won=True)
        _baja(rnd, 0, "rival1", "mate", 50)
        medio = self._fila(self._fases(), "medio")
        self.assertEqual(
            (medio["rounds_behind"], medio["rounds_behind_won"], medio["rounds_behind_winrate"]),
            (1, 1, 100.0),
        )

    def test_una_ronda_sin_tu_fila_usa_el_equipo_de_la_partida(self):
        rnd = make_round(self.match, 0, won=True)
        make_round_player(rnd, username="mate", is_me=False, team_index=0)
        make_round_player(rnd, username="rival1", is_me=False, team_index=1, won=False)
        _baja(rnd, 0, "mate", "rival1", 40)
        medio = self._fila(self._fases(), "medio")
        self.assertEqual((medio["mine"], medio["rival"]), (1, 0))
