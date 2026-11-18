# 137. Cuantas de tus muertes son headshot

estado: entregado
candado: -
rama: claude/equipo-dev/137-cuantas-de-tus-muertes-son-headshot
tipo: funcionalidad
epica: rivales
area: fullstack
prioridad: 3
fuente: ALCANCE.md D8
archivos: backend/replays/analytics/aggregates.py, backend/replays/views.py, backend/tests/test_muertes_headshot.py, frontend/src/muertesHeadshot.js, frontend/src/muertesHeadshot.test.js, frontend/src/pages/Duelos.jsx, frontend/e2e/humo.spec.js, docs/metricas.md
turnos: po 20261113T2157Z-cG2vDSe, arquitecto 20261114T0040Z-chQsvnq, dev 20261114T0316Z-cwWsU9i, revisor 20261115T0219Z-i32143169, qa 20261118T1211Z-cMNRUxv, release 20261118T1211Z-cMNRUxv

## PR

Titulo: `[equipo-dev][fullstack] Cuántas de tus muertes son headshot, en Duelos`

### Que cambia

En Duelos, entre *Por rival* y *Rivales repetidos*, el panel **Muertes por
headshot**: de tus muertes a manos de rivales, cuántas fueron headshot, por
lado y en total, al lado del mismo número para tus compañeros en las mismas
rondas, con el `n` (muertes con dato) en cada celda. Es el reverso del HS%:
si te enganchan la cabeza más que al resto del equipo, te asomas expuesto.

### Por que esto y no otra cosa

Ficha 137 (ALCANCE D8, épica rivales). Se calcula al consultar sobre el
feed, como `nemesis` y `death_state` (conteo de eventos, sin columna nueva
ni migración), con una clave nueva en `/api/duels/` y sin URL nueva. Tus
compañeros van como referencia en tus mismas rondas filtradas para separar
"me enganchan la cabeza" de "en este juego todo es headshot". Partirlo por
operador rival quedó para la ficha 147 (D20).

### Como se probo

- `check.sh` (con `verificar.sh`): VERDE ede9b1244, 1404 tests backend, 459 vitest, 122 e2e.
- Tests nuevos: `test_muertes_headshot.py` (14: headshot sobre muertes con
  dato, `headshot` nulo fuera del %, teamkill y baja sin autor fuera, tus
  compañeros aparte, un rival no es compañero, víctima sin fila, partir por
  lado y sumar el total, lado desconocido solo al total, filtros de lado y de
  mapa, sin dato el % es nulo, la clave en `/api/duels/`, 2 consultas
  fijas); vitest `muertesHeadshot.test.js` (4); e2e `Duelos muestra las
  muertes por headshot`.
- QA: base sembrada desde `factories.py` (teamkills, baja sin autor, rival
  sobre rival, víctima sin fila, partida de un jugador, nick repetido,
  muerte sin dato): Tú total `7/5/4 80.0` y compañeros ataque `5/4/2 50.0`
  recalculados en SQL crudo iguales a la API; 25 combinaciones de filtros
  borde en 200; Playwright sin Critical ni Major (contraste 5,71:1 y
  14,17:1, teclado, CSV, 320 px, nota sin dato, consola limpia); 4
  mutaciones muertas; chunk inicial sin cambio (200,34 kB).
- OMC: plan=— · revisión=— · verificación=— (diseno)
- OMC: plan=— · revisión=no disponible (sin subagentes) · verificación=— (implementacion)
- OMC: plan=— · revisión=1 LOW (0 arreglados) · verificación=— (revision, sin subagentes)
- OMC: plan=— · revisión=— · verificación=PASS (QA, fallback del lider, sin subagentes)
- Skills del repo: statistical-analysis, testing-strategy (diseno); test-driven-development, testing-strategy, statistical-analysis, ux-copy, modern-web-guidance (implementacion); ninguna (revision); accessibility-review, design-critique, validate-data (QA).

### Riesgos y lo que no entra

Sin migración ni `recompute`: 2 consultas fijas por request
(`assertNumQueries`). Con `seed_demo` la fila *Tus compañeros* sale en raya
(la semilla no crea muertes de compañeros en el feed); la cubre el vitest y
la base sembrada de la QA. Fuera: por operador rival (ficha 147), en el
tiempo (idea E23), señal del Coach.

### Como probarlo en 2 minutos

```
cd backend; python manage.py seed_demo; python manage.py runserver
```
Abrir `/duelos`: el panel *Muertes por headshot* entre *Por rival* y
*Rivales repetidos*; con `seed_demo`, Tú `27% (98)` en Ataque, `23% (75)`
en Defensa y `25% (173)` en Total (173 = tus muertes del Resumen), Tus
compañeros en raya. Con "Solo ataque", Defensa queda en raya.

### Para el humano

Nada.

### Candidatos descubiertos

Ninguno (dos ideas de la QA en `ALCANCE.md`: D21, la diferencia Tú menos
compañeros por lado, y T10, encabezado de fila en las tablas).

## Que gana quien usa la app

El HS% que muestra la app es el tuyo al matar; el reverso no existe. En Duelos,
de tus muertes a manos de rivales, cuantas fueron headshot, por lado, al lado
del mismo numero para tus compañeros en las mismas rondas: si te enganchan la
cabeza mas que al resto del equipo, te asomas expuesto.

## Criterios de aceptacion

- [x] Agregado nuevo: de los `Event` de baja cuyo `target` eres tu y cuyo
      autor es rival (`_solo_rivales`, sin teamkills), `deaths`,
      `with_data` (`headshot` no nulo), `headshots` y `pct` =
      headshots / with_data, por lado de tu fila (`Attack`, `Defense`) y
      total. `headshot` nulo no entra en el porcentaje. Test con muertes con
      y sin dato y un teamkill que no cuenta.
- [x] La referencia: el mismo calculo sobre las muertes de tus compañeros
      (tu `team_index`, `is_me=False`) en tus rondas filtradas. Test.
- [x] Los filtros globales aplican sobre tu fila de la ronda; test con
      filtro de lado.
- [x] Se ve en Duelos (clave nueva en el endpoint que ya usa la pagina o uno
      nuevo de lectura) como una tabla chica Tú / Tus compañeros por lado, con
      el `n` (muertes con dato) a la vista y aviso si es chico; sin dato,
      una nota. e2e sobre `seed_demo` con los numeros de la API y consola
      limpia.
- [x] Fila nueva en `docs/metricas.md`.

## Fuera de alcance

- Partirlo por operador rival (otro tramo).
- Señal del Coach.

## Diseno

(arquitecto 20261114T0040Z-chQsvnq) Detalle completo en `git log`.
`aggregates.headshot_deaths(**filters)`: los `Kill` de tus rondas filtradas
(`_mis_bajas`) con autor rival (`_solo_rivales`) y víctima tuya (`_me_ids`)
o de tu equipo con fila en la ronda; por el lado de tu fila y en total,
`deaths`, `with_data`, `headshots` y `pct = headshots / with_data`. Conteos
sumados. Clave `headshot_deaths` en `/api/duels/`, panel en Duelos, fila en
`metricas.md`.

OMC: plan=— · revisión=— · verificación=—

## Implementacion

(dev 20261114T0316Z-cwWsU9i) El diseño completo, más CSV del panel y tres
tests extra (víctima sin fila, lado desconocido, filtro de mapa). La función
va junto a `_duelos` y la fila de `metricas.md` antes de *Rival repetido*
para no chocar con la 134. TDD con el rojo visto; 3 mutaciones muertas.

OMC: plan=— · revisión=no disponible (sin subagentes) · verificación=—

## Revision

- 2026-11-15 sobre d5009f8 (revisor 20261115T0219Z-i32143169): aprobar, 1
  LOW sin arreglar (el e2e no ve números en la fila de compañeros porque
  `seed_demo` no crea sus muertes; lo cubrió la QA con base sembrada).

OMC: plan=— · revisión=1 LOW (0 arreglados) · verificación=— (sin subagentes)

## QA 2026-11-18 sobre ede9b12

(qa 20261118T1211Z-cMNRUxv) `aprobado`; detalle con los comandos en
`git log` (commit `Prueba: 137`). check.sh VERDE ede9b1244 (1404, 459,
122); Tú total y compañeros ataque recalculados en SQL iguales a la API;
bordes 200; Playwright sin Critical ni Major; 4 mutaciones muertas.

Skills del repo: accessibility-review (0 Critical, 0 Major, 1 Minor que ya
estaba -> T10), design-critique (1 idea -> D21), validate-data (2 valores a
mano iguales, sin hallazgos).
OMC: plan=— · revisión=— · verificación=PASS (fallback del lider, sin subagentes)

## Para el humano

(nada)
