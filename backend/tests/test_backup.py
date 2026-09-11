"""Tests de la copia de seguridad de la base."""

from __future__ import annotations

import shutil
import sqlite3
import tempfile
import time
import warnings
from io import StringIO
from pathlib import Path

from django.core.management import call_command
from django.test import TestCase

from replays import backup as bk


def base_de_prueba(destino: Path, filas: int = 3) -> Path:
    """Un SQLite de verdad: la copia se valida abriendola, no mirando el tamano."""
    con = sqlite3.connect(destino)
    con.execute("CREATE TABLE partidas (id INTEGER PRIMARY KEY, mapa TEXT)")
    con.executemany(
        "INSERT INTO partidas (mapa) VALUES (?)", [(f"Mapa {i}",) for i in range(filas)]
    )
    con.commit()
    con.close()
    return destino


class BackupTests(TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.origen = base_de_prueba(self.tmp / "db.sqlite3")
        self.destino = self.tmp / "backups"

    def test_deja_una_copia_con_fecha(self):
        result = bk.backup_database(source=self.origen, dest_dir=self.destino)
        self.assertTrue(result.path.exists())
        self.assertTrue(result.path.name.startswith("db-"))
        self.assertTrue(result.path.name.endswith(".sqlite3"))
        self.assertGreater(result.size, 0)

    def test_la_copia_se_puede_abrir_y_tiene_los_datos(self):
        """Lo unico que importa de un backup es poder leerlo despues."""
        result = bk.backup_database(source=self.origen, dest_dir=self.destino)
        con = sqlite3.connect(result.path)
        self.addCleanup(con.close)
        self.assertEqual(con.execute("PRAGMA integrity_check").fetchone()[0], "ok")
        self.assertEqual(con.execute("SELECT count(*) FROM partidas").fetchone()[0], 3)

    def test_no_toca_la_base_original(self):
        bk.backup_database(source=self.origen, dest_dir=self.destino)
        con = sqlite3.connect(self.origen)
        self.addCleanup(con.close)
        self.assertEqual(con.execute("SELECT count(*) FROM partidas").fetchone()[0], 3)

    def test_crea_la_carpeta_si_no_existe(self):
        self.assertFalse(self.destino.exists())
        bk.backup_database(source=self.origen, dest_dir=self.destino)
        self.assertTrue(self.destino.is_dir())

    def test_dos_copias_seguidas_no_se_pisan(self):
        """El nombre llega al segundo: dos en el mismo segundo son dos archivos."""
        primera = bk.backup_database(source=self.origen, dest_dir=self.destino, keep=0)
        segunda = bk.backup_database(source=self.origen, dest_dir=self.destino, keep=0)
        self.assertNotEqual(primera.path, segunda.path)
        self.assertEqual(len(bk.existing_backups(self.destino)), 2)

    def test_sin_base_lo_dice_claro(self):
        with self.assertRaises(FileNotFoundError):
            bk.backup_database(source=self.tmp / "no-existe.sqlite3", dest_dir=self.destino)


class RotacionTests(TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.origen = base_de_prueba(self.tmp / "db.sqlite3")
        self.destino = self.tmp / "backups"

    def _copias(self, cuantas: int, keep: int) -> None:
        for _ in range(cuantas):
            bk.backup_database(source=self.origen, dest_dir=self.destino, keep=keep)
            time.sleep(0.01)  # para que las fechas de archivo no empaten

    def test_conserva_solo_las_ultimas(self):
        self._copias(5, keep=2)
        self.assertEqual(len(bk.existing_backups(self.destino)), 2)

    def test_borra_las_mas_viejas_y_no_las_nuevas(self):
        self._copias(3, keep=0)
        todas = bk.existing_backups(self.destino)
        mas_nueva = todas[0]

        bk.backup_database(source=self.origen, dest_dir=self.destino, keep=2)
        quedan = bk.existing_backups(self.destino)
        self.assertEqual(len(quedan), 2)
        self.assertIn(mas_nueva, quedan)  # la vieja se fue, la nueva sigue

    def test_keep_cero_las_deja_todas(self):
        self._copias(4, keep=0)
        self.assertEqual(len(bk.existing_backups(self.destino)), 4)

    def test_carpeta_vacia_no_revienta(self):
        self.assertEqual(bk.existing_backups(self.tmp / "no-existe"), [])


class ComandoTests(TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.origen = base_de_prueba(self.tmp / "db.sqlite3")
        self.destino = self.tmp / "backups"

        # Django avisa que pisar DATABASES es riesgoso, y en general lo es: aca
        # solo se lee la ruta como string y se abre con sqlite3 directo, sin
        # pasar por el ORM, asi que el aviso es ruido en la salida de la suite.
        silencio = warnings.catch_warnings()
        silencio.__enter__()
        self.addCleanup(silencio.__exit__, None, None, None)
        warnings.filterwarnings("ignore", message="Overriding setting DATABASES")

        # el comando lee la ruta de settings; aca se apunta a la base de prueba
        ctx = self.settings(DATABASES={"default": {"NAME": str(self.origen)}})
        ctx.enable()
        self.addCleanup(ctx.disable)

    def _correr(self, *args) -> str:
        out, err = StringIO(), StringIO()
        call_command("backup", *args, stdout=out, stderr=err)
        return out.getvalue() + err.getvalue()

    def test_hace_la_copia_y_la_reporta(self):
        salida = self._correr("--out", str(self.destino))
        self.assertIn("Copia lista", salida)
        self.assertIn("MB", salida)
        self.assertEqual(len(bk.existing_backups(self.destino)), 1)

    def test_lista_sin_copiar(self):
        self._correr("--out", str(self.destino))
        salida = self._correr("--out", str(self.destino), "--list")
        self.assertIn("1 copias", salida)
        self.assertEqual(len(bk.existing_backups(self.destino)), 1)

    def test_sin_copias_lo_dice(self):
        self.assertIn("No hay copias", self._correr("--out", str(self.destino), "--list"))

    def test_avisa_lo_que_borra(self):
        for _ in range(3):
            self._correr("--out", str(self.destino), "--keep", "0")
            time.sleep(0.01)
        salida = self._correr("--out", str(self.destino), "--keep", "1")
        self.assertIn("se borro la copia vieja", salida)
        self.assertEqual(len(bk.existing_backups(self.destino)), 1)

    def test_base_inexistente_va_a_stderr(self):
        with self.settings(DATABASES={"default": {"NAME": str(self.tmp / "no-existe.sqlite3")}}):
            salida = self._correr("--out", str(self.destino))
        self.assertIn("no existe la base", salida)
