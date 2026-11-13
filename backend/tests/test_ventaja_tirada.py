"""Ventaja numerica tirada: rondas en que tu equipo quedo con mas vivos y las perdio."""

from __future__ import annotations

from datetime import datetime, timedelta

from django.test import SimpleTestCase, TestCase

from replays.analytics import aggregates as agg
from replays.analytics import metrics

from .factories import ME, make_event, make_match, make_round, make_round_player

MATES = [f"mate{i}" for i in range(4)]
RIVALES = [f"rival{i}" for i in range(5)]
URL = "/api/duels/thrown-advantage/"


class VentajaMaximaTests(SimpleTestCase):
    def setUp(self):
        self.team_of = {ME: 0, **dict.fromkeys(MATES, 0), **dict.fromkeys(RIVALES, 1)}

    def _max(self, eventos):
        return metrics.ventaja_maxima(eventos, self.team_of, 0)

    def test_una_baja_rival_da_ventaja_de_uno(self):
        self.assertEqual(self._max([{"kind": "Kill", "actor": ME, "target": "rival0"}]), 1)

    def test_un_5v3_da_ventaja_de_dos(self):
        eventos = [
            {"kind": "Kill", "actor": ME, "target": "rival0"},
            {"kind": "Kill", "actor": "mate0", "target": "rival1"},
            {"kind": "Kill", "actor": "rival2", "target": ME},
        ]
        self.assertEqual(self._max(eventos), 2)

    def test_un_abandono_rival_cuenta_como_baja(self):
        self.assertEqual(self._max([{"kind": "PlayerLeave", "actor": "rival0"}]), 1)

    def test_un_teamkill_resta_un_vivo_propio(self):
        eventos = [
            {"kind": "Kill", "actor": ME, "target": "rival0"},
            {"kind": "Kill", "actor": "mate0", "target": "mate1"},
        ]
        self.assertEqual(self._max(eventos), 1)
        self.assertEqual(self._max([{"kind": "Kill", "actor": "mate0", "target": "mate1"}]), -1)

    def test_un_5v4_de_arranque_sin_bajas_no_es_ventaja(self):
        team_of = {ME: 0, **dict.fromkeys(MATES, 0), **dict.fromkeys(RIVALES[:4], 1)}
        self.assertIsNone(metrics.ventaja_maxima([], team_of, 0))

    def test_un_5v4_de_arranque_con_una_baja_sin_resolver_no_es_ventaja(self):
        team_of = {ME: 0, **dict.fromkeys(MATES, 0), **dict.fromkeys(RIVALES[:4], 1)}
        eventos = [{"kind": "Kill", "actor": "rival0", "target": None}]
        self.assertIsNone(metrics.ventaja_maxima(eventos, team_of, 0))

    def test_cambiar_bajas_sin_pasar_adelante_no_es_ventaja(self):
        eventos = [
            {"kind": "Kill", "actor": "rival0", "target": "mate0"},
            {"kind": "Kill", "actor": ME, "target": "rival0"},
        ]
        self.assertEqual(self._max(eventos), 0)

    def test_una_muerte_repetida_o_sin_resolver_no_resta_dos_veces(self):
        eventos = [
            {"kind": "Kill", "actor": "mate0", "target": None},
            {"kind": "Kill", "actor": ME, "target": "rival0"},
            {"kind": "Death", "actor": "rival0"},
        ]
        self.assertEqual(self._max(eventos), 1)


class VentajaTiradaTests(TestCase):
    def setUp(self):
        self.match = make_match()
        self.numero = 0

    def _ronda(self, eventos, *, won=True, side="Attack", match=None):
        """Ronda 5v5 con tu fila; `eventos` es (kind, actor, target)."""
        match = match or self.match
        rnd = make_round(match, self.numero, side=side, won=won)
        self.numero += 1
        rival_side = "Defense" if side == "Attack" else "Attack"
        mio = bool(won)
        rival = False if won is None else not won
        make_round_player(rnd, won=mio)
        for nick in MATES:
            make_round_player(rnd, username=nick, is_me=False, won=mio)
        for nick in RIVALES:
            make_round_player(rnd, username=nick, is_me=False, team_index=1, side=rival_side,
                              won=rival)
        for orden, (kind, actor, target) in enumerate(eventos):
            make_event(rnd, orden, actor, target, kind=kind)
        return rnd

    def test_cuenta_ventaja_ganada_tirada_y_sin_ventaja(self):
        self._ronda([("Kill", ME, "rival0")], won=True)
        self._ronda([("Kill", ME, "rival0"), ("Kill", "rival1", ME)], won=False)
        self._ronda([("Kill", "rival0", ME)], won=False)
        data = agg.thrown_advantage()
        self.assertEqual((data["rounds"], data["thrown"], data["thrown_pct"]), (2, 1, 50.0))

    def test_separa_ventaja_de_uno_y_de_dos(self):
        self._ronda([("Kill", ME, "rival0")], won=False)
        self._ronda([("Kill", ME, "rival0"), ("Kill", ME, "rival1")], won=False)
        grupos = {g["group"]: g for g in agg.thrown_advantage()["groups"]}
        self.assertEqual([g["group"] for g in agg.thrown_advantage()["groups"]],
                         ["one", "two_plus"])
        self.assertEqual((grupos["one"]["rounds"], grupos["one"]["thrown"]), (1, 1))
        self.assertEqual((grupos["two_plus"]["rounds"], grupos["two_plus"]["thrown"]), (1, 1))

    def test_una_ronda_sin_ganador_no_cuenta(self):
        self._ronda([("Kill", ME, "rival0")], won=None)
        data = agg.thrown_advantage()
        self.assertEqual((data["rounds"], data["thrown"], data["thrown_pct"]), (0, 0, None))
        self.assertEqual(data["recent"], [])

    def test_la_lista_va_de_la_mas_reciente_y_tiene_tope(self):
        inicio = datetime(2026, 9, 1, 20, 0)
        for i in range(agg.VENTAJA_TIRADA_TOPE + 1):
            match = make_match(index=i + 1, played_at=inicio + timedelta(days=i))
            self._ronda([("Kill", ME, "rival0")], won=False, match=match)
        recientes = agg.thrown_advantage()["recent"]
        self.assertEqual(len(recientes), agg.VENTAJA_TIRADA_TOPE)
        fechas = [r["played_at"] for r in recientes]
        self.assertEqual(fechas, sorted(fechas, reverse=True))
        ultimo = recientes[0]
        self.assertEqual(ultimo["played_at"][:10], "2026-09-21")
        self.assertEqual((ultimo["round"], ultimo["side"], ultimo["advantage"], ultimo["map"]),
                         (self.numero, "Attack", 1, "Club House"))

    def test_en_la_misma_partida_va_primero_la_ronda_posterior(self):
        self._ronda([("Kill", ME, "rival0")], won=False)
        self._ronda([("Kill", ME, "rival0"), ("Kill", ME, "rival1")], won=False)
        recientes = agg.thrown_advantage()["recent"]
        self.assertEqual([(r["round"], r["advantage"]) for r in recientes], [(2, 2), (1, 1)])
        self.assertEqual(recientes[0]["match_id"], self.match.id)

    def test_el_filtro_de_lado_aplica_sobre_tu_fila(self):
        self._ronda([("Kill", ME, "rival0")], won=False, side="Attack")
        self._ronda([("Kill", ME, "rival0")], won=False, side="Defense")
        data = agg.thrown_advantage(side="Attack")
        self.assertEqual((data["rounds"], data["thrown"]), (1, 1))
        self.assertEqual([s["side"] for s in data["sides"]], ["Attack"])

    def test_por_lado(self):
        self._ronda([("Kill", ME, "rival0")], won=False, side="Attack")
        self._ronda([("Kill", ME, "rival0")], won=True, side="Defense")
        lados = {s["side"]: s for s in agg.thrown_advantage()["sides"]}
        self.assertEqual((lados["Attack"]["rounds"], lados["Attack"]["thrown_pct"]), (1, 100.0))
        self.assertEqual((lados["Defense"]["rounds"], lados["Defense"]["thrown_pct"]), (1, 0.0))

    def test_por_mapa(self):
        otra = make_match(map_name="Oregon", index=7)
        self._ronda([("Kill", ME, "rival0")], won=False)
        self._ronda([("Kill", ME, "rival0")], won=True)
        self._ronda([("Kill", ME, "rival0")], won=True, match=otra)
        mapas = agg.thrown_advantage()["maps"]
        self.assertEqual([m["map"] for m in mapas], ["Club House", "Oregon"])
        self.assertEqual((mapas[0]["rounds"], mapas[0]["thrown"], mapas[0]["thrown_pct"]),
                         (2, 1, 50.0))
        self.assertEqual((mapas[1]["rounds"], mapas[1]["thrown"]), (1, 0))

    def test_por_mapa_separa_las_versiones_del_mismo_nombre(self):
        vieja = make_match(map_name="Club House", map_id=1, index=8)
        nueva = make_match(map_name="Club House", map_id=2, index=9)
        self._ronda([("Kill", ME, "rival0")], won=False, match=vieja)
        self._ronda([("Kill", ME, "rival0")], won=True, match=nueva)
        mapas = agg.thrown_advantage()["maps"]
        self.assertEqual(len(mapas), 2)
        etiquetas = {m["map"] for m in mapas}
        self.assertEqual(len(etiquetas), 2)
        self.assertEqual(sum(m["rounds"] for m in mapas), 2)
        recientes = agg.thrown_advantage()["recent"]
        self.assertIn(recientes[0]["map"], etiquetas)

    def test_las_consultas_no_crecen_con_las_rondas(self):
        self._ronda([("Kill", ME, "rival0")], won=False)
        with self.assertNumQueries(4):
            agg.thrown_advantage()
        self._ronda([("Kill", ME, "rival0")], won=False)
        self._ronda([("Kill", "rival0", ME)], won=True)
        with self.assertNumQueries(4):
            agg.thrown_advantage()

    def test_la_api_responde_con_los_filtros(self):
        self._ronda([("Kill", ME, "rival0")], won=False, side="Defense")
        data = self.client.get(URL, {"side": "Attack"}).json()
        self.assertEqual(data["rounds"], 0)
        data = self.client.get(URL).json()
        self.assertEqual((data["rounds"], data["thrown"]), (1, 1))
        self.assertEqual(data["recent"][0]["match_id"], self.match.id)
