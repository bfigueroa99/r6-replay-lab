# 139. Rondas perdidas sobreviviendo

estado: implementado
candado: -
rama: claude/equipo-dev/139-rondas-perdidas-sobreviviendo
tipo: funcionalidad
epica: revision-de-rondas
area: fullstack
prioridad: 3
fuente: ALCANCE.md F11
archivos: backend/replays/analytics/aggregates.py, backend/replays/views.py, backend/replays/urls.py, backend/tests/test_perdidas_vivo.py, frontend/src/perdidasVivo.js, frontend/src/perdidasVivo.test.js, frontend/src/pages/Trends.jsx, frontend/e2e/humo.spec.js, docs/metricas.md
turnos: po 20261113T2318Z-chc2kiA, arquitecto 20261114T0040Z-c3LsMAo, dev 20261118T1211Z-cMNRUxv

## PR

## Que gana quien usa la app

Cuantas rondas terminaste vivo y tu equipo igual las perdio, por lado y por
mapa, con la lista de las mas recientes para abrirlas: dice si te guardas de
mas cuando la ronda se esta perdiendo (en ataque, tiempo agotado o defuse; en
defensa, la bomba que entra mientras sigues vivo).

## Criterios de aceptacion

- [x] Agregado nuevo en `aggregates.py` (p. ej. `lost_alive(**filters)`)
      sobre `base_queryset`: por lado (`Attack`, `Defense`) y total, rondas
      perdidas (`Round.my_team_won is False`) con tu `RoundPlayer.survived`
      en `True`, sobre tus rondas perdidas de ese lado. Las rondas con
      `my_team_won` nulo no entran ni al numerador ni al denominador. Test
      Django con una ronda perdida vivo, una perdida muerto, una ganada vivo
      (no cuenta) y una sin resultado (fuera).
- [x] El mismo agregado por mapa (con la version del mapa, como el resto de
      las tablas por mapa) y los filtros globales aplicados; test con filtro
      de lado o de mapa.
- [x] Lista de las 10 rondas perdidas vivo mas recientes (partida, mapa,
      lado, numero de ronda) con enlace que abre esa ronda en el detalle
      (`?ronda=` como el resto de enlaces a ronda). Test del orden y del
      tope.
- [x] Panel en la UI (pagina a elegir por el Arquitecto, cerca de
      "Duración de la ronda" o "Estado al morir") con la ayuda que diga que
      cuenta; e2e sobre `seed_demo` con los numeros de la API y consola
      limpia.
- [x] Fila nueva en `docs/metricas.md`.

## Fuera de alcance

- Juzgar si quedarse vivo estuvo bien o mal: no hay coordenadas ni plants
  exactos en temporadas nuevas (`docs/formato-rec.md`); no se usa
  `possible_plant`.
- Señales del Coach sobre esto.
- Lo mismo para tus compañeros (idea C20 de `ALCANCE.md`).
- Marcar esas rondas en el detalle de partida (idea F27).

## Diseno

(arquitecto 20261114T0040Z-c3LsMAo, sobre dev f34baba) Filtros duros: pasa (`RoundPlayer.survived`
y `Round.my_team_won`, que ya se guardan al importar; no usa plants ni
coordenadas; sin red, sin dependencias, sin POST, sin migracion ni
`recompute`). Una sola forma obvia: sin arena ni consenso.

Implementar despues de que #135 se mergee: la 135 (`implementado`) tambien
toca `frontend/src/pages/Trends.jsx`. El resto de `archivos:` lo tocan casi
todas las ramas con cambios aditivos y no frena.

**Regla** (va tal cual a `metricas.md`). Sobre tus filas de
`base_queryset(**filters)` (todos los filtros globales aplican, lado
incluido: es tu ronda): rondas perdidas = `round__my_team_won is False`;
perdidas vivo = esas con `survived=True`. `pct` = perdidas vivo / perdidas,
por lado (`Attack`, `Defense`), total y por mapa con version. Rondas
ganadas y sin ganador (`my_team_won` nulo) no entran a ninguno de los dos
lados de la division. Una fila con `side` vacio cuenta en el total y en su
mapa, no en ningun lado (como el resto de los cortes por lado).

**Archivos:**
- `backend/replays/analytics/aggregates.py`: `PERDIDAS_VIVO_RECIENTES = 10`
  y `lost_alive(**filters) -> dict`, cerca de `by_round_length`. Tres
  consultas fijas: un `aggregate` con `Count(... filter=Q(...))` por lado
  (perdidas y perdidas vivo de `Attack`, `Defense` y total), un `values(*_MAPA)
  .annotate(...)` por mapa con `_etiquetar` (orden por `lost` desc, despues
  `map`), y las 10 mas recientes (`order_by("-round__match__played_at",
  "-round__number")`, `values("round__match_id", "round__number", "side",
  "round__match__played_at", *_MAPA)`). Devuelve `{"total": {"lost",
  "lost_alive", "pct"}, "sides": [{"side": "Attack", ...}, {"side":
  "Defense", ...}], "maps": [...], "recent": [{"match_id", "number",
  "side", "played_at", "map", "slug", "map_id"}]}`. `pct` con `_pct`
  (None sin perdidas).
- `backend/replays/views.py` + `urls.py`: `GET /api/rounds/lost-alive/` ->
  `lost_alive(**_filters(request))`. Endpoint propio y no dentro de
  `/api/trends/`: ese payload ya es grande y lo comparten varios paneles.
- `backend/tests/test_perdidas_vivo.py` (Django, `factories.py`):
  `test_cuenta_perdidas_vivo_sobre_perdidas` (perdida vivo, perdida muerto,
  ganada vivo, sin ganador vivo -> `lost 2`, `lost_alive 1`, `pct 50.0`);
  `test_parte_por_lado`; `test_una_ronda_sin_lado_cuenta_en_el_total_y_no_en_los_lados`;
  `test_por_mapa_con_version`; `test_el_filtro_de_lado_aplica`;
  `test_las_recientes_van_de_la_mas_nueva_a_la_mas_vieja_con_tope_de_10`
  (12 rondas perdidas vivo en 3 partidas -> 10, la primera de la partida mas
  nueva y su ronda mas alta); `test_sin_rondas_no_rompe` (`pct` None, listas
  vacias); `test_consultas_constantes` (`assertNumQueries(3)`);
  `test_api_lost_alive_responde_con_filtros`.
- `frontend/src/perdidasVivo.js` + `perdidasVivo.test.js` (vitest):
  `hayPerdidas(data)`, `filasPorLado(data)` (Ataque, Defensa, Total, con
  `poca: lost < MUESTRA_CORTE` de `muestra.js`), `enlaceDeRonda(fila)` ->
  `` `/partidas/${match_id}${anclaDeRonda(number)}` `` (reusa
  `anclaDeRonda` de `navegacionRondas.js`). Tests: sin datos; orden y
  etiquetas de lado; `poca`; el enlace de la ronda 0 es `#ronda-1`.
- `frontend/src/pages/Trends.jsx`: panel "Rondas perdidas sobreviviendo"
  justo debajo de "Rondas cortas y largas", con su propio
  `useApi('/rounds/lost-alive/', filters)`. Hint: "Rondas que tu equipo
  perdió con vos vivo al final, sobre todas tus rondas perdidas. En ataque
  suele ser tiempo agotado o defuse; en defensa, la bomba que entra. No dice
  si quedarte vivo estuvo bien o mal." Tabla por lado (Lado, Perdidas,
  Vivo, % vivo, aviso "pocas rondas" si `poca`), tabla por mapa (Mapa,
  Perdidas, Vivo, % vivo), y lista "Las más recientes" con `Link` a cada
  ronda (fecha, mapa, lado, "Ronda N"). Nota sin perdidas: "Con estos
  filtros no hay rondas perdidas."
- `frontend/e2e/humo.spec.js`: test "Tendencias muestra las rondas perdidas
  sobreviviendo": panel por `section.panel` + heading, numeros por lado
  contra `/api/rounds/lost-alive/` sobre `seed_demo`, el primer enlace de la
  lista apunta a `/partidas/<id>#ronda-<n>` de `recent[0]` y al hacer clic
  abre el detalle en esa ronda; consola limpia. Si `seed_demo` no tiene
  perdidas vivo (el Dev lo mira en una base temporal), el test afirma la
  nota y el 0 contra la API; no se cambia `seed_demo`.
- `docs/metricas.md`: fila **Rondas perdidas sobreviviendo** en la tabla de
  Tendencias, cerca de **Rondas cortas y largas**, con la regla de arriba y
  el corte de muestra de 30 rondas (`MUESTRA_CORTE`).

**Numero (statistical-analysis):** proporcion sobre las perdidas (no sobre
todas las rondas: si no, perder mas bajaria el numero), con el `n` a la
vista; el total es la suma de conteos, nunca promedio de los dos lados. Sin
umbral nuevo: reusa `MUESTRA_CORTE`.

**Orden:** tests Django en rojo -> `lost_alive` -> vista/URL -> vitest ->
helper -> panel -> e2e -> `metricas.md` -> `npm run build`.

**Puede romperse:** el e2e de Tendencias que cuente paneles por posicion;
`survived` con abandonos (`PLAYER_LEAVE`): quien se fue figura no vivo, como
en el resto de la app, sin cambio aca.

**Verificacion manual:** `seed_demo` + `runserver`, Tendencias: el panel,
y un clic en una ronda reciente abre el detalle en esa ronda.

Skills: no aplica (panel con precedentes en la misma pagina).
Skills del repo: statistical-analysis (proporcion sobre perdidas, total por conteos, corte reusado), testing-strategy (Django para la regla y el orden, vitest para el helper y el enlace, e2e para el panel y la navegacion).
OMC: plan=— · revisión=— · verificación=—

## Implementacion

(dev 20261118T1211Z-cMNRUxv)

Quedo el diseno completo:

- `aggregates.lost_alive(**filters)` debajo de `by_round_length`, con
  `PERDIDAS_VIVO_RECIENTES = 10` y `PERDIDAS_VIVO_LADOS`. Tres consultas
  fijas sobre tus filas de `base_queryset` con `round__my_team_won=False`: un
  `aggregate` con `Count(..., filter=Q(...))` para total y cada lado (perdidas
  y perdidas con `survived`), un `values(*_MAPA).annotate(...)` por mapa con
  `_etiquetar` (orden: perdidas desc, despues mapa) y las 10 perdidas vivo
  mas recientes. Devuelve `total`, `sides` (Attack y Defense siempre, con
  ceros), `maps` y `recent` (`match_id`, `number`, `side`, `played_at`,
  `map`, `slug`, `map_id`); `pct` con `_pct`.
- `GET /api/rounds/lost-alive/` (`views.lost_alive`, junto a `trends`;
  url `lost-alive`).
- `frontend/src/perdidasVivo.js`: `hayPerdidas`, `filasPorLado` (Ataque,
  Defensa, Total con `orden` fijo y `poca` entre 1 y 29 perdidas, corte
  `MUESTRA_CORTE`), `enlaceDeRonda` con `anclaDeRonda` (`number` 0 ->
  `#ronda-1`) y `ETIQUETAS_LADO`.
- `Trends.jsx`: componente `PerdidasVivo` con su propio
  `useApi('/rounds/lost-alive/', filters)`, justo debajo de "Rondas cortas y
  largas": tabla por lado (Lado, Perdidas, Vivo, % vivo con "· pocas
  rondas"), "Por mapa" (Mapa, Perdidas, Vivo, % vivo), "Las más recientes"
  (fecha, mapa, lado y el enlace "Ronda N") y la nota de muestra chica; sin
  perdidas, "Con estos filtros no hay rondas perdidas."
- e2e "Tendencias muestra las rondas perdidas sobreviviendo": numeros por
  lado y total contra `/api/rounds/lost-alive/` (formateados a mano), suma
  por mapa = total, y el primer enlace de "Las más recientes" abre el
  detalle en esa ronda (`#ronda-N` y la pestaña activa `RN`).
- `docs/metricas.md`: fila **Rondas perdidas sobreviviendo** debajo de
  **Duracion de la ronda** y su corte en `## Muestra minima`.

Desvios menores del diseno:

- El hint dice "contigo vivo" y no "con vos vivo": la UI tutea en todas las
  paginas ("contigo" en Duelos y Compañeros), y la skill `ux-copy` pide el
  mismo termino en todos lados.
- Las recientes desempatan por `match_id` despues de `played_at` (dos
  partidas a la misma hora no cambian de orden entre consultas).
- La nota de muestra chica mira tambien la tabla por mapa (como Ventaja
  numerica tirada); el "· pocas rondas" va solo en la tabla por lado.
- Tests extra: `test_el_filtro_de_mapa_aplica` y
  `test_solo_rondas_ganadas_no_dan_perdidas`.

Criterios -> tests (`backend/tests/test_perdidas_vivo.py`, 11): (1)
`test_cuenta_perdidas_vivo_sobre_perdidas` (perdida vivo, perdida muerto,
ganada vivo y sin ganador vivo -> 2, 1, 50.0), `test_parte_por_lado`,
`test_una_ronda_sin_lado_cuenta_en_el_total_y_no_en_los_lados`,
`test_sin_rondas_no_rompe`, `test_solo_rondas_ganadas_no_dan_perdidas`;
(2) `test_por_mapa_con_version`, `test_el_filtro_de_lado_aplica`,
`test_el_filtro_de_mapa_aplica`; (3)
`test_las_recientes_van_de_la_mas_nueva_a_la_mas_vieja_con_tope_de_10`;
(4) `perdidasVivo.test.js` (4) y el e2e de Tendencias,
`test_api_lost_alive_responde_con_filtros` (`until=foo`, `page=-1`); (5)
fila en `metricas.md`. Ademas `test_consultas_constantes`
(`assertNumQueries(3)` con 1 y con 11 rondas).

TDD: los 11 tests Django en rojo antes del agregado (10 `AttributeError`
por `lost_alive`, 1 `404 != 200` por la ruta); el vitest en rojo antes de
`perdidasVivo.js` (`Failed to load url ./perdidasVivo.js`).

Mutaciones (codigo roto a mano y restaurado): las rondas sin ganador dentro
de las perdidas -> cae `test_cuenta_perdidas_vivo_sobre_perdidas`; el total
como suma de los dos lados (sin la fila sin lado) -> cae
`test_una_ronda_sin_lado_cuenta_en_el_total_y_no_en_los_lados`.

Sobre `seed_demo` (base del e2e): 87 rondas perdidas, todas en defensa, 12
vivo (13,8 %); por mapa Bank 30 (4), Club House 30 (3), Border 27 (5); 10
recientes, la primera la ronda 6 de la partida 29 (Bank).

Revision ciega: no disponible (esta sesion no tiene herramienta para lanzar
`omc-code-reviewer`). En su lugar, pasada propia con la lista de
`revision.md` sobre `git diff origin/dev...HEAD -- . ':(exclude)docs/backlog'`:
sin hallazgos (sin dependencias ni POST; calculado al consultar como
`by_round_length`, sin columna nueva; identificadores y comentarios sin
tildes, UI con tildes; sin `print` ni `console.log`; fila en `metricas.md`).
El Revisor hace la revision independiente.

Verificacion: `verificar.sh` VERDE cdd077c56 en 433s (1415 tests backend,
463 vitest, 123 e2e). Chunk inicial `index-*.js` 200,34 -> 200,38 kB;
`Trends-*.js` 36,05 -> 38,69 kB (diferido).

Verificacion manual sugerida: `seed_demo` + `runserver`, `/tendencias`: el
panel debajo de "Rondas cortas y largas" con Defensa 87 / 12 / 14 %, y un
clic en "Ronda 6" de la primera reciente abre la partida en R6.

Skills: no aplica (panel con precedentes en la misma pagina y en Ventaja numerica tirada).
Skills del repo: test-driven-development (rojo visto en Django y vitest),
testing-strategy (regla, orden y API en `TestCase`, helper y enlace en
vitest, panel y navegacion en e2e), statistical-analysis (proporcion sobre
las perdidas, total por conteos, `MUESTRA_CORTE` reusado), ux-copy (tuteo
"contigo" como el resto de la UI; nota vacia con que y por que),
modern-web-guidance (`guides/accessibility/accessibility.md`, "Lists and
tables": las tres tablas son datos con `th` por la `DataTable` existente y
el enlace dice a que ronda va); sql-queries no hizo falta (patron vecino
`thrown_advantage`, con `assertNumQueries`).
OMC: plan=— · revisión=no disponible (sin subagentes) · verificación=—

## Revision

## QA

## Para el humano

(nada)
