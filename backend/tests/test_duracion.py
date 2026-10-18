"""Rondas cortas y largas: winrate por cuanto duro la fase de accion, por lado."""

from __future__ import annotations

from django.test import TestCase

from replays.analytics import aggregates as agg
from replays.models import RoundPlayer

from .factories import make_match, make_round, make_round_player


def _ronda(match, numero: int, lado: str, *, gano: bool | None, fin: float,
           inicio: float = 180, plant: bool = False, kills: int = 1):
    """Una ronda de `inicio - fin` segundos con tu fila del lado dado."""
    rnd = make_round(match, numero, side=lado, won=gano, clock_start=inicio, clock_end=fin,
                     possible_plant=plant)
    make_round_player(rnd, kills=kills, won=bool(gano))
    return rnd


def _fila(datos: dict, tramo: str) -> dict:
    return next(f for f in datos["rows"] if f["length"] == tramo)


def _rondas(datos: dict) -> dict[str, tuple[int, int, int]]:
    return {
        f["length"]: (f["Attack"]["rounds"], f["Defense"]["rounds"], f["total"]["rounds"])
        for f in datos["rows"]
    }


class DuracionTests(TestCase):
    def setUp(self):
        self.match = make_match()

    def test_los_tramos_salen_en_orden_fijo_con_ataque_defensa_y_total(self):
        _ronda(self.match, 0, "Attack", gano=True, fin=160)   # 20 s
        _ronda(self.match, 1, "Defense", gano=False, fin=100)  # 80 s
        _ronda(self.match, 2, "Attack", gano=True, fin=60)    # 120 s
        datos = agg.by_round_length()
        self.assertEqual([f["length"] for f in datos["rows"]],
                         ["0-45", "45-90", "90-135", "135+", "plant"])
        self.assertEqual(_rondas(datos), {
            "0-45": (1, 0, 1), "45-90": (0, 1, 1), "90-135": (1, 0, 1),
            "135+": (0, 0, 0), "plant": (0, 0, 0),
        })
        for fila in datos["rows"]:
            self.assertEqual(set(fila), {"length", "Attack", "Defense", "total"})
            self.assertEqual(set(fila["total"]), set(agg.CAMPOS_DURACION))

    def test_una_ronda_de_45_segundos_cae_en_45_a_90(self):
        _ronda(self.match, 0, "Attack", gano=True, fin=135)  # 45 s exactos
        _ronda(self.match, 1, "Attack", gano=True, fin=45)   # 135 s exactos
        datos = agg.by_round_length()
        self.assertEqual(_fila(datos, "0-45")["total"]["rounds"], 0)
        self.assertEqual(_fila(datos, "45-90")["total"]["rounds"], 1)
        self.assertEqual(_fila(datos, "90-135")["total"]["rounds"], 0)
        self.assertEqual(_fila(datos, "135+")["total"]["rounds"], 1)

    def test_una_ronda_que_llega_al_final_del_reloj_cae_en_135_o_mas(self):
        # `clock_last` ignora ceros: el final del reloj queda en 1, no en 0
        _ronda(self.match, 0, "Defense", gano=True, fin=1)
        datos = agg.by_round_length()
        self.assertEqual(_fila(datos, "135+")["Defense"]["rounds"], 1)
        self.assertEqual(datos["rounds_unknown_clock"], 0)

    def test_un_posible_plant_cuenta_solo_en_su_fila_y_sin_metricas(self):
        _ronda(self.match, 0, "Attack", gano=True, fin=40, plant=True)
        datos = agg.by_round_length()
        plant = _fila(datos, "plant")
        for celda in (plant["Attack"], plant["total"]):
            self.assertEqual(celda["rounds"], 1)
            self.assertEqual(celda["rounds_won"], 0)
            for campo in ("winrate", "rating", "kpr", "avg_duration_won", "avg_duration_lost"):
                self.assertIsNone(celda[campo], campo)
        for tramo, _, _ in agg.TRAMOS_DURACION:
            self.assertEqual(_fila(datos, tramo)["total"]["rounds"], 0, tramo)
        self.assertEqual(datos["summary"]["total"]["rounds"], 0)

    def test_una_ronda_con_reloj_desconocido_no_cuenta_en_ninguna_fila(self):
        _ronda(self.match, 0, "Attack", gano=True, fin=30, inicio=0)
        _ronda(self.match, 1, "Attack", gano=True, fin=0, inicio=0, plant=True)
        datos = agg.by_round_length()
        self.assertEqual(datos["rounds_unknown_clock"], 2)
        self.assertTrue(all(total == 0 for _, _, total in _rondas(datos).values()))
        self.assertEqual(datos["summary"]["total"]["rounds"], 0)

    def test_un_clock_end_en_cero_con_inicio_cuenta_como_reloj_desconocido(self):
        _ronda(self.match, 0, "Attack", gano=True, fin=0)
        datos = agg.by_round_length()
        self.assertEqual(datos["rounds_unknown_clock"], 1)
        self.assertEqual(_fila(datos, "135+")["total"]["rounds"], 0)

    def test_un_tramo_vacio_trae_cero_rondas_y_winrate_nulo(self):
        _ronda(self.match, 0, "Attack", gano=True, fin=160)
        vacio = _fila(agg.by_round_length(), "90-135")
        for lado in ("Attack", "Defense", "total"):
            self.assertEqual(vacio[lado]["rounds"], 0)
            self.assertEqual(vacio[lado]["rounds_won"], 0)
            self.assertIsNone(vacio[lado]["winrate"])
            self.assertIsNone(vacio[lado]["avg_duration_won"])

    def test_los_promedios_de_ganadas_y_perdidas_van_con_un_decimal(self):
        _ronda(self.match, 0, "Attack", gano=True, fin=130)    # 50 s
        _ronda(self.match, 1, "Attack", gano=True, fin=119)    # 61 s
        _ronda(self.match, 2, "Attack", gano=False, fin=100)   # 80 s
        celda = _fila(agg.by_round_length(), "45-90")["Attack"]
        self.assertEqual(celda["avg_duration_won"], 55.5)
        self.assertEqual(celda["avg_duration_lost"], 80.0)
        self.assertEqual(celda["rounds"], 3)
        self.assertEqual(celda["rounds_won"], 2)
        self.assertEqual(celda["winrate"], 66.7)

    def test_una_ronda_sin_ganador_no_entra_en_los_promedios(self):
        _ronda(self.match, 0, "Attack", gano=True, fin=130)   # 50 s
        _ronda(self.match, 1, "Attack", gano=None, fin=110)   # 70 s, sin ganador
        celda = agg.by_round_length()["summary"]["Attack"]
        self.assertEqual(celda["rounds"], 2)
        self.assertEqual(celda["avg_duration_won"], 50.0)
        self.assertIsNone(celda["avg_duration_lost"])

    def test_el_resumen_junta_los_cuatro_tramos_sin_plant(self):
        _ronda(self.match, 0, "Attack", gano=True, fin=160)    # 20 s
        _ronda(self.match, 1, "Attack", gano=True, fin=20)     # 160 s
        _ronda(self.match, 2, "Defense", gano=False, fin=100)  # 80 s
        _ronda(self.match, 3, "Defense", gano=True, fin=50, plant=True)
        resumen = agg.by_round_length()["summary"]
        self.assertEqual(resumen["Attack"]["rounds"], 2)
        self.assertEqual(resumen["Attack"]["avg_duration_won"], 90.0)
        self.assertEqual(resumen["Defense"]["rounds"], 1)
        self.assertEqual(resumen["Defense"]["avg_duration_lost"], 80.0)
        self.assertIsNone(resumen["Defense"]["avg_duration_won"])
        self.assertEqual(resumen["total"]["rounds"], 3)

    def test_el_total_incluye_rondas_sin_lado(self):
        _ronda(self.match, 0, "Attack", gano=True, fin=160)
        rnd = _ronda(self.match, 1, "Attack", gano=True, fin=150)
        RoundPlayer.objects.filter(round=rnd).update(side="")
        fila = _fila(agg.by_round_length(), "0-45")
        self.assertEqual(fila["Attack"]["rounds"], 1)
        self.assertEqual(fila["Defense"]["rounds"], 0)
        self.assertEqual(fila["total"]["rounds"], 2)

    def test_el_filtro_de_lado_deja_el_otro_lado_en_cero(self):
        _ronda(self.match, 0, "Attack", gano=True, fin=160)
        _ronda(self.match, 1, "Defense", gano=False, fin=150)
        fila = _fila(agg.by_round_length(side="Attack"), "0-45")
        self.assertEqual(fila["Attack"]["rounds"], 1)
        self.assertEqual(fila["Defense"]["rounds"], 0)
        self.assertEqual(fila["total"]["rounds"], 1)

    def test_el_filtro_de_mapa_recorta_las_rondas(self):
        _ronda(self.match, 0, "Attack", gano=True, fin=160)
        otro = make_match(index=1, map_name="Bank")
        _ronda(otro, 0, "Attack", gano=True, fin=160)
        _ronda(otro, 1, "Attack", gano=True, fin=20)
        datos = agg.by_round_length(map="bank")
        self.assertEqual(_rondas(datos)["0-45"], (1, 0, 1))
        self.assertEqual(_rondas(datos)["135+"], (1, 0, 1))
        self.assertEqual(datos["summary"]["total"]["rounds"], 2)

    def test_rating_y_kpr_del_tramo_son_los_de_totals(self):
        _ronda(self.match, 0, "Attack", gano=True, fin=160, kills=3)
        _ronda(self.match, 1, "Attack", gano=False, fin=150, kills=0)
        _ronda(self.match, 2, "Attack", gano=True, fin=20, kills=1)
        celda = _fila(agg.by_round_length(), "0-45")["total"]
        self.assertEqual(celda["kpr"], 1.5)
        esperado = agg.totals(
            RoundPlayer.objects.filter(is_me=True, round__number__in=(0, 1)),
            agg.rating_baseline(),
        )
        self.assertEqual(celda["rating"], esperado["rating"])
        self.assertIsNotNone(celda["rating"])

    def test_base_vacia_trae_las_cinco_filas_en_cero(self):
        datos = agg.by_round_length()
        self.assertEqual(len(datos["rows"]), 5)
        self.assertTrue(all(total == 0 for _, _, total in _rondas(datos).values()))
        self.assertEqual(datos["summary"]["total"]["rounds"], 0)
        self.assertIsNone(datos["summary"]["total"]["winrate"])
        self.assertEqual(datos["rounds_unknown_clock"], 0)
