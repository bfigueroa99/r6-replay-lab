# 133. Ventaja numerica tirada

estado: en curso 2026-11-13T22:01Z
candado: -
rama: claude/equipo-dev/133-ventaja-numerica-tirada
tipo: funcionalidad
epica: revision-de-rondas
area: backend
prioridad: 3
fuente: ALCANCE.md F5
archivos: backend/replays/analytics/metrics.py (ventaja_maxima), backend/replays/analytics/aggregates.py (thrown_advantage), backend/replays/views.py, backend/replays/urls.py, backend/tests/test_ventaja_tirada.py (nuevo), frontend/src/ventajaTirada.js (nuevo), frontend/src/ventajaTirada.test.js (nuevo), frontend/src/components/VentajaTirada.jsx (nuevo), frontend/src/pages/Duelos.jsx, frontend/e2e/humo.spec.js, docs/metricas.md
turnos: po 20261113T1926Z-ce4Pmp6, arquitecto 20261113T1926Z-cq9nfTP

## PR

## Que gana quien usa la app

Cuantas rondas perdio tu equipo despues de quedar con un jugador mas (o
dos), por lado y por mapa, con enlace a cada una para volver a verla. Es el
error que mas duele y el marcador no lo muestra; hoy solo lo cuenta la
narrativa de una ronda suelta en el detalle de partida.

## Criterios de aceptacion

- [ ] Agregado nuevo en `aggregates.py`: recorre las bajas de cada ronda en
      orden de reloj (`Event` de baja con el `team_index` de la victima;
      los abandonos cuentan como baja, igual que en `stats.py`) y marca la
      ronda si tu equipo llego a tener mas vivos que el rival y la perdio
      (`Round.my_team_won = False`). Rondas sin ganador no cuentan. Devuelve
      el total de rondas con ventaja, cuantas se tiraron y el %, por lado y
      por mapa. Test con una ronda 5v4 ganada, una 5v4 perdida y una sin
      ventaja.
- [ ] Separa ventaja de uno y de dos o mas (la maxima de la ronda). Test con
      una ronda que llego a 5v3.
- [ ] Lista de las rondas tiradas (partida, numero de ronda, mapa, lado,
      ventaja maxima) con enlace al detalle de la ronda, mas recientes
      primero y con tope; test del orden y del tope.
- [ ] Los filtros globales aplican sobre tu fila de la ronda; test con
      filtro de lado.
- [ ] Panel en una pagina que no este en `saturadas` de `ROTACION` (hoy
      Tendencias lo esta), con su nota sin rondas; e2e sobre `seed_demo`
      con los numeros de la API y consola limpia.
- [ ] Fila nueva en `docs/metricas.md` (y en `## Muestra minima` si avisa
      muestra chica).

## Fuera de alcance

- El reverso, rondas dadas vuelta en inferioridad (F12).
- Quien murio despues de la ventaja.
- Señales del Coach sobre esto.

## Diseno

(arquitecto 20261113T1926Z-cq9nfTP, sobre `origin/dev@c332e72`) Filtros duros: pasa (feed de bajas, `PlayerLeave`, `team_index` y `Round.my_team_won`, todo ya importado; sin red, sin dependencias, sin POST, sin migracion: se calcula al consultar, como `death_state`, que es el vecino directo). Una forma obvia que copia `death_state`, ~400 lineas con tests: cabe en un turno de Dev, sin tramos. Sin arena ni consenso (no toca migraciones, `recompute` ni parser).

**Regla (metrics.py, pura y testeable).** `ventaja_maxima(eventos, team_of, equipo) -> int | None` en `backend/replays/analytics/metrics.py`, junto a `estado_al_morir` y con su mismo recorrido: `vivos = set(team_of)`; por cada evento `Kill` (sale `target`), `Death` o `PlayerLeave` (sale `actor`) cuyo jugador sigue vivo, se lo quita y se mide `mios - suyos` (vivos de `equipo` contra el resto). Devuelve el maximo de esas diferencias despues de cada salida, o `None` si el feed no tiene ninguna salida. Un `PlayerLeave` resta un vivo (como en `estado_al_morir`: quien se fue no ayuda); un teamkill tambien. La diferencia **inicial** (un 5v4 de arranque) no cuenta sola: cuenta desde la primera salida, asi "quedar con uno mas" es algo que paso en la ronda. Ventaja = maximo >= 1; *de uno* si es 1, *de dos o mas* si es >= 2.

**Agregado, `backend/replays/analytics/aggregates.py`**: `thrown_advantage(**filters) -> dict`, despues de `death_state`, con su misma forma de consultar:
- `mias = base_queryset(**filters)` (tu fila de cada ronda: los filtros globales aplican sobre ella, criterio 4); `filas = mias.values("round_id", "team_index", "side", "round__my_team_won", "round__number", "round__match_id", "round__match__map_name", "round__match__played_at")`.
- Equipos y feeds con `Exists(mias.filter(round_id=OuterRef("round_id")))`, igual que `death_state` (correlacionada por el tope de parametros de SQLite), con `Event.KILL`, `Event.DEATH`, `PLAYER_LEAVE` en orden `("round_id", "order")`, por ids.
- Por ronda: `ventaja_maxima(feed, equipos[rid], fila["team_index"])`. `None` o `< 1`: no entra. Sin ganador (`my_team_won is None`): no entra (criterio 1). Si entra: `rounds += 1`; `thrown += 1` si `my_team_won is False`; por grupo (`one` / `two_plus`), por lado (`Attack` / `Defense`, otro lado solo en total) y por mapa (`map_name`).
- Salida: `{"rounds", "thrown", "thrown_pct", "groups": [{"group": "one"|"two_plus", "rounds", "thrown", "thrown_pct"}], "sides": [{"side", ...}], "maps": [{"map", ...}] (orden: `-thrown`, `-rounds`, `map`), "recent": [...]}`. `thrown_pct = _pct(thrown, rounds)`.
- `recent`: las tiradas, `played_at` desc y `round__number` desc, tope `VENTAJA_TIRADA_TOPE = 20` (constante con comentario: la lista es para abrir rondas, no un historial), cada una `{"match_id", "map", "played_at" (ISO), "round" (number + 1, la etiqueta R<n>), "side", "advantage"}`.
- `views.py`: `thrown_advantage(request)` como `death_state` (`_ok(agg.thrown_advantage(**_filters(request)))`); `urls.py`: `path("duels/thrown-advantage/", views.thrown_advantage, name="thrown-advantage")`, junto a `death-state`.

**Tests**, `backend/tests/test_ventaja_tirada.py` (nuevo; feeds con `make_event` de `factories.py`, cinco por lado como arman `test_death_state`/`test_estado_al_morir` si existen; si no, `make_round_player` por jugador):
- `metrics`: `test_una_baja_rival_da_ventaja_de_uno`, `test_un_5v3_da_ventaja_de_dos`, `test_un_abandono_rival_cuenta_como_baja`, `test_un_5v4_de_arranque_sin_bajas_no_es_ventaja` (feed vacio -> `None`), `test_cambiar_bajas_sin_pasar_adelante_no_es_ventaja` (4v5 y despues 4v4: max 0).
- agregado: `test_cuenta_ventaja_ganada_tirada_y_sin_ventaja` (5v4 ganada, 5v4 perdida, ronda sin ventaja -> rounds 2, thrown 1, 50.0), `test_separa_ventaja_de_uno_y_de_dos` (una llega a 5v3), `test_una_ronda_sin_ganador_no_cuenta`, `test_la_lista_va_de_la_mas_reciente_y_tiene_tope` (21 tiradas -> 20, la primera es la mas reciente), `test_el_filtro_de_lado_aplica_sobre_tu_fila` (`side="Attack"` deja afuera la de defensa), `test_por_mapa` (dos mapas), y un `assertNumQueries` que fije las consultas con 1 y con 3 rondas (no crece por ronda).

**Frontend.**
- `frontend/src/ventajaTirada.js` (nuevo, puro, como `estadoAlMorir.js`): `hayVentajas(data)`, `filasDeGrupos(data)` (etiquetas "Con uno más" / "Con dos o más"), `filasDeLados(data)` ("Ataque" / "Defensa"), `enlaceDeRonda(fila)` -> `/partidas/<match_id>#ronda-<round>` (la etiqueta R<n> ya es el numero humano que lee `indiceDeAncla`). Vitest `ventajaTirada.test.js`: sin datos / sin rondas, etiquetas y orden de los grupos, enlace.
- `frontend/src/components/VentajaTirada.jsx` (nuevo, como `EstadoAlMorir.jsx`: panel aparte con su consulta, para que Duelos sume un import y una linea): `Panel title="Ventaja numérica tirada"` con `hint` "Rondas en que tu equipo llegó a tener más vivos que el rival, y cuántas perdió."; tres `DataTable` chicos (por ventaja, por lado, por mapa) con columnas Rondas con ventaja, Tiradas, % tiradas (`pct`); aviso de muestra chica con `MUESTRA_CORTE` (30 rondas con ventaja por fila, no se oculta); lista "Últimas tiradas" (`DataTable`: Partida con `Link` a `enlaceDeRonda`, Mapa, Ronda, Lado, Ventaja `+N`, fecha). Sin rondas: nota "No hay rondas con ventaja numérica con estos filtros.".
- `frontend/src/pages/Duelos.jsx`: `import VentajaTirada from '../components/VentajaTirada.jsx'` y `<VentajaTirada filters={filters} />` justo despues de `<EstadoAlMorir filters={filters} />`. Duelos no esta en `saturadas` (2 de las ultimas 10).

**e2e, `frontend/e2e/humo.spec.js`**, test `Duelos muestra la ventaja numerica tirada`, junto al de `Estado al morir` (linea ~488): leer `/api/duels/thrown-advantage/`; el panel `section.panel` con "Ventaja numérica tirada" muestra `rounds` y `thrown` del total (o, si `seed_demo` no tiene rondas con ventaja, la nota sin rondas: el test afirma la rama que corresponde segun la API); si hay `recent`, el primer enlace apunta a `/partidas/<id>#ronda-<n>` y al clicarlo la pestaña de esa ronda esta `active`. Consola limpia.

**`docs/metricas.md`**, seccion `## Duelos`, fila nueva **Ventaja numérica tirada**: "Panel de Duelos (`/api/duels/thrown-advantage/`). Rondas en que, despues de alguna baja o abandono del feed, tu equipo tuvo mas vivos que el rival (contandote; una diferencia de arranque sin bajas no cuenta). *Tiradas*: las de esas que tu equipo perdio. % tiradas = tiradas / rondas con ventaja; rondas sin ganador no entran. Se separa la ventaja maxima de la ronda: uno, dos o mas. Un `PlayerLeave` y un teamkill restan su vivo. Todos los filtros globales aplican sobre tu fila. Lista: las 20 tiradas mas recientes." Y en `## Muestra minima`: "Ventaja numérica tirada | 30 rondas con ventaja por fila: no se oculta, se avisa".

**statistical-analysis.** Denominador: rondas con ventaja y con ganador (el `n` va en la tabla, columna Rondas con ventaja). Ponderado por ronda, sin promedio de promedios (por mapa y por lado son cuentas, no medias de partidas). Con `n < 30` la diferencia entre mapas es ruido: aviso, no se oculta. Umbral de 30 calibrado con datos sinteticos: "calibrar con la base real" va a `## Para el humano`.

**Orden.** `ventaja_maxima` + tests (rojo, verde) -> `thrown_advantage` + tests + `assertNumQueries` -> vista y url -> `ventajaTirada.js` + vitest -> `VentajaTirada.jsx` -> Duelos -> e2e -> `metricas.md` -> `npm run build` -> `verificar.sh`.

**Que puede romperse.** Nada existente: endpoint, componente y funcion nuevos; Duelos suma un panel al final (los e2e de Duelos buscan paneles por titulo). Rendimiento: dos consultas correlacionadas como `death_state`, que ya corre en la misma pagina.

**Archivos ocupados.** 123 toca `aggregates.py`, `views.py`, `metricas.md` y `humo.spec.js` en otras zonas (clutches de compañeros); 79 toca `aggregates.py`/`views.py`/`urls.py` (otras funciones y otra ruta). Hunks distintos: no se frena; si `merge-tree` da conflicto en `urls.py`, P3.

**Verificacion manual.** `seed_demo`, `/duelos`: panel "Ventaja numérica tirada"; filtrar por lado cambia los numeros; clic en una fila de "Últimas tiradas" abre la partida en esa ronda.

Skills: no aplica (copia el patron de `death_state` y `EstadoAlMorir`).
Skills del repo: statistical-analysis (denominador, `n` en la tabla, sin promedio de promedios, muestra 30 avisada), testing-strategy (Django para la regla y el agregado, vitest para las etiquetas y el enlace, e2e para el panel en la app real).
OMC: plan=— · revisión=— · verificación=—

## Implementacion

## Revision

## QA

## Para el humano

- (arquitecto 2026-11-13, no bloquea) Calibrar con la base real el aviso de muestra de 30 rondas con ventaja por fila.

(nada)
