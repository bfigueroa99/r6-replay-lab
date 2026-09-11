"""Tests del rango de fechas de los filtros."""

from __future__ import annotations

from datetime import datetime

from django.test import TestCase

from .factories import make_match, make_round, make_round_player


def rondas(response) -> int:
    return response.json()["overall"]["rounds"]


class RangoTests(TestCase):
    def setUp(self):
        # una partida cada dia, del 6 al 9 de septiembre
        for i, dia in enumerate((6, 7, 8, 9)):
            match = make_match(index=i, played_at=datetime(2026, 9, dia, 21, 30))
            make_round_player(make_round(match, 0))

    def _rondas(self, query: str) -> int:
        return rondas(self.client.get(f"/api/overview/?{query}"))

    def test_sin_filtro_estan_todas(self):
        self.assertEqual(self._rondas(""), 4)

    def test_hasta_incluye_el_dia_completo(self):
        """`until=2026-09-08` tiene que incluir el 8, no cortar a medianoche."""
        self.assertEqual(self._rondas("until=2026-09-08"), 3)

    def test_desde_arranca_a_medianoche(self):
        self.assertEqual(self._rondas("since=2026-09-08"), 2)

    def test_un_solo_dia(self):
        """El caso que motiva el item: aislar una noche puntual."""
        self.assertEqual(self._rondas("since=2026-09-08&until=2026-09-08"), 1)

    def test_rango_cerrado(self):
        self.assertEqual(self._rondas("since=2026-09-07&until=2026-09-08"), 2)

    def test_con_hora_explicita_se_respeta(self):
        """Si viene la hora, no se estira al final del dia."""
        self.assertEqual(self._rondas("until=2026-09-08T21:00:00"), 2)
        self.assertEqual(self._rondas("until=2026-09-08T22:00:00"), 3)

    def test_fecha_invalida_se_ignora(self):
        self.assertEqual(self._rondas("since=no-es-una-fecha"), 4)
        self.assertEqual(self._rondas("until=2026-13-45"), 4)

    def test_el_rango_le_gana_a_los_dias(self):
        """Si hay `since` explicito, `days` no se aplica."""
        self.assertEqual(self._rondas("since=2026-09-08&days=1"), 2)

    def test_rango_al_reves_no_devuelve_nada(self):
        self.assertEqual(self._rondas("since=2026-09-09&until=2026-09-06"), 0)

    def test_llega_a_todos_los_endpoints(self):
        for url in (
            "/api/maps/?since=2026-09-08&min_rounds=1",
            "/api/operators/?since=2026-09-08&min_rounds=1",
            "/api/export/?table=maps&since=2026-09-08",
            "/api/coach/?since=2026-09-08",
        ):
            with self.subTest(url=url):
                self.assertEqual(self.client.get(url).status_code, 200)

        data = self.client.get("/api/trends/?since=2026-09-08").json()
        self.assertEqual(sum(f["rounds"] for f in data["by_day"]), 2)

    def test_el_export_respeta_el_rango(self):
        csv = self.client.get("/api/export/?table=days&since=2026-09-08").content.decode()
        self.assertEqual(len(csv.strip().splitlines()), 3)  # cabecera + 2 dias
