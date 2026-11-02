"""Los casos de apertura de la timeline (frontend) contra el import (backend).

`frontend/src/aperturas.js` repite en el navegador la regla de
`opening_kill`/`opening_death` y `entry_kill`; los dos lados leen los mismos
casos para que no se separen sin que caiga un test.
"""

from __future__ import annotations

import json
from pathlib import Path

from django.test import SimpleTestCase

from replays.analytics.metrics import analyse_round

CASOS = Path(__file__).resolve().parents[2] / "frontend" / "src" / "casosApertura.json"


def round_data(caso: dict) -> dict:
    eventos = caso["eventos"]
    return {
        "players": [{"username": nick, "teamIndex": equipo} for nick, equipo in caso["jugadores"]],
        "teams": [{}, {}],
        "stats": [],
        # El reloj del feed baja: el primer evento es el de mas segundos.
        "matchFeedback": [
            {
                "type": {"name": kind},
                "username": actor,
                "target": target,
                "timeInSeconds": 170 - i,
            }
            for i, (kind, actor, target) in enumerate(eventos)
        ],
    }


def con(metricas: dict, campo: str, equipo: int | None = None) -> set[str]:
    return {
        nick
        for nick, m in metricas.items()
        if m[campo] and (equipo is None or m["team_index"] == equipo)
    }


class CasosAperturaTests(SimpleTestCase):
    def test_los_casos_de_la_timeline_son_los_del_import(self):
        casos = json.loads(CASOS.read_text(encoding="utf-8"))
        self.assertGreaterEqual(len(casos), 6)
        for caso in casos:
            with self.subTest(caso["nombre"]):
                metricas = analyse_round(round_data(caso))["players"]
                nicks = {nick for nick, _ in caso["jugadores"]}

                abre = abrio = set()
                if caso["apertura"] is not None:
                    kind, actor, target = caso["eventos"][caso["apertura"]]
                    if kind == "Kill":
                        abre = {actor} & nicks
                        abrio = {target} & nicks
                    else:
                        abrio = {actor} & nicks
                self.assertEqual(con(metricas, "opening_kill"), abre)
                self.assertEqual(con(metricas, "opening_death"), abrio)

                entry = set()
                if caso["entry"] is not None:
                    entry = {caso["eventos"][caso["entry"]][1]}
                self.assertEqual(con(metricas, "entry_kill", caso["mi_equipo"]), entry)
