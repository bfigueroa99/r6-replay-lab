"""Tests de la pestana de posicionamiento.

Lo que se prueba aca es sobre todo lo que la vista **no** debe afirmar: la
granularidad es sitio y spawn porque el `.rec` no trae coordenadas, y una
diferencia que no pasa la banda de ruido se marca como ruido y no como hallazgo.
"""

from __future__ import annotations

import json

from django.test import TestCase

from replays.analytics import aggregates as agg
from replays.analytics.coach import build_insights
from replays.export import TABLES, export

from .factories import make_match, make_round, make_round_player


def buscar(payload, key):
    return next((i for i in payload["insights"] if i["key"] == key), None)


class Escenario(TestCase):
    """Base con un helper para fabricar rondas en una zona."""

    def setUp(self):
        self.numero = 0
        self.matches: dict[str, object] = {}

    def _match(self, map_name: str):
        if map_name not in self.matches:
            self.matches[map_name] = make_match(map_name=map_name, index=len(self.matches))
        return self.matches[map_name]

    def zona(
        self,
        cantidad: int,
        *,
        dormidas: int,
        site: str = "A Cocina",
        map_name: str = "Club House",
        side: str = "Attack",
        spawn: str = "Warehouse",
    ) -> None:
        """`cantidad` rondas en esa zona, `dormidas` de ellas fuera de posicion.

        Fuera de posicion = moriste, sin bajas y sin que nadie te vengue. Las
        otras se resuelven con una baja y sobreviviendo, que es el contrario
        limpio: ni muerte ni nada que discutir.
        """
        match = self._match(map_name)
        for i in range(cantidad):
            rnd = make_round(match, self.numero, side=side, site=site)
            self.numero += 1
            fuera = i < dormidas
            make_round_player(
                rnd,
                side=side,
                spawn=spawn,
                kills=0 if fuera else 1,
                died=fuera,
                was_traded=False,
                death_elapsed=40.0 if fuera else None,
            )


class MetricaTests(Escenario):
    """La definicion de 'te agarraron fuera de posicion'."""

    def _pct(self):
        return agg.totals(agg.base_queryset())["caught_out_pct"]

    def test_muerto_sin_bajas_y_sin_trade_cuenta(self):
        self.zona(4, dormidas=4)
        self.assertEqual(self._pct(), 100.0)

    def test_una_baja_lo_desarma(self):
        """Moriste, pero te llevaste a alguien: eso no es quedar dormido."""
        match = self._match("Club House")
        rnd = make_round(match, 0, site="A Cocina")
        make_round_player(rnd, kills=1, died=True, was_traded=False)
        self.assertEqual(self._pct(), 0.0)

    def test_que_te_vengan_lo_desarma(self):
        """Muerte sin bajas, pero tradeada: estabas con el equipo."""
        match = self._match("Club House")
        rnd = make_round(match, 0, site="A Cocina")
        make_round_player(rnd, kills=0, died=True, was_traded=True)
        self.assertEqual(self._pct(), 0.0)

    def test_sobrevivir_lo_desarma(self):
        match = self._match("Club House")
        rnd = make_round(match, 0, site="A Cocina")
        make_round_player(rnd, kills=0, died=False, death_elapsed=None)
        self.assertEqual(self._pct(), 0.0)

    def test_el_porcentaje_va_sobre_rondas_y_no_sobre_muertes(self):
        """Dos de cuatro rondas, no dos de dos muertes.

        Es la diferencia con `untraded_death_pct`, que si va sobre muertes: la
        pregunta aca es cada cuanto te pasa por ronda jugada.
        """
        self.zona(4, dormidas=2)
        fila = agg.totals(agg.base_queryset())
        self.assertEqual(fila["caught_out_pct"], 50.0)
        self.assertEqual(fila["untraded_death_pct"], 100.0)


class VeredictoTests(Escenario):
    def _sitio(self, nombre: str, datos=None):
        datos = datos or agg.positioning()
        return next(s for s in datos["sites"] if s["site"] == nombre)

    def test_una_diferencia_grande_es_dormidero(self):
        self.zona(20, dormidas=18, site="A Cocina")
        self.zona(80, dormidas=16, site="B Iglesia")
        fila = self._sitio("A Cocina")
        self.assertEqual(fila["verdict"], "dormidero")
        self.assertEqual(fila["caught_out_pct"], 90.0)
        self.assertEqual(fila["rest_caught_out_pct"], 20.0)
        self.assertEqual(fila["caught_out_delta"], 70.0)

    def test_una_diferencia_chica_es_ruido(self):
        """6 puntos con 10 rondas contra 50 no significan nada, y se dice."""
        self.zona(10, dormidas=5, site="A Cocina")
        self.zona(50, dormidas=22, site="B Iglesia")
        fila = self._sitio("A Cocina")
        self.assertEqual(fila["verdict"], "ruido")
        self.assertEqual(fila["caught_out_delta"], 6.0)
        self.assertGreater(fila["noise"], abs(fila["caught_out_delta"]))

    def test_la_zona_buena_se_marca_solida(self):
        self.zona(20, dormidas=1, site="A Cocina")
        self.zona(80, dormidas=56, site="B Iglesia")
        fila = self._sitio("A Cocina")
        self.assertEqual(fila["verdict"], "solido")
        self.assertLess(fila["caught_out_delta"], 0)

    def test_se_compara_contra_el_resto_y_no_contra_el_total(self):
        """La zona esta dentro del total: incluirla es compararla consigo misma.

        Con 20 de 20 dormidas en un sitio y 0 de 20 en el otro, contra el total
        la diferencia seria 50 puntos; contra el resto es 100, que es la
        comparacion que se quiere.
        """
        self.zona(20, dormidas=20, site="A Cocina")
        self.zona(20, dormidas=0, site="B Iglesia")
        fila = self._sitio("A Cocina")
        self.assertEqual(fila["rest_rounds"], 20)
        self.assertEqual(fila["rest_caught_out_pct"], 0.0)
        self.assertEqual(fila["caught_out_delta"], 100.0)

    def test_sin_resto_no_hay_veredicto(self):
        """Un solo sitio en todo el historial: no hay contra que comparar."""
        self.zona(10, dormidas=5, site="A Cocina")
        fila = self._sitio("A Cocina")
        self.assertEqual(fila["rest_rounds"], 0)
        self.assertIsNone(fila["rest_caught_out_pct"])
        self.assertEqual(fila["verdict"], "ruido")


class TablasTests(Escenario):
    def test_min_rounds_deja_fuera_las_zonas_flacas(self):
        self.zona(10, dormidas=5, site="A Cocina")
        self.zona(2, dormidas=2, site="B Iglesia")
        sitios = [s["site"] for s in agg.positioning(min_rounds=5)["sites"]]
        self.assertIn("A Cocina", sitios)
        self.assertNotIn("B Iglesia", sitios)

    def test_los_spawns_son_solo_de_ataque(self):
        self.zona(6, dormidas=3, side="Attack", spawn="Warehouse")
        self.zona(6, dormidas=3, side="Defense", spawn="", site="B Iglesia")
        spawns = agg.positioning(min_rounds=1)["spawns"]
        self.assertEqual([s["spawn"] for s in spawns], ["Warehouse"])
        self.assertEqual(spawns[0]["rounds"], 6)

    def test_el_spawn_se_compara_solo_contra_ataque(self):
        """Un spawn normal para tu ataque no puede salir marcado.

        En ataque se queda fuera de posicion mucho mas seguido que en defensa.
        Medir un spawn contra un promedio que incluye defensa lo hace ver mal
        por ser de ataque, no por ser ese spawn.
        """
        # ataque: 80% fuera de posicion en los dos spawns por igual
        self.zona(20, dormidas=16, side="Attack", spawn="Warehouse", site="A Cocina")
        self.zona(20, dormidas=16, side="Attack", spawn="Muddy Road", site="A Cocina")
        # defensa: mucho mejor, y arrastra el promedio general hacia abajo
        self.zona(40, dormidas=4, side="Defense", spawn="", site="B Iglesia")

        spawns = {s["spawn"]: s for s in agg.positioning(min_rounds=5)["spawns"]}
        warehouse = spawns["Warehouse"]
        self.assertEqual(warehouse["caught_out_pct"], 80.0)
        # contra el resto del ataque (el otro spawn) no hay diferencia
        self.assertEqual(warehouse["rest_caught_out_pct"], 80.0)
        self.assertEqual(warehouse["caught_out_delta"], 0.0)
        self.assertEqual(warehouse["verdict"], "ruido")

    def test_el_sitio_si_se_compara_contra_los_dos_lados(self):
        """Un sitio se juega de los dos lados, asi que su referencia es el total."""
        self.zona(20, dormidas=16, side="Attack", site="A Cocina")
        self.zona(40, dormidas=4, side="Defense", site="B Iglesia")
        cocina = next(s for s in agg.positioning(min_rounds=5)["sites"] if s["site"] == "A Cocina")
        self.assertEqual(cocina["rest_rounds"], 40)
        self.assertEqual(cocina["rest_caught_out_pct"], 10.0)

    def test_los_lados_van_siempre_aunque_tengan_poca_muestra(self):
        self.zona(3, dormidas=3, side="Attack")
        self.zona(2, dormidas=0, side="Defense", site="B Iglesia")
        lados = {s["side"]: s for s in agg.positioning(min_rounds=99)["sides"]}
        self.assertEqual(set(lados), {"Attack", "Defense"})
        self.assertEqual(lados["Attack"]["caught_out_pct"], 100.0)

    def test_las_zonas_sin_sitio_no_inventan_una_fila(self):
        match = self._match("Club House")
        rnd = make_round(match, 0, site="")
        make_round_player(rnd, kills=0, died=True)
        self.assertEqual(agg.positioning(min_rounds=1)["sites"], [])

    def test_la_base_vacia_no_revienta(self):
        datos = agg.positioning()
        self.assertEqual(datos["sites"], [])
        self.assertEqual(datos["overall"]["rounds"], 0)


class ApiTests(Escenario):
    def test_el_endpoint_responde_con_las_tres_tablas(self):
        self.zona(20, dormidas=18, site="A Cocina")
        self.zona(80, dormidas=16, site="B Iglesia")
        respuesta = self.client.get("/api/positioning/")
        self.assertEqual(respuesta.status_code, 200)
        payload = json.loads(respuesta.content)
        self.assertEqual(set(payload) >= {"overall", "sites", "spawns", "sides"}, True)
        self.assertEqual(payload["min_rounds"], agg.POSITION_MIN_ROUNDS)
        cocina = next(s for s in payload["sites"] if s["site"] == "A Cocina")
        self.assertEqual(cocina["verdict"], "dormidero")

    def test_respeta_el_filtro_de_mapa(self):
        self.zona(10, dormidas=10, map_name="Club House", site="A Cocina")
        self.zona(10, dormidas=0, map_name="Border", site="B Armeria")
        payload = json.loads(self.client.get("/api/positioning/?map=border").content)
        self.assertEqual([s["site"] for s in payload["sites"]], ["B Armeria"])

    def test_min_rounds_llega_por_query_string(self):
        self.zona(3, dormidas=3, site="A Cocina")
        payload = json.loads(self.client.get("/api/positioning/?min_rounds=1").content)
        self.assertEqual(len(payload["sites"]), 1)

    def test_la_base_vacia_responde_200(self):
        self.assertEqual(self.client.get("/api/positioning/").status_code, 200)


class ExportTests(Escenario):
    def test_las_tablas_estan_registradas(self):
        self.assertIn("positioning_sites", TABLES)
        self.assertIn("positioning_spawns", TABLES)

    def test_exporta_el_veredicto(self):
        self.zona(20, dormidas=18, site="A Cocina")
        self.zona(80, dormidas=16, site="B Iglesia")
        filas = export("positioning_sites")
        cocina = next(f for f in filas if f["site"] == "A Cocina")
        self.assertEqual(cocina["verdict"], "dormidero")


class CoachTests(Escenario):
    def test_marca_la_peor_zona(self):
        self.zona(20, dormidas=18, site="A Cocina")
        self.zona(80, dormidas=16, site="B Iglesia")
        insight = buscar(build_insights(), "zona-dormidero")
        self.assertIsNotNone(insight)
        self.assertIn("A Cocina", insight["title"])
        self.assertEqual(insight["sample"], 20)

    def test_no_habla_cuando_la_diferencia_es_ruido(self):
        self.zona(10, dormidas=5, site="A Cocina")
        self.zona(50, dormidas=22, site="B Iglesia")
        self.assertIsNone(buscar(build_insights(), "zona-dormidero"))

    def test_reconoce_la_zona_solida(self):
        self.zona(20, dormidas=1, site="A Cocina")
        self.zona(80, dormidas=56, site="B Iglesia")
        insight = buscar(build_insights(), "zona-solida")
        self.assertIsNotNone(insight)
        self.assertEqual(insight["severity"], "positivo")
