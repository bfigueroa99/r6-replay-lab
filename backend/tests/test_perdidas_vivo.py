"""Rondas perdidas sobreviviendo: las que tu equipo perdio contigo vivo al final."""

from __future__ import annotations

from django.test import TestCase

from replays.analytics import aggregates as agg
from replays.models import Round, RoundPlayer

from .factories import make_match, make_round, make_round_player

URL = "/api/rounds/lost-alive/"


class PerdidasVivoTests(TestCase):
    def setUp(self):
        self.match = make_match()

    def _ronda(self, *, ganada, vivo, side="Attack", match=None):
        """Tu fila en una ronda nueva; `ganada` None deja la ronda sin ganador."""
        match = match or self.match
        numero = Round.objects.filter(match=match).count()
        rnd = make_round(match, numero, side=side, won=bool(ganada))
        if ganada is None:
            rnd.my_team_won = None
            rnd.save()
        return make_round_player(rnd, died=not vivo, won=bool(ganada))

    def _celda(self, fila):
        return (fila["lost"], fila["lost_alive"], fila["pct"])

    def _lado(self, data, lado):
        return next(f for f in data["sides"] if f["side"] == lado)

    def test_cuenta_perdidas_vivo_sobre_perdidas(self):
        self._ronda(ganada=False, vivo=True)
        self._ronda(ganada=False, vivo=False)
        self._ronda(ganada=True, vivo=True)
        self._ronda(ganada=None, vivo=True)
        self.assertEqual(self._celda(agg.lost_alive()["total"]), (2, 1, 50.0))

    def test_parte_por_lado(self):
        self._ronda(ganada=False, vivo=True)
        self._ronda(ganada=False, vivo=True)
        self._ronda(ganada=False, vivo=False, side="Defense")
        self._ronda(ganada=False, vivo=True, side="Defense")
        self._ronda(ganada=False, vivo=False, side="Defense")
        data = agg.lost_alive()
        self.assertEqual([f["side"] for f in data["sides"]], ["Attack", "Defense"])
        self.assertEqual(self._celda(self._lado(data, "Attack")), (2, 2, 100.0))
        self.assertEqual(self._celda(self._lado(data, "Defense")), (3, 1, 33.3))
        # el total suma conteos, no promedia los dos lados
        self.assertEqual(self._celda(data["total"]), (5, 3, 60.0))

    def test_una_ronda_sin_lado_cuenta_en_el_total_y_no_en_los_lados(self):
        fila = self._ronda(ganada=False, vivo=True)
        RoundPlayer.objects.filter(pk=fila.pk).update(side="")
        self._ronda(ganada=False, vivo=False, side="Defense")
        data = agg.lost_alive()
        self.assertEqual(self._celda(data["total"]), (2, 1, 50.0))
        self.assertEqual(self._celda(self._lado(data, "Attack")), (0, 0, None))
        self.assertEqual(self._celda(self._lado(data, "Defense")), (1, 0, 0.0))
        self.assertEqual(self._celda(data["maps"][0]), (2, 1, 50.0))

    def test_por_mapa_con_version(self):
        vieja = make_match(map_name="Club House", map_id=1, index=8)
        nueva = make_match(map_name="Club House", map_id=2, index=9)
        oregon = make_match(map_name="Oregon", index=10)
        self._ronda(ganada=False, vivo=True, match=vieja)
        self._ronda(ganada=False, vivo=False, match=nueva)
        self._ronda(ganada=False, vivo=False, match=nueva)
        self._ronda(ganada=False, vivo=True, match=oregon)
        mapas = agg.lost_alive()["maps"]
        self.assertEqual(len(mapas), 3)
        self.assertEqual(len({m["map"] for m in mapas}), 3)
        # mas perdidas primero; a igual cantidad, por nombre
        self.assertEqual([m["lost"] for m in mapas], [2, 1, 1])
        self.assertEqual(self._celda(mapas[0]), (2, 0, 0.0))
        self.assertEqual(mapas[0]["map_id"], 2)
        self.assertEqual(sum(m["lost_alive"] for m in mapas), 2)

    def test_el_filtro_de_lado_aplica(self):
        self._ronda(ganada=False, vivo=True)
        self._ronda(ganada=False, vivo=False, side="Defense")
        data = agg.lost_alive(side="Defense")
        self.assertEqual(self._celda(data["total"]), (1, 0, 0.0))
        self.assertEqual(self._celda(self._lado(data, "Attack")), (0, 0, None))
        self.assertEqual(data["recent"], [])

    def test_el_filtro_de_mapa_aplica(self):
        oregon = make_match(map_name="Oregon", index=4)
        self._ronda(ganada=False, vivo=True)
        self._ronda(ganada=False, vivo=True, match=oregon)
        data = agg.lost_alive(map="oregon")
        self.assertEqual(self._celda(data["total"]), (1, 1, 100.0))
        self.assertEqual([m["map"] for m in data["maps"]], ["Oregon"])

    def test_las_recientes_van_de_la_mas_nueva_a_la_mas_vieja_con_tope_de_10(self):
        partidas = [make_match(map_name="Bank", index=i) for i in (1, 2, 3)]
        for partida in partidas:
            for _ in range(4):
                self._ronda(ganada=False, vivo=True, match=partida)
        # ni las perdidas muerto ni las ganadas vivo entran a la lista
        self._ronda(ganada=False, vivo=False, match=partidas[2])
        self._ronda(ganada=True, vivo=True, match=partidas[2])
        recientes = agg.lost_alive()["recent"]
        self.assertEqual(len(recientes), agg.PERDIDAS_VIVO_RECIENTES)
        self.assertEqual(agg.PERDIDAS_VIVO_RECIENTES, 10)
        nueva = partidas[2]
        self.assertEqual((recientes[0]["match_id"], recientes[0]["number"]), (nueva.id, 3))
        self.assertEqual([r["match_id"] for r in recientes[:4]], [nueva.id] * 4)
        self.assertEqual([r["number"] for r in recientes[:4]], [3, 2, 1, 0])
        # la partida mas vieja aporta solo sus dos rondas mas altas
        self.assertEqual([(r["match_id"], r["number"]) for r in recientes[8:]],
                         [(partidas[0].id, 3), (partidas[0].id, 2)])
        self.assertEqual(set(recientes[0]), {"match_id", "number", "side", "played_at", "map", "slug",
                                             "map_id"})
        self.assertEqual((recientes[0]["map"], recientes[0]["side"]), ("Bank", "Attack"))

    def test_sin_rondas_no_rompe(self):
        data = agg.lost_alive()
        self.assertEqual(self._celda(data["total"]), (0, 0, None))
        self.assertEqual([self._celda(f) for f in data["sides"]], [(0, 0, None), (0, 0, None)])
        self.assertEqual((data["maps"], data["recent"]), ([], []))

    def test_solo_rondas_ganadas_no_dan_perdidas(self):
        self._ronda(ganada=True, vivo=True)
        self._ronda(ganada=True, vivo=False)
        data = agg.lost_alive()
        self.assertEqual(self._celda(data["total"]), (0, 0, None))
        self.assertEqual(data["maps"], [])

    def test_consultas_constantes(self):
        self._ronda(ganada=False, vivo=True)
        with self.assertNumQueries(3):
            agg.lost_alive()
        otra = make_match(map_name="Oregon", index=5)
        for _ in range(5):
            self._ronda(ganada=False, vivo=True, match=otra)
            self._ronda(ganada=False, vivo=False, side="Defense")
        with self.assertNumQueries(3):
            agg.lost_alive()

    def test_api_lost_alive_responde_con_filtros(self):
        self._ronda(ganada=False, vivo=True)
        self._ronda(ganada=False, vivo=True, side="Defense")
        resp = self.client.get(URL, {"side": "Attack", "until": "foo", "page": "-1"})
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(self._celda(data["total"]), (1, 1, 100.0))
        self.assertEqual(len(data["recent"]), 1)
        self.assertEqual(data["recent"][0]["side"], "Attack")
