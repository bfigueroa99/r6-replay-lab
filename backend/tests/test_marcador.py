"""Tendencias segun el marcador antes de la ronda: adelante, empatado o atras."""

from __future__ import annotations

from django.test import TestCase

from pydissect.constants import Y9S4
from replays.analytics import aggregates as agg

from .factories import make_match, make_round, make_round_player


def _partida(marcadores: list, *, index: int = 0, team_index: int = 0,
             map_name: str = "Club House", sides: list[str] | None = None,
             code_version: int = Y9S4):
    """Una partida con una ronda mia por cada `score_before` de la lista."""
    match = make_match(index=index, map_name=map_name, code_version=code_version)
    for numero, marcador in enumerate(marcadores):
        lado = sides[numero] if sides else "Attack"
        rnd = make_round(match, numero, side=lado, won=numero % 2 == 0, score_before=marcador)
        make_round_player(rnd, team_index=team_index)
    return match


def _por_estado(filas: list[dict]) -> dict[str, int]:
    return {fila["score_state"]: fila["rounds"] for fila in filas}


class MarcadorTests(TestCase):
    def test_las_cuatro_filas_salen_en_orden_fijo(self):
        _partida([[0, 0], [1, 0]])
        filas = agg.by_score_state()
        self.assertEqual([f["score_state"] for f in filas], ["ahead", "tied", "behind", "unknown"])

    def test_cero_cero_uno_cero_uno_uno_uno_dos_desde_tu_lado(self):
        _partida([[0, 0], [1, 0], [1, 1], [1, 2]])
        self.assertEqual(
            _por_estado(agg.by_score_state()),
            {"ahead": 1, "tied": 2, "behind": 1, "unknown": 0},
        )

    def test_siendo_el_equipo_uno_el_marcador_se_lee_al_reves(self):
        _partida([[2, 1], [0, 3]], team_index=1)
        filas = agg.by_score_state()
        self.assertEqual(
            _por_estado(filas),
            {"ahead": 1, "tied": 0, "behind": 1, "unknown": 0},
        )
        adelante, _, atras, _ = filas
        # la ronda 0 ([2, 1], atras) se gano; la 1 ([0, 3], adelante) se perdio
        self.assertEqual(atras["winrate"], 100.0)
        self.assertEqual(adelante["winrate"], 0.0)

    def test_marcador_vacio_o_de_otro_largo_va_a_sin_marcador(self):
        _partida([[], [1], [1, 2, 3]])
        self.assertEqual(
            _por_estado(agg.by_score_state()),
            {"ahead": 0, "tied": 0, "behind": 0, "unknown": 3},
        )

    def test_un_equipo_fuera_de_cero_y_uno_va_a_sin_marcador(self):
        _partida([[1, 0]], team_index=2)
        self.assertEqual(_por_estado(agg.by_score_state())["unknown"], 1)

    def test_antes_de_y9s4_el_cero_cero_es_sin_marcador_y_no_empate(self):
        # el parser pone startingScore en 0 en versiones viejas: parece 0-0 y no lo es
        _partida([[0, 0], [0, 0]], code_version=Y9S4 - 1)
        _partida([[0, 0]], index=1, code_version=0)
        self.assertEqual(
            _por_estado(agg.by_score_state()),
            {"ahead": 0, "tied": 0, "behind": 0, "unknown": 3},
        )

    def test_las_filas_suman_las_rondas_del_resumen(self):
        _partida([[0, 0], [1, 0], [], [2, 3]], index=0,
                 sides=["Attack", "Defense", "Attack", "Defense"])
        _partida([[0, 0], [0, 1], [1]], index=1, team_index=1, map_name="Oregon")
        for filtros in ({}, {"map": "oregon"}, {"side": "Attack"}):
            filas = agg.by_score_state(**filtros)
            total = agg.overview(**filtros)["overall"]["rounds"]
            self.assertEqual(sum(f["rounds"] for f in filas), total, filtros)
        self.assertEqual(sum(f["rounds"] for f in agg.by_score_state()), 7)


class MarcadorApiTests(TestCase):
    def test_base_vacia_y_filtros_raros_dan_200_con_cuatro_filas_en_cero(self):
        for url in ("/api/trends/", "/api/trends/?days=-1", "/api/trends/?since=foo",
                    "/api/trends/?map=%00", "/api/trends/?until=foo"):
            respuesta = self.client.get(url)
            self.assertEqual(respuesta.status_code, 200, url)
            filas = respuesta.json()["by_score_state"]
            self.assertEqual([f["score_state"] for f in filas],
                             ["ahead", "tied", "behind", "unknown"], url)
            self.assertEqual([f["rounds"] for f in filas], [0, 0, 0, 0], url)

    def test_trends_con_datos_trae_el_marcador(self):
        _partida([[0, 0], [1, 0]])
        filas = self.client.get("/api/trends/").json()["by_score_state"]
        self.assertEqual(_por_estado(filas), {"ahead": 1, "tied": 1, "behind": 0, "unknown": 0})
