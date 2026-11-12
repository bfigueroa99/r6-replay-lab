# 107. Sitio que tu equipo repite tras perderlo

estado: en curso 2026-11-12T16:11Z
candado: -
rama: claude/equipo-dev/107-sitio-que-tu-equipo-repite-tras-perderlo
tipo: funcionalidad
epica: posicionamiento
area: fullstack
prioridad: 3
fuente: ALCANCE.md S4 (PO 20261105T1759Z-cCJ5erc)
archivos: backend/replays/analytics/aggregates.py (site_after_loss, REPETIR_SITIO_*), backend/replays/views.py (site_after_loss), backend/replays/urls.py, backend/tests/test_repetir_sitio.py, frontend/src/repetirSitio.js, frontend/src/repetirSitio.test.js, frontend/src/pages/Coach.jsx, frontend/e2e/humo.spec.js, docs/metricas.md
turnos: po 20261112T1127Z-cT8M5Vz, arquitecto 20261112T1204Z-chGLrtC

## PR

## Que gana quien usa la app

Despues de perder una ronda defendiendo un sitio, la app dice cuantas veces
tu equipo vuelve a ese sitio en la siguiente ronda de defensa y cuantas
cambia, con el winrate de cada caso, en total y por mapa. Si el rival ya leyo
el sitio, repetir cuesta: es una decision de la defensa, o sea tuya y de tu
equipo, que ninguna tabla muestra hoy.

## Criterios de aceptacion

- [ ] Un agregado devuelve, para pares de rondas de defensa consecutivas de
      la misma partida (por `Round.number`, saltando las de ataque entre
      medio) donde la primera se perdio: `repeat` y `switch` con
      `rounds` y `winrate` de la segunda ronda, en total y por mapa. Test
      con una partida armada: perder en "2F Kitchen" y volver a "2F Kitchen"
      cuenta `repeat`; ir a "1F Bar" cuenta `switch`.
- [ ] Una ronda con `site=""` corta el par (no cuenta ni como primera ni
      como segunda) y el test lo afirma; los pares no cruzan partidas.
- [ ] Los filtros globales (mapa, tipo de partida, fechas, sesion) aplican;
      el de lado se ignora (solo hay pares de defensa) y el de sitio filtra
      por el sitio de la ronda perdida. Test del filtro de sitio.
- [ ] Se ve en la UI con los dos casos lado a lado y la muestra minima de
      `metricas.md` para winrates; sin pares, un texto vacio y no un error.
      El e2e de humo pasa por esa pagina con la consola limpia.
- [ ] Fila nueva en `docs/metricas.md` ("Repetir el sitio tras perderlo").

## Fuera de alcance

- El lado de ataque (S3, spawn tras perder): otra idea.
- Pares que siguen a una ronda ganada.
- Recomendar que sitio jugar: solo se cuenta.

## Diseno

(arquitecto 20261112T1204Z-chGLrtC) Filtros duros: pasa. Usa `Round.number`,
`my_side`, `site` y `my_team_won`, que el `.rec` entrega (el sitio en
defensa es el de bomba elegido); sin red, sin dependencias, sin POST, sin
migracion. Una forma obvia y chica (~300 lineas): sin arena ni consenso.

**Pagina: Coach**, panel propio despues de `PanelSalidaSpawn` (la epica
`posicionamiento` ya vive ahi: "Dónde quedas fuera de posición" y "Salida
del spawn"). Endpoint propio `GET /api/positioning/site-after-loss/`, pedido
aparte: un error no tumba el Coach.

**Backend, `aggregates.py`**, despues de `positioning`:

- `REPETIR_SITIO_MIN_RONDAS = 8`, la de "Sitio / spawn" de la tabla de
  muestra minima: debajo, el winrate se muestra igual con aviso (como los
  cortes de Tendencias), no se oculta.
- `site_after_loss(**filters) -> dict`:
  1. `sitio = filters.get("site")`; `base = {k: v for k, v in filters.items()
     if k not in ("side", "site", "operator")}`. `side` se ignora (solo hay
     pares de defensa); `site` no filtra el queryset sino la ronda perdida
     (paso 4); `operator` tampoco filtra: el par es del equipo, no de tu
     operador, y filtrarlo cortaria pares a la mitad.
  2. Rondas de defensa: `base_queryset(**base).filter(side="Defense")
     .order_by("round__match_id", "round__number").values("round__match_id",
     "round__number", "round__site", "round__my_team_won", *_MAPA)`
     (`_MAPA` da slug, version y nombre para la fila por mapa).
     Por `base_queryset` entran las exclusiones de la 79 cuando se mergee.
  3. Numeros existentes por partida: `Round.objects.filter(match_id__in=<ids
     de las partidas del paso 2>).values_list("match_id", "number")` en un
     `set`. Un par (a, b) son dos rondas de defensa consecutivas de la misma
     partida; **se corta** si algun numero entre `a.number` y `b.number`
     falta en ese set (ronda sin `.rec`: no se sabe si fue de defensa) o si
     `a` o `b` tiene `site=""`. Las de ataque entre medio no cortan.
  4. Cuenta el par solo si `a.my_team_won is False` (una sin ganador no es
     derrota) y, con `sitio`, si `a.site == sitio`. `repeat` si
     `b.site == a.site`, si no `switch`.
  5. Por caso, en total y por mapa (clave `_MAPA`): `rounds` (pares),
     `decided` (con `b.my_team_won` no nulo), `won` y `winrate =
     _pct(won, decided)` (la segunda sin ganador cuenta en `rounds` y no en
     el winrate, como `operator_by_site`).
  6. Respuesta:
     ```
     {"min_rounds": 8, "pairs": <total de pares>,
      "total": {"repeat": {...}, "switch": {...}},
      "maps": [{"slug", "map_id", "map", "repeat": {...}, "switch": {...}}]}
     ```
     `maps` pasa por `_etiquetar` (etiqueta de version), ordenado por pares
     descendente y despues por `map`. Sin pares: `pairs: 0`, casos en 0 con
     `winrate: None`, `maps: []`.

**`views.py`**: `site_after_loss` con `@require_GET` y
`_ok(agg.site_after_loss(**_filters(request)))`, junto a `positioning`.
**`urls.py`**: `path("positioning/site-after-loss/", views.site_after_loss,
name="site-after-loss")` despues de `positioning/`.

**Frontend.**

- `frontend/src/repetirSitio.js` (logica pura): `casosRepetirSitio(caso,
  minRondas)` devuelve `[{clave: "repeat", titulo: "Repite el sitio"},
  {clave: "switch", titulo: "Cambia de sitio"}]` con `rounds`, `winrate` y
  `poca: rounds < minRondas`; `textoPares(n)` ("1 ronda perdida en defensa
  seguida de otra" / "N rondas ..."); `hayPares(data)` (`!!data?.pairs`).
- `repetirSitio.test.js` (vitest): sin datos y `pairs: 0` -> `hayPares`
  false; `poca` por debajo y en el minimo; singular y plural.
- `Coach.jsx`: `PanelRepetirSitio({ filters })` con
  `useApi('/positioning/site-after-loss/', filters)`, ErrorBox / Loading /
  nota como `PorSitio` de Operadores. `<Panel title="Repetir el sitio tras
  perderlo" hint="Después de perder una ronda defendiendo un sitio, qué hace
  tu equipo en la siguiente ronda de defensa de esa partida y cuánto la
  gana. Con el filtro de sitio, solo las rondas perdidas en ese sitio.">`.
  Dos tarjetas lado a lado (`stat-grid`/`stat` si existen en `ui.jsx` o
  `styles.css`; si no, un `DataTable` de dos filas: nada nuevo en
  `styles.css`) con rondas y winrate (`pct`), y "pocas rondas" en
  `.note` si `poca`. Debajo un `DataTable` por mapa: Mapa, Repite (rondas),
  Winrate repitiendo, Cambia (rondas), Winrate cambiando, `csvName=
  "repetir-sitio-por-mapa"`. Sin pares: `<p className="note">` "Sin rondas
  de defensa perdidas seguidas de otra con estos filtros.".

**Tests backend, `backend/tests/test_repetir_sitio.py`** (con `factories`):

- `test_perder_y_volver_al_mismo_sitio_cuenta_repeat` ("2F Kitchen" ->
  "2F Kitchen") y `test_ir_a_otro_sitio_cuenta_switch` ("1F Bar").
- `test_las_rondas_de_ataque_entre_medio_no_cortan_el_par` (D0 perdida,
  A1, D2).
- `test_una_ronda_sin_sitio_corta_el_par` (ni como primera ni como
  segunda).
- `test_una_ronda_faltante_entre_medio_corta_el_par` (numeros 0 y 2 sin 1).
- `test_los_pares_no_cruzan_partidas`.
- `test_tras_ganar_o_sin_ganador_no_hay_par`.
- `test_winrate_de_la_segunda_ronda_sin_contar_la_sin_ganador`.
- `test_el_filtro_de_sitio_mira_la_ronda_perdida`: con `?site=2F Kitchen`
  cuenta el par Kitchen -> Bar y no el Bar -> Kitchen.
- `test_el_filtro_de_lado_y_el_de_operador_se_ignoran`: respuesta igual con
  `?side=Attack&operator=Ash`.
- `test_el_filtro_de_mapa_aplica` y `test_separa_por_mapa_con_su_version`.
- `test_sin_pares_responde_vacio_sin_error` (200, `pairs: 0`).

**e2e, `humo.spec.js`**, test `el Coach muestra si repites el sitio tras
perderlo` junto a los del Coach. Calculado con `seed_demo` en una base
temporal (toda la defensa del seed se pierde): 58 pares, 56 `repeat` y 2
`switch`, winrate 0 en los dos; por mapa Club House 19/1, Bank 19/1,
Border 18/0. Afirmar: el panel dice 56 en "Repite el sitio" y 2 en "Cambia
de sitio", la fila de Club House tiene 19 y 1, y "pocas rondas" aparece en
"Cambia" (2 < 8); consola limpia. Si el Dev cambia la regla de corte, los
numeros cambian: recalcularlos igual que aca.

**`docs/metricas.md`**, tabla de `## Cortes`, fila "**Repetir el sitio
tras perderlo**" junto a las de posicionamiento: pares de rondas de defensa
consecutivas de la misma partida (por numero, saltando las de ataque;
cortado por una ronda sin `.rec` entre medio o sin sitio) cuya primera se
perdio; *repite* si la segunda es en el mismo sitio, *cambia* si no; winrate
de la segunda sobre las que tienen ganador. Mapa, tipo, modo, fechas y
sesion aplican; lado y operador no; sitio elige la ronda perdida. Muestra
minima 8 (`REPETIR_SITIO_MIN_RONDAS`): debajo se avisa, no se oculta. Y la
fila en `## Muestra minima`.

**Orden.** aggregates + tests backend, vista + url, `repetirSitio.js` +
vitest, `Coach.jsx`, e2e, `metricas.md`, `npm run build`.

**Que puede romperse.** Ordenar por `round__number` y no por el orden por
defecto de `Round` (`match__played_at`, `number`) mezclaria partidas si se
olvida el `match_id`: el test de partidas cruzadas lo cubre. La prorroga
sigue la numeracion de `number` (unica por partida), asi que entra sin caso
aparte. El seed tiene casi solo `repeat`: el e2e no prueba el winrate
distinto de 0, eso lo hacen los tests backend.

**Archivos ocupados.** La 79 (espera al humano) toca `aggregates.py`,
`views.py` y `urls.py` en otras funciones; la 102 (`implementado`) agrega
en `aggregates.py`, `views.py`, `urls.py` y `humo.spec.js` en lugares
distintos (Operadores). Funciones nuevas en zonas distintas: el merge es
trivial y no se frena, como no se frenaron la 98, la 100 ni la 103.

**Verificacion manual.** `seed_demo`, `/coach`: panel con 56 y 2;
`?site=<un sitio de Bank>` solo pares que arrancan ahi; `?side=Attack` igual
que sin el; base vacia: el Coach muestra el EmptyState de siempre.

Skills: no aplica (panel y tabla en una pagina existente; el repo ya lo resuelve con `PorSitio` y `PanelPosicion`).
OMC: plan=— · revisión=— · verificación=—

## Implementacion

## Revision

## QA

## Para el humano

(nada)
