"""Modo de juego como filtro de la barra y como tabla de Tendencias (ficha 100)."""

from __future__ import annotations

import json

from django.test import TestCase

from replays.analytics import aggregates as agg
from replays.models import Match

from .factories import make_match, make_round, make_round_player


def _partida(index: int, gamemode: str, resultados: list[bool], kills: int = 1, **extra) -> Match:
    """Partida con una ronda por resultado; el marcador sale de los resultados."""
    ganadas = sum(resultados)
    match = make_match(
        index=index,
        gamemode=gamemode,
        my_score=ganadas,
        opponent_score=len(resultados) - ganadas,
        **extra,
    )
    for numero, gano in enumerate(resultados, start=1):
        lado = "Attack" if numero % 2 else "Defense"
        rnd = make_round(match, numero, side=lado, won=gano)
        make_round_player(rnd, kills=kills, died=not gano)
    return match


class ModoDeJuegoTests(TestCase):
    def setUp(self):
        # Bomb ganada 3-0 (2 kills por ronda), Bomb perdida 0-2, Hostage 1-1.
        self.bomba_ganada = _partida(0, "Bomb", [True, True, True], kills=2)
        self.bomba_perdida = _partida(1, "Bomb", [False, False])
        self.rehen = _partida(2, "Hostage", [True, False])

    def _get(self, url: str) -> dict:
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        return json.loads(response.content)

    def test_filtrar_por_hostage_cuenta_solo_sus_rondas(self):
        self.assertEqual(self._get("/api/overview/")["overall"]["rounds"], 7)
        self.assertEqual(self._get("/api/overview/?gamemode=Hostage")["overall"]["rounds"], 2)

    def test_un_modo_que_no_existe_da_cero_rondas_y_no_500(self):
        overview = self._get("/api/overview/?gamemode=Nada")
        self.assertEqual(overview["overall"]["rounds"], 0)
        self.assertEqual(self._get("/api/trends/?gamemode=Nada")["by_gamemode"], [])
        self.assertEqual(self._get("/api/matches/?gamemode=Nada")["total"], 0)

    def test_el_listado_de_partidas_respeta_el_modo(self):
        datos = self._get("/api/matches/?gamemode=Bomb")
        self.assertEqual(datos["total"], 2)
        self.assertEqual(
            {m["id"] for m in datos["matches"]}, {self.bomba_ganada.pk, self.bomba_perdida.pk}
        )

    def test_las_opciones_listan_cada_modo_una_vez_sin_vacios(self):
        _partida(3, "", [True])
        self.assertEqual(self._get("/api/filters/")["gamemodes"], ["Bomb", "Hostage"])

    def test_por_modo_suma_partidas_winrate_y_rating_por_modo(self):
        filas = {f["gamemode"]: f for f in self._get("/api/trends/")["by_gamemode"]}
        self.assertEqual(list(filas), ["Bomb", "Hostage"])

        bomba = filas["Bomb"]
        self.assertEqual(bomba["matches"], 2)
        self.assertEqual(bomba["matches_decided"], 2)
        self.assertEqual(bomba["matches_won"], 1)
        self.assertEqual(bomba["match_winrate"], 50.0)
        self.assertEqual(bomba["rounds"], 5)
        self.assertEqual(bomba["rounds_won"], 3)
        self.assertEqual(bomba["winrate"], 60.0)
        # 6 + 2 kills, 2 muertes (las rondas perdidas)
        self.assertEqual(bomba["kd"], 4.0)
        self.assertEqual(bomba["rating"], agg.overview(gamemode="Bomb")["overall"]["rating"])

        rehen = filas["Hostage"]
        self.assertEqual(rehen["matches"], 1)
        self.assertEqual(rehen["rounds"], 2)
        self.assertEqual(rehen["winrate"], 50.0)
        # 1 + 1 kills, 1 muerte
        self.assertEqual(rehen["kd"], 2.0)

    def test_por_modo_deja_fuera_del_porcentaje_las_partidas_sin_resultado(self):
        sin_resultado = _partida(3, "Hostage", [True, False])
        Match.objects.filter(pk=sin_resultado.pk).update(won=None)
        rehen = {f["gamemode"]: f for f in agg.by_gamemode()}["Hostage"]
        self.assertEqual(rehen["matches"], 2)
        self.assertEqual(rehen["matches_decided"], 1)
        # la Hostage del setUp va 1-1: won=False
        self.assertEqual(rehen["matches_won"], 0)
        self.assertEqual(rehen["match_winrate"], 0.0)

    def test_por_modo_con_filtro_de_lado_mantiene_el_resultado_de_la_partida(self):
        filas = {f["gamemode"]: f for f in agg.by_gamemode(side="Defense")}
        bomba = filas["Bomb"]
        # Defensa: ronda 2 de cada Bomb; la ganada 3-0 sigue contando como ganada
        self.assertEqual(bomba["rounds"], 2)
        self.assertEqual(bomba["matches"], 2)
        self.assertEqual(bomba["matches_won"], 1)
        self.assertEqual(bomba["match_winrate"], 50.0)

    def test_por_modo_deja_la_partida_sin_modo_en_su_propia_fila(self):
        _partida(3, "", [True])
        filas = agg.by_gamemode()
        self.assertEqual([f["gamemode"] for f in filas], ["Bomb", "", "Hostage"])

    def test_por_modo_con_filtro_de_lado_cuenta_ganada_la_partida_que_perdio_su_defensa(self):
        # Gana 2-1 pero pierde su unica ronda de defensa: leyendo las rondas
        # filtradas contaria como perdida; el resultado es el de la partida.
        _partida(3, "SecureArea", [True, False, True])
        area = {f["gamemode"]: f for f in agg.by_gamemode(side="Defense")}["SecureArea"]
        self.assertEqual(area["rounds"], 1)
        self.assertEqual(area["rounds_won"], 0)
        self.assertEqual(area["matches_won"], 1)
        self.assertEqual(area["match_winrate"], 100.0)
