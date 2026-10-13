"""Tendencias segun el resultado de la ronda anterior (inercia entre rondas)."""

from __future__ import annotations

from django.test import TestCase

from replays.analytics import aggregates as agg
from replays.models import Round

from .factories import make_match, make_round, make_round_player


def _partida(rondas: list[tuple[int, bool]], *, index: int = 0, sides: list[str] | None = None,
             map_name: str = "Club House"):
    """Una partida con una ronda mia por cada `(numero, gane)` de la lista."""
    match = make_match(index=index, map_name=map_name)
    for i, (numero, gane) in enumerate(rondas):
        lado = sides[i] if sides else "Attack"
        make_round_player(make_round(match, numero, side=lado, won=gane))
    return match


def _por_anterior(filas: list[dict]) -> dict[str, int]:
    return {fila["previous"]: fila["rounds"] for fila in filas}


class RondaAnteriorTests(TestCase):
    def test_las_tres_filas_salen_en_orden_fijo(self):
        _partida([(1, True), (2, False)])
        filas = agg.by_previous_round()
        self.assertEqual([f["previous"] for f in filas], ["after_win", "after_loss", "no_previous"])

    def test_ganar_y_perder_mandan_la_siguiente_a_su_fila(self):
        _partida([(1, True), (2, False), (3, True)])
        filas = agg.by_previous_round()
        self.assertEqual(_por_anterior(filas), {"after_win": 1, "after_loss": 1, "no_previous": 1})
        despues_de_ganar, despues_de_perder, _ = filas
        # la 2 viene despues de ganar la 1 y se perdio; la 3 viene despues de perder y se gano
        self.assertEqual(despues_de_ganar["winrate"], 0.0)
        self.assertEqual(despues_de_perder["winrate"], 100.0)

    def test_la_primera_ronda_y_la_que_le_falta_la_anterior_van_a_sin_anterior(self):
        _partida([(1, True), (2, True), (5, False)])
        self.assertEqual(
            _por_anterior(agg.by_previous_round()),
            {"after_win": 1, "after_loss": 0, "no_previous": 2},
        )

    def test_anterior_sin_resultado_va_a_sin_anterior(self):
        match = _partida([(1, True), (2, True)])
        Round.objects.filter(match=match, number=1).update(my_team_won=None)
        self.assertEqual(
            _por_anterior(agg.by_previous_round()),
            {"after_win": 0, "after_loss": 0, "no_previous": 2},
        )

    def test_la_ronda_anterior_no_se_cruza_entre_partidas(self):
        _partida([(1, False)], index=0)
        _partida([(2, True)], index=1)
        self.assertEqual(
            _por_anterior(agg.by_previous_round()),
            {"after_win": 0, "after_loss": 0, "no_previous": 2},
        )

    def test_el_filtro_de_lado_no_cambia_la_ronda_anterior(self):
        _partida([(1, True), (2, False)], sides=["Defense", "Attack"])
        self.assertEqual(
            _por_anterior(agg.by_previous_round(side="Attack")),
            {"after_win": 1, "after_loss": 0, "no_previous": 0},
        )

    def test_el_filtro_de_operador_no_cambia_la_ronda_anterior(self):
        match = make_match()
        make_round_player(make_round(match, 0, won=False), operator="Ash")
        make_round_player(make_round(match, 1, won=True), operator="Zofia")
        self.assertEqual(
            _por_anterior(agg.by_previous_round(operator="Zofia")),
            {"after_win": 0, "after_loss": 1, "no_previous": 0},
        )

    def test_las_filas_suman_las_rondas_del_resumen(self):
        _partida([(1, True), (2, False), (3, False), (4, True), (7, True)], index=0,
                 sides=["Attack", "Attack", "Defense", "Defense", "Attack"])
        _partida([(0, False), (1, True)], index=1, map_name="Oregon")
        for filtros in ({}, {"map": "oregon"}, {"side": "Attack"}):
            filas = agg.by_previous_round(**filtros)
            total = agg.overview(**filtros)["overall"]["rounds"]
            self.assertEqual(sum(f["rounds"] for f in filas), total, filtros)
        self.assertEqual(sum(f["rounds"] for f in agg.by_previous_round()), 7)
        self.assertEqual(sum(f["rounds"] for f in agg.by_previous_round(side="Attack")), 5)


class RondaAnteriorApiTests(TestCase):
    def test_base_vacia_y_filtros_raros_dan_200_con_tres_filas_en_cero(self):
        for url in ("/api/trends/", "/api/trends/?days=-1", "/api/trends/?since=foo",
                    "/api/trends/?map=%00"):
            respuesta = self.client.get(url)
            self.assertEqual(respuesta.status_code, 200, url)
            filas = respuesta.json()["by_previous_round"]
            self.assertEqual([f["previous"] for f in filas],
                             ["after_win", "after_loss", "no_previous"], url)
            self.assertEqual([f["rounds"] for f in filas], [0, 0, 0], url)

    def test_trends_con_datos_trae_la_ronda_anterior(self):
        _partida([(1, True), (2, False)])
        filas = self.client.get("/api/trends/").json()["by_previous_round"]
        self.assertEqual(_por_anterior(filas), {"after_win": 1, "after_loss": 0, "no_previous": 1})
