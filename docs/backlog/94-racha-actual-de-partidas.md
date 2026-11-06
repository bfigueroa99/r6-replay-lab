# 94. Racha actual de partidas

estado: en curso 2026-11-06
candado: -
rama: claude/equipo-dev/94-racha-actual-de-partidas
tipo: funcionalidad
epica: progreso
area: fullstack
prioridad: 3
fuente: E14 de ALCANCE.md (salio del PR #14, cerrado sin merge el 2026-11-05; la rama `claude/dazzling-einstein-w3qcyq` sirve de referencia)
archivos: backend/replays/analytics/aggregates.py, frontend/src/rachas.js, frontend/src/rachas.test.js, frontend/src/pages/Dashboard.jsx, backend/tests/test_racha_actual.py, frontend/e2e/humo.spec.js, docs/metricas.md
turnos: po 20261105T1945Z-cvqUYh1, arquitecto 20261106T0015Z-cR6uHk3

## PR

(La escribe el Release manager al final.)

## Que gana quien usa la app

En el Inicio, cuantas partidas seguidas llevas ganando o perdiendo ahora
("3 victorias seguidas", "2 derrotas seguidas"), al lado de la forma
reciente: saber de un vistazo si conviene seguir jugando o cortar. Hoy hay
que contar los puntos de la forma reciente a mano, y solo se ven 10.

## Criterios de aceptacion

- [ ] `GET /api/overview/` trae en `matches_summary` una clave
      `current_streak`: `{"result": "win"|"loss", "length": n, "since": <fecha
      de la primera partida de la racha>, "match_ids": [...]}`, o `null` si no
      hay ninguna partida decidida.
- [ ] Orden por `played_at` y `id` (igual que `matches_summary`); las
      partidas con `won=None` (incompletas o empate, ficha 68) no cortan ni
      suman la racha: test con G, None, G -> racha de 2 victorias.
- [ ] Se calcula sobre las partidas del filtro, como el resto de
      `matches_summary` (el lado no parte una partida): test con filtro de
      mapa que cambia la racha.
- [ ] Una racha de 1 se muestra igual ("1 victoria"); singular y plural
      correctos en la UI.
- [ ] El Inicio muestra la racha junto a la forma reciente, sin renderizar
      nada con `current_streak: null`; e2e con el numero que fija
      `seed_demo`.
- [ ] Fila nueva en `docs/metricas.md`.

## Fuera de alcance

- La racha mas larga de partidas (record): otra idea, junto a los records (E4).
- Racha de rondas (ya existe, ficha 60).
- Señal del Coach sobre la racha (E6 cubre "despues de perder seguido").

## Diseno

(arquitecto 20261106T0015Z-cR6uHk3, sobre `origin/dev@c63314e`)

**Forma.** Una sola forma obvia: `matches_summary` ya trae la lista de
partidas del filtro (sin lado) en orden `played_at, id`; la racha sale de
recorrerla desde el final. Sin arena ni consenso. `Skills:` no aplica (una
linea de texto en un panel existente). La rama `claude/dazzling-einstein-w3qcyq`
(PR #14, cerrado) no se reusa: es anterior a `won=None` (ficha 68) y a
`matches_summary`; sirve solo como referencia del texto.

### Backend

1. `backend/replays/analytics/aggregates.py`:
   - Funcion pura nueva, arriba de `matches_summary`:
     `racha_actual_de_partidas(partidas: list[dict]) -> dict | None`. Recibe
     las filas de `matches_summary` (con `id`, `played_at`, `won`) ya en orden
     cronologico. Recorre desde la ultima: salta las de `won is None` (ni
     cortan ni suman: empate o incompleta, ficha 68); la primera decidida fija
     el resultado; sigue sumando mientras `won` sea igual y corta en la
     primera decidida distinta. Devuelve
     `{"result": "win"|"loss", "length": n, "since": <played_at.isoformat() de la mas vieja de la racha>, "match_ids": [ids en orden cronologico, sin las None]}`,
     o `None` si no hay ninguna decidida. Docstring con el por que de saltar
     las `None` (no son resultado; cortarian la racha por un `.rec` faltante).
   - `matches_summary`: agregar `"current_streak": racha_actual_de_partidas(partidas)`
     al dict que devuelve. Nada mas cambia: el filtro sin lado ya esta
     (`filtros` sin `side`), asi que el lado no parte una partida.
   - Con la ficha 79 en dev, las partidas excluidas ya no llegan a
     `matches_summary` (sale de `base_queryset`): no cortan ni suman, sin
     codigo extra.
2. `backend/replays/views.py`: nada; `overview` ya pone `matches_summary`.

### Frontend

3. `frontend/src/rachas.js` (ya tiene el texto de las rachas de rondas):
   `textoRachaActual(racha)`:
   - `null`/`undefined` -> `''`.
   - `length === 1` -> `"Racha actual: 1 victoria (2026-11-05)"` /
     `"Racha actual: 1 derrota (2026-11-05)"`.
   - `length > 1` -> `"Racha actual: 3 victorias seguidas desde 2026-11-05"` /
     `"... 2 derrotas seguidas desde ..."`.
   - Fecha: `since.slice(0, 10)` (como el resto de la UI; `USE_TZ = False`).
4. `frontend/src/rachas.test.js`: `la racha actual nula no da texto`,
   `una victoria va en singular sin seguidas`,
   `varias derrotas van en plural con desde`.
5. `frontend/src/pages/Dashboard.jsx`, panel **Últimas partidas**: arriba del
   `.form-row`, `{racha && <p className="note racha-actual" style={{ margin: '0 0 8px' }}>{racha}</p>}`
   con `const racha = textoRachaActual(overview.data.matches_summary?.current_streak)`.
   Con `current_streak: null` no se renderiza nada. Color: si se quiere,
   clase `win`/`loss` ya existente en `styles.css`; no es requisito.
   Nota: la forma reciente usa todos los filtros (lado incluido) y la racha
   no usa el lado, igual que "Partidas ganadas": con filtro de lado pueden no
   coincidir los puntos con la racha. Es a proposito (una partida no se
   parte por lado) y queda en `metricas.md`.

### Tests backend

6. `backend/tests/test_racha_actual.py` (nuevo; `make_match` de `factories.py`
   con `my_score`/`opponent_score` y `index` para el orden, y
   `Match.objects.filter(...).update(won=None)` para las incompletas, como en
   `test_stacks_rivales.py`; cada partida con una ronda y su `make_round_player`
   para que `base_queryset` la vea):
   - `test_sin_partidas_la_racha_es_nula`
   - `test_tres_ganadas_al_final_dan_racha_de_tres` (P, G, G, G -> win 3,
     `since` de la primera G, `match_ids` en orden)
   - `test_una_partida_sin_resultado_no_corta_ni_suma` (G, None, G -> win 2)
   - `test_solo_partidas_sin_resultado_dan_nula`
   - `test_la_ultima_perdida_da_racha_de_una_derrota` (G, G, P -> loss 1)
   - `test_el_filtro_de_mapa_cambia_la_racha` (en orden: Club House G,
     Border P, Club House G; sin filtro -> win 1; con `map=club-house` ->
     win 2)
   - `test_el_filtro_de_lado_no_parte_la_partida` (partida con una ronda de
     ataque y una de defensa; `side=Attack` da la misma racha que sin filtro)
   - `test_la_api_del_resumen_trae_la_racha`: `GET /api/overview/` ->
     `matches_summary.current_streak.length`.
   Ademas tests directos de `racha_actual_de_partidas` con dicts a mano para
   el orden (no hace falta base).

### e2e

7. `frontend/e2e/humo.spec.js`, en `el Resumen muestra tus partidas` (que ya
   fija los numeros de `seed_demo`): `seed_demo` tiene 29 partidas, todas
   ganadas, la primera a `2026-08-01T20:00` (`INICIO`, `numero = 0`), asi que
   `await expect(page.locator('.racha-actual')).toHaveText('Racha actual: 29 victorias seguidas desde 2026-08-01')`.
   No hace falta tocar el seed.

### docs

8. `docs/metricas.md`, `## Base`, fila debajo de **Partidas ganadas**:
   **Racha actual de partidas** — partidas seguidas con el mismo resultado
   contando hacia atras desde la mas reciente (orden `played_at`, `id`), sobre
   las partidas del filtro sin el lado (como Partidas ganadas). Las partidas
   sin resultado (empate o incompleta, `won` nulo) no cortan ni suman. "Desde"
   es la fecha de la mas vieja de la racha. Inicio, panel Últimas partidas.

### Orden

1 -> 6 -> 3, 4 -> 5 -> `npm run build` -> 7 -> 8 -> `check.sh`.

### Que puede romperse

- `matches_summary` lo consume `ResumenPartidas`; una clave mas no la rompe.
  Si el Coach o algun test compara el dict entero de `matches_summary` con
  `assertEqual`, hay que sumarle la clave (`git grep -n "matches_summary" backend/tests`).
- Comparte `aggregates.py` y `metricas.md` con la ficha 92 (disenada en el
  mismo turno) y con la rama abierta de la 79: funciones y filas distintas,
  se resuelve con `git merge origin/dev`. Prioriza, no bloquea. Sin migracion.

### Verificacion manual

`seed_demo`, `runserver`, Inicio: en Últimas partidas, "Racha actual: 29
victorias seguidas desde 2026-08-01". Con la base real: la racha coincide con
los ultimos puntos de la forma reciente (sin filtro de lado), y un filtro de
mapa la cambia.

OMC: plan=— (ficha chica, una forma obvia) · revisión=— · verificación=—

## Implementacion

## Revision

## QA

## Pendiente

## Para el humano
