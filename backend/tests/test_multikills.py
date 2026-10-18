"""Multikills por tamano: rondas de 2, 3 y 4 bajas y aces."""

from __future__ import annotations

from django.test import SimpleTestCase, TestCase

from replays import views
from replays.analytics import aggregates as agg
from replays.models import Player

from .factories import make_match, make_round, make_round_player

CLAVES = ("k2", "k3", "k4", "aces", "multikill_rounds")


def _conteos(fila: dict) -> dict:
    return {clave: fila[clave] for clave in CLAVES}


class MultikillsTests(TestCase):
    def setUp(self):
        self.match = make_match()
        # tus rondas: 0, 2, 3, 4, 5 y 6 bajas; ataque las pares, defensa las impares
        for numero, bajas in enumerate((0, 2, 3, 4, 5, 6)):
            lado = "Attack" if numero % 2 == 0 else "Defense"
            rnd = make_round(self.match, numero, side=lado)
            make_round_player(rnd, kills=bajas)
            make_round_player(rnd, username="amigo", is_me=False, kills=2 if numero == 0 else 0)
            make_round_player(rnd, username="rival", is_me=False, team_index=1, side="Defense",
                              kills=1)

    def _scoreboard(self) -> dict[str, dict]:
        return {f["username"]: f for f in views._match_scoreboard(self.match)}

    def test_el_scoreboard_cuenta_rondas_por_tamano_y_seis_es_ace(self):
        yo = self._scoreboard()["BearF99"]
        self.assertEqual(_conteos(yo), {"k2": 1, "k3": 1, "k4": 1, "aces": 2,
                                        "multikill_rounds": 5})
        # el alias `kills` del scoreboard sigue siendo la suma
        self.assertEqual(yo["kills"], 20)

    def test_el_scoreboard_no_mezcla_jugadores(self):
        filas = self._scoreboard()
        self.assertEqual(_conteos(filas["amigo"]), {"k2": 1, "k3": 0, "k4": 0, "aces": 0,
                                                    "multikill_rounds": 1})
        self.assertEqual(_conteos(filas["rival"]), dict.fromkeys(CLAVES, 0))

    def test_los_cuatro_tamanos_suman_multikill_rounds(self):
        for fila in self._scoreboard().values():
            self.assertEqual(fila["k2"] + fila["k3"] + fila["k4"] + fila["aces"],
                             fila["multikill_rounds"])

    def test_totals_trae_los_cuatro_conteos(self):
        fila = agg.totals(agg.base_queryset())
        self.assertEqual(_conteos(fila), {"k2": 1, "k3": 1, "k4": 1, "aces": 2,
                                          "multikill_rounds": 5})

    def test_overview_trae_los_conteos_en_overall_y_por_lado(self):
        datos = agg.overview()
        self.assertEqual(datos["overall"]["aces"], 2)
        # ataque: 0, 3 y 5 bajas; defensa: 2, 4 y 6
        self.assertEqual(_conteos(datos["attack"]), {"k2": 0, "k3": 1, "k4": 0, "aces": 1,
                                                     "multikill_rounds": 2})
        self.assertEqual(_conteos(datos["defense"]), {"k2": 1, "k3": 0, "k4": 1, "aces": 1,
                                                      "multikill_rounds": 3})

    def test_el_perfil_trae_los_conteos_del_jugador_en_theirs(self):
        amigo = Player.objects.get(username="amigo")
        perfil = agg.player_profile(amigo.pk)
        self.assertEqual(perfil["theirs"]["k2"], 1)
        self.assertEqual(perfil["theirs"]["multikill_rounds"], 1)

    def test_el_filtro_de_lado_recorta_los_conteos(self):
        fila = agg.totals(agg.base_queryset(side="Attack"))
        self.assertEqual(fila["k3"], 1)
        self.assertEqual(fila["k2"], 0)
        self.assertEqual(fila["k4"], 0)

    def test_group_by_mapa_trae_los_conteos(self):
        [fila] = agg.group_by(agg.base_queryset(), "round__match__map_name", labels=("map",))
        self.assertEqual(fila["map"], "Club House")
        self.assertEqual(fila["aces"], 2)

    def test_multikill_pct_no_cambia(self):
        fila = agg.totals(agg.base_queryset())
        self.assertEqual(fila["multikill_pct"], round(5 / 6 * 100, 1))


class DeriveMultikillsTests(SimpleTestCase):
    def test_derive_sin_las_claves_las_deja_en_cero(self):
        fila = agg.derive({"rounds": 3})
        self.assertEqual(_conteos(fila), dict.fromkeys(CLAVES, 0))
