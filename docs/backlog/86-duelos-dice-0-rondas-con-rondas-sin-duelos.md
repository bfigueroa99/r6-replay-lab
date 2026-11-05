# 86. Duelos dice "0 rondas con estos filtros" con un filtro que tiene rondas pero ningun duelo

estado: entregado
candado: -
rama: claude/equipo-dev/86-duelos-dice-0-rondas-con-rondas-sin-duelos
tipo: bug
epica: -
area: fullstack
prioridad: 3
fuente: hallazgo MEDIUM del Revisor de la 85 (`Duelos.jsx:43`), reproducido por la QA 20261105T1358Z-cxcyM5F en la app real
archivos: backend/replays/views.py, backend/tests/test_duels.py, frontend/src/tipoPartida.js, frontend/src/tipoPartida.test.js, frontend/src/components/ui.jsx, frontend/src/pages/Duelos.jsx, frontend/e2e/humo.spec.js
turnos: qa 20261105T1358Z-cxcyM5F, arquitecto 20261105T1429Z-c7UZ3T6, dev 20261105T1429Z-chSa5eY, revisor 20261105T1455Z-caYiimg, qa 20261105T1521Z-cEexMKJ, release 20261105T1521Z-cEexMKJ

## PR

Titulo: `[equipo-dev][frontend] Duelos dice "0 duelos" y no "0 rondas" cuando el filtro tiene rondas sin duelos`

## Que cambia

Duelos decide si esta vacia por las rondas que deja el filtro, no por los
duelos. Con un filtro que deja rondas en las que no mataste ni moriste (un
mapa, un lado), la pagina ya no dice "0 rondas con estos filtros" (falso: el
Resumen muestra esas rondas) sino "0 duelos con estos filtros", con la barra
y Limpiar a mano. Con 0 rondas sigue diciendo "0 rondas"; base vacia, el
EmptyState de siempre.

## Por que esto y no otra cosa

Ficha 86, hallazgo MEDIUM del Revisor de la 85 (`Duelos.jsx:43`),
reproducido por la QA en la app real. `/api/duels/` suma `rounds` al nivel
de `totals` (fuera de `duel_totals`, que comparte el coach); se descarto
deducir las rondas en el frontend, que no las tiene, y tocar como se cuentan
los duelos (fuera de alcance).

## Como se probo

- `check.sh` (con `verificar.sh`): VERDE 27c46daef, 955 tests backend, 197 vitest, 62 e2e.
- Tests nuevos: `test_la_api_de_duelos_cuenta_las_rondas_aunque_no_haya_duelos`
  (backend: `?map=bank` da `rounds=1`, `duels=0`); vitest `vistaDuelos (ficha
  86)` (5 casos: con duelos, sin duelos, 0 rondas con y sin filtros, cargando)
  y `textosSinDuelos (ficha 86)` (2: con y sin filtros); e2e `Duelos con
  rondas pero sin duelos dice 0 duelos y no 0 rondas`. El e2e de la 85 (0
  rondas) sin tocar, verde.
- Manual (QA): base de `factories.py`, Chromium: Bank -> "0 duelos con estos
  filtros" con barra y Limpiar; Bank + Defensa -> "0 rondas con estos
  filtros"; base vacia -> EmptyState. `rounds` de Duelos igual a
  `overall.rounds` del Resumen en 8 combinaciones. Mutacion de 3 puntos:
  cada una tumba un test.
- OMC diseno: plan=— (ficha chica, una forma obvia) · revisión=— · verificación=—
- OMC implementacion: plan=— · revisión=3 hallazgos (1 arreglado) · verificación=—
- OMC revision: plan=— · revisión=1 hallazgo LOW (0 arreglados; el Revisor no arregla) · verificación=—
- OMC QA: plan=— · revisión=— · verificación=PASS

## Riesgos y lo que no entra

Sin migracion ni `recompute`. Chunk inicial +0.27 %. Fuera: mostrar `faced`
y `rivals` en la vista sin duelos (ya no se mostraban), y el LOW del
Revisor: mientras carga un filtro nuevo, la vista puede decir un instante
"Hay rondas con estos filtros" antes de pasar a "0 rondas".

## Como probarlo en 2 minutos

```bash
cd backend; python manage.py test tests.test_duels
cd ../frontend; npx vitest run src/tipoPartida.test.js
npm run e2e -- -g "Duelos con rondas pero sin duelos|filtro sin rondas deja la barra"
```

En la app, Duelos con un mapa donde no mataste ni moriste: "0 duelos con
estos filtros", barra visible; Limpiar vuelve a los numeros.

## Para el humano

Nada.

## Candidatos descubiertos

Ninguno.

## Diseno (resumen)

Arquitecto 20261105T1429Z-c7UZ3T6 sobre dev 85009f6. `views.py` (`duels`)
agrega `"rounds": agg.base_queryset(**filters).count()`; `tipoPartida.js`
suma `vistaDuelos({ rondas, duelos, filtros, cargando })`; `ui.jsx`
(`SinRondasFiltradas`) acepta `subtitulo` y `nota` con el texto de hoy por
defecto; `Duelos.jsx` usa `vistaDuelos` y pinta la vista `sin-duelos`. Sin
fila en `metricas.md` (no hay numero nuevo). El detalle, en `git log`.

## Implementacion (resumen)

Dev 20261105T1429Z-chSa5eY: el diseno entero, mas `textosSinDuelos(filtros)`
para que sin filtros la nota no mencione Limpiar (que no se dibuja). El e2e
espera la respuesta `side=Attack` antes de afirmar. VERDE af11d395c.

## Revision 2026-11-05 sobre 61625a8

Revisor 20261105T1455Z-caYiimg: aprobar -> `revisado`. Un LOW sin arreglar
(texto transitorio mientras carga, ver Riesgos). VERDE d75692b61.

## QA 2026-11-05 sobre 27c46da

QA 20261105T1521Z-cEexMKJ: los 3 criterios cubiertos en la app real (bases
factories, vacia y seed_demo), bordes de `/api/duels/` en 200 (`until=foo`,
`page=-1`, `map=`, `days=-1`, mapa inexistente), mutacion de 3 puntos, chunk
+0.27 %. VERDE 27c46daef. `omc-verifier`: PASS. -> `aprobado`.

OMC: plan=— · revisión=— · verificación=PASS

## Para el humano

- 2026-11-05 (revisor 20261105T1455Z-caYiimg): LOW sin arreglar, no bloquea: mientras carga un filtro nuevo, la vista `sin-duelos` puede decir un instante "Hay rondas con estos filtros" antes de pasar a "0 rondas".
