"""Rondas que tu equipo gano sin ti: caiste y la ronda igual fue tuya, y quien seguia vivo."""

from __future__ import annotations

from django.test import TestCase

from replays.analytics import aggregates as agg

from .factories import make_match, make_round, make_round_player

_indice = iter(range(10_000))


def partidas_juntas(nicks: tuple[str, ...], cuantas: int = agg.MIN_PARTIDAS_HABITUAL) -> None:
    """Partidas de una ronda que sobreviviste con `nicks` en tu equipo: los vuelve habituales."""
    for _ in range(cuantas):
        match = make_match(index=next(_indice))
        rnd = make_round(match, 1)
        make_round_player(rnd, died=False)
        for nick in nicks:
            make_round_player(rnd, username=nick, is_me=False)


def ronda(*, caiste: bool = True, won: bool | None = True, side: str = "Attack",
          vivos: tuple[str, ...] = (), muertos: tuple[str, ...] = (),
          rivales_vivos: tuple[str, ...] = (), map_name: str = "Clubhouse"):
    """Una ronda en una partida nueva; `vivos` y `muertos` son companeros de tu equipo."""
    match = make_match(index=next(_indice), map_name=map_name)
    rnd = make_round(match, 1, side=side, won=bool(won))
    if won is None:
        rnd.my_team_won = None
        rnd.save()
    make_round_player(rnd, died=caiste, won=bool(won))
    for nick in vivos:
        make_round_player(rnd, username=nick, is_me=False, died=False, won=bool(won))
    for nick in muertos:
        make_round_player(rnd, username=nick, is_me=False, died=True, won=bool(won))
    otro = "Defense" if side == "Attack" else "Attack"
    for nick in rivales_vivos:
        make_round_player(rnd, username=nick, is_me=False, team_index=1, died=False,
                          side=otro, won=not bool(won))
    return rnd


def por_lado(data: dict) -> dict[str, dict]:
    return {f["side"]: f for f in data["sides"]}


def por_nombre(data: dict) -> dict[str, dict]:
    return {f["username"]: f for f in data["mates"]}


class GanadasSinTiTests(TestCase):
    def test_cuenta_las_rondas_en_que_caiste_y_cuantas_gano_tu_equipo_por_lado(self):
        ronda(side="Attack", won=True)
        ronda(side="Attack", won=False)
        ronda(side="Attack", won=False)
        ronda(side="Defense", won=True)
        lados = por_lado(agg.won_without_me())
        self.assertEqual(
            (lados["Attack"]["rounds"], lados["Attack"]["won"], lados["Attack"]["pct"]),
            (3, 1, 33.3),
        )
        self.assertEqual(
            (lados["Defense"]["rounds"], lados["Defense"]["won"], lados["Defense"]["pct"]),
            (1, 1, 100.0),
        )

    def test_una_ronda_en_que_sobreviviste_no_cuenta(self):
        ronda(caiste=False, won=True)
        self.assertEqual(por_lado(agg.won_without_me())["total"]["rounds"], 0)

    def test_una_ronda_sin_ganador_no_cuenta(self):
        ronda(won=None)
        total = por_lado(agg.won_without_me())["total"]
        self.assertEqual((total["rounds"], total["pct"]), (0, None))

    def test_la_fila_total_suma_los_dos_lados(self):
        ronda(side="Attack", won=True)
        ronda(side="Defense", won=False)
        ronda(side="Defense", won=True)
        data = agg.won_without_me()
        self.assertEqual([f["side"] for f in data["sides"]], ["Attack", "Defense", "total"])
        total = por_lado(data)["total"]
        self.assertEqual((total["rounds"], total["won"], total["pct"]), (3, 2, 66.7))

    def test_cuenta_que_companero_habitual_seguia_vivo(self):
        partidas_juntas(("Seba", "Nico"))
        ronda(won=True, vivos=("Seba",), muertos=("Nico",))
        ronda(won=True, vivos=("Seba", "Nico"))
        ronda(won=True, muertos=("Seba", "Nico"))
        data = agg.won_without_me()
        self.assertEqual([f["username"] for f in data["mates"]], ["Seba", "Nico"])
        seba, nico = data["mates"]
        self.assertEqual((seba["rounds"], seba["survived"], seba["pct"]), (3, 2, 66.7))
        self.assertEqual((nico["rounds"], nico["survived"], nico["pct"]), (3, 1, 33.3))

    def test_un_companero_no_habitual_no_sale(self):
        partidas_juntas(("Seba",))
        partidas_juntas(("Random",), cuantas=agg.MIN_PARTIDAS_HABITUAL - 2)
        ronda(won=True, vivos=("Seba", "Random"))
        self.assertEqual(list(por_nombre(agg.won_without_me())), ["Seba"])

    def test_un_rival_que_sobrevive_no_cuenta(self):
        partidas_juntas(("Seba",))
        # el rival juega todas tus partidas pero nunca en tu equipo: no es habitual
        for _ in range(agg.MIN_PARTIDAS_HABITUAL):
            ronda(won=True, vivos=("Seba",), rivales_vivos=("Rival",))
        self.assertEqual(list(por_nombre(agg.won_without_me())), ["Seba"])

    def test_una_ronda_perdida_no_suma_al_companero(self):
        partidas_juntas(("Seba",))
        ronda(won=False, vivos=("Seba",))
        self.assertEqual(agg.won_without_me()["mates"], [])

    def test_con_filtro_de_lado_sale_ese_lado_y_el_total(self):
        ronda(side="Attack", won=True)
        ronda(side="Defense", won=False)
        data = agg.won_without_me(side="Defense")
        self.assertEqual([f["side"] for f in data["sides"]], ["Defense", "total"])
        total = por_lado(data)["total"]
        self.assertEqual((total["rounds"], total["won"]), (1, 0))

    def test_el_filtro_de_mapa_va_sobre_tu_fila(self):
        partidas_juntas(("Seba",))
        ronda(won=True, vivos=("Seba",), map_name="Clubhouse")
        ronda(won=True, vivos=("Seba",), map_name="Oregon")
        data = agg.won_without_me(map="oregon")
        self.assertEqual(por_lado(data)["total"]["rounds"], 1)
        self.assertEqual(por_nombre(data)["Seba"]["rounds"], 1)

    def test_marca_muestra_chica_debajo_de_cinco_rondas(self):
        partidas_juntas(("Seba",))
        for _ in range(agg.GANADA_SIN_TI_MIN - 1):
            ronda(won=True, vivos=("Seba",))
        self.assertTrue(por_nombre(agg.won_without_me())["Seba"]["low_sample"])
        ronda(won=True, vivos=("Seba",))
        data = agg.won_without_me()
        self.assertFalse(por_nombre(data)["Seba"]["low_sample"])
        self.assertEqual(data["min_rounds"], agg.GANADA_SIN_TI_MIN)

    def test_teammates_devuelve_ganadas_sin_ti(self):
        ronda(won=True)
        payload = self.client.get("/api/teammates/").json()
        self.assertEqual(payload["won_without_me"]["sides"][-1]["rounds"], 1)
        self.assertEqual(payload["won_without_me"]["mates"], [])

