# 68. Partidas con marcador que no cierra quedan sin resultado

estado: disenado
candado: -
rama: -
tipo: bug
epica: -
area: backend
prioridad: 2
fuente: decision del humano 2026-10-28 en `## Para el equipo` de `ESTADO.md` (aviso de la ficha 50, idea G7 de `ALCANCE.md`); `ingest.py:169` decide `won` solo por quien tiene mas rondas
archivos: backend/replays/analytics/reglas_partida.py, backend/replays/ingest.py, backend/replays/recompute.py, backend/replays/management/commands/recompute.py, backend/tests/test_match_point.py, backend/tests/test_ingest.py, backend/tests/test_recompute.py, backend/tests/test_api.py, docs/metricas.md
turnos: po 20261029T0004Z, arquitecto 20261029T0404Z

## PR

(La escribe el Release manager al final.)

## Que gana quien usa la app

Si falta el `.rec` de la ultima ronda, hoy una ranked que iba 3-2 entra como
victoria (o derrota) por 1 y mueve tu winrate de partidas. Con el arreglo esa
partida queda "incompleta": sigue en el listado, pero no suma ni resta en los
winrates de partida.

## Criterios de aceptacion

- [ ] Importar una partida `Ranked` (regla de `reglas_partida.py`) con
      marcador final 3-2 deja `Match.won = None` y `result == "incompleta"`;
      4-2, 2-4 y 5-4 (prorroga) siguen en `True`/`False`; 4-3 (sin cerrar,
      la prorroga va a 5) queda `None`. La comprobacion vive en
      `reglas_partida.py` (sin Django) con test propio.
- [ ] Un tipo de partida sin regla (`regla_para` devuelve None, p. ej.
      `Unranked` o `Custom`) se comporta como hoy: gana el que tiene mas
      rondas, empate = `None`.
- [ ] Lo ya importado se corrige sin reparsear: `manage.py recompute`
      (o el camino que elija el Arquitecto, sin migracion de esquema)
      recalcula `Match.won` con la misma funcion; `--dry-run` cuenta las
      partidas que cambian y una segunda corrida no cambia nada.
- [ ] Con una partida 3-2 Ranked y otra 4-1 Ranked ganada, el winrate de
      partidas de `/api/overview/` (`matches_summary`, ficha 64) es 100 %
      sobre 1 partida, y el listado `/api/matches/` muestra la 3-2 como
      incompleta.
- [ ] `docs/metricas.md`: la fila que define el resultado de partida dice
      cuando una partida queda incompleta (marcador que no cierra segun la
      regla del tipo).

## Fuera de alcance

- La lista de partidas dudosas en Datos (resto de la idea G7): otra ficha si
  hace falta.
- Reglas para otros tipos de partida sin fuente citable (`reglas_partida.py`
  solo admite reglas con fuente).
- Abandonos o rendiciones que cierran la partida antes de tiempo: si el
  marcador no llega, queda incompleta (se anota como limite en `metricas.md`).
- El winrate de rondas: no cambia.

## Diseno

Arquitecto 20261029T0404Z, sobre `origin/dev@c3597f4`.

**Implementar despues de que #67 se mergee**: las dos tocan
`backend/replays/recompute.py` y el comando `recompute`. No bloquea el
diseno; ordena el trabajo para que el segundo Dev parta del recompute ya
extendido.

Idea: la partida esta cerrada si el que tiene mas rondas, viniendo de una
menos, cerraba con la regla del tipo. Eso ya lo dice `cierra()` de
`reglas_partida.py`, que usa match point: `cerrada = mio != suyo and
cierra(max - 1, min, regla)`. Comprobado a mano con Ranked (4, prorroga 5):
4-2 -> `cierra(3,2)` objetivo 4, cerrada; 3-2 -> `cierra(2,2)` objetivo 4, no;
4-3 -> `cierra(3,3)` objetivo 5 (prorroga), no; 5-3 -> `cierra(4,3)` si;
5-4 -> `cierra(4,4)` si; 4-4 empate, `None`. Un marcador que se pasa (6-2,
dato raro) da cerrada: no se inventa un tercer estado.

`archivos:` y por que:

- `backend/replays/analytics/reglas_partida.py`: funcion nueva
  `resultado(mio: int, suyo: int, regla: dict | None) -> bool | None`.
  `mio == suyo` -> `None`. Sin regla -> `mio > suyo` (lo de hoy). Con regla:
  si `not cierra(max(mio, suyo) - 1, min(mio, suyo), regla)` -> `None`; si
  no, `mio > suyo`. Docstring: por que (un `.rec` faltante deja un marcador
  que la regla no da por terminado). Sin Django, como el resto del modulo.
- `backend/replays/ingest.py:169`: `won` pasa a
  `resultado(my_score, opp_score, regla_para(match_type, code_version))`,
  con `match_type` y `code_version` los mismos que ya se guardan en esa
  llamada (sacarlos a variables locales antes del `update_or_create`).
- `backend/replays/recompute.py`: funcion `_recompute_resultados(dry_run) ->
  int` que recorre `Match.objects.only("id", "match_type", "code_version",
  "my_score", "opponent_score", "won")`, calcula `resultado(...)` con la misma
  `regla_para` y hace `bulk_update(..., ["won"])` de las que cambian (nada si
  `dry_run`). `RecomputeResult` suma `matches_changed: int = 0` y `changed`
  lo incluye. `recompute()` la llama dentro de la misma transaccion. Docstring
  del modulo: "tambien rehace `Match.won` con la regla del tipo de partida".
  No hacen falta eventos: marcador, tipo y version estan en `Match`.
- `backend/replays/management/commands/recompute.py`: el resumen agrega
  `y {result.matches_changed} partidas (resultado)`; `help` y docstring lo
  dicen.
- `docs/metricas.md`, fila **Partidas ganadas** (l.13): "Una partida queda
  incompleta (sin ganador, `won` nulo) cuando su marcador final no la cierra
  segun la regla de su tipo (`reglas_partida.py`: hoy solo Ranked desde Y9S4,
  primero a 4 con prorroga a 5); p. ej. 3-2 o 4-3 por un `.rec` faltante. Un
  tipo sin regla se decide por mas rondas. Limite: una rendicion antes de
  llegar a 4 tambien queda incompleta."
- Tests: `backend/tests/test_match_point.py` (clase `ReglasTests`, que ya
  prueba el modulo), `backend/tests/test_ingest.py`,
  `backend/tests/test_recompute.py`, `backend/tests/test_api.py`.

Tests nuevos (nombres exactos):

- `ReglasTests` en `test_match_point.py`:
  `test_ranked_tres_a_dos_no_cierra_la_partida` (`None`),
  `test_ranked_cuatro_a_dos_es_victoria_y_dos_a_cuatro_derrota`,
  `test_ranked_cinco_a_cuatro_en_prorroga_es_victoria`,
  `test_ranked_cuatro_a_tres_no_cierra_por_la_prorroga` (`None`),
  `test_sin_regla_gana_el_que_tiene_mas_rondas` (`resultado(3, 2, None)` True,
  `resultado(2, 2, None)` None).
- `test_ingest.py`: `test_una_ranked_tres_a_dos_se_importa_sin_resultado`
  (si el test de ingest arma el replay sintetico con `matchType` y
  `codeVersion`; si armarlo cuesta, basta con el test de `recompute` y la
  funcion pura, anotado en Implementacion).
- `test_recompute.py`: `test_recompute_deja_sin_resultado_la_ranked_que_no_cierra`
  (Match Ranked `code_version=Y9S4`, 3-2, `won=True` -> `None`; una Unranked
  3-2 sigue `True`), `test_recompute_dry_run_cuenta_las_partidas_sin_escribir`,
  `test_recompute_de_resultados_es_idempotente`.
- `test_api.py`: `test_la_ranked_incompleta_sale_del_winrate_de_partidas`:
  con `factories`, una Ranked 3-2 (`won=None`) y una Ranked 4-1 ganada,
  `/api/overview/` -> `matches_summary.match_winrate == 100` y
  `matches_decided == 1`; `/api/matches/` -> la 3-2 con `result ==
  "incompleta"`. (`match_result` ya etiqueta `None` como incompleta; no se
  toca.) Ubicar `matches_summary` en la respuesta real de `/api/overview/`
  antes de escribir el assert.

Orden: (1) `resultado` + `ReglasTests`; (2) ingest; (3) recompute + comando +
tests; (4) test de API; (5) `metricas.md`; (6) `check.sh`.

Que puede romperse: tests y `factories` que crean Ranked con
`code_version >= Y9S4` y un marcador que no cierra (p. ej. 3-1) **no** se
rompen al importar (no pasan por ingest), pero si un test corre `recompute()`
sobre ellos, su `won` pasa a `None`. Revisar `factories.py` (valores por
defecto de `match_type`, `code_version`, `my_score`) y los tests que llaman
`recompute`. `seed_demo` siembra sus partidas sin ingest: si alguna es Ranked
Y9S4+ con un marcador que no cierra, el e2e no cambia (no corre recompute),
pero el QA lo tiene que mirar.

Verificacion manual: base sembrada con una Ranked 3-2 `won=True`,
`manage.py recompute --dry-run` -> "1 partidas (resultado)"; `recompute`;
`/api/matches/` la muestra incompleta; segunda corrida "Nada que recalcular".

Sin migracion, sin umbral, sin fila nueva de `metricas.md`.

Skills: no aplica (backend puro, mismo patron que `recompute`). Sin arena.

## Implementacion

## Revision <fecha> sobre <sha>

## QA <fecha> sobre <sha>

## Verificar en el PC

## Pendiente

## Para el humano

Sin decision pendiente (la tomaste el 2026-10-28). Aviso: una ranked que
termino por rendicion del rival (sin llegar a 4) tambien queda incompleta;
si eso pasa seguido en tus replays, avisa y se busca otra señal.
