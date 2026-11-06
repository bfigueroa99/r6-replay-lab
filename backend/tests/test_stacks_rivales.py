"""Tests de los stacks rivales: grupos que te tocaron juntos en varias partidas."""

from __future__ import annotations

from django.test import TestCase

from replays.analytics import aggregates as agg
from replays.models import Match, Player

from .factories import make_match, make_round, make_round_player


def nicks(fila):
    return [j["username"] for j in fila["players"]]


class StacksRivalesTests(TestCase):
    def _partida(self, index, rivales, *, companeros=(), ganada=True, mapa="Club House"):
        match = make_match(
            index=index,
            map_name=mapa,
            my_score=4 if ganada else 2,
            opponent_score=2 if ganada else 4,
        )
        rnd = make_round(match, 0)
        make_round_player(rnd)
        for nick in rivales:
            make_round_player(rnd, username=nick, is_me=False, team_index=1)
        for nick in companeros:
            make_round_player(rnd, username=nick, is_me=False, team_index=0)
        return match

    def test_tres_rivales_juntos_en_dos_partidas_dan_una_sola_fila(self):
        self._partida(0, ["A", "B", "C", "X"])
        self._partida(1, ["A", "B", "C", "Y"])

        filas = agg.rival_stacks()
        self.assertEqual(len(filas), 1)
        self.assertEqual(nicks(filas[0]), ["A", "B", "C"])
        self.assertEqual((filas[0]["size"], filas[0]["matches"]), (3, 2))

    def test_un_grupo_mas_chico_sale_aparte_si_suma_partidas_propias(self):
        self._partida(0, ["A", "B", "C"])
        self._partida(1, ["A", "B", "C"])
        self._partida(2, ["A", "B", "Z"])

        filas = agg.rival_stacks()
        self.assertEqual([nicks(f) for f in filas], [["A", "B"], ["A", "B", "C"]])
        self.assertEqual([f["matches"] for f in filas], [3, 2])

    def test_el_record_deja_las_partidas_sin_resultado_fuera_del_winrate(self):
        self._partida(0, ["A", "B"], ganada=True)
        self._partida(1, ["A", "B"], ganada=False)
        sin_resultado = self._partida(2, ["A", "B"])
        Match.objects.filter(id=sin_resultado.id).update(won=None)

        fila = agg.rival_stacks()[0]
        self.assertEqual(
            (fila["matches"], fila["wins"], fila["losses"], fila["winrate"]), (3, 1, 1, 50.0)
        )

    def test_un_companero_que_fue_rival_solo_cuenta_donde_fue_rival(self):
        self._partida(0, ["A", "B"])
        self._partida(1, ["A", "B"])
        self._partida(2, ["B", "Z"], companeros=["A"])

        filas = agg.rival_stacks()
        self.assertEqual(len(filas), 1)
        self.assertEqual(nicks(filas[0]), ["A", "B"])
        self.assertEqual(filas[0]["matches"], 2)

    def test_respeta_el_filtro_de_mapa(self):
        self._partida(0, ["A", "B"], mapa="Club House")
        self._partida(1, ["A", "B"], mapa="Club House")
        self._partida(2, ["A", "B"], mapa="Border")

        self.assertEqual(agg.rival_stacks(map="club-house")[0]["matches"], 2)
        self.assertEqual(agg.rival_stacks(map="border"), [])

    def _partida_por_rondas(self, index, rondas):
        """Una partida ganada con una alineacion rival distinta en cada ronda."""
        match = make_match(index=index, my_score=4, opponent_score=2)
        for numero, rivales in enumerate(rondas):
            rnd = make_round(match, numero)
            make_round_player(rnd)
            for nick in rivales:
                make_round_player(rnd, username=nick, is_me=False, team_index=1)
        return match

    def test_un_reemplazo_no_forma_grupo_con_quien_reemplazo(self):
        # A se va despues de la primera ronda y entra B: nunca jugaron juntos
        self._partida_por_rondas(0, [["A", "C"], ["B", "C"]])
        self._partida_por_rondas(1, [["A", "C"], ["B", "C"]])

        grupos = [nicks(f) for f in agg.rival_stacks()]
        self.assertEqual(grupos, [["A", "C"], ["B", "C"]])
        self.assertNotIn(["A", "B", "C"], grupos)
        self.assertNotIn(["A", "B"], grupos)

    def test_ronda_con_rivales_de_mas_no_arma_grupos(self):
        # dato raro: mas rivales que los que entran en un equipo
        muchos = [f"R{i}" for i in range(11)]
        self._partida(0, muchos)
        self._partida(1, muchos)
        self.assertEqual(agg.rival_stacks(), [])
        # rivales repetidos, que no arma subconjuntos, los sigue contando
        self.assertEqual(len(agg.repeated_rivals()), 11)

    def test_sin_grupos_repetidos_devuelve_lista_vacia(self):
        self._partida(0, ["A", "B"])
        self._partida(1, ["C", "D"])
        self.assertEqual(agg.rival_stacks(), [])

    def test_sin_datos_no_revienta(self):
        self.assertEqual(agg.rival_stacks(), [])

    def test_la_api_de_duelos_trae_rival_stacks(self):
        self._partida(0, ["A", "B", "C", "X"])
        self._partida(1, ["A", "B", "C", "Y"])

        fila = self.client.get("/api/duels/").json()["rival_stacks"][0]
        self.assertEqual(nicks(fila), ["A", "B", "C"])
        self.assertEqual(fila["players"][0]["player_id"], Player.objects.get(profile_id="pid-A").id)
        self.assertEqual((fila["size"], fila["matches"], fila["wins"]), (3, 2, 2))
        self.assertEqual(self.client.get("/api/duels/?min_matches=3").json()["rival_stacks"], [])
