"""Tests de las sesiones de juego y la curva de fatiga."""

from __future__ import annotations

from datetime import datetime, timedelta

from django.test import TestCase

from replays.analytics import aggregates as agg
from replays.analytics.coach import build_insights

from .factories import make_match, make_round, make_round_player

INICIO = datetime(2026, 9, 1, 20, 0)


def find(payload, key):
    return next((i for i in payload["insights"] if i["key"] == key), None)


def partida(indice: int, cuando: datetime, *, rondas: int = 4, ganadas: int = 2):
    match = make_match(
        index=indice, played_at=cuando, my_score=ganadas, opponent_score=rondas - ganadas
    )
    for n in range(rondas):
        rnd = make_round(match, n, won=n < ganadas)
        make_round_player(rnd, kills=1 if n < ganadas else 0)
    return match


class CorteDeSesionTests(TestCase):
    def test_una_pausa_larga_corta_la_sesion(self):
        partida(0, INICIO)
        partida(1, INICIO + timedelta(minutes=40))
        partida(2, INICIO + timedelta(hours=5))  # al otro rato: sesion nueva

        sesiones = agg.sessions()
        self.assertEqual(len(sesiones), 2)
        # la mas reciente primero
        self.assertEqual(sesiones[0]["matches"], 1)
        self.assertEqual(sesiones[1]["matches"], 2)
        self.assertEqual(sesiones[0]["index"], 0)

    def test_el_gap_es_configurable(self):
        partida(0, INICIO)
        partida(1, INICIO + timedelta(hours=3))
        self.assertEqual(len(agg.sessions()), 2)
        with self.settings(SESSION_GAP_MINUTES=240):
            self.assertEqual(len(agg.sessions()), 1)

    def test_posicion_dentro_de_la_sesion(self):
        for i in range(3):
            partida(i, INICIO + timedelta(minutes=40 * i))
        filas = {r["position"]: r for r in agg.by_session_position()}
        self.assertEqual(sorted(filas), [1, 2, 3])
        self.assertEqual(filas[1]["matches"], 1)

    def test_las_posiciones_altas_se_juntan(self):
        for i in range(7):
            partida(i, INICIO + timedelta(minutes=40 * i))
        filas = {r["label"]: r for r in agg.by_session_position(max_position=5)}
        self.assertIn("5a+", filas)
        self.assertEqual(filas["5a+"]["matches"], 3)  # la 5a, 6a y 7a

    def test_la_sesion_se_calcula_sobre_todo_el_historial(self):
        """Filtrar por mapa no cambia que esa partida fue la segunda de la noche."""
        partida(0, INICIO)
        match = partida(1, INICIO + timedelta(minutes=40))
        match.map_name, match.map_slug = "Villa", "villa"
        match.save()

        filas = agg.by_session_position(map="villa")
        self.assertEqual(len(filas), 1)
        self.assertEqual(filas[0]["position"], 2)

    def test_filtro_por_sesion(self):
        partida(0, INICIO)
        partida(1, INICIO + timedelta(hours=5), rondas=6)
        self.assertEqual(agg.base_queryset(session=0).count(), 6)
        self.assertEqual(agg.base_queryset(session=1).count(), 4)
        self.assertEqual(agg.base_queryset(session="").count(), 10)
        self.assertEqual(agg.base_queryset(session=99).count(), 0)
        self.assertEqual(agg.base_queryset(session="no-es-un-numero").count(), 0)

    def test_promedio_ponderado_no_promedia_promedios(self):
        """avg_death_elapsed se pondera por muertes, no se promedia plano."""
        match = make_match(index=0, played_at=INICIO)
        rnd = make_round(match, 0)
        make_round_player(rnd, death_elapsed=30.0)
        rnd2 = make_round(match, 1)
        make_round_player(rnd2, death_elapsed=90.0)

        otra = make_match(index=1, played_at=INICIO + timedelta(minutes=40))
        make_round_player(make_round(otra, 0), death_elapsed=150.0)

        fila = agg.sessions()[0]
        self.assertEqual(fila["avg_death_elapsed"], 90.0)  # (30 + 90 + 150) / 3

    def test_sin_datos_no_revienta(self):
        self.assertEqual(agg.sessions(), [])
        self.assertEqual(agg.by_session_position(), [])
        self.assertEqual(agg.session_options(), [])


class SesionesApiTests(TestCase):
    def setUp(self):
        for i in range(3):
            partida(i, INICIO + timedelta(minutes=40 * i))

    def test_endpoint(self):
        data = self.client.get("/api/sessions/").json()
        self.assertEqual(data["gap_minutes"], 120)
        self.assertEqual(len(data["sessions"]), 1)
        self.assertEqual(len(data["by_position"]), 3)

    def test_filtros_trae_las_sesiones(self):
        data = self.client.get("/api/filters/").json()
        self.assertEqual(data["sessions"][0]["matches"], 3)

    def test_el_filtro_de_sesion_llega_a_los_agregados(self):
        data = self.client.get("/api/overview/?session=0").json()
        self.assertEqual(data["overall"]["matches"], 3)


class CoachFatigaTests(TestCase):
    def _sesion_que_decae(self, *, tardias_ganadas=0):
        """Sesiones de 4 partidas: las dos primeras buenas, las dos ultimas malas."""
        indice = 0
        for sesion in range(5):
            base = INICIO + timedelta(days=sesion)
            for posicion in range(4):
                ganadas = 4 if posicion < 2 else tardias_ganadas
                partida(indice, base + timedelta(minutes=40 * posicion), rondas=4, ganadas=ganadas)
                indice += 1

    def test_avisa_de_la_caida(self):
        self._sesion_que_decae()
        insight = find(build_insights(), "fatiga-sesion")
        self.assertIsNotNone(insight)
        self.assertEqual(insight["value"], 0.0)
        self.assertEqual(insight["baseline"], 100.0)
        self.assertEqual(insight["sample"], 40)

    def test_no_avisa_si_no_hay_caida(self):
        self._sesion_que_decae(tardias_ganadas=4)
        self.assertIsNone(find(build_insights(), "fatiga-sesion"))

    def test_no_opina_con_pocas_rondas(self):
        for posicion in range(4):
            partida(posicion, INICIO + timedelta(minutes=40 * posicion), ganadas=4 if posicion < 2 else 0)
        self.assertIsNone(find(build_insights(), "fatiga-sesion"))
