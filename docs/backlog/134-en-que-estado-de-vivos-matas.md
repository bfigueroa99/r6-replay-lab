# 134. En que estado de vivos matas

estado: entregado
candado: -
rama: claude/equipo-dev/134-en-que-estado-de-vivos-matas
tipo: funcionalidad
epica: impacto
area: backend
prioridad: 3
fuente: ALCANCE.md K8; Fuera de alcance de la ficha 116 ("el reverso, tus bajas por estado (K8): otro tramo de la epica")
archivos: backend/replays/analytics/metrics.py (estado_al_matar), backend/replays/analytics/aggregates.py (kill_state), backend/replays/views.py, backend/replays/urls.py, backend/tests/test_estado_al_matar.py (nuevo), frontend/src/estadoAlMatar.js (nuevo), frontend/src/estadoAlMatar.test.js (nuevo), frontend/src/components/EstadoAlMatar.jsx (nuevo), frontend/src/pages/Duelos.jsx, frontend/e2e/humo.spec.js, docs/metricas.md
turnos: po 20261113T1954Z-cfZTvvE, arquitecto 20261113T2317Z-cBbsozQ, dev 20261114T0012Z-ccgaH14, revisor 20261114T0040Z-c3LsMAo, dev 20261114T0104Z-cWK4yQD, revisor 20261114T0316Z-cwWsU9i, qa 20261115T0219Z-i32143169, release 20261115T0219Z-i32143169

## PR

Titulo: `[equipo-dev][backend] En qué estado de vivos matas, en Duelos`

### Que cambia

En Duelos, debajo de *Estado al morir*, el panel **Estado al matar**: tus
bajas a rivales repartidas por cuántos quedaban vivos de cada lado justo
antes de cada una (5v5, 5v4, 4v5...), agrupadas en con ventaja, en paridad y
en desventaja, con el winrate de esas rondas. Dice si tus bajas abren
ventajas o llegan cuando la ronda ya estaba decidida.

### Por que esto y no otra cosa

Ficha 134 (ALCANCE K8, épica impacto): el reverso de Estado al morir
(ficha 116), con su mismo recorrido del feed (`metrics.estado_al_matar`) y
endpoint aparte `GET /api/duels/kill-state/`. Las bajas que el feed te da
después de tu caída (trampas, gadgets o un intercambio del mismo instante)
no tienen estado tuyo y se cuentan aparte (`post_mortem`), en vez de pasar
por "no se puede ubicar en el feed", que era falso (hallazgo de la primera
revisión).

### Como se probo

- `check.sh` (con `verificar.sh`): VERDE 6c4fd3ef3, 1390 tests backend, 455 vitest, 121 e2e.
- Tests nuevos: `test_estado_al_matar.py` (23: regla pura con 5v5 y 5v4,
  teamkill que resta un vivo, teamkill tuyo, `PlayerLeave`, trade, autor
  que ya cayó, sin actor; agregado con winrate sobre rondas distintas, ronda
  sin ganador, solo teamkills, sin feed, después de caer, filtro de lado,
  orden de estados, 3 consultas fijas, API); vitest `estadoAlMatar.test.js`
  (6); e2e `Duelos muestra el estado de vivos al matar`.
- QA: base sembrada desde `factories.py` con dos valores recalculados a
  mano iguales a la API y el total igual a las bajas del Resumen (9 + 1 + 2
  = 12), `curl` con filtros borde (todos 200), nick repetido, partida de un
  jugador, Playwright (orden de paneles, teclado, `aria-sort`, contraste
  14,17:1 y 5,71:1, reflow a 640 px, estado sin bajas, consola limpia),
  3 mutaciones muertas, chunk inicial sin cambio.
- OMC: plan=— · revisión=— · verificación=— (diseno)
- OMC: plan=— · revisión=1 MEDIUM, 5 LOW (3 arreglados) · verificación=— (implementacion, con el arreglo de hallazgos)
- OMC: plan=— · revisión=1 LOW (0 arreglados) · verificación=— (revision, sin subagentes)
- OMC: plan=— · revisión=— · verificación=PASS (QA, fallback del lider, sin subagentes)
- Skills del repo: statistical-analysis, testing-strategy (diseno); test-driven-development, testing-strategy, statistical-analysis, ux-copy (implementacion); ninguna (revision); accessibility-review, validate-data, design-critique (QA).

### Riesgos y lo que no entra

Sin migración ni `recompute`: se calcula al consultar sobre el feed, como
Estado al morir (3 consultas fijas por request). Con `seed_demo` 65 de 99
bajas caen en "después de tu caída", porque el seed ordena tu muerte antes
que tus bajas (idea T7 de `ALCANCE.md`); con datos reales el feed va en
orden de juego. Fuera: probabilidad de ganar por estado o impacto por baja
(K1, K2), bajas de tus compañeros por estado, normalizar a 5v5.

### Como probarlo en 2 minutos

```
cd backend; python manage.py seed_demo; python manage.py runserver
```
Abrir `/duelos`: el panel *Estado al matar* debajo de *Estado al morir*;
con `seed_demo`, Con ventaja 19 bajas en 17 rondas (64,7 %), En paridad 15
(60 %), y la nota "65 bajas llegaron al feed después de tu caída". Bajas
por estado + las de las notas = Bajas del Resumen con los mismos filtros;
"Solo ataque" cambia los números.

### Para el humano

Nada.

### Candidatos descubiertos

Ninguno (dos ideas de la QA en `ALCANCE.md`: el `n` del winrate y los anchos de columna).

## Que gana quien usa la app

Tus bajas repartidas por el estado de vivos de la ronda en el instante en
que las haces (5v5, 5v4, 4v5, 2v3...) y el winrate de esas rondas: si tus
bajas abren ventajas o llegan cuando la ronda ya estaba decidida. Es el
reverso de Estado al morir (ficha 116), que ya esta en Duelos.

## Criterios de aceptacion

- [x] Un agregado devuelve, por estado `tuyos vivos v rivales vivos` justo
      antes de cada baja tuya a un rival, `kills` y `winrate` de esas rondas
      (sobre las que tienen ganador; una ronda con dos bajas tuyas cuenta
      en los dos estados). Test con una ronda armada: tu primera baja en
      `5v5`, la segunda en `5v4`.
- [x] Los teamkills no cuentan como baja tuya (como `kills` desde la
      ficha 67) pero si restan un vivo de tu equipo; un `PlayerLeave` resta
      un vivo (como `pydissect/stats.py`). Test de los dos.
- [x] Ventaja, paridad y desventaja agregadas (`ahead`, `even`, `behind`)
      ademas del estado exacto, con su winrate, con la misma recorrida de
      vivos que `death_state` (`metrics.estado_al_morir` o su vecina). Test.
- [x] Los filtros globales aplican (lado, mapa, operador, tipo, fechas,
      sesion). Test de lado.
- [x] Se ve en Duelos junto a Estado al morir, con la muestra minima de
      `metricas.md` como aviso; sin bajas, un texto y no un error; e2e por
      esa pagina con la consola limpia. Fila nueva en `docs/metricas.md`
      ("Estado al matar").

## Fuera de alcance

- Probabilidad de ganar por estado o impacto por baja (K1, K2).
- Bajas de tus compañeros por estado.
- Partidas con menos de 5 por lado: el estado se cuenta con los jugadores
  que hay, sin normalizar a 5v5 (como la 116).

## Diseno

(arquitecto 20261113T2317Z-cBbsozQ) Detalle completo en `git log`. Espejo
de `death_state`: `metrics.estado_al_matar(eventos, team_of)` anota para el
autor de cada `Kill` a un rival `(aliados vivos contandose, rivales vivos)`
antes de descontar al muerto; teamkill y `PlayerLeave` restan su vivo y no
son baja; sin agrupar por segundo. `aggregates.kill_state` suma bajas por
fila y rondas y winrate sobre rondas distintas de la fila. Panel
`EstadoAlMatar.jsx` en Duelos y fila en `metricas.md`.

OMC: plan=— · revisión=— · verificación=—

## Implementacion

(dev 20261114T0012Z-ccgaH14; arreglo de hallazgos dev 20261114T0104Z-cWK4yQD)
El diseño completo, con `_equipos_y_feeds` compartido con `death_state`,
columna Rondas en la tabla por estado y `post_mortem`
(`metrics.bajas_despues_de_caer`) aparte de `sin_feed`. TDD con el rojo
visto. Deuda anotada: el orden del feed de `seed_demo` (idea T7).

OMC: plan=— · revisión=1 MEDIUM, 5 LOW (3 arreglados) · verificación=—

## Revision

- 2026-11-14 sobre 6851732 (revisor 20261114T0040Z-c3LsMAo): corregir. MEDIUM
  arreglado: bajas tras tu caída contadas como `sin_feed` -> `post_mortem`;
  LOW arreglados: test de `sin_feed` y `_grupo_de` compartido.
- 2026-11-14 sobre 55b3d67 (revisor 20261114T0316Z-cwWsU9i): aprobar, 1 LOW
  sin arreglar (la nota dice "tu caída" y tambien cuenta un `PlayerLeave`
  tuyo; `metricas.md` si lo dice).

OMC: plan=— · revisión=1 LOW (0 arreglados) · verificación=— (sin subagentes)

## QA 2026-11-15 sobre 6c4fd3e

(qa 20261115T0219Z-i32143169) `aprobado`; detalle con los comandos en
`git log` (commit `Prueba: 134`). check.sh VERDE 6c4fd3ef3 (1390, 455,
121); dos valores recalculados a mano iguales a la API y total igual al
Resumen; bordes 200; Playwright sin Critical ni Major; 3 mutaciones muertas.

Skills del repo: accessibility-review (0 Critical, 0 Major), validate-data
(2 valores a mano iguales; 1 Minor: el `n` del winrate son las decididas),
design-critique (1 idea: anchos de columna).
OMC: plan=— · revisión=— · verificación=PASS (fallback del lider, sin subagentes)

## Para el humano

(nada)
