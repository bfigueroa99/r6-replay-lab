# 122. Cuando te toco por ultima vez

estado: aprobado
candado: release 2026-11-13T19:34Z
rama: claude/equipo-dev/122-cuando-te-toco-por-ultima-vez
tipo: funcionalidad
epica: rivales
area: backend
prioridad: 3
fuente: ALCANCE.md D10
archivos: backend/replays/analytics/aggregates.py (_record, repeated_rivals, _filas_de_stacks), backend/tests/test_duels.py, backend/tests/test_stacks_rivales.py, frontend/src/ultimaVez.js (nuevo), frontend/src/ultimaVez.test.js (nuevo), frontend/src/pages/Duelos.jsx, frontend/e2e/humo.spec.js, docs/metricas.md
turnos: po 20261113T1650Z-c9H2L8Y, arquitecto 20261113T1802Z-c8dAf7p, dev 20261113T1830Z-c2rHpej, revisor 20261113T1858Z-cxdASk3, qa 20261113T1926Z-cq9nfTP

## PR

## Que gana quien usa la app

En Duelos, las tablas Rivales repetidos y Stacks rivales que se repiten
suman una columna "Última vez" con la fecha de la partida mas reciente
contra esa persona o ese grupo. Se distingue al rival que te sigue tocando
esta semana del que fue de una racha de hace meses, sin abrir su perfil.

## Criterios de aceptacion

- [x] Cada fila de `repeated_rivals` y de `rival_stacks`
      (`replays/analytics/aggregates.py`) trae `last_played` en ISO 8601:
      el `max(Match.played_at)` de las partidas que ya cuenta la fila.
      Test con un rival en tres partidas de fechas distintas: sale la mas
      reciente.
- [x] Con filtros globales (`since`/`until`), `last_played` sale de las
      partidas que pasan el filtro, igual que `matches`; test con un
      `until` que deja afuera la ultima partida.
- [x] `rival_stacks_de_partida` (el aviso del detalle, ficha 92) no cambia
      su record; si suma `last_played`, es el mismo valor que la fila de
      Duelos. Test.
- [x] En `Duelos.jsx` las dos tablas muestran la columna "Última vez" con
      la fecha corta del resto de la app y se ordenan por ella; vitest o e2e.
- [x] e2e: en `seed_demo`, Duelos muestra "Última vez" en Rivales
      repetidos con una fecha no vacia; consola limpia.

## Fuera de alcance

- Columna nueva en la base o migracion: sale de la misma consulta.
- Enlace de la fecha a la partida (puede ser una idea aparte).
- "Última vez" en la tabla Por rival (nemesis) de Duelos.

## Diseno

(arquitecto 20261113T1802Z-c8dAf7p, sobre `origin/dev@1de3c54`) Filtros
duros: pasa (`Match.played_at`, ya importado; sin red, sin dependencias, sin
POST, sin migracion). Una forma obvia, ~150 lineas: sin arena ni consenso.

**Backend, `backend/replays/analytics/aggregates.py`.** Las dos tablas y el
aviso del detalle ya arman su record con `_record(ids, resultado)`, sobre
las partidas que la fila cuenta (las que pasan los filtros). Un solo cambio
ahi cubre los tres criterios de backend y garantiza que la fila de Duelos y
el aviso de la partida den la misma fecha:
- `repeated_rivals` y `_filas_de_stacks`: la consulta de resultados pasa a
  `Match.objects.filter(id__in=match_ids).values_list("id", "won",
  "played_at")`, y se arman dos dicts (`resultado` y `fechas`).
- `_record(ids, resultado, fechas)` suma `"last_played":
  max(fechas[mid] for mid in ids).isoformat()` (`ids` nunca es vacio: la
  fila existe porque tiene `min_matches` partidas). Sin consultas nuevas:
  la misma consulta trae una columna mas.
- `rival_stacks_de_partida` hereda el campo por `_filas_de_stacks`; su
  record no cambia.
- `docs/metricas.md`: en las filas **Rival repetido** y **Stack rival
  repetido** (seccion `## Duelos`), sumar: "*Última vez*: la fecha de la
  partida mas reciente de las que cuenta la fila (con los filtros
  aplicados)." No es un numero nuevo; es una columna de esas tablas.

**Tests.**
- `backend/tests/test_duels.py`, clase `RivalesRepetidosTests`:
  `test_la_ultima_vez_es_la_partida_mas_reciente` (un rival en tres partidas
  con `index` 0, 5 y 2 -> `last_played` == `played_at` de la de `index` 5 en
  ISO) y `test_la_ultima_vez_respeta_el_filtro_de_fechas` (`until` que deja
  afuera la mas reciente -> la siguiente).
- `backend/tests/test_stacks_rivales.py`, clase `StacksRivalesTests`:
  `test_el_stack_trae_la_ultima_vez` (dos partidas con el mismo grupo) y
  `test_el_aviso_de_la_partida_da_la_misma_ultima_vez_que_duelos`
  (`rival_stacks_de_partida(match.id)[0]["last_played"] ==
  rival_stacks()[0]["last_played"]`, y el record igual que antes).
- Un `assertNumQueries` vecino de `repeated_rivals`/`rival_stacks`, si
  existe, no cambia; si no existe, no se agrega.

**Frontend.**
- `frontend/src/ultimaVez.js` (nuevo, puro): `fechaCorta(iso)` -> `"DD-MM-AAAA"`
  (el formato de `Jugador.jsx`), `"—"` sin fecha; `fechaCsv(iso)` ->
  `"AAAA-MM-DD"` o `""` (el CSV se ordena bien en Excel). Vitest
  `frontend/src/ultimaVez.test.js`: fecha con hora, sin fecha (`null`,
  `undefined`, `""`), y que `fechaCsv` no lleva hora.
- `frontend/src/pages/Duelos.jsx`, tablas **Rivales repetidos** y **Stacks
  rivales que se repiten**: columna `{ key: 'last_played', label: 'Última
  vez', help: 'La partida más reciente contra esa persona (o ese grupo) entre
  las que cuenta la fila.', render: (row) => fechaCorta(row.last_played),
  csv: (row) => fechaCsv(row.last_played) }` despues de "Partidas". Ordenable:
  `DataTable` ordena por el valor crudo de `key`, y un ISO se ordena bien como
  texto. Sin cambios en el `initialSort`.
- `MatchDetail.jsx` (`StacksRivales`): fuera de alcance; el campo llega y no
  se muestra.

**e2e, `frontend/e2e/humo.spec.js`**, en `Duelos muestra rivales repetidos
con enlace al perfil` (antes del clic): la tabla tiene la cabecera "Última
vez" y la celda de la primera fila es `fechaCorta` del `last_played` de la
primera fila de `/api/duels/` con el mismo orden inicial (o, mas simple, que
matchea `/^\d{2}-\d{2}-\d{4}$/`). Consola limpia.

**Orden.** Tests backend (rojo) -> `_record` + las dos consultas -> vitest ->
`ultimaVez.js` -> columnas en Duelos -> e2e -> `metricas.md` ->
`npm run build` -> `verificar.sh`.

**Que puede romperse.** El campo es aditivo en `/api/duels/` y en el detalle
de partida. `_record` cambia de firma: sus dos llamadas estan en este mismo
archivo. El CSV de las dos tablas gana la columna despues de "Partidas"; no tienen
consumidor automatico en el repo (`git grep rivales-repetidos` solo da
`Duelos.jsx`).

**Archivos ocupados.** Ramas abiertas (79, 119, 120, 121): la 79 toca
`aggregates.py` lejos de `_record`/`repeated_rivals` (hunks en
`base_queryset`, `_sessions_raw`, `by_stack`...), ninguna toca `Duelos.jsx`,
`test_duels.py` ni `test_stacks_rivales.py`; `humo.spec.js` y `metricas.md`
en otras zonas. No se frena.

**Verificacion manual.** `seed_demo`, `/duelos`: "Última vez" en las dos
tablas con fecha; ordenar por esa columna; con `?until=<fecha vieja>` la
fecha baja; "Descargar CSV" con `AAAA-MM-DD`.

Skills: no aplica (una columna con un dato que ya se consulta).
Skills del repo: testing-strategy (Django para el max y el filtro, vitest para el formato, humo e2e para la columna), statistical-analysis (no aplica: una fecha, no una tasa).
OMC: plan=— · revisión=— · verificación=—

## Implementacion

(dev 20261113T1830Z-c2rHpej) Diseno completo, sobre `origin/dev@72fad68`:

- `aggregates.py`: `_resultados_y_fechas(match_ids)` (una sola consulta con
  `id`, `won`, `played_at`, la misma que habia con una columna mas) y
  `_record(ids, resultado, fechas)` con `last_played` = `max(played_at)` de
  las partidas de la fila, en ISO. Lo usan `repeated_rivals` y
  `_filas_de_stacks`, asi que `rival_stacks_de_partida` lo hereda con el
  mismo valor que Duelos. Sin consultas nuevas.
- `ultimaVez.js`: `fechaCorta` (DD-MM-AAAA, como `Jugador.jsx`; `—` sin
  fecha) y `fechaCsv` (AAAA-MM-DD).
- `Duelos.jsx`: columna "Última vez" despues de "Partidas" en Rivales
  repetidos y Stacks rivales que se repiten, ordenable (ISO como texto con
  `localeCompare`), `help` y `csv`.
- `metricas.md`: *Última vez* en las filas Rival repetido y Stack rival repetido.
- e2e: en `Duelos muestra rivales repetidos con enlace al perfil`, la
  cabecera "Última vez" existe y la celda de la primera fila es la fecha de
  `rivals[0].last_played` de `/api/duels/` (el orden inicial es estable).

Tests vistos en rojo antes del codigo (`KeyError: 'last_played'`):
`test_la_ultima_vez_es_la_partida_mas_reciente`,
`test_la_ultima_vez_respeta_el_filtro_de_fechas` (`test_duels.py`),
`test_el_stack_trae_la_ultima_vez`,
`test_el_aviso_de_la_partida_da_la_misma_ultima_vez_que_duelos`
(`test_stacks_rivales.py`, con el record 2-1-1-50.0 igual que antes); vitest
`ultimaVez.test.js` (3, rojo por modulo inexistente). Criterios -> tests: 1 y
2 los dos de `test_duels`; 3 el del aviso; 4 e2e + vitest; 5 e2e. Chunk
inicial `index-*.js` 200.00 kB (Duelos es lazy, 11.58 kB).

Desvio menor: en la fila de stacks, `salida.append(...)` partido en tres
lineas por el limite de 100 de ruff.

verificar.sh: VERDE 8aa8d4de8 (1243 backend, 391 vitest, 105 e2e).

Revision ciega (`omc-code-reviewer`, `revision.md`, 237 lineas): aprobar, 0
hallazgos (miro `max` sobre vacio, `KeyError`, zona horaria con
`USE_TZ = False`, doble consulta, orden de la columna).

Skills: no aplica.
Skills del repo: testing-strategy (Django para el max y el filtro, vitest para el formato, e2e para la columna), ux-copy (`help` con tildes, `—` como el resto), modern-web-guidance (no aplica: columna de un `DataTable` existente, sin CSS ni componente nuevo).
OMC: plan=— · revisión=0 hallazgos · verificación=—

## Revision 2026-11-13 sobre 5dd09ad

(qa 20261113T1858Z-cxdASk3, revisor en el fallback de QA: la 120 la tomo otra corrida) Punto de partida: la rama ya contenia `origin/dev`; `verificar.sh`: VERDE 5dd09adb9 (1243 backend, 391 vitest, 105 e2e).

**Eje de estandares** (`omc-code-reviewer`, prompt de `revision.md`, 106 lineas de diff; un solo tema y menos de 150 lineas: sin eje de intencion ni seguridad): aprobar, 1 LOW **confirmado leyendo el codigo**:
- L1 [estilo, LOW] `frontend/src/ultimaVez.js:6-8`: `fechaCorta` es identica a `fecha` de `frontend/src/pages/Jugador.jsx:21`; si una cambia, la otra queda desalineada. Arreglo: que `Jugador.jsx` importe `fechaCorta`. No bloquea (el diseno pidio "el formato de `Jugador.jsx`" y `Jugador.jsx` esta fuera de `archivos:`).
Verifico ademas: `Match.played_at` no admite nulos (`models.py:74`), `ids` nunca vacio, una sola consulta (`_resultados_y_fechas` reemplaza la que habia), `USE_TZ = False` (ISO sin desfase, `slice(0, 10)` da la fecha local), sin dependencias ni escritura nueva, nada que el `.rec` no traiga. Los tests caerian con el bug: indices 0, 5, 2 (ni primera ni ultima creada) y `until` que deja afuera la mas reciente.

**Ficha.** Criterio 1: `test_la_ultima_vez_es_la_partida_mas_reciente`; 2: `test_la_ultima_vez_respeta_el_filtro_de_fechas`; 3: `test_el_aviso_de_la_partida_da_la_misma_ultima_vez_que_duelos` (record igual); 4: columna en las dos tablas de `Duelos.jsx`, ordenable, vitest `ultimaVez.test.js` + e2e; 5: e2e `Duelos muestra rivales repetidos con enlace al perfil` (cabecera y fecha de la API, consola limpia). Diff dentro de `archivos:`; `metricas.md` con *Última vez* en Rival repetido y Stack rival repetido; identificadores sin tildes, UI con tildes; sin `print` ni `console.log`.

Veredicto: aprobar.

Skills del repo: ninguna (revision con `revision.md`).
OMC: plan=— · revisión=1 hallazgo LOW (0 arreglados: al humano) · verificación=—

## QA 2026-11-13 sobre c7a8e7a

(qa 20261113T1926Z-cq9nfTP) La rama no contenia `origin/dev`: `git merge origin/dev` limpio (db4f5b4), `verificar.sh`: VERDE db4f5b4ec (1257 backend, 398 vitest, 106 e2e). Con el test de borde agregado: VERDE c7a8e7a25 (1258 backend, 398 vitest, 106 e2e).

Base temporal en el scratchpad (`SQLITE_PATH=<scratch>/qa122.sqlite3 R6_ENV_FILE=<scratch>/qa.env`, `manage.py migrate`, `runserver 8122`):

- Base vacia: `curl localhost:8122/api/duels/` -> 200, `rivals` 0, `rival_stacks` 0.
- `manage.py seed_demo` (29 partidas): `/api/duels/` -> Kaid_, Mozzie99, Thorn.exe con 29 partidas y `last_played` `2026-08-05T08:00:00`; stack de los tres igual.
- **Recalculado a mano** (ORM, `played_at` de las partidas de cada rival): ultima `2026-08-05T08:00:00` (coincide). Con `?until=2026-08-03`: la API da 18 partidas y `2026-08-03T23:00:00`; a mano, 2 del 01 + 8 del 02 + 8 del 03 = 18, ultima 23:00 (coincide). `since=2026-08-02&until=2026-08-03`: 16, `2026-08-03T23:00:00`. `until=2026-08-01`: 2, `2026-08-01T23:00:00`.
- Bordes: `until=2000-01-01` -> 200 y listas vacias; `until=foo`, `since=2026-13-40`, `page=-1`, `map=` -> 200, igual que sin filtro (comportamiento previo de los filtros, no regresion).
- Aviso del detalle: `/api/matches/29/` `rival_stacks` -> (29 partidas, 29-0, `2026-08-05T08:00:00`), el mismo `last_played` que Duelos.
- Chunk inicial `index-*.js` 200116 B (el Dev midio 200.00 kB); `ultimaVez.js` va en el chunk lazy de Duelos (11.6 kB).
- **accessibility-review** (Playwright sobre `/duelos`, base sembrada): 2 cabeceras "Última vez", `<button class="th-orden">` con `title`; foco + Enter -> `aria-sort="descending"`; celdas `05-08-2026`; contraste del texto de la celda 14.17:1; consola sin errores. Sin Critical ni Major.
- **validate-data** (fila Rival repetido / Stack rival repetido de `metricas.md`): es una fecha, no una tasa: sin division ni promedio; `ids` nunca vacio (la fila existe con `min_matches`), `played_at` no nulo.
- **Mutacion:** `max` -> `min` en `_record`: caen los 3 tests nuevos de fecha. `max(fechas.values())` (fecha de cualquier partida de la consulta conjunta) **sobrevivia** a todos; agregue `test_la_ultima_vez_de_cada_rival_sale_de_sus_propias_partidas` (`backend/tests/test_duels.py`: dos rivales en partidas distintas), que cae con ese mutante y pasa con el codigo.

Criterios: 1 VERIFIED (API + recalculo + 3 tests), 2 VERIFIED (until/since contra calculo a mano), 3 VERIFIED (detalle = Duelos), 4 VERIFIED (Playwright: dos tablas, orden por teclado), 5 VERIFIED (e2e verde, consola limpia).

Veredicto: aprobado.

Skills del repo: accessibility-review (0 Critical, 0 Major), validate-data (fecha sin tasa; 2 valores recalculados: 2026-08-05T08:00:00 y 18 partidas/2026-08-03T23:00:00).
OMC: plan=— · revisión=— · verificación=PASS

## Para el humano

- (revisor 2026-11-13, no bloquea) `fechaCorta` de `ultimaVez.js` duplica `fecha` de `Jugador.jsx:21`; que `Jugador.jsx` la importe. Lo puede hacer un Dev despues.
