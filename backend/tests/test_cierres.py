"""Como se cierran tus rondas: por eliminacion o sin ella, por lado."""

from __future__ import annotations

from django.test import TestCase

from replays.analytics import aggregates as agg
from replays.models import Round

from .factories import make_match, make_round, make_round_player


def _ronda(match, numero: int, *, lado: str = "Attack", gano: bool | None = True,
           condicion: str = "KilledOpponents"):
    """Una ronda mia con el ganador y la condicion de cierre dados."""
    rnd = make_round(match, numero, side=lado, won=bool(gano))
    Round.objects.filter(pk=rnd.pk).update(
        my_team_won=gano,
        win_condition=condicion,
        win_condition_certain=condicion != "ObjectiveOrTime",
    )
    rnd.refresh_from_db()
    # como la ingesta: `won` es False cuando la ronda no tiene ganador
    make_round_player(rnd, won=bool(gano))
    return rnd


def _por_lado(filas: list[dict]) -> dict[str, dict]:
    return {fila["side"]: fila for fila in filas}


CUENTAS = ("won_elimination", "won_other", "lost_elimination", "lost_other", "unknown")


class CierresTests(TestCase):
    def test_una_ronda_ganada_por_eliminacion_en_ataque_suma_solo_ahi(self):
        _ronda(make_match(), 0, lado="Attack", gano=True)
        filas = _por_lado(agg.round_endings())
        self.assertEqual(
            {clave: filas["Attack"][clave] for clave in CUENTAS},
            {"won_elimination": 1, "won_other": 0, "lost_elimination": 0,
             "lost_other": 0, "unknown": 0},
        )
        self.assertEqual(filas["Attack"]["rounds"], 1)
        self.assertEqual({clave: filas["Defense"][clave] for clave in CUENTAS},
                         dict.fromkeys(CUENTAS, 0))

    def test_las_dos_filas_salen_en_orden_fijo_aunque_una_este_vacia(self):
        self.assertEqual([f["side"] for f in agg.round_endings()], ["Attack", "Defense"])
        _ronda(make_match(), 0, lado="Defense")
        filas = agg.round_endings()
        self.assertEqual([f["side"] for f in filas], ["Attack", "Defense"])
        self.assertEqual([f["rounds"] for f in filas], [0, 1])

    def test_ganada_y_perdida_sin_eliminacion_van_a_other(self):
        match = make_match()
        _ronda(match, 0, lado="Defense", gano=True, condicion="ObjectiveOrTime")
        _ronda(match, 1, lado="Defense", gano=False, condicion="ObjectiveOrTime")
        defensa = _por_lado(agg.round_endings())["Defense"]
        self.assertEqual((defensa["won_other"], defensa["lost_other"]), (1, 1))
        self.assertEqual((defensa["won_elimination"], defensa["lost_elimination"]), (0, 0))
        self.assertEqual(defensa["won_elimination_pct"], 0.0)

    def test_sin_ganador_o_sin_condicion_va_a_unknown(self):
        match = make_match()
        _ronda(match, 0, gano=None)
        _ronda(match, 1, gano=True, condicion="")
        ataque = _por_lado(agg.round_endings())["Attack"]
        self.assertEqual(ataque["unknown"], 2)
        self.assertEqual(ataque["rounds"], 2)
        # `won` de RoundPlayer es False sin ganador: no tiene que contar como perdida
        self.assertEqual(ataque["lost_elimination"], 0)

    def test_cada_fila_suma_todas_tus_rondas_de_ese_lado(self):
        match = make_match()
        casos = [
            (True, "KilledOpponents"), (True, "ObjectiveOrTime"),
            (False, "KilledOpponents"), (False, "ObjectiveOrTime"),
            (None, "KilledOpponents"), (True, ""),
        ]
        for numero, (gano, condicion) in enumerate(casos):
            for desfase, lado in ((0, "Attack"), (10, "Defense")):
                _ronda(match, numero + desfase, lado=lado, gano=gano, condicion=condicion)
        for fila in agg.round_endings():
            self.assertEqual(sum(fila[clave] for clave in CUENTAS), fila["rounds"], fila["side"])
            self.assertEqual(fila["rounds"], 6)
            self.assertEqual(fila["unknown"], 2)
        self.assertEqual(sum(f["rounds"] for f in agg.round_endings()),
                         agg.overview()["overall"]["rounds"])

    def test_la_respuesta_no_trae_claves_de_plant_ni_de_defuse(self):
        _ronda(make_match(), 0, gano=True, condicion="ObjectiveOrTime")
        filas = self.client.get("/api/trends/").json()["round_endings"]
        self.assertEqual(len(filas), 2)
        for fila in filas:
            for clave in fila:
                self.assertNotIn("plant", clave.lower())
                self.assertNotIn("defuse", clave.lower())

    def test_el_filtro_de_mapa_deja_solo_las_rondas_de_ese_mapa(self):
        _ronda(make_match(index=0, map_name="Club House"), 0, gano=True)
        oregon = make_match(index=1, map_name="Oregon")
        _ronda(oregon, 0, gano=False, condicion="ObjectiveOrTime")
        _ronda(oregon, 1, gano=False, condicion="ObjectiveOrTime")
        ataque = _por_lado(agg.round_endings(map="oregon"))["Attack"]
        self.assertEqual(ataque["rounds"], 2)
        self.assertEqual(ataque["lost_other"], 2)
        self.assertEqual(ataque["won_elimination"], 0)
        filas = self.client.get("/api/trends/?map=oregon").json()["round_endings"]
        self.assertEqual(_por_lado(filas)["Attack"]["lost_other"], 2)

    def test_los_porcentajes_son_nulos_sin_rondas_ganadas_o_perdidas(self):
        match = make_match()
        _ronda(match, 0, gano=True)
        _ronda(match, 1, gano=True, condicion="ObjectiveOrTime")
        _ronda(match, 2, gano=True)
        _ronda(match, 3, gano=True)
        ataque = _por_lado(agg.round_endings())["Attack"]
        self.assertEqual(ataque["won_elimination_pct"], 75.0)
        self.assertIsNone(ataque["lost_elimination_pct"])
        defensa = _por_lado(agg.round_endings())["Defense"]
        self.assertIsNone(defensa["won_elimination_pct"])
        self.assertIsNone(defensa["lost_elimination_pct"])


class CierresApiTests(TestCase):
    def test_base_vacia_y_filtros_raros_dan_200_con_dos_filas_en_cero(self):
        for url in ("/api/trends/", "/api/trends/?since=foo", "/api/trends/?side=Attack",
                    "/api/trends/?map=%00"):
            respuesta = self.client.get(url)
            self.assertEqual(respuesta.status_code, 200, url)
            filas = respuesta.json()["round_endings"]
            self.assertEqual([f["side"] for f in filas], ["Attack", "Defense"], url)
            self.assertEqual([f["rounds"] for f in filas], [0, 0], url)
