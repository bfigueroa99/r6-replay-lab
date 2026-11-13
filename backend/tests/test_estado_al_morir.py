"""Estado al morir: cuantos quedaban vivos de cada lado justo antes de tu muerte."""

from __future__ import annotations

from django.test import SimpleTestCase, TestCase

from replays.analytics import aggregates as agg
from replays.analytics import metrics

from .factories import ME, make_event, make_match, make_round, make_round_player

MATES = [f"mate{i}" for i in range(4)]
RIVALES = [f"rival{i}" for i in range(5)]
URL = "/api/duels/death-state/"


def _estado(data: dict, estado: str) -> dict:
    return next(f for f in data["states"] if f["state"] == estado)


def _grupo(data: dict, grupo: str) -> dict:
    return next(f for f in data["groups"] if f["group"] == grupo)


class EstadoAlMorirPuroTests(SimpleTestCase):
    def setUp(self):
        self.team_of = {ME: 0, **dict.fromkeys(MATES, 0), **dict.fromkeys(RIVALES, 1)}

    def test_estado_al_morir_cuenta_a_la_victima(self):
        eventos = [{"kind": "Kill", "actor": "rival0", "target": ME}]
        self.assertEqual(metrics.estado_al_morir(eventos, self.team_of), {ME: (5, 5)})

    def test_cada_muerte_resta_su_vivo_para_las_siguientes(self):
        eventos = [
            {"kind": "Kill", "actor": ME, "target": "rival0"},
            {"kind": "Kill", "actor": "rival1", "target": "mate0"},
            {"kind": "Death", "actor": ME},
        ]
        estados = metrics.estado_al_morir(eventos, self.team_of)
        self.assertEqual(estados["rival0"], (5, 5))
        self.assertEqual(estados["mate0"], (5, 4))
        self.assertEqual(estados[ME], (4, 4))

    def test_un_abandono_no_anota_estado_y_deja_fuera_su_muerte_posterior(self):
        eventos = [
            {"kind": "PlayerLeave", "actor": ME},
            {"kind": "Kill", "actor": "rival0", "target": ME},
        ]
        self.assertNotIn(ME, metrics.estado_al_morir(eventos, self.team_of))

    def test_un_evento_con_jugador_sin_resolver_se_salta(self):
        eventos = [
            {"kind": "Kill", "actor": "rival0", "target": None},
            {"kind": "Kill", "actor": "rival0", "target": ME},
        ]
        self.assertEqual(metrics.estado_al_morir(eventos, self.team_of), {ME: (5, 5)})


class EstadoAlMorirTests(TestCase):
    def setUp(self):
        self.match = make_match()
        self.numero = 0

    def _ronda(self, eventos, *, side="Attack", won=True, mi_muerte=True):
        """Ronda 5v5 con tu fila, cuatro companeros y cinco rivales; `eventos` es (kind, actor, target)."""
        rnd = make_round(self.match, self.numero, side=side, won=won)
        self.numero += 1
        rival_side = "Defense" if side == "Attack" else "Attack"
        # `RoundPlayer.won` no admite nulo: sin ganador, nadie gana la fila.
        mio = bool(won)
        rival = False if won is None else not won
        make_round_player(rnd, died=mi_muerte, won=mio)
        for nick in MATES:
            make_round_player(rnd, username=nick, is_me=False, won=mio)
        for nick in RIVALES:
            make_round_player(rnd, username=nick, is_me=False, team_index=1, side=rival_side,
                              won=rival)
        for orden, (kind, actor, target) in enumerate(eventos):
            make_event(rnd, orden, actor, target, kind=kind)
        return rnd

    def test_caes_tras_una_baja_rival_cuenta_en_5v4(self):
        self._ronda([("Kill", "mate0", "rival0"), ("Kill", "rival1", ME)])
        data = agg.death_state()
        self.assertEqual(data["deaths"], 1)
        fila = _estado(data, "5v4")
        self.assertEqual((fila["allies"], fila["enemies"], fila["group"]), (5, 4, "ahead"))
        self.assertEqual(_grupo(data, "ahead")["rounds"], 1)

    def test_un_abandono_resta_un_vivo_del_estado(self):
        self._ronda([("PlayerLeave", "mate0", ""), ("Kill", "rival0", ME)])
        self.assertEqual(_estado(agg.death_state(), "4v5")["rounds"], 1)

    def test_un_teamkill_resta_un_vivo_de_tu_equipo(self):
        self._ronda([("Kill", "mate0", "mate1"), ("Kill", "rival0", ME)])
        data = agg.death_state()
        self.assertEqual(_estado(data, "4v5")["group"], "behind")

    def test_una_muerte_sin_evento_no_entra(self):
        self._ronda([("Kill", "mate0", "rival0")])
        data = agg.death_state()
        self.assertEqual((data["deaths"], data["sin_feed"]), (0, 1))
        self.assertEqual(data["states"], [])

    def test_si_te_fuiste_antes_de_morir_no_entra(self):
        self._ronda([("PlayerLeave", ME, ""), ("Kill", "rival0", ME)])
        data = agg.death_state()
        self.assertEqual((data["deaths"], data["sin_feed"]), (0, 1))

    def test_solo_cuenta_la_primera_muerte_del_feed(self):
        self._ronda([("Kill", "rival0", ME), ("Kill", "mate0", "rival1"), ("Death", ME, "")])
        data = agg.death_state()
        self.assertEqual(data["deaths"], 1)
        self.assertEqual([f["state"] for f in data["states"]], ["5v5"])

    def test_si_no_moriste_la_ronda_no_entra(self):
        self._ronda([("Kill", ME, "rival0")], mi_muerte=False)
        data = agg.death_state()
        self.assertEqual((data["deaths"], data["sin_feed"]), (0, 0))

    def test_grupos_ventaja_paridad_y_desventaja_con_winrate(self):
        self._ronda([("Kill", "mate0", "rival0"), ("Kill", "rival1", ME)], won=True)
        self._ronda([("Kill", "rival0", ME)], won=False)
        self._ronda([("Kill", "rival0", "mate0"), ("Kill", "rival1", ME)], won=None)
        data = agg.death_state()
        self.assertEqual([g["group"] for g in data["groups"]], ["ahead", "even", "behind"])
        ventaja, paridad, desventaja = data["groups"]
        self.assertEqual((ventaja["rounds"], ventaja["decided"], ventaja["won"],
                          ventaja["winrate"]), (1, 1, 1, 100.0))
        self.assertEqual((paridad["rounds"], paridad["decided"], paridad["winrate"]), (1, 1, 0.0))
        self.assertEqual((desventaja["rounds"], desventaja["decided"], desventaja["winrate"]),
                         (1, 0, None))
        self.assertEqual(data["deaths"], 3)

    def test_cada_estado_exacto_trae_su_winrate(self):
        self._ronda([("Kill", "mate0", "rival0"), ("Kill", "rival1", ME)], won=True)
        self._ronda([("Kill", "rival0", ME)], won=False)
        self._ronda([("Kill", "rival0", "mate0"), ("Kill", "rival1", ME)], won=None)
        data = agg.death_state()
        filas = {estado: _estado(data, estado) for estado in ("5v4", "5v5", "4v5")}
        self.assertEqual({e: (f["rounds"], f["decided"], f["won"], f["winrate"])
                          for e, f in filas.items()},
                         {"5v4": (1, 1, 1, 100.0), "5v5": (1, 1, 0, 0.0),
                          "4v5": (1, 0, 0, None)})

    def test_estados_ordenados_por_tuyos_vivos_y_despues_rivales(self):
        self._ronda([("Kill", "rival0", "mate0"), ("Kill", "rival1", ME)])
        self._ronda([("Kill", "rival0", ME)])
        self._ronda([("Kill", "mate0", "rival0"), ("Kill", "mate0", "rival1"),
                     ("Kill", "rival2", ME)])
        self._ronda([("Kill", "mate0", "rival0"), ("Kill", "rival1", ME)])
        estados = [f["state"] for f in agg.death_state()["states"]]
        self.assertEqual(estados, ["5v3", "5v4", "5v5", "4v5"])

    def test_filtro_de_lado_aplica(self):
        self._ronda([("Kill", "rival0", ME)], side="Attack")
        self._ronda([("Kill", "mate0", "rival0"), ("Kill", "rival1", ME)], side="Defense")
        data = agg.death_state(side="Attack")
        self.assertEqual(data["deaths"], 1)
        self.assertEqual([f["state"] for f in data["states"]], ["5v5"])

    def test_partida_con_menos_jugadores_no_se_normaliza(self):
        rnd = make_round(self.match, 99)
        make_round_player(rnd)
        make_round_player(rnd, username="mate0", is_me=False)
        make_round_player(rnd, username="rival0", is_me=False, team_index=1, side="Defense")
        make_event(rnd, 0, "rival0", ME)
        self.assertEqual([f["state"] for f in agg.death_state()["states"]], ["2v1"])

    def test_endpoint_sin_muertes_devuelve_grupos_vacios(self):
        resp = self.client.get(URL)
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual((data["deaths"], data["sin_feed"], data["states"]), (0, 0, []))
        self.assertEqual(
            [(g["group"], g["rounds"], g["winrate"]) for g in data["groups"]],
            [("ahead", 0, None), ("even", 0, None), ("behind", 0, None)],
        )

    def test_endpoint_aplica_los_filtros(self):
        self._ronda([("Kill", "rival0", ME)], side="Attack")
        self._ronda([("Kill", "rival0", ME)], side="Defense")
        resp = self.client.get(URL, {"side": "Defense"})
        self.assertEqual(resp.json()["deaths"], 1)

    def test_consultas_acotadas(self):
        for _ in range(3):
            self._ronda([("Kill", "rival0", ME)])
        with self.assertNumQueries(3):
            agg.death_state()
