# 68. Partidas con marcador que no cierra quedan sin resultado

estado: revisado
candado: qa 2026-10-30T20:04Z
rama: claude/equipo-dev/68-partidas-sin-cerrar-sin-resultado
tipo: bug
epica: -
area: backend
prioridad: 2
fuente: decision del humano 2026-10-28 en `## Para el equipo` de `ESTADO.md` (aviso de la ficha 50, idea G7 de `ALCANCE.md`); `ingest.py:169` decide `won` solo por quien tiene mas rondas
archivos: backend/replays/analytics/reglas_partida.py, backend/replays/ingest.py, backend/replays/recompute.py, backend/replays/management/commands/recompute.py, backend/tests/test_match_point.py, backend/tests/test_ingest.py, backend/tests/test_recompute.py, backend/tests/test_api.py, docs/metricas.md
turnos: po 20261029T0004Z, arquitecto 20261029T0404Z, dev 20261030T1604Z, revisor 20261030T1653Z

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

Dev 20261030T1604Z, sobre `origin/dev@0fedc7b`.

Implementado segun el diseno, sin desvios de fondo:

- `reglas_partida.resultado(mio, suyo, regla)`, sin Django; docstring del
  modulo menciona que tambien decide el resultado.
- `ingest.py`: `match_type` y `code_version` a variables locales; `won` sale
  de `resultado(..., regla_para(match_type, code_version))`.
- `recompute.py`: `_recompute_resultados(dry_run)` con `bulk_update` de las
  que cambian, dentro de la misma transaccion; `RecomputeResult.matches_changed`
  entra en `changed`. El comando suma "y N partidas (resultado)" al resumen,
  y `help`/docstring lo dicen.
- `docs/metricas.md`, fila **Partidas ganadas**: cuando una partida queda
  incompleta, que se corrige con `recompute` y el limite de la rendicion.

Tests (todos con el nombre del diseno, mas algunos):

- `ReglasTests`: los 5 del diseno + `test_ranked_empatada_queda_sin_resultado`.
- `test_ingest.py`, clase `ResultadoAlImportarTests`: el ingest se prueba de
  punta a punta con `MatchReader` simulado (rondas sin jugadores ni eventos):
  `test_una_ranked_tres_a_dos_se_importa_sin_resultado` y
  `test_una_ranked_cuatro_a_dos_se_importa_como_victoria`.
- `test_recompute.py`, clase `ResultadoDePartidaTests`: los 3 del diseno +
  `test_el_comando_cuenta_las_partidas_que_cambian` (dry-run "1 partidas
  (resultado)", segunda corrida "Nada que recalcular").
- `test_api.py`: `test_la_ranked_incompleta_sale_del_winrate_de_partidas`; la
  3-2 nace `won=True` (factory) y la deja en `None` el `recompute()`, asi el
  test pasa por el codigo nuevo y no por un `update` a mano.

Revision ciega previa (subagente con `revision.md`): sin bloqueantes. Se
tomaron dos menores (test de API via `recompute`, docstring del modulo).
Quedan anotados para QA:

- `seed_demo` siembra Ranked Y9S4 con marcadores 4-3 y 3-2 como victorias
  (`won=True`). El e2e no corre `recompute`, asi que no cambia; pero si
  alguien corre `recompute` sobre la base demo, esas partidas pasan a
  incompletas. No se toco `seed_demo` (cambiaria los numeros del e2e); si
  se quiere coherencia, ficha aparte.
- La rendicion antes de 4 queda incompleta (limite ya en `metricas.md` y en
  `## Para el humano`).

`check.sh`: Todo en verde (851 tests backend, 133 frontend, build, 53 e2e).

Skills: no aplica. Sin arena.

## Revision 2026-10-30 sobre f0b3782

Revisor 20261030T1653Z. Rama al dia con `origin/dev@0fedc7b` (sin merge).
`check.sh` en `Todo en verde.` sobre `f0b3782` (codigo de `00b8f94`): ruff
ok, 851 tests backend (4 omitidos, ninguno del diff), 133 vitest, build ok,
53 e2e.

Revision: no fue a ciegas. Esta sesion no tenia herramienta de subagentes,
y la ficha se leyo al reclamar; la pasada con `revision.md` sobre el diff
sin `docs/backlog` la hizo el lider. Sin hallazgos bloqueantes. Confirmado:

- `resultado()` contra la regla Ranked (4, prorroga 5): 4-0, 4-2, 5-3 y 5-4
  cierran; 3-2 y 4-3 no; 4-4 `None`; 6-2 (marcador imposible) cierra, sin
  tercer estado. Es simetrica: 2-4 y 3-5 son derrota.
- El marcador de la ultima ronda es el de despues de jugarla desde Y9S4
  (`events.py:392`, `teamscore` contra `startingteamscore`), y la regla solo
  existe desde Y9S4: no hay corrimiento de una ronda. Antes de Y9S4
  `regla_para` da `None` y el resultado sigue siendo el de hoy.
- Nada mas escribe `Match.won` (no hay override de resultado), asi que
  `recompute` no pisa una decision del usuario. Frontend y agregados leen
  `won`/`result` del backend; ninguno recalcula el ganador desde el marcador.
- `_recompute_resultados` corre dentro de la transaccion de `recompute()`;
  `dry_run` solo muta objetos en memoria.
- Mutacion (worktree aparte, `test_match_point`, `test_ingest`,
  `test_recompute`, `test_api`): ingest con la regla vieja -> cae
  `test_una_ranked_tres_a_dos_se_importa_sin_resultado`; `recompute()` sin
  llamar a `_recompute_resultados` -> caen 4; `resultado` sin regla -> 7;
  dry-run que escribe -> 1; `cierra(max, ...)` en vez de `max - 1` -> 7;
  `changed` sin `matches_changed` -> 2.
- Base demo (`seed_demo` + `recompute`): 200 en todas las rutas GET de
  `/api/` con las 29 partidas incompletas; `/api/overview/` da
  `match_winrate: None`, `matches_undecided: 29`, sin division por cero.

Test de borde agregado (verde, y cae si `recompute` ignora la version):
`test_recompute_no_toca_una_ranked_anterior_a_y9s4` (`e561bcb`). Con el,
`check.sh` otra vez en `Todo en verde.`: ruff ok, 852 tests backend (4
omitidos), 133 vitest, build ok, 53 e2e.

Hallazgo menor, no bloquea (fuera de `archivos:`):

- [test] `backend/replays/management/commands/seed_demo.py:181` (y `:56`)
  Que pasa: las 29 partidas demo son Ranked Y9S4 4-3 con `won=True`, un
  estado que el import ya no produce; con 7 rondas por partida ninguna
  Ranked cierra (las cerradas tienen 4, 5, 6, 8 o 9 rondas).
  Como reproducirlo: base vacia, `seed_demo --force`, `recompute --dry-run`
  -> "... y 29 partidas (resultado)"; despues de `recompute`, las 29 son
  `incompleta`. El e2e no corre `recompute` y sigue verde.
  Arreglo sugerido: ficha aparte que cierre los marcadores del seed (cambia
  los numeros del e2e); no entra en esta.

Ficha:

- Criterio 1 -> `ReglasTests` (`test_ranked_tres_a_dos_no_cierra_la_partida`,
  `..._cuatro_a_dos_...`, `..._cinco_a_cuatro_...`,
  `..._cuatro_a_tres_...`, `..._empatada_...`) y `ResultadoAlImportarTests`
  (ingest real con `MatchReader` simulado, 3-2 -> `incompleta`, 4-2 ->
  victoria).
- Criterio 2 -> `test_sin_regla_gana_el_que_tiene_mas_rondas`; la Unranked
  3-2 sigue `True` en `test_recompute_deja_sin_resultado_la_ranked_que_no_cierra`.
- Criterio 3 -> `ResultadoDePartidaTests` (dry-run, idempotencia, comando);
  sin migracion.
- Criterio 4 -> `test_la_ranked_incompleta_sale_del_winrate_de_partidas`.
- Criterio 5 -> fila **Partidas ganadas** de `metricas.md`; las filas que
  ya hablaban de partidas sin resultado (Margen final, Lado inicial,
  Tamano del grupo) siguen siendo ciertas.
- El diff toca exactamente `archivos:`. Identificadores sin tildes, sin
  `print` ni `console.log`; no hay texto nuevo de UI.

Veredicto: aprobar -> `revisado`.

## QA <fecha> sobre <sha>

## Verificar en el PC

## Pendiente

## Para el humano

Sin decision pendiente (la tomaste el 2026-10-28). Aviso: una ranked que
termino por rendicion del rival (sin llegar a 4) tambien queda incompleta;
si eso pasa seguido en tus replays, avisa y se busca otra señal.
