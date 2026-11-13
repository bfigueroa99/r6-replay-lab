"""Tests de repetir o cambiar de operador tras una ronda (ficha 113)."""

from __future__ import annotations

from django.test import TestCase

from replays.analytics import aggregates as agg

from .factories import make_match, make_round, make_round_player

URL = "/api/operators/after-result/"
A, D = "Attack", "Defense"


class OperadorTrasResultadoTests(TestCase):
    def setUp(self):
        self.indice = 0

    def _partida(self, rondas, *, map_name="Club House", desde=0):
        """`rondas`: tuplas (lado, operador, gano[, sitio]); None salta un numero."""
        match = make_match(index=self.indice, map_name=map_name)
        self.indice += 1
        for numero, ronda in enumerate(rondas, start=desde):
            if ronda is None:
                continue
            lado, operador, gano, *resto = ronda
            rnd = make_round(match, numero, side=lado, won=gano,
                             site=resto[0] if resto else "")
            make_round_player(rnd, operator=operador, won=bool(gano))
        return match

    def _celda(self, datos, tras, caso, lado=A):
        return datos["sides"][lado][tras][caso]

    def test_perder_con_ash_y_volver_a_ash_cuenta_repeat(self):
        self._partida([(A, "Ash", False), (A, "Ash", True)])
        datos = agg.operator_after_result()
        self.assertEqual(datos["pairs"], 1)
        repeat = self._celda(datos, "after_loss", "repeat")
        self.assertEqual((repeat["rounds"], repeat["winrate"]), (1, 100.0))
        self.assertEqual(self._celda(datos, "after_loss", "switch")["rounds"], 0)

    def test_pasar_a_thermite_cuenta_switch(self):
        self._partida([(A, "Ash", False), (A, "Thermite", False)])
        switch = self._celda(agg.operator_after_result(), "after_loss", "switch")
        self.assertEqual((switch["rounds"], switch["winrate"]), (1, 0.0))

    def test_tras_ganar_va_a_after_win(self):
        self._partida([(A, "Ash", True), (A, "Ash", True)])
        datos = agg.operator_after_result()
        self.assertEqual(self._celda(datos, "after_win", "repeat")["rounds"], 1)
        self.assertEqual(self._celda(datos, "after_loss", "repeat")["rounds"], 0)

    def test_las_rondas_del_otro_lado_no_cortan_el_par(self):
        self._partida([(A, "Ash", False), (D, "Mute", True), (A, "Ash", True)])
        datos = agg.operator_after_result()
        self.assertEqual(datos["pairs"], 1)
        self.assertEqual(self._celda(datos, "after_loss", "repeat")["rounds"], 1)

    def test_una_ronda_faltante_entre_medio_corta_el_par(self):
        self._partida([(A, "Ash", False), None, (A, "Ash", True)])
        self.assertEqual(agg.operator_after_result()["pairs"], 0)

    def test_operador_vacio_o_unknown_corta_el_par(self):
        # Como segunda no cuenta, y como primera no abre par con la siguiente.
        self._partida([(A, "Ash", False), (A, "", False), (A, "Ash", True)])
        self._partida([(A, "Ash", False), (A, "Unknown(7)", False), (A, "Ash", True)])
        self.assertEqual(agg.operator_after_result()["pairs"], 0)

    def test_una_ronda_sin_lado_corta_el_par(self):
        self._partida([(A, "Ash", False), ("", "Ash", False), (A, "Ash", True)])
        self.assertEqual(agg.operator_after_result()["pairs"], 0)

    def test_los_pares_no_cruzan_partidas(self):
        # La segunda arranca en la ronda 2: sin hueco de numero, solo el cambio
        # de partida puede cortar el par.
        self._partida([(A, "Ash", False), (A, "Ash", False)])
        self._partida([(A, "Ash", True)], desde=2)
        datos = agg.operator_after_result()
        self.assertEqual(datos["pairs"], 1)
        self.assertEqual(self._celda(datos, "after_loss", "repeat")["winrate"], 0.0)

    def test_los_pares_no_cruzan_lados(self):
        self._partida([(A, "Ash", False), (D, "Mute", True)])
        self.assertEqual(agg.operator_after_result()["pairs"], 0)

    def test_primera_sin_ganador_no_abre_par(self):
        self._partida([(A, "Ash", None), (A, "Ash", True)])
        self.assertEqual(agg.operator_after_result()["pairs"], 0)

    def test_segunda_sin_ganador_cuenta_en_rondas_y_no_en_winrate(self):
        self._partida([(A, "Ash", False), (A, "Ash", True), (A, "Ash", None)])
        datos = agg.operator_after_result()
        perder = self._celda(datos, "after_loss", "repeat")
        ganar = self._celda(datos, "after_win", "repeat")
        self.assertEqual((perder["rounds"], perder["decided"], perder["winrate"]), (1, 1, 100.0))
        self.assertEqual((ganar["rounds"], ganar["decided"], ganar["winrate"]), (1, 0, None))

    def test_el_filtro_de_operador_elige_la_primera_ronda(self):
        self._partida([
            (A, "Ash", False), (A, "Thermite", False),
            (A, "Thermite", False), (A, "Ash", False),
        ])
        datos = self.client.get(URL, {"operator": "Ash"}).json()
        self.assertEqual(datos["pairs"], 1)
        self.assertEqual(self._celda(datos, "after_loss", "switch")["rounds"], 1)
        self.assertEqual(self._celda(datos, "after_loss", "repeat")["rounds"], 0)

    def test_el_filtro_de_operador_no_mira_la_segunda_ronda(self):
        # Ash->Thermite cae en after_win y Thermite->Ash en after_loss: si el
        # filtro mirara la segunda ronda, los numeros saldrian al reves
        self._partida([
            (A, "Ash", True), (A, "Thermite", False),
            (A, "Thermite", False), (A, "Ash", False),
        ])
        datos = self.client.get(URL, {"operator": "Ash"}).json()
        self.assertEqual(datos["pairs"], 1)
        self.assertEqual(self._celda(datos, "after_win", "switch")["rounds"], 1)
        self.assertEqual(self._celda(datos, "after_loss", "switch")["rounds"], 0)

    def test_el_filtro_de_sitio_elige_la_primera_ronda(self):
        self._partida([
            (A, "Ash", False, "2F Kitchen"), (A, "Thermite", True, "1F Bar"),
            (A, "Thermite", False, "1F Bar"), (A, "Thermite", True, "2F Kitchen"),
        ])
        datos = self.client.get(URL, {"site": "2F Kitchen"}).json()
        self.assertEqual(datos["pairs"], 1)
        switch = self._celda(datos, "after_loss", "switch")
        self.assertEqual((switch["rounds"], switch["winrate"]), (1, 100.0))

    def test_el_filtro_de_lado_se_ignora(self):
        self._partida([(A, "Ash", False), (D, "Mute", True), (A, "Ash", True),
                       (D, "Smoke", False)])
        sin = self.client.get(URL).json()
        con = self.client.get(URL, {"side": A}).json()
        self.assertEqual(sin["pairs"], 2)
        self.assertEqual(sin, con)

    def test_el_filtro_de_mapa_aplica(self):
        self._partida([(A, "Ash", False), (A, "Ash", True)])
        self._partida([(A, "Ash", False), (A, "Sledge", True)], map_name="Bank")
        datos = self.client.get(URL, {"map": "bank"}).json()
        self.assertEqual(datos["pairs"], 1)
        self.assertEqual(self._celda(datos, "after_loss", "switch")["rounds"], 1)
        self.assertEqual(self._celda(datos, "after_loss", "repeat")["rounds"], 0)

    def test_el_filtro_de_tipo_de_partida_aplica(self):
        self._partida([(A, "Ash", False), (A, "Ash", True)])
        self.assertEqual(self.client.get(URL, {"match_type": "Unranked"}).json()["pairs"], 0)

    def test_total_suma_los_dos_lados(self):
        self._partida([
            (A, "Ash", False), (D, "Mute", False), (A, "Ash", True), (D, "Smoke", True),
        ])
        datos = agg.operator_after_result()
        self.assertEqual(datos["pairs"], 2)
        self.assertEqual(self._celda(datos, "after_loss", "switch", D)["rounds"], 1)
        perder = datos["total"]["after_loss"]
        self.assertEqual(perder["repeat"]["rounds"], 1)
        self.assertEqual(perder["switch"]["rounds"], 1)
        self.assertEqual(perder["repeat"]["winrate"], 100.0)

    def test_sin_pares_responde_vacio_sin_error(self):
        respuesta = self.client.get(URL)
        self.assertEqual(respuesta.status_code, 200)
        datos = respuesta.json()
        self.assertEqual(datos["pairs"], 0)
        self.assertEqual(datos["min_rounds"], agg.OPERADOR_TRAS_RESULTADO_MIN_RONDAS)
        self.assertIsNone(datos["total"]["after_loss"]["repeat"]["winrate"])
