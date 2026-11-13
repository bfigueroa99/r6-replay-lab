"""Una request con un Host que no es el de la app recibe un 400 plano.

El caso real es DNS rebinding: una pagina de `atacante.example` reapunta su
nombre a 127.0.0.1 y le habla a la app con `Host: atacante.example:8000`. Para
el navegador esa respuesta es del mismo origen que la pagina, asi que la puede
leer entera. Django ya rechaza el Host, pero con `DJANGO_DEBUG=true` (el
default al correr desde el repo) el rechazo era la pagina tecnica, con los
settings y el entorno del proceso adentro.
"""

from __future__ import annotations

from django.test import TestCase, override_settings

AJENO = "atacante.example:8000"
RUTAS = ("/api/health/", "/api/settings/", "/", "/partidas/1", "/admin/")


@override_settings(DEBUG=True, UBI_EMAIL="cuenta-secundaria@example.com")
class HostAjenoConDebugTests(TestCase):
    def test_un_host_ajeno_recibe_un_400_plano_y_no_la_pagina_de_debug(self):
        for ruta in RUTAS:
            with self.subTest(ruta=ruta):
                response = self.client.get(ruta, HTTP_HOST=AJENO)
                self.assertEqual(response.status_code, 400)
                cuerpo = response.content.decode()
                self.assertTrue(response["Content-Type"].startswith("text/plain"))
                # la pagina tecnica pesa 60 KB y trae todo esto
                self.assertLess(len(cuerpo), 200)
                for filtrado in (
                    "cuenta-secundaria@example.com", "DisallowedHost", "REPLAY_DIR",
                    "SQLITE", "Traceback",
                ):
                    self.assertNotIn(filtrado, cuerpo)

    def test_un_post_con_host_ajeno_tampoco_llega_a_la_vista(self):
        response = self.client.post(
            "/api/backup/", data="{}", content_type="application/json", HTTP_HOST=AJENO
        )
        self.assertEqual(response.status_code, 400)
        self.assertNotIn("DisallowedHost", response.content.decode())

    def test_un_host_mal_formado_tambien_es_un_400_plano(self):
        response = self.client.get("/api/health/", HTTP_HOST="no es un host")
        self.assertEqual(response.status_code, 400)
        self.assertLess(len(response.content), 200)

    def test_los_hosts_de_la_app_siguen_respondiendo(self):
        for host in ("127.0.0.1:8000", "localhost:8000", "127.0.0.1", "localhost"):
            with self.subTest(host=host):
                response = self.client.get("/api/health/", HTTP_HOST=host)
                self.assertEqual(response.status_code, 200)
                self.assertTrue(response.json()["ok"])


class HostAjenoSinDebugTests(TestCase):
    def test_sin_debug_el_400_es_el_mismo(self):
        response = self.client.get("/api/health/", HTTP_HOST=AJENO)
        self.assertEqual(response.status_code, 400)
        self.assertTrue(response["Content-Type"].startswith("text/plain"))
        self.assertLess(len(response.content), 200)
