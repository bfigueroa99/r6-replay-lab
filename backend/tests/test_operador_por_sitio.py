"""Operador por sitio contra el resto de tus operadores ahi (ficha 93)."""

from __future__ import annotations

from django.test import TestCase

from replays.analytics import aggregates as agg

from .factories import make_match, make_round, make_round_player

SITIO_A = "A Bedroom, A Gym"
SITIO_B = "B Church, B Arsenal Room"
CONSULATE_Y7 = 2609221242
CONSULATE_Y10 = 418126004176

_indices = iter(range(10_000))


def rondas(operador: str, n: int, ganadas: int, *, site: str = SITIO_A, side: str = "Attack",
           map_name: str = "Club House", map_id: int = 0, sin_ganador: int = 0):
    """`n` rondas con `operador`, las primeras `ganadas` ganadas.

    `sin_ganador` agrega rondas con `my_team_won` nulo. Cada tanda va en su
    propia partida para no chocar con el numero de ronda.
    """
    match = make_match(map_name=map_name, map_id=map_id, index=next(_indices))
    for i in range(n):
        rnd = make_round(match, i, side=side, site=site, won=i < ganadas)
        make_round_player(rnd, side=side, operator=operador)
    for i in range(sin_ganador):
        rnd = make_round(match, n + i, side=side, site=site, won=None)
        # sin `won` explicito la factory copiaria el None a RoundPlayer.won
        make_round_player(rnd, side=side, operator=operador, won=False)


def pedir(client, **params) -> dict:
    resp = client.get("/api/operators/sites/", params)
    assert resp.status_code == 200, resp.content
    return resp.json()


def fila(datos: dict, operador: str, **extra) -> dict | None:
    return next(
        (
            f for f in datos["rows"]
            if f["operator"] == operador and all(f[k] == v for k, v in extra.items())
        ),
        None,
    )


class OperadorPorSitioTests(TestCase):
    def test_un_operador_que_gana_mas_que_el_resto_del_sitio_rinde(self):
        rondas("Ash", 20, 20)
        rondas("Zofia", 20, 4)
        datos = pedir(self.client)
        ash, zofia = fila(datos, "Ash"), fila(datos, "Zofia")
        self.assertEqual(ash["verdict"], "rinde")
        self.assertEqual(ash["winrate_delta"], 80.0)
        self.assertEqual(zofia["verdict"], "hunde")
        self.assertEqual(zofia["winrate_delta"], -80.0)
        self.assertEqual(datos["min_rounds"], agg.OPERADOR_SITIO_MIN_RONDAS)
        self.assertEqual(datos["bands"], agg.POSICION_BANDAS)
        # mayor |delta| primero; a igual delta, mas rondas y despues nombre
        self.assertEqual([f["operator"] for f in datos["rows"]], ["Ash", "Zofia"])

    def test_una_diferencia_chica_es_ruido(self):
        rondas("Ash", 20, 11)
        rondas("Zofia", 20, 10)
        ash = fila(pedir(self.client), "Ash")
        self.assertEqual(ash["winrate_delta"], 5.0)
        self.assertEqual(ash["verdict"], "ruido")
        self.assertGreater(ash["margin"], 5.0)

    def test_compara_contra_el_resto_y_no_contra_el_total(self):
        rondas("Ash", 10, 8)
        rondas("Zofia", 10, 2)
        rondas("Thatcher", 10, 5)
        ash = fila(pedir(self.client), "Ash")
        self.assertEqual(ash["rounds"], 10)
        self.assertEqual(ash["rounds_won"], 8)
        self.assertEqual(ash["winrate"], 80.0)
        self.assertEqual(ash["rest_rounds"], 20)
        # resto = Zofia + Thatcher = 7/20; contra el total (15/30) daria 30
        self.assertEqual(ash["rest_winrate"], 35.0)
        self.assertEqual(ash["winrate_delta"], 45.0)

    def test_sin_muestra_del_operador_o_del_resto_no_hay_fila(self):
        rondas("Ash", 9, 5)
        rondas("Zofia", 20, 10)
        datos = pedir(self.client)
        self.assertIsNone(fila(datos, "Ash"))
        # Zofia tiene 20 pero su resto (Ash) solo 9
        self.assertIsNone(fila(datos, "Zofia"))
        datos = pedir(self.client, min_rounds=5)
        self.assertEqual(datos["min_rounds"], 5)
        self.assertIsNotNone(fila(datos, "Ash"))
        self.assertIsNotNone(fila(datos, "Zofia"))

    def test_las_rondas_sin_ganador_no_cuentan(self):
        rondas("Ash", 10, 10, sin_ganador=4)
        rondas("Zofia", 10, 5, sin_ganador=3)
        ash = fila(pedir(self.client), "Ash")
        self.assertEqual(ash["rounds"], 10)
        self.assertEqual(ash["winrate"], 100.0)
        self.assertEqual(ash["rest_rounds"], 10)
        self.assertEqual(ash["rest_winrate"], 50.0)

    def test_rondas_sin_sitio_lado_u_operador_quedan_fuera(self):
        rondas("Ash", 10, 10)
        rondas("Zofia", 10, 0)
        # sin sitio, en tandas de 10: sin el exclude formarian su propia fila
        rondas("Ash", 10, 0, site="")
        rondas("Zofia", 10, 10, site="")
        rondas("", 5, 5)
        # tandas de 10 para que, sin el exclude, pasen el minimo y se vean
        rondas("Zofia", 10, 10, side="")
        rondas("Ash", 10, 0, side="")
        datos = pedir(self.client)
        self.assertEqual({f["site"] for f in datos["rows"]}, {SITIO_A})
        self.assertNotIn("", {f["operator"] for f in datos["rows"]})
        self.assertEqual({f["side"] for f in datos["rows"]}, {"Attack"})
        ash = fila(datos, "Ash")
        self.assertEqual(ash["rounds"], 10)
        self.assertEqual(ash["rest_rounds"], 10)

    def test_otro_lado_u_otro_sitio_no_es_el_resto(self):
        rondas("Ash", 10, 10)
        rondas("Zofia", 10, 0)
        rondas("Zofia", 30, 30, site=SITIO_B)
        rondas("Mute", 30, 30, side="Defense")
        ash = fila(pedir(self.client), "Ash", site=SITIO_A)
        self.assertEqual(ash["rest_rounds"], 10)
        self.assertEqual(ash["rest_winrate"], 0.0)

    def test_las_versiones_de_un_mapa_van_separadas(self):
        for map_id in (CONSULATE_Y7, CONSULATE_Y10):
            rondas("Ash", 10, 10, map_name="Consulate", map_id=map_id)
            rondas("Zofia", 10, 0, map_name="Consulate", map_id=map_id)
        datos = pedir(self.client)
        ash = [f for f in datos["rows"] if f["operator"] == "Ash"]
        self.assertEqual(len(ash), 2)
        self.assertEqual({f["map_id"] for f in ash}, {CONSULATE_Y7, CONSULATE_Y10})
        self.assertEqual(len({f["map"] for f in ash}), 2)
        for f in ash:
            self.assertEqual(f["slug"], "consulate")
            self.assertEqual(f["rest_rounds"], 10)

    def test_el_filtro_de_operador_no_vacia_el_resto(self):
        rondas("Ash", 10, 10)
        rondas("Zofia", 10, 0)
        rondas("Thatcher", 10, 5)
        datos = pedir(self.client, operator="Ash")
        self.assertEqual([f["operator"] for f in datos["rows"]], ["Ash"])
        self.assertEqual(datos["rows"][0]["rest_rounds"], 20)

    def test_respeta_el_filtro_de_lado(self):
        rondas("Ash", 10, 10)
        rondas("Zofia", 10, 0)
        rondas("Mute", 10, 10, side="Defense")
        rondas("Jager", 10, 0, side="Defense")
        datos = pedir(self.client, side="Defense")
        self.assertEqual({f["side"] for f in datos["rows"]}, {"Defense"})
        self.assertEqual({f["operator"] for f in datos["rows"]}, {"Mute", "Jager"})

    def test_respeta_el_filtro_de_mapa(self):
        rondas("Ash", 10, 10)
        rondas("Zofia", 10, 0)
        rondas("Ash", 10, 10, map_name="Kanal")
        rondas("Zofia", 10, 0, map_name="Kanal")
        datos = pedir(self.client, map="kanal")
        self.assertEqual({f["slug"] for f in datos["rows"]}, {"kanal"})

    def test_sin_rondas_devuelve_lista_vacia(self):
        datos = pedir(self.client)
        self.assertEqual(datos["rows"], [])
        self.assertEqual(datos["min_rounds"], 10)

    def test_solo_acepta_get(self):
        self.assertEqual(self.client.post("/api/operators/sites/").status_code, 405)
