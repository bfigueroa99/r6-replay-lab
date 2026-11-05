"""Filtro por tipo de partida que usa el selector "Tipo" (ficha 77).

El backend ya filtraba por `match_type`; estos tests fijan el contrato que
la barra de filtros empieza a usar y que reemplaza al checkbox "Solo ranked".
"""

from __future__ import annotations

from django.test import TestCase

from .factories import make_match, make_round, make_round_player


class TipoDePartidaTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        # 2 Ranked de 3 rondas y 1 Unranked de 2, con ataque y defensa en cada una
        for index, (tipo, rondas) in enumerate((("Ranked", 3), ("Ranked", 3), ("Unranked", 2))):
            match = make_match(match_type=tipo, index=index, my_score=rondas, opponent_score=0)
            for numero in range(1, rondas + 1):
                rnd = make_round(match, numero, side="Attack" if numero % 2 else "Defense", won=numero != 2)
                make_round_player(rnd, kills=numero % 3, died=numero != 1)

    def _overview(self, query: str) -> dict:
        response = self.client.get(f"/api/overview/{query}")
        self.assertEqual(response.status_code, 200)
        return response.json()

    def test_filtrar_por_ranked_da_lo_mismo_que_solo_ranked(self):
        por_tipo = self._overview("?match_type=Ranked")
        por_check = self._overview("?ranked_only=1")
        self.assertEqual(por_tipo["overall"]["rounds"], 6)
        for bloque in ("overall", "attack", "defense"):
            self.assertEqual(por_tipo[bloque], por_check[bloque], bloque)

    def test_filtrar_por_unranked_deja_afuera_las_ranked(self):
        self.assertEqual(self._overview("?match_type=Unranked")["overall"]["rounds"], 2)
        self.assertEqual(self._overview("")["overall"]["rounds"], 8)

    def test_las_opciones_listan_cada_tipo_una_vez(self):
        make_match(match_type="", index=9)
        data = self.client.get("/api/filters/").json()
        self.assertEqual(data["match_types"], ["Ranked", "Unranked"])

    def test_un_tipo_que_no_existe_da_cero_rondas_y_no_500(self):
        self.assertEqual(self._overview("?match_type=Nada")["overall"]["rounds"], 0)

    def test_ranked_only_con_otro_tipo_no_da_500(self):
        # la API los aplica juntos; la UI ya no los manda juntos
        self.assertEqual(self._overview("?ranked_only=1&match_type=Unranked")["overall"]["rounds"], 0)
