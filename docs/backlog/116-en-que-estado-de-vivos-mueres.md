# 116. En que estado de vivos mueres

estado: implementado
candado: -
rama: claude/equipo-dev/116-en-que-estado-de-vivos-mueres
tipo: funcionalidad
epica: impacto
area: fullstack
prioridad: 3
fuente: ALCANCE.md K6
archivos: backend/replays/analytics/metrics.py (estado_al_morir), backend/replays/analytics/aggregates.py (death_state), backend/replays/views.py (death_state), backend/replays/urls.py, backend/tests/test_estado_al_morir.py (nuevo), frontend/src/estadoAlMorir.js (nuevo), frontend/src/estadoAlMorir.test.js (nuevo), frontend/src/components/EstadoAlMorir.jsx (nuevo), frontend/src/pages/Duelos.jsx, frontend/e2e/humo.spec.js, docs/metricas.md
turnos: po 20261112T1603Z-cor3JBP, arquitecto 20261113T1649Z-ccPezGq, dev 20261113T1703Z-c66ztji

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

## Revision

## QA

## Para el humano

- 2026-11-13 (arquitecto): el estado se calcula al consultar, sobre el feed, y no
  en columnas de `RoundPlayer` al importar (lo que pide `CLAUDE.md` para las
  metricas) para no frenarla detras de la migracion de la 79. Si preferis la
  columna, es mecanico: la funcion ya vive en `metrics.py`. No frena nada.
