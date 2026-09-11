"""Tests de la importacion en segundo plano y su progreso."""

from __future__ import annotations

import shutil
import tempfile
import time
from pathlib import Path

from django.test import TestCase

from replays import ingest
from replays.models import Match

from .factories import make_match


class CarpetasPendientesTests(TestCase):
    """El total se calcula antes de empezar: sin eso no hay "3 de 12"."""

    def setUp(self):
        self.raiz = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.raiz, True)

    def _carpeta(self, nombre: str) -> Path:
        sub = self.raiz / nombre
        sub.mkdir()
        (sub / "ronda.rec").write_bytes(b"x")
        return sub

    def test_carpeta_inexistente(self):
        self.assertEqual(ingest.pending_folders("/ruta/que/no/existe"), [])

    def test_estan_todas_las_que_faltan(self):
        self._carpeta("Match-a")
        self._carpeta("Match-b")
        pendientes = ingest.pending_folders(self.raiz, quiet_seconds=0)
        self.assertEqual({p.name for p in pendientes}, {"Match-a", "Match-b"})

    def test_una_ya_importada_no_esta_pendiente(self):
        self._carpeta("Match-a")
        self._carpeta("Match-b")
        match = make_match(index=0)
        Match.objects.filter(pk=match.pk).update(folder="Match-a")

        pendientes = ingest.pending_folders(self.raiz, quiet_seconds=0)
        self.assertEqual({p.name for p in pendientes}, {"Match-b"})

    def test_con_force_vuelven_todas(self):
        self._carpeta("Match-a")
        match = make_match(index=0)
        Match.objects.filter(pk=match.pk).update(folder="Match-a")
        self.assertEqual(len(ingest.pending_folders(self.raiz, quiet_seconds=0, force=True)), 1)

    def test_una_partida_recien_escrita_no_entra(self):
        """Puede estar jugandose todavia."""
        self._carpeta("Match-a")
        self.assertEqual(ingest.pending_folders(self.raiz, quiet_seconds=3600), [])

    def test_el_limite_corta(self):
        for nombre in ("Match-a", "Match-b", "Match-c"):
            self._carpeta(nombre)
        self.assertEqual(len(ingest.pending_folders(self.raiz, quiet_seconds=0, limit=2)), 2)


class ProgresoTests(TestCase):
    """`run_import_job` es sincrono a proposito: en los tests un hilo abre otra
    conexion y no ve los datos de la transaccion."""

    def test_sin_nada_que_importar_termina_enseguida(self):
        job = ingest.run_import_job([])
        self.assertFalse(job.running)
        self.assertEqual(job.total, 0)
        self.assertEqual(job.as_dict()["count"], 0)

    def test_reporta_carpeta_por_carpeta(self):
        carpeta = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, carpeta, True)
        for nombre in ("Match-a", "Match-b"):
            sub = carpeta / nombre
            sub.mkdir()
            (sub / "r.rec").write_bytes(b"no soy un replay")

        vistos = []
        real = ingest.import_folders

        def espia(folders, **kwargs):
            original = kwargs.pop("on_progress", None)

            def hook(done, total, folder):
                vistos.append((done, total, folder))
                if original:
                    original(done, total, folder)

            return real(folders, on_progress=hook, **kwargs)

        ingest.import_folders = espia
        self.addCleanup(setattr, ingest, "import_folders", real)
        job = ingest.run_import_job(ingest.pending_folders(carpeta, quiet_seconds=0))

        self.assertEqual([v[0] for v in vistos], [0, 1, 2])
        self.assertEqual([v[1] for v in vistos], [2, 2, 2])
        self.assertEqual(vistos[0][2], "Match-a")
        # los .rec falsos fallan al parsear, pero el trabajo igual termina
        self.assertFalse(job.running)
        self.assertEqual(job.as_dict()["errors"], 2)

    def test_un_error_inesperado_queda_en_el_estado(self):
        real = ingest.import_folders

        def explota(*args, **kwargs):
            raise RuntimeError("se cayo el disco")

        ingest.import_folders = explota
        self.addCleanup(setattr, ingest, "import_folders", real)

        job = ingest.run_import_job([Path("/lo/que/sea")])
        self.assertFalse(job.running)
        self.assertIn("se cayo el disco", job.error)


class HiloTests(TestCase):
    def test_el_post_ya_trae_el_total(self):
        """El total se calcula antes de lanzar el hilo, para el "3 de 12"."""
        raiz = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, raiz, True)
        for nombre in ("Match-a", "Match-b"):
            sub = raiz / nombre
            sub.mkdir()
            (sub / "r.rec").write_bytes(b"x")

        with self.settings(REPLAY_DIR=str(raiz), IMPORT_QUIET_SECONDS=0):
            data = self.client.post("/api/import/").json()
        self.assertEqual(data["total"], 2)

        for _ in range(200):
            if not ingest.import_job().running:
                break
            time.sleep(0.02)

    def test_el_post_vuelve_enseguida(self):
        with self.settings(REPLAY_DIR="/ruta/que/no/existe"):
            respuesta = self.client.post("/api/import/")
        self.assertEqual(respuesta.status_code, 200)
        self.assertIn("running", respuesta.json())

        # el hilo no tiene nada que hacer, pero se le da un momento
        for _ in range(50):
            if not ingest.import_job().running:
                break
            time.sleep(0.02)
        self.assertFalse(ingest.import_job().running)

    def test_no_lanza_dos_a_la_vez(self):
        ingest._job = ingest.ImportJob(running=True, total=7, done=3, current="Match-x")
        self.addCleanup(setattr, ingest, "_job", ingest.ImportJob())

        with self.settings(REPLAY_DIR="/ruta/que/no/existe"):
            data = self.client.post("/api/import/").json()
        self.assertTrue(data["running"])
        self.assertEqual(data["total"], 7)
        self.assertEqual(data["current"], "Match-x")

    def test_endpoint_de_progreso(self):
        ingest._job = ingest.ImportJob(running=True, total=12, done=2, current="Match-y")
        self.addCleanup(setattr, ingest, "_job", ingest.ImportJob())

        data = self.client.get("/api/import/progress/").json()
        self.assertEqual((data["done"], data["total"], data["current"]), (2, 12, "Match-y"))

    def test_el_progreso_no_acepta_post(self):
        self.assertEqual(self.client.post("/api/import/progress/").status_code, 405)
