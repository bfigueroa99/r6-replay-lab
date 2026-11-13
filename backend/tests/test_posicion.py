"""Fuera de posicion por sitio y spawn (ficha 80)."""

from __future__ import annotations

import math

from django.test import TestCase

from replays.analytics import aggregates as agg
from replays.analytics.coach import build_insights

from .factories import make_match, make_round, make_round_player

SITIO_A = "A Bedroom, A Gym"
SITIO_B = "B Church, B Arsenal Room"


def zona(rondas: int, fuera: int, *, site: str = SITIO_A, side: str = "Attack",
         spawn: str = "Warehouse", index: int = 0, map_name: str = "Club House"):
    """`rondas` rondas en una zona, las primeras `fuera` fuera de posicion.

    Las demas se sobreviven sin bajas: no cuentan como fuera de posicion.
    """
    match = make_match(map_name=map_name, index=index)
    for n in range(rondas):
        rnd = make_round(match, n, side=side, site=site)
        if n < fuera:
            make_round_player(rnd, side=side, spawn=spawn, kills=0, died=True, was_traded=False)
        else:
            make_round_player(rnd, side=side, spawn=spawn, kills=0, died=False)
    return match


def fila(filas: list[dict], clave: str, valor: str) -> dict | None:
    return next((f for f in filas if f[clave] == valor), None)


def find(payload: dict, key: str) -> dict | None:
    return next((i for i in payload["insights"] if i["key"] == key), None)


class MetricaFueraDePosicionTests(TestCase):
    def test_fuera_de_posicion_exige_morir_sin_bajas_y_sin_trade(self):
        match = make_match()
        casos = (
            {"kills": 0, "died": True, "was_traded": False},  # fuera de posicion
            {"kills": 1, "died": True, "was_traded": False},  # murio peleando
            {"kills": 0, "died": True, "was_traded": True},  # lo vengaron
            {"kills": 0, "died": False},  # sobrevivio
        )
        for n, caso in enumerate(casos):
            make_round_player(make_round(match, n), **caso)
        overall = self.client.get("/api/overview/").json()["overall"]
        self.assertEqual(overall["caught_out_rounds"], 1)
        self.assertEqual(overall["caught_out_pct"], 25.0)

    def test_fuera_de_posicion_sale_en_el_csv(self):
        zona(4, 2)
        resp = self.client.get("/api/export/?table=sites")
        self.assertEqual(resp.status_code, 200)
        cabecera = resp.content.decode("utf-8-sig").splitlines()[0].split(",")
        self.assertIn("caught_out_pct", cabecera)
        self.assertIn("caught_out_rounds", cabecera)


class PosicionPorZonaTests(TestCase):
    def test_la_zona_se_compara_contra_el_resto_y_no_contra_el_total(self):
        zona(10, 8, site=SITIO_A, index=0)
        zona(10, 2, site=SITIO_B, index=1)
        datos = agg.positioning()
        a = fila(datos["sites"], "site", SITIO_A)
        self.assertEqual(a["caught_out_pct"], 80.0)
        self.assertEqual(a["rest_rounds"], 10)
        self.assertEqual(a["rest_caught_out_pct"], 20.0)  # no 50.0, el total
        self.assertEqual(a["caught_out_delta"], 60.0)

    def test_el_spawn_se_compara_contra_el_resto_del_ataque(self):
        zona(10, 8, side="Attack", spawn="Warehouse", index=0)
        zona(10, 2, side="Attack", spawn="Construction Site", index=1)
        sin_defensa = fila(agg.positioning()["spawns"], "spawn", "Warehouse")
        # Defensa toda fuera de posicion: no tiene que mover el resto del spawn.
        zona(30, 30, side="Defense", spawn="", index=2)
        con_defensa = fila(agg.positioning()["spawns"], "spawn", "Warehouse")
        self.assertEqual(sin_defensa["rest_caught_out_pct"], 20.0)
        self.assertEqual(con_defensa["rest_caught_out_pct"], 20.0)
        self.assertEqual(con_defensa["rest_rounds"], 10)

    def test_una_diferencia_dentro_del_margen_es_ruido(self):
        zona(10, 6, site=SITIO_A, index=0)
        zona(10, 4, site=SITIO_B, index=1)
        a = fila(agg.positioning()["sites"], "site", SITIO_A)
        # Proporcion combinada 10/20: se = sqrt(.5*.5*(1/10 + 1/10)) = 22.4 puntos.
        se = round(math.sqrt(0.5 * 0.5 * (1 / 10 + 1 / 10)) * 100, 1)
        self.assertEqual(a["margin"], round(2 * se, 1))
        self.assertEqual(a["margin"], 44.8)
        self.assertEqual(a["caught_out_delta"], 20.0)
        self.assertEqual(a["verdict"], "ruido")

    def test_dormidero_y_solido_segun_el_signo(self):
        zona(20, 16, site=SITIO_A, index=0)
        zona(20, 4, site=SITIO_B, index=1)
        sitios = agg.positioning()["sites"]
        a = fila(sitios, "site", SITIO_A)
        b = fila(sitios, "site", SITIO_B)
        self.assertEqual(a["margin"], 31.6)  # 2 x sqrt(.5*.5*(1/20 + 1/20))
        self.assertEqual(a["verdict"], "dormidero")
        self.assertEqual(b["verdict"], "solido")
        # Mayor diferencia primero.
        self.assertEqual([f["site"] for f in sitios], [SITIO_A, SITIO_B])

    def test_una_zona_chica_en_cero_no_tiene_veredicto_por_azar(self):
        # 0 de 5 contra un resto del 30 %: pasa por azar 1 de cada 6 veces.
        # Con la varianza de Wald el margen seria 6.5 y saldria "solido".
        zona(5, 0, site=SITIO_A, index=0)
        zona(200, 60, site=SITIO_B, index=1)
        a = fila(agg.positioning()["sites"], "site", SITIO_A)
        self.assertEqual(a["caught_out_delta"], -30.0)
        self.assertEqual(a["margin"], 41.2)
        self.assertEqual(a["verdict"], "ruido")

    def test_con_una_sola_zona_el_veredicto_es_ruido(self):
        zona(20, 20, site=SITIO_A)
        a = fila(agg.positioning()["sites"], "site", SITIO_A)
        self.assertEqual(a["rest_rounds"], 0)
        self.assertIsNone(a["rest_caught_out_pct"])
        self.assertIsNone(a["margin"])
        self.assertEqual(a["verdict"], "ruido")

    def test_la_vista_respeta_min_rounds(self):
        zona(10, 5, site=SITIO_A, index=0)
        zona(14, 5, site=SITIO_B, index=1)
        datos = self.client.get("/api/positioning/?min_rounds=12").json()
        self.assertEqual([f["site"] for f in datos["sites"]], [SITIO_B])
        self.assertEqual(datos["min_rounds"], 12)

    def test_una_zona_bajo_el_minimo_no_sale(self):
        zona(10, 5, site=SITIO_A, index=0)
        zona(4, 4, site=SITIO_B, index=1)
        sitios = agg.positioning(min_rounds=5)["sites"]
        self.assertIsNone(fila(sitios, "site", SITIO_B))
        # Pero sus rondas siguen en el resto de las demas zonas.
        self.assertEqual(fila(sitios, "site", SITIO_A)["rest_rounds"], 4)

    def test_el_filtro_de_lado_deja_el_resto_del_mismo_lado(self):
        zona(10, 8, site=SITIO_A, side="Defense", index=0)
        zona(10, 2, site=SITIO_B, side="Defense", index=1)
        zona(10, 10, site=SITIO_B, side="Attack", index=2)
        resp = self.client.get("/api/positioning/?side=Defense")
        self.assertEqual(resp.status_code, 200)
        a = fila(resp.json()["sites"], "site", SITIO_A)
        self.assertEqual(a["rest_rounds"], 10)
        self.assertEqual(a["rest_caught_out_pct"], 20.0)
        self.assertEqual(resp.json()["spawns"], [])

    def test_sin_rondas_no_da_500(self):
        resp = self.client.get("/api/positioning/")
        self.assertEqual(resp.status_code, 200)
        datos = resp.json()
        self.assertEqual(datos["sites"], [])
        self.assertEqual(datos["spawns"], [])
        self.assertIsNone(datos["overall"]["caught_out_pct"])
        self.assertEqual(datos["min_rounds"], agg.POSICION_MIN_RONDAS)
        self.assertEqual(datos["bands"], agg.POSICION_BANDAS)


class SenalesDeZonaTests(TestCase):
    def test_zona_dormidero_sale_con_muestra(self):
        zona(20, 16, site=SITIO_A, index=0)
        zona(20, 4, site=SITIO_B, index=1)
        insight = find(build_insights(), "zona-dormidero")
        self.assertIsNotNone(insight)
        self.assertEqual(
            insight["title"],
            f"En {SITIO_A} (Club House) te agarran fuera de posición el 80% de las rondas",
        )
        self.assertEqual(insight["severity"], "media")
        self.assertEqual(insight["value"], 80.0)
        self.assertEqual(insight["baseline"], 20.0)
        self.assertEqual(insight["sample"], 20)
        self.assertIn("del resto de tu historial", insight["detail"])

    def test_zona_solida_sale_con_muestra(self):
        zona(20, 16, site=SITIO_A, index=0)
        zona(20, 4, site=SITIO_B, index=1)
        insight = find(build_insights(), "zona-solida")
        self.assertIsNotNone(insight)
        self.assertEqual(insight["title"], f"En {SITIO_B} (Club House) te sostienes")
        self.assertEqual(insight["severity"], "positivo")
        self.assertIn("bajo el resto de tu historial", insight["detail"])
        self.assertEqual(insight["filters"], {"map": "club-house", "site": SITIO_B})

    def test_un_spawn_dormidero_habla_del_resto_del_ataque(self):
        zona(20, 16, site=SITIO_A, spawn="Warehouse", index=0)
        zona(20, 4, site=SITIO_A, spawn="Construction Site", index=1)
        payload = build_insights()
        insight = find(payload, "zona-dormidero")
        self.assertEqual(
            insight["title"],
            "En el spawn Warehouse (Club House) te agarran fuera de posición el 80% de las rondas",
        )
        self.assertIn("del resto de tu ataque", insight["detail"])
        self.assertEqual(insight["scope"], "Club House · Warehouse (ataque)")
        # no hay filtro de spawn: el enlace abre el mapa en ataque
        self.assertEqual(insight["filters"], {"map": "club-house", "side": "Attack"})

    def test_sin_muestra_no_hay_senal_de_zona(self):
        zona(7, 7, site=SITIO_A, spawn="Warehouse", index=0)
        zona(7, 0, site=SITIO_B, spawn="Construction Site", index=1)
        zona(7, 0, site="C Lab", spawn="Shooting Range", index=2)
        payload = build_insights()
        self.assertNotIn("sin-datos", {i["key"] for i in payload["insights"]})
        self.assertIsNone(find(payload, "zona-dormidero"))
        self.assertIsNone(find(payload, "zona-solida"))

    def test_una_zona_en_ruido_no_da_senal(self):
        zona(12, 7, site=SITIO_A, index=0)
        zona(12, 5, site=SITIO_B, index=1)
        payload = build_insights()
        self.assertIsNone(find(payload, "zona-dormidero"))
        self.assertIsNone(find(payload, "zona-solida"))
