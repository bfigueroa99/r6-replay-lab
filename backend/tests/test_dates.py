"""Tests del rango de fechas de los filtros."""

from __future__ import annotations

from datetime import datetime

from django.test import TestCase, override_settings

from replays.models import Player

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


@override_settings(TIME_ZONE="America/Santiago")
class FechaConZonaTests(TestCase):
    """Una fecha ISO con offset (la de `toISOString()`) no puede dar 500."""

    def setUp(self):
        # 21:30 en Santiago el 8 de septiembre de 2026 (UTC-3) = 00:30 UTC del 9
        for i, dia in enumerate((6, 7, 8, 9)):
            match = make_match(index=i, played_at=datetime(2026, 9, dia, 21, 30))
            make_round_player(make_round(match, 0))
        self.jugador = Player.objects.get(is_me=True)

    def _rondas(self, query: str) -> int:
        return rondas(self.client.get(f"/api/overview/?{query}"))

    def test_una_fecha_con_z_no_revienta_ningun_endpoint(self):
        endpoints = (
            "/api/overview/",
            "/api/coach/",
            "/api/operators/",
            "/api/trends/",
            "/api/teammates/",
            "/api/duels/",
            "/api/sessions/",
            "/api/compare/",
            f"/api/players/{self.jugador.pk}/",
            "/api/export/?table=maps",
        )
        for url in endpoints:
            for query in (
                "since=2026-09-07T00:00Z",
                "until=2026-09-09T00:00:00.000Z",
                "since=2026-09-07T00:00%2B00:00",
                "until=2026-09-09T00:00-03:00",
            ):
                sep = "&" if "?" in url else "?"
                with self.subTest(url=url, query=query):
                    self.assertEqual(self.client.get(f"{url}{sep}{query}").status_code, 200)

    def test_la_fecha_con_zona_se_pasa_a_la_hora_local(self):
        """La partida del 8 a las 21:30 locales es la del 9 a las 00:30 UTC."""
        self.assertEqual(self._rondas("since=2026-09-09T00:30Z"), 2)
        self.assertEqual(self._rondas("since=2026-09-09T00:31Z"), 1)
        self.assertEqual(self._rondas("until=2026-09-09T00:30Z"), 3)
        self.assertEqual(self._rondas("until=2026-09-09T00:29Z"), 2)

    def test_un_offset_distinto_de_utc_tambien_se_convierte(self):
        # 23:30 en UTC-1 = 00:30 UTC = 21:30 en Santiago
        self.assertEqual(self._rondas("since=2026-09-08T23:30-01:00"), 2)
        self.assertEqual(self._rondas("since=2026-09-08T23:31-01:00"), 1)
