"""Tests de repetir el sitio tras perderlo en defensa (ficha 107)."""

from __future__ import annotations

from datetime import datetime

from django.test import TestCase

from replays.analytics import aggregates as agg

from .factories import make_match, make_round, make_round_player

KITCHEN = "2F Kitchen"
BAR = "1F Bar"
URL = "/api/positioning/site-after-loss/"


class RepetirSitioTests(TestCase):
    def setUp(self):
        self.indice = 0

    def _partida(self, rondas, *, map_name="Club House", map_id=0):
        """`rondas`: tuplas (lado, sitio, gano) en orden; None en vez de tupla salta un numero."""
        match = make_match(index=self.indice, map_name=map_name, map_id=map_id)
        self.indice += 1
        for numero, ronda in enumerate(rondas):
            if ronda is None:
                continue
            lado, sitio, gano = ronda
            rnd = make_round(match, numero, side=lado, site=sitio, won=gano)
            make_round_player(rnd, operator="Ash" if lado == "Attack" else "Mute",
                              won=bool(gano))
        return match

    def _total(self, **filters):
        return agg.site_after_loss(**filters)["total"]

    def test_perder_y_volver_al_mismo_sitio_cuenta_repeat(self):
        self._partida([("Defense", KITCHEN, False), ("Defense", KITCHEN, True)])
        datos = agg.site_after_loss()
        self.assertEqual(datos["pairs"], 1)
        self.assertEqual(datos["total"]["repeat"]["rounds"], 1)
        self.assertEqual(datos["total"]["repeat"]["winrate"], 100.0)
        self.assertEqual(datos["total"]["switch"]["rounds"], 0)

    def test_ir_a_otro_sitio_cuenta_switch(self):
        self._partida([("Defense", KITCHEN, False), ("Defense", BAR, False)])
        total = self._total()
        self.assertEqual(total["switch"]["rounds"], 1)
        self.assertEqual(total["switch"]["winrate"], 0.0)
        self.assertEqual(total["repeat"]["rounds"], 0)

    def test_las_rondas_de_ataque_entre_medio_no_cortan_el_par(self):
        self._partida([
            ("Defense", KITCHEN, False), ("Attack", "", True), ("Defense", KITCHEN, True),
        ])
        self.assertEqual(self._total()["repeat"]["rounds"], 1)

    def test_una_ronda_sin_sitio_corta_el_par(self):
        # Como segunda: no cuenta. Como primera: no abre par con la siguiente.
        self._partida([
            ("Defense", KITCHEN, False), ("Defense", "", False), ("Defense", KITCHEN, True),
        ])
        self.assertEqual(agg.site_after_loss()["pairs"], 0)

    def test_una_ronda_faltante_entre_medio_corta_el_par(self):
        self._partida([("Defense", KITCHEN, False), None, ("Defense", KITCHEN, True)])
        self.assertEqual(agg.site_after_loss()["pairs"], 0)

    def test_los_pares_no_cruzan_partidas(self):
        # La segunda partida arranca en la ronda 2: solo el cambio de partida corta.
        self._partida([("Attack", "", True), ("Defense", KITCHEN, False)])
        self._partida([None, None, ("Defense", KITCHEN, True)])
        self.assertEqual(agg.site_after_loss()["pairs"], 0)

    def test_tras_ganar_o_sin_ganador_no_hay_par(self):
        self._partida([
            ("Defense", KITCHEN, True), ("Defense", KITCHEN, None), ("Defense", KITCHEN, True),
        ])
        self.assertEqual(agg.site_after_loss()["pairs"], 0)

    def test_winrate_de_la_segunda_ronda_sin_contar_la_sin_ganador(self):
        self._partida([
            ("Defense", KITCHEN, False), ("Defense", KITCHEN, False),
            ("Defense", KITCHEN, True),
        ])
        self._partida([("Defense", KITCHEN, False), ("Defense", KITCHEN, None)])
        repeat = self._total()["repeat"]
        # Pares: L->L, L->W y L->sin ganador.
        self.assertEqual(repeat["rounds"], 3)
        self.assertEqual(repeat["decided"], 2)
        self.assertEqual(repeat["won"], 1)
        self.assertEqual(repeat["winrate"], 50.0)

    def test_el_filtro_de_sitio_mira_la_ronda_perdida(self):
        self._partida([("Defense", KITCHEN, False), ("Defense", BAR, False)])
        self._partida([("Defense", BAR, False), ("Defense", KITCHEN, False)])
        datos = self.client.get(URL, {"site": KITCHEN}).json()
        self.assertEqual(datos["pairs"], 1)
        self.assertEqual(datos["total"]["switch"]["rounds"], 1)
        self.assertEqual(datos["maps"][0]["switch"]["rounds"], 1)

    def test_el_filtro_de_sitio_no_mira_la_segunda_ronda(self):
        # Si el filtro mirara la segunda ronda, ningun par entraria: las dos
        # segundas son Bar. Mirando la perdida entra solo el de Kitchen.
        self._partida([("Defense", KITCHEN, False), ("Defense", BAR, True)])
        self._partida([("Defense", BAR, False), ("Defense", BAR, False)])
        datos = self.client.get(URL, {"site": KITCHEN}).json()
        self.assertEqual(datos["pairs"], 1)
        self.assertEqual(datos["total"]["switch"]["rounds"], 1)
        self.assertEqual(datos["total"]["switch"]["winrate"], 100.0)
        self.assertEqual(datos["total"]["repeat"]["rounds"], 0)

    def test_el_filtro_de_fechas_aplica(self):
        vieja = self._partida([("Defense", KITCHEN, False), ("Defense", KITCHEN, True)])
        vieja.played_at = datetime(2025, 1, 10, 20, 0)
        vieja.save(update_fields=["played_at"])
        self._partida([("Defense", KITCHEN, False), ("Defense", BAR, True)])
        datos = self.client.get(URL, {"since": "2026-01-01"}).json()
        self.assertEqual(datos["pairs"], 1)
        self.assertEqual(datos["total"]["switch"]["rounds"], 1)
        self.assertEqual(datos["total"]["repeat"]["rounds"], 0)

    def test_el_filtro_de_lado_y_el_de_operador_se_ignoran(self):
        self._partida([
            ("Defense", KITCHEN, False), ("Attack", "", True), ("Defense", BAR, True),
        ])
        sin = self.client.get(URL).json()
        con = self.client.get(URL, {"side": "Attack", "operator": "Ash"}).json()
        self.assertEqual(sin["pairs"], 1)
        self.assertEqual(sin, con)

    def test_el_filtro_de_mapa_aplica(self):
        self._partida([("Defense", KITCHEN, False), ("Defense", KITCHEN, True)])
        self._partida([("Defense", "1F Vault", False), ("Defense", "2F Office", True)],
                      map_name="Bank")
        datos = self.client.get(URL, {"map": "bank"}).json()
        self.assertEqual(datos["pairs"], 1)
        self.assertEqual(datos["total"]["switch"]["rounds"], 1)
        self.assertEqual([m["slug"] for m in datos["maps"]], ["bank"])

    def test_el_filtro_de_tipo_de_partida_aplica(self):
        self._partida([("Defense", KITCHEN, False), ("Defense", KITCHEN, True)])
        datos = self.client.get(URL, {"match_type": "Unranked"}).json()
        self.assertEqual(datos["pairs"], 0)

    def test_separa_por_mapa_con_su_version(self):
        self._partida([("Defense", KITCHEN, False), ("Defense", KITCHEN, True)])
        self._partida([("Defense", KITCHEN, False), ("Defense", BAR, True)])
        self._partida([("Defense", "1F Vault", False), ("Defense", "1F Vault", False)],
                      map_name="Bank")
        mapas = agg.site_after_loss()["maps"]
        self.assertEqual([m["slug"] for m in mapas], ["club-house", "bank"])
        club = mapas[0]
        self.assertEqual(club["map"], "Club House")
        self.assertEqual((club["repeat"]["rounds"], club["switch"]["rounds"]), (1, 1))
        self.assertEqual(mapas[1]["repeat"]["winrate"], 0.0)

    def test_dos_versiones_del_mapa_son_dos_filas(self):
        self._partida([("Defense", KITCHEN, False), ("Defense", KITCHEN, True)], map_id=1)
        self._partida([("Defense", KITCHEN, False), ("Defense", KITCHEN, True)], map_id=2)
        mapas = agg.site_after_loss()["maps"]
        self.assertEqual(sorted(m["map_id"] for m in mapas), [1, 2])

    def test_sin_pares_responde_vacio_sin_error(self):
        respuesta = self.client.get(URL)
        self.assertEqual(respuesta.status_code, 200)
        datos = respuesta.json()
        self.assertEqual(datos["pairs"], 0)
        self.assertEqual(datos["maps"], [])
        self.assertIsNone(datos["total"]["repeat"]["winrate"])
        self.assertEqual(datos["min_rounds"], agg.REPETIR_SITIO_MIN_RONDAS)
