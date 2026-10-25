"""Tests de clutch_vs: intentos de clutch, ganes o pierdas, y su conversion."""

from __future__ import annotations

from importlib import import_module

from django.apps import apps
from django.test import TestCase

from replays.analytics import aggregates as agg
from replays.analytics.metrics import analyse_round, clutch_vs
from replays.models import RoundPlayer

from .factories import ME, make_event, make_match, make_round, make_round_player

EQUIPOS = {"yo": 0, "a1": 0, "a2": 0, "r1": 1, "r2": 1, "r3": 1}


def kill(actor: str, target: str) -> dict:
    return {"kind": "Kill", "actor": actor, "target": target}


class ClutchVsTests(TestCase):
    def test_quedar_solo_frente_a_tres_da_tres(self):
        valores = clutch_vs([kill("r1", "a1"), kill("r2", "a2")], EQUIPOS)
        self.assertEqual(valores["yo"], 3)
        self.assertEqual(valores["r1"], 0)

    def test_un_uno_contra_uno_le_da_uno_a_los_dos(self):
        valores = clutch_vs([kill("yo", "r1")], {"yo": 0, "r1": 1})
        self.assertEqual((valores["yo"], valores["r1"]), (1, 1))

    def test_quien_ya_estaba_solo_conserva_su_primer_valor(self):
        # r1 arranca 1v2; cae a1 y yo quedo 1v1, pero r1 sigue con su 2
        valores = clutch_vs([kill("r1", "a1")], {"yo": 0, "a1": 0, "r1": 1})
        self.assertEqual((valores["yo"], valores["r1"]), (1, 2))

    def test_el_player_leave_cuenta_como_muerte(self):
        eventos = [{"kind": "PlayerLeave", "actor": "a1", "target": ""}, kill("r1", "a2")]
        self.assertEqual(clutch_vs(eventos, EQUIPOS)["yo"], 3)

    def test_matar_despues_de_quedar_solo_no_cambia_el_valor(self):
        eventos = [kill("r1", "a1"), kill("r2", "a2"), kill("yo", "r1"), kill("yo", "r2")]
        self.assertEqual(clutch_vs(eventos, EQUIPOS)["yo"], 3)

    def test_nadie_queda_solo_da_cero_a_todos(self):
        valores = clutch_vs([kill("r1", "a1")], EQUIPOS)
        self.assertEqual(set(valores), set(EQUIPOS))
        self.assertTrue(all(v == 0 for v in valores.values()))

    def test_un_nick_desconocido_en_el_feed_se_ignora(self):
        eventos = [kill("r1", "fantasma"), {"kind": "Death", "actor": "", "target": ""},
                   kill("r1", "a1"), kill("r1", "a1"), kill("r2", "a2")]
        valores = clutch_vs(eventos, EQUIPOS)
        self.assertNotIn("fantasma", valores)
        self.assertEqual(valores["yo"], 3)

    def test_solo_desde_el_inicio_cuenta_todos_los_rivales(self):
        equipos = {"yo": 0, "r1": 1, "r2": 1, "r3": 1}
        self.assertEqual(clutch_vs([kill("yo", "r1")], equipos)["yo"], 3)

    def test_solo_desde_el_inicio_y_caer_primero_es_un_intento_perdido(self):
        equipos = {"yo": 0, "r1": 1, "r2": 1, "r3": 1}
        self.assertEqual(clutch_vs([kill("r1", "yo")], equipos)["yo"], 3)


def round_data(ganamos: bool, rivales: int) -> dict:
    """Quedo solo frente a `rivales` (el resto de mi equipo cae primero)."""
    rivales_nicks = [f"r{i}" for i in range(1, 4)]
    feed = [
        {"type": {"name": "Kill"}, "username": "r1", "target": "a1", "timeInSeconds": 120.0},
        {"type": {"name": "Kill"}, "username": "r1", "target": "a2", "timeInSeconds": 110.0},
    ]
    if rivales == 2:
        feed.insert(0, {"type": {"name": "Kill"}, "username": "yo", "target": "r3",
                        "timeInSeconds": 130.0})
    return {
        "clockStart": 180.0,
        "players": [{"username": n, "teamIndex": 0} for n in ("yo", "a1", "a2")]
        + [{"username": n, "teamIndex": 1} for n in rivales_nicks],
        "teams": [{"role": "Attack", "won": ganamos}, {"role": "Defense", "won": not ganamos}],
        "stats": [{"username": "yo", "died": not ganamos, "1vX": rivales if ganamos else 0}],
        "matchFeedback": feed,
    }


class ImportClutchTests(TestCase):
    def test_quedar_solo_frente_a_tres_y_perder_da_tres(self):
        yo = analyse_round(round_data(ganamos=False, rivales=3))["players"]["yo"]
        self.assertEqual(yo["clutch_vs"], 3)
        self.assertEqual(yo["one_vx"], 0)

    def test_quedar_solo_frente_a_dos_y_ganar_da_dos_y_el_one_vx_de_siempre(self):
        yo = analyse_round(round_data(ganamos=True, rivales=2))["players"]["yo"]
        self.assertEqual(yo["clutch_vs"], 2)
        self.assertEqual(yo["one_vx"], 2)
        self.assertTrue(yo["won"])


class ConversionTests(TestCase):
    def _ronda(self, indice: int, *, vs: int, won: bool, side: str = "Attack"):
        rnd = make_round(make_match(index=indice), 0, side=side, won=won)
        make_round_player(rnd, clutch_vs=vs, won=won, side=side)

    def test_una_fila_por_x_con_intentos_y_ganados(self):
        self._ronda(0, vs=1, won=True)
        self._ronda(1, vs=1, won=False)
        self._ronda(2, vs=3, won=False)
        self._ronda(3, vs=0, won=True)
        filas = agg.clutch_conversion()
        self.assertEqual([f["label"] for f in filas], ["1v1", "1v3"])
        self.assertEqual((filas[0]["attempts"], filas[0]["won"], filas[0]["pct"]), (2, 1, 50.0))
        self.assertEqual((filas[1]["attempts"], filas[1]["won"], filas[1]["pct"]), (1, 0, 0.0))

    def test_el_lado_se_separa_y_filtra_con_side(self):
        self._ronda(0, vs=2, won=True, side="Attack")
        self._ronda(1, vs=2, won=False, side="Defense")
        self._ronda(2, vs=2, won=False, side="Defense")
        fila = agg.clutch_conversion()[0]
        self.assertEqual(fila["attack"], {"attempts": 1, "won": 1, "pct": 100.0})
        self.assertEqual(fila["defense"], {"attempts": 2, "won": 0, "pct": 0.0})
        solo_defensa = agg.clutch_conversion(side="Defense")[0]
        self.assertEqual(solo_defensa["attempts"], 2)
        self.assertIsNone(solo_defensa["attack"]["pct"])

    def test_x_de_seis_se_agrupa_en_cinco_mas(self):
        self._ronda(0, vs=5, won=False)
        self._ronda(1, vs=6, won=True)
        filas = agg.clutch_conversion()
        self.assertEqual(len(filas), 1)
        self.assertEqual((filas[0]["vs"], filas[0]["label"]), (5, "1v5+"))
        self.assertEqual((filas[0]["attempts"], filas[0]["won"]), (2, 1))

    def test_una_ronda_sin_ganador_conocido_no_cuenta_como_intento(self):
        self._ronda(0, vs=2, won=True)
        rnd = make_round(make_match(index=1), 0)
        rnd.my_team_won = None
        rnd.save(update_fields=["my_team_won"])
        make_round_player(rnd, clutch_vs=2, won=False)
        fila = agg.clutch_conversion()[0]
        self.assertEqual((fila["attempts"], fila["won"]), (1, 1))

    def test_sin_intentos_devuelve_lista_vacia(self):
        self._ronda(0, vs=0, won=True)
        self.assertEqual(agg.clutch_conversion(), [])

    def test_la_api_de_companeros_trae_la_conversion_filtrada(self):
        self._ronda(0, vs=2, won=True, side="Attack")
        self._ronda(1, vs=1, won=False, side="Defense")
        filas = self.client.get("/api/teammates/?side=Attack").json()["clutch_conversion"]
        self.assertEqual([(f["label"], f["attempts"]) for f in filas], [("1v2", 1)])


class MigracionTests(TestCase):
    def test_la_migracion_llena_lo_ya_importado(self):
        llenar = import_module("replays.migrations.0003_roundplayer_clutch_vs").llenar
        rnd = make_round(make_match(index=0), 0)
        make_round_player(rnd, username=ME, team_index=0)
        make_round_player(rnd, username="a1", is_me=False, team_index=0)
        for nick in ("r1", "r2"):
            make_round_player(rnd, username=nick, is_me=False, team_index=1)
        make_event(rnd, 0, "r1", "a1", clock=120.0)
        make_event(rnd, 1, "", "", kind="Death", clock=110.0)
        # ronda sin jugadores: no tiene que tumbar la migracion
        make_round(make_match(index=1), 0)

        llenar(apps, None)

        self.assertEqual(RoundPlayer.objects.get(username=ME).clutch_vs, 2)
        self.assertEqual(RoundPlayer.objects.get(username="r1").clutch_vs, 0)


class ClutchPorSitioTests(TestCase):
    def _ronda(self, indice: int, *, mapa: str, sitio: str, won: bool, side: str = "Attack"):
        rnd = make_round(make_match(index=indice, map_name=mapa), 0, side=side, site=sitio, won=won)
        make_round_player(rnd, clutch_vs=2, won=won, side=side)

    def test_clutch_por_sitio_agrupa_por_mapa_y_sitio(self):
        self._ronda(0, mapa="Border", sitio="B Armory", won=True)
        self._ronda(1, mapa="Border", sitio="B Armory", won=False)
        self._ronda(2, mapa="Border", sitio="A Ventilation", won=True)
        self._ronda(3, mapa="Bank", sitio="B Lockers", won=False)
        filas = agg.clutch_by_site()
        self.assertEqual(
            [(f["kind"], f["map"], f["site"], f["attempts"], f["won"]) for f in filas],
            [
                ("map", "Bank", None, 1, 0),
                ("site", "Bank", "B Lockers", 1, 0),
                ("map", "Border", None, 3, 2),
                ("site", "Border", "B Armory", 2, 1),
                ("site", "Border", "A Ventilation", 1, 1),
            ],
        )
        self.assertEqual(filas[3]["pct"], 50.0)
        self.assertEqual(filas[2]["slug"], "border")

    def test_una_ronda_sin_sitio_va_a_sin_sitio(self):
        self._ronda(0, mapa="Border", sitio="", won=True)
        self._ronda(1, mapa="Border", sitio="", won=False)
        self._ronda(2, mapa="Border", sitio="B Armory", won=True)
        filas = agg.clutch_by_site()
        self.assertEqual([f["site"] for f in filas], [None, "B Armory", "Sin sitio"])
        self.assertEqual(filas[0]["attempts"], 3)
        self.assertEqual(filas[2]["attempts"], 2)

    def test_cuatro_intentos_son_muestra_chica_y_cinco_no(self):
        for i in range(5):
            self._ronda(i, mapa="Border", sitio="B Armory", won=i % 2 == 0)
        for i in range(5, 9):
            self._ronda(i, mapa="Border", sitio="A Ventilation", won=True)
        total, armory, ventilation = agg.clutch_by_site()
        self.assertEqual(agg.CLUTCH_SITIO_MIN, 5)
        self.assertEqual((armory["site"], armory["attempts"], armory["low_sample"]), ("B Armory", 5, False))
        self.assertEqual(
            (ventilation["site"], ventilation["attempts"], ventilation["low_sample"]), ("A Ventilation", 4, True)
        )
        self.assertFalse(total["low_sample"])

    def test_una_ronda_sin_ganador_no_cuenta_como_intento_por_sitio(self):
        self._ronda(0, mapa="Border", sitio="B Armory", won=True)
        rnd = make_round(make_match(index=1, map_name="Border"), 0, site="B Armory")
        rnd.my_team_won = None
        rnd.save(update_fields=["my_team_won"])
        make_round_player(rnd, clutch_vs=2, won=False)
        total, sitio = agg.clutch_by_site()
        self.assertEqual((total["attempts"], sitio["attempts"], sitio["won"]), (1, 1, 1))

    def test_clutch_por_sitio_respeta_el_filtro_de_lado(self):
        self._ronda(0, mapa="Border", sitio="B Armory", won=True, side="Attack")
        self._ronda(1, mapa="Border", sitio="B Armory", won=False, side="Defense")
        self._ronda(2, mapa="Bank", sitio="B Lockers", won=False, side="Defense")
        filas = self.client.get("/api/teammates/?side=Attack").json()["clutch_by_site"]
        self.assertEqual([(f["map"], f["site"], f["attempts"]) for f in filas], [("Border", None, 1), ("Border", "B Armory", 1)])

    def test_clutch_por_sitio_con_base_vacia_es_lista_vacia(self):
        self.assertEqual(agg.clutch_by_site(), [])
        respuesta = self.client.get("/api/teammates/")
        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(respuesta.json()["clutch_by_site"], [])


class ClutchPorOperadorTests(TestCase):
    def _ronda(self, indice: int, *, operator: str, won: bool, side: str = "Attack"):
        rnd = make_round(make_match(index=indice), 0, side=side, won=won)
        make_round_player(rnd, clutch_vs=2, won=won, side=side, operator=operator)

    def test_una_fila_por_operador_y_lado_con_intentos_y_ganados(self):
        self._ronda(0, operator="Ash", won=True)
        self._ronda(1, operator="Ash", won=False)
        self._ronda(2, operator="Ash", won=True)
        self._ronda(3, operator="Mute", won=True, side="Defense")
        self._ronda(4, operator="Thermite", won=False)
        filas = agg.clutch_by_operator()
        self.assertEqual(
            [(f["operator"], f["side"], f["attempts"], f["won"]) for f in filas],
            [("Ash", "Attack", 3, 2), ("Mute", "Defense", 1, 1), ("Thermite", "Attack", 1, 0)],
        )
        self.assertEqual(filas[0]["pct"], 66.7)
        self.assertEqual(filas[2]["pct"], 0.0)

    def test_los_intentos_suman_lo_mismo_que_la_conversion_menos_sin_operador(self):
        self._ronda(0, operator="Ash", won=True)
        self._ronda(1, operator="Mute", won=False, side="Defense")
        self._ronda(2, operator="", won=True)
        por_operador = sum(f["attempts"] for f in agg.clutch_by_operator())
        conversion = sum(f["attempts"] for f in agg.clutch_conversion())
        self.assertEqual(conversion, 3)
        self.assertEqual(por_operador, conversion - 1)
        self.assertNotIn("", [f["operator"] for f in agg.clutch_by_operator()])

    def test_cuatro_intentos_son_muestra_chica_y_cinco_no(self):
        minimo = agg.CLUTCH_OPERADOR_MIN
        for i in range(minimo):
            self._ronda(i, operator="Ash", won=i % 2 == 0)
        for i in range(minimo, 2 * minimo - 1):
            self._ronda(i, operator="Thermite", won=True)
        ash, thermite = agg.clutch_by_operator()
        self.assertEqual((ash["operator"], ash["attempts"], ash["low_sample"]), ("Ash", minimo, False))
        self.assertEqual((thermite["operator"], thermite["attempts"], thermite["low_sample"]), ("Thermite", minimo - 1, True))

    def test_una_ronda_sin_ganador_no_cuenta_como_intento_por_operador(self):
        self._ronda(0, operator="Ash", won=True)
        rnd = make_round(make_match(index=1), 0, side="Attack")
        rnd.my_team_won = None
        rnd.save(update_fields=["my_team_won"])
        make_round_player(rnd, clutch_vs=2, won=False, side="Attack", operator="Ash")
        (fila,) = agg.clutch_by_operator()
        self.assertEqual((fila["attempts"], fila["won"]), (1, 1))

    def test_clutch_por_operador_respeta_el_filtro_de_lado(self):
        self._ronda(0, operator="Ash", won=True, side="Attack")
        self._ronda(1, operator="Mute", won=False, side="Defense")
        self._ronda(2, operator="Jager", won=True, side="Defense")
        filas = self.client.get("/api/teammates/?side=Attack").json()["clutch_by_operator"]
        self.assertEqual([(f["operator"], f["side"], f["attempts"]) for f in filas], [("Ash", "Attack", 1)])

    def test_la_api_de_companeros_trae_clutch_por_operador_vacio_sin_datos(self):
        self.assertEqual(agg.clutch_by_operator(), [])
        respuesta = self.client.get("/api/teammates/")
        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(respuesta.json()["clutch_by_operator"], [])
