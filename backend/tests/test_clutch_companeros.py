"""Clutches de tus companeros: quien queda ultimo vivo contigo y cuantas convierte."""

from __future__ import annotations

from django.test import TestCase

from replays.analytics import aggregates as agg

from .factories import ME, make_match, make_round, make_round_player

_indice = iter(range(10_000))


def partidas_juntas(nicks: tuple[str, ...], cuantas: int = agg.MIN_PARTIDAS_HABITUAL) -> None:
    """Partidas de una ronda con vos y `nicks` en tu equipo, sin clutches: los vuelve habituales."""
    for _ in range(cuantas):
        match = make_match(index=next(_indice))
        rnd = make_round(match, 1)
        make_round_player(rnd)
        for nick in nicks:
            make_round_player(rnd, username=nick, is_me=False)


def ronda_de_clutch(clutch: dict[str, int], *, won: bool | None = True, side: str = "Attack",
                    companeros: tuple[str, ...] = (), rivales: dict[str, int] | None = None):
    """Una ronda en una partida nueva; `clutch` es nick -> `clutch_vs` de tu equipo."""
    match = make_match(index=next(_indice))
    rnd = make_round(match, 1, side=side, won=bool(won))
    if won is None:
        rnd.my_team_won = None
        rnd.save()
    filas = {}
    for nick in {ME, *companeros, *clutch}:
        filas[nick] = make_round_player(
            rnd, username=nick, is_me=nick == ME, clutch_vs=clutch.get(nick, 0), won=bool(won)
        )
    for nick, vs in (rivales or {}).items():
        filas[nick] = make_round_player(
            rnd, username=nick, is_me=False, team_index=1, clutch_vs=vs, won=not won,
            side="Defense" if side == "Attack" else "Attack",
        )
    return filas


def por_nombre(data: dict) -> dict[str, dict]:
    return {f["username"]: f for f in data["rows"]}


class ClutchesDeCompanerosTests(TestCase):
    def test_cuenta_intentos_y_ganados_por_companero(self):
        partidas_juntas(("Seba", "Nico"))
        ronda_de_clutch({"Seba": 2}, won=True, companeros=("Nico",))
        ronda_de_clutch({"Seba": 1}, won=False, companeros=("Nico",))
        ronda_de_clutch({"Nico": 3}, won=True, companeros=("Seba",))
        data = agg.teammate_clutches()
        self.assertEqual([f["username"] for f in data["rows"]], ["Seba", "Nico"])
        seba, nico = data["rows"]
        self.assertEqual((seba["attempts"], seba["won"], seba["pct"]), (2, 1, 50.0))
        self.assertEqual((nico["attempts"], nico["won"], nico["pct"]), (1, 1, 100.0))

    def test_una_ronda_sin_ganador_no_cuenta(self):
        partidas_juntas(("Seba",))
        ronda_de_clutch({"Seba": 2}, won=None)
        self.assertEqual(agg.teammate_clutches()["rows"], [])

    def test_un_companero_que_no_es_habitual_no_sale(self):
        partidas_juntas(("Seba",), cuantas=agg.MIN_PARTIDAS_HABITUAL - 2)
        ronda_de_clutch({"Seba": 1})
        # 4 partidas juntas, contando la del clutch
        self.assertEqual(agg.teammate_clutches()["rows"], [])
        ronda_de_clutch({"Seba": 1})
        self.assertEqual([f["username"] for f in agg.teammate_clutches()["rows"]], ["Seba"])

    def test_un_rival_no_cuenta_aunque_clutchee(self):
        partidas_juntas(("Seba",))
        # el rival es "habitual" de tus partidas pero nunca estuvo en tu equipo
        for _ in range(agg.MIN_PARTIDAS_HABITUAL):
            ronda_de_clutch({}, companeros=("Seba",), rivales={"Rival": 2})
        data = agg.teammate_clutches()
        self.assertEqual(data["rows"], [])

    def test_el_filtro_de_lado_aplica(self):
        partidas_juntas(("Seba",))
        ronda_de_clutch({"Seba": 1}, side="Attack", won=True)
        ronda_de_clutch({"Seba": 1}, side="Defense", won=False)
        ronda_de_clutch({"Seba": 2}, side="Defense", won=False)
        seba = por_nombre(agg.teammate_clutches(side="Defense"))["Seba"]
        self.assertEqual((seba["attempts"], seba["won"]), (2, 0))
        seba = por_nombre(agg.teammate_clutches())["Seba"]
        self.assertEqual((seba["attempts"], seba["won"]), (3, 1))

    def test_un_cambio_de_nick_no_parte_la_fila(self):
        partidas_juntas(("Seba",))
        ronda_de_clutch({"Seba": 1})
        fila = ronda_de_clutch({"Seba": 1})["Seba"]
        fila.username = "SebaNuevo"
        fila.save()
        data = agg.teammate_clutches()
        self.assertEqual(len(data["rows"]), 1)
        self.assertEqual(data["rows"][0]["username"], "Seba")
        self.assertEqual(data["rows"][0]["attempts"], 2)

    def test_tu_fila_es_tu_conversion(self):
        partidas_juntas(("Seba",))
        ronda_de_clutch({ME: 1}, won=True, companeros=("Seba",))
        ronda_de_clutch({ME: 2}, won=False, companeros=("Seba",))
        ronda_de_clutch({ME: 3}, won=True, companeros=("Seba",))
        ronda_de_clutch({ME: 1}, won=None, companeros=("Seba",))
        yo = agg.teammate_clutches()["me"]
        conversion = agg.clutch_conversion()
        self.assertEqual(yo["attempts"], sum(f["attempts"] for f in conversion))
        self.assertEqual(yo["won"], sum(f["won"] for f in conversion))
        self.assertEqual((yo["attempts"], yo["won"]), (3, 2))
        self.assertAlmostEqual(yo["pct"], 66.7, places=1)

    def test_marca_muestra_chica_debajo_de_5(self):
        partidas_juntas(("Seba",))
        for _ in range(agg.CLUTCH_COMPANERO_MIN - 1):
            ronda_de_clutch({"Seba": 1})
        self.assertTrue(agg.teammate_clutches()["rows"][0]["low_sample"])
        ronda_de_clutch({"Seba": 1})
        self.assertFalse(agg.teammate_clutches()["rows"][0]["low_sample"])

    def test_consultas_acotadas(self):
        partidas_juntas(("Seba", "Nico"))
        ronda_de_clutch({"Seba": 1}, companeros=("Nico",))
        with self.assertNumQueries(2):
            agg.teammate_clutches()
        for _ in range(4):
            ronda_de_clutch({"Nico": 2}, companeros=("Seba",))
        with self.assertNumQueries(2):
            agg.teammate_clutches()

    def test_la_api_trae_teammate_clutches(self):
        data = self.client.get("/api/teammates/").json()["teammate_clutches"]
        self.assertEqual(data["rows"], [])
        self.assertEqual(data["min_attempts"], 5)
        self.assertEqual(data["me"]["attempts"], 0)
        self.assertIsNone(data["me"]["pct"])
