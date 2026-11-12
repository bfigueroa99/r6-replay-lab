"""La tira de rondas de cada fila de Partidas (ficha 103)."""

from __future__ import annotations

from django.db import connection
from django.test import TestCase
from django.test.utils import CaptureQueriesContext

from .factories import make_match, make_round


def _tira(client, match_id: int, query: str = "") -> list[dict]:
    data = client.get(f"/api/matches/{query}").json()
    return next(m["strip"] for m in data["matches"] if m["id"] == match_id)


class TiraDeRondasTests(TestCase):
    def test_cada_partida_trae_su_tira_en_orden(self):
        match = make_match(my_score=2, opponent_score=1)
        # creadas desordenadas: el orden lo da `number`, no el id
        make_round(match, 2, side="Defense", won=True)
        make_round(match, 0, side="Attack", won=True)
        make_round(match, 1, side="Attack", won=False)
        self.assertEqual(
            _tira(self.client, match.id),
            [
                {"number": 0, "won": True, "side": "Attack", "overtime": False},
                {"number": 1, "won": False, "side": "Attack", "overtime": False},
                {"number": 2, "won": True, "side": "Defense", "overtime": False},
            ],
        )

    def test_cada_tira_es_de_su_partida(self):
        una = make_match(index=0)
        otra = make_match(index=1)
        make_round(una, 0, won=True)
        make_round(otra, 0, won=False)
        make_round(otra, 1, won=False)
        self.assertEqual([r["won"] for r in _tira(self.client, una.id)], [True])
        self.assertEqual([r["won"] for r in _tira(self.client, otra.id)], [False, False])

    def test_ronda_sin_ganador_viaja_como_null(self):
        match = make_match()
        make_round(match, 0, won=None)
        self.assertIsNone(_tira(self.client, match.id)[0]["won"])

    def test_la_prorroga_se_marca(self):
        match = make_match(my_score=4, opponent_score=3)
        make_round(match, 5, won=True)
        make_round(match, 6, won=True, overtime_number=1)
        self.assertEqual([r["overtime"] for r in _tira(self.client, match.id)], [False, True])

    def test_lado_desconocido_viaja_vacio(self):
        match = make_match()
        make_round(match, 0, side="")
        self.assertEqual(_tira(self.client, match.id)[0]["side"], "")

    def test_partida_sin_rondas_trae_tira_vacia(self):
        match = make_match()
        self.assertEqual(_tira(self.client, match.id), [])

    def test_el_filtro_de_lado_no_recorta_la_tira(self):
        match = make_match()
        make_round(match, 0, side="Attack", site="1F Kitchen", won=True)
        make_round(match, 1, side="Defense", site="2F Bedroom", won=False)
        for query in ("?side=Attack", "?side=Defense", "?site=1F%20Kitchen", "?operator=Ash"):
            with self.subTest(query=query):
                self.assertEqual(
                    [r["side"] for r in _tira(self.client, match.id, query)], ["Attack", "Defense"]
                )

    def test_la_tira_no_suma_una_consulta_por_partida(self):
        for index in range(6):
            match = make_match(index=index)
            for number in range(3):
                make_round(match, number, side="Attack" if number < 2 else "Defense")

        def consultas(limit: int) -> int:
            with CaptureQueriesContext(connection) as capturadas:
                data = self.client.get(f"/api/matches/?limit={limit}").json()
            self.assertEqual(len(data["matches"]), limit)
            self.assertTrue(all(len(m["strip"]) == 3 for m in data["matches"]))
            return len(capturadas)

        # el numero absoluto no se fija: otras fichas suman consultas a
        # match_list sin que eso sea un problema; lo que no puede pasar es
        # que crezca con el largo de la pagina
        self.assertEqual(consultas(2), consultas(6))
