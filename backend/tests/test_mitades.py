"""Tendencias por mitad de la partida, prorroga y lado inicial."""

from __future__ import annotations

from django.test import TestCase

from replays.analytics import aggregates as agg

from .factories import make_match, make_round, make_round_player


def _partida(lados: list[str], *, index: int = 0, map_name: str = "Club House",
             prorroga: int = 0, primera: int = 1, my_score: int = 4,
             opponent_score: int = 2):
    """Una partida con una ronda mia por lado de la lista, mas las de prorroga."""
    match = make_match(index=index, map_name=map_name, my_score=my_score,
                       opponent_score=opponent_score)
    numero = primera
    for lado in lados:
        make_round_player(make_round(match, numero, side=lado))
        numero += 1
    for ot in range(1, prorroga + 1):
        make_round_player(make_round(match, numero, side="Attack", overtime_number=ot))
        numero += 1
    return match


def _por_mitad(filas: list[dict]) -> dict[str, dict]:
    return {fila["half"]: fila for fila in filas}


class MitadesTests(TestCase):
    def test_seis_rondas_y_dos_de_prorroga_dan_tres_tres_y_dos(self):
        _partida(["Attack"] * 3 + ["Defense"] * 3, prorroga=2)
        filas = agg.by_half()
        self.assertEqual([f["half"] for f in filas], ["first", "second", "overtime"])
        self.assertEqual([f["rounds"] for f in filas], [3, 3, 2])

    def test_el_lado_inicial_sale_de_la_ronda_mas_baja_aunque_no_sea_la_uno(self):
        # la ronda 0 y la 1 tienen lados distintos: exigir number=1 daria Attack
        _partida(["Defense", "Attack", "Attack"], primera=0)
        mitades = _por_mitad(agg.by_half())
        self.assertEqual(mitades["first"]["rounds"], 1)
        self.assertEqual(mitades["second"]["rounds"], 2)

    def test_una_mitad_sin_rondas_sale_con_cero_y_metricas_nulas(self):
        _partida(["Attack"] * 3 + ["Defense"] * 3)
        prorroga = _por_mitad(agg.by_half())["overtime"]
        self.assertEqual(prorroga["rounds"], 0)
        self.assertIsNone(prorroga["winrate"])
        self.assertIsNone(prorroga["rating"])

    def test_ronda_sin_lado_no_cae_en_la_segunda_mitad(self):
        _partida(["Attack", "Attack", ""])
        mitades = _por_mitad(agg.by_half())
        self.assertEqual(mitades["first"]["rounds"], 2)
        self.assertEqual(mitades["second"]["rounds"], 0)

    def test_el_filtro_de_lado_no_cambia_el_lado_inicial(self):
        _partida(["Attack"] * 3 + ["Defense"] * 3)
        mitades = _por_mitad(agg.by_half(side="Defense"))
        self.assertEqual(mitades["first"]["rounds"], 0)
        self.assertEqual(mitades["second"]["rounds"], 3)


class LadoInicialTests(TestCase):
    def test_lado_inicial_cuenta_partidas_y_winrate_de_partida(self):
        _partida(["Attack", "Defense"], index=0, my_score=4, opponent_score=2)
        _partida(["Attack", "Defense"], index=1, my_score=2, opponent_score=4)
        _partida(["Defense", "Attack"], index=2, my_score=4, opponent_score=3)
        ataque, defensa = agg.by_start_side()
        self.assertEqual(ataque["side"], "Attack")
        self.assertEqual((ataque["matches"], ataque["winrate"]), (2, 50.0))
        self.assertEqual(defensa["side"], "Defense")
        self.assertEqual((defensa["matches"], defensa["winrate"]), (1, 100.0))

    def test_partida_sin_lado_en_la_primera_ronda_no_cuenta_para_el_lado_inicial(self):
        _partida(["", "Attack", "Defense"])
        ataque, defensa = agg.by_start_side()
        self.assertEqual(ataque["matches"], 0)
        self.assertEqual(defensa["matches"], 0)
        mitades = _por_mitad(agg.by_half())
        self.assertEqual(mitades["first"]["rounds"] + mitades["second"]["rounds"], 0)

    def test_partida_sin_resultado_cuenta_pero_no_entra_al_winrate(self):
        match = _partida(["Attack", "Defense"])
        match.won = None
        match.save()
        ataque, _ = agg.by_start_side()
        self.assertEqual(ataque["matches"], 1)
        self.assertEqual(ataque["decided"], 0)
        self.assertIsNone(ataque["winrate"])


class TendenciasApiTests(TestCase):
    def test_el_filtro_de_mapa_cambia_el_conteo_por_mitad(self):
        _partida(["Attack"] * 3 + ["Defense"] * 3, index=0, map_name="Club House")
        _partida(["Defense"] * 2 + ["Attack"] * 2, index=1, map_name="Oregon")
        data = self.client.get("/api/trends/?map=oregon").json()
        mitades = _por_mitad(data["by_half"])
        self.assertEqual(mitades["first"]["rounds"], 2)
        self.assertEqual(mitades["second"]["rounds"], 2)
        ataque, defensa = data["by_start_side"]
        self.assertEqual((ataque["matches"], defensa["matches"]), (0, 1))

    def test_trends_sin_datos_devuelve_las_filas_vacias_sin_500(self):
        respuesta = self.client.get("/api/trends/")
        self.assertEqual(respuesta.status_code, 200)
        data = respuesta.json()
        self.assertEqual([f["rounds"] for f in data["by_half"]], [0, 0, 0])
        self.assertEqual([f["side"] for f in data["by_start_side"]], ["Attack", "Defense"])
        self.assertTrue(all(f["matches"] == 0 for f in data["by_start_side"]))


def _por_apertura(filas: list[dict]) -> dict[str, dict]:
    return {fila["opener"]: fila for fila in filas}


class PrimeraRondaTests(TestCase):
    def test_seis_rondas_con_cambio_en_la_cuatro_dan_uno_uno_y_cuatro(self):
        _partida(["Attack"] * 3 + ["Defense"] * 3)
        filas = agg.by_half_opener()
        self.assertEqual([f["opener"] for f in filas], ["match_start", "side_switch", "rest"])
        self.assertEqual([f["rounds"] for f in filas], [1, 1, 4])

    def test_la_prorroga_no_cae_en_ninguna_fila(self):
        _partida(["Attack"] * 3 + ["Defense"] * 3, prorroga=2)
        self.assertEqual([f["rounds"] for f in agg.by_half_opener()], [1, 1, 4])

    def test_el_filtro_de_lado_no_cambia_cual_es_la_primera(self):
        _partida(["Attack"] * 3 + ["Defense"] * 3)
        self.assertEqual([f["rounds"] for f in agg.by_half_opener(side="Defense")], [0, 1, 2])

    def test_una_partida_sin_cambio_de_lado_suma_al_resto(self):
        _partida(["Attack"] * 5)
        aperturas = _por_apertura(agg.by_half_opener())
        self.assertEqual(aperturas["match_start"]["rounds"], 1)
        self.assertEqual(aperturas["side_switch"]["rounds"], 0)
        self.assertEqual(aperturas["rest"]["rounds"], 4)

    def test_la_primera_ronda_es_la_mas_baja_aunque_no_sea_la_uno(self):
        _partida(["Defense", "Attack", "Attack"], primera=0)
        self.assertEqual([f["rounds"] for f in agg.by_half_opener()], [1, 1, 1])

    def test_una_partida_sin_lado_inicial_no_aporta(self):
        _partida(["", "", ""])
        self.assertEqual([f["rounds"] for f in agg.by_half_opener()], [0, 0, 0])

    def test_base_vacia_da_tres_filas_en_cero(self):
        filas = agg.by_half_opener()
        self.assertEqual([f["rounds"] for f in filas], [0, 0, 0])
        self.assertTrue(all(f["winrate"] is None for f in filas))

    def test_trends_trae_by_half_opener_en_orden_fijo(self):
        _partida(["Attack"] * 3 + ["Defense"] * 3)
        respuesta = self.client.get("/api/trends/?side=Defense")
        self.assertEqual(respuesta.status_code, 200)
        filas = respuesta.json()["by_half_opener"]
        self.assertEqual([f["opener"] for f in filas], ["match_start", "side_switch", "rest"])
        self.assertEqual([f["rounds"] for f in filas], [0, 1, 2])
