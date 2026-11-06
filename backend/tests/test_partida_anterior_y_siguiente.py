"""Partida anterior y siguiente desde el detalle (ficha 95)."""

from __future__ import annotations

from datetime import datetime

from django.test import TestCase

from .factories import make_match

MISMA_FECHA = datetime(2026, 9, 2, 21, 0)


class PartidaAnteriorYSiguienteTests(TestCase):
    def _vecinas(self, match) -> tuple[int | None, int | None]:
        datos = self.client.get(f"/api/matches/{match.pk}/").json()["match"]
        return datos["prev_id"], datos["next_id"]

    def test_la_partida_del_medio_trae_anterior_y_siguiente(self):
        primera = make_match(index=0)
        medio = make_match(index=1)
        ultima = make_match(index=2)
        self.assertEqual(self._vecinas(medio), (primera.pk, ultima.pk))

    def test_la_primera_no_tiene_anterior_y_la_ultima_no_tiene_siguiente(self):
        primera = make_match(index=0)
        medio = make_match(index=1)
        ultima = make_match(index=2)
        self.assertEqual(self._vecinas(primera), (None, medio.pk))
        self.assertEqual(self._vecinas(ultima), (medio.pk, None))

    def test_el_orden_es_por_fecha_y_no_por_id(self):
        # la importada despues pero jugada antes va primero
        nueva = make_match(index=5)
        vieja = make_match(index=1)
        self.assertEqual(self._vecinas(vieja), (None, nueva.pk))
        self.assertEqual(self._vecinas(nueva), (vieja.pk, None))

    def test_dos_partidas_con_la_misma_fecha_no_se_saltan_ni_se_repiten(self):
        primera = make_match(index=0)
        empate_a = make_match(index=1, played_at=MISMA_FECHA)
        empate_b = make_match(index=2, played_at=MISMA_FECHA)
        todas = [primera.pk, empate_a.pk, empate_b.pk]

        hacia_adelante, actual = [], primera
        while actual is not None:
            hacia_adelante.append(actual.pk)
            siguiente = self._vecinas(actual)[1]
            actual = type(primera).objects.get(pk=siguiente) if siguiente else None
        self.assertEqual(hacia_adelante, todas)

        hacia_atras, actual = [], empate_b
        while actual is not None:
            hacia_atras.append(actual.pk)
            anterior = self._vecinas(actual)[0]
            actual = type(primera).objects.get(pk=anterior) if anterior else None
        self.assertEqual(hacia_atras, list(reversed(todas)))

    def test_una_sola_partida_no_tiene_vecinas(self):
        sola = make_match()
        self.assertEqual(self._vecinas(sola), (None, None))

    def test_el_listado_desempata_por_id(self):
        empate_a = make_match(index=1, played_at=MISMA_FECHA)
        empate_b = make_match(index=2, played_at=MISMA_FECHA)
        ids = [m["id"] for m in self.client.get("/api/matches/").json()["matches"]]
        self.assertEqual(ids, [empate_b.pk, empate_a.pk])
        # el listado (mas nueva arriba) y la navegacion siguen el mismo orden
        self.assertEqual(self._vecinas(empate_b), (empate_a.pk, None))
