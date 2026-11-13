"""Prorroga partida por el lado de tu ronda (Tendencias, panel de mitades)."""

from __future__ import annotations

from django.test import TestCase

from replays.analytics import aggregates as agg

from .factories import make_match, make_round, make_round_player


def _partida_con_prorroga(*, index: int = 0, map_name: str = "Club House"):
    """Tres rondas normales y tres de prorroga: dos en ataque ganadas, una en defensa perdida."""
    match = make_match(index=index, map_name=map_name, my_score=5, opponent_score=4)
    for numero, lado in enumerate(["Attack", "Attack", "Defense"], start=1):
        make_round_player(make_round(match, numero, side=lado))
    prorroga = [("Attack", True), ("Attack", True), ("Defense", False)]
    for ot, (lado, gano) in enumerate(prorroga, start=1):
        make_round_player(make_round(match, 3 + ot, side=lado, won=gano, overtime_number=ot))
    return match


def _por_lado(filas: list[dict]) -> dict[str, dict]:
    return {fila["side"]: fila for fila in filas}


class ProrrogaPorLadoTests(TestCase):
    def test_parte_la_prorroga_por_lado(self):
        _partida_con_prorroga()
        filas = agg.by_overtime_side()
        self.assertEqual([f["side"] for f in filas], ["Attack", "Defense"])
        ataque, defensa = filas
        self.assertEqual((ataque["rounds"], ataque["winrate"]), (2, 100.0))
        self.assertEqual((defensa["rounds"], defensa["winrate"]), (1, 0.0))
        self.assertIsNotNone(ataque["rating"])
        self.assertIsNotNone(defensa["rating"])

    def test_las_rondas_sin_prorroga_no_entran(self):
        _partida_con_prorroga()
        filas = agg.by_overtime_side()
        # tres rondas normales (dos en ataque) quedan afuera
        self.assertEqual(sum(f["rounds"] for f in filas), 3)

    def test_by_half_no_cambia(self):
        _partida_con_prorroga()
        mitades = {f["half"]: f["rounds"] for f in agg.by_half()}
        self.assertEqual(mitades, {"first": 2, "second": 1, "overtime": 3})

    def test_by_half_no_cambia_ni_winrate_ni_rating(self):
        _partida_con_prorroga()
        filas = {f["half"]: f for f in agg.by_half()}
        winrates = {mitad: fila["winrate"] for mitad, fila in filas.items()}
        self.assertEqual(winrates, {"first": 100.0, "second": 100.0, "overtime": 66.7})
        # la fila de prorroga sigue juntando los dos lados, no es ninguna de las nuevas
        por_lado = agg.by_overtime_side()
        self.assertNotIn(filas["overtime"]["winrate"], [f["winrate"] for f in por_lado])
        self.assertTrue(all(fila["rating"] is not None for fila in filas.values()))

    def test_con_filtro_de_lado_sale_solo_ese(self):
        _partida_con_prorroga()
        data = self.client.get("/api/trends/?side=Defense").json()
        self.assertEqual([f["side"] for f in data["by_overtime_side"]], ["Defense"])
        self.assertEqual(data["by_overtime_side"][0]["rounds"], 1)

    def test_el_filtro_de_mapa_aplica(self):
        _partida_con_prorroga(index=0, map_name="Club House")
        _partida_con_prorroga(index=1, map_name="Oregon")
        data = self.client.get("/api/trends/?map=oregon").json()
        lados = _por_lado(data["by_overtime_side"])
        self.assertEqual((lados["Attack"]["rounds"], lados["Defense"]["rounds"]), (2, 1))

    def test_sin_prorroga_las_filas_salen_en_cero(self):
        match = make_match()
        make_round_player(make_round(match, 1, side="Attack"))
        filas = agg.by_overtime_side()
        self.assertEqual([(f["side"], f["rounds"]) for f in filas], [("Attack", 0), ("Defense", 0)])
        self.assertIsNone(filas[0]["winrate"])

    def test_la_api_sin_datos_devuelve_las_dos_filas_en_cero(self):
        data = self.client.get("/api/trends/").json()
        self.assertEqual([f["rounds"] for f in data["by_overtime_side"]], [0, 0])


def _a_prorroga(index: int, lados_prorroga: list[str], *, gano: bool | None = True,
                map_name: str = "Club House"):
    """Partida que llega a prorroga; `lados_prorroga` en orden de `overtime_number`."""
    match = make_match(index=index, map_name=map_name, my_score=5 if gano else 4,
                       opponent_score=4 if gano else 5)
    if gano is None:
        match.won = None
        match.save(update_fields=["won"])
    for numero, lado in enumerate(["Attack", "Defense"], start=1):
        make_round_player(make_round(match, numero, side=lado))
    for ot, lado in enumerate(lados_prorroga, start=1):
        make_round_player(make_round(match, 2 + ot, side=lado, overtime_number=ot))
    return match


class PartidasAProrrogaPorLadoTests(TestCase):
    def test_cuenta_partidas_y_ganadas_por_el_lado_de_la_primera_ronda_de_prorroga(self):
        _a_prorroga(0, ["Defense"], gano=True)
        _a_prorroga(1, ["Defense"], gano=False)
        _a_prorroga(2, ["Attack"], gano=True)
        lados = _por_lado(agg.by_overtime_start_side())
        self.assertEqual(
            (lados["Defense"]["matches"], lados["Defense"]["decided"], lados["Defense"]["wins"],
             lados["Defense"]["winrate"]),
            (2, 2, 1, 50.0),
        )
        self.assertEqual((lados["Attack"]["matches"], lados["Attack"]["winrate"]), (1, 100.0))

    def test_el_lado_es_el_de_la_primera_ronda_de_prorroga_y_no_el_de_la_mayoria(self):
        _a_prorroga(0, ["Defense", "Attack", "Attack"])
        lados = _por_lado(agg.by_overtime_start_side())
        self.assertEqual((lados["Defense"]["matches"], lados["Attack"]["matches"]), (1, 0))

    def test_una_partida_sin_prorroga_no_entra(self):
        match = make_match(index=5)
        make_round_player(make_round(match, 1, side="Defense"))
        _a_prorroga(0, ["Attack"])
        lados = _por_lado(agg.by_overtime_start_side())
        self.assertEqual((lados["Attack"]["matches"], lados["Defense"]["matches"]), (1, 0))

    def test_sin_resultado_cuenta_en_partidas_y_no_en_el_porcentaje(self):
        _a_prorroga(0, ["Defense"], gano=True)
        _a_prorroga(1, ["Defense"], gano=None)
        defensa = _por_lado(agg.by_overtime_start_side())["Defense"]
        self.assertEqual(
            (defensa["matches"], defensa["decided"], defensa["wins"], defensa["winrate"]),
            (2, 1, 1, 100.0),
        )

    def test_con_filtro_de_lado_sale_solo_esa_fila(self):
        _a_prorroga(0, ["Defense", "Attack"])
        _a_prorroga(1, ["Attack"])
        filas = agg.by_overtime_start_side(side="Attack")
        self.assertEqual([f["side"] for f in filas], ["Attack"])
        # la partida que arranco la prorroga en defensa no se muda a ataque
        self.assertEqual(filas[0]["matches"], 1)

    def test_el_filtro_de_mapa_aplica(self):
        _a_prorroga(0, ["Defense"], map_name="Club House")
        _a_prorroga(1, ["Defense"], map_name="Oregon")
        data = self.client.get("/api/trends/?map=oregon").json()
        defensa = _por_lado(data["by_overtime_start_side"])["Defense"]
        self.assertEqual(defensa["matches"], 1)

    def test_sin_prorrogas_las_dos_filas_en_cero_y_winrate_nulo(self):
        match = make_match()
        make_round_player(make_round(match, 1, side="Attack"))
        filas = agg.by_overtime_start_side()
        self.assertEqual([(f["side"], f["matches"]) for f in filas], [("Attack", 0), ("Defense", 0)])
        self.assertTrue(all(f["winrate"] is None for f in filas))

    def test_trends_devuelve_partidas_a_prorroga_por_lado(self):
        _a_prorroga(0, ["Attack"])
        data = self.client.get("/api/trends/").json()
        self.assertEqual(
            [(f["side"], f["matches"]) for f in data["by_overtime_start_side"]],
            [("Attack", 1), ("Defense", 0)],
        )
