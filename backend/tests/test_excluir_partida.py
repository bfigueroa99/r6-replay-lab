"""Excluir una partida de los agregados (ficha 79).

La regla es una sola: una partida excluida es, en todo numero, igual a una que
nunca se importo. Por eso la red principal no afirma valores sueltos: arma una
partida que toca cada raiz de los agregados, guarda las respuestas con la
partida excluida, la borra y compara.
"""

from __future__ import annotations

import ast
import json
import tempfile
from datetime import timedelta
from pathlib import Path
from unittest import mock

from django.test import TestCase, override_settings

from replays import export, urls
from replays.analytics import aggregates as agg
from replays.ingest import import_match_folder
from replays.models import Match, Player

from .factories import (
    ME,
    build_dataset,
    make_event,
    make_match,
    make_round,
    make_round_player,
)
from .test_ingest import _ronda

# --------------------------------------------------------------------- helpers


def _normalizar(obj):
    """Redondea los floats: el orden del JOIN puede mover el ultimo bit."""
    if isinstance(obj, float):
        return round(obj, 9)
    if isinstance(obj, dict):
        return {k: _normalizar(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_normalizar(v) for v in obj]
    return obj


def _sin_rating(obj):
    """El rating de una partida se mide contra el 1.00 de las que cuentan."""
    if isinstance(obj, dict):
        return {k: _sin_rating(v) for k, v in obj.items() if k != "rating"}
    if isinstance(obj, list):
        return [_sin_rating(v) for v in obj]
    return obj


def _excluir(client, pk: int, valor: bool = True):
    return client.post(
        f"/api/matches/{pk}/exclude/",
        data=json.dumps({"excluded": valor}),
        content_type="application/json",
    )


#: Rutas GET que dan numeros. Cada una se compara con y sin la partida.
COMPARADAS = {
    "filters", "overview", "coach", "positioning", "operators", "trends", "teammates",
    "duels", "sessions", "compare", "player-detail", "export",
}

#: Rutas que muestran partidas o inventario, no numeros agregados.
NO_AGREGADOS = {
    "health",  # inventario: cuenta todas las importadas
    "operator-catalog",  # catalogo del parser mas lo visto, para la ruleta
    "match-list",  # muestra la partida, marcada
    "match-detail",  # muestra la partida completa
    "unknown",  # etiquetado de mapas y operadores desconocidos
    "settings",  # configuracion (GET y POST)
    "import-status",  # inventario del job de importacion
    "import-progress",  # estado del job de importacion
}

#: Rutas que solo aceptan POST.
SOLO_POST = {"player-ubisoft", "overrides", "backup", "import", "match-exclude"}

RUTAS_SOLO_POST = {
    "player-ubisoft": "/api/players/1/ubisoft/",
    "overrides": "/api/overrides/",
    "backup": "/api/backup/",
    "import": "/api/import/",
    "match-exclude": "/api/matches/1/exclude/",
}


@override_settings(SESSION_GAP_MINUTES=120)
class _ConPartidaX(TestCase):
    """Seis partidas normales y una X armada para tocar cada raiz.

    X tiene un rating muy alto, une dos sesiones (a 100 minutos de cada lado),
    es la unica de su `map_id` dentro de un slug compartido y la unica
    "Custom", lleva al habitual a 5 partidas y repite un rival con duelos y un
    clutch.
    """

    def setUp(self):
        self.normales = build_dataset(matches=6, rounds_per_match=6)
        # dos bloques: 20-22 h y, 200 minutos despues de la ultima, 01:20-03:20
        for m in self.normales[3:]:
            m.played_at += timedelta(minutes=140)
            m.save()
        for m in self.normales[:4]:
            rnd = m.rounds.first()
            make_round_player(rnd, username="habitual", is_me=False, team_index=0,
                              kills=0, died=False, death_elapsed=None)
        rnd_rival = self.normales[1].rounds.first()
        make_round_player(rnd_rival, username="repetido", is_me=False, team_index=1,
                          side="Defense", kills=0, died=True, death_elapsed=30.0)
        make_event(rnd_rival, 0, ME, "repetido")

        self.x = make_match(
            map_name="Club House",
            map_id=987654,
            match_type="Custom",
            played_at=self.normales[2].played_at + timedelta(minutes=100),
            index=99,
            my_score=4,
            opponent_score=0,
        )
        for n in range(4):
            side = "Attack" if n % 2 == 0 else "Defense"
            rnd = make_round(self.x, n, side=side, won=True, site="2F Bar, 2F Cash Room")
            make_round_player(rnd, side=side, kills=4, died=False, death_elapsed=None,
                              opening_kill=True, trade_kills=1, one_vx=2 if n == 0 else 0,
                              clutch_vs=2 if n == 0 else 0, operator="Ash" if n % 2 == 0 else "Jager")
            make_round_player(rnd, username="habitual", is_me=False, team_index=0,
                              side=side, kills=0, died=False, death_elapsed=None)
            make_round_player(rnd, username="repetido", is_me=False, team_index=1,
                              side="Defense" if side == "Attack" else "Attack",
                              kills=0, died=True, death_elapsed=20.0)
            make_event(rnd, 0, ME, "repetido", clock=160.0)
        self.otros_ids = list(
            Player.objects.filter(is_me=False).values_list("id", flat=True)
        )

    # ------------------------------------------------------------- capturas

    def _rutas(self) -> dict[str, str]:
        rutas = {
            "filters": "/api/filters/",
            "overview": "/api/overview/",
            "overview session": "/api/overview/?session=0",
            "overview mapa": "/api/overview/?map=club-house&side=Attack",
            "coach": "/api/coach/",
            "positioning": "/api/positioning/",
            "operators": "/api/operators/",
            "trends": "/api/trends/",
            "trends session": "/api/trends/?session=0",
            "trends mapa": "/api/trends/?map=club-house&side=Attack",
            "teammates": "/api/teammates/",
            "duels": "/api/duels/",
            "sessions": "/api/sessions/",
            "compare matches": "/api/compare/?by=matches&n=2",
            "compare days": "/api/compare/?by=days&n=1",
        }
        for pid in self.otros_ids:
            rutas[f"player {pid}"] = f"/api/players/{pid}/"
        return rutas

    def _capturar(self) -> dict:
        salida = {}
        for nombre, ruta in self._rutas().items():
            resp = self.client.get(ruta)
            self.assertEqual(resp.status_code, 200, ruta)
            salida[nombre] = resp.json()
        return salida

    def _capturar_csv(self) -> dict:
        salida = {}
        for tabla in export.TABLES:
            resp = self.client.get(f"/api/export/?table={tabla}")
            self.assertEqual(resp.status_code, 200, tabla)
            salida[tabla] = resp.content.decode("utf-8")
        return salida


# --------------------------------------------------------------------- el POST


class ExcluirPartidaPostTests(TestCase):
    def setUp(self):
        self.match = make_match()

    def test_sin_json_da_415(self):
        resp = self.client.post(f"/api/matches/{self.match.pk}/exclude/", {"excluded": "true"})
        self.assertEqual(resp.status_code, 415)
        self.match.refresh_from_db()
        self.assertFalse(self.match.excluded)

    def test_partida_inexistente_da_404(self):
        self.assertEqual(_excluir(self.client, 999_999).status_code, 404)

    def test_json_sin_booleano_da_400(self):
        url = f"/api/matches/{self.match.pk}/exclude/"
        for cuerpo in ("{}", json.dumps({"excluded": "si"}), "esto no es json", "[true]"):
            resp = self.client.post(url, data=cuerpo, content_type="application/json")
            self.assertEqual(resp.status_code, 400, cuerpo)
        self.match.refresh_from_db()
        self.assertFalse(self.match.excluded)

    def test_get_no_esta_permitido(self):
        resp = self.client.get(f"/api/matches/{self.match.pk}/exclude/")
        self.assertEqual(resp.status_code, 405)

    def test_excluir_y_volver_a_incluir_cambia_la_marca(self):
        resp = _excluir(self.client, self.match.pk)
        self.assertEqual(resp.json(), {"id": self.match.pk, "excluded": True})
        self.match.refresh_from_db()
        self.assertTrue(self.match.excluded)
        resp = _excluir(self.client, self.match.pk, False)
        self.assertEqual(resp.json(), {"id": self.match.pk, "excluded": False})
        self.match.refresh_from_db()
        self.assertFalse(self.match.excluded)

    def test_excluir_no_toca_parsed_at(self):
        antes = self.match.parsed_at
        _excluir(self.client, self.match.pk)
        self.match.refresh_from_db()
        self.assertEqual(self.match.parsed_at, antes)


# --------------------------------------------------------------------- la regla


class ExcluidaIgualQueSinImportarTests(_ConPartidaX):
    def test_la_partida_x_cambia_los_numeros(self):
        """Sin esto, la comparacion de abajo podria pasar con una X inofensiva."""
        con_x = self._capturar()
        _excluir(self.client, self.x.pk)
        sin_x = self._capturar()
        for nombre in ("filters", "overview", "overview session", "teammates", "duels",
                       "sessions", "coach"):
            self.assertNotEqual(_normalizar(con_x[nombre]), _normalizar(sin_x[nombre]), nombre)

    def test_cada_get_agregado_da_lo_mismo_que_sin_la_partida(self):
        """Cubre tambien las raices de agregados de `views.py` (filtros), que
        la guardia estatica de `aggregates.py` no mira."""
        _excluir(self.client, self.x.pk)
        excluida = self._capturar()
        self.x.delete()
        borrada = self._capturar()
        for nombre in excluida:
            self.assertEqual(_normalizar(excluida[nombre]), _normalizar(borrada[nombre]), nombre)

    def test_cada_tabla_del_csv_da_lo_mismo_que_sin_la_partida(self):
        _excluir(self.client, self.x.pk)
        excluida = self._capturar_csv()
        self.x.delete()
        borrada = self._capturar_csv()
        self.assertIn("matches", excluida)
        for tabla in excluida:
            self.assertEqual(excluida[tabla], borrada[tabla], tabla)

    def test_toda_ruta_esta_clasificada(self):
        nombres = {p.name for p in urls.urlpatterns}
        grupos = (COMPARADAS, NO_AGREGADOS, SOLO_POST)
        self.assertFalse(COMPARADAS & NO_AGREGADOS)
        self.assertFalse(COMPARADAS & SOLO_POST)
        self.assertFalse(NO_AGREGADOS & SOLO_POST)
        self.assertEqual(nombres, set().union(*grupos))
        for nombre, ruta in RUTAS_SOLO_POST.items():
            self.assertEqual(self.client.get(ruta).status_code, 405, nombre)


class ExcluidaSigueVisibleTests(_ConPartidaX):
    def test_sigue_en_el_listado_marcada(self):
        antes = self.client.get("/api/matches/").json()
        _excluir(self.client, self.x.pk)
        despues = self.client.get("/api/matches/").json()
        self.assertEqual(antes["total"], despues["total"])
        fila = next(m for m in despues["matches"] if m["id"] == self.x.pk)
        self.assertTrue(fila["excluded"])
        otras = [m for m in despues["matches"] if m["id"] != self.x.pk]
        self.assertTrue(otras)
        self.assertTrue(all(m["excluded"] is False for m in otras))

    def test_el_my_rating_de_una_excluida_se_mide_contra_el_baseline_contable(self):
        con_x = agg.rating_baseline()
        _excluir(self.client, self.x.pk)
        contable = agg.rating_baseline()
        self.assertNotEqual(round(con_x, 6), round(contable, 6))
        promedio = (
            agg.RoundPlayer.objects.filter(is_me=True, round__match=self.x)
            .aggregate(v=agg.Avg(agg.rating_points_expr()))["v"]
        )
        fila = next(
            m for m in self.client.get("/api/matches/").json()["matches"] if m["id"] == self.x.pk
        )
        self.assertEqual(fila["my_rating"], round(promedio / contable, 2))
        self.assertNotEqual(fila["my_rating"], round(promedio / con_x, 2))

    def test_el_detalle_de_una_excluida_sigue_completo(self):
        antes = self.client.get(f"/api/matches/{self.x.pk}/").json()
        _excluir(self.client, self.x.pk)
        despues = self.client.get(f"/api/matches/{self.x.pk}/").json()
        for campo in ("rounds", "rounds_won", "kills", "deaths", "headshots",
                      "opening_kills", "opening_deaths"):
            self.assertEqual(antes["my_totals"][campo], despues["my_totals"][campo], campo)
        self.assertEqual(antes["my_totals"]["rounds"], 4)
        self.assertEqual(_sin_rating(antes["rounds"]), _sin_rating(despues["rounds"]))
        self.assertEqual(_sin_rating(antes["scoreboard"]), _sin_rating(despues["scoreboard"]))
        self.assertFalse(antes["match"]["excluded"])
        self.assertTrue(despues["match"]["excluded"])
        self.assertEqual(antes["match"]["map"], despues["match"]["map"])
        self.assertIn("(id 987654)", despues["match"]["map"])

    def test_health_cuenta_todas_las_importadas(self):
        _excluir(self.client, self.x.pk)
        data = self.client.get("/api/health/").json()
        self.assertEqual(data["matches"], 7)


class IdaYVueltaTests(_ConPartidaX):
    def test_volver_a_incluirla_deja_los_agregados_exactamente_como_antes(self):
        antes, antes_csv = self._capturar(), self._capturar_csv()
        _excluir(self.client, self.x.pk)
        _excluir(self.client, self.x.pk, False)
        despues, despues_csv = self._capturar(), self._capturar_csv()
        for nombre in antes:
            self.assertEqual(_normalizar(antes[nombre]), _normalizar(despues[nombre]), nombre)
        self.assertEqual(antes_csv, despues_csv)


class ReimportarConservaLaMarcaTests(TestCase):
    def test_reimportar_con_force_no_pierde_la_marca(self):
        rondas = [_ronda(0, 1, 0), _ronda(1, 2, 0), _ronda(2, 3, 0), _ronda(3, 4, 0)]
        lector = mock.Mock()
        lector.read.return_value.to_dict.return_value = {"rounds": rondas}
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        carpeta = Path(tmp.name) / "Match-sintetica"
        carpeta.mkdir()
        with mock.patch("replays.ingest.MatchReader", return_value=lector):
            self.assertTrue(import_match_folder(carpeta).ok)
            partida = Match.objects.get(match_id="sintetica")
            _excluir(self.client, partida.pk)
            self.assertTrue(import_match_folder(carpeta, force=True).ok)
        otra_vez = Match.objects.get(match_id="sintetica")
        self.assertEqual(otra_vez.pk, partida.pk)
        self.assertIs(otra_vez.excluded, True)


# --------------------------------------------------------------------- guardia estatica


def _arbol_de_aggregates() -> ast.Module:
    return ast.parse(Path(agg.__file__).read_text(encoding="utf-8"))


def _funciones_por_nodo(arbol: ast.Module) -> dict[int, str | None]:
    """La funcion de nivel mas interno que contiene cada nodo (None: modulo)."""
    salida: dict[int, str | None] = {}

    def recorrer(nodo, funcion):
        for hijo in ast.iter_child_nodes(nodo):
            actual = hijo.name if isinstance(hijo, (ast.FunctionDef, ast.AsyncFunctionDef)) else funcion
            salida[id(hijo)] = actual
            recorrer(hijo, actual)

    recorrer(arbol, None)
    return salida


def _cadena(llamada: ast.Call) -> tuple[ast.AST, list[ast.Call]]:
    """Baja por `func` y `value` hasta la raiz; devuelve la raiz y los eslabones."""
    eslabones = []
    nodo: ast.AST = llamada
    while True:
        if isinstance(nodo, ast.Call):
            eslabones.append(nodo)
            nodo = nodo.func
        elif isinstance(nodo, ast.Attribute) and not (
            isinstance(nodo.value, ast.Name) and nodo.attr == "objects"
        ):
            nodo = nodo.value
        else:
            return nodo, eslabones


def _es_manager(raiz: ast.AST, modelo: str) -> bool:
    return (
        isinstance(raiz, ast.Attribute)
        and raiz.attr == "objects"
        and isinstance(raiz.value, ast.Name)
        and raiz.value.id == modelo
    )


def _es_is_me_true(kw: ast.keyword) -> bool:
    # `is_me=False` son los otros de tus rondas: se correlacionan con una
    # consulta que ya salio de una raiz contable, no son raiz.
    return (
        kw.arg in ("is_me", "player__is_me")
        and not (isinstance(kw.value, ast.Constant) and kw.value.value is False)
    )


def _lleva_is_me(eslabon: ast.Call) -> bool:
    if any(_es_is_me_true(kw) for kw in eslabon.keywords):
        return True
    for arg in eslabon.args:
        for sub in ast.walk(arg):
            if (
                isinstance(sub, ast.Call)
                and isinstance(sub.func, ast.Name)
                and sub.func.id == "Q"
                and any(_es_is_me_true(kw) for kw in sub.keywords)
            ):
                return True
    return False


class GuardiaEstaticaTests(TestCase):
    """Red secundaria: atrapa la regresion tipica (una consulta raiz nueva que
    no pasa por los helpers), no prueba semantica. La primaria es la
    comparacion de arriba."""

    def setUp(self):
        self.arbol = _arbol_de_aggregates()
        self.funcion = _funciones_por_nodo(self.arbol)
        # solo la llamada mas externa de cada cadena
        internas = set()
        for nodo in ast.walk(self.arbol):
            if isinstance(nodo, ast.Call):
                _, eslabones = _cadena(nodo)
                internas.update(id(e) for e in eslabones[1:])
        self.cadenas = [
            n for n in ast.walk(self.arbol) if isinstance(n, ast.Call) and id(n) not in internas
        ]

    def test_tus_rondas_salen_de_rondas_contables(self):
        permitidas = {"rondas_contables", "_mia_en_la_ronda"}
        fuera = []
        for llamada in self.cadenas:
            raiz, eslabones = _cadena(llamada)
            if not _es_manager(raiz, "RoundPlayer"):
                continue
            if any(_lleva_is_me(e) for e in eslabones):
                if self.funcion.get(id(llamada)) not in permitidas:
                    fuera.append((llamada.lineno, self.funcion.get(id(llamada))))
        self.assertEqual(fuera, [])

    def test_las_partidas_salen_de_partidas_contables(self):
        fuera = []
        for llamada in self.cadenas:
            raiz, eslabones = _cadena(llamada)
            if not _es_manager(raiz, "Match"):
                continue
            if self.funcion.get(id(llamada)) == "partidas_contables":
                continue
            primero = eslabones[-1]
            metodo = primero.func.attr if isinstance(primero.func, ast.Attribute) else None
            claves = {kw.arg for kw in primero.keywords}
            if metodo == "filter" and claves & {"id__in", "pk__in"}:
                continue
            if metodo == "get" and "pk" in claves:
                continue
            fuera.append((llamada.lineno, self.funcion.get(id(llamada))))
        self.assertEqual(fuera, [])

    def test_la_guardia_ve_una_consulta_raiz_sin_helper(self):
        """La guardia no es decorativa: un `RoundPlayer.objects.filter(is_me=True)`
        suelto en una funcion cualquiera aparece."""
        arbol = ast.parse(
            "def nueva():\n"
            "    return RoundPlayer.objects.select_related('round').filter(is_me=True).count()\n"
        )
        llamada = next(n for n in ast.walk(arbol) if isinstance(n, ast.Call))
        raiz, eslabones = _cadena(llamada)
        self.assertTrue(_es_manager(raiz, "RoundPlayer"))
        self.assertTrue(any(_lleva_is_me(e) for e in eslabones))
