# 78. Filtros en el listado de Partidas

estado: entregado
candado: -
rama: claude/equipo-dev/78-filtros-en-el-listado-de-partidas
tipo: funcionalidad
epica: revision-de-rondas
area: fullstack
prioridad: 2
fuente: ALCANCE.md F16 (del PR #14, cerrado sin merge el 2026-11-05; rama claude/dazzling-einstein-w3qcyq como referencia, no se mergea)
archivos: backend/replays/models.py (filtro_resultado), backend/replays/analytics/aggregates.py (match_queryset), backend/replays/views.py (match_list), frontend/src/api.js (useApi), frontend/src/partidas.js, frontend/src/partidas.test.js, frontend/src/components/Filters.jsx, frontend/src/pages/Matches.jsx, backend/tests/test_filtros_de_partidas.py, frontend/e2e/humo.spec.js
turnos: po 20261105T0230Z-c8Ahepa, arquitecto 20261105T0349Z-cfLc9Nn, dev 20261105T0418Z-cQaYMkM, revisor 20261105T0804Z-cuHheZT, qa 20261105T1205Z-cUisFZX, release 20261105T1205Z-cUisFZX

## PR

Titulo: `[equipo-dev][fullstack] Filtros en el listado de Partidas`

### Que cambia

La pagina Partidas gana la barra de filtros (mapa, periodo, sesion, tipo) y un selector "Resultado" (Victoria, Derrota, Empate, Incompleta). La lista y el subtitulo ("N partidas con estos filtros.") cuentan solo lo filtrado, y cambiar un filtro vuelve a la primera pagina. De paso, `useApi` ya no deja que una respuesta vieja que llega tarde pise la del filtro nuevo (afectaba a toda pagina con filtros).

### Por que esto y no otra cosa

Ficha 78 (ALCANCE.md F16, idea del PR #14 cerrado). Se reusa la barra compartida de `App` (variante conservadora); Lado, Operador y Sitio no se muestran ni se mandan porque son de ronda. El resultado es local a Partidas. Empate e incompleta siguen a `match_result` caso por caso (el PR #14 los mezclaba con `won=None`).

### Como se probo

- verificar.sh: VERDE 3707572e0 (QA) y sobre el commit de entrega; 936 tests backend, 179 vitest, 58 e2e.
- Tests nuevos: `test_filtros_de_partidas.py` (cada resultado, coincidencia con `match_result`, empate con `won=True`, resultado desconocido ignorado, paginacion con filtro, `days`, `until` de dia entero y el dia siguiente afuera, fecha con zona, sesion, tipo y solo ranked, lado/operador/sitio ignorados, mapa + resultado); `partidas.test.js` (9); e2e `Partidas filtra por resultado y por mapa` (incluye una respuesta demorada a proposito para el bug de `useApi`).
- QA: runserver con base vacia y sembrada, curl con bordes (todo 200, conteos exactos), chunk inicial 190.68 -> 190.78 kB, 4 mutaciones (la de `until` sobrevivia: test agregado).
- OMC: diseno plan=— · revisión=— · verificación=—
- OMC: implementacion plan=— · revisión=2 hallazgos (1 arreglado) · verificación=—
- OMC: revision plan=— · revisión=4 hallazgos (1 refutado, 1 arreglado con test del Revisor) · verificación=—
- OMC: QA plan=— · revisión=— · verificación=PASS

### Riesgos y lo que no entra

Sin migracion, sin `recompute`, sin metrica nueva. Afuera: filtros en la URL (A10), partida anterior/siguiente (F17), orden del lado del servidor, filtros de ronda en Partidas.

### Como probarlo en 2 minutos

```
cd backend; python manage.py runserver
```
Abrir Partidas: la barra no tiene Lado ni Operador. Elegir "Derrota": solo derrotas y el subtitulo con el total filtrado. Ir a "Siguientes" y cambiar el mapa: vuelve a la pagina 1. "Limpiar" deja todo como estaba.

### Para el humano

Aviso, no bloquea: con un Lado elegido en otra pagina, Partidas muestra "Limpiar" aunque no se vea ningun filtro puesto (lo borra en todas las paginas). Si molesta, es pasarle a `Filters` solo los filtros de partida.

### Candidatos descubiertos

Ninguno.

## Que gana quien usa la app

Para encontrar "mis derrotas en Bank de esta semana" ya no hay que recorrer el historial entero de a 50: la lista se achica a lo que uno busca y el total dice cuantas son.

## Criterios de aceptacion

- [x] `result=<victoria|derrota|empate|incompleta>` filtra y `total` cuenta las filtradas; valor desconocido se ignora, nunca 500.
- [x] `days`, `since`/`until` y `session` con la semantica de `_filters`; fecha con zona no da 500; `map` y `match_type` como antes.
- [x] La paginacion respeta los filtros.
- [x] `Matches.jsx` con barra y selector de resultado; cambiar un filtro vuelve a la pagina 1; subtitulo con el total filtrado.
- [x] e2e: Resultado en Partidas con la consola limpia (seed_demo no tiene derrotas: la fila con chip de derrota la cubre el backend).

## Diseno (resumen)

`filtro_resultado` junto a `match_result` en `models.py`; `match_queryset` junto a `base_queryset` en `aggregates.py`; `match_list` usa los dos. En el frontend, `partidas.js` (logica pura: claves de partida, params, clave de filtros, `offsetVigente` que vuelve a la pagina 1 sin un `useEffect` extra, subtitulo). `Filters.jsx` gana `showSide`, `hayExtra` y `children` con defaults que dejan igual a las demas paginas. El detalle completo esta en `git log` de esta ficha.

## Implementacion (resumen)

dev 20261105T0418Z-cQaYMkM. Diseno completo. Desvio: arreglo en `useApi` (bandera `vigente` por efecto en vez de un `alive` compartido); el e2e lo caza con una respuesta demorada (falla con el `api.js` de dev, pasa con el arreglo).

## Revision 2026-11-05 sobre e5e4aa5

Revisor 20261105T0804Z-cuHheZT. Veredicto: aprobar. Corregido: test del empate con `won=True` (agregado por el Revisor). LOW sin cambio: "Limpiar" con filtro invisible (aviso en el PR) y el e2e sin fila de derrota.

## QA 2026-11-05 sobre 3707572

QA 20261105T1205Z-cUisFZX. Base: `tests/factories.py` en un script del scratchpad (65 partidas: 56 victorias, 1 derrota, 7 empates incluido un 3-3 con `won=True`, 1 incompleta, 55 en enero para paginar).

- `verificar.sh` -> VERDE 3707572e0 (935 backend, 179 vitest, 58 e2e).
- Base vacia, `SQLITE_PATH=<tmp> python3 manage.py runserver 8781`: `curl /api/matches/?result=derrota`, `?days=foo`, `?offset=-1`, `?limit=-5`, `?session=99` -> 200, total 0.
- Base sembrada: `?result=victoria` 56 / `derrota` 1 / `empate` 7 / `incompleta` 1, cada uno solo con su etiqueta; `?result=ganada`, `?result=`, `?result=VICTORIA` -> 65 (ignorado); `?result=victoria&offset=50&limit=50` -> total 56, 6 filas victoria; `?days=30` 3; `?days=foo`, `?days=99999999999`, `?until=foo` ignorados; `?since=2026-09-08T00:00:00Z` y `%2B02:00` -> 200; `?until=2026-01-01` 24 (dia entero); `?session=-1|abc|999` -> 0 sin 500; `?map=bank&result=victoria` 1; `?side=Attack&operator=Ash&site=X` 65. `/api/matches/1/` y `/api/export/` 200.
- Chunk inicial (`npx vite build`): dev 190.68 kB, rama 190.78 kB.
- Mutaciones: empate sin `won__isnull=False` -> caen 2; `offsetVigente` sin reset -> cae el vitest; ignorar `until` en `match_queryset` -> **sobrevivia**: agregado `test_until_deja_afuera_una_partida_del_dia_siguiente`, que cae con la mutacion y pasa sin ella.
- `omc-verifier`: PASS (criterio 5 PARTIAL por el seed sin derrotas, cubierto en backend).

Veredicto: `aprobado`.

OMC: plan=— · revisión=— · verificación=PASS

## Para el humano

- (po/arquitecto, aviso) Partidas reusa la barra compartida de `App`: los filtros elegidos ahi siguen puestos al volver al Inicio. Si preferis filtros propios de Partidas, es tocar solo `Matches.jsx`.
