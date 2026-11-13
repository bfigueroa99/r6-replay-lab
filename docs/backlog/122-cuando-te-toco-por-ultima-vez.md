# 122. Cuando te toco por ultima vez

estado: en curso 2026-11-13T18:47Z
candado: -
rama: claude/equipo-dev/122-cuando-te-toco-por-ultima-vez
tipo: funcionalidad
epica: rivales
area: backend
prioridad: 3
fuente: ALCANCE.md D10
archivos: backend/replays/analytics/aggregates.py (_record, repeated_rivals, _filas_de_stacks), backend/tests/test_duels.py, backend/tests/test_stacks_rivales.py, frontend/src/ultimaVez.js (nuevo), frontend/src/ultimaVez.test.js (nuevo), frontend/src/pages/Duelos.jsx, frontend/e2e/humo.spec.js, docs/metricas.md
turnos: po 20261113T1650Z-c9H2L8Y, arquitecto 20261113T1802Z-c8dAf7p

## PR

## Que gana quien usa la app

En Duelos, las tablas Rivales repetidos y Stacks rivales que se repiten
suman una columna "Última vez" con la fecha de la partida mas reciente
contra esa persona o ese grupo. Se distingue al rival que te sigue tocando
esta semana del que fue de una racha de hace meses, sin abrir su perfil.

## Criterios de aceptacion

- [ ] Cada fila de `repeated_rivals` y de `rival_stacks`
      (`replays/analytics/aggregates.py`) trae `last_played` en ISO 8601:
      el `max(Match.played_at)` de las partidas que ya cuenta la fila.
      Test con un rival en tres partidas de fechas distintas: sale la mas
      reciente.
- [ ] Con filtros globales (`since`/`until`), `last_played` sale de las
      partidas que pasan el filtro, igual que `matches`; test con un
      `until` que deja afuera la ultima partida.
- [ ] `rival_stacks_de_partida` (el aviso del detalle, ficha 92) no cambia
      su record; si suma `last_played`, es el mismo valor que la fila de
      Duelos. Test.
- [ ] En `Duelos.jsx` las dos tablas muestran la columna "Última vez" con
      la fecha corta del resto de la app y se ordenan por ella; vitest o e2e.
- [ ] e2e: en `seed_demo`, Duelos muestra "Última vez" en Rivales
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

## Revision

## QA

## Para el humano

(nada)
