# 110. Tu forma contra tu historial

estado: entregado
candado: -
rama: claude/equipo-dev/110-tu-forma-contra-tu-historial
tipo: funcionalidad
epica: progreso
area: fullstack
prioridad: 3
fuente: ALCANCE.md E16
archivos: backend/replays/analytics/aggregates.py (compare_periods against, _periodo_por_partidas), backend/replays/views.py (compare), backend/tests/test_compare.py, frontend/src/components/Delta.jsx (nuevo, sale de Trends.jsx), frontend/src/pages/Trends.jsx (import), frontend/src/formaHistorial.js (nuevo), frontend/src/formaHistorial.test.js (nuevo), frontend/src/pages/Dashboard.jsx, frontend/e2e/humo.spec.js, docs/metricas.md
turnos: po 20261112T1128Z-cKKCvKD, arquitecto 20261113T0003Z-cVnayJ8, dev 20261113T0804Z-cJw5MQs, revisor 20261113T1203Z-cWfR3tT, qa 20261113T1603Z-cHj1H4k, release 20261113T1603Z-cHj1H4k

## PR

Titulo: `[equipo-dev][frontend] Tu forma contra tu historial en el Inicio`

### Que cambia

El Inicio suma el panel **Tu forma contra tu historial**: tus ultimas 10
partidas contra todas las anteriores (no las 10 anteriores, como Progreso),
en Rondas ganadas, Rating, KST y Muertes sin trade, con el cambio, la banda
de ruido y el veredicto. Dice si estas en racha o en bajon por algo mas que
el resultado. `GET /api/compare/` acepta `against=rest`.

### Por que esto y no otra cosa

Ficha 110 (ALCANCE E16). No hay bloque `form` en `/api/overview/`: se
extiende `compare_periods`, que ya tenia delta y banda, y el panel hace su
propia request (si falla, el Inicio sigue en pie).

### Como se probo

- `check.sh` (con `verificar.sh`): VERDE 196edd0, 1173 tests backend, 340 vitest, 96 e2e.
- Tests nuevos: `ContraElRestoTests` (8: resto completo, recientes = `recent_form`,
  sale del ruido, sin resto con 10 o menos, `?map=` a los dos lados, por dias,
  regresion sin `against`, vista con `against=rest`/`foo`); vitest
  `formaHistorial.test.js` (6); e2e `el Inicio compara tu forma con tu historial`
  (cabeceras y valores de la API, consola limpia).
- QA: curl con bordes y valores recalculados a mano, Chromium en 4 escenarios, mutacion (5 de 5 caen). Detalle en `## QA`.
- OMC: diseno plan=— · revisión=— · verificación=—
- OMC: implementacion plan=— · revisión=5 hallazgos (5 arreglados; 0 CRITICAL/HIGH) · verificación=—
- OMC: revision plan=— · revisión=8 hallazgos (1 arreglado; 0 CRITICAL/HIGH) · verificación=—
- OMC: QA plan=— · revisión=— · verificación=PASS
- Skills del repo: statistical-analysis, testing-strategy (diseno); accessibility-review (0 Critical/Major), validate-data (QA).

### Riesgos y lo que no entra

Sin migracion, sin `recompute`, sin POST. El resto usa `exclude` y no `IN`
(limite de variables de SQLite). Fuera: ventana configurable, grafico, señal
del Coach. Fecha y sesion de la barra no aplican al panel (como Progreso).

### Como probarlo en 2 minutos

```
cd backend; python manage.py seed_demo; python manage.py runserver
```
En `/`: panel "Tu forma contra tu historial" con "El resto (19 partidas)"
contra "Últimas 10 partidas". `/?map=bank` cambia los dos lados.
Tendencias -> Progreso sigue diciendo "Las 10 anteriores".

### Para el humano

Aviso, no frena: si preferis que "el resto" respete Desde/Hasta, es una linea.

### Candidatos descubiertos

Ninguno (idea de accesibilidad en `ALCANCE.md`: ayuda de columnas solo en `title`).

## Que gana quien usa la app

En el Inicio, un panel compara tus ultimas 10 partidas con el resto de tu
historial (rating, winrate de rondas, KST, muertes sin trade) con la
diferencia y si sale del ruido.

## Criterios de aceptacion

- [x] `/api/compare/?against=rest`: `current` = las de `recent_form()`, `previous` = el resto, con `delta`, `noise` y `verdict` (forma del diseno).
- [x] Con 10 partidas o menos no hay resto y el panel muestra una nota, no ceros.
- [x] Los filtros de la barra aplican a los dos lados (`?map=`).
- [x] El panel se ve en el Inicio; el e2e de humo lo afirma con numeros y consola limpia.
- [x] Fila "Forma contra tu historial" en `docs/metricas.md`.

## Diseno

(arquitecto 20261113T0003Z-cVnayJ8) `compare_periods(..., against="rest")` y
`_periodo_por_partidas(..., resto=True)`; la vista acepta `against=rest`
(otro valor = `previous`). `Delta` sale a `components/Delta.jsx`;
`formaHistorial.js` con `filasDeForma` y `estadoDeForma`; `PanelForma` en
`Dashboard.jsx`. Detalle en `git log`.
OMC: plan=— · revisión=— · verificación=—

## Implementacion

(dev 20261113T0804Z-cJw5MQs) Diseno completo. Desvios: etiquetas con tildes;
resto con `exclude`; hint y `metricas.md` aclaran que fecha y sesion no
aplican; test extra por dias.
OMC: plan=— · revisión=5 hallazgos (5 arreglados; 0 CRITICAL/HIGH) · verificación=—

## Revision 2026-11-13 sobre 5c49845

(revisor 20261113T1203Z-cWfR3tT) VERDE 5c49845. Corregido: el e2e ahora afirma
valores (previo, actual, ruido) y no solo cabeceras; con columnas cruzadas cae.
LOW sin frenar: `El resto (1 partidas)`, `by_map`/`by_operator` calculados de mas.
Veredicto: `revisado`.
OMC: plan=— · revisión=8 hallazgos (1 arreglado; 0 CRITICAL/HIGH) · verificación=—

## QA 2026-11-13 sobre 196edd0

(qa 20261113T1603Z-cHj1H4k) VERDE 196edd0 (1173/340/96). Bases sinteticas con
`factories.py` (25 partidas, 6 partidas, vacia). Recalculado a mano: winrate
30/90 = 33.3 contra 50/60 = 83.3, banda 6.9; con `map=bank` 35/60 = 58.3
contra 6/18 = 33.3. Bordes (`n=-1`, `n=foo`, `until=foo`, mapa sin rondas,
base vacia, `against=foo|REST`): 200 y modo de hoy intacto. Chromium: tabla,
muestra chica, sin resto (nota, sin tabla) y vacio (sin panel), consola limpia.
Chunk inicial +1.2 %. Mutacion: 5 de 5 caen. Detalle en `git log`.
Skills del repo: accessibility-review (0 Critical/Major; contraste 5.8:1 y 5.71:1; Minor previo: ayuda solo en `title`), validate-data (sin promedio de promedios ni division por cero; Low: cabeceras en partidas y no rondas).
OMC: plan=— · revisión=— · verificación=PASS (omc-verifier 5/5 VERIFIED)

## Para el humano

- Aviso, no frena (arquitecto): las fechas y la sesion de la barra no aplican a
  esta comparacion, igual que en Progreso. Si preferis que "el resto" respete
  "Desde/Hasta", es un cambio de una linea.
