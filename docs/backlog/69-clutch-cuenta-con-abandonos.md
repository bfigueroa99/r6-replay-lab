# 69. El 1vX cuenta cuando un compañero se fue

estado: entregado
candado: -
rama: claude/equipo-dev/69-clutch-cuenta-con-abandonos
tipo: bug
epica: -
area: backend
prioridad: 2
fuente: decision del humano 2026-10-28 en `## Para el equipo` de `ESTADO.md` (pregunta de la ficha 31); `pydissect/stats.py:100-104` arma `winners_alive` solo con `died`, que `PlayerLeave` no marca
archivos: backend/replays/analytics/metrics.py, backend/replays/recompute.py, backend/replays/management/commands/recompute.py, backend/tests/test_clutch.py, backend/tests/test_player_stats.py, backend/tests/test_recompute.py, docs/metricas.md
turnos: po 20261029T0004Z, arquitecto 20261030T1652Z, dev 20261103T0403Z-cYjVEvZ, revisor 20261103T0804Z-chGRfoT, qa 20261103T1205Z-cZPEnjG, release 20261103T1205Z-cZPEnjG


## PR

Titulo: `[equipo-dev][backend] El 1vX cuenta cuando un compañero se fue`

### Que cambia

Si un compañero abandona la partida y despues quedas ultimo vivo y ganas la
ronda, ahora el clutch te cuenta: suma en Clutch, en el record "Clutch mas
grande" y en el rating. Un rival que se fue tampoco suma al X. Lo ya
importado se corrige con `manage.py recompute`, sin reparsear. Solo cambian
partidas anteriores a Y9S1: desde ahi el `.rec` no trae `PlayerLeave`.

### Por que esto y no otra cosa

Decision del humano del 2026-10-28 (pregunta de la ficha 31). La regla va en
la app (`metrics.one_vx`), no en el parser, que sigue a r6-dissect como en la
ficha 67. Descartado: marcar el abandono como muerte en `died` (cambiaria K/D
y Supervivencia, fuera de alcance).

### Como se probo

- `check.sh` (con `verificar.sh`): VERDE d0a2649, 873 tests backend, 153 vitest, 54 e2e.
- Tests nuevos: `test_clutch.OneVxTests` (compañero que se fue, rival que se
  fue, muerto que se desconecta, quien se fue no cobra, compañero que se va
  despues de la ultima muerte, compañero que se fue antes, sin ganador,
  ganador = ultimo equipo con `won`); `ImportClutchTests.test_el_import_cuenta_el_clutch_con_un_companero_que_se_fue`;
  `test_player_stats.OneVxParidadTests` (3000 rondas sin abandonos = parser;
  el parser sigue contando al que se fue como vivo); `test_recompute.RecomputeOneVxTests`
  (corrige, `--dry-run`, idempotente).
- Manual (QA): base sembrada con los dos escenarios, `recompute --dry-run`
  2 filas, `recompute` 2, tercera corrida "Nada que recalcular"; `curl
  /api/matches/1/` da `one_vx: 2`; overview con clutch 2 y record 2.
  Mutaciones M1-M4 caen; fuzz de paridad de 200.000 rondas: 0 diferencias.
- OMC: plan=— · revisión=3 hallazgos (2 arreglados) · verificación=— (Implementacion)
- OMC: plan=— · revisión=2 hallazgos LOW (0 arreglados, ninguno bloquea) · verificación=— (Revision)
- OMC: plan=— · revisión=— · verificación=PASS (QA)

### Riesgos y lo que no entra

Sin migracion, sin frontend. `recompute` sobre la base real reescribe
`one_vx` solo en rondas con abandonos anteriores a Y9S1. Fuera: `clutch_vs`
(ya tomaba `PlayerLeave`), abandonos como metrica propia (idea D3 de
`ALCANCE.md`), el teamkill del ultimo en pie y las rondas sin ganador, que
siguen a r6-dissect.

### Como probarlo en 2 minutos

```
cd backend; python manage.py test tests.test_clutch tests.test_recompute tests.test_player_stats
```

Tiene que dar `OK` (86 tests).

### Verificar en el PC

`manage.py backup`, `manage.py recompute --dry-run` (cuenta las filas que
cambian) y `manage.py recompute` sobre la base real.

### Para el humano

Nada.

### Candidatos descubiertos

Ninguno.

## Que gana quien usa la app

Si un compañero abandona y despues quedas ultimo vivo y ganas la ronda, hoy
no te cuenta el clutch: el que se fue sigue figurando "vivo". Con el arreglo
ese 1vX suma en Clutch, en el record "Clutch mas grande" y en el rating, igual
que ya lo ve "Clutch: intentos y conversión" (`clutch_vs`, ficha 55).

## Criterios de aceptacion

- [x] Compañero que sale por `PlayerLeave`: el ultimo que gana suma 1v2 (antes 0).
- [x] Un rival que se fue no suma al X.
- [x] Sin abandonos, el 1vX no cambia (paridad con r6-dissect).
- [x] `manage.py recompute` corrige lo importado; `--dry-run` cuenta; idempotente.
- [x] `docs/metricas.md`, fila **1vX (clutch)** al dia.

## Diseno

Arquitecto 20261030T1652Z: funcion unica `metrics.one_vx(eventos, team_of,
ganador)` (port de `stats.player_round_stats`; `PlayerLeave` saca de la
ronda a compañero o rival) y `metrics.equipo_ganador(teams)`, usadas por el
import y por `recompute`. Sin reparsear: `Event` guarda `PlayerLeave` y
`Round.teams` guarda `won`. El detalle de la regla esta en el docstring y en
`git log` de esta rama.

## Implementacion

Dev 20261103T0403Z-cYjVEvZ, segun el diseno. Revision ciega: arreglados la
fila de `metricas.md` (el X se cuenta desde el final) y un fixture que no
detectaba un doble descuento.

## Revision

Revisor 20261103T0804Z-chGRfoT: aprobar. Dos LOW sin bloquear: el valor
inicial de `one_vx` en `analyse_round` sale del parser y siempre se pisa; la
ganancia se limita a replays anteriores a Y9S1 (dicho en la doc y en el PR).

## QA 2026-11-03 sobre d0a2649

QA 20261103T1205Z-cZPEnjG. Rama al dia con `origin/dev@6aee89a` (merge-tree sin conflicto).

- `verificar.sh` (check.sh completo): VERDE d0a2649 en 122 s, 873 tests
  backend, 153 vitest, 54 e2e.
- Base sembrada (script en el scratchpad, `SQLITE_PATH` temporal, nada al
  repo) con `factories`: escenario 1 (A0-A2 matan a B0-B2, B3 mata a A0-A2,
  A3 `PlayerLeave`, A4 mata a B3 y B4) y escenario 2 (B3 mata a A0-A3, B4
  `PlayerLeave`, A4 mata a B3), `one_vx` de A4 en 0 como el import viejo:
  - `manage.py recompute --dry-run`: "cambiarian 2 filas de jugador ... sobre 2 rondas".
  - `manage.py recompute`: "se actualizaron 2 filas"; otra vez: "Nada que
    recalcular ... las 2 rondas ya estan al dia" (idempotente).
  - `one_vx` de A4: escenario 1 = 2 (criterio 1), escenario 2 = 1 (criterio 2).
  - `runserver` + `curl /api/matches/1/`: A4 `one_vx: 2`, scoreboard
    `clutches: 1`. Con A4 como `is_me`: `/api/overview/` `clutch_rounds: 2`,
    `records.biggest_clutch.value: 2`; `/api/teammates/` `clutch_conversion`
    1v2 2/2 (no cambia: ya tomaba `PlayerLeave`).
  - Bordes: `/api/overview/?until=foo`, `/api/matches/?page=-1`,
    `/api/matches/?map=`, `/api/sessions/?days=99999999999`, `/api/coach/`,
    `/api/trends/`, `/api/compare/`, `/api/players/1/`,
    `/api/export/?table=rounds`: 200; `/api/matches/999/`: 404.
- Base vacia: `recompute` "Nada que recalcular ... 0 rondas"; `/api/overview/`,
  `/api/matches/`, `/api/teammates/` 200.
- Sin migracion, sin frontend (chunk sin cambios), sin parser (`pydissect/` no se toca).
- Mutacion (`tests.test_clutch tests.test_recompute tests.test_player_stats`,
  restaurado despues): M1 `PlayerLeave` ignorado en `one_vx` -> 10 fallan;
  M2 rival que se fue suma al X -> 2 fallan (`test_un_rival_que_se_fue_no_suma_al_x`);
  M3 sin la guarda `all(salida[n] < i ...)` -> 2 fallan
  (`test_si_un_companero_se_va_despues_de_la_ultima_muerte_nadie_cobra`);
  M4 `one_vx` fuera de `CAMPOS` de `recompute` -> 3 de `RecomputeOneVxTests` fallan.
- omc-verifier (general-purpose con su cuerpo): PASS, 5/5 VERIFIED; corrio
  ademas un fuzz de paridad de 200.000 rondas sin abandonos contra
  `pydissect.stats`: 0 diferencias.

Veredicto: `aprobado`.

Skills: no aplica.
OMC: plan=— · revisión=— · verificación=PASS

## Verificar en el PC

- `manage.py backup`, `manage.py recompute --dry-run` (cuenta las filas de
  jugador que cambian; solo partidas anteriores a Y9S1 con abandonos) y
  `manage.py recompute` sobre la base real.

## Para el humano

Sin decision pendiente (la tomaste el 2026-10-28).
