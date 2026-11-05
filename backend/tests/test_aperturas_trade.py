"""Aperturas limpias, devueltas, vengadas y sin vengar (ficha 76)."""

from __future__ import annotations

from importlib import import_module

from django.apps import apps
from django.test import TestCase

from replays import export
from replays.analytics import aggregates as agg
from replays.analytics.metrics import analyse_round, annotate_trades
from replays.models import RoundPlayer
from replays.recompute import recompute

from .factories import ME, make_event, make_match, make_round, make_round_player


def ronda_apertura(gap: float, *, vengador_rival: bool = True) -> dict:
    """`yo` abre matando a `rival` y `rival2` (o `amigo`) me mata `gap` segundos despues."""
    vengador = "rival2" if vengador_rival else "amigo"
    return {
        "clockStart": 180.0,
        "players": [
            {"username": "yo", "teamIndex": 0},
            {"username": "amigo", "teamIndex": 0},
            {"username": "rival", "teamIndex": 1},
            {"username": "rival2", "teamIndex": 1},
        ],
        "teams": [{"role": "Attack"}, {"role": "Defense"}],
        "stats": [
            {"username": "yo", "kills": 1, "died": True},
            {"username": "amigo", "kills": 0, "died": False},
            {"username": "rival", "kills": 0, "died": True},
            {"username": "rival2", "kills": int(vengador_rival), "died": False},
        ],
        "matchFeedback": [
            {"type": {"name": "Kill"}, "username": "yo", "target": "rival", "timeInSeconds": 100.0},
            {
                "type": {"name": "Kill"},
                "username": vengador,
                "target": "yo",
                "timeInSeconds": 100.0 - gap,
            },
        ],
    }


def _marca(analisis: dict, nick: str) -> bool:
    return analisis["players"][nick]["opening_kill_traded"]


class AperturaDevueltaTests(TestCase):
    def test_apertura_devuelta_en_el_borde_exacto_de_la_ventana(self):
        self.assertTrue(_marca(analyse_round(ronda_apertura(3.0), window=3.0), "yo"))

    def test_apertura_limpia_si_la_venganza_llega_pasada_la_ventana(self):
        self.assertFalse(_marca(analyse_round(ronda_apertura(3.01), window=3.0), "yo"))

    def test_achicar_la_ventana_saca_la_apertura_devuelta(self):
        datos = ronda_apertura(5.0)
        self.assertTrue(_marca(analyse_round(datos, window=10.0), "yo"))
        self.assertFalse(_marca(analyse_round(datos, window=3.0), "yo"))

    def test_annotate_trades_resetea_la_marca(self):
        metrics = {"yo": {"opening_kill": True, "opening_kill_traded": True}}
        annotate_trades([], {"yo": 0}, metrics, 3.0)
        self.assertFalse(metrics["yo"]["opening_kill_traded"])

    def test_ronda_que_abre_con_death_no_marca_apertura_devuelta(self):
        datos = ronda_apertura(1.0)
        datos["matchFeedback"].insert(
            0, {"type": {"name": "Death"}, "username": "amigo", "timeInSeconds": 120.0}
        )
        analisis = analyse_round(datos, window=3.0)
        self.assertFalse(analisis["players"]["yo"]["opening_kill"])
        self.assertTrue(analisis["players"]["amigo"]["opening_death"])
        self.assertFalse(any(m["opening_kill_traded"] for m in analisis["players"].values()))

    def test_solo_el_autor_de_la_apertura_queda_marcado(self):
        analisis = analyse_round(ronda_apertura(1.0), window=3.0)
        marcados = [n for n, m in analisis["players"].items() if m["opening_kill_traded"]]
        self.assertEqual(marcados, ["yo"])

    def test_morir_por_teamkill_en_la_ventana_no_devuelve_la_apertura(self):
        analisis = analyse_round(ronda_apertura(1.0, vengador_rival=False), window=3.0)
        self.assertTrue(analisis["players"]["yo"]["opening_kill"])
        self.assertFalse(_marca(analisis, "yo"))

    def test_victima_fuera_de_los_jugadores_deja_la_apertura_limpia(self):
        datos = ronda_apertura(1.0)
        datos["matchFeedback"][0]["target"] = "fantasma"
        analisis = analyse_round(datos, window=3.0)
        self.assertTrue(analisis["players"]["yo"]["opening_kill"])
        self.assertFalse(_marca(analisis, "yo"))

    def test_teamkill_de_apertura_vengado_por_el_equipo_queda_devuelto(self):
        # teamkill de apertura y el equipo de la victima (el mio) me mata en la ventana
        datos = ronda_apertura(1.0)
        datos["matchFeedback"] = [
            {"type": {"name": "Kill"}, "username": "yo", "target": "amigo", "timeInSeconds": 100.0},
            {"type": {"name": "Kill"}, "username": "amigo2", "target": "yo", "timeInSeconds": 99.0},
        ]
        datos["players"].append({"username": "amigo2", "teamIndex": 0})
        analisis = analyse_round(datos, window=3.0)
        self.assertTrue(analisis["players"]["yo"]["opening_kill"])
        self.assertTrue(_marca(analisis, "yo"))


def _ronda_bd(indice: int, *, ok=False, od=False, devuelta=False, vengada=False, won=True,
              side="Attack"):
    rnd = make_round(make_match(index=indice), 0, side=side, won=won)
    fila = make_round_player(rnd, opening_kill=ok, opening_death=od, was_traded=vengada,
                             died=od or devuelta, won=won, side=side)
    if devuelta:
        RoundPlayer.objects.filter(pk=fila.pk).update(opening_kill_traded=True)
    return rnd


class DesgloseApiTests(TestCase):
    def setUp(self):
        _ronda_bd(0, ok=True, won=True)
        _ronda_bd(1, ok=True, won=False)
        _ronda_bd(2, ok=True, devuelta=True, won=False)
        _ronda_bd(3, od=True, vengada=True, won=True, side="Defense")
        _ronda_bd(4, od=True, won=False, side="Defense")
        _ronda_bd(5, od=True, won=False)
        _ronda_bd(6)  # ronda sin apertura propia

    def test_las_cuatro_filas_suman_las_aperturas_crudas(self):
        total = self.client.get("/api/overview/").json()["overall"]
        self.assertEqual(total["opening_kills_clean"], 2)
        self.assertEqual(total["opening_kills_traded"], 1)
        self.assertEqual(total["opening_deaths_traded"], 1)
        self.assertEqual(total["opening_deaths_untraded"], 2)
        self.assertEqual(
            total["opening_kills_clean"] + total["opening_kills_traded"], total["opening_kills"]
        )
        self.assertEqual(
            total["opening_deaths_traded"] + total["opening_deaths_untraded"],
            total["opening_deaths"],
        )
        self.assertEqual(total["winrate_opening_kill_clean"], 50.0)
        self.assertEqual(total["winrate_opening_kill_traded"], 0.0)
        self.assertEqual(total["winrate_opening_death_traded"], 100.0)
        self.assertEqual(total["winrate_opening_death_untraded"], 0.0)

    def test_el_desglose_respeta_el_filtro_de_lado(self):
        total = self.client.get("/api/overview/?side=Defense").json()["overall"]
        self.assertEqual(total["opening_kills_clean"], 0)
        self.assertEqual(total["opening_deaths_traded"], 1)
        self.assertEqual(total["opening_deaths_untraded"], 1)

    def test_sin_muestra_el_winrate_es_null(self):
        total = self.client.get("/api/overview/?side=Defense").json()["overall"]
        self.assertIsNone(total["winrate_opening_kill_clean"])
        self.assertIsNone(total["winrate_opening_kill_traded"])

    def test_el_csv_de_mapas_no_trae_columnas_nuevas(self):
        columnas = export.to_csv(export.export("maps")).splitlines()[0]
        for clave in agg.APERTURAS_CON_TRADE:
            self.assertNotIn(clave, columnas)
        self.assertNotIn("winrate_opening_kill_clean", columnas)

    def test_el_rating_no_cambia_con_la_apertura_devuelta(self):
        antes = self.client.get("/api/overview/").json()["overall"]["rating_points"]
        RoundPlayer.objects.filter(opening_kill=True).update(opening_kill_traded=True)
        despues = self.client.get("/api/overview/").json()["overall"]["rating_points"]
        self.assertEqual(antes, despues)


class RecomputeAperturaTests(TestCase):
    """Importada antes de la ficha 76: la apertura tradeada quedo sin marca."""

    def setUp(self):
        rnd = make_round(make_match(index=0), 0)
        make_round_player(rnd, username=ME, team_index=0, kills=1, died=True, opening_kill=True)
        make_round_player(rnd, username="amigo", is_me=False, team_index=0, kills=0, died=False)
        make_round_player(rnd, username="r1", is_me=False, team_index=1, kills=0, died=True,
                          opening_death=True)
        make_round_player(rnd, username="r2", is_me=False, team_index=1, kills=1, died=False)
        make_event(rnd, 0, ME, "r1", clock=120.0)
        make_event(rnd, 1, "r2", ME, clock=118.0)
        # el resto ya al dia: solo falta la marca nueva
        recompute(window=3.0)
        RoundPlayer.objects.filter(username=ME).update(opening_kill_traded=False)

    def test_recompute_llena_la_apertura_devuelta_de_lo_ya_importado(self):
        self.assertEqual(recompute(window=3.0).players_changed, 1)
        self.assertTrue(RoundPlayer.objects.get(username=ME).opening_kill_traded)

    def test_recompute_dry_run_no_escribe_la_apertura_devuelta(self):
        self.assertEqual(recompute(window=3.0, dry_run=True).players_changed, 1)
        self.assertFalse(RoundPlayer.objects.get(username=ME).opening_kill_traded)

    def test_recompute_de_apertura_devuelta_es_idempotente(self):
        recompute(window=3.0)
        self.assertFalse(recompute(window=3.0).changed)
        self.assertTrue(RoundPlayer.objects.get(username=ME).opening_kill_traded)

    def test_recompute_con_ventana_corta_saca_la_apertura_devuelta(self):
        recompute(window=3.0)
        recompute(window=1.0)
        self.assertFalse(RoundPlayer.objects.get(username=ME).opening_kill_traded)


class MigracionAperturaTests(TestCase):
    llenar = staticmethod(
        import_module("replays.migrations.0004_roundplayer_opening_kill_traded").llenar
    )

    def _ronda(self, indice: int, *, gap: float, abre_con_death: bool = False):
        rnd = make_round(make_match(index=indice), 0)
        make_round_player(rnd, username=ME, team_index=0, kills=1, died=True,
                          opening_kill=not abre_con_death)
        make_round_player(rnd, username="r1", is_me=False, team_index=1, kills=0, died=True,
                          opening_death=not abre_con_death)
        make_round_player(rnd, username="r2", is_me=False, team_index=1, kills=1, died=False)
        orden = 0
        if abre_con_death:
            make_event(rnd, orden, "r1", "", kind="Death", clock=130.0)
            orden += 1
        make_event(rnd, orden, ME, "r1", clock=120.0)
        make_event(rnd, orden + 1, "r2", ME, clock=120.0 - gap)
        return rnd

    def test_la_migracion_llena_la_apertura_devuelta_desde_los_eventos(self):
        tradeada = self._ronda(0, gap=1.0)
        limpia = self._ronda(1, gap=10.0)
        self._ronda(2, gap=1.0, abre_con_death=True)
        make_round(make_match(index=3), 0)  # ronda sin jugadores
        recompute(window=3.0)  # deja Event.traded como lo dejo el import
        RoundPlayer.objects.update(opening_kill_traded=False)

        self.llenar(apps, None)

        marcadas = set(
            RoundPlayer.objects.filter(opening_kill_traded=True).values_list("round_id", flat=True)
        )
        self.assertEqual(marcadas, {tradeada.id})
        self.assertFalse(RoundPlayer.objects.get(round=limpia, username=ME).opening_kill_traded)

    def test_migracion_y_recompute_coinciden(self):
        self._ronda(0, gap=1.0)
        self._ronda(1, gap=10.0)
        self._ronda(2, gap=1.0, abre_con_death=True)
        recompute(window=3.0)
        RoundPlayer.objects.update(opening_kill_traded=False)
        self.llenar(apps, None)
        self.assertEqual(recompute(window=3.0, dry_run=True).players_changed, 0)
