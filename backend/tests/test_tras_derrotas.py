"""Tests del winrate de la partida siguiente segun las derrotas seguidas de la sesion."""

from __future__ import annotations

from datetime import datetime, timedelta

from django.test import TestCase

from replays.analytics import aggregates as agg
from replays.models import Match

from .factories import make_match, make_round, make_round_player

INICIO = datetime(2026, 9, 1, 20, 0)


def partidas(resultados: str, *, inicio: datetime = INICIO, desde: int = 0, mapas=None):
    """Una partida por letra (V, D, E empate, I incompleta), a 40 min una de otra."""
    creadas = []
    for i, letra in enumerate(resultados):
        mios, suyos = {"V": (4, 2), "D": (2, 4), "E": (3, 3), "I": (2, 2)}[letra]
        match = make_match(
            index=desde + i,
            played_at=inicio + timedelta(minutes=40 * i),
            map_name=mapas[i] if mapas else "Club House",
            my_score=mios,
            opponent_score=suyos,
        )
        if letra == "I":
            Match.objects.filter(id=match.id).update(won=None)
        creadas.append(match)
    return creadas


def por_racha(**filters):
    return {fila["streak"]: fila for fila in agg.by_losing_streak(**filters)}


def resumen(fila):
    return (fila["matches"], fila["decided"], fila["wins"], fila["losses"])


class TrasDerrotasTests(TestCase):
    def test_sesion_d_d_v_d_reparte_por_derrotas_previas(self):
        partidas("DDVD")
        filas = por_racha()
        # la primera (D) y la que sigue a la V (D) caen en 0
        self.assertEqual(resumen(filas[0]), (2, 2, 0, 2))
        self.assertEqual(resumen(filas[1]), (1, 1, 0, 1))
        self.assertEqual(resumen(filas[2]), (1, 1, 1, 0))
        self.assertEqual(filas[2]["winrate"], 100.0)
        self.assertEqual(resumen(filas[3]), (0, 0, 0, 0))
        self.assertIsNone(filas[3]["winrate"])

    def test_la_primera_de_la_sesion_cae_en_cero(self):
        partidas("V")
        filas = por_racha()
        self.assertEqual(resumen(filas[0]), (1, 1, 1, 0))
        self.assertEqual(sum(f["matches"] for f in filas.values()), 1)

    def test_tres_o_mas_se_juntan_en_la_ultima_fila(self):
        partidas("DDDDV")
        filas = por_racha()
        self.assertEqual(resumen(filas[3]), (2, 2, 1, 1))
        self.assertEqual(filas[3]["label"], "3+")
        self.assertEqual(filas[3]["winrate"], 50.0)

    def test_una_sesion_nueva_reinicia_la_racha(self):
        partidas("DD")
        partidas("V", inicio=INICIO + timedelta(days=1), desde=10)
        filas = por_racha()
        # la V del dia siguiente no cuenta las dos derrotas de la noche anterior
        self.assertEqual(resumen(filas[0]), (2, 2, 1, 1))
        self.assertEqual(resumen(filas[1]), (1, 1, 0, 1))
        self.assertEqual(filas[2]["matches"], 0)

    def test_incompleta_y_empate_no_suman_ni_cortan_ni_entran_al_winrate(self):
        partidas("DIEDV")
        filas = por_racha()
        # D (0), I y E (1: no suman ni cortan), D (1), V (2)
        self.assertEqual(resumen(filas[0]), (1, 1, 0, 1))
        self.assertEqual(resumen(filas[1]), (3, 1, 0, 1))
        self.assertEqual(resumen(filas[2]), (1, 1, 1, 0))
        self.assertEqual(filas[1]["winrate"], 0.0)

    def test_filtro_de_mapa_cuenta_solo_esas_pero_la_racha_es_de_todas(self):
        partidas("DDV", mapas=["Border", "Border", "Club House"])
        filas = por_racha(map="club-house")
        # la V de Club House sigue a dos derrotas en Border: el filtro no borra la racha
        self.assertEqual(resumen(filas[2]), (1, 1, 1, 0))
        self.assertEqual(filas[0]["matches"], 0)
        self.assertEqual(filas[1]["matches"], 0)

    def test_lado_operador_y_sitio_no_cambian_las_filas(self):
        for match in partidas("DDV"):
            # rondas tuyas solo de defensa, con otro operador y sitio: si el
            # filtro mirara tus rondas, estas partidas desaparecerian
            make_round_player(make_round(match, 0, side="Defense"))
        # una partida tiene los dos lados: esos filtros no eligen partidas
        sin_filtro = agg.by_losing_streak()
        self.assertEqual(sum(f["matches"] for f in sin_filtro), 3)
        self.assertEqual(agg.by_losing_streak(side="Attack"), sin_filtro)
        self.assertEqual(agg.by_losing_streak(operator="Ash"), sin_filtro)
        self.assertEqual(agg.by_losing_streak(site="1F Bar"), sin_filtro)

    def test_sin_partidas_devuelve_las_cuatro_filas_vacias(self):
        filas = agg.by_losing_streak()
        self.assertEqual([f["label"] for f in filas], ["0", "1", "2", "3+"])
        self.assertTrue(all(f["matches"] == 0 and f["winrate"] is None for f in filas))

    def test_consultas_constantes(self):
        partidas("DDVD")
        with self.assertNumQueries(3):
            agg.by_losing_streak()
        partidas("DDDDDVV", inicio=INICIO + timedelta(days=2), desde=20)
        with self.assertNumQueries(3):
            agg.by_losing_streak()

    def test_api_sessions_trae_by_losing_streak(self):
        partidas("DV")
        data = self.client.get("/api/sessions/").json()
        filas = {f["streak"]: f for f in data["by_losing_streak"]}
        self.assertEqual(resumen(filas[1]), (1, 1, 1, 0))
        self.assertEqual(len(data["by_losing_streak"]), 4)
