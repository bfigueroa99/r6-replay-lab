"""Tests del export a CSV."""

from __future__ import annotations

import csv
from io import StringIO

from django.test import TestCase

from replays import export

from .factories import make_match, make_round, make_round_player


def leer(texto: str, delimiter: str = ",") -> list[dict]:
    return list(csv.DictReader(StringIO(texto), delimiter=delimiter))


class CsvTests(TestCase):
    def test_cabecera_y_filas(self):
        texto = export.to_csv([{"mapa": "Bank", "rondas": 5}, {"mapa": "Villa", "rondas": 2}])
        filas = leer(texto)
        self.assertEqual([f["mapa"] for f in filas], ["Bank", "Villa"])
        self.assertEqual(filas[0]["rondas"], "5")

    def test_columnas_son_la_union_en_orden_de_aparicion(self):
        texto = export.to_csv([{"a": 1}, {"a": 2, "b": 3}])
        self.assertEqual(texto.splitlines()[0], "a,b")
        self.assertEqual(leer(texto)[0]["b"], "")

    def test_valores_especiales(self):
        texto = export.to_csv([{"nulo": None, "si": True, "no": False, "lista": ["a", "b"]}])
        fila = leer(texto)[0]
        self.assertEqual(fila["nulo"], "")
        self.assertEqual(fila["si"], "si")
        self.assertEqual(fila["no"], "no")
        self.assertEqual(fila["lista"], "a / b")

    def test_escapa_lo_que_rompe_el_formato(self):
        texto = export.to_csv([{"sitio": '2F Bathroom, 2F "Office"'}])
        self.assertEqual(leer(texto)[0]["sitio"], '2F Bathroom, 2F "Office"')

    def test_sin_filas_devuelve_algo_valido(self):
        self.assertEqual(export.to_csv([]).strip(), "")

    def test_punto_y_coma(self):
        texto = export.to_csv([{"a": 1, "b": 2}], delimiter=";")
        self.assertEqual(texto.splitlines()[0], "a;b")


class EndpointTests(TestCase):
    def setUp(self):
        match = make_match(map_name="Bank", index=0)
        for n in range(4):
            make_round_player(make_round(match, n, side="Attack"), operator="Zofia")

    def _csv(self, url: str) -> list[dict]:
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertIn("text/csv", response["Content-Type"])
        return leer(response.content.decode("utf-8"))

    def test_lista_las_tablas_disponibles(self):
        data = self.client.get("/api/export/").json()
        self.assertIn("maps", data["tables"])
        self.assertIn("sessions", data["tables"])

    def test_todas_las_tablas_responden(self):
        for nombre in export.table_names():
            with self.subTest(tabla=nombre):
                response = self.client.get(f"/api/export/?table={nombre}")
                self.assertEqual(response.status_code, 200)

    def test_exporta_mapas(self):
        filas = self._csv("/api/export/?table=maps")
        self.assertEqual(filas[0]["map"], "Bank")
        self.assertEqual(filas[0]["rounds"], "4")

    def test_respeta_los_filtros(self):
        self.assertEqual(len(self._csv("/api/export/?table=maps&side=Attack")), 1)
        self.assertEqual(len(self._csv("/api/export/?table=maps&side=Defense")), 0)

    def test_nombre_de_archivo_descargable(self):
        response = self.client.get("/api/export/?table=operators")
        self.assertIn("attachment", response["Content-Disposition"])
        self.assertIn("r6-operadores-", response["Content-Disposition"])

    def test_separador_alternativo(self):
        response = self.client.get("/api/export/?table=maps&sep=;")
        self.assertIn("map;", response.content.decode("utf-8").splitlines()[0])

    def test_tabla_desconocida_da_400_y_sugiere(self):
        response = self.client.get("/api/export/?table=noexiste")
        self.assertEqual(response.status_code, 400)
        self.assertIn("maps", response.json()["tables"])

    def test_base_vacia_no_revienta(self):
        from replays.models import Match

        Match.objects.all().delete()
        for nombre in export.table_names():
            with self.subTest(tabla=nombre):
                self.assertEqual(self.client.get(f"/api/export/?table={nombre}").status_code, 200)
