"""Estado al matar: cuantos quedaban vivos de cada lado justo antes de cada baja tuya."""

from __future__ import annotations

from django.test import SimpleTestCase, TestCase

from replays.analytics import aggregates as agg
from replays.analytics import metrics

from .factories import ME, make_event, make_match, make_round, make_round_player

MATES = [f"mate{i}" for i in range(4)]
RIVALES = [f"rival{i}" for i in range(5)]
URL = "/api/duels/kill-state/"


def _estado(data: dict, estado: str) -> dict:
    return next(f for f in data["states"] if f["state"] == estado)


def _grupo(data: dict, grupo: str) -> dict:
    return next(f for f in data["groups"] if f["group"] == grupo)


class EstadoAlMatarPuroTests(SimpleTestCase):
    def setUp(self):
        self.team_of = {ME: 0, **dict.fromkeys(MATES, 0), **dict.fromkeys(RIVALES, 1)}

    def test_tu_primera_baja_en_5v5_y_la_segunda_en_5v4(self):
        eventos = [
            {"kind": "Kill", "actor": ME, "target": "rival0"},
            {"kind": "Kill", "actor": ME, "target": "rival1"},
        ]
        self.assertEqual(metrics.estado_al_matar(eventos, self.team_of)[ME], [(5, 5), (5, 4)])

    def test_un_teamkill_no_es_baja_pero_resta_un_vivo(self):
        eventos = [
            {"kind": "Kill", "actor": "mate0", "target": "mate1"},
            {"kind": "Kill", "actor": ME, "target": "rival0"},
        ]
        estados = metrics.estado_al_matar(eventos, self.team_of)
        self.assertEqual(estados[ME], [(4, 5)])
        self.assertNotIn("mate0", estados)

    def test_un_teamkill_tuyo_no_es_baja(self):
        eventos = [{"kind": "Kill", "actor": ME, "target": "mate0"}]
        self.assertNotIn(ME, metrics.estado_al_matar(eventos, self.team_of))

    def test_un_player_leave_resta_un_vivo(self):
        eventos = [
            {"kind": "PlayerLeave", "actor": "rival0"},
            {"kind": "Kill", "actor": ME, "target": "rival1"},
        ]
        self.assertEqual(metrics.estado_al_matar(eventos, self.team_of)[ME], [(5, 4)])

    def test_un_trade_ve_el_estado_que_dejo_la_baja_anterior(self):
        eventos = [
            {"kind": "Kill", "actor": "rival0", "target": "mate0"},
            {"kind": "Kill", "actor": ME, "target": "rival0"},
        ]
        estados = metrics.estado_al_matar(eventos, self.team_of)
        self.assertEqual(estados["rival0"], [(5, 5)])
        self.assertEqual(estados[ME], [(4, 5)])

    def test_un_kill_de_quien_ya_no_esta_vivo_no_se_anota(self):
        eventos = [
            {"kind": "Death", "actor": ME},
            {"kind": "Kill", "actor": ME, "target": "rival0"},
            {"kind": "Kill", "actor": "mate0", "target": "rival1"},
        ]
        estados = metrics.estado_al_matar(eventos, self.team_of)
        self.assertNotIn(ME, estados)
        # la victima del kill raro igual sale de los vivos
        self.assertEqual(estados["mate0"], [(4, 4)])

    def test_sin_actor_no_es_baja_de_nadie(self):
        eventos = [
            {"kind": "Kill", "actor": None, "target": "rival0"},
            {"kind": "Kill", "actor": ME, "target": "rival1"},
        ]
        self.assertEqual(metrics.estado_al_matar(eventos, self.team_of), {ME: [(5, 4)]})


class EstadoAlMatarAgregadoTests(TestCase):
    def setUp(self):
        self.match = make_match()
        self.numero = 0

    def _ronda(self, eventos, *, side="Attack", won=True, kills=None):
        """Ronda 5v5 con tu fila, cuatro companeros y cinco rivales; `eventos` es (kind, actor, target).

        Tus `kills` salen de los eventos (bajas tuyas a rivales) salvo que se pasen.
        """
        rnd = make_round(self.match, self.numero, side=side, won=won)
        self.numero += 1
        rival_side = "Defense" if side == "Attack" else "Attack"
        mio = bool(won)
        rival = False if won is None else not won
        if kills is None:
            kills = sum(1 for k, a, t in eventos if k == "Kill" and a == ME and t in RIVALES)
        make_round_player(rnd, kills=kills, died=False, won=mio)
        for nick in MATES:
            make_round_player(rnd, username=nick, is_me=False, won=mio)
        for nick in RIVALES:
            make_round_player(rnd, username=nick, is_me=False, team_index=1, side=rival_side,
                              won=rival)
        for orden, (kind, actor, target) in enumerate(eventos):
            make_event(rnd, orden, actor, target, kind=kind)
        return rnd

    def test_cuenta_bajas_por_estado_y_winrate(self):
        self._ronda([("Kill", ME, "rival0"), ("Kill", ME, "rival1")], won=True)
        self._ronda([("Kill", ME, "rival0")], won=False)
        data = agg.kill_state()
        self.assertEqual(data["kills"], 3)
        cinco = _estado(data, "5v5")
        self.assertEqual((cinco["kills"], cinco["rounds"], cinco["decided"], cinco["won"],
                          cinco["winrate"]), (2, 2, 2, 1, 50.0))
        cuatro = _estado(data, "5v4")
        self.assertEqual((cuatro["kills"], cuatro["rounds"], cuatro["winrate"], cuatro["group"]),
                         (1, 1, 100.0, "ahead"))

    def test_dos_bajas_con_ventaja_en_la_misma_ronda_son_una_ronda_del_grupo(self):
        self._ronda([("Kill", ME, "rival0"), ("Kill", ME, "rival1"), ("Kill", ME, "rival2")])
        ventaja = _grupo(agg.kill_state(), "ahead")
        self.assertEqual((ventaja["kills"], ventaja["rounds"], ventaja["won"]), (2, 1, 1))

    def test_una_ronda_sin_ganador_cuenta_bajas_y_no_winrate(self):
        self._ronda([("Kill", ME, "rival0")], won=None)
        fila = _estado(agg.kill_state(), "5v5")
        self.assertEqual((fila["kills"], fila["rounds"], fila["decided"], fila["winrate"]),
                         (1, 1, 0, None))

    def test_solo_teamkills_no_entra(self):
        self._ronda([("Kill", ME, "mate0")])
        data = agg.kill_state()
        self.assertEqual((data["kills"], data["sin_feed"], data["states"]), (0, 0, []))

    def test_baja_sin_evento_va_a_sin_feed(self):
        self._ronda([("Kill", ME, "rival0")], kills=2)
        data = agg.kill_state()
        self.assertEqual((data["kills"], data["sin_feed"]), (1, 1))

    def test_ventaja_paridad_y_desventaja(self):
        self._ronda([("Kill", "mate0", "rival0"), ("Kill", ME, "rival1")])
        self._ronda([("Kill", ME, "rival0")], won=False)
        self._ronda([("Kill", "rival0", "mate0"), ("Kill", ME, "rival1")], won=None)
        data = agg.kill_state()
        self.assertEqual([g["group"] for g in data["groups"]], ["ahead", "even", "behind"])
        self.assertEqual([(g["kills"], g["rounds"], g["winrate"]) for g in data["groups"]],
                         [(1, 1, 100.0), (1, 1, 0.0), (1, 1, None)])

    def test_el_filtro_de_lado_aplica_sobre_tu_fila(self):
        self._ronda([("Kill", ME, "rival0")], side="Attack")
        self._ronda([("Kill", "mate0", "rival0"), ("Kill", ME, "rival1")], side="Defense")
        data = agg.kill_state(side="Defense")
        self.assertEqual(data["kills"], 1)
        self.assertEqual([f["state"] for f in data["states"]], ["5v4"])

    def test_el_orden_de_estados_va_de_ventaja_a_desventaja(self):
        self._ronda([("Kill", "rival0", "mate0"), ("Kill", ME, "rival0")])
        self._ronda([("Kill", ME, "rival0"), ("Kill", ME, "rival1"), ("Kill", ME, "rival2")])
        estados = [f["state"] for f in agg.kill_state()["states"]]
        self.assertEqual(estados, ["5v3", "5v4", "5v5", "4v5"])

    def test_consultas_constantes(self):
        self._ronda([("Kill", ME, "rival0")])
        with self.assertNumQueries(3):
            agg.kill_state()
        for _ in range(4):
            self._ronda([("Kill", ME, "rival0")])
        with self.assertNumQueries(3):
            agg.kill_state()

    def test_la_api_responde_con_los_filtros(self):
        self._ronda([("Kill", ME, "rival0")], side="Attack")
        self._ronda([("Kill", ME, "rival0")], side="Defense")
        resp = self.client.get(URL, {"side": "Attack"})
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["kills"], 1)

    def test_la_api_sin_bajas_devuelve_grupos_vacios(self):
        data = self.client.get(URL).json()
        self.assertEqual((data["kills"], data["sin_feed"], data["states"]), (0, 0, []))
        self.assertEqual([(g["group"], g["kills"], g["winrate"]) for g in data["groups"]],
                         [("ahead", 0, None), ("even", 0, None), ("behind", 0, None)])
