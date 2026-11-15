"""El sitio con el que abres la defensa: la primera ronda de defensa de cada partida."""

from __future__ import annotations

from django.test import TestCase

from replays.analytics import aggregates as agg

from .factories import make_match, make_round, make_round_player

URL = "/api/positioning/defense-opener/"


def _partida(index, rondas, *, map_name="Club House", sin_mi_fila=()):
    """Una partida; `rondas` es una lista de (numero, lado, sitio, ganada) con `ganada` None sin ganador.

    Los numeros que no estan en la lista no existen (hueco de `.rec`); los de
    `sin_mi_fila` existen como `Round` pero sin tu fila.
    """
    match = make_match(map_name=map_name, index=index)
    for numero, lado, sitio, ganada in rondas:
        rnd = make_round(match, numero, side=lado, site=sitio, won=bool(ganada))
        if ganada is None:
            rnd.my_team_won = None
            rnd.save()
        if numero not in sin_mi_fila:
            make_round_player(rnd, side=lado, won=bool(ganada))
    return match


def _mapa(data, nombre):
    return next(m for m in data["maps"] if m["map"] == nombre)


def _sitio(data, nombre, sitio):
    return next(s for s in _mapa(data, nombre)["sites"] if s["site"] == sitio)


class AperturaDefensaTests(TestCase):
    def test_tres_partidas_una_con_hueco_dan_dos_aperturas(self):
        _partida(0, [(0, "Defense", "A", True), (1, "Defense", "A", False), (2, "Attack", "", True)])
        _partida(1, [(0, "Attack", "", True), (1, "Defense", "B", False), (2, "Defense", "A", True)])
        # falta la ronda 1: no se sabe si la defensa empezo ahi
        _partida(2, [(0, "Attack", "", True), (2, "Defense", "A", True)])
        data = agg.defense_opener()
        self.assertEqual(data["matches"], 2)
        self.assertEqual(data["skipped"], 1)
        a = _sitio(data, "Club House", "A")
        self.assertEqual((a["opens"], a["opens_decided"], a["opens_won"], a["opens_winrate"]),
                         (1, 1, 1, 100.0))
        # el resto de A: la ronda 1 de la partida 0, la 2 de la 1 y la defensa de la del hueco
        self.assertEqual((a["rest_rounds"], a["rest_decided"], a["rest_won"], a["rest_winrate"]),
                         (3, 3, 2, 66.7))
        b = _sitio(data, "Club House", "B")
        self.assertEqual((b["opens"], b["opens_winrate"], b["rest_rounds"], b["rest_winrate"]),
                         (1, 0.0, 0, None))

    def test_la_apertura_es_la_primera_defensa_aunque_arranques_en_ataque(self):
        _partida(0, [(0, "Attack", "", True), (1, "Attack", "", True), (2, "Defense", "C", True),
                     (3, "Defense", "D", True)])
        data = agg.defense_opener()
        self.assertEqual(_sitio(data, "Club House", "C")["opens"], 1)
        self.assertEqual(_sitio(data, "Club House", "D")["opens"], 0)
        self.assertEqual(_sitio(data, "Club House", "D")["rest_rounds"], 1)

    def test_sin_tu_fila_de_la_primera_ronda_no_hay_apertura(self):
        _partida(0, [(0, "Defense", "A", True), (1, "Defense", "A", True)], sin_mi_fila=(0,))
        data = agg.defense_opener()
        self.assertEqual((data["matches"], data["skipped"]), (0, 1))
        a = _sitio(data, "Club House", "A")
        self.assertEqual((a["opens"], a["rest_rounds"]), (0, 1))

    def test_una_ronda_sin_lado_antes_corta_la_apertura(self):
        _partida(0, [(0, "", "", True), (1, "Defense", "A", True)])
        data = agg.defense_opener()
        self.assertEqual((data["matches"], data["skipped"]), (0, 1))
        self.assertEqual(_sitio(data, "Club House", "A")["rest_rounds"], 1)

    def test_una_apertura_sin_sitio_no_entra_y_su_defensa_tampoco(self):
        _partida(0, [(0, "Defense", "", True), (1, "Defense", "A", True)])
        data = agg.defense_opener()
        self.assertEqual((data["matches"], data["skipped"]), (0, 1))
        a = _sitio(data, "Club House", "A")
        self.assertEqual((a["opens"], a["rest_rounds"]), (0, 1))
        self.assertEqual([s["site"] for s in _mapa(data, "Club House")["sites"]], ["A"])

    def test_una_apertura_sin_ganador_cuenta_y_no_entra_al_winrate(self):
        _partida(0, [(0, "Defense", "A", None)])
        _partida(1, [(0, "Defense", "A", True)])
        a = _sitio(agg.defense_opener(), "Club House", "A")
        self.assertEqual((a["opens"], a["opens_decided"], a["opens_won"], a["opens_winrate"]),
                         (2, 1, 1, 100.0))

    def test_el_resto_es_el_mismo_sitio_sin_las_aperturas(self):
        _partida(0, [(0, "Defense", "A", False), (1, "Defense", "A", True), (2, "Defense", "B", True),
                     (3, "Defense", "A", None)])
        data = agg.defense_opener()
        a = _sitio(data, "Club House", "A")
        self.assertEqual((a["opens"], a["opens_winrate"]), (1, 0.0))
        self.assertEqual((a["rest_rounds"], a["rest_decided"], a["rest_won"], a["rest_winrate"]),
                         (2, 1, 1, 100.0))
        self.assertEqual(_sitio(data, "Club House", "B")["rest_rounds"], 1)

    def test_el_porcentaje_de_aperturas_es_sobre_las_del_mapa(self):
        _partida(0, [(0, "Defense", "A", True)])
        _partida(1, [(0, "Defense", "A", True)])
        _partida(2, [(0, "Defense", "B", True)])
        _partida(3, [(0, "Defense", "Z", True)], map_name="Border")
        data = agg.defense_opener()
        self.assertEqual(_mapa(data, "Club House")["opens_total"], 3)
        self.assertEqual(_sitio(data, "Club House", "A")["opens_share"], 66.7)
        self.assertEqual(_sitio(data, "Club House", "B")["opens_share"], 33.3)
        self.assertEqual(_sitio(data, "Border", "Z")["opens_share"], 100.0)
        # mapas por aperturas, sitios por aperturas
        self.assertEqual([m["map"] for m in data["maps"]], ["Club House", "Border"])
        self.assertEqual([s["site"] for s in _mapa(data, "Club House")["sites"]], ["A", "B"])

    def test_un_mapa_sin_aperturas_sale_con_su_resto_y_sin_porcentaje(self):
        _partida(0, [(0, "Attack", "", True), (2, "Defense", "A", True)])
        data = agg.defense_opener()
        mapa = _mapa(data, "Club House")
        self.assertEqual(mapa["opens_total"], 0)
        self.assertEqual((mapa["sites"][0]["opens"], mapa["sites"][0]["opens_share"]), (0, None))

    def test_el_filtro_de_mapa_aplica_y_el_de_lado_no(self):
        _partida(0, [(0, "Attack", "", True), (1, "Defense", "A", True)])
        _partida(1, [(0, "Defense", "Z", False)], map_name="Border")
        data = agg.defense_opener(map="border")
        self.assertEqual(data["matches"], 1)
        self.assertEqual([m["map"] for m in data["maps"]], ["Border"])
        # con el lado de la barra en ataque la apertura de defensa sigue saliendo
        data = agg.defense_opener(side="Attack", operator="Ash", site="otro")
        self.assertEqual(data["matches"], 2)
        self.assertEqual(_sitio(data, "Club House", "A")["opens"], 1)

    def test_sin_partidas_devuelve_vacio(self):
        data = agg.defense_opener()
        self.assertEqual(data, {"min_matches": agg.APERTURA_DEFENSA_MIN_PARTIDAS, "matches": 0,
                                "skipped": 0, "maps": []})

    def test_consultas_constantes(self):
        _partida(0, [(0, "Defense", "A", True)])
        _partida(1, [(0, "Attack", "", True), (1, "Defense", "B", True)])
        with self.assertNumQueries(2):
            agg.defense_opener()
        for i in range(2, 6):
            _partida(i, [(0, "Defense", "A", True), (1, "Defense", "B", False)])
        with self.assertNumQueries(2):
            agg.defense_opener()

    def test_api_defense_opener_responde_con_filtros(self):
        _partida(0, [(0, "Defense", "A", True)])
        _partida(1, [(0, "Defense", "Z", True)], map_name="Border")
        resp = self.client.get(URL, {"map": "club-house", "side": "Attack"})
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["matches"], 1)
        self.assertEqual(data["min_matches"], agg.APERTURA_DEFENSA_MIN_PARTIDAS)
        self.assertEqual(data["maps"][0]["sites"][0]["site"], "A")
