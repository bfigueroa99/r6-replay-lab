"""Match point: rondas que podian cerrar la partida, segun la regla de cada tipo."""

from __future__ import annotations

from unittest import mock

from django.test import SimpleTestCase, TestCase

from pydissect.constants import Y9S3, Y9S4, Y10S1
from replays.analytics import aggregates as agg
from replays.analytics import reglas_partida as rp

from .factories import make_match, make_round, make_round_player

RANKED = rp.regla_para("Ranked", Y9S4)


def _partida(marcadores: list, *, index: int = 0, team_index: int = 0,
             match_type: str = "Ranked", code_version: int = Y9S4,
             map_name: str = "Club House"):
    """Una partida con una ronda mia por cada `score_before` de la lista."""
    match = make_match(index=index, match_type=match_type, code_version=code_version,
                       map_name=map_name)
    for numero, marcador in enumerate(marcadores):
        lado = "Attack" if numero % 2 == 0 else "Defense"
        rnd = make_round(match, numero, side=lado, won=numero % 2 == 0, score_before=marcador)
        make_round_player(rnd, team_index=team_index)
    return match


def _por_estado(filas: list[dict]) -> dict[str, int]:
    return {fila["match_point"]: fila["rounds"] for fila in filas}


class ReglasTests(SimpleTestCase):
    def test_ranked_tres_a_dos_es_tu_match_point(self):
        self.assertEqual(rp.estado(3, 2, RANKED), "mine")

    def test_ranked_tres_a_tres_no_es_match_point_por_la_prorroga(self):
        self.assertEqual(rp.estado(3, 3, RANKED), "normal")

    def test_ranked_cuatro_a_tres_vuelve_a_ser_tu_match_point(self):
        self.assertEqual(rp.estado(4, 3, RANKED), "mine")

    def test_ranked_cuatro_a_cuatro_es_de_los_dos(self):
        self.assertEqual(rp.estado(4, 4, RANKED), "both")

    def test_dos_a_tres_es_match_point_rival(self):
        self.assertEqual(rp.estado(2, 3, RANKED), "theirs")

    def test_sin_prorroga_el_empate_a_uno_de_ganar_es_de_los_dos(self):
        regla = {"desde": 0, "para_ganar": 3, "prorroga_hasta": 3}
        self.assertEqual(rp.estado(2, 2, regla), "both")
        self.assertEqual(rp.estado(2, 1, regla), "mine")

    def test_los_tramos_no_traen_marcadores_de_partida_terminada(self):
        pares = [p for lista in rp.tramos(RANKED).values() for p in lista]
        self.assertNotIn((4, 0), pares)
        self.assertNotIn((4, 2), pares)
        self.assertIn((4, 3), pares)
        self.assertIn((4, 4), pares)

    def test_regla_para_toma_la_de_mayor_desde_que_aplica(self):
        reglas = {"Raro": ({"desde": 10, "para_ganar": 4, "prorroga_hasta": 5},
                           {"desde": 20, "para_ganar": 3, "prorroga_hasta": 3})}
        self.assertIsNone(rp.regla_para("Raro", 9, reglas))
        self.assertEqual(rp.regla_para("Raro", 15, reglas)["para_ganar"], 4)
        self.assertEqual(rp.regla_para("Raro", 25, reglas)["para_ganar"], 3)
        self.assertIsNone(rp.regla_para("Otro", 25, reglas))

    def test_ranked_no_tiene_regla_antes_de_y9s4(self):
        self.assertIsNone(rp.regla_para("Ranked", Y9S4 - 1))


class MatchPointTests(TestCase):
    def test_las_cinco_filas_salen_en_orden_y_suman_todas_tus_rondas(self):
        _partida([[0, 0], [1, 0], [1, 1], [2, 1], [2, 2], [3, 2], [3, 3], [4, 3], [4, 4]])
        _partida([[0, 0], [2, 3]], index=1, match_type="QuickMatch", map_name="Oregon")
        filas = agg.by_match_point()
        self.assertEqual([f["match_point"] for f in filas],
                         ["mine", "theirs", "both", "normal", "unknown"])
        self.assertEqual(
            _por_estado(filas),
            {"mine": 2, "theirs": 0, "both": 1, "normal": 6, "unknown": 2},
        )
        # los filtros recortan de verdad: Attack son las pares y Oregon solo la segunda
        for filtros, esperado in (({}, 11), ({"side": "Attack"}, 6), ({"map": "oregon"}, 2)):
            total = agg.overview(**filtros)["overall"]["rounds"]
            self.assertEqual(total, esperado, filtros)
            self.assertEqual(sum(f["rounds"] for f in agg.by_match_point(**filtros)), total)

    def test_dos_a_tres_en_ranked_es_match_point_rival(self):
        _partida([[2, 3]])
        self.assertEqual(_por_estado(agg.by_match_point())["theirs"], 1)

    def test_un_tipo_sin_regla_va_a_unknown_y_no_a_normal(self):
        _partida([[0, 0], [3, 2]], match_type="Arcade")
        self.assertEqual(
            _por_estado(agg.by_match_point()),
            {"mine": 0, "theirs": 0, "both": 0, "normal": 0, "unknown": 2},
        )

    def test_quick_match_sin_fuente_va_a_unknown(self):
        _partida([[3, 2]], match_type="QuickMatch")
        self.assertEqual(_por_estado(agg.by_match_point())["unknown"], 1)

    def test_una_partida_y9s3_va_a_unknown(self):
        _partida([[3, 2], [0, 0]], code_version=Y9S3)
        self.assertEqual(_por_estado(agg.by_match_point())["unknown"], 2)

    def test_siendo_el_equipo_uno_el_marcador_se_lee_al_reves(self):
        _partida([[2, 3], [3, 1]], team_index=1)
        self.assertEqual(
            _por_estado(agg.by_match_point()),
            {"mine": 1, "theirs": 1, "both": 0, "normal": 0, "unknown": 0},
        )

    def test_un_marcador_fuera_de_rango_cae_en_normal(self):
        # la partida ya estaba ganada: no se inventa un match point
        _partida([[4, 0]])
        self.assertEqual(_por_estado(agg.by_match_point())["normal"], 1)

    def test_con_dos_reglas_cada_partida_usa_la_de_su_version(self):
        # desordenadas a proposito: la consulta no puede depender del orden de la tupla
        reglas = {"Ranked": ({"desde": Y10S1, "para_ganar": 3, "prorroga_hasta": 3},
                             {"desde": Y9S4, "para_ganar": 4, "prorroga_hasta": 5})}
        _partida([[2, 2]], code_version=Y9S4)
        _partida([[2, 2]], index=1, code_version=Y10S1)
        with mock.patch.dict(rp.REGLAS, reglas, clear=True):
            self.assertEqual(
                _por_estado(agg.by_match_point()),
                {"mine": 0, "theirs": 0, "both": 1, "normal": 1, "unknown": 0},
            )

    def test_marcador_vacio_va_a_unknown(self):
        _partida([[], [1]])
        self.assertEqual(_por_estado(agg.by_match_point())["unknown"], 2)


class MatchPointApiTests(TestCase):
    def test_base_vacia_y_filtros_raros_dan_cinco_filas_en_cero(self):
        for url in ("/api/trends/", "/api/trends/?days=-1", "/api/trends/?until=foo"):
            respuesta = self.client.get(url)
            self.assertEqual(respuesta.status_code, 200, url)
            filas = respuesta.json()["by_match_point"]
            self.assertEqual([f["rounds"] for f in filas], [0, 0, 0, 0, 0], url)

    def test_trends_con_datos_trae_el_match_point(self):
        _partida([[3, 2], [3, 3]])
        filas = self.client.get("/api/trends/").json()["by_match_point"]
        self.assertEqual(_por_estado(filas)["mine"], 1)
        self.assertEqual(_por_estado(filas)["normal"], 1)
