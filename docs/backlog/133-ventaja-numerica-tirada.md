# 133. Ventaja numerica tirada

estado: con hallazgos
candado: -
rama: claude/equipo-dev/133-ventaja-numerica-tirada
tipo: funcionalidad
epica: revision-de-rondas
area: backend
prioridad: 3
fuente: ALCANCE.md F5
archivos: backend/replays/analytics/metrics.py (ventaja_maxima), backend/replays/analytics/aggregates.py (thrown_advantage), backend/replays/views.py, backend/replays/urls.py, backend/tests/test_ventaja_tirada.py (nuevo), frontend/src/ventajaTirada.js (nuevo), frontend/src/ventajaTirada.test.js (nuevo), frontend/src/components/VentajaTirada.jsx (nuevo), frontend/src/pages/Duelos.jsx, frontend/e2e/humo.spec.js, docs/metricas.md
turnos: po 20261113T1926Z-ce4Pmp6, arquitecto 20261113T1926Z-cq9nfTP, dev 20261113T2157Z-chbMW9r, revisor 20261113T2156Z-cQ8Kk3s

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

(dev 20261113T2157Z-chbMW9r) Diseno completo, sobre `origin/dev@72df8f9`:

- `metrics.ventaja_maxima(eventos, team_of, equipo)`: mismo recorrido que `estado_al_morir`; `Kill`/`Death`/`PlayerLeave` sacan un vivo (teamkill y abandono incluidos), maximo de `mios - suyos` despues de cada salida, `None` sin salidas (el 5v4 de arranque no cuenta solo).
- `aggregates.thrown_advantage(**filters)` + `VENTAJA_TIRADA_TOPE = 20`: tu fila filtrada, rondas sin ganador fuera, feeds y equipos con `Exists` correlacionado como `death_state`; total, `groups` (`one`/`two_plus`), `sides`, `maps` y `recent` (fecha desc, ronda desc, tope 20; `round` = `number + 1`, la etiqueta que lee `#ronda-N`). Vista `@require_GET` y ruta `duels/thrown-advantage/`.
- Frontend: `ventajaTirada.js` (puro: `hayVentajas`, `filasDeGrupos`, `filasDeLados`, `enlaceDeRonda` sobre `anclaDeRonda`), `components/VentajaTirada.jsx` (panel "Ventaja numérica tirada": linea de total, tablas por ventaja, lado y mapa, aviso de muestra con `MUESTRA_CORTE`, "Últimas tiradas" con enlace a la ronda, nota sin rondas) y una linea en `Duelos.jsx` despues de `EstadoAlMorir`.
- `metricas.md`: fila en `## Duelos` y en `## Muestra minima`.

Desvio del diseno: `maps` agrupa por version (`map_slug`, `map_id`) con `etiquetas_de_mapas`, como Mapas y la conversion de clutch por sitio, y no por `map_name` (hallazgo MEDIUM de la revision ciega: con un rework de Club House las dos versiones se juntaban; un renombre en Datos partia la fila). Suma una consulta: `assertNumQueries(4)`, fija con 1 y con 3 rondas.

Tests vistos en rojo antes del codigo: los 17 iniciales de `test_ventaja_tirada.py` (`AttributeError`, sin `ventaja_maxima` ni `thrown_advantage`). Criterios -> tests: 1 `test_cuenta_ventaja_ganada_tirada_y_sin_ventaja`, `test_una_ronda_sin_ganador_no_cuenta`, `test_un_abandono_rival_cuenta_como_baja`, `test_un_5v4_de_arranque_*`; 2 `test_separa_ventaja_de_uno_y_de_dos`, `test_un_5v3_da_ventaja_de_dos`; 3 `test_la_lista_va_de_la_mas_reciente_y_tiene_tope`, `test_en_la_misma_partida_va_primero_la_ronda_posterior`, vitest `enlaceDeRonda` (cruzado con `indiceDeAncla`); 4 `test_el_filtro_de_lado_aplica_sobre_tu_fila`, `test_la_api_responde_con_los_filtros`; 5 e2e `Duelos muestra la ventaja numerica tirada` (total y grupo "Con uno más" contra la API, primer enlace de "Últimas tiradas" abre la partida con esa pestaña `active`; con `seed_demo` la API trae rondas, respuesta de 2912 bytes en el log), mas `test_por_mapa`, `test_por_mapa_separa_las_versiones_del_mismo_nombre`, `test_por_lado`; 6 `metricas.md`. Mutaciones: `ventaja >= 1` en el grupo cae `test_separa_ventaja_de_uno_y_de_dos`; sacar el `if muerto not in vivos` sobrevivia y se agrego `test_un_5v4_de_arranque_con_una_baja_sin_resolver_no_es_ventaja`, que ahora lo mata.

Revision ciega (`omc-code-reviewer`, `revision.md`, eje de estandares): aprobar, 1 MEDIUM y 1 LOW (el test por mapa que no lo veia); los dos arreglados (desvio de arriba y test nuevo). Nota sin peso del revisor: filas de `RoundPlayer` con un `team_index` ajeno contarian como rivales, igual que en `estado_al_morir`; no lo introduce esta ficha.

verificar.sh: VERDE 4c313f073 (1303 backend, 417 vitest, 113 e2e).

Skills: no aplica.
Skills del repo: statistical-analysis (denominador = rondas con ventaja y con ganador, `n` en la columna "Rondas con ventaja", cuentas por ronda sin promedio de promedios, muestra 30 avisada), testing-strategy (Django para la regla y el agregado, vitest para etiquetas y enlace, e2e en la app real, mutaciones), ux-copy ("Con uno más", "Últimas tiradas", nota sin rondas, con tildes), modern-web-guidance no leida (sin CSS nuevo: `DataTable` y `Panel` existentes), sql-queries no aplica (sigue el patron vecino de `death_state`, con `assertNumQueries`).
OMC: plan=— · revisión=2 hallazgos (2 arreglados) · verificación=—

## Revision 2026-11-13 sobre e1e70af

(revisor 20261113T2156Z-cQ8Kk3s) La rama ya contenia `origin/dev@72df8f9`. verificar.sh: VERDE e1e70af3c (1303 backend, 417 vitest, 113 e2e).

**Eje de estandares** (`omc-code-reviewer` ciego, prompt de `revision.md`): corregir, 1 HIGH, 1 MEDIUM, 1 LOW.
- [bug] **HIGH confirmado** `backend/replays/analytics/metrics.py:228-230` (`ventaja_maxima`): la diferencia se mide tambien tras la salida que deja a un equipo en 0, asi que toda ronda ganada por eliminacion entra como "ronda con ventaja" (no tirada) con la ventaja de los vivos finales. Repro (`manage.py shell`, `team_of` 5v5 a0..a4 / r0..r4, equipo 0): cinco `Kill a0 -> r0..r4` -> **5** (cae en "Con dos o más"); clutch 1v1 ganado (r0 mata a1..a4, a0 mata r1..r4 y al final r0) -> **1** (cuenta como "Con uno más" una ronda en la que nunca tuviste mas vivos). Infla el denominador y baja el % tiradas, sobre todo en `two_plus`; en `seed_demo` hoy da 64 con ventaja, 25 tiradas (39,1 %; one 43/18, two_plus 21/7). Ningun test tiene una ronda ganada por eliminacion. Arreglo: no tomar la diferencia cuando un equipo queda sin vivos (cortar el recorrido ahi) y tests: eliminacion 5-0 ganada sin la ventaja de cierre (5v1 -> 4 si paso por ahi, o lo que corresponda antes de la ultima baja) y clutch 1v1 ganado -> `None` o <= 0.
- [regla] MEDIUM propuesto -> **LOW confirmado** `aggregates.py` (`thrown_advantage`): se calcula al consultar recorriendo el feed, contra "las metricas se calculan al importar" de `CLAUDE.md`. Tiene precedente (`death_state`, `nemesis`) y el docstring lo justifica; consultas constantes (test de queries). No bloquea; si se quiere, columna en `RoundPlayer` en ficha aparte.
- [test] LOW `backend/tests/test_ventaja_tirada.py` (`test_la_lista_va_de_la_mas_reciente_y_tiene_tope`): una ronda por partida, el desempate por numero no lo prueba ese test (si lo prueba `test_en_la_misma_partida_va_primero_la_ronda_posterior`). Sin arreglo obligatorio.

**Eje de intencion** (`omc-code-reviewer` contra Que gana, Criterios y Fuera de alcance): aprobar; los 6 criterios cubiertos, nada fuera de alcance. Hallazgos:
- [bug] **MEDIUM confirmado** `metrics.py:217-230`: cada baja actualiza la maxima sola aunque la siguiente tenga el mismo reloj; un trade en el mismo segundo crea un +1 que no existio. Repro: `[Kill a0->r0, Kill r1->a0]` -> **1**. Arreglo: agrupar por `clock` (sumarlo al `.values()` del feed en `thrown_advantage`) y medir al cerrar cada grupo, con test del trade; o documentarlo en `metricas.md` si se decide mantener.
- [intencion] LOW: ronda que arranca 5v4: primera baja rival -> +2, primera baja tuya -> 0 (la ventaja de arranque cuenta a medias). Elegir la regla, escribirla en `metricas.md` y fijarla con test.
- [test] LOW `frontend/e2e/humo.spec.js` (bloque de la ventaja tirada): afirma total, "Con uno más" y el primer enlace; no `two_plus` ni una fila de lado y de mapa. Sumarlas con los numeros de la API.
- [intencion] LOW: `recent[].round` sale en base 1 y otros endpoints (`round_number` de records) en base 0; el frontend lo compensa. Unificar a base 0 si se toca.

Sin eje de seguridad: endpoint GET nuevo, sin red, POST, rutas, parser ni dependencias.

**Ficha.** Criterios 1-6 con test (detalle del eje de intencion: `test_ventaja_tirada.py`, `ventajaTirada.test.js`, e2e en `humo.spec.js`, panel en Duelos, fila y muestra minima en `metricas.md`), pero el criterio 2 ("ventaja de uno y de dos o mas, la maxima de la ronda") da un numero equivocado en toda ronda ganada por eliminacion (HIGH). Identificadores sin tildes, UI con tildes, sin `print` ni `console.log`.

Veredicto: corregir (HIGH de `ventaja_maxima`; el MEDIUM del mismo segundo conviene en la misma pasada).

Skills del repo: ninguna (revision con `revision.md`).
OMC: plan=— · revisión=8 hallazgos (1 HIGH, 1 MEDIUM, 6 LOW; 0 arreglados: los arregla el Dev) · verificación=—

## QA

## Para el humano

- (arquitecto 2026-11-13, no bloquea) Calibrar con la base real el aviso de muestra de 30 rondas con ventaja por fila.

(nada)
