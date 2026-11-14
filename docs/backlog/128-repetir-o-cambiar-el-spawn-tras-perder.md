# 128. Repetir o cambiar el spawn tras perder

estado: entregado
candado: -
rama: claude/equipo-dev/128-repetir-o-cambiar-el-spawn-tras-perder
tipo: funcionalidad
epica: posicionamiento
area: fullstack
prioridad: 3
fuente: ALCANCE.md S3
archivos: backend/replays/analytics/aggregates.py, backend/replays/views.py, backend/replays/urls.py, backend/tests/test_repetir_spawn.py, frontend/src/repetirSpawn.js, frontend/src/repetirSpawn.test.js, frontend/src/pages/Coach.jsx, frontend/e2e/humo.spec.js, docs/metricas.md
turnos: po 20261113T1858Z-cxdASk3, arquitecto 20261113T2157Z-cG2vDSe, dev 20261113T2345Z-c5J2BqJ, revisor 20261113T2345Z-c6MAT6w, qa 20261114T0004Z-cagB2Hb, release 20261114T0004Z-cagB2Hb

## PR

Titulo: [equipo-dev][fullstack] Repetir o cambiar el spawn tras perder

### Que cambia

El Coach suma el panel "Repetir o cambiar el spawn", debajo de "Repetir el
sitio tras perderlo": en ataque, tras perder (y tras ganar, como base), cuantas
veces vuelves a salir del mismo spawn en tu siguiente ronda de ataque de la
partida y cuantas cambias, con el winrate de esa siguiente ronda.

### Por que esto y no otra cosa

Ficha 128 (ALCANCE.md S3), gemela de spawn de la 113 (operador). Molde de
`site_after_loss` (107); sin desglose por par de spawns ni defensa (fuera de alcance).

### Como se probo

- `check.sh` (con `verificar.sh`): VERDE c0da754, 1335 tests backend, 435 vitest, 116 e2e.
- Tests nuevos: `tests/test_repetir_spawn.py` (14: caso del criterio, tras ganar,
  defensa entre medio, hueco, sin spawn, sin lado, partidas distintas, primera y
  segunda sin ganador, filtros de operador, sitio, mapa y lado, base vacia);
  `repetirSpawn.test.js` (4); e2e `el Coach muestra si repites el spawn tras perder`.
- QA: runserver con base vacia y sembrada, 5 pares recalculados a mano contra la
  API, bordes de parametros en 200, a11y en Chromium (contraste 5,71:1, teclado),
  3 mutaciones que hacen caer su test.
- OMC: plan=— · revisión=4 hallazgos (4 arreglados) · verificación=— (implementacion);
  revisión=2 LOW + 1 LOW del lider (revision); verificación=PASS (QA).
- Skills del repo: statistical-analysis, testing-strategy (diseno);
  test-driven-development, ux-copy (implementacion); accessibility-review, validate-data (QA).

### Riesgos y lo que no entra

Sin migracion, sin `recompute`, sin parser. Fuera: a que spawn cambias,
defensa, recomendar un spawn. `seed_demo` no tiene rondas perdidas en ataque:
el e2e ve "Tras perder" en 0 (lo cubren Django y vitest).

### Como probarlo en 2 minutos

`cd backend; python manage.py seed_demo; python manage.py runserver`, abrir
`/coach`: panel "Repetir o cambiar el spawn" con 87 pares, dos filas. Con el
filtro de lado en Defensa, los mismos numeros.

### Para el humano

Nada.

### Candidatos descubiertos

Ninguno.

## Que gana quien usa la app

En ataque, despues de perder una ronda, cuantas veces vuelves a salir del
mismo spawn y cuantas cambias, con el winrate de la ronda siguiente en cada
caso (y lo mismo tras ganar, como base).

## Criterios de aceptacion

- [x] Agregado de pares de rondas de ataque con `after_loss`/`after_win` x `repeat`/`switch`.
- [x] Par sin spawn, con hueco o sin lado no entra; segunda sin ganador fuera del winrate.
- [x] Filtros globales; `site` y `operator` eligen la primera ronda.
- [x] Panel en el Coach con aviso de muestra y texto sin pares; e2e de humo.
- [x] Fila en `docs/metricas.md`.

## Fuera de alcance

A que spawn cambias; defensa; recomendar un spawn.

## Diseno

`aggregates.spawn_after_result` con el molde de `site_after_loss` y la regla
de par de la 113 (las de defensa entre medio no cortan). Ruta
`positioning/spawn-after-result/`, `repetirSpawn.js` y `PanelRepetirSpawn`.
Muestra minima 8 (la de la 107). Cuando entre la 79, la ruta va como comparada
en `test_excluir_partida.py`.

## Implementacion

Diseno completo sin desvios. Revision ciega: 4 LOW, los 4 atendidos. TDD con
rojo visto en Django y vitest.

## Revision 2026-11-14T00:00Z sobre dfde6d7

Veredicto: aprobar. 3 LOW sin arreglar (el Revisor no arregla): ", la de la 107"
en la fila de `metricas.md`; el hint no dice que el filtro de lado no aplica;
el seed no ejercita "Cambia" en el e2e. Detalle en `git log`.

## QA 2026-11-14 sobre c0da754

Veredicto: aprobado. Evidencia completa (comandos y salidas) en el commit
316b413 ("Prueba: 128 ..."); resumen en "Como se probo".

## Para el humano

(nada)
