# 139. Rondas perdidas sobreviviendo

estado: disenado
candado: -
rama: -
tipo: funcionalidad
epica: revision-de-rondas
area: fullstack
prioridad: 3
fuente: ALCANCE.md F11
archivos: backend/replays/analytics/aggregates.py, backend/replays/views.py, backend/replays/urls.py, backend/tests/test_perdidas_vivo.py, frontend/src/perdidasVivo.js, frontend/src/perdidasVivo.test.js, frontend/src/pages/Trends.jsx, frontend/e2e/humo.spec.js, docs/metricas.md
turnos: po 20261113T2318Z-chc2kiA, arquitecto 20261114T0040Z-c3LsMAo

## PR

## Que gana quien usa la app

Cuantas rondas terminaste vivo y tu equipo igual las perdio, por lado y por
mapa, con la lista de las mas recientes para abrirlas: dice si te guardas de
mas cuando la ronda se esta perdiendo (en ataque, tiempo agotado o defuse; en
defensa, la bomba que entra mientras sigues vivo).

## Criterios de aceptacion

- [ ] Agregado nuevo en `aggregates.py` (p. ej. `lost_alive(**filters)`)
      sobre `base_queryset`: por lado (`Attack`, `Defense`) y total, rondas
      perdidas (`Round.my_team_won is False`) con tu `RoundPlayer.survived`
      en `True`, sobre tus rondas perdidas de ese lado. Las rondas con
      `my_team_won` nulo no entran ni al numerador ni al denominador. Test
      Django con una ronda perdida vivo, una perdida muerto, una ganada vivo
      (no cuenta) y una sin resultado (fuera).
- [ ] El mismo agregado por mapa (con la version del mapa, como el resto de
      las tablas por mapa) y los filtros globales aplicados; test con filtro
      de lado o de mapa.
- [ ] Lista de las 10 rondas perdidas vivo mas recientes (partida, mapa,
      lado, numero de ronda) con enlace que abre esa ronda en el detalle
      (`?ronda=` como el resto de enlaces a ronda). Test del orden y del
      tope.
- [ ] Panel en la UI (pagina a elegir por el Arquitecto, cerca de
      "Duración de la ronda" o "Estado al morir") con la ayuda que diga que
      cuenta; e2e sobre `seed_demo` con los numeros de la API y consola
      limpia.
- [ ] Fila nueva en `docs/metricas.md`.

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

## Revision

## QA

## Para el humano

(nada)
