"""Remontadas y derrumbes: partidas que se dieron vuelta y winrate segun el marcador al cambio de lado."""

from __future__ import annotations

from django.test import SimpleTestCase, TestCase

from pydissect.constants import Y9S3, Y9S4
from replays.analytics import aggregates as agg
from replays.models import Match

from .factories import make_match, make_round, make_round_player


def _partida(marcadores: list, *, index: int = 0, ganada: bool = True, team_index: int = 0,
             code_version: int = Y9S4, map_name: str = "Club House", lados: list | None = None):
    """Una partida con una ronda mia por cada `score_before` de la lista.

    Por defecto la primera mitad es de ataque y la segunda de defensa, con el
    cambio en la mitad de las rondas.
    """
    mio, suyo = (4, 2) if ganada else (2, 4)
    match = make_match(index=index, code_version=code_version, map_name=map_name,
                       my_score=mio, opponent_score=suyo)
    mitad = (len(marcadores) + 1) // 2
    for numero, marcador in enumerate(marcadores):
        lado = lados[numero] if lados else ("Attack" if numero < mitad else "Defense")
        rnd = make_round(match, numero, side=lado, score_before=marcador)
        make_round_player(rnd, team_index=team_index)
    return match


def _por_tramo(datos: dict) -> dict[str, tuple[int, int]]:
    return {f["diff"]: (f["matches"], f["wins"]) for f in datos["by_side_change_diff"]}


class MarcadorDeRondaTests(SimpleTestCase):
    def test_team_index_0_lee_el_marcador_en_orden(self):
        self.assertEqual(agg._marcador_de_ronda([1, 3], 0), (1, 3))

    def test_marcador_vacio_o_de_tres_equipos_es_ilegible(self):
        self.assertIsNone(agg._marcador_de_ronda([], 0))
        self.assertIsNone(agg._marcador_de_ronda([1, 2, 0], 0))
        self.assertIsNone(agg._marcador_de_ronda([1, 2], 2))
        self.assertIsNone(agg._marcador_de_ronda(None, 0))


class RemontadasTests(TestCase):
    def test_ganada_que_estuvo_1_3_es_remontada_con_desventaja_2(self):
        m = _partida([[0, 0], [0, 1], [1, 1], [1, 2], [1, 3], [2, 3], [3, 3]])
        datos = agg.comebacks()
        self.assertEqual(len(datos["remontadas"]), 1)
        item = datos["remontadas"][0]
        self.assertEqual(item["match_id"], m.id)
        self.assertEqual(item["max_deficit"], 2)
        self.assertEqual(item["score"], "4-2")
        self.assertEqual(item["map"], "Club House")
        self.assertEqual(datos["remontadas_total"], 1)
        self.assertEqual(datos["derrumbes"], [])

    def test_ganada_que_nunca_estuvo_abajo_por_2_no_entra(self):
        _partida([[0, 0], [0, 1], [1, 1], [1, 2], [2, 2], [3, 2]])
        datos = agg.comebacks()
        self.assertEqual(datos["remontadas"], [])
        self.assertEqual(datos["matches_known"], 1)

    def test_perdida_que_estuvo_3_1_es_derrumbe(self):
        _partida([[0, 0], [1, 0], [2, 0], [2, 1], [3, 1], [3, 2], [3, 3]], ganada=False)
        datos = agg.comebacks()
        self.assertEqual(len(datos["derrumbes"]), 1)
        self.assertEqual(datos["derrumbes"][0]["max_lead"], 2)
        self.assertEqual(datos["derrumbes"][0]["score"], "2-4")
        self.assertEqual(datos["remontadas"], [])

    def test_perdida_que_nunca_estuvo_arriba_por_2_no_entra(self):
        _partida([[0, 0], [1, 0], [1, 1], [1, 2], [2, 2], [2, 3]], ganada=False)
        self.assertEqual(agg.comebacks()["derrumbes"], [])

    def test_el_marcador_antes_de_la_ultima_ronda_cuenta(self):
        # 3-1 recien antes de la ultima ronda: ya es un derrumbe de 2.
        _partida([[0, 0], [1, 0], [1, 1], [2, 1], [3, 1]], ganada=False)
        self.assertEqual(agg.comebacks()["derrumbes"][0]["max_lead"], 2)

    def test_una_ronda_que_falta_saca_la_partida(self):
        # Sin la ronda 2 (el 0-2) la desventaja maxima pareceria 1.
        m = make_match(index=0)
        for numero, marcador in ((0, [0, 0]), (1, [0, 1]), (3, [1, 2]), (4, [2, 2])):
            make_round_player(make_round(m, numero, score_before=marcador))
        datos = agg.comebacks()
        self.assertEqual(datos["matches_known"], 0)
        self.assertEqual(sum(n for n, _ in _por_tramo(datos).values()), 0)

    def test_partida_anterior_a_y9s4_no_aparece_en_nada(self):
        _partida([[0, 0], [0, 1], [0, 2], [1, 2], [2, 2], [3, 2]], code_version=Y9S3)
        _partida([[0, 0], [0, 1], [0, 2], [1, 2], [2, 2], [3, 2]], index=1)
        datos = agg.comebacks()
        self.assertEqual(datos["matches_known"], 1)
        self.assertEqual(datos["remontadas_total"], 1)
        self.assertEqual(sum(n for n, _ in _por_tramo(datos).values()), 1)

    def test_partida_con_marcador_de_tres_equipos_no_aparece(self):
        _partida([[0, 0, 0], [0, 1, 0], [0, 2, 0], [1, 2, 0]])
        datos = agg.comebacks()
        self.assertEqual(datos["matches_known"], 0)
        self.assertEqual(datos["remontadas"], [])

    def test_una_ronda_ilegible_en_el_medio_saca_la_partida(self):
        _partida([[0, 0], [0, 1], [], [1, 3], [2, 3], [3, 3]])
        self.assertEqual(agg.comebacks()["matches_known"], 0)

    def test_team_index_1_lee_el_marcador_al_reves(self):
        # Visto desde el equipo 0 va 3-1, pero tu eres el equipo 1: ibas 1-3.
        _partida([[0, 0], [1, 0], [2, 0], [3, 1], [3, 2], [3, 3]], team_index=1)
        datos = agg.comebacks()
        self.assertEqual(datos["remontadas"][0]["max_deficit"], 2)

    def test_partida_sin_resultado_no_entra(self):
        m = _partida([[0, 0], [0, 1], [0, 2], [1, 2], [2, 2], [3, 2]])
        Match.objects.filter(pk=m.pk).update(won=None)
        datos = agg.comebacks()
        self.assertEqual(datos["remontadas"], [])
        self.assertEqual(datos["matches_known"], 0)
        self.assertEqual(sum(n for n, _ in _por_tramo(datos).values()), 0)

    def test_orden_mayor_diferencia_primero_y_despues_la_mas_reciente(self):
        a = _partida([[0, 0], [0, 1], [0, 2], [1, 2], [2, 2], [3, 2]], index=0)
        b = _partida([[0, 0], [0, 1], [0, 2], [0, 3], [1, 3], [2, 3]], index=1)
        c = _partida([[0, 0], [0, 1], [0, 2], [1, 2], [2, 2], [3, 2]], index=2)
        ids = [p["match_id"] for p in agg.comebacks()["remontadas"]]
        self.assertEqual(ids, [b.id, c.id, a.id])

    def test_la_lista_tiene_tope_pero_el_total_cuenta_todo(self):
        for i in range(agg.TOPE_LISTA + 2):
            _partida([[0, 0], [0, 1], [0, 2], [1, 2]], index=i)
        datos = agg.comebacks()
        self.assertEqual(len(datos["remontadas"]), agg.TOPE_LISTA)
        self.assertEqual(datos["remontadas_total"], agg.TOPE_LISTA + 2)

    def test_diferencia_al_cambio_de_lado_por_tramo(self):
        # Seis rondas por mitad: el marcador de la ronda 6 es el del cambio.
        def con_cambio(mio, suyo, index, ganada):
            antes = [[0, 0]] * 6
            return _partida(antes + [[mio, suyo]] * 6, index=index, ganada=ganada)

        con_cambio(6, 0, 0, True)    # +6 -> +2
        con_cambio(4, 2, 1, False)   # +2
        con_cambio(3, 2, 2, True)    # +1
        con_cambio(3, 3, 3, True)    # 0
        con_cambio(2, 3, 4, False)   # -1
        con_cambio(1, 5, 5, True)    # -4 -> -2
        tramos = _por_tramo(agg.comebacks())
        self.assertEqual(list(tramos), list(agg.TRAMOS_CAMBIO))
        self.assertEqual(tramos, {"+2": (2, 1), "+1": (1, 1), "0": (1, 1),
                                  "-1": (1, 0), "-2": (1, 1)})
        filas = {f["diff"]: f for f in agg.comebacks()["by_side_change_diff"]}
        self.assertEqual(filas["+2"]["winrate"], 50.0)

    def test_el_lado_inicial_sale_de_la_ronda_mas_baja(self):
        # Arranca en defensa y numera desde 0, como `seed_demo`.
        _partida([[0, 0], [1, 0], [2, 0], [2, 1]],
                 lados=["Defense", "Defense", "Attack", "Attack"])
        self.assertEqual(_por_tramo(agg.comebacks())["+2"], (1, 1))

    def test_partida_sin_segunda_mitad_no_entra_a_la_tabla(self):
        _partida([[0, 0], [0, 1], [0, 2], [1, 2]], lados=["Attack"] * 4)
        datos = agg.comebacks()
        self.assertEqual(datos["matches_known"], 1)
        self.assertEqual(datos["remontadas_total"], 1)
        self.assertEqual(sum(n for n, _ in _por_tramo(datos).values()), 0)

    def test_respeta_el_filtro_de_mapa(self):
        _partida([[0, 0], [0, 1], [0, 2], [1, 2]], index=0, map_name="Club House")
        _partida([[0, 0], [0, 1], [0, 2], [1, 2]], index=1, map_name="Oregon")
        datos = agg.comebacks(map="oregon")
        self.assertEqual([p["map"] for p in datos["remontadas"]], ["Oregon"])
        self.assertEqual(datos["matches_known"], 1)

    def test_el_filtro_de_lado_no_corta_la_partida(self):
        # La desventaja fue en defensa; con ?side=Attack la partida se lee entera.
        _partida([[0, 0], [0, 1], [0, 2], [1, 2]], lados=["Defense", "Defense", "Attack", "Attack"])
        self.assertEqual(agg.comebacks(side="Attack")["remontadas"][0]["max_deficit"], 2)


class RemontadasApiTests(TestCase):
    def test_trends_trae_comebacks_con_base_vacia(self):
        respuesta = self.client.get("/api/trends/")
        self.assertEqual(respuesta.status_code, 200)
        datos = respuesta.json()["comebacks"]
        self.assertEqual(datos["remontadas"], [])
        self.assertEqual(datos["derrumbes"], [])
        self.assertEqual(datos["matches_known"], 0)
        self.assertEqual([f["matches"] for f in datos["by_side_change_diff"]], [0] * 5)

    def test_trends_con_filtros_raros_da_200(self):
        _partida([[0, 0], [0, 1], [0, 2], [1, 2]])
        for url in ("/api/trends/?until=foo", "/api/trends/?session=-1",
                    "/api/trends/?days=-1", "/api/trends/?map="):
            respuesta = self.client.get(url)
            self.assertEqual(respuesta.status_code, 200, url)
            self.assertIn("comebacks", respuesta.json(), url)

    def test_trends_con_datos_trae_la_remontada(self):
        m = _partida([[0, 0], [0, 1], [0, 2], [1, 2]])
        datos = self.client.get("/api/trends/").json()["comebacks"]
        self.assertEqual(datos["remontadas"][0]["match_id"], m.id)
