# 131. Rondas que el equipo gano sin ti

estado: entregado
candado: -
rama: claude/equipo-dev/131-rondas-que-el-equipo-gano-sin-ti
tipo: funcionalidad
epica: escuadra
area: fullstack
prioridad: 3
fuente: ALCANCE.md C13
archivos: backend/replays/analytics/aggregates.py, backend/replays/views.py, backend/tests/test_ganadas_sin_ti.py, frontend/src/ganadasSinTi.js, frontend/src/ganadasSinTi.test.js, frontend/src/pages/Teammates.jsx, frontend/e2e/humo.spec.js, docs/metricas.md
turnos: po 20261113T1858Z-cxQ3TuB, arquitecto 20261113T2157Z-cG2vDSe, dev 20261113T2345Z-c6MAT6w, revisor 20261114T0012Z-crDhgd7, qa 20261114T0012Z-ccgaH14, release 20261114T0012Z-ccgaH14

## PR

Titulo: [equipo-dev][fullstack] Rondas que el equipo ganó sin ti

### Que cambia

Compañeros suma el panel "Rondas que tu equipo ganó sin ti", debajo de
"Primero en caer": de las rondas en que caíste, cuántas igual ganó tu equipo,
por lado y en total, y qué compañero habitual seguía vivo al final de esas
rondas ("Quién la sostiene", con su `n` y `*` debajo de 5 rondas).

### Por que esto y no otra cosa

Ficha 131 (ALCANCE.md C13, épica escuadra). Hoy solo se ve tu winrate cuando
mueres, no quién lo sostiene. Molde de `first_teammate_death` (tabla por lado)
y de `teammate_clutches` (habituales); sin ruta nueva: clave en `/api/teammates/`.

### Como se probo

- `check.sh` (con `verificar.sh`): VERDE 5532bae (fusionada con dev), 1348 tests backend, 443 vitest, 119 e2e.
- Tests nuevos: `tests/test_ganadas_sin_ti.py` (13: por lado, sobrevivir no
  cuenta, sin ganador fuera, total, compañero vivo, no habitual, rival, habitual
  de rival, ronda perdida, filtros de lado y mapa, muestra chica, vista);
  `ganadasSinTi.test.js` (4); e2e `Compañeros muestra las rondas que el equipo ganó sin ti`.
- QA: base vacía y sembrada con bordes en 200; 4 valores recalculados con SQL
  crudo contra la API; a11y en Chromium (teclado, contraste 5,71:1, consola
  limpia); chunk inicial sin crecer; 3 mutaciones que hacen caer su test.
- OMC: plan=— (diseno); revisión=3 hallazgos (3 arreglados) (implementacion);
  revisión=2 LOW (0 arreglados, confirmados) (revision); verificación=PASS (QA).
- Skills del repo: statistical-analysis, testing-strategy (diseno);
  testing-strategy, statistical-analysis, ux-copy (implementacion);
  accessibility-review, validate-data, design-critique (QA).

### Riesgos y lo que no entra

Sin migracion, sin `recompute`, sin parser. "Seguía vivo" no es "hizo las
bajas". Fuera: rondas perdidas sobreviviendo (ficha 139), quién hizo las bajas
después de que caíste, señales del Coach. La subconsulta de habituales queda
copiada por tercera vez: extraer `_habituales_qs()` cuando entre la 79.

### Como probarlo en 2 minutos

`cd backend; python manage.py seed_demo; python manage.py runserver`, abrir
`/companeros`: panel "Rondas que tu equipo ganó sin ti" con Total 173, 98, 57 %
y Seba 98 juntos, 38 vivo. Con lado Defensa: fila Defensa y Total, sin compañeros.

### Para el humano

Nada.

## Que gana quien usa la app

En Compañeros, de las rondas en que caiste, cuantas igual gano tu equipo, por
lado, y que compañero habitual seguia vivo al final de esas rondas.

## Criterios de aceptacion

- [x] `won_without_me`: tus filas `died=True` con ganador, por lado y total.
- [x] Por compañero habitual: en cuantas ganadas sin ti seguia vivo (mismo `team_index`).
- [x] Filtros globales sobre tu fila; test con filtro de lado.
- [x] Clave en `/api/teammates/`, panel en `Teammates.jsx`, nota sin rondas, e2e.
- [x] Fila en `docs/metricas.md` y en `## Muestra minima`.

## Diseno

`aggregates.won_without_me` despues de `teammate_clutches`, `GANADA_SIN_TI_MIN = 5`,
lados con la regla de `by_overtime_side`, habituales copiados de
`teammate_clutches`, `mia_ganada` correlacionada por `round_id` y `team_index`.
`ganadasSinTi.js` y panel en `Teammates.jsx`. Detalle en `git log`.

## Implementacion

Diseno completo. Desvios menores: compañeros vivos con `died=False` (la factory
deriva `survived`), test extra de habitual que juega de rival, filtro de mapa
probado. TDD con rojo visto.

## Revision 2026-11-14 sobre 92c030c

Veredicto: aprobar. 2 LOW sin arreglar: la fila Total del e2e se afirma sin
orden; subconsulta de habituales copiada por tercera vez. Detalle en `git log`.

## QA 2026-11-14 sobre 5532bae

Veredicto: aprobado. Evidencia completa en el commit "Prueba: 131 ..."; resumen
en "Como se probo".

## Para el humano

(nada)
