"""Racha de rondas: ganadas y perdidas seguidas dentro de una partida."""

from __future__ import annotations

from datetime import datetime

from django.test import TestCase

from replays.analytics import aggregates as agg

from .factories import make_match, make_round, make_round_player

G, P = True, False


def _rondas(resultados: list[bool | None]) -> list[tuple[int, bool | None]]:
    return list(enumerate(resultados))


def _partida(resultados: dict[int, bool | None], *, index: int = 0,
             played_at: datetime | None = None, map_name: str = "Club House"):
    """Una partida con una ronda mia por cada numero de `resultados`."""
    match = make_match(index=index, map_name=map_name, played_at=played_at)
    for numero, gano in resultados.items():
        rnd = make_round(match, numero, won=gano)
        make_round_player(rnd, kills=1)
    return match


class RachasPurasTests(TestCase):
    def test_g_g_p_g_g_g_da_tres_ganadas_desde_la_cuatro_y_una_perdida(self):
        rachas = agg.rachas_de_rondas(_rondas([G, G, P, G, G, G]))
        self.assertEqual(rachas["wins"], {"length": 3, "from_number": 3})
        self.assertEqual(rachas["losses"], {"length": 1, "from_number": 2})

    def test_un_hueco_en_la_numeracion_corta_la_racha(self):
        rachas = agg.rachas_de_rondas([(0, G), (1, G), (3, G)])
        self.assertEqual(rachas["wins"], {"length": 2, "from_number": 0})

    def test_una_ronda_sin_resultado_corta_la_racha(self):
        rachas = agg.rachas_de_rondas(_rondas([G, None, G]))
        self.assertEqual(rachas["wins"], {"length": 1, "from_number": 0})
        self.assertIsNone(rachas["losses"])

    def test_a_igual_largo_gana_la_primera(self):
        rachas = agg.rachas_de_rondas(_rondas([P, P, G, P, P]))
        self.assertEqual(rachas["losses"], {"length": 2, "from_number": 0})

    def test_sin_rondas_da_dos_nulos(self):
        self.assertEqual(agg.rachas_de_rondas([]), {"wins": None, "losses": None})

    def test_el_orden_de_entrada_no_importa(self):
        rachas = agg.rachas_de_rondas([(2, G), (0, P), (3, G), (1, G)])
        self.assertEqual(rachas["wins"], {"length": 3, "from_number": 1})


class RachasEnLaApiTests(TestCase):
    def test_el_detalle_de_partida_trae_round_streaks(self):
        match = _partida({0: P, 1: G, 2: G, 3: G, 4: P, 5: P})
        data = self.client.get(f"/api/matches/{match.id}/").json()
        self.assertEqual(data["round_streaks"], {
            "wins": {"length": 3, "from_round_label": "R2"},
            "losses": {"length": 2, "from_round_label": "R5"},
        })

    def test_sin_rondas_perdidas_losses_es_nulo(self):
        match = _partida({0: G, 1: G})
        data = self.client.get(f"/api/matches/{match.id}/").json()
        self.assertIsNone(data["round_streaks"]["losses"])


class RecordDeRachaTests(TestCase):
    def test_el_record_de_racha_es_la_partida_con_la_racha_mas_larga(self):
        _partida({0: G, 1: G, 2: G, 3: P}, index=0)
        mejor = _partida({0: P, 1: P, 2: G, 3: G, 4: G, 5: G}, index=1, map_name="Oregon")
        record = agg.personal_records()["longest_round_streak"]
        self.assertEqual(record["match_id"], mejor.id)
        self.assertEqual(record["value"], 4)
        self.assertEqual(record["round_label"], "R3")
        self.assertEqual(record["map"], "Oregon")
        self.assertEqual(record["played_at"], mejor.played_at.isoformat())

    def test_a_igual_racha_gana_la_partida_mas_reciente(self):
        _partida({0: G, 1: G}, index=0, played_at=datetime(2026, 9, 1, 20, 0))
        nueva = _partida({0: G, 1: G}, index=1, played_at=datetime(2026, 9, 3, 20, 0))
        _partida({0: G, 1: G}, index=2, played_at=datetime(2026, 9, 2, 20, 0))
        record = agg.personal_records()["longest_round_streak"]
        self.assertEqual(record["match_id"], nueva.id)

    def test_sin_rondas_ganadas_no_hay_record(self):
        _partida({0: P, 1: P})
        self.assertIsNone(agg.personal_records()["longest_round_streak"])

    def test_el_filtro_de_lado_elige_partidas_y_la_racha_usa_todas_sus_rondas(self):
        match = make_match(index=0)
        for numero in range(4):
            lado = "Attack" if numero < 2 else "Defense"
            rnd = make_round(match, numero, side=lado, won=True)
            make_round_player(rnd, kills=1)
        record = agg.personal_records(side="Attack")["longest_round_streak"]
        self.assertEqual(record["value"], 4)
