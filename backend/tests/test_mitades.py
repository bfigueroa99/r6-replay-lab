"""Tendencias por mitad de la partida, prorroga y lado inicial."""

from __future__ import annotations

from unittest import mock

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


_SIGUIENTE = iter(range(1000, 10000))


def _arranque(lado: str, *, map_name: str = "Bank", gano: bool | None = True,
              map_id: int = 0):
    """Partida de dos rondas que arranca en `lado`; `gano=None` es sin resultado."""
    otro = "Defense" if lado == "Attack" else "Attack"
    match = make_match(index=next(_SIGUIENTE), map_name=map_name, map_id=map_id,
                       my_score=4 if gano is not False else 2,
                       opponent_score=2 if gano is not False else 4)
    if gano is None:
        match.won = None
        match.save()
    make_round_player(make_round(match, 1, side=lado))
    make_round_player(make_round(match, 2, side=otro))
    return match


def _por_mapa(filas: list[dict]) -> dict[str, dict]:
    return {fila["map"]: fila for fila in filas}


class LadoInicialPorMapaTests(TestCase):
    def _cuatro_partidas(self):
        _arranque("Defense", gano=True)
        _arranque("Defense", gano=False)
        _arranque("Attack", gano=True)
        _arranque("Attack", map_name="Oregon", gano=False)

    def test_lado_inicial_por_mapa_cuenta_cada_mapa_por_separado(self):
        self._cuatro_partidas()
        with mock.patch.object(agg, "MIN_PARTIDAS_LADO_INICIAL", 1):
            filas = agg.by_start_side_map()
        self.assertEqual([f["map"] for f in filas], ["Bank", "Oregon"])
        bank, oregon = _por_mapa(filas)["Bank"], _por_mapa(filas)["Oregon"]
        self.assertEqual(bank["matches"], 3)
        self.assertEqual((bank["defense"]["matches"], bank["defense"]["wins"]), (2, 1))
        self.assertEqual(bank["defense"]["winrate"], 50.0)
        self.assertEqual((bank["attack"]["matches"], bank["attack"]["wins"]), (1, 1))
        self.assertEqual(bank["attack"]["winrate"], 100.0)
        self.assertEqual(bank["delta"], 50.0)
        self.assertEqual((oregon["attack"]["matches"], oregon["attack"]["winrate"]), (1, 0.0))
        self.assertEqual(oregon["defense"]["matches"], 0)
        self.assertIsNone(oregon["defense"]["winrate"])
        self.assertIsNone(oregon["verdict"])

        # con el minimo real (3) ninguna celda llega: conteos si, porcentaje no
        filas = agg.by_start_side_map()
        for fila in filas:
            self.assertIsNone(fila["attack"]["winrate"])
            self.assertIsNone(fila["defense"]["winrate"])
        self.assertEqual(_por_mapa(filas)["Bank"]["defense"]["matches"], 2)

    def test_un_lado_bajo_el_minimo_no_da_porcentaje_ni_veredicto(self):
        for gano in (True, True, False):
            _arranque("Attack", gano=gano)
        for gano in (True, False):
            _arranque("Defense", gano=gano)
        (bank,) = agg.by_start_side_map()
        self.assertEqual(bank["attack"]["winrate"], 66.7)
        self.assertEqual(bank["defense"]["matches"], 2)
        self.assertIsNone(bank["defense"]["winrate"])
        self.assertIsNone(bank["delta"])
        self.assertIsNone(bank["margin"])
        self.assertIsNone(bank["verdict"])

    def test_partida_sin_resultado_cuenta_en_partidas_y_no_en_el_porcentaje(self):
        for gano in (True, True, False, None):
            _arranque("Attack", gano=gano)
        (bank,) = agg.by_start_side_map()
        ataque = bank["attack"]
        self.assertEqual((ataque["matches"], ataque["decided"], ataque["wins"]), (4, 3, 2))
        self.assertEqual(ataque["winrate"], 66.7)

    def test_el_filtro_de_lado_no_cambia_el_lado_inicial_por_mapa(self):
        self._cuatro_partidas()
        self.assertEqual(agg.by_start_side_map(side="Attack"), agg.by_start_side_map())

    def test_las_versiones_de_un_mapa_van_en_filas_distintas(self):
        _arranque("Attack", map_name="Consulate", map_id=1)
        _arranque("Attack", map_name="Consulate", map_id=2)
        filas = agg.by_start_side_map()
        self.assertEqual(len(filas), 2)
        self.assertEqual({f["map_id"] for f in filas}, {1, 2})
        self.assertEqual(len({f["map"] for f in filas}), 2)

    def test_una_diferencia_grande_con_muestra_da_veredicto(self):
        for _ in range(8):
            _arranque("Attack", gano=True)
            _arranque("Defense", gano=False)
        (bank,) = agg.by_start_side_map()
        self.assertEqual(bank["delta"], 100.0)
        self.assertEqual(bank["verdict"], "ataque")

    def test_una_diferencia_chica_con_poca_muestra_es_ruido(self):
        for gano in (True, True, True, False):
            _arranque("Attack", gano=gano)
        for gano in (True, True, False, False):
            _arranque("Defense", gano=gano)
        (bank,) = agg.by_start_side_map()
        self.assertEqual(bank["delta"], 25.0)
        self.assertGreater(bank["margin"], 25.0)
        self.assertEqual(bank["verdict"], "ruido")

    def test_el_filtro_de_mapa_de_la_api_deja_solo_ese_mapa(self):
        self._cuatro_partidas()
        data = self.client.get("/api/trends/?map=oregon").json()
        self.assertEqual([f["map"] for f in data["by_start_side_map"]], ["Oregon"])


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
        self.assertEqual(data["by_start_side_map"], [])


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

    def test_una_ronda_sin_lado_no_es_el_cambio(self):
        _partida(["Attack", "", "Defense", "Defense"])
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

    def test_la_fila_del_cambio_es_la_primera_ronda_del_otro_lado_y_no_otra(self):
        # contar rondas no alcanza: la R6 tambien da una ronda; solo la R4 se pierde
        match = make_match()
        for numero, lado in enumerate(["Attack"] * 3 + ["Defense"] * 3, start=1):
            make_round_player(make_round(match, numero, side=lado, won=numero != 4))
        aperturas = _por_apertura(agg.by_half_opener())
        self.assertEqual(aperturas["match_start"]["winrate"], 100.0)
        self.assertEqual(aperturas["side_switch"]["winrate"], 0.0)
        self.assertEqual(aperturas["rest"]["winrate"], 100.0)
