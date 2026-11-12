"""Tests del atrapa-todo que sirve el build de React (`config.urls.spa`)."""

from __future__ import annotations

import os
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

    def test_los_nombres_que_genera_un_build_se_siguen_sirviendo(self):
        # ata el filtro de forma: endurecerlo no puede dejar afuera estos nombres
        from config import urls

        (urls.DIST / "@vite").mkdir()
        for nombre in ("assets/index-Ab_C1.js", "@vite/x.js", "a b.png", "favicon.ico"):
            (urls.DIST / nombre).write_text(nombre, encoding="utf-8")
        for url, nombre in (
            ("/assets/index-Ab_C1.js", "assets/index-Ab_C1.js"),
            ("/@vite/x.js", "@vite/x.js"),
            ("/a%20b.png", "a b.png"),
            ("/favicon.ico", "favicon.ico"),
        ):
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertEqual(response.status_code, 200)
                self.assertEqual(self.contenido(response), nombre.encode())

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
        # el ".." se descarta por su forma, antes de tocar el disco: sin esa
        # afirmacion el test pasaba tambien con el chequeo de contencion borrado
        tocadas = self.espiar_disco()
        response = self.client.get("/..%2F..%2Fdist-viejo%2Fsecreto.txt")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.contenido(response), b"<html>la app</html>")
        self.assertEqual(tocadas, [])

    def espiar_disco(self):
        """Anota cada ruta sobre la que se llama resolve o is_file, sin cambiar su resultado."""
        tocadas = []
        for nombre in ("resolve", "is_file"):
            original = getattr(Path, nombre)

            def espia(ruta, *a, _orig=original, **kw):
                tocadas.append(str(ruta))
                return _orig(ruta, *a, **kw)

            parche = mock.patch.object(Path, nombre, autospec=True, side_effect=espia)
            parche.start()
            self.addCleanup(parche.stop)
        return tocadas

    def test_una_ruta_que_no_puede_ser_del_build_no_toca_el_disco(self):
        # en Windows `\\host\s\x` o `//host/s/x` reemplazan a DIST en el join y
        # resolve() abriria la ruta UNC (SMB, hash NTLM) antes del chequeo de
        # contencion: estas rutas se descartan por su forma
        casos = {
            "barra invertida UNC": {"path": "/%5C%5Chost%5Cs%5Cx"},
            "barra invertida suelta": {"path": "/assets%5Capp.js"},
            # el cliente de prueba se come la doble barra al parsear la URL:
            # PATH_INFO forzado para que la vista reciba `//host/s/x`
            "doble barra": {"PATH_INFO": "///host/s/x"},
            "doble barra sin host": {"PATH_INFO": "//host/s/x"},
            "unidad con barra invertida": {"path": "/C:%5Cx"},
            "unidad con barra": {"path": "/C:/x"},
            "punto punto escapado": {"path": "/..%2Fdist-viejo%2Fsecreto.txt"},
            # Win32 recorta el punto y el espacio final: ".. " termina siendo ".."
            "punto punto con espacio": {"path": "/..%20%2Fdist-viejo%2Fsecreto.txt"},
            "punto final": {"path": "/assets/app.js."},
        }
        tocadas = self.espiar_disco()
        for nombre, caso in casos.items():
            with self.subTest(caso=nombre):
                tocadas.clear()
                extra = {"PATH_INFO": caso["PATH_INFO"]} if "PATH_INFO" in caso else {}
                response = self.client.get(caso.get("path", "/x"), **extra)
                self.assertEqual(response.status_code, 200)
                self.assertEqual(self.contenido(response), b"<html>la app</html>")
                self.assertEqual(tocadas, [])

    def test_un_bucle_de_symlinks_devuelve_el_index(self):
        # resolve() lanza RuntimeError en Python 3.11 y 3.12; desde 3.13 no
        # lanza y is_file da False: en ningun caso puede terminar en un 500
        from config import urls

        try:
            os.symlink("b", urls.DIST / "a")
            os.symlink("a", urls.DIST / "b")
        except OSError:
            # Windows sin modo de desarrollador no deja crear symlinks
            self.skipTest("el sistema no permite crear symlinks")
        response = self.client.get("/a")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.contenido(response), b"<html>la app</html>")
