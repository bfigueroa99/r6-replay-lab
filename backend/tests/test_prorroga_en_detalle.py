"""La prorroga marcada en el detalle de la partida (ficha 136)."""

from __future__ import annotations

from django.test import TestCase

from .factories import make_match, make_round


def _overtime_del_detalle(client, match_id: int) -> list[bool]:
    data = client.get(f"/api/matches/{match_id}/").json()
    return [r["overtime"] for r in data["rounds"]]


class ProrrogaEnDetalleTests(TestCase):
    def test_detalle_marca_las_rondas_de_prorroga(self):
        match = make_match(my_score=4, opponent_score=3)
        for n in range(3):
            make_round(match, n, won=n % 2 == 0)
        make_round(match, 3, won=True, overtime_number=1)
        make_round(match, 4, won=True, overtime_number=2)
        self.assertEqual(
            _overtime_del_detalle(self.client, match.id), [False, False, False, True, True]
        )

    def test_detalle_sin_prorroga_las_marca_todas_false(self):
        match = make_match(my_score=2, opponent_score=1)
        for n in range(3):
            make_round(match, n, won=n != 1)
        self.assertEqual(_overtime_del_detalle(self.client, match.id), [False, False, False])

    def test_overtime_del_detalle_coincide_con_la_tira_del_listado(self):
        match = make_match(my_score=4, opponent_score=3)
        make_round(match, 0, won=True)
        make_round(match, 1, won=False)
        make_round(match, 2, won=True, overtime_number=1)
        listado = self.client.get("/api/matches/").json()["matches"]
        tira = next(m["strip"] for m in listado if m["id"] == match.id)
        self.assertEqual(
            _overtime_del_detalle(self.client, match.id), [r["overtime"] for r in tira]
        )
