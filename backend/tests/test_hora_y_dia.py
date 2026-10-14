"""Tendencias por hora del dia y por dia de la semana del inicio de la partida."""

from __future__ import annotations

from datetime import datetime

from django.test import TestCase

from replays.analytics import aggregates as agg

from .factories import make_match, make_round, make_round_player


def _partida(played_at: datetime, *, index: int = 0, rondas: int = 1,
             map_name: str = "Club House", side: str = "Attack") -> None:
    """Una partida con `rondas` rondas mias, todas ganadas las pares."""
    match = make_match(index=index, played_at=played_at, map_name=map_name)
    for numero in range(rondas):
        rnd = make_round(match, numero, side=side, won=numero % 2 == 0)
        make_round_player(rnd)


def _rondas(filas: list[dict], campo: str) -> dict[int, int]:
    return {fila[campo]: fila["rounds"] for fila in filas}


class HoraYDiaTests(TestCase):
    def test_ocho_franjas_fijas_aunque_no_haya_rondas(self):
        filas = agg.by_hour()
        self.assertEqual([f["hour_from"] for f in filas], [0, 3, 6, 9, 12, 15, 18, 21])
        self.assertEqual([f["rounds"] for f in filas], [0] * 8)

    def test_siete_dias_fijos_de_lunes_a_domingo(self):
        filas = agg.by_weekday()
        self.assertEqual([f["weekday"] for f in filas], [1, 2, 3, 4, 5, 6, 7])
        self.assertEqual([f["rounds"] for f in filas], [0] * 7)

    def test_domingo_23_30_y_lunes_00_30_caen_en_su_dia_y_su_franja(self):
        # 2026-09-06 es domingo
        _partida(datetime(2026, 9, 6, 23, 30), index=0, rondas=2)
        _partida(datetime(2026, 9, 7, 0, 30), index=1, rondas=3)
        por_dia = _rondas(agg.by_weekday(), "weekday")
        por_hora = _rondas(agg.by_hour(), "hour_from")
        self.assertEqual(por_dia[7], 2)
        self.assertEqual(por_dia[1], 3)
        self.assertEqual(por_hora[21], 2)
        self.assertEqual(por_hora[0], 3)
        self.assertEqual(sum(por_dia.values()), 5)
        self.assertEqual(sum(por_hora.values()), 5)

    def test_el_borde_de_la_franja_es_la_hora_de_inicio(self):
        _partida(datetime(2026, 9, 8, 2, 59), index=0)
        _partida(datetime(2026, 9, 8, 3, 0), index=1)
        por_hora = _rondas(agg.by_hour(), "hour_from")
        self.assertEqual(por_hora[0], 1)
        self.assertEqual(por_hora[3], 1)

    def test_cada_fila_trae_las_metricas_de_siempre(self):
        _partida(datetime(2026, 9, 9, 20, 0), rondas=4)
        fila = next(f for f in agg.by_hour() if f["hour_from"] == 18)
        self.assertEqual(fila["rounds"], 4)
        self.assertEqual(fila["winrate"], 50.0)
        for clave in ("rating", "kpr", "opening_winrate"):
            self.assertIn(clave, fila)

    def test_las_filas_suman_las_rondas_del_resumen(self):
        for i, hora in enumerate((1, 5, 8, 11, 14, 17, 20, 23)):
            _partida(datetime(2026, 9, 1 + i, hora, 15), index=i, rondas=i + 1,
                     map_name="Club House" if i % 2 else "Bank",
                     side="Defense" if i % 3 == 0 else "Attack")
        for filtros in ({}, {"map": "bank"}, {"side": "Attack"}):
            total = agg.overview(**filtros)["overall"]["rounds"]
            self.assertEqual(sum(f["rounds"] for f in agg.by_hour(**filtros)), total, filtros)
            self.assertEqual(sum(f["rounds"] for f in agg.by_weekday(**filtros)), total, filtros)
        self.assertEqual(sum(f["rounds"] for f in agg.by_hour()), 36)
        # los filtros tienen que recortar de verdad, si no la suma no prueba nada
        self.assertEqual(agg.overview(map="bank")["overall"]["rounds"], 16)
        self.assertEqual(agg.overview(side="Attack")["overall"]["rounds"], 36 - 1 - 4 - 7)


class HoraYDiaApiTests(TestCase):
    def test_base_vacia_y_filtros_raros_dan_200(self):
        for url in ("/api/trends/", "/api/trends/?days=-1", "/api/trends/?since=foo",
                    "/api/trends/?map=%00", "/api/trends/?until=foo"):
            respuesta = self.client.get(url)
            self.assertEqual(respuesta.status_code, 200, url)
            datos = respuesta.json()
            self.assertEqual(len(datos["by_hour"]), 8, url)
            self.assertEqual(len(datos["by_weekday"]), 7, url)
            self.assertEqual(sum(f["rounds"] for f in datos["by_hour"]), 0, url)

    def test_trends_con_datos_trae_hora_y_dia(self):
        _partida(datetime(2026, 9, 6, 23, 30), rondas=2)
        datos = self.client.get("/api/trends/").json()
        self.assertEqual(_rondas(datos["by_hour"], "hour_from")[21], 2)
        self.assertEqual(_rondas(datos["by_weekday"], "weekday")[7], 2)
