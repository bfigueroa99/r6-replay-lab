"""Solo, en duo o en stack: tus partidas segun cuantos habituales jugaron contigo."""

from __future__ import annotations

from django.test import TestCase

from replays.analytics import aggregates as agg
from replays.models import Match, Player, RoundPlayer

from .factories import make_match, make_round, make_round_player


def _partida(index: int, companeros=(), *, mapa: str = "Club House", mi: int = 4,
             rival: int = 2, rondas: int = 2, kills: int = 1, solo_en_ronda: dict | None = None):
    """Tus rondas, una fila `team_index=0` por companero y un rival en el otro equipo.

    `solo_en_ronda` deja a un companero solo en la ronda de ese numero.
    """
    solo_en_ronda = solo_en_ronda or {}
    match = make_match(index=index, map_name=mapa, my_score=mi, opponent_score=rival)
    for numero in range(rondas):
        lado = "Attack" if numero % 2 == 0 else "Defense"
        rnd = make_round(match, numero, side=lado)
        make_round_player(rnd, kills=kills)
        for nombre in companeros:
            if nombre in solo_en_ronda and solo_en_ronda[nombre] != numero:
                continue
            make_round_player(rnd, username=nombre, is_me=False)
        make_round_player(rnd, username=f"rival-{index}", is_me=False, team_index=1, side="Defense")
    return match


def _fila(datos: dict, grupo: str) -> dict:
    return next(f for f in datos["rows"] if f["group"] == grupo)


def _partidas(datos: dict) -> dict[str, int]:
    return {f["group"]: f["matches"] for f in datos["rows"]}


def _habituales(*nombres, desde: int = 100):
    """Cinco partidas con esos companeros, para que todos queden habituales."""
    for i in range(agg.MIN_PARTIDAS_HABITUAL):
        _partida(desde + i, nombres)


class GrupoTests(TestCase):
    def test_cinco_partidas_juntas_hacen_habitual_y_cuatro_no(self):
        for i in range(5):
            _partida(i, ["Chamo"] + (["Seba"] if i < 4 else []))
        datos = agg.by_stack()
        self.assertEqual([h["username"] for h in datos["regulars"]], ["Chamo"])
        self.assertEqual(datos["regulars"][0]["matches"], 5)
        self.assertEqual(datos["min_matches"], 5)
        self.assertEqual(_partidas(datos), {"solo": 0, "duo": 5, "trio": 0, "stack": 0})

    def test_las_cuatro_filas_salen_en_orden_aunque_esten_vacias(self):
        _partida(0)
        datos = agg.by_stack()
        self.assertEqual([f["group"] for f in datos["rows"]], ["solo", "duo", "trio", "stack"])
        self.assertEqual([f["regulars"] for f in datos["rows"]], [0, 1, 2, 3])
        claves = {"group", "regulars", "matches", "matches_decided", "matches_won",
                  "match_winrate", "rounds", "rounds_won", "winrate", "rating"}
        for fila in datos["rows"]:
            self.assertEqual(set(fila), claves)
        self.assertEqual(_fila(datos, "duo")["rounds"], 0)
        self.assertIsNone(_fila(datos, "duo")["winrate"])
        self.assertIsNone(_fila(datos, "duo")["match_winrate"])

    def test_cada_partida_cae_en_una_sola_fila_segun_sus_habituales(self):
        _habituales("A", "B", "C")
        _partida(0)
        _partida(1, ["A"])
        _partida(2, ["A", "B"])
        datos = agg.by_stack()
        self.assertEqual(_partidas(datos), {"solo": 1, "duo": 1, "trio": 1, "stack": 5})
        self.assertEqual(sum(_partidas(datos).values()), Match.objects.count())

    def test_cuatro_habituales_tambien_es_stack(self):
        _habituales("A", "B", "C", "D")
        self.assertEqual(_partidas(agg.by_stack())["stack"], 5)

    def test_un_habitual_que_jugo_una_sola_ronda_cuenta_para_la_partida(self):
        _habituales("A")
        _partida(0, ["A"], rondas=4, solo_en_ronda={"A": 3})
        fila = _fila(agg.by_stack(), "duo")
        self.assertEqual(fila["matches"], 6)
        self.assertEqual(fila["rounds"], 5 * 2 + 4)

    def test_un_companero_no_habitual_no_cambia_la_fila(self):
        _habituales("A")
        _partida(0, ["A", "Random"])
        self.assertEqual(_partidas(agg.by_stack()), {"solo": 0, "duo": 6, "trio": 0, "stack": 0})

    def test_un_rival_frecuente_no_es_habitual(self):
        for i in range(5):
            match = _partida(i)
            for rnd in match.rounds.all():
                make_round_player(rnd, username="Nemesis", is_me=False, team_index=1)
        datos = agg.by_stack()
        self.assertEqual(datos["regulars"], [])
        self.assertEqual(_partidas(datos)["solo"], 5)

    def test_un_empate_cuenta_en_partidas_y_rondas_pero_no_en_el_winrate_de_partida(self):
        _habituales("A")
        m = _partida(0, ["A"], mi=3, rival=3)
        Match.objects.filter(pk=m.pk).update(won=None)
        fila = _fila(agg.by_stack(), "duo")
        self.assertEqual(fila["matches"], 6)
        self.assertEqual(fila["matches_decided"], 5)
        self.assertEqual(fila["matches_won"], 5)
        self.assertEqual(fila["match_winrate"], 100.0)
        self.assertEqual(fila["rounds"], 12)

    def test_una_derrota_baja_el_winrate_de_partida(self):
        _habituales("A")
        _partida(0, ["A"], mi=2, rival=4)
        fila = _fila(agg.by_stack(), "duo")
        self.assertEqual(fila["matches_won"], 5)
        self.assertEqual(fila["match_winrate"], 83.3)

    def test_un_cambio_de_nick_no_parte_al_habitual(self):
        _habituales("amigo")
        amigo = Player.objects.get(username="amigo")
        ids = list(RoundPlayer.objects.filter(player=amigo).order_by("id").values_list("id", flat=True))
        RoundPlayer.objects.filter(id__in=ids[5:]).update(username="amigo-nuevo")
        amigo.username = "amigo-nuevo"
        amigo.save()
        datos = agg.by_stack()
        self.assertEqual([h["username"] for h in datos["regulars"]], ["amigo-nuevo"])
        self.assertEqual(_partidas(datos)["duo"], 5)

    def test_el_filtro_de_mapa_no_cambia_quien_es_habitual(self):
        for i in range(3):
            _partida(i, ["A"], mapa="Club House")
        for i in range(3, 5):
            _partida(i, ["A"], mapa="Bank")
        datos = agg.by_stack(map="bank")
        self.assertEqual([h["username"] for h in datos["regulars"]], ["A"])
        self.assertEqual(_partidas(datos), {"solo": 0, "duo": 2, "trio": 0, "stack": 0})

    def test_el_filtro_de_lado_recorta_rondas_pero_no_el_grupo_de_la_partida(self):
        _habituales("A")
        # A solo juega la ronda 1, que es de defensa
        _partida(0, ["A"], mi=2, rival=4, solo_en_ronda={"A": 1})
        datos = agg.by_stack(side="Attack")
        fila = _fila(datos, "duo")
        self.assertEqual(fila["matches"], 6)
        self.assertEqual(fila["rounds"], 6)
        self.assertEqual(fila["matches_won"], 5)
        self.assertEqual(fila["match_winrate"], 83.3)
        self.assertEqual(_fila(datos, "solo")["matches"], 0)

    def test_sin_habituales_todo_cae_en_solo(self):
        _partida(0, ["X"])
        _partida(1, ["Y", "Z"])
        datos = agg.by_stack()
        self.assertEqual(_partidas(datos), {"solo": 2, "duo": 0, "trio": 0, "stack": 0})
        self.assertEqual(_fila(datos, "solo")["rounds"], 4)
        self.assertEqual(_fila(datos, "solo")["match_winrate"], 100.0)

    def test_base_vacia_devuelve_las_cuatro_filas_en_cero(self):
        datos = agg.by_stack()
        self.assertEqual(_partidas(datos), {"solo": 0, "duo": 0, "trio": 0, "stack": 0})
        self.assertEqual(datos["regulars"], [])
        self.assertTrue(all(f["rounds"] == 0 and f["rating"] is None for f in datos["rows"]))

    def test_el_rating_de_la_fila_pondera_por_rondas(self):
        _partida(0, rondas=1, kills=3)
        _partida(1, rondas=5, kills=0)
        fila = _fila(agg.by_stack(), "solo")
        esperado = agg.totals(RoundPlayer.objects.filter(is_me=True), agg.rating_baseline())
        self.assertEqual(fila["rounds"], 6)
        self.assertEqual(fila["rating"], esperado["rating"])
        self.assertEqual(fila["winrate"], esperado["winrate"])

    def test_la_cantidad_de_consultas_no_crece_con_las_partidas(self):
        _habituales("A", "B")
        with self.assertNumQueries(5):
            agg.by_stack()
        for i in range(3):
            _partida(i, ["A"])
        with self.assertNumQueries(5):
            agg.by_stack()
