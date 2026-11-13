# 120. Puesto en el lobby

estado: entregado
candado: -
rama: claude/equipo-dev/120-puesto-en-el-lobby
tipo: funcionalidad
epica: progreso
area: fullstack
prioridad: 3
fuente: ALCANCE.md E7
archivos: backend/replays/analytics/aggregates.py (lobby_rank), backend/replays/views.py (trends), backend/tests/test_puesto_en_el_lobby.py (nuevo), frontend/src/puestoLobby.js (nuevo), frontend/src/puestoLobby.test.js (nuevo), frontend/src/pages/Trends.jsx (panel Puesto en el lobby), frontend/e2e/humo.spec.js, docs/metricas.md
turnos: po 20261113T1603Z-cHj1H4k, arquitecto 20261113T1733Z-cudo1Sw, dev 20261113T1802Z-c8dAf7p, revisor 20261113T1830Z-c2rHpej, qa 20261113T1858Z-cxQ3TuB, release 20261113T1858Z-cxQ3TuB

## PR

**Titulo:** [equipo-dev][frontend] Puesto en el lobby en Tendencias

### Que cambia

Tendencias suma el panel "Puesto en el lobby": en cuantas partidas fuiste el
mejor de los diez por Rating, el mejor de tu equipo y el ultimo, cada uno con
su % y su conteo. El Rating suelto no dice si arrastraste al equipo o te
arrastraron; esto si, y sale solo de tus replays.

### Por que esto y no otra cosa

Ficha 120 (`ALCANCE.md` E7, epica progreso). Se calcula al consultar con
`rating_points_expr` sobre las filas de todos (como `trend_by_match`): guardarlo
al importar pedia migracion. Descartado: puesto por score (el `.rec` ya no lo
atribuye) y comparar contra el promedio del lobby (E9, otra idea).

### Como se probo

- `check.sh` (con `verificar.sh`): VERDE sobre la rama fusionada con dev (QA: aec18f7, 1253 backend, 395 vitest, 106 e2e; Release: ver el ultimo commit).
- Tests nuevos (`backend/tests/test_puesto_en_el_lobby.py`, 14): mejor de la partida y de tu equipo, mejor de equipo sin ser mejor de la partida, ultimo, empates (con el mejor; con todos = mejor y ultimo), menos de 10 jugadores, solo vos no cuenta, sin compañeros, filtro de mapa, filtro de lado recorta las rondas de todos, un rival no te quita el mejor de tu equipo, tu fila sale de `RoundPlayer.is_me`, `assertNumQueries(2)` con 2 y 5 partidas, clave en `/api/trends/`. vitest `puestoLobby.test.js` (7). e2e `Tendencias muestra el puesto en el lobby`.
- Manual (QA): base sembrada con 6 partidas, valores recalculados a mano iguales a la API (total, `map=club-house`, `map=border`); bordes `until=foo`, `page=-1`, `side=Defense`, `map=nada` en 200; contraste medido >= 5.21:1; chunk inicial sin cambio.
- OMC: plan=— · revisión=—; implementacion: revisión=4 hallazgos (1 MEDIUM, 3 LOW; 3 arreglados, 1 cubierto con test); revision: 3 hallazgos LOW (el de estilo, arreglado en la entrega); QA: verificación=PASS
- Skills del repo: statistical-analysis, testing-strategy, ux-copy, sql-queries (dev); accessibility-review, design-critique, validate-data (QA).

### Riesgos y lo que no entra

Sin migracion, sin `recompute`, sin parser. Rendimiento: dos consultas
agrupadas sobre las filas de todos en tus rondas filtradas (la escala de
`teammate_synergy`). Fuera: el puesto en el detalle de cada partida (otro
tramo) y el promedio del lobby (E9).

### Como probarlo en 2 minutos

```powershell
cd backend; python manage.py seed_demo; python manage.py runserver
curl -s localhost:8000/api/trends/   # mirar "lobby_rank": tres casos con count, matches y pct
```

Abrir `http://localhost:8000/tendencias`: panel "Puesto en el lobby" despues de
"Por partida", tres stats con "N de M partidas". Con un mapa en el filtro
cambian los numeros; con un filtro sin partidas con otros jugadores, la nota.

### Para el humano

Nada.

### Candidatos descubiertos

Ninguno.

## Que gana quien usa la app

En Tendencias, cuantas veces fuiste el mejor de la partida por Rating, el
mejor de tu equipo y el ultimo de los diez: el Rating suelto no dice si
arrastraste al equipo o te arrastraron. Solo sale de tus replays, que traen
a los diez jugadores.

## Criterios de aceptacion

- [x] Un agregado nuevo en `aggregates.py` calcula, por partida, tu puesto
      entre los jugadores de la partida y dentro de tu equipo por el rating
      de la partida (`rating_points_expr` sobre las filas `RoundPlayer` de
      todos, como `trend_by_match`), y devuelve `matches`, `best_in_lobby`,
      `best_in_team` y `last_in_lobby` (conteo y %). Test con una partida
      armada de 10 jugadores de rating conocido.
- [x] Empate de rating con otro jugador: cuenta como mejor (o ultimo) solo
      si nadie te supera (o nadie esta por debajo); regla en
      `docs/metricas.md` y test.
- [x] Partidas con menos de 10 jugadores (abandonos) entran con los que hay;
      una partida en la que solo estas vos no cuenta. Test.
- [x] Los filtros globales de partida (mapa, tipo, modo, fechas) aplican;
      los de ronda (lado, operador, sitio) recortan las rondas de todos por
      igual. Test con filtro de mapa.
- [x] En Tendencias, una fila de tres stats (Mejor de la partida, Mejor de
      tu equipo, Último de la partida) con el % y el conteo; sin partidas,
      un texto y no ceros. e2e de humo con los numeros de `seed_demo` y la
      consola limpia.
- [x] Fila nueva en `docs/metricas.md` ("Puesto en el lobby").

## Fuera de alcance

- El puesto en el detalle de cada partida (otro tramo, chico, despues de este).
- Comparar contra el promedio del lobby (E9, otra idea).
- Puesto por score de la partida: el `.rec` ya no lo atribuye.

## Diseno

Arquitecto 20261113T1733Z-cudo1Sw: `lobby_rank(**filters)` en `aggregates.py`,
rating de la partida = promedio de `rating_points_expr` en las rondas filtradas
(sin dividir por la linea base: no cambia el orden); empate con tolerancia
`1e-9` cuenta como mejor y como ultimo; compañero = mismo `team_index` en alguna
ronda filtrada; partida con solo vos no entra. Clave `lobby_rank` en `trends`,
`puestoLobby.js` + panel en `Trends.jsx`, humo e2e y filas en `metricas.md`.
El detalle completo esta en `git log` de esta ficha.

## Implementacion

(dev 20261113T1802Z-c8dAf7p) Diseno completo. Desvio corregido: tu fila sale de
`RoundPlayer.is_me` (como `base_queryset`) y no de `Player.is_me`, con test que
cae sin el arreglo. 2 consultas fijas. VERDE 8571ad34c.
OMC: plan=— · revisión=4 hallazgos (1 MEDIUM, 3 LOW; 3 arreglados, 1 cubierto con test) · verificación=—

## Revision 2026-11-13 sobre dc941a9

(revisor 20261113T1830Z-c2rHpej) Aprobar. P3 resuelto (import en `Trends.jsx`
contra la 119). Unico hallazgo: L1 LOW, dos comentarios con "compañero" con ñ;
corregido en la entrega. VERDE dc941a9b0.
OMC: plan=— · revisión=3 hallazgos LOW (0 arreglados: 1 al humano, 2 decisiones del diseno) · verificación=—

## QA 2026-11-13 sobre aec18f7

(qa 20261113T1858Z-cxQ3TuB) Aprobado. VERDE aec18f7fe (1253 backend, 395 vitest, 106 e2e). Base
vacia: ceros con `pct None`, sin panel. Base sembrada (6 partidas, nick
repetido incluido): total (2,5,40) (3,4,75) (2,5,40), `map=club-house` y
`map=border` iguales a mano; bordes en 200. Chunk inicial 0 %, Trends +3,5 %.
Contraste 5.21 a 12.92, sin Critical/Major, consola limpia. Mutacion 3/3
detectadas. Detalle con comandos en `git log` (commit `Prueba: 120`).
Skills del repo: accessibility-review, design-critique, validate-data, testing-strategy.
OMC: plan=— · revisión=— · verificación=PASS

## Entrega

(release 20261113T1858Z-cxQ3TuB) Fusionada con `origin/dev`, comentarios sin ñ (L1 de la
revision), `verificar.sh` en verde sobre el commit de entrega.

## Para el humano

(nada)
