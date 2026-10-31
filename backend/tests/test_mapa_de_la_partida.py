"""Partidas y el detalle de la partida dicen la version del mapa, igual que Mapas (ficha 71)."""

from __future__ import annotations

from django.db import connection
from django.test import TestCase
from django.test.utils import CaptureQueriesContext

from replays.analytics import aggregates as agg

from .factories import make_match, make_round, make_round_player

CONSULATE_Y7 = 2609221242
CONSULATE_Y10 = 418126004176
CONSULATE_SIN_SUFIJO = 379218689149
KANAL = 1460220617


def _partida(map_name: str, map_id: int, index: int):
    match = make_match(map_name=map_name, map_id=map_id, index=index)
    make_round_player(make_round(match, 0))
    return match


class MapaDeLaPartidaTests(TestCase):
    def setUp(self):
        self.y7 = _partida("Consulate", CONSULATE_Y7, 0)
        self.y10 = _partida("Consulate", CONSULATE_Y10, 1)
        self.kanal = _partida("Kanal", KANAL, 2)
        # seed_demo y las factories dejan map_id=0, que MAPS no conoce
        self.club = _partida("Club House", 0, 3)

    def _listado(self, query: str = "") -> dict[int, str]:
        data = self.client.get(f"/api/matches/{query}").json()
        return {m["id"]: m["map"] for m in data["matches"]}

    def _detalle(self, match) -> str:
        return self.client.get(f"/api/matches/{match.id}/").json()["match"]["map"]

    def test_el_listado_dice_la_version_del_mapa(self):
        self.assertEqual(
            self._listado(),
            {
                self.y7.id: "Consulate (Y7)",
                self.y10.id: "Consulate (Y10)",
                self.kanal.id: "Kanal",
                self.club.id: "Club House",
            },
        )

    def test_el_detalle_dice_la_version_del_mapa(self):
        self.assertEqual(self._detalle(self.y10), "Consulate (Y10)")
        self.assertEqual(self._detalle(self.kanal), "Kanal")
        self.assertEqual(self._detalle(self.club), "Club House")

    def test_listado_y_detalle_dicen_lo_mismo_que_mapas(self):
        _partida("Consulate", CONSULATE_SIN_SUFIJO, 4)
        # un rework que MAPS no conoce y que el usuario llamo "Consulate" en Datos
        _partida("Consulate", 999, 5)
        listado = self._listado()
        self.assertEqual(set(listado.values()), {r["map"] for r in agg.by_map()})
        self.assertIn("Consulate (id 999)", listado.values())
        for pk, etiqueta in listado.items():
            with self.subTest(pk=pk):
                detalle = self.client.get(f"/api/matches/{pk}/").json()["match"]["map"]
                self.assertEqual(detalle, etiqueta)

    def test_la_etiqueta_no_cambia_con_la_pagina(self):
        # el "(id N)" depende de las otras versiones del slug, aunque esten en otra pagina
        _partida("Consulate", CONSULATE_SIN_SUFIJO, 4)
        nuevo = _partida("Consulate", 999, 5)
        vistos = {}
        for offset in range(6):
            fila = self.client.get(f"/api/matches/?limit=1&offset={offset}").json()["matches"][0]
            vistos[fila["id"]] = fila["map"]
        self.assertEqual(vistos[nuevo.id], "Consulate (id 999)")
        self.assertEqual(vistos, self._listado())

    def test_el_filtro_del_listado_sigue_igual(self):
        self.assertEqual(
            self._listado("?map=consulate"),
            {self.y7.id: "Consulate (Y7)", self.y10.id: "Consulate (Y10)"},
        )
        self.assertEqual(self._listado(f"?map={CONSULATE_Y10}"), {self.y10.id: "Consulate (Y10)"})
        self.assertEqual(self._listado("?map=club-house"), {self.club.id: "Club House"})

    def _consultas_del_listado(self) -> int:
        with CaptureQueriesContext(connection) as consultas:
            self.assertEqual(self.client.get("/api/matches/").status_code, 200)
        return len(consultas)

    def test_el_listado_no_hace_una_consulta_por_partida(self):
        # se compara contra la misma base con el doble de partidas y no contra
        # un numero fijo: otra consulta por pagina no es el bug que se vigila
        antes = self._consultas_del_listado()
        for i, (nombre, map_id) in enumerate(
            [("Consulate", CONSULATE_Y7), ("Consulate", CONSULATE_Y10), ("Kanal", KANAL),
             ("Club House", 0)],
            start=10,
        ):
            _partida(nombre, map_id, i)
        self.assertEqual(self._consultas_del_listado(), antes)
