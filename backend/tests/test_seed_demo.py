"""Tests del comando que siembra los datos del e2e.

El grueso de lo que hace el comando lo verifica el propio e2e (si el seed sale
mal, las 24 pruebas de Playwright se caen). Lo que se prueba aca es lo que el
e2e no puede: que el comando **no** pise la base de un usuario que lo corrio en
la ventana equivocada, y que la forma de los datos sea la que las pruebas de
Playwright dan por hecha.
"""

from __future__ import annotations

from io import StringIO

from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase

from replays.analytics import aggregates as agg
from replays.management.commands.seed_demo import PERFIL
from replays.models import Match, Player, Round, RoundPlayer

from .factories import make_match


def sembrar(**opciones) -> str:
    salida = StringIO()
    call_command("seed_demo", stdout=salida, **opciones)
    return salida.getvalue()


class GuardaTests(TestCase):
    def test_se_niega_si_ya_hay_partidas(self):
        """La proteccion que importa: no borrar el historial de nadie."""
        make_match(index=0)
        with self.assertRaises(CommandError) as caso:
            sembrar()
        self.assertIn("ya tiene partidas", str(caso.exception))
        self.assertEqual(Match.objects.count(), 1)

    def test_con_force_reemplaza(self):
        make_match(index=0)
        sembrar(force=True)
        self.assertFalse(Match.objects.filter(match_id__startswith="match-").exists())
        self.assertTrue(Match.objects.filter(match_id__startswith="demo-").exists())

    def test_sobre_una_base_vacia_no_hace_falta_force(self):
        sembrar()
        self.assertTrue(Match.objects.exists())


class FormaTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        sembrar()

    def test_el_volumen_es_el_que_afirman_las_pruebas_de_playwright(self):
        # la cabecera de la app dice "29 partidas · 203 rondas" y el e2e lo afirma
        self.assertEqual(Match.objects.count(), 29)
        self.assertEqual(Round.objects.count(), sum(c for _, _, c, _ in PERFIL))
        self.assertEqual(Round.objects.count(), 203)

    def test_hay_un_solo_jugador_principal(self):
        self.assertEqual(Player.objects.filter(is_me=True).count(), 1)
        self.assertEqual(RoundPlayer.objects.filter(is_me=True).count(), 203)

    def test_ninguna_partida_mezcla_sitios_de_otro_mapa(self):
        """Cortar las partidas sobre la lista plana dejaba rondas de Bank dentro
        de una partida etiquetada Border. Es dato imposible, y el e2e lo habria
        dado por bueno sin darse cuenta."""
        por_mapa: dict[str, set[str]] = {}
        for mapa, sitio, _, _ in PERFIL:
            por_mapa.setdefault(mapa, set()).add(sitio)
        for rnd in Round.objects.select_related("match"):
            self.assertIn(
                rnd.site,
                por_mapa[rnd.match.map_name],
                f"{rnd.site} no existe en {rnd.match.map_name}",
            )

    def test_cada_ronda_tiene_companeros_y_rivales(self):
        rnd = Round.objects.first()
        self.assertGreaterEqual(rnd.players.filter(team_index=0, is_me=False).count(), 2)
        self.assertGreaterEqual(rnd.players.filter(team_index=1).count(), 3)

    def test_los_veredictos_son_los_que_espera_el_e2e(self):
        """Si esto cambia, `frontend/e2e/posicionamiento.spec.js` miente."""
        sitios = {s["site"]: s for s in agg.positioning(min_rounds=5)["sites"]}
        self.assertEqual(sitios["B Church, B Arsenal Room"]["verdict"], "dormidero")
        self.assertEqual(sitios["B Church, B Arsenal Room"]["caught_out_pct"], 85.0)
        self.assertEqual(sitios["A Ventilation, A Workshop"]["verdict"], "solido")
        self.assertEqual(sitios["A Ventilation, A Workshop"]["caught_out_pct"], 25.0)
        self.assertEqual(
            sum(1 for s in sitios.values() if s["verdict"] == "ruido"), 4
        )

    def test_la_zona_flaca_solo_aparece_bajando_el_corte(self):
        con_corte = {s["site"] for s in agg.positioning(min_rounds=5)["sites"]}
        sin_corte = {s["site"] for s in agg.positioning(min_rounds=3)["sites"]}
        self.assertNotIn("A Vault, A Gold Partition", con_corte)
        self.assertIn("A Vault, A Gold Partition", sin_corte)
