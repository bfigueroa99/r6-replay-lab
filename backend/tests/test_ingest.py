"""Tests de la importacion: deteccion de carpetas, idempotencia e integracion."""

from __future__ import annotations

import os
import time
from pathlib import Path

from django.test import TestCase

from replays.ingest import (
    find_match_folders,
    folder_is_settled,
    import_match_folder,
    scan_and_import,
)
from replays.models import Event, ImportLog, Match, Player, Round, RoundPlayer


class FolderDetectionTests(TestCase):
    def setUp(self):
        import tempfile

        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.addCleanup(self.tmp.cleanup)

    def _folder(self, name: str, files: list[str]) -> Path:
        folder = self.root / name
        folder.mkdir()
        for f in files:
            (folder / f).write_bytes(b"x")
        return folder

    def test_ignora_carpetas_sin_rec(self):
        self._folder("Match-vacia", [])
        self._folder("Match-buena", ["a-R01.rec"])
        self._folder("otra-cosa", ["a-R01.rec"])
        names = [f.name for f in find_match_folders(self.root)]
        self.assertEqual(names, ["Match-buena"])

    def test_carpeta_inexistente_devuelve_vacio(self):
        self.assertEqual(find_match_folders(self.root / "nope"), [])

    def test_partida_recien_escrita_no_esta_lista(self):
        folder = self._folder("Match-fresca", ["a-R01.rec"])
        self.assertFalse(folder_is_settled(folder, quiet_seconds=300))
        self.assertTrue(folder_is_settled(folder, quiet_seconds=0))

    def test_partida_vieja_esta_lista(self):
        folder = self._folder("Match-vieja", ["a-R01.rec"])
        old = time.time() - 600
        os.utime(folder / "a-R01.rec", (old, old))
        self.assertTrue(folder_is_settled(folder, quiet_seconds=60))

    def test_error_de_parseo_queda_registrado(self):
        folder = self._folder("Match-corrupta", ["a-R01.rec"])
        result = import_match_folder(folder)
        self.assertFalse(result.ok)
        self.assertEqual(Match.objects.count(), 0)
        entry = ImportLog.objects.first()
        self.assertFalse(entry.ok)
        self.assertIn("InvalidFile", entry.message)


class RealImportTests(TestCase):
    """Integracion completa. Corre si R6_TEST_REPLAY_DIR apunta a un MatchReplay."""

    def setUp(self):
        raw = os.environ.get("R6_TEST_REPLAY_DIR", "")
        if not raw or not Path(raw).exists():
            self.skipTest("define R6_TEST_REPLAY_DIR con una carpeta de replays")
        self.root = Path(raw)
        self.folders = find_match_folders(self.root)
        if not self.folders:
            self.skipTest("la carpeta no tiene partidas")

    def test_importa_y_es_idempotente(self):
        folder = self.folders[0]
        first = import_match_folder(folder)
        self.assertTrue(first.ok, first.message)
        self.assertGreater(first.rounds, 0)

        matches = Match.objects.count()
        rounds = Round.objects.count()
        self.assertEqual(rounds, first.rounds)

        second = import_match_folder(folder)
        self.assertTrue(second.ok)
        self.assertEqual(Match.objects.count(), matches)
        self.assertEqual(Round.objects.count(), rounds)

    def test_datos_coherentes(self):
        import_match_folder(self.folders[0])
        match = Match.objects.first()
        self.assertTrue(match.map_name)
        self.assertTrue(match.match_id)
        self.assertEqual(match.rounds_count, match.rounds.count())

        me = Player.objects.filter(is_me=True)
        self.assertEqual(me.count(), 1)

        for rnd in match.rounds.all():
            self.assertIn(rnd.my_side, ("Attack", "Defense"))
            mine = rnd.players.filter(is_me=True)
            self.assertEqual(mine.count(), 1, f"ronda {rnd.number}")
            self.assertEqual(mine.first().side, rnd.my_side)
            # los dos equipos tienen roles opuestos
            roles = {t["role"] for t in rnd.teams}
            self.assertEqual(roles, {"Attack", "Defense"})

        # cada kill del feed tiene que tener victima muerta en las stats
        for event in Event.objects.filter(kind="Kill"):
            victim = RoundPlayer.objects.filter(
                round=event.round, username=event.target_name
            ).first()
            if victim:
                self.assertTrue(victim.died, f"{event.target_name} deberia estar muerto")

    def test_scan_salta_lo_ya_importado(self):
        scan_and_import(self.root, quiet_seconds=0, limit=1)
        imported = Match.objects.count()
        self.assertGreaterEqual(imported, 1)
        again = scan_and_import(self.root, quiet_seconds=0, limit=1)
        self.assertEqual(Match.objects.count(), imported + len([r for r in again if r.created]))
