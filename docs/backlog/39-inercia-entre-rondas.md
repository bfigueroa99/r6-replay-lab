# 39. Inercia entre rondas: como juegas despues de ganar y despues de perder

estado: aprobado
candado: -
rama: claude/equipo-dev/39-inercia-entre-rondas
tipo: funcionalidad
epica: lado-y-marcador
area: fullstack
prioridad: 2
fuente: ALCANCE.md B4 (idea del PO 20261013T0511Z); epica lado-y-marcador en curso (B1 en main por #25)
archivos: backend/replays/analytics/aggregates.py, backend/replays/views.py, frontend/src/muestra.js, frontend/src/muestra.test.js, frontend/src/pages/Trends.jsx, docs/metricas.md, backend/tests/test_ronda_anterior.py, frontend/e2e/humo.spec.js
turnos: po 20261013T1915Z, arquitecto 20261013T2011Z, dev 20261013T2112Z, revisor 20261013T2211Z, qa 20261013T2311Z

## PR

(La escribe el Release manager al final.)

## Que gana quien usa la app

Ver en Tendencias si una ronda perdida te arrastra a la siguiente: tu winrate
y tu rating en las rondas que vienen despues de ganar contra las que vienen
despues de perder. Es un dato que solo sale del historial acumulado y que
ninguna pantalla muestra hoy.

## Criterios de aceptacion

- [ ] `GET /api/trends/` devuelve `by_previous_round`: tres filas en orden fijo
      `after_win`, `after_loss`, `no_previous`, cada una con las metricas de
      `totals()` (rondas, ganadas, winrate, rating, KPR...). La ronda anterior
      es la de `number - 1` de la misma partida; su resultado es
      `Round.my_team_won` de esa ronda.
- [ ] Va a `no_previous` la primera ronda de la partida, la que no tiene
      ronda `number - 1` importada (falta el `.rec`) y la que tiene la
      anterior con `my_team_won` nulo. Ninguna ronda queda contada en dos
      filas: la suma de `rounds` de las tres filas es igual a `rounds` de
      `/api/overview/` con los mismos filtros (test).
- [ ] La ronda anterior se lee de la partida entera, no del queryset
      filtrado: con `?side=Attack` una ronda de ataque cuya anterior fue de
      defensa sigue cayendo en `after_win`/`after_loss` (test, igual que
      `_lado_inicial` en `by_half`).
- [ ] Tendencias muestra el panel "Despues de ganar o perder la ronda
      anterior" con las tres filas y CSV, con la banda de ruido o un aviso de
      muestra chica cuando alguna fila tiene menos de 30 rondas.
- [ ] `docs/metricas.md` tiene la fila de la metrica; el e2e de Tendencias
      ve el panel con los datos de `seed_demo` sin errores de consola.
- [ ] Base vacia y filtros raros (`days=-1`, `since=foo`, `map=%00`)
      devuelven 200 con las tres filas en 0.

## Fuera de alcance

- Rachas de mas de una ronda (despues de 2 o 3 perdidas seguidas): otra ficha
  si esta sale util.
- Marcador antes de la ronda (adelante, empatado, atras): ficha 41.
- Cualquier cambio en el Coach o en las reglas de señales.

## Diseno

(Arquitecto 20261013T2011Z, sobre main 5d2aecc. Spike en el scratchpad con
`seed_demo`: la subconsulta de abajo da 87 / 87 / 29 rondas, suma 203 = total.)

Es la primera de tres fichas que agregan cortes a `/api/trends/` y a
Tendencias (39, 41, 40). Esta deja armados los dos ayudantes que las otras
reusan: `_filas_por_tramo` en el backend y `TablaDeCorte` + `muestra.js` en
el frontend. Implementar primero esta.

**Archivos y por que**

- `backend/replays/analytics/aggregates.py`:
  - `_filas_por_tramo(campo: str, tramos: dict[str, QuerySet]) -> list[dict]`:
    una fila `{campo: nombre, **totals(qs, baseline)}` por tramo, en el orden
    del dict, con un solo `rating_baseline()`. Reescribir el final de
    `by_half` para usarlo (mismo resultado; `test_mitades.py` lo cubre).
  - `RONDA_ANTERIOR = ("after_win", "after_loss", "no_previous")`, constante
    de orden como `MITADES`.
  - `_resultado_anterior() -> Subquery`: `Round.objects.filter(match_id=OuterRef("round__match_id"), number=OuterRef("round__number") - 1).values("my_team_won")[:1]`.
    Se lee de `Round`, no del queryset filtrado: por eso `?side=` no la
    cambia (mismo criterio que `_lado_inicial`). Docstring corto con ese por que.
  - `by_previous_round(**filters)`: `qs = base_queryset(**filters).annotate(anterior=_resultado_anterior())`;
    tramos `after_win: qs.filter(anterior=True)`, `after_loss: qs.filter(anterior=False)`,
    `no_previous: qs.filter(anterior__isnull=True)`. Las tres son disjuntas
    y cubren todo (nulo = sin ronda anterior importada o anterior sin
    resultado). Devuelve `_filas_por_tramo("previous", tramos)`.
- `backend/replays/views.py`: en `trends`, `"by_previous_round": agg.by_previous_round(**filters)`.
- `frontend/src/muestra.js` (nuevo, logica pura): `export const MUESTRA_CORTE = 30`
  y `export function filasConPocaMuestra(filas, minimo = MUESTRA_CORTE)` que
  devuelve las filas con `0 < rounds < minimo` (las de 0 rondas no avisan:
  salen vacias). `frontend/src/muestra.test.js` con vitest.
- `frontend/src/pages/Trends.jsx`:
  - componente local `TablaDeCorte({ filas, columna, etiquetas, rowKey, csvName })`
    con las columnas de "Por mitad" (etiqueta, Rondas, Ganadas %, Rating con
    su `help`, KPR, Aperturas %), `initialSort` por `orden`. "Por mitad"
    no se migra (no hace falta tocarla).
  - panel "Después de ganar o perder la ronda anterior", entre "Por mitad de
    la partida" y "Por numero de ronda". Etiquetas: `after_win` "Después de
    ganar", `after_loss` "Después de perder", `no_previous` "Sin ronda anterior".
    `csvName="ronda-anterior"`. Hint normal: "Si después de perder tu winrate
    o tu rating caen más que tu promedio, la ronda perdida te sigue pesando."
    Si `filasConPocaMuestra(filas).length`, el hint pasa a: "Ojo: alguna fila
    tiene menos de 30 rondas; la diferencia puede ser varianza." (mismo
    patron que `flaco` en `Jugador.jsx`). Se renderiza solo si
    `data.by_previous_round?.length`.
- `docs/metricas.md`: seccion nueva `## Contexto de la ronda` debajo de
  "Mitades y prorroga", con la fila **Despues de ganar / perder** (ronda
  anterior = `number - 1` de la misma partida, leida de la partida entera;
  sin ronda anterior importada o sin resultado va a "Sin ronda anterior";
  metricas las de siempre). En `## Muestra minima` la fila
  `Cortes de Tendencias (ronda anterior, marcador, hora, dia) | 30 rondas por fila: no se oculta, se avisa`.
- `backend/tests/test_ronda_anterior.py` (nuevo), con `factories`
  (`make_match`, `make_round(match, n, side=, won=)`, `make_round_player`):
  - `test_las_tres_filas_salen_en_orden_fijo`
  - `test_ganar_y_perder_mandan_la_siguiente_a_su_fila` (R1 gana, R2 pierde,
    R3: R2 en after_win, R3 en after_loss, R1 en no_previous)
  - `test_la_primera_ronda_y_la_que_le_falta_la_anterior_van_a_sin_anterior`
    (rondas 1, 2 y 5: la 5 sin la 4)
  - `test_anterior_sin_resultado_va_a_sin_anterior` (`won=None` via `Round.objects.filter(...).update(my_team_won=None)`)
  - `test_el_filtro_de_lado_no_cambia_la_ronda_anterior` (R1 defensa ganada,
    R2 ataque; `by_previous_round(side="Attack")`: R2 en after_win)
  - `test_las_filas_suman_las_rondas_del_resumen` (contra `overview()["overall"]["rounds"]`)
  - `test_base_vacia_y_filtros_raros_dan_200_con_tres_filas_en_cero`
    (cliente sobre `/api/trends/?days=-1`, `?since=foo`, `?map=%00`)
- `frontend/e2e/humo.spec.js`: test `Tendencias muestra la inercia entre rondas`,
  calcado de `Tendencias muestra la tabla por mitad`: panel por titulo, celdas
  "Después de ganar" y "Después de perder", consola limpia. Con `seed_demo`
  las rondas alternan ganada/perdida, asi que "Después de ganar" da 0 % y
  "Después de perder" 100 % (87 rondas cada una): se puede afirmar, pero
  basta con las celdas.

**Orden:** aggregates + test backend -> views -> muestra.js + test ->
Trends.jsx -> e2e -> metricas.md -> `check.sh`.

**Que puede romperse:** nada de base (sin migracion ni recompute). Si
`_filas_por_tramo` cambia el orden o las claves de `by_half`, cae
`test_mitades.py`. `OuterRef(...) - 1` funciona en Django + SQLite (spike).

**Verificacion manual:** `python manage.py seed_demo`, `runserver`,
`curl -s localhost:8000/api/trends/ | python -m json.tool | grep -A3 by_previous_round`,
y `/tendencias` muestra el panel con 0 % / 100 %.

## Implementacion

(Dev 20261013T2112Z.) Diseno completo, sin desvios de alcance:

- `aggregates.py`: `_filas_por_tramo`, `RONDA_ANTERIOR`, `_resultado_anterior()`
  y `by_previous_round()`; `by_half` ahora termina en `_filas_por_tramo`
  (mismo resultado, `test_mitades.py` verde). El orden de las filas sale de
  `RONDA_ANTERIOR`, igual que `by_half` con `MITADES`.
- `views.py`: `by_previous_round` en `/api/trends/`.
- `frontend/src/muestra.js` + `muestra.test.js` (4 tests): `MUESTRA_CORTE = 30`
  y `filasConPocaMuestra`.
- `Trends.jsx`: `TablaDeCorte` local y el panel "Después de ganar o perder la
  ronda anterior" entre "Por mitad" y "Por numero de ronda", CSV
  `ronda-anterior`, hint con aviso de muestra chica.
- `test_ronda_anterior.py`: los 7 tests del diseno mas
  `test_la_ronda_anterior_no_se_cruza_entre_partidas` y
  `test_trends_con_datos_trae_la_ronda_anterior`.
- e2e `Tendencias muestra la inercia entre rondas`: ademas de las celdas
  afirma Ganadas 0 % despues de ganar y 100 % despues de perder (seed_demo
  alterna), para que unas filas invertidas no pasen.
- `metricas.md`: seccion `## Contexto de la ronda` y fila de muestra minima.
  Desvio menor: la fila de muestra dice solo "(ronda anterior)"; las fichas
  40 y 41 agregan marcador, hora y dia cuando existan.

Revision ciega previa (subagente): 4 hallazgos menores (e2e sin numeros,
filtro de lado que no filtraba en un test, fila de doc que nombraba cortes
inexistentes, constante sin usar), los 4 corregidos.

Verificacion: `check.sh` en `Todo en verde.` (502 tests backend, 69 vitest,
build ok, 27 e2e).

## Revision 2026-10-13 sobre 5f23d8f

(Revisor 20261013T2211Z.) Revision ciega (subagente con `revision.md` sobre el diff sin
`docs/backlog`): sin hallazgos, veredicto `aprobar`. Confirmado por el lider:

- Criterios: los 6 cubiertos. Orden fijo, ganar/perder, primera ronda y
  anterior faltante, anterior sin resultado, filtro de lado y suma contra
  `overview` con test en `test_ronda_anterior.py`; panel, CSV y aviso de
  muestra en `Trends.jsx` + `muestra.test.js`; e2e `Tendencias muestra la
  inercia entre rondas` afirma 0 % / 100 %; fila en `metricas.md` (corte y
  muestra minima); base vacia y filtros raros con test de API.
- Con `seed_demo` las tres filas suman el total en cada filtro probado
  (todo 87/87/29 = 203; `side=Attack` 0/87/29 = 116; `side=Defense` 87/0/0 =
  87; `map=oregon` 0/0/0), sin rondas contadas dos veces.
- Diff dentro de `archivos:`; sin tildes en identificadores, UI con tildes,
  sin `print` ni `console.log`; sin dependencias ni migraciones.
- La subconsulta corre al consultar: es un corte (como `_lado_inicial` en
  `by_half`), no una metrica por ronda; no rompe la regla de metricas al
  importar.
- Test agregado (verde): `test_el_filtro_de_operador_no_cambia_la_ronda_anterior`,
  porque `metricas.md` promete que el filtro de operador tampoco cambia la
  anterior y solo estaba probado el de lado.

`check.sh` en `Todo en verde.` (503 tests backend, 69 vitest, build ok, 27 e2e).

Veredicto: aprobar.

## QA 2026-10-13 sobre d2f1dc7

(QA 20261013T2311Z.) Rama sin conflicto con `origin/main`
(`git merge-tree --write-tree origin/main HEAD`, salida 0). Bases en el
scratchpad, nunca en el repo; `S` = carpeta del scratchpad.

- **`check.sh`**: `Todo en verde.` (ruff ok, 503 tests backend OK con 4
  skipped, 69 vitest, build ok, 27 e2e incluido `Tendencias muestra la
  inercia entre rondas`).
- **Base vacia** (`SQLITE_PATH=$S/vacia.sqlite3 python manage.py migrate`,
  `runserver 8101`): `/api/trends/` con `""`, `?days=-1`, `?since=foo`,
  `?until=foo`, `?map=%00`, `?page=-1`, `?side=`, `?side=Attack` -> 200 y
  `by_previous_round` = `after_win 0, after_loss 0, no_previous 0`. La UI
  muestra el estado vacio de siempre, sin errores de consola.
- **Base sembrada con `factories.py`** (`$S/sembrar.py` via `manage.py shell`):
  partida Club House con rondas 1 G (ataque), 2 P (def), 3 P (at), 5 G (at,
  sin bajas), 6 con `my_team_won=None` (def), 7 G (at): falta la 4; partida
  Border de una sola ronda perdida; un compañero con nick repetido (otro
  `profile_id`). Esperado a mano: despues de ganar = R2 y R6, despues de
  perder = R3, sin anterior = R1, R5 (falta la 4), R7 (anterior sin
  resultado), Border R1.
  - `/api/trends/` -> 2 / 1 / 4 (winrate 50 / 0 / 75), suma 7 = `overview`
    7. Coincide con lo esperado.
  - `?side=Attack` -> 0 / 1 / 4 (suma 5 = `overview?side=Attack` 5: R3 sigue
    en despues de perder aunque la R2 fue de defensa). `?side=Defense` -> 2 / 0 / 0.
  - `?map=club-house` -> 2 / 1 / 3 (= overview 6); `?map=border` -> 0 / 0 / 1
    (= overview 1); `?days=-1` -> 0 / 0 / 0 (= overview 0); `?operator=Zofia`,
    `?since=foo`, `?until=foo`, `?page=-1`, `?side=`, `?map=` -> 2 / 1 / 4.
    `?map=%00` -> 0 / 0 / 0. Todo 200, sin trazas en el log del server.
  - Vecinos (`overview`, `matches`, `maps`, `operators`, `coach`, `sessions`,
    `trends?side=Attack`) en las dos bases: 200. `by_half` intacto (5 / 2 / 0).
- **UI en Chromium** (`node $S/ui.cjs frontend $S` sobre la base sembrada):
  `/tendencias` muestra el panel con "Después de ganar 2 50 %", "Después de
  perder 1 0 %", "Sin ronda anterior 4 75 %" y el aviso "menos de 30
  rondas"; 0 errores de consola.
- **Chunk inicial**: `vite build` de `origin/main` y de la rama, `index-*.js`
  185.47 kB en los dos (0 %); el chunk lazy de Tendencias pasa de 12.05 a
  13.31 kB.
- **Mutacion** (cada una revertida con `git checkout --`):
  1. `OuterRef("round__number") - 1` -> `+ 1`: `tests.test_ronda_anterior`
     FAILED (failures=4).
  2. filtros de `after_win` y `after_loss` invertidos: FAILED (failures=5).
  3. subconsulta sin `match_id` (cruza partidas): FAILED (failures=1).
  4. `muestra.js` `rondas > 0` -> `>= 0`: vitest 2 failed.
  5. `muestra.js` `rondas < minimo` -> `<= minimo`: vitest 1 failed.
- Sin migracion, sin `recompute`, sin parser, sin Electron ni `.ps1`: no hay
  `## Verificar en el PC`.

Criterios: los 6 cumplidos con la evidencia de arriba. Veredicto: aprobado.

## Para el humano

El umbral de 30 rondas del aviso de muestra se probo solo con datos
sinteticos: calibrar con la base real (si el aviso sale siempre, o nunca).
