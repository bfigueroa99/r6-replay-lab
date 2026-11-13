# 116. En que estado de vivos mueres

estado: aprobado
candado: -
rama: claude/equipo-dev/116-en-que-estado-de-vivos-mueres
tipo: funcionalidad
epica: impacto
area: fullstack
prioridad: 3
fuente: ALCANCE.md K6
archivos: backend/replays/analytics/metrics.py (estado_al_morir), backend/replays/analytics/aggregates.py (death_state), backend/replays/views.py (death_state), backend/replays/urls.py, backend/tests/test_estado_al_morir.py (nuevo), frontend/src/estadoAlMorir.js (nuevo), frontend/src/estadoAlMorir.test.js (nuevo), frontend/src/components/EstadoAlMorir.jsx (nuevo), frontend/src/pages/Duelos.jsx, frontend/e2e/humo.spec.js, docs/metricas.md
turnos: po 20261112T1603Z-cor3JBP, arquitecto 20261113T1649Z-ccPezGq, dev 20261113T1703Z-c66ztji, revisor 20261113T1651Z-cxTme8t, qa 20261113T1733Z-cudo1Sw

## PR

## Que gana quien usa la app

Tus muertes repartidas por el estado de vivos de la ronda en el instante en
que caes (5v5, 5v4, 4v5, 3v3...) y el winrate de la ronda en cada caso. Dice
si mueres regalando una ventaja o cuando la ronda ya estaba perdida, que el
K/D y las aperturas no separan.

## Criterios de aceptacion

- [ ] Un agregado devuelve, por estado `tuyos vivos v rivales vivos` justo
      antes de tu muerte, `deaths` y `winrate` de esas rondas (sobre las
      que tienen ganador). Test con una ronda armada: caes cuando ya habia
      caido un rival y ninguno de los tuyos cuenta en `5v4`.
- [ ] Un `PlayerLeave` cuenta como baja para el estado (como
      `pydissect/stats.py`), un teamkill tambien resta un vivo de tu equipo,
      y una muerte tuya sin evento en el feed no entra. Test de los tres.
- [ ] Ventaja, paridad y desventaja agregadas (`ahead`, `even`, `behind`)
      ademas del estado exacto, con su winrate. Test.
- [ ] Los filtros globales aplican (lado, mapa, operador, tipo, fechas,
      sesion). Test de lado.
- [ ] Se ve en la UI con la muestra minima de `metricas.md` como aviso; sin
      muertes, un texto y no un error; e2e de humo por esa pagina con la
      consola limpia. Fila nueva en `docs/metricas.md` ("Estado al morir").

## Fuera de alcance

- El reverso, tus bajas por estado (K8): otro tramo de la epica.
- Probabilidad de ganar por estado o impacto por baja (K1, K2).
- Partidas con menos de 5 por lado: el estado se cuenta con los jugadores
  que hay, sin normalizar a 5v5.

## Diseno

Arquitecto 20261113T1649Z-ccPezGq, sobre `origin/dev@16d3986`. Una sola forma
razonable: sin arena ni consenso (sin migracion, sin `recompute`, sin parser).

**Decision: se calcula al consultar, sobre `Event`, con la funcion pura en
`metrics.py`.** La alternativa (dos columnas en `RoundPlayer` llenadas al
importar) pide migracion `0007` + `recompute`, y la 79 (que espera al humano
con su `0006`) la dejaria frenada. `first_teammate_death`, `site_after_loss` y
`nemesis` ya leen el feed al consultar. Para que pasar a columna despues sea
mecanico, el algoritmo vive una sola vez en `metrics.py` (como `_quedar_solo`)
y el agregado solo lo llama. Si el humano prefiere la columna, va en
`## Para el humano`; no frena nada.

### Archivos y por que

1. `backend/replays/analytics/metrics.py`: `estado_al_morir(eventos, team_of)
   -> dict[clave, tuple[int, int]]`, junto a `_quedar_solo` y con el mismo
   recorrido. `vivos = set(team_of)`; por evento: `KILL` saca a `target`,
   `DEATH` y `PLAYER_LEAVE` sacan a `actor`; si el que cae no esta en `vivos`,
   se salta. **Antes** de sacarlo, si el evento es una muerte (`KILL` o
   `DEATH`, no `PLAYER_LEAVE`) y la victima no tiene estado todavia, se anota
   `(vivos de su equipo, vivos rivales)` contando a la victima. Asi sale la
   primera muerte del feed (la misma eleccion de `analyse_round`), un teamkill
   o un abandono previos ya restaron, y quien se fue antes de "morir" no
   aparece. Claves genericas (nick o `player_id`): el agregado usa ids.
2. `backend/replays/analytics/aggregates.py`: `death_state(**filters) -> dict`,
   cerca de `first_teammate_death` (reusa su patron de `Exists` correlacionado
   por el tope de parametros de SQLite; nada de `round_id__in`).
   - `mias = base_queryset(**filters).filter(died=True)`; filas
     `round_id, player_id, round__my_team_won`.
   - Equipos: `RoundPlayer.objects.filter(Exists(mias.filter(round_id=OuterRef("round_id"))))
     .values("round_id", "player_id", "team_index")`.
   - Feed: `Event.objects.filter(Exists(...), kind__in=(Event.KILL, Event.DEATH, PLAYER_LEAVE))
     .order_by("round_id", "order").values("round_id", "kind", "actor_id", "target_id")`,
     mapeado a `{"kind", "actor", "target"}` para la funcion de `metrics.py`.
   - Por cada fila mia: si `estado_al_morir(...)` no trae su `player_id`
     (muerte sin evento en el feed, o se fue antes) suma a `sin_feed` y no
     entra. Si trae `(a, r)`: estado `f"{a}v{r}"`, grupo `ahead` si `a > r`,
     `even` si `a == r`, `behind` si `a < r`; `_sumar_caso` con
     `round__my_team_won` (sin ganador cuenta en `rounds`, no en `decided`).
   - Salida: `{"deaths": n, "sin_feed": m, "states": [...], "groups": [...]}`.
     Cada fila de `states`: `state, allies, enemies, group, rounds, decided,
     won, winrate` (`_pct(won, decided)`), solo los estados con muertes,
     ordenados por `allies` desc y `enemies` asc (5v5, 5v4 ... 4v5 ...).
     `groups` siempre trae las tres filas en orden `ahead, even, behind`,
     con 0 y `winrate: None` si no hubo. `deaths` es la suma de `rounds`.
   - Sin normalizar a 5v5: el estado se cuenta con los jugadores de la ronda.
3. `backend/replays/views.py` + `urls.py`: `death_state` con `@require_GET`,
   `_ok(agg.death_state(**_filters(request)))`, en
   `path("duels/death-state/", ...)`, `name="death-state"`. Endpoint propio y
   no dentro de `views.duels`: la 114 (disenada) toca esa vista y asi no se
   pisan. `PLAYER_LEAVE` se importa de `metrics.py`.
4. `frontend/src/estadoAlMorir.js` (logica pura, con vitest):
   `ETIQUETAS_GRUPO = {ahead: 'Con ventaja', even: 'En paridad', behind: 'En
   desventaja'}`, `filasDeGrupos(data)` (agrega `label`), y `notaSinFeed(n)`
   ("N muertes sin evento en el feed no entran." / `null` con 0). El aviso de
   muestra usa `filasConPocaMuestra` de `muestra.js` con `MUESTRA_CORTE`
   (30, sobre `rounds`): no se oculta, se avisa.
5. `frontend/src/components/EstadoAlMorir.jsx`: panel con su propio
   `useApi('/duels/death-state/', filters)`, `Panel` titulo "Estado al
   morir", subtitulo "Cuántos quedaban vivos de cada lado justo antes de tu
   muerte, y cómo terminó esa ronda". Dos `DataTable`: grupos (Situación,
   Muertes, Winrate de la ronda) y estados (Estado como "5v4", Muertes,
   Winrate), con `csvName` `estado-al-morir` y `estado-al-morir-grupos`.
   Sin muertes con estado: texto "No hay muertes tuyas con evento en el
   feed con estos filtros." (no error). Componente aparte para que
   `Duelos.jsx` gane solo un import y una linea.
6. `frontend/src/pages/Duelos.jsx`: `<EstadoAlMorir filters={filters} />` al
   final, despues de "Stacks rivales que se repiten" (la 114 agrega lo suyo
   cerca de "Por operador rival").
7. `frontend/e2e/humo.spec.js`: un test, `/duelos` muestra el panel "Estado
   al morir" con al menos una fila y la consola limpia (el humo ya vigila la
   consola). El Dev fija ahi un numero del `seed_demo` (las muertes de
   `deaths`) leido de la API, no inventado.
8. `docs/metricas.md`: fila "Estado al morir" (texto abajo) y fila en
   `## Muestra minima` ("Estado al morir | 30 muertes por fila: no se oculta,
   se avisa").

### Tests (`backend/tests/test_estado_al_morir.py`, con `factories.make_event`)

- `test_caes_tras_una_baja_rival_cuenta_en_5v4`: muere un rival, despues vos;
  ninguno de los tuyos cayo: estado `5v4`, grupo `ahead`.
- `test_un_abandono_resta_un_vivo_del_estado`: un compañero `PlayerLeave`,
  despues caes: `4v5`.
- `test_un_teamkill_resta_un_vivo_de_tu_equipo`: un compañero mata a otro
  compañero, despues caes: `4v5`.
- `test_una_muerte_sin_evento_no_entra`: `died=True` sin evento: `deaths` 0,
  `sin_feed` 1.
- `test_solo_cuenta_la_primera_muerte_del_feed`: un `Kill` sobre vos y un
  `Death` tuyo despues: una sola muerte, con el estado del primero.
- `test_grupos_ventaja_paridad_y_desventaja_con_winrate`: tres rondas, una por
  grupo, una ganada, una perdida y una sin ganador: `decided` y `winrate`
  correctos, y la sin ganador en `rounds`.
- `test_filtro_de_lado_aplica`: una muerte en ataque y otra en defensa;
  `side=Attack` deja una.
- `test_endpoint_sin_muertes_devuelve_grupos_vacios`: base vacia, 200 y tres
  grupos en 0.
- `metrics.estado_al_morir` directo (sin base): `test_estado_al_morir_cuenta_a_la_victima`
  (5v5 en la primera baja de la ronda).
- vitest `estadoAlMorir.test.js`: etiquetas de grupo, `notaSinFeed(0)` es
  `null`, aviso de muestra con 29 y sin aviso con 30.

### Orden

metrics.py + su test -> aggregates + tests de base -> vista/url + test del
endpoint -> `estadoAlMorir.js` + vitest -> componente y Duelos -> humo ->
`metricas.md` -> `verificar.sh`.

### Que puede romperse

- Rendimiento: carga el feed de las rondas en que moriste; es lo que ya hace
  `nemesis`. Sin `round_id__in` (tope de SQLite).
- Conflictos de texto con 113, 115, 114 y 111 en `aggregates.py`,
  `views.py`, `urls.py`, `humo.spec.js` y `metricas.md` (todos agregan al
  final o en su lugar): P3 si aparecen. No toca migraciones.
- Eventos con `actor_id`/`target_id` en `None` (nick sin resolver): no estan
  en `vivos` y se saltan; no rompen el conteo de los demas.

### Verificacion manual

`runserver` con `seed_demo`, `curl -s localhost:8000/api/duels/death-state/`
y `?side=Defense`; abrir `/duelos` y ver el panel al final; con un filtro sin
rondas, la pagina sigue en su vista vacia de siempre.

### Fila de `docs/metricas.md` (Duelos)

| **Estado al morir** | Panel de Duelos (`/api/duels/death-state/`). Por cada ronda en que moriste, los vivos de tu equipo (contandote) y los rivales justo antes del primer evento del feed que te mata (`Kill` sobre vos o `Death` tuyo, la misma eleccion que `died`). Un `PlayerLeave` y un teamkill anteriores ya restaron su vivo. Una muerte sin evento en el feed, o despues de haberte ido, no entra (se informa cuantas). *Con ventaja* si tu equipo tenia mas vivos, *en paridad* si igual, *en desventaja* si menos. Winrate de esas rondas sobre las que tienen ganador. Sin normalizar a 5v5: partidas con menos jugadores dan estados como 4v4. Todos los filtros globales aplican. Muestra minima 30 muertes por fila: no se oculta, se avisa. |

`Skills del repo:` statistical-analysis (denominador = rondas con ganador, `n`
visible por fila, sin promedio de promedios: cada muerte es una ronda),
testing-strategy (Django para el algoritmo y el agregado, vitest para
etiquetas y avisos, humo e2e para la pagina). dataviz no aplica: tablas, sin
grafico.
Skills: ninguna de afuera (sin dominio nuevo: ni tabla, ni migracion, ni flujo e2e nuevo).
OMC: plan=— · revisión=— · verificación=—

## Implementacion

Dev 20261113T1703Z-c66ztji, sobre `origin/dev@0293ade`. Diseno completo, sin desvios de fondo.

- `metrics.estado_al_morir(eventos, team_of)`: junto a `_quedar_solo`, mismo recorrido. Anota
  `(aliados, rivales)` contando a la victima en su primera muerte (`Kill`/`Death`); `PlayerLeave`
  resta sin anotar; un jugador fuera de `team_of` (id nulo) se salta.
- `aggregates.death_state(**filters)`: tres consultas fijas (mis muertes, equipos y feed con
  `Exists` correlacionado, sin `round_id__in`), fijadas con `assertNumQueries(3)`. Salida
  `deaths, sin_feed, states, groups` como el diseno; `groups` siempre trae las tres filas.
- `GET /api/duels/death-state/` (`views.death_state`, `name="death-state"`).
- `frontend/src/estadoAlMorir.js` (+ vitest): etiquetas, `filasDeGrupos`, `filasDeEstados`,
  `notaSinFeed`, `avisoPocaMuestra` (corte `MUESTRA_CORTE` = 30 sobre `rounds`), `hayMuertes`.
- `components/EstadoAlMorir.jsx`: panel con su `useApi`, dos `DataTable` (grupos y estado exacto)
  con CSV, aviso de muestra y nota de muertes no ubicadas; sin muertes, texto. `Duelos.jsx` suma
  import y una linea, despues de "Stacks rivales que se repiten".
- e2e `Duelos muestra el estado de vivos al morir`: con `seed_demo`, 173 muertes, 87 con ventaja
  (4v3) y 86 en paridad (3v3), leidos de la API (`seed_demo` usa 4 contra 3 jugadores).
- `docs/metricas.md`: fila "Estado al morir" en Duelos y en `## Muestra minima`.

Desvios menores:
- Las filas llevan `orden` (indice de la API) e `initialSort` por el: sin eso `DataTable` ordenaba
  por la etiqueta.
- La nota de `sin_feed` dice "no se pueden ubicar en el feed (sin evento o después de irte)" y no
  "sin evento": `sin_feed` tambien cuenta la muerte posterior a un `PlayerLeave` propio (hallazgo
  del revisor ciego).
- Tests extra: `test_si_te_fuiste_antes_de_morir_no_entra`, `test_si_no_moriste_la_ronda_no_entra`,
  `test_estados_ordenados_por_tuyos_vivos_y_despues_rivales`,
  `test_partida_con_menos_jugadores_no_se_normaliza`, `test_endpoint_aplica_los_filtros`,
  `test_consultas_acotadas` y tres puros mas de `estado_al_morir`.

Criterios -> tests: 5v4 (`test_caes_tras_una_baja_rival_cuenta_en_5v4`); abandono, teamkill y sin
evento (`test_un_abandono_resta_un_vivo_del_estado`, `test_un_teamkill_resta_un_vivo_de_tu_equipo`,
`test_una_muerte_sin_evento_no_entra`); grupos (`test_grupos_ventaja_paridad_y_desventaja_con_winrate`);
filtros (`test_filtro_de_lado_aplica`); UI (vitest `estadoAlMorir.test.js`, e2e de humo, consola limpia).

Verificacion: `verificar.sh` VERDE c8d3560 (1218 tests backend, 356 vitest, 99 e2e).

Skills del repo: statistical-analysis (denominador = rondas con ganador; `n` visible por fila en
Muertes; sin promedio de promedios), testing-strategy (algoritmo puro en SimpleTestCase, agregado
y endpoint en TestCase, etiquetas en vitest, humo e2e). modern-web-guidance y ux-copy no leidas
por reloj de corrida simultanea: el JSX copia los patrones vecinos (`Panel`, `DataTable`, `note`) y
los textos siguen el voseo y las tildes de la UI.
Skills: ninguna de afuera.
OMC: plan=— · revisión=2 hallazgos LOW (2 arreglados) · verificación=—

## Revision 2026-11-13 sobre 6fc0a6b

(revisor 20261113T1651Z-cxTme8t) La rama trae `origin/dev` (a6a9fe8, con la
111 y la 113) sin conflictos. verificar.sh: VERDE 6fc0a6b42 (1218 backend,
367 vitest, 100 e2e). Revision a ciegas en dos ejes (`omc-code-reviewer`
estandares e intencion; sin POST, red, parser ni rutas: sin eje de
seguridad). Los dos: aprobar, 0 CRITICAL/HIGH. Confirmados por el lider:

- [regla] MEDIUM `backend/replays/analytics/aggregates.py` (`death_state`):
  la metrica se calcula al consultar sobre el feed y no al importar, como pide
  `CLAUDE.md`. No frena: es la decision explicita del Diseno (para no esperar
  la migracion de la 79), con precedente en `first_teammate_death` y
  `nemesis`, la funcion pura ya vive en `metrics.py` y la pregunta esta en
  `## Para el humano`. `test_consultas_acotadas` fija 3 queries.
- [test] LOW `backend/tests/test_estado_al_morir.py`: ningun test miraba
  `won`/`decided`/`winrate` de las filas por estado exacto (`states`).
  Repro: cambiar `_sumar_caso(caso, ...)` por `caso["rounds"] += 1` deja los
  18 tests en verde. **Agregado por el Revisor (pasa):**
  `test_cada_estado_exacto_trae_su_winrate` (5v4 100 %, 5v5 0 %, 4v5 sin
  ganador `None`); con la mutacion cae.
- [estilo] LOW `docs/metricas.md` fila **Estado al morir**: "la misma
  eleccion que `died`" es impreciso (`died` tambien sale de `stats` sin
  evento); el numero no cambia porque esas van a `sin_feed`. Sugerido: "la
  primera muerte tuya en el feed".
- [bug] LOW `frontend/src/pages/Duelos.jsx:49`: con la vista `sin-duelos`
  (cero duelos contra rivales) la pagina corta antes del panel, aunque haya
  muertes por teamkill o `Death` que el panel contaria. Caso raro; sugerido
  renderizar el panel tambien en esa vista.
- [estilo] LOW `frontend/src/components/EstadoAlMorir.jsx:34`: "...con estos
  filtros." sale aunque no haya filtros; sugerido variar con `hayFiltros`
  como `textosSinDuelos`.
- [formato] LOW: las filas traen el conteo como `rounds` y no `deaths` (el
  criterio dice `deaths`); mismo numero (una muerte por ronda), nombre de
  `_caso_vacio`. Sin cambio.
- Sin confirmar (confianza baja, sin `.rec` real): si el parser deja una
  fila de `RoundPlayer` para quien se fue en una ronda anterior, contaria
  como vivo; `clutch_vs` comparte la suposicion.

Criterios: estado exacto con muertes y winrate (`test_cada_estado_exacto_trae_su_winrate`
y los de estado), `PlayerLeave`/teamkill/sin evento (tests de los tres),
ahead/even/behind con winrate, filtro de lado (agregado y endpoint), UI con
aviso de muestra y texto sin muertes, e2e con consola limpia (numeros del
e2e recalculados contra `seed_demo`: 173 muertes, 87 en 4v3, 86 en 3v3),
fila en `metricas.md`: cubiertos. Sin dependencias, GET, identificadores sin
tildes y UI con tildes, sin `print` ni `console.log`.

Veredicto: aprobar -> `revisado`.

Skills: no aplica.
OMC: plan=— · revisión=7 hallazgos (1 arreglado, test; 0 CRITICAL/HIGH) · verificación=—

## QA 2026-11-13 sobre 16066a1

(qa 20261113T1733Z-cudo1Sw) Rama al dia con `origin/dev` (a6a9fe8), sin
migracion, sin parser, sin `recompute`. Scripts en el scratchpad de la sesion
(`sembrar.py`, `a11y.cjs`, `teclado.cjs`, `vacia.cjs`); se repiten asi:

- `verificar.sh` -> `VERDE 16066a14c en 185s: 1219 tests backend, 367 vitest, 100 e2e. Todo en verde.`
- Base vacia (`SQLITE_PATH=<tmp>/vacia.sqlite3 manage.py migrate && runserver 8761`):
  `curl -s localhost:8761/api/duels/death-state/` -> 200, `deaths 0`, tres grupos en 0 con `winrate: null`.
  `/duelos` muestra la bienvenida de siempre, consola limpia.
- Base sembrada con `factories.py` (Club House, 5 contra 5, siete rondas armadas):
  R0 cae un rival y despues yo; R1 `PlayerLeave` de un aliado + teamkill + yo;
  R2 `Kill` sobre mi y despues `Death` mio; R3 `died` sin evento; R4 `PlayerLeave`
  mio y el feed me mata despues; R5 no muero; R6 `Death` mio con dos rivales
  caidos, ronda sin ganador. **Recalculado a mano:** 4 muertes (5v4 ganada,
  3v5 perdida, 5v5 perdida, 5v3 sin ganador), `sin_feed` 2; ahead 2 rondas /
  1 decidida / 1 ganada = 100 %, even 1/1/0 = 0 %, behind 1/1/0 = 0 %; orden
  5v3, 5v4, 5v5, 3v5. `curl .../api/duels/death-state/` devolvio exactamente eso.
- Bordes, todos 200: `side=Attack` 3 (5v3, 5v4, 3v5); `side=Defense` 1 (5v5) +
  `sin_feed` 2; `side=foo` 0; `until=foo` y `page=-1` ignorados; `map=` vacio
  ignorado; `map=border` (ronda sin muerte mia) 0; `map=oregon` (muerte sin
  evento) 0 + `sin_feed` 1; `operator=Nadie` 0; `days=99999999999` sin 500;
  `session=abc` 0. POST -> 403 (CSRF), como el resto de los GET. Vecino
  `/api/duels/` sin cambios (200).
- Chunk inicial de `vite build`: `index` 199.91 kB en `origin/dev` -> 200.10 kB
  (+0.1 %). `Duelos` (lazy) 7.92 -> 10.09 kB.
- accessibility-review en Chromium sobre `/duelos` sembrada: `h2` "Estado al
  morir", dos `table` con `columnheader` (Situación/Muertes/Winrate de la
  ronda; Estado/...), filas iguales a la API ("5v3 1 —"). Contraste medido
  5.71:1 (titulo, hint y cabeceras, `--muted`) a 14.17:1 (celdas): todo >= 4.5.
  Teclado: los dos "Descargar CSV" y las cabeceras ordenables se alcanzan con
  Tab con foco visible (outline 2px); Enter ordena y pone `aria-sort`; Enter en
  CSV baja `estado-al-morir-<fecha>.csv` con BOM y `;`. Consola limpia.
  0 Critical, 0 Major. Con `map=border` el panel muestra "No hay muertes tuyas
  con evento en el feed con estos filtros." (texto, no error).
- design-critique (panel nuevo, no frena): jerarquia y patrones iguales a los
  paneles vecinos (`Panel`, `DataTable`, `note`). Lo unico: con `map=oregon`
  (muertes sin evento y 0 duelos) la pagina cae en su vista sin-duelos y no
  muestra el panel; es el LOW que ya anoto el Revisor, fuera de los criterios.
- validate-data sobre la fila "Estado al morir" de `metricas.md`: winrate sobre
  `decided` (`_pct` devuelve `None` con 0: sin division por cero), `n` visible
  en Muertes, grupos sumados de conteos (sin promedio de promedios), redondeo a
  un decimal. Valores recalculados: arriba (ahead 100 %, 5v4 100 %).
- Mutacion (`manage.py test tests.test_estado_al_morir`, revertida cada una):
  `PlayerLeave` no resta -> caen 3; `PlayerLeave` anota estado -> caen 2;
  paridad como ventaja (`>=`) -> cae `test_grupos_ventaja_paridad_y_desventaja_con_winrate`;
  no contar a la victima -> caen 12.

Criterios: los cinco verificados (estado exacto con winrate, abandono /
teamkill / sin evento, grupos, filtros, UI con aviso, texto vacio, e2e y
`metricas.md`).

Veredicto: `aprobado`.

Skills del repo: accessibility-review (0 Critical, 0 Major; contraste 5.71-14.17),
design-critique (0 nuevos; repite el LOW del Revisor), validate-data (sin
hallazgos; 2 valores recalculados a mano iguales a la API).
Skills: ninguna de afuera.
OMC: plan=— · revisión=— · verificación=PASS (omc-verifier, 5/5 criterios)

## Para el humano

- 2026-11-13 (arquitecto): el estado se calcula al consultar, sobre el feed, y no
  en columnas de `RoundPlayer` al importar (lo que pide `CLAUDE.md` para las
  metricas) para no frenarla detras de la migracion de la 79. Si preferis la
  columna, es mecanico: la funcion ya vive en `metrics.py`. No frena nada.
