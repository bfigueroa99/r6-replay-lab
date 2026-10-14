# 44. Records personales en el Resumen

estado: en curso 2026-10-14
candado: -
rama: claude/equipo-dev/44-records-personales
tipo: funcionalidad
epica: progreso
area: fullstack
prioridad: 3
fuente: ALCANCE.md E4 (idea del PO 20261013T1915Z); epica progreso en curso (E3 en main por la ficha 40)
archivos: backend/replays/analytics/aggregates.py, backend/replays/views.py, backend/tests/test_records.py, frontend/src/pages/Dashboard.jsx, frontend/src/records.js, frontend/src/records.test.js, frontend/e2e/humo.spec.js, docs/metricas.md
turnos: po 20261014T0911Z, arquitecto 20261014T1012Z

## PR

(La escribe el Release manager al final.)

## Que gana quien usa la app

Ver de un vistazo tus mejores marcas (mejor partida, mas bajas en una
partida y en una ronda, el clutch mas grande, el mejor dia), cada una con un
enlace para volver a mirarla. Marca el techo a superar y saca provecho del
historial acumulado, que es lo que ningun tracker de API tiene ronda por
ronda.

## Criterios de aceptacion

- [ ] Un agregado nuevo en `analytics/aggregates.py` (expuesto en
  `/api/overview/` o en un endpoint GET propio, a eleccion del Arquitecto)
  devuelve, cada uno con `match_id`, fecha, mapa y el valor: mejor rating de
  partida (solo partidas con al menos 6 rondas tuyas), mas bajas en una
  partida, mas bajas en una ronda (con el numero de ronda), 1vX ganado mas
  grande (`one_vx`) y mejor dia por rondas ganadas (con minimo de rondas, el
  dia sin `match_id`). Test con factories que afirma cada record y su
  `match_id`.
- [ ] Empates: gana la partida mas reciente, para que el record cambie cuando
  lo igualas. Test con dos partidas de igual cantidad de bajas.
- [ ] Respeta los filtros de siempre (`map`, `operator`, `side`, `since`,
  `match_type`): test con `map=` que cambia el record de bajas.
- [ ] Base vacia o sin clutches: el record que no existe es `null` (no 500, no
  0 inventado). Test sobre base vacia.
- [ ] El Resumen (`Dashboard.jsx`) muestra el panel "Tus récords" con un
  enlace `/partidas/<id>` en cada uno; el e2e (`humo.spec.js`) lo ve con
  `seed_demo`, sigue un enlace y no ensucia la consola.
- [ ] Fila nueva en `docs/metricas.md` para cada record (que cuenta, minimos y
  desempate).

## Fuera de alcance

- La racha actual: es de PR #14, no se duplica.
- Historial de records (cuando se batio cada uno) o avisos de record nuevo.
- Records de otros jugadores o de compañeros.

## Diseno

(arquitecto 20261014T1012Z, sobre main 3438ab2)

Filtros duros: pasa. Todo sale de columnas que `metrics.py` ya escribe en
`RoundPlayer` (`kills`, `one_vx`, `won`, los del rating) y de `Match`
(`played_at`, `map_name`); se agrega al consultar, como el resto de
`aggregates.py`. Sin migracion, sin red, sin dependencia. No toca la racha
(PR #14).

**Donde se expone:** en `/api/overview/`, clave `records`, agregada en la
**vista** (`views.overview`, igual que `data_health`) y no dentro de
`agg.overview`: `coach.py:44` llama a `agg.overview` y no necesita pagar
estas consultas. El Resumen ya pide `/overview/` y se ahorra una request.

**Archivos y por que:**

- `backend/replays/analytics/aggregates.py`: `personal_records(**filters) ->
  dict` y sus constantes, despues de `recent_form`:
  - `RECORD_MIN_RONDAS_PARTIDA = 6`, `RECORD_MIN_RONDAS_DIA = 20` (unas
    tres partidas: un dia de una sola partida ganada 4-0 no es un record).
  - Base: `qs = base_queryset(**filters)`, `baseline = rating_baseline()`.
  - Por partida: el mismo `qs.values(*_MATCH_FIELDS).annotate(**AGGREGATES)`
    de `recent_form`, pasado por `derive`. Se hace una vez y de ahi salen
    dos records en Python:
    - `best_match_rating`: max de `rating` entre las de `rounds >=
      RECORD_MIN_RONDAS_PARTIDA`; desempate `played_at` mas reciente.
      `value` = rating (2 decimales), mas `rounds`.
    - `most_kills_match`: max de `kills`; desempate el mas reciente;
      `value` = bajas, mas `rounds`. Con 0 bajas en todo: `null`.
  - `most_kills_round`: `qs.filter(kills__gt=0).order_by("-kills",
    "-round__match__played_at", "-round__number").first()`; `value` = bajas,
    mas `round_label` = `f"R{number + 1}"` (la misma etiqueta que
    `views.py:454` usa en el detalle de partida).
  - `biggest_clutch`: `qs.filter(one_vx__gt=0, won=True)` con el mismo orden
    sobre `one_vx`; `value` = X de 1vX, mas `round_label`. Sin clutches:
    `null`.
  - `best_day`: `qs.values("round__match__played_at__date")` con `rounds` y
    `rounds_won`, solo dias con `rounds >= RECORD_MIN_RONDAS_DIA`; max de
    winrate de rondas, desempate mas rondas ganadas y despues el dia mas
    reciente. `value` = winrate (1 decimal), mas `rounds`, `rounds_won` y
    `day` (ISO). Sin `match_id` ni `map`.
  - Cada record con partida: `{"match_id", "played_at" (ISO), "map",
    "value", ...extras}`. Si no hay candidato: `null`. Base vacia: los cinco
    `null`, nunca 0.
  - "El mas reciente gana el empate" es a proposito: igualar tu record lo
    mueve a la partida nueva. Va en `metricas.md`.
- `backend/replays/views.py`: `payload["records"] = agg.personal_records(**filters)` en `overview`.
- `frontend/src/records.js` (nuevo) + `frontend/src/records.test.js`:
  `filasDeRecords(records)` devuelve la lista para el panel en orden fijo
  (mejor partida, mas bajas en una partida, mas bajas en una ronda, clutch
  mas grande, mejor dia), con etiqueta, valor formateado (`1v3`, `5 bajas`,
  `1.62`, `78 %`), detalle (`mapa · fecha` o `ronda R4 · mapa`) y `href`
  (`/partidas/<id>` o `null` para el dia). Deja afuera los `null`. Es logica
  pura y se prueba en vitest.
- `frontend/src/pages/Dashboard.jsx`: panel **"Tus récords"** despues de
  "Ultimas partidas", lista de filas con un `Link` a la partida en las que
  tienen `href`. Si `filasDeRecords` devuelve vacio, el panel no se muestra.
  Hint: `'Tus mejores marcas con los filtros activos. Si igualas una, cuenta
  la más reciente.'`.
- `frontend/e2e/humo.spec.js`: test `el Resumen muestra tus records y enlaza
  a la partida`: el panel "Tus récords" es visible, tiene "Más bajas en una
  partida", se hace clic en su enlace, la URL es `/partidas/\d+$` y el `h1`
  contiene un mapa de `seed_demo` (`/Club House|Border|Bank/`, como el test
  del detalle); consola limpia. `seed_demo` no se toca: tiene clutches
  (`indice % 17 == 0`), partidas de 7 rondas y dias con mas de 20 rondas.
- `backend/tests/test_records.py` (nuevo).
- `docs/metricas.md`: seccion nueva **`## Records`** despues de `## Sesiones`,
  una fila por record.

**Tests (`test_records.py`, con `factories.py`):**

- `test_mejor_rating_ignora_partidas_de_menos_de_seis_rondas`
- `test_mas_bajas_en_una_partida_trae_su_match_id`
- `test_mas_bajas_en_una_ronda_trae_la_etiqueta_de_la_ronda`
- `test_el_clutch_mas_grande_es_el_1vx_ganado_mayor`
- `test_mejor_dia_exige_el_minimo_de_rondas_y_no_trae_partida`
- `test_en_un_empate_gana_la_partida_mas_reciente`
- `test_el_filtro_de_mapa_cambia_el_record_de_bajas`
- `test_base_vacia_devuelve_todos_los_records_nulos`
- `test_sin_clutches_el_record_de_clutch_es_nulo_y_los_demas_no`
- `test_overview_trae_los_records` (por `/api/overview/`)

Frontend (`records.test.js`): orden fijo, `null` fuera, el dia sin `href`,
formato de cada valor.

**Orden:** agregado + tests de backend -> vista -> `records.js` + vitest ->
panel -> e2e -> `metricas.md`.

**Que puede romperse:** `/api/overview/` hace cinco consultas mas; con una
base grande la de por partida es la misma que `recent_form` sin el `limit`.
Es aceptable (se agrega por partida, no por ronda); si QA ve la respuesta
por encima de ~300 ms con 2.000 partidas sinteticas, se anota. Ningun test
existente afirma las claves exactas de `overview`.

**Filas de `metricas.md`** (texto sugerido): *Mejor partida*: rating de
partida mas alto (el de 'Rating') entre las partidas con al menos 6 rondas
tuyas con los filtros activos. *Mas bajas en una partida / en una ronda*:
maximo de bajas tuyas. *Clutch mas grande*: el 1vX ganado de X mas alto.
*Mejor dia*: winrate de rondas mas alto en un dia con al menos 20 rondas;
empata a favor de mas rondas ganadas. En todos, a igual valor gana la
partida (o el dia) mas reciente. Sin candidato, el record no aparece.

**Verificacion manual:** `seed_demo`, `/`, el panel muestra los cinco
records y cada enlace abre su partida; con `?map=Border` cambian.

**Umbrales:** 6 rondas por partida y 20 por dia son a ojo; calibrar con la
base real (a `## Para el humano` si QA lo confirma solo con sinteticos).

## Implementacion

## Para el humano
