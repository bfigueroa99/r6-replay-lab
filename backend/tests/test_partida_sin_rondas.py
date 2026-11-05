"""Detalle de una partida importada sin rondas (ficha 82)."""

from __future__ import annotations

import json
from pathlib import Path

from django.test import TestCase

from .factories import make_match

# El e2e sirve este archivo en lugar de la respuesta real para dibujar una
# partida sin rondas sobre los datos de seed_demo
SIN_RONDAS = Path(__file__).resolve().parents[2] / "frontend" / "e2e" / "partida-sin-rondas.json"


class PartidaSinRondasTests(TestCase):
    def test_el_detalle_de_una_partida_sin_rondas_responde_200(self):
        """Si el detalle suma o cambia una clave, este test obliga a regenerar
        el JSON del e2e: asi el e2e no queda probando una forma vieja."""
        match = make_match()
        response = self.client.get(f"/api/matches/{match.pk}/")
        self.assertEqual(response.status_code, 200)
        cuerpo = response.json()
        cuerpo.pop("match")
        self.assertEqual(cuerpo["rounds"], [])
        self.assertEqual(cuerpo, json.loads(SIN_RONDAS.read_text(encoding="utf-8")))
