"""Tests del atrapa-todo que sirve el build de React (`config.urls.spa`)."""

from __future__ import annotations

import shutil
import tempfile
from pathlib import Path
from unittest import mock

from django.test import TestCase


class SpaTests(TestCase):
    """Un build falso en una carpeta temporal: no depende de que se haya corrido `npm run build`."""

    def setUp(self):
        raiz = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, raiz, ignore_errors=True)
        dist = raiz / "dist"
        (dist / "assets").mkdir(parents=True)
        (dist / "index.html").write_text("<html>la app</html>", encoding="utf-8")
        (dist / "assets" / "app.js").write_text("console.log(1)", encoding="utf-8")
        # carpeta hermana cuyo nombre empieza igual que dist: un chequeo por
        # prefijo de texto la tomaria por de adentro
        (raiz / "dist-viejo").mkdir()
        (raiz / "dist-viejo" / "secreto.txt").write_text("no se sirve", encoding="utf-8")
        for nombre, valor in (("DIST", dist), ("INDEX", dist / "index.html")):
            parche = mock.patch(f"config.urls.{nombre}", valor)
            parche.start()
            self.addCleanup(parche.stop)

    def contenido(self, response):
        return b"".join(response.streaming_content)

    def test_un_archivo_del_build_se_sirve_tal_cual(self):
        response = self.client.get("/assets/app.js")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.contenido(response), b"console.log(1)")

    def test_una_ruta_de_la_app_devuelve_el_index(self):
        response = self.client.get("/partidas/12")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.contenido(response), b"<html>la app</html>")

    def test_una_url_con_byte_nulo_devuelve_el_index_y_no_un_500(self):
        for url in ("/partidas/%00", "/assets/app%00.js", "/comparar/3/%00"):
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertEqual(response.status_code, 200)
                self.assertEqual(self.contenido(response), b"<html>la app</html>")

    def test_no_sirve_archivos_de_una_carpeta_hermana_con_el_mismo_prefijo(self):
        # %2F llega como "/" a la vista: el navegador no normaliza un ".." escapado
        response = self.client.get("/..%2Fdist-viejo%2Fsecreto.txt")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.contenido(response), b"<html>la app</html>")

    def test_no_sirve_archivos_fuera_del_build(self):
        # red de regresion: el prefijo viejo ya rechazaba este, el nuevo tambien
        response = self.client.get("/..%2F..%2Fdist-viejo%2Fsecreto.txt")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.contenido(response), b"<html>la app</html>")
