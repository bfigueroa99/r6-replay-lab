"""Salida del spawn por mapa: muertes y bajas en los primeros segundos de ataque (ficha 89)."""

from __future__ import annotations

from django.test import TestCase

from replays.analytics import aggregates as agg

from .factories import ME, make_event, make_match, make_round, make_round_player

RIVAL = "Rival1"
COMPA = "Compa1"


def zona(rondas: int, tempranas: int, *, spawn: str = "Warehouse", side: str = "Attack",
         index: int = 0, map_name: str = "Club House", segundos: float = 5.0):
    """`rondas` rondas con ese spawn; en las primeras `tempranas` moris a los `segundos`.

    En las demas moris a los 60 s: cuentan como ronda, no como muerte temprana.
    """
    match = make_match(map_name=map_name, index=index)
    rondas_creadas = []
    for n in range(rondas):
        rnd = make_round(match, n, side=side)
        make_round_player(rnd, side=side, spawn=spawn,
                          death_elapsed=segundos if n < tempranas else 60.0)
        rondas_creadas.append(rnd)
    return rondas_creadas


def fila(filas: list[dict], spawn: str) -> dict | None:
    return next((f for f in filas if f["spawn"] == spawn), None)


def salidas(**filtros) -> dict:
    return agg.positioning(**filtros)


class MuerteTempranaTests(TestCase):
    def test_una_muerte_a_los_14_9_cuenta_y_a_los_15_no(self):
        zona(5, 5, spawn="Warehouse", segundos=14.9, index=0)
        zona(5, 5, spawn="Construction Site", segundos=15.0, index=1)
        datos = salidas()
        self.assertEqual(datos["spawn_exit_seconds"], 15)
        self.assertEqual(fila(datos["spawn_exits"], "Warehouse")["early_deaths"], 5)
        self.assertEqual(fila(datos["spawn_exits"], "Construction Site")["early_deaths"], 0)

    def test_una_muerte_sin_reloj_no_cuenta_ni_rompe_la_fila(self):
        match = make_match()
        for n in range(4):
            make_round_player(make_round(match, n), death_elapsed=5.0)
        make_round_player(make_round(match, 4), died=True, death_elapsed=None)
        make_round_player(make_round(match, 5), died=True, death_elapsed=0.0)
        f = fila(salidas()["spawn_exits"], "Warehouse")
        self.assertEqual(f["rounds"], 6)
        self.assertEqual(f["early_deaths"], 4)
        self.assertEqual(f["early_death_pct"], 66.7)

    def test_las_rondas_de_defensa_y_sin_spawn_no_cuentan(self):
        zona(5, 5, spawn="Warehouse", index=0)
        zona(5, 5, spawn="Warehouse", side="Defense", index=1)
        zona(5, 5, spawn="", index=2)
        datos = salidas()
        self.assertEqual(len(datos["spawn_exits"]), 1)
        self.assertEqual(datos["spawn_exits"][0]["rounds"], 5)
        self.assertEqual(datos["spawn_exit_attack"]["rounds"], 5)
        self.assertEqual(datos["spawn_exit_attack"]["early_deaths"], 5)

    def test_un_spawn_con_menos_rondas_que_el_minimo_no_sale(self):
        zona(5, 1, spawn="Warehouse", index=0)
        zona(agg.POSICION_MIN_RONDAS - 1, 1, spawn="Construction Site", index=1)
        datos = salidas()
        self.assertIsNotNone(fila(datos["spawn_exits"], "Warehouse"))
        self.assertIsNone(fila(datos["spawn_exits"], "Construction Site"))
        # El total del ataque se arma antes del minimo: la fila oculta sigue contando.
        self.assertEqual(datos["spawn_exit_attack"]["rounds"], 5 + agg.POSICION_MIN_RONDAS - 1)
        self.assertEqual(fila(datos["spawn_exits"], "Warehouse")["rest_rounds"],
                         agg.POSICION_MIN_RONDAS - 1)


class BajaTempranaTests(TestCase):
    def test_las_bajas_tempranas_cuentan_solo_rivales(self):
        rondas = zona(5, 0, spawn="Warehouse")
        for rnd in rondas:
            make_round_player(rnd, username=RIVAL, is_me=False, team_index=1, side="Defense")
            make_round_player(rnd, username=COMPA, is_me=False, team_index=0)
        # Ronda 0: baja a un rival a los 5 s (cuenta) y teamkill a los 5 s (no).
        make_event(rondas[0], 1, ME, RIVAL, clock=rondas[0].clock_start - 5)
        make_event(rondas[0], 2, ME, COMPA, clock=rondas[0].clock_start - 5)
        # Ronda 1: baja a un rival a los 20 s: fuera de la ventana.
        make_event(rondas[1], 1, ME, RIVAL, clock=rondas[1].clock_start - 20)
        # Ronda 2: baja a un rival con reloj en 0 (sin reloj): no cuenta.
        make_event(rondas[2], 1, ME, RIVAL, clock=rondas[2].clock_start)
        datos = salidas()
        f = fila(datos["spawn_exits"], "Warehouse")
        self.assertEqual(f["early_kills"], 1)
        self.assertEqual(f["early_kills_per_round"], 0.2)
        self.assertEqual(datos["spawn_exit_attack"]["early_kills"], 1)


    def test_cada_baja_temprana_cae_en_el_spawn_de_su_ronda(self):
        warehouse = zona(5, 0, spawn="Warehouse", index=0)
        obras = zona(5, 0, spawn="Construction Site", index=1)
        for rnd in warehouse + obras:
            make_round_player(rnd, username=RIVAL, is_me=False, team_index=1, side="Defense")
        for orden, rnd in enumerate(warehouse[:2]):
            make_event(rnd, orden, ME, RIVAL, clock=rnd.clock_start - 3)
        make_event(obras[0], 1, ME, RIVAL, clock=obras[0].clock_start - 3)
        datos = salidas()
        self.assertEqual(fila(datos["spawn_exits"], "Warehouse")["early_kills"], 2)
        self.assertEqual(fila(datos["spawn_exits"], "Construction Site")["early_kills"], 1)
        self.assertEqual(datos["spawn_exit_attack"]["early_kills"], 3)


class ContraElRestoTests(TestCase):
    def test_el_spawn_se_compara_contra_el_resto_del_ataque(self):
        zona(10, 8, spawn="Warehouse", index=0)
        zona(10, 0, spawn="Construction Site", index=1)
        datos = salidas()
        malo = fila(datos["spawn_exits"], "Warehouse")
        bueno = fila(datos["spawn_exits"], "Construction Site")
        self.assertEqual(malo["early_death_pct"], 80.0)
        self.assertEqual(malo["rest_rounds"], 10)
        self.assertEqual(malo["rest_early_death_pct"], 0.0)
        self.assertEqual(malo["early_death_delta"], 80.0)
        self.assertEqual(malo["verdict"], "temprano")
        self.assertEqual(bueno["verdict"], "aguanta")
        # La peor sale primero.
        self.assertEqual(datos["spawn_exits"][0]["spawn"], "Warehouse")
        self.assertEqual(datos["spawn_exit_attack"]["early_death_pct"], 40.0)

    def test_un_solo_spawn_no_tiene_resto_y_es_ruido(self):
        zona(10, 8, spawn="Warehouse")
        f = salidas()["spawn_exits"][0]
        self.assertEqual(f["rest_rounds"], 0)
        self.assertIsNone(f["margin"])
        self.assertEqual(f["verdict"], "ruido")

    def test_la_fila_lleva_la_etiqueta_del_mapa(self):
        zona(5, 1, spawn="Warehouse", map_name="Bank")
        f = salidas()["spawn_exits"][0]
        self.assertEqual(f["slug"], "bank")
        self.assertIn("Bank", f["map"])
        self.assertNotIn("map_name", f)


class FiltrosTests(TestCase):
    def test_respeta_el_filtro_de_mapa(self):
        zona(5, 5, spawn="Warehouse", map_name="Club House", index=0)
        zona(5, 5, spawn="Lobby", map_name="Bank", index=1)
        datos = self.client.get("/api/positioning/?map=bank").json()
        self.assertEqual([f["spawn"] for f in datos["spawn_exits"]], ["Lobby"])
        self.assertEqual(datos["spawn_exit_attack"]["rounds"], 5)

    def test_con_filtro_de_defensa_no_hay_salidas(self):
        zona(5, 5, spawn="Warehouse")
        datos = self.client.get("/api/positioning/?side=Defense").json()
        self.assertEqual(datos["spawn_exits"], [])
        self.assertEqual(datos["spawn_exit_attack"]["rounds"], 0)
        self.assertIsNone(datos["spawn_exit_attack"]["early_death_pct"])
