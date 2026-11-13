"""Tests de repetir o cambiar el spawn de ataque tras perder (ficha 128)."""

from __future__ import annotations

from django.test import TestCase

from replays.analytics import aggregates as agg

from .factories import make_match, make_round, make_round_player

URL = "/api/positioning/spawn-after-result/"
A = "Warehouse"
B = "Construction Site"


class RepetirSpawnTests(TestCase):
    def setUp(self):
        self.indice = 0

    def _partida(self, rondas, *, map_name="Club House", map_id=0):
        """`rondas`: tuplas (lado, spawn, gano[, operador]); None salta un numero."""
        match = make_match(index=self.indice, map_name=map_name, map_id=map_id)
        self.indice += 1
        for numero, ronda in enumerate(rondas):
            if ronda is None:
                continue
            lado, spawn, gano, *resto = ronda
            operador = resto[0] if resto else ("Ash" if lado == "Attack" else "Mute")
            rnd = make_round(match, numero, side=lado, won=gano)
            make_round_player(rnd, operator=operador, spawn=spawn, won=bool(gano))
        return match

    def test_tras_perder_cuenta_repetir_y_cambiar_con_el_winrate_de_la_segunda(self):
        # Pierdes desde A y repites A (ganas); pierdes desde A y repites A
        # (pierdes); pierdes desde A y cambias a B (ganas).
        self._partida([("Attack", A, False), ("Attack", A, True)])
        self._partida([("Attack", A, False), ("Attack", A, False)])
        self._partida([("Attack", A, False), ("Attack", B, True)])
        datos = agg.spawn_after_result()
        tras = datos["after_loss"]
        self.assertEqual(datos["pairs"], 3)
        self.assertEqual(tras["repeat"]["rounds"], 2)
        self.assertEqual(tras["repeat"]["winrate"], 50.0)
        self.assertEqual(tras["switch"]["rounds"], 1)
        self.assertEqual(tras["switch"]["winrate"], 100.0)
        self.assertEqual(datos["after_win"]["repeat"]["rounds"], 0)
        self.assertEqual(datos["min_rounds"], agg.REPETIR_SITIO_MIN_RONDAS)

    def test_tras_ganar_va_a_su_propio_bloque(self):
        self._partida([("Attack", A, True), ("Attack", B, False)])
        datos = agg.spawn_after_result()
        self.assertEqual(datos["after_win"]["switch"]["rounds"], 1)
        self.assertEqual(datos["after_win"]["switch"]["winrate"], 0.0)
        self.assertEqual(datos["after_loss"]["switch"]["rounds"], 0)

    def test_una_ronda_de_defensa_entre_medio_no_corta_el_par(self):
        self._partida([("Attack", A, False), ("Defense", "", True), ("Attack", A, True)])
        datos = agg.spawn_after_result()
        self.assertEqual(datos["pairs"], 1)
        self.assertEqual(datos["after_loss"]["repeat"]["rounds"], 1)

    def test_un_hueco_de_numeracion_corta_el_par(self):
        self._partida([("Attack", A, False), None, ("Attack", A, True)])
        self.assertEqual(agg.spawn_after_result()["pairs"], 0)

    def test_una_ronda_de_ataque_sin_spawn_corta_el_par(self):
        # Como segunda no cuenta; como primera no abre par con la siguiente.
        self._partida([("Attack", A, False), ("Attack", "", False), ("Attack", A, True)])
        self.assertEqual(agg.spawn_after_result()["pairs"], 0)

    def test_los_pares_no_cruzan_partidas(self):
        self._partida([("Attack", A, False)])
        self._partida([None, ("Attack", A, True)])
        self.assertEqual(agg.spawn_after_result()["pairs"], 0)

    def test_una_primera_sin_ganador_no_abre_par(self):
        self._partida([("Attack", A, None), ("Attack", A, True)])
        self.assertEqual(agg.spawn_after_result()["pairs"], 0)

    def test_una_segunda_sin_ganador_cuenta_en_rondas_y_no_en_el_winrate(self):
        self._partida([("Attack", A, False), ("Attack", A, None)])
        self._partida([("Attack", A, False), ("Attack", A, True)])
        repeat = agg.spawn_after_result()["after_loss"]["repeat"]
        self.assertEqual(repeat["rounds"], 2)
        self.assertEqual(repeat["decided"], 1)
        self.assertEqual(repeat["won"], 1)
        self.assertEqual(repeat["winrate"], 100.0)

    def test_el_filtro_de_operador_elige_la_primera_ronda(self):
        # Si el filtro mirara la segunda ronda, el par de Thermite no entraria.
        self._partida([("Attack", A, False, "Thermite"), ("Attack", B, True, "Ash")])
        self._partida([("Attack", A, False, "Ash"), ("Attack", A, True, "Ash")])
        datos = self.client.get(URL, {"operator": "Thermite"}).json()
        self.assertEqual(datos["pairs"], 1)
        self.assertEqual(datos["after_loss"]["switch"]["rounds"], 1)
        self.assertEqual(datos["after_loss"]["repeat"]["rounds"], 0)

    def test_el_filtro_de_mapa_aplica(self):
        self._partida([("Attack", A, False), ("Attack", A, True)])
        self._partida([("Attack", "Lakeside", False), ("Attack", "Parking", True)],
                      map_name="Bank")
        datos = self.client.get(URL, {"map": "bank"}).json()
        self.assertEqual(datos["pairs"], 1)
        self.assertEqual(datos["after_loss"]["switch"]["rounds"], 1)
        self.assertEqual(datos["after_loss"]["repeat"]["rounds"], 0)

    def test_el_filtro_de_lado_no_cambia_nada(self):
        self._partida([("Attack", A, False), ("Defense", "", True), ("Attack", B, True)])
        sin = self.client.get(URL).json()
        con = self.client.get(URL, {"side": "Defense"}).json()
        self.assertEqual(sin["pairs"], 1)
        self.assertEqual(sin, con)

    def test_el_endpoint_responde_con_base_vacia(self):
        datos = self.client.get(URL).json()
        self.assertEqual(datos["pairs"], 0)
        for tras in ("after_loss", "after_win"):
            for caso in ("repeat", "switch"):
                self.assertEqual(datos[tras][caso]["rounds"], 0)
                self.assertIsNone(datos[tras][caso]["winrate"])
