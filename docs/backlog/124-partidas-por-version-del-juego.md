# 124. Partidas por version del juego en Datos

estado: entregado
candado: -
rama: claude/equipo-dev/124-partidas-por-version-del-juego
tipo: funcionalidad
epica: datos
area: backend
prioridad: 3
fuente: ALCANCE.md G8
archivos: backend/replays/unknowns.py (partidas_por_version), backend/replays/views.py (import_status), backend/tests/test_versiones_del_juego.py (nuevo), frontend/src/pages/Datos.jsx (panel Importación), frontend/e2e/humo.spec.js, docs/metricas.md
turnos: po 20261113T1650Z-c9H2L8Y, arquitecto 20261113T1830Z-cTivbSq, dev 20261113T1926Z-cNCxUZs, revisor 20261113T1926Z-cq9nfTP, qa 20261113T2003Z-c3vr7mZ, release 20261113T2003Z-c3vr7mZ

## PR

Titulo: `[equipo-dev][backend] Datos: partidas por versión del juego`

### Que cambia

En Datos, panel Importación, una tabla nueva "Partidas por versión del juego": cuántas partidas importadas hay de cada versión, con la fecha de la primera y la última, la más nueva arriba y las partidas sin versión en una fila "Sin versión" al final. `/api/import/status/` suma la clave `versions`.

### Por que esto y no otra cosa

Ficha 124 (ALCANCE G8). `Match.game_version` y `code_version` ya se guardan al importar: sin migracion, sin `recompute`, sin POST. Descartado: nombre de temporada derivado de la version y filtro global por version (A3), reimportar desde la tabla (G1).

### Como se probo

- `check.sh` (con `verificar.sh`): VERDE 2cdd4b862, 1284 tests backend, 405 vitest, 111 e2e (rama fusionada con `origin/dev@f6cd92d`).
- Tests nuevos (`backend/tests/test_versiones_del_juego.py`, 5): agrupa con primera y ultima, sin version al final, a igual codigo la usada mas tarde primero, el `ordering` del modelo no parte las filas, `/api/import/status/` con base vacia y con una partida. e2e: la tabla igual a `versions` de la API con `seed_demo`, y el orden de la API (Y10S4 antes que Y9S4) con respuesta inyectada.
- Verificacion manual (QA): base vacia y sembrada desde `factories.py`, valores recalculados a mano (Y10S3: 2 partidas, 09-01 a 09-05), parametros borde, Playwright en `/datos` (orden, teclado, contraste 14.17:1, consola limpia), 4 mutaciones (3 caen en su test; el `order_by()` vacio es defensivo en Django 5.2).
- OMC: plan=— · revisión=— · verificación=—
- OMC: plan=— · revisión=2 hallazgos (2 arreglados) · verificación=—
- OMC: plan=— · revisión=0 hallazgos · verificación=—
- OMC: plan=— · revisión=— · verificación=PASS
- Skills del repo: testing-strategy (diseno e implementacion), ux-copy (implementacion), accessibility-review (0 Critical, 0 Major), validate-data (Y10S3 recalculado).

### Riesgos y lo que no entra

Clave aditiva en `/api/import/status/` y un GROUP BY sobre `Match` en esa vista: despreciable al lado del recorrido de carpetas que ya hace. Incluye el arreglo de un e2e intermitente de la 126 (`waitForLoadState('networkidle')` antes del segundo `goto` en Operadores). Las fechas de la tabla van `AAAA-MM-DD` y el resto de Datos `DD-MM` (nota del Revisor). Ordenar a mano por Versión ordena como texto (Y9S4 antes que Y10S4).

### Como probarlo en 2 minutos

```powershell
cd backend; python manage.py seed_demo; python manage.py runserver
```
Abrir `http://127.0.0.1:8000/datos`, panel Importación, al final: "Partidas por versión del juego" con una fila "Sin versión" y 29 partidas (la semilla no trae version). Con la base real: una fila por version importada, la mas nueva arriba. `curl -s localhost:8000/api/import/status/` trae `versions`.

### Para el humano

Nada que decidir.

## Que gana quien usa la app

En Datos, una tabla con cuantas partidas importadas hay de cada version del juego, con la fecha de la primera y de la ultima: que temporadas cubre el historial y si una version nueva entro sin nombre.

## Criterios de aceptacion

- [x] Agregado por `game_version` (orden por `code_version`) con `Count`, `Min`/`Max(played_at)`, la mas nueva arriba. Test con tres partidas en dos versiones.
- [x] `game_version` vacio en una fila "Sin versión", al final. Test.
- [x] En `/api/import/status/`, sin POST, columna ni migracion. Base vacia: lista vacia, 200.
- [x] `Datos.jsx` muestra la tabla con estado vacio; e2e en `seed_demo` con una fila y consola limpia.

## Diseno

(arquitecto 20261113T1830Z-cTivbSq) `partidas_por_version()` en `unknowns.py` (inventario de `Match` sin filtros de la barra, junto a `unknown_maps`; cuenta tambien las partidas que la 79 excluya), clave `versions` en `views.import_status`, tabla en el panel Importación de `Datos.jsx`, fila en `metricas.md` (`## Datos`).

## Implementacion

(dev 20261113T1926Z-cNCxUZs) Como el diseno. Desvio: `DataTable` siempre ordena (por texto, "Y9S4" antes que "Y10S4"), asi que cada fila lleva `posicion` y la tabla arranca con `initialSort` por ella; lo fija el segundo e2e. P4: e2e intermitente de la 126 arreglado. VERDE e4d26b5cb.

## Revision 2026-11-13 sobre 0bd7e6f

(revisor 20261113T1926Z-cq9nfTP) Aprobar, 0 hallazgos. Nota menor: formato de fecha distinto al resto de Datos.

## QA 2026-11-13 sobre 2cdd4b8

(qa 20261113T2003Z-c3vr7mZ) Rama con `origin/dev@f6cd92d` fusionado (entro la 123), merge limpio.

- `verificar.sh`: VERDE 2cdd4b862 en 196 s (1284 tests backend, 405 vitest, 111 e2e).
- Base vacia (`SQLITE_PATH` y `R6_ENV_FILE` temporales, `migrate`, `runserver 8124`): `curl -s localhost:8124/api/import/status/` -> 200, `versions == []`.
- Base sembrada con `make_match` (script en el scratchpad): Y10S3 code 20 x2 (2026-09-01 y 09-05), Y10S4 code 30 x1, `""` code 99 x1, Y9S4 code 10 x1. La API: Y10S4 1, Y10S3 2 (first 2026-09-01T20:00, last 2026-09-05T21:00), Y9S4 1, `""` 1 al final pese al code 99. Recalculado a mano: coincide.
- Borde: `?until=foo`, `?page=-1`, `?side=`, `?x=%00` -> 200; vecino `/api/unknown/` 200; `POST /api/import/status/` -> 403; `/datos` -> 200.
- Playwright en `/datos` (accessibility-review): heading presente; filas en el orden de la API (Y10S4, Y10S3, Y9S4, Sin versión), no por texto; encabezados botones alcanzables con Tab y Enter ordena; contraste de celda 14.17:1; consola sin errores ni warnings. 0 Critical, 0 Major en lo nuevo. Ya estaba: `DataTable` no pone `aria-sort` en los encabezados (WCAG 4.1.2), va como idea.
- Chunk inicial `index-*.js` 200116 bytes; Datos es chunk lazy propio: sin crecimiento del inicial atribuible.
- validate-data sobre la fila de `metricas.md`: conteo y fechas min/max, sin division ni promedio; sin redondeo.
- Mutacion (`tests.test_versiones_del_juego`): quitar el `sort` de "sin version al final" -> FAILED (1); `reverse=False` -> FAILED (2); quitar `versions` de la vista -> FAILED (errors=1); quitar el `order_by()` vacio -> OK. Sobrevive porque en Django 5.2.19 `values().annotate()` ya no mete `Meta.ordering` en el GROUP BY (`str(q.query)`: `GROUP BY 1`): el `order_by()` es defensivo y su comentario sobreestima. LOW, no es criterio.

Veredicto: aprobado.

Skills del repo: accessibility-review (0 Critical, 0 Major; aria-sort preexistente), validate-data (Y10S3 2 partidas 09-01 a 09-05, recalculado).
OMC: plan=— · revisión=— · verificación=PASS

## Para el humano

(nada)
