"""Records personales: tus mejores marcas, cada una con su partida."""

from __future__ import annotations

from datetime import datetime

from django.test import TestCase

from replays.analytics import aggregates as agg

from .factories import make_match, make_round, make_round_player


def _partida(bajas: list[int], *, index: int = 0, map_name: str = "Club House",
             played_at: datetime | None = None, ganadas: int | None = None,
             one_vx: dict[int, int] | None = None):
    """Una partida con una ronda mia por cada elemento de `bajas`.

    `ganadas` dice cuantas de las primeras rondas gana tu equipo (todas si es
    None); `one_vx` mapea numero de ronda a la X del clutch.
    """
    match = make_match(index=index, map_name=map_name, played_at=played_at)
    for numero, kills in enumerate(bajas):
        gano = ganadas is None or numero < ganadas
        rnd = make_round(match, numero, won=gano)
        make_round_player(rnd, kills=kills, died=kills == 0,
                          one_vx=(one_vx or {}).get(numero, 0))
    return match


class RecordsTests(TestCase):
    def test_mejor_rating_ignora_partidas_de_menos_de_seis_rondas(self):
        # la corta tiene mejor rating por ronda, pero no llega al minimo
        _partida([5, 5, 5], index=0)
        larga = _partida([1, 1, 0, 1, 2, 1], index=1)
        record = agg.personal_records()["best_match_rating"]
        self.assertEqual(record["match_id"], larga.id)
        self.assertEqual(record["rounds"], 6)
        self.assertIsNotNone(record["value"])

    def test_mas_bajas_en_una_partida_trae_su_match_id(self):
        _partida([1, 1], index=0)
        mejor = _partida([2, 3, 1], index=1, map_name="Oregon")
        record = agg.personal_records()["most_kills_match"]
        self.assertEqual(record["match_id"], mejor.id)
        self.assertEqual(record["value"], 6)
        self.assertEqual(record["map"], "Oregon")
        self.assertEqual(record["played_at"], mejor.played_at.isoformat())

    def test_mas_bajas_en_una_ronda_trae_la_etiqueta_de_la_ronda(self):
        _partida([1, 1, 4, 0], index=0)
        record = agg.personal_records()["most_kills_round"]
        self.assertEqual(record["value"], 4)
        self.assertEqual(record["round_label"], "R3")

    def test_el_clutch_mas_grande_es_el_1vx_ganado_mayor(self):
        _partida([1, 1, 1], index=0, one_vx={0: 2, 2: 3})
        # un 1v4 perdido no es un clutch ganado
        _partida([1, 1], index=1, ganadas=0, one_vx={1: 4})
        record = agg.personal_records()["biggest_clutch"]
        self.assertEqual(record["value"], 3)
        self.assertEqual(record["round_label"], "R3")

    def test_mejor_dia_exige_el_minimo_de_rondas_y_no_trae_partida(self):
        # dia 1: 4 de 4 ganadas, no llega al minimo; dia 2: 15 de 20
        _partida([1] * 4, index=0, played_at=datetime(2026, 9, 1, 20, 0))
        _partida([1] * 10, index=1, played_at=datetime(2026, 9, 2, 20, 0), ganadas=8)
        _partida([1] * 10, index=2, played_at=datetime(2026, 9, 2, 22, 0), ganadas=7)
        record = agg.personal_records()["best_day"]
        self.assertEqual(record["day"], "2026-09-02")
        self.assertEqual(record["value"], 75.0)
        self.assertEqual((record["rounds"], record["rounds_won"]), (20, 15))
        self.assertNotIn("match_id", record)

    def test_en_un_empate_gana_la_partida_mas_reciente(self):
        _partida([2, 2, 1, 1, 1, 1], index=0, played_at=datetime(2026, 9, 1, 20, 0))
        nueva = _partida([2, 2, 1, 1, 1, 1], index=1, played_at=datetime(2026, 9, 3, 20, 0))
        _partida([2, 2, 1, 1, 1, 1], index=2, played_at=datetime(2026, 9, 2, 20, 0))
        records = agg.personal_records()
        self.assertEqual(records["most_kills_match"]["match_id"], nueva.id)
        self.assertEqual(records["best_match_rating"]["match_id"], nueva.id)
        self.assertEqual(records["most_kills_round"]["match_id"], nueva.id)

    def test_el_filtro_de_mapa_cambia_el_record_de_bajas(self):
        _partida([5, 5], index=0, map_name="Club House")
        oregon = _partida([1, 2], index=1, map_name="Oregon")
        self.assertEqual(agg.personal_records()["most_kills_match"]["value"], 10)
        record = agg.personal_records(map="oregon")["most_kills_match"]
        self.assertEqual((record["match_id"], record["value"]), (oregon.id, 3))

    def test_base_vacia_devuelve_todos_los_records_nulos(self):
        self.assertEqual(
            agg.personal_records(),
            dict.fromkeys(
                ("best_match_rating", "most_kills_match", "most_kills_round",
                 "biggest_clutch", "best_day"),
                None,
            ),
        )

    def test_sin_clutches_el_record_de_clutch_es_nulo_y_los_demas_no(self):
        _partida([1, 2, 1, 1, 0, 1], index=0)
        records = agg.personal_records()
        self.assertIsNone(records["biggest_clutch"])
        self.assertIsNone(records["best_day"])
        for clave in ("best_match_rating", "most_kills_match", "most_kills_round"):
            self.assertIsNotNone(records[clave], clave)

    def test_sin_bajas_no_inventa_un_record_de_cero(self):
        _partida([0, 0, 0], index=0)
        records = agg.personal_records()
        self.assertIsNone(records["most_kills_match"])
        self.assertIsNone(records["most_kills_round"])


class RecordsApiTests(TestCase):
    def test_overview_trae_los_records(self):
        match = _partida([1, 3, 1], index=0)
        records = self.client.get("/api/overview/").json()["records"]
        self.assertEqual(records["most_kills_match"]["match_id"], match.id)
        self.assertEqual(records["most_kills_round"]["round_label"], "R2")

    def test_base_vacia_y_filtros_raros_dan_200_con_records_nulos(self):
        for url in ("/api/overview/", "/api/overview/?since=foo", "/api/overview/?map=%00",
                    "/api/overview/?side=Defense"):
            respuesta = self.client.get(url)
            self.assertEqual(respuesta.status_code, 200, url)
            self.assertIsNone(respuesta.json()["records"]["most_kills_match"], url)
