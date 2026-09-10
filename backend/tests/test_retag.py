"""Tests del re-etiquetado de IDs sin reparsear los replays."""

from __future__ import annotations

import json
import os
import tempfile
from io import StringIO
from pathlib import Path

from django.core.management import call_command
from django.test import TestCase

from pydissect import overrides
from replays.models import Match, RoundPlayer
from replays.retag import retag

from .factories import make_match, make_round, make_round_player

MAPA_NUEVO = 398899676157
OPERADOR_NUEVO = 444310693746


class OverridesTestCase(TestCase):
    """Base que apunta PYDISSECT_OVERRIDES a un JSON temporal."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.path = Path(self._tmp.name) / "overrides.json"

        previo = os.environ.get(overrides.ENV_VAR)
        os.environ[overrides.ENV_VAR] = str(self.path)
        self.addCleanup(self._restaurar_env, previo)
        self.addCleanup(overrides.load, True)
        overrides.load(force=True)

    def _restaurar_env(self, previo: str | None) -> None:
        if previo is None:
            os.environ.pop(overrides.ENV_VAR, None)
        else:
            os.environ[overrides.ENV_VAR] = previo

    def escribir_overrides(self, maps: dict | None = None, operators: dict | None = None) -> None:
        self.path.write_text(
            json.dumps({"maps": maps or {}, "operators": operators or {}}),
            encoding="utf-8",
        )


class RetagTests(OverridesTestCase):
    def setUp(self):
        super().setUp()
        self.match = make_match(
            map_name=f"Unknown({MAPA_NUEVO})", index=0, map_id=MAPA_NUEVO
        )
        self.match.map_slug = f"unknown-{MAPA_NUEVO}"
        self.match.save()
        rnd = make_round(self.match, 0)
        make_round_player(
            rnd, operator=f"Unknown({OPERADOR_NUEVO})", operator_id=OPERADOR_NUEVO
        )

    def test_sin_overrides_no_cambia_nada(self):
        result = retag()
        self.assertFalse(result.changed)
        self.assertEqual(Match.objects.get().map_name, f"Unknown({MAPA_NUEVO})")

    def test_aplica_el_nombre_y_recalcula_el_slug(self):
        self.escribir_overrides(maps={str(MAPA_NUEVO): "Nighthaven Labs"})
        result = retag()

        self.assertEqual(result.matches, 1)
        match = Match.objects.get()
        self.assertEqual(match.map_name, "Nighthaven Labs")
        self.assertEqual(match.map_slug, "nighthaven-labs")

    def test_aplica_el_nombre_del_operador(self):
        self.escribir_overrides(operators={str(OPERADOR_NUEVO): "Denari"})
        result = retag()

        self.assertEqual(result.round_players, 1)
        self.assertEqual(RoundPlayer.objects.get().operator, "Denari")

    def test_es_idempotente(self):
        self.escribir_overrides(
            maps={str(MAPA_NUEVO): "Nighthaven Labs"},
            operators={str(OPERADOR_NUEVO): "Denari"},
        )
        self.assertTrue(retag().changed)
        self.assertFalse(retag().changed)

    def test_no_degrada_una_etiqueta_buena_a_unknown(self):
        """Si el override desaparece, lo ya etiquetado conserva su nombre."""
        self.escribir_overrides(maps={str(MAPA_NUEVO): "Nighthaven Labs"})
        retag()
        self.escribir_overrides()  # se vacia el archivo

        self.assertFalse(retag().changed)
        self.assertEqual(Match.objects.get().map_name, "Nighthaven Labs")

    def test_dry_run_no_escribe(self):
        self.escribir_overrides(maps={str(MAPA_NUEVO): "Nighthaven Labs"})
        result = retag(dry_run=True)

        self.assertEqual(result.matches, 1)
        self.assertEqual(Match.objects.get().map_name, f"Unknown({MAPA_NUEVO})")

    def test_ignora_lo_que_no_tiene_id(self):
        """Las partidas viejas sin map_id no se pueden resolver, y no revientan."""
        make_match(map_name="Club House", index=1)
        self.escribir_overrides(maps={str(MAPA_NUEVO): "Nighthaven Labs"})
        retag()
        self.assertEqual(Match.objects.get(map_id=0).map_name, "Club House")


class RetagCommandTests(OverridesTestCase):
    def setUp(self):
        super().setUp()
        match = make_match(map_name=f"Unknown({MAPA_NUEVO})", index=0, map_id=MAPA_NUEVO)
        make_round_player(make_round(match, 0))

    def _correr(self, *args) -> str:
        out = StringIO()
        call_command("retag", *args, stdout=out)
        return out.getvalue()

    def test_sin_cambios_lo_dice(self):
        self.assertIn("Nada que reetiquetar", self._correr())

    def test_reporta_el_cambio(self):
        self.escribir_overrides(maps={str(MAPA_NUEVO): "Nighthaven Labs"})
        salida = self._correr()
        self.assertIn(f"Unknown({MAPA_NUEVO}) -> Nighthaven Labs", salida)
        self.assertIn("Reetiquetadas 1 partidas", salida)

    def test_dry_run_avisa_que_no_toco_nada(self):
        self.escribir_overrides(maps={str(MAPA_NUEVO): "Nighthaven Labs"})
        self.assertIn("[dry-run]", self._correr("--dry-run"))
        self.assertEqual(Match.objects.get().map_name, f"Unknown({MAPA_NUEVO})")


class UnknownIdsCommandTests(OverridesTestCase):
    def setUp(self):
        super().setUp()
        match = make_match(map_name=f"Unknown({MAPA_NUEVO})", index=0, map_id=MAPA_NUEVO)
        rnd = make_round(match, 0, site="2F Dormitory, 2F Games Room")
        make_round_player(
            rnd, operator=f"Unknown({OPERADOR_NUEVO})", operator_id=OPERADOR_NUEVO
        )

    def test_write_usa_overrides_path_y_deja_las_entradas_listas(self):
        out = StringIO()
        with self.settings(OVERRIDES_PATH=self.path):
            call_command("unknown_ids", "--write", stdout=out)

        data = json.loads(self.path.read_text(encoding="utf-8"))
        self.assertEqual(data["maps"][str(MAPA_NUEVO)], "")
        self.assertEqual(data["operators"][str(OPERADOR_NUEVO)], "")
        self.assertIn("manage.py retag", out.getvalue())

    def test_muestra_los_sitios_que_delatan_el_mapa(self):
        out = StringIO()
        with self.settings(OVERRIDES_PATH=self.path):
            call_command("unknown_ids", stdout=out)
        self.assertIn("2F Dormitory, 2F Games Room", out.getvalue())
