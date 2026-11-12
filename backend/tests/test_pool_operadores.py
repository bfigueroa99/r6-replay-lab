"""Tests del pool de operadores por lado (ficha 102)."""

from __future__ import annotations

from datetime import datetime, timedelta

from django.test import TestCase

from replays.analytics import aggregates as agg

from .factories import make_match, make_round, make_round_player

CATALOGO = [
    {"name": "Ash", "side": "Attack"},
    {"name": "Sledge", "side": "Attack"},
    {"name": "Thermite", "side": "Attack"},
    {"name": "Mute", "side": "Defense"},
    {"name": "Smoke", "side": "Defense"},
]

HOY = datetime(2026, 9, 1, 20, 0)


class PoolDeOperadoresTests(TestCase):
    def setUp(self):
        self.indice = 0

    def _partida(self, operadores, *, cuando, side="Attack", map_name="Club House"):
        match = make_match(index=self.indice, played_at=cuando, map_name=map_name)
        self.indice += 1
        for numero, operador in enumerate(operadores):
            rnd = make_round(match, numero, side=side)
            make_round_player(rnd, operator=operador)
        return match

    def test_cuenta_operadores_distintos_por_lado_en_la_ventana_y_en_total(self):
        for i in range(22):
            operador = "Thermite" if i < 2 else "Ash"
            self._partida([operador], cuando=HOY - timedelta(hours=22 - i))
        self._partida(["Mute"], cuando=HOY, side="Defense")
        pool = agg.operator_pool(CATALOGO)
        self.assertEqual(pool["matches"], 23)
        self.assertEqual(pool["recent_matches"], agg.POOL_PARTIDAS_RECIENTES)
        ataque = pool["sides"]["Attack"]
        self.assertEqual(ataque["distinct_all"], 2)
        self.assertEqual(ataque["distinct_recent"], 1)
        self.assertEqual(pool["sides"]["Defense"]["distinct_recent"], 1)

    def test_un_operador_jugado_hace_40_dias_cae_en_stale(self):
        self._partida(["Thermite", "Thermite"], cuando=HOY - timedelta(days=40))
        self._partida(["Sledge"], cuando=HOY - timedelta(days=10))
        self._partida(["Ash"], cuando=HOY)
        stale = agg.operator_pool(CATALOGO)["sides"]["Attack"]["stale"]
        self.assertEqual(
            stale,
            [{"operator": "Thermite",
              "last_played": (HOY - timedelta(days=40)).isoformat(), "rounds": 2}],
        )

    def test_stale_va_de_la_mas_reciente_a_la_mas_vieja(self):
        self._partida(["Thermite"], cuando=HOY - timedelta(days=90))
        self._partida(["Sledge"], cuando=HOY - timedelta(days=40))
        self._partida(["Ash"], cuando=HOY)
        stale = agg.operator_pool(CATALOGO)["sides"]["Attack"]["stale"]
        self.assertEqual([s["operator"] for s in stale], ["Sledge", "Thermite"])

    def test_la_referencia_es_tu_ultima_partida_y_no_hoy(self):
        hace_un_anio = datetime(2025, 9, 1, 20, 0)
        self._partida(["Thermite"], cuando=hace_un_anio - timedelta(days=3))
        self._partida(["Ash"], cuando=hace_un_anio)
        pool = agg.operator_pool(CATALOGO)
        self.assertEqual(pool["sides"]["Attack"]["stale"], [])
        self.assertTrue(pool["reference"].startswith("2025-09-01"))

    def test_un_operador_del_catalogo_sin_rondas_cae_en_never(self):
        self._partida(["Ash"], cuando=HOY)
        pool = agg.operator_pool(CATALOGO)
        self.assertEqual(pool["sides"]["Attack"]["never"], ["Sledge", "Thermite"])
        self.assertEqual(pool["sides"]["Defense"]["never"], ["Mute", "Smoke"])

    def test_unknown_y_operador_vacio_no_cuentan(self):
        self._partida(["Ash", "", "Unknown(123)"], cuando=HOY)
        catalogo = [*CATALOGO, {"name": "Unknown(123)", "side": "Attack"},
                    {"name": "", "side": "Attack"}]
        pool = agg.operator_pool(catalogo)
        ataque = pool["sides"]["Attack"]
        self.assertEqual(ataque["distinct_all"], 1)
        self.assertEqual(ataque["distinct_recent"], 1)
        self.assertNotIn("", ataque["never"])
        self.assertNotIn("Unknown(123)", ataque["never"])

    def test_una_partida_solo_con_unknown_no_cuenta_como_partida(self):
        self._partida(["Unknown(9)"], cuando=HOY)
        pool = agg.operator_pool(CATALOGO)
        self.assertEqual(pool["matches"], 0)
        self.assertIsNone(pool["reference"])

    def test_el_filtro_de_operador_y_el_de_lado_se_ignoran(self):
        self._partida(["Ash", "Sledge"], cuando=HOY)
        self._partida(["Mute"], cuando=HOY, side="Defense")
        sin_filtro = self.client.get("/api/operators/pool/").json()
        con_filtro = self.client.get("/api/operators/pool/?operator=Ash&side=Attack").json()
        self.assertEqual(sin_filtro, con_filtro)
        self.assertEqual(sin_filtro["sides"]["Defense"]["distinct_all"], 1)

    def test_el_filtro_de_sitio_se_ignora(self):
        self._partida(["Ash", "Sledge"], cuando=HOY)
        sin_filtro = self.client.get("/api/operators/pool/").json()
        con_sitio = self.client.get("/api/operators/pool/?site=Otro").json()
        self.assertEqual(sin_filtro, con_sitio)

    def test_stale_desempata_por_nombre_con_la_misma_fecha(self):
        self._partida(["Thermite", "Ash"], cuando=HOY - timedelta(days=40))
        self._partida(["Sledge"], cuando=HOY)
        stale = agg.operator_pool(CATALOGO)["sides"]["Attack"]["stale"]
        self.assertEqual([s["operator"] for s in stale], ["Ash", "Thermite"])

    def test_el_filtro_de_mapa_aplica(self):
        self._partida(["Ash"], cuando=HOY)
        self._partida(["Sledge"], cuando=HOY, map_name="Oregon")
        pool = self.client.get("/api/operators/pool/?map=club-house").json()
        ataque = pool["sides"]["Attack"]
        self.assertIn("Sledge", ataque["never"])
        self.assertNotIn("Ash", ataque["never"])
        self.assertEqual(pool["matches"], 1)

    def test_sin_partidas_responde_vacio_sin_error(self):
        respuesta = self.client.get("/api/operators/pool/")
        self.assertEqual(respuesta.status_code, 200)
        pool = respuesta.json()
        self.assertEqual(pool["matches"], 0)
        self.assertEqual(pool["recent_matches"], 0)
        self.assertIsNone(pool["reference"])
        self.assertEqual(pool["sides"]["Attack"]["distinct_all"], 0)
        self.assertEqual(pool["sides"]["Attack"]["stale"], [])
