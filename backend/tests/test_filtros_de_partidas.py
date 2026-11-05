"""Partidas filtra por resultado, mapa, periodo, sesion y tipo (ficha 78)."""

from __future__ import annotations

from datetime import datetime, timedelta

from django.test import TestCase

from replays.analytics import aggregates as agg
from replays.models import RESULTADOS, Match, filtro_resultado

from .factories import make_match


def _partida(index: int, *, won, my_score: int = 4, opponent_score: int = 2, **kwargs) -> Match:
    """`make_match` deduce `won` del marcador; aca se fija aparte porque un
    empate y una incompleta no salen de comparar el marcador."""
    match = make_match(index=index, my_score=my_score, opponent_score=opponent_score, **kwargs)
    match.won = won
    match.save(update_fields=["won"])
    return match


def _cuatro_resultados() -> dict[str, Match]:
    return {
        "victoria": _partida(0, won=True),
        "derrota": _partida(1, won=False, my_score=2, opponent_score=4),
        "empate": _partida(2, won=False, my_score=3, opponent_score=3),
        "incompleta": _partida(3, won=None, my_score=1, opponent_score=1),
    }


class FiltroDeResultadoTests(TestCase):
    def setUp(self):
        self.partidas = _cuatro_resultados()

    def test_cada_resultado_trae_solo_sus_partidas(self):
        for valor in RESULTADOS:
            with self.subTest(resultado=valor):
                data = self.client.get(f"/api/matches/?result={valor}").json()
                self.assertEqual(data["total"], 1)
                self.assertEqual(data["matches"][0]["result"], valor)

    def test_el_filtro_de_resultado_coincide_con_match_result(self):
        for match in Match.objects.all():
            with self.subTest(partida=match.id):
                self.assertTrue(Match.objects.filter(filtro_resultado(match.result)).filter(id=match.id).exists())
                en_cuantos = sum(
                    Match.objects.filter(filtro_resultado(v)).filter(id=match.id).exists() for v in RESULTADOS
                )
                self.assertEqual(en_cuantos, 1)

    def test_un_resultado_desconocido_se_ignora_y_no_da_500(self):
        response = self.client.get("/api/matches/?result=ganada")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["total"], 4)
        self.assertIsNone(filtro_resultado("ganada"))


class PaginacionConFiltrosTests(TestCase):
    def test_la_paginacion_respeta_el_resultado(self):
        for i in range(60):
            _partida(i, won=True)
        for i in range(60, 65):
            _partida(i, won=False, my_score=1, opponent_score=4)
        data = self.client.get("/api/matches/?result=victoria&limit=50&offset=50").json()
        self.assertEqual(data["total"], 60)
        self.assertEqual(len(data["matches"]), 10)
        self.assertEqual({m["result"] for m in data["matches"]}, {"victoria"})


class FiltrosDeLaBarraTests(TestCase):
    def test_days_deja_afuera_una_partida_vieja(self):
        ahora = datetime.now()
        make_match(index=0, played_at=ahora - timedelta(days=2))
        make_match(index=1, played_at=ahora - timedelta(days=40))
        self.assertEqual(self.client.get("/api/matches/?days=30").json()["total"], 1)

    def test_until_sin_hora_incluye_todo_ese_dia(self):
        make_match(index=0, played_at=datetime(2026, 9, 8, 22, 0))
        self.assertEqual(self.client.get("/api/matches/?until=2026-09-08").json()["total"], 1)
        self.assertEqual(self.client.get("/api/matches/?since=2026-09-09").json()["total"], 0)

    def test_una_fecha_con_zona_no_da_500(self):
        make_match(index=0, played_at=datetime(2026, 9, 8, 22, 0))
        for consulta in ("since=2026-09-08T00:00:00Z", "since=2026-09-08T00:00:00%2B02:00"):
            with self.subTest(consulta=consulta):
                response = self.client.get(f"/api/matches/?{consulta}")
                self.assertEqual(response.status_code, 200)

    def test_la_sesion_trae_solo_sus_partidas(self):
        # dos noches separadas por un dia: mucho mas que el corte de sesion
        for i in range(3):
            make_match(index=i, played_at=datetime(2026, 9, 1, 20, 0) + timedelta(minutes=30 * i))
        for i in range(3, 5):
            make_match(index=i, played_at=datetime(2026, 9, 2, 20, 0) + timedelta(minutes=30 * i))
        data = self.client.get("/api/matches/?session=0").json()
        self.assertEqual(data["total"], 2)
        self.assertEqual(data["total"], len(agg.session_match_ids(0)))
        self.assertEqual(self.client.get("/api/matches/?session=99").json()["total"], 0)

    def test_tipo_y_solo_ranked_filtran_partidas(self):
        make_match(index=0, match_type="Ranked")
        make_match(index=1, match_type="Unranked")
        self.assertEqual(self.client.get("/api/matches/?match_type=Unranked").json()["total"], 1)
        data = self.client.get("/api/matches/?ranked_only=1").json()
        self.assertEqual(data["total"], 1)
        self.assertEqual(data["matches"][0]["match_type"], "Ranked")

    def test_lado_operador_y_sitio_no_filtran_partidas(self):
        make_match(index=0)
        make_match(index=1)
        data = self.client.get("/api/matches/?side=Attack&operator=Ash&site=X").json()
        self.assertEqual(data["total"], 2)

    def test_mapa_y_resultado_se_combinan(self):
        _partida(0, won=True, map_name="Bank")
        _partida(1, won=False, my_score=1, opponent_score=4, map_name="Bank")
        _partida(2, won=True, map_name="Border")
        data = self.client.get("/api/matches/?map=bank&result=victoria").json()
        self.assertEqual(data["total"], 1)
        self.assertEqual(data["matches"][0]["result"], "victoria")

    def test_match_queryset_filtra_el_mapa_e_ignora_el_lado(self):
        make_match(index=0, map_name="Bank")
        make_match(index=1, map_name="Border")
        self.assertEqual(agg.match_queryset(map="bank", side="Attack").count(), 1)
