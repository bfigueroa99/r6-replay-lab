# 102. Tu pool de operadores por lado

estado: entregado
candado: -
rama: claude/equipo-dev/102-pool-de-operadores-por-lado
tipo: funcionalidad
epica: operadores
area: fullstack
prioridad: 3
fuente: ALCANCE.md O7
archivos: backend/replays/analytics/aggregates.py (operator_pool, POOL_*), backend/replays/views.py (operators_pool), backend/replays/urls.py, backend/tests/test_pool_operadores.py, frontend/src/poolOperadores.js, frontend/src/poolOperadores.test.js, frontend/src/pages/Operators.jsx, frontend/e2e/humo.spec.js, docs/metricas.md
turnos: po 20261106T0530Z-ciXX3AM, arquitecto 20261112T1128Z-cKKCvKD, dev 20261112T1204Z-chGLrtC, revisor 20261112T1603Z-cor3JBP, qa 20261112T2004Z-cbaTGDt, release 20261112T2004Z-cbaTGDt

## PR

Titulo: `[equipo-dev][frontend] Tu pool de operadores por lado`

### Que cambia

En Operadores, un panel "Tu pool" dice por lado cuantos operadores distintos
jugaste en tus ultimas 20 partidas y en todo lo filtrado, cuales dejaste
(jugados alguna vez y no en los 30 dias anteriores a tu partida mas nueva) y
cuales del catalogo nunca jugaste. Endpoint nuevo de lectura
`GET /api/operators/pool/`.

### Por que esto y no otra cosa

Ficha 102 (ALCANCE.md O7, epica operadores). La tabla por operador ordena
por rondas y no dice si dependes de dos operadores por lado. Endpoint propio
en vez de una clave en `/api/operators/`: un error del panel no tumba la
pagina (mismo patron que Operador por sitio). Los filtros de lado, operador y
sitio se ignoran: con ellos todo lo demas caeria en "Nunca jugados".

### Como se probo

- `check.sh` (con `verificar.sh`): VERDE 7bde1db, 1122 tests backend, 303 vitest, 85 e2e.
- `tests/test_pool_operadores.py` (13): ventana y total, 40 dias en stale,
  referencia = tu ultima partida y no hoy, never, Unknown y vacio fuera,
  operador/lado/sitio ignorados, mapa y tipo aplican, orden y desempate de
  stale, sin partidas. Vitest `poolOperadores.test.js` (8). e2e
  `Operadores muestra tu pool por lado`.
- QA: runserver con base vacia y sembrada con bordes, `curl` con filtros
  basura (todos 200), UI en Chromium con consola limpia, chunk inicial sin
  cambio, 5 mutaciones cazadas por los tests.
- OMC diseno: plan=— · revisión=— · verificación=—
- OMC implementacion: plan=— · revisión=4 hallazgos (4 arreglados; 0 CRITICAL/HIGH) · verificación=—
- OMC revision: plan=— · revisión=2 hallazgos LOW (0 arreglados; 1 test agregado) · verificación=—
- OMC QA: plan=— · revisión=— · verificación=PASS

### Riesgos y lo que no entra

Sin migracion, `recompute`, parser ni Electron. Una consulta agrupada mas
un iterador cortado en 20 partidas. Fuera: curva de aprendizaje (E1),
presencia (O5), recomendar que practicar, ventanas configurables.

### Como probarlo en 2 minutos

```
cd backend; python manage.py seed_demo; python manage.py runserver
```
Abrir `http://127.0.0.1:8000/operadores`: panel "Tu pool" con Ataque y
Defensa, "3 operadores distintos en tus últimas 20 partidas", "Sin jugar...:
ninguno", Sledge en Nunca jugados de Ataque. `/operadores?side=Defense`:
solo Defensa. `/api/operators/pool/?operator=Ash` igual que sin el filtro.

### Para el humano

Nada.

### Candidatos descubiertos

Ninguno.

## Que gana quien usa la app

Responde si dependes de dos operadores por lado y que practicar para cuando
te los banean o te los quitan.

## Criterios de aceptacion

- [x] API por lado con `distinct_recent`, `distinct_all`, `never` y `stale`; test de 40 dias.
- [x] Mapa y tipo aplican; lado decide el bloque; operador ignorado (test).
- [x] `Unknown(...)` y `operator=""` fuera del conteo y de `never`.
- [x] Panel con los dos lados; vacio sin error; e2e con consola limpia.
- [x] Fila "Pool de operadores" en `docs/metricas.md`.

## Diseno, Implementacion y Revision (condensado; detalle en git log)

Arquitecto: endpoint propio, `operator_pool(catalogo, **filters)` en
`aggregates.py`, referencia = tu partida mas nueva filtrada (no hoy).
Dev: desvios documentados: `site` tambien se ignora; `stale` desempata por
nombre; "Sin jugar" muestra rondas. Revisor (sobre 1ff5760): aprobar; agrego
`test_el_filtro_de_tipo_de_partida_aplica`; dos LOW sin arreglar en el hint
(no dice que el filtro de operador tampoco aplica, ni que mapa y tipo si).

## QA 2026-11-12 sobre 7bde1db

(qa 20261112T2004Z-cbaTGDt) verificar.sh VERDE 7bde1db (1122/303/85). Base sembrada
con bordes (Montagne 40 dias antes, partida solo Unknown y "", Valkyrie en
otro mapa): 200, 31 de 32 partidas, stale Montagne y Valkyrie, Unknown fuera
de `never`. `?operator=Ash&side=Attack`, `?site=foo`, `?until=foo`,
`?page=-1`, `?days=99999999999`, `?map=` iguales a sin filtros;
`?map=noexiste`, `?since=2099-01-01`, `?session=abc` -> 200 vacio; POST 403.
Chromium: panel ok, `?side=Defense` solo Defensa, base vacia con EmptyState,
consola limpia. Chunk inicial 195.52 kB igual que dev. Mutaciones (5) cazadas.
Observacion: con un mapa donde jugaste un solo lado, el otro bloque sale en 0
con todo el catalogo en Nunca jugados; coherente, pulible.

Skills: no aplica.
OMC: plan=— · revisión=— · verificación=PASS

## Para el humano

(nada)
