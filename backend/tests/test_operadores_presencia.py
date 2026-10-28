"""Tests de presencia y delta de winrate por operador contra tu lado."""

from __future__ import annotations

from django.test import TestCase

from replays.analytics import aggregates as agg

from .factories import make_match, make_round, make_round_player


class PresenciaYDeltaTests(TestCase):
    def setUp(self):
        self.match = make_match(index=0)
        self.numero = 0

    def _rondas(self, operador, n, ganadas, *, side="Attack", sin_ganador=False):
        for i in range(n):
            gano = None if sin_ganador else i < ganadas
            rnd = make_round(self.match, self.numero, side=side, won=gano)
            make_round_player(rnd, operator=operador, won=bool(gano))
            self.numero += 1

    def _ataque_base(self):
        # 10 rondas de ataque, 5 ganadas: base 50 %
        self._rondas("Ash", 4, 3)
        self._rondas("Thermite", 6, 2)

    def _fila(self, filas, operador, side="Attack"):
        return next(f for f in filas if f["operator"] == operador and f["side"] == side)

    def test_presencia_y_delta_contra_el_lado(self):
        self._ataque_base()
        filas = agg.by_operator()
        ash = self._fila(filas, "Ash")
        thermite = self._fila(filas, "Thermite")
        self.assertEqual(ash["presence_pct"], 40.0)
        self.assertEqual(ash["winrate_delta"], 25.0)
        self.assertEqual(thermite["presence_pct"], 60.0)
        self.assertEqual(thermite["winrate_delta"], -16.7)

    def test_min_rounds_no_mueve_la_base(self):
        self._ataque_base()
        filas = agg.by_operator(min_rounds=5)
        self.assertEqual([f["operator"] for f in filas], ["Thermite"])
        self.assertEqual(filas[0]["presence_pct"], 60.0)
        self.assertEqual(filas[0]["winrate_delta"], -16.7)

    def test_cada_lado_tiene_su_base(self):
        self._ataque_base()
        self._rondas("Mute", 5, 0, side="Defense")
        filas = agg.by_operator()
        ash = self._fila(filas, "Ash")
        mute = self._fila(filas, "Mute", "Defense")
        self.assertEqual(ash["presence_pct"], 40.0)
        self.assertEqual(ash["winrate_delta"], 25.0)
        self.assertEqual(mute["presence_pct"], 100.0)
        self.assertEqual(mute["winrate_delta"], 0.0)

    def test_las_presencias_de_un_lado_suman_cien(self):
        self._rondas("Ash", 3, 1)
        self._rondas("Thermite", 3, 2)
        self._rondas("Zofia", 1, 1)
        filas = agg.by_operator()
        total = sum(f["presence_pct"] for f in filas if f["side"] == "Attack")
        self.assertAlmostEqual(total, 100.0, delta=0.2)

    def test_filtro_de_lado_recorta_la_base(self):
        self._ataque_base()
        self._rondas("Mute", 3, 3, side="Defense")
        self._rondas("Jager", 1, 0, side="Defense")
        filas = agg.by_operator(side="Defense")
        self.assertEqual({f["side"] for f in filas}, {"Defense"})
        mute = self._fila(filas, "Mute", "Defense")
        self.assertEqual(mute["presence_pct"], 75.0)
        self.assertEqual(mute["winrate_delta"], 25.0)

    def test_fila_sin_rondas_decididas_no_tiene_delta(self):
        self._ataque_base()
        self._rondas("Iana", 2, 0, sin_ganador=True)
        filas = agg.by_operator()
        iana = self._fila(filas, "Iana")
        self.assertIsNone(iana["winrate_delta"])
        self.assertEqual(iana["presence_pct"], 16.7)

    def test_base_vacia_devuelve_lista_vacia(self):
        response = self.client.get("/api/operators/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["operators"], [])

    def test_la_api_trae_las_columnas(self):
        self._ataque_base()
        fila = self._fila(self.client.get("/api/operators/").json()["operators"], "Ash")
        self.assertEqual(fila["presence_pct"], 40.0)
        self.assertEqual(fila["winrate_delta"], 25.0)

    def test_el_export_de_operadores_trae_las_columnas(self):
        self._ataque_base()
        response = self.client.get("/api/export/?table=operators")
        self.assertEqual(response.status_code, 200)
        cabecera = response.content.decode("utf-8-sig").splitlines()[0]
        self.assertIn("presence_pct", cabecera)
        self.assertIn("winrate_delta", cabecera)
