# 102. Tu pool de operadores por lado

estado: disenado
candado: -
rama: -
tipo: funcionalidad
epica: operadores
area: fullstack
prioridad: 3
fuente: ALCANCE.md O7
archivos: backend/replays/analytics/aggregates.py (operator_pool, POOL_*), backend/replays/views.py (operators_pool), backend/replays/urls.py, backend/tests/test_pool_operadores.py, frontend/src/poolOperadores.js, frontend/src/poolOperadores.test.js, frontend/src/pages/Operators.jsx, frontend/e2e/humo.spec.js, docs/metricas.md
turnos: po 20261106T0530Z-ciXX3AM, arquitecto 20261112T1128Z-cKKCvKD

## PR

## Que gana quien usa la app

En Operadores, un panel "Tu pool" dice cuantos operadores distintos jugaste
por lado en tus ultimas 20 partidas y en todo el historial, y cuales del
catalogo nunca jugaste o no jugas hace 30 dias. Responde si dependes de dos
operadores por lado y que practicar para cuando te los banean o te los
quitan, cosa que la tabla por operador (ordenada por rondas) no dice.

## Criterios de aceptacion

- [ ] La API de Operadores (o una clave nueva en `/api/operators/`) devuelve
      por lado (`Attack`, `Defense`): `distinct_recent` (operadores
      distintos en tus ultimas 20 partidas), `distinct_all`, `never` (lista
      del catalogo `_catalogo_operadores` de ese lado sin ninguna ronda tuya)
      y `stale` (jugados alguna vez pero no en los ultimos 30 dias, con la
      fecha de la ultima vez). Test con historial armado: un operador jugado
      hace 40 dias cae en `stale`, uno nunca jugado en `never`.
- [ ] Los filtros de mapa y tipo de partida aplican; el de lado decide que
      bloque se muestra; el de operador se ignora para este panel (no tiene
      sentido "tu pool de Ash") y el test lo afirma.
- [ ] Las filas `Unknown(...)` y los operadores con `operator=""` no entran
      ni al conteo ni a `never`.
- [ ] El panel se ve en Operadores con los dos lados; sin partidas, un texto
      vacio y no un error. El e2e de humo pasa por Operadores con la consola
      limpia.
- [ ] Fila nueva en `docs/metricas.md` ("Pool de operadores") con las
      ventanas de 20 partidas y 30 dias.

## Fuera de alcance

- Curva de aprendizaje por operador (E1) y presencia sobre lo jugado (O5).
- Recomendar que operador practicar: solo se lista.
- Hacer configurables las ventanas de 20 partidas y 30 dias (constantes en
  `aggregates.py`, como las demas muestras minimas).

## Diseno

(arquitecto 20261112T1128Z-cKKCvKD) Filtros duros: pasa. Usa `RoundPlayer.operator`, `side`,
`Match.played_at` y el catalogo que ya existe; sin red, sin dependencias, sin
POST, sin migracion. Una sola forma razonable y chica (~300 lineas): sin
arena ni plan por consenso.

**Forma.** Endpoint propio `GET /api/operators/pool/`, pedido aparte desde
Operadores igual que `PorSitio`: un error del panel no tumba la pagina y la
vista vacia la sigue decidiendo `/operators/`. No se toca la respuesta de
`/api/operators/`.

**Backend, `backend/replays/analytics/aggregates.py`** (junto a `by_operator`):

- Constantes `POOL_PARTIDAS_RECIENTES = 20` y `POOL_DIAS_SIN_JUGAR = 30`, con
  comentario de por que (ventana de "lo que jugas hoy" y umbral de "lo
  dejaste").
- `operator_pool(catalogo: list[dict], **filters) -> dict`. El catalogo entra
  como argumento porque `_catalogo_operadores` vive en `views.py` y
  `aggregates.py` no importa vistas.
  1. `filtros = {k: v for k, v in filters.items() if k not in ("side", "operator")}`.
     `operator` se ignora (no hay "tu pool de Ash"); `side` tambien, porque
     filtrar el queryset por lado dejaria el otro lado entero en `never`: el
     backend devuelve siempre los dos y el frontend muestra el bloque del
     lado filtrado.
  2. `qs = base_queryset(**filtros).exclude(operator="").exclude(operator__startswith=unknowns.UNKNOWN_PREFIX).exclude(side="")`
     (`from .. import unknowns`, como `views.py`; `unknowns.py` no importa
     `analytics`, asi que no hay ciclo).
     Por `base_queryset` entran solas las exclusiones de la 79 cuando se
     mergee: no se arma ningun queryset desde `RoundPlayer.objects`.
  3. Ventana reciente: ids de las ultimas `POOL_PARTIDAS_RECIENTES` partidas
     de `qs` (`values("round__match_id", "round__match__played_at").distinct()
     .order_by("-round__match__played_at", "-round__match_id")`, recortado en
     Python a 20 ids distintos).
  4. Por operador y lado, una sola consulta: `values("operator", "side")
     .annotate(rounds=Count("id"), last=Max("round__match__played_at"),
     recent=Count("id", filter=Q(round__match_id__in=ids)))`.
  5. Fecha de referencia = `played_at` de tu partida mas nueva en `qs`, **no**
     `datetime.now()`: quien deja de jugar dos meses no ve todo como "sin
     jugar", y el e2e (seed con fechas fijas de 2026-08) queda
     deterministico. `stale` = jugados con `last < referencia -
     timedelta(days=POOL_DIAS_SIN_JUGAR)`.
  6. Respuesta:
     ```
     {"matches": <partidas en qs>, "recent_matches": <len(ids)>,
      "reference": "<fecha iso de la referencia o null>",
      "recent_window": 20, "stale_days": 30,
      "sides": {"Attack": {...}, "Defense": {...}}}
     ```
     cada lado: `distinct_recent` (operadores con `recent > 0`),
     `distinct_all`, `never` (nombres del catalogo de ese lado sin ninguna
     fila, orden alfabetico sin mayusculas, como el catalogo) y `stale`
     (lista de `{"operator", "last_played" (fecha iso), "rounds"}`, de la mas
     reciente a la mas vieja). Un operador visto en la base con lado que no
     esta en el catalogo no existe: el catalogo ya suma los vistos.
  7. Sin partidas: `matches: 0`, `reference: null`, contadores en 0, `stale`
     vacio y `never` con todo el catalogo del lado (el frontend no lo muestra:
     ver abajo).

**`backend/replays/views.py`**: `operators_pool` con `@require_GET`,
`_ok(agg.operator_pool(_catalogo_operadores(), **_filters(request)))`, al
lado de `operators_by_site`. **`backend/replays/urls.py`**:
`path("operators/pool/", views.operators_pool, name="operators-pool")` junto
a `operators/sites/`.

**Frontend.**

- `frontend/src/poolOperadores.js` (logica pura): `bloquesDelPool(data, lado)`
  devuelve los bloques a mostrar (`[]` si `!data` o `data.matches === 0`;
  solo el del lado si `lado` es `Attack` o `Defense`; si no, Ataque y
  Defensa en ese orden), cada uno con `titulo` (`Ataque`/`Defensa`),
  `resumen`, `stale` y `never`. `textoResumen(bloque, recentMatches)`:
  "3 operadores distintos en tus últimas 20 partidas · 5 en todo el
  historial", con singular ("1 operador", "tu última partida") y con
  `recent_matches` real cuando hay menos de 20.
- `frontend/src/poolOperadores.test.js` (vitest): sin datos y con
  `matches: 0` da `[]`; con lado filtrado sale un solo bloque; singular y
  plural del resumen; ventana menor a 20 usa el numero real.
- `frontend/src/pages/Operators.jsx`: componente `TuPool({ filters })` con
  `useApi('/operators/pool/', filters)`, mismo patron que `PorSitio`
  (ErrorBox / Loading / nota), entre las tablas por lado y `PorSitio`.
  `<Panel title="Tu pool" hint="Operadores distintos por lado. «Sin jugar»
  cuenta 30 días desde tu última partida con estos filtros, no desde hoy.">`.
  Por bloque: un `<h3>` con el titulo, el resumen, "Sin jugar hace más de 30
  días:" con `Operador (último: <fecha>)` o "ninguno", y "Nunca jugados
  (<n>):" con los nombres en chips (`<span className="chip">`, clases que
  ya existen; nada nuevo en `styles.css`). Sin bloques: `<p className="note">`
  "Sin partidas con estos filtros.".

**Tests backend, `backend/tests/test_pool_operadores.py`** (con `factories`,
como `test_operadores_presencia.py`):

- `test_cuenta_operadores_distintos_por_lado_en_la_ventana_y_en_total`:
  22 partidas; un operador solo en las 2 mas viejas cuenta en `distinct_all`
  y no en `distinct_recent`.
- `test_un_operador_jugado_hace_40_dias_cae_en_stale`, con `last_played` y
  `rounds`; uno jugado hace 10 dias no.
- `test_la_referencia_es_tu_ultima_partida_y_no_hoy`: todo de hace un año,
  jugado la misma semana: `stale` vacio.
- `test_un_operador_del_catalogo_sin_rondas_cae_en_never` (y uno jugado no).
- `test_unknown_y_operador_vacio_no_cuentan` (ni en conteos ni en `never`).
- `test_el_filtro_de_operador_y_el_de_lado_se_ignoran`: respuesta igual con
  y sin `?operator=Ash&side=Attack`.
- `test_el_filtro_de_mapa_aplica`: un operador jugado solo en otro mapa cae
  en `never` con `?map=`.
- `test_sin_partidas_responde_vacio_sin_error`: 200, `matches: 0`.

**e2e, `frontend/e2e/humo.spec.js`**, test `Operadores muestra tu pool por
lado` junto a los de Operadores: seed = 3 operadores por lado
(`OPERADORES` de `seed_demo`), todos en las ultimas 20 partidas y ninguno
viejo. El panel "Tu pool" dice "3 operadores distintos" en Ataque y en
Defensa, "Nunca jugados" de Ataque contiene `Sledge` y no `Thermite`, "Sin
jugar" dice "ninguno"; con `/operadores?side=Attack` no hay `<h3>` Defensa;
consola limpia. Afirmar el numero exacto de "Nunca jugados" no: cambia con
cada operador que se sume a `OPERATOR_SIDES`.

**`docs/metricas.md`**, tabla de `## Cortes`, fila nueva "**Pool de
operadores**" despues de "Operador por sitio": operadores distintos por lado
(sin `Unknown(...)` ni vacios) en tus ultimas 20 partidas
(`POOL_PARTIDAS_RECIENTES`) y en todo lo filtrado; "Sin jugar" = jugado
alguna vez y no en los 30 dias (`POOL_DIAS_SIN_JUGAR`) anteriores a tu
partida mas nueva con los filtros; "Nunca jugados" = catalogo del lado
(tabla del parser mas los vistos en la base) sin rondas tuyas; mapa, tipo,
modo, fechas y sesion aplican, lado y operador no.

**Orden.** aggregates + test backend, vista + url, `poolOperadores.js` +
vitest, `Operators.jsx`, e2e, `metricas.md`, `npm run build`.

**Que puede romperse.** La consulta del paso 4 con `__in` de 20 ids es
barata; no agregar el queryset entero a memoria. Un `played_at` nulo no
existe en el modelo (si existiera, `Max` lo ignora). El catalogo trae
operadores de rivales vistos: correcto, son operadores del juego.

**Archivos ocupados.** La 79 (abierta, espera al humano) toca
`aggregates.py`, `views.py` y `urls.py`, pero en otras funciones; la 102
agrega funciones nuevas y no edita las que la 79 cambia, y entra a las
exclusiones por `base_queryset`. No se frena detras de la 79 (151 h
esperando el merge del humano), como no se frenaron la 98, la 100 ni la 103
con los mismos archivos. Si la 79 entra antes, nada cambia en este diseno.

**Verificacion manual.** `seed_demo`, `/operadores`: panel con los dos
lados; `?side=Defense` solo Defensa; `curl /api/operators/pool/?operator=Ash`
igual que sin el; base vacia: la pagina muestra el EmptyState de siempre.

Skills: no aplica (panel y lista en una pagina existente; el repo ya lo resuelve con `PorSitio`).
OMC: plan=— · revisión=— · verificación=—

## Implementacion

## Revision

## QA

## Para el humano

(nada)
