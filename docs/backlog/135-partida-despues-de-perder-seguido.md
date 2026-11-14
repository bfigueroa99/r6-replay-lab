# 135. Partida despues de perder seguido

estado: aprobado
candado: -
rama: claude/equipo-dev/135-partida-despues-de-perder-seguido
tipo: funcionalidad
epica: progreso
area: backend
prioridad: 3
fuente: ALCANCE.md E6; el Coach ya aconseja "si son tres derrotas seguidas, corta la sesión" (`coach.py`, `_form`) sin mostrar el dato que lo respalda
archivos: backend/replays/analytics/aggregates.py, backend/replays/views.py, backend/tests/test_tras_derrotas.py, frontend/src/trasDerrotas.js, frontend/src/trasDerrotas.test.js, frontend/src/pages/Trends.jsx, frontend/e2e/humo.spec.js, docs/metricas.md
turnos: po 20261113T1954Z-cfZTvvE, arquitecto 20261114T0040Z-chQsvnq, dev 20261114T0040Z-c3LsMAo, revisor 20261114T0104Z-choi73m, qa 20261114T0104Z-cWK4yQD

## PR

## Que gana quien usa la app

En Tendencias, tu winrate en la partida siguiente segun cuantas derrotas
seguidas llevabas en la sesion (0, 1, 2, 3 o mas): saber con tus propios
numeros si conviene cortar despues de dos derrotas, que hoy el Coach dice
como regla general.

## Criterios de aceptacion

- [x] Un agregado ordena las partidas de cada sesion (el corte de sesion
      que ya usan `sessions` y `by_session_position`) y devuelve, por
      derrotas seguidas previas en esa sesion (0, 1, 2, 3+), `matches`,
      `wins` y `winrate` de la partida siguiente. La primera partida de la
      sesion cae en 0. Test con una sesion D, D, V, D.
- [x] Una partida con `won` nulo o empatada no suma ni corta la racha y
      no entra al winrate de su fila (como `match_result`). Test.
- [x] Los filtros globales aplican a la partida que se cuenta; la racha
      previa se mide sobre todas las partidas de la sesion, sin filtros
      (si no, un filtro de mapa inventaria rachas). Test con filtro de mapa.
- [x] Panel en Tendencias cerca de "Curva de la sesión", con su `n` por
      fila y aviso de muestra chica; sin sesiones, un texto y no un error;
      e2e con `seed_demo` y consola limpia. Fila nueva en `docs/metricas.md`.

## Fuera de alcance

- Minutos desde la partida anterior (otro tramo).
- Rachas entre sesiones (E13 mira los dias de descanso).
- Cambiar la señal del Coach para que use este dato.

## Diseno

(arquitecto 20261114T0040Z-chQsvnq) Filtros duros: pasa (orden y resultado
de `Match`, el corte de sesion que ya existe; sin red, sin dependencias, sin
POST, sin migracion). Una sola forma obvia: sin arena ni consenso.

**Regla** (va tal cual a `metricas.md`). Las sesiones son las de
`_sessions_raw()`, sobre **todas** las partidas y en orden de `played_at`
(como `by_session_position`: un filtro no inventa ni borra rachas). Dentro de
cada sesion se recorre en orden con un contador `racha` que arranca en 0:
la partida se anota en la fila `min(racha, 3)` y despues, segun
`match_result(won, my_score, opponent_score)`: `derrota` suma 1, `victoria`
lo vuelve a 0, `empate` e `incompleta` no lo tocan. Una partida cuenta en
`matches` de su fila si pasa los filtros de `match_queryset(**filters)`
(mapa, tipo, modo, fechas, sesion; lado, operador y sitio se ignoran como en
`match_queryset`, porque una partida tiene los dos lados); entra a `decided`
solo si es `victoria` o `derrota`, y `winrate = _pct(wins, decided)`. Es
winrate de **partida**, no de rondas: el panel lo dice.

**Archivos:**
- `backend/replays/analytics/aggregates.py`: `TRAS_DERROTAS_TOPE = 3` y
  `by_losing_streak(**filters) -> list[dict]`, justo despues de
  `by_session_position`. Una consulta para `Match.objects.values("id", "won",
  "my_score", "opponent_score")` de todas, una para los ids de
  `match_queryset(**filters)` y `_sessions_raw()`; sin consulta por fila.
  Devuelve siempre las 4 filas en orden: `{"streak": 0..3, "label": "0" |
  "1" | "2" | "3+", "matches", "decided", "wins", "losses", "winrate"}`
  (`winrate` None con `decided == 0`).
- `backend/replays/views.py`: clave `"by_losing_streak"` en `sessions()`,
  el endpoint que Tendencias ya pide (`/api/sessions/`); no hay URL nueva.
- `backend/tests/test_tras_derrotas.py` (Django, con `factories.py`):
  `test_sesion_d_d_v_d_reparte_por_derrotas_previas` (filas 0:2 partidas
  -primera y la que sigue a la V-, 1:1, 2:1, con sus wins);
  `test_la_primera_de_la_sesion_cae_en_cero`;
  `test_tres_o_mas_se_juntan_en_la_ultima_fila` (D,D,D,D,V: la 4a y la 5a en 3+);
  `test_una_sesion_nueva_reinicia_la_racha` (hueco > SESSION_GAP_MINUTES);
  `test_incompleta_y_empate_no_suman_ni_cortan_ni_entran_al_winrate`;
  `test_filtro_de_mapa_cuenta_solo_esas_pero_la_racha_es_de_todas`;
  `test_sin_partidas_devuelve_las_cuatro_filas_vacias`;
  `test_api_sessions_trae_by_losing_streak`;
  `assertNumQueries` fijo sobre `by_losing_streak` (como `test_aggregates.py`).
- `frontend/src/trasDerrotas.js`: `filasTrasDerrotas(rows)` (`[]` si
  ninguna fila tiene `matches`, para mostrar la nota y no ceros; agrega
  `tramo`: "Sin derrotas antes", "Tras 1 derrota", "Tras 2 derrotas",
  "Tras 3 o más") y `conPocasPartidas(filas)` con `PARTIDAS_CORTE` importado
  de `prorrogaPorLado.js` (el corte de 10 partidas de Margen final; no se
  define otro numero).
- `frontend/src/trasDerrotas.test.js` (vitest): sin datos devuelve `[]`;
  etiquetas y orden; aviso con una fila de 1..9 partidas decididas y no con 0.
- `frontend/src/pages/Trends.jsx`: Panel "Después de perder seguido" justo
  debajo de "Curva de la sesión" (fuera de su condicional
  `porPosicion.length > 2`), con `sesiones.data.by_losing_streak`. Tabla
  `DataTable` con columnas Tramo, Partidas, Decididas, Ganadas (`winrate`,
  0 digitos, `%`); `hint`: "Winrate de la partida siguiente según cuántas
  derrotas seguidas llevabas en esa sesión. Las rachas se cuentan con todas
  tus partidas; los filtros eligen qué partidas se cuentan." Nota si
  `conPocasPartidas`; sin filas, `<p className="note">` "Todavía no hay
  partidas con estos filtros." Sin grafico: cuatro filas se leen mejor en la
  tabla (dataviz: no aplica).
- `frontend/e2e/humo.spec.js`: test "Tendencias muestra la partida después
  de perder seguido": ubica el panel por `section.panel` + heading (no por
  posicion), afirma las 4 filas y los numeros que devuelve
  `/api/sessions/` sobre `seed_demo` (sacarlos corriendo el seed en una base
  temporal), y consola limpia.
- `docs/metricas.md`: fila **Después de perder seguido** en la tabla de
  Tendencias, con la regla de arriba, el `n` (decididas) y el corte de 10.

**Orden:** tests Django en rojo -> `by_losing_streak` -> clave en la vista
-> vitest -> helper -> panel -> e2e -> `metricas.md` -> `npm run build`.

**Puede romperse:** el e2e de Tendencias que cuente paneles por posicion;
`_sessions_raw` se llama una vez mas por request de `/api/sessions/` (ya la
llaman `sessions` y `by_session_position`): si `assertNumQueries` lo
muestra caro, pasarle las sesiones ya calculadas desde la vista no esta
permitido (cambia firmas usadas por el coach); se acepta una consulta mas.

**Archivos ocupados:** `aggregates.py` y `views.py` los tocan 132 y 134 en
funciones lejanas (solo agregan); sin pisada real, no se frena.

**Verificacion manual:** `/api/sessions/` con `map=<slug>` y sin el: las
filas cambian de `matches` pero una partida no salta de fila por el filtro.

Skills: no aplica (agregado y tabla en una pagina existente, con precedente `by_session_position`).
Skills del repo: statistical-analysis (winrate sobre decididas, `n` a la vista, corte de 10 reusado, sin promedio de promedios), testing-strategy (Django para la regla, vitest para el helper, e2e para el panel).
OMC: plan=— · revisión=— · verificación=—

## Implementacion

Quedo el diseno completo, sin desvios de alcance.

- `aggregates.py`: `TRAS_DERROTAS_TOPE = 3` y `by_losing_streak(**filters)`
  despues de `by_session_position`: resultados de todas las partidas con
  `match_result`, ids de `match_queryset(**filters)` y `_sessions_raw()`; tres
  consultas fijas. Siempre 4 filas (`streak`, `label`, `matches`, `decided`,
  `wins`, `losses`, `winrate`).
- `views.py`: clave `by_losing_streak` en `/api/sessions/`.
- `trasDerrotas.js`: `filasTrasDerrotas` (`[]` sin partidas, tramos y orden)
  y `conPocasPartidas` sobre las **decididas**, con `PARTIDAS_CORTE` de
  `prorrogaPorLado.js`.
- `Trends.jsx`: panel "Después de perder seguido" debajo de "Curva de la
  sesión", fuera de su condicional; tabla Tramo, Partidas, Decididas (con
  ayuda), Ganadas; aviso de muestra; nota sin partidas.
- e2e `Tendencias muestra la partida después de perder seguido`: las 4 filas
  de `/api/sessions/` sobre `seed_demo` (`0: 29/29/29`, el resto en 0: el
  seed separa sus partidas 3 h y las gana todas) y la tabla, consola limpia.
- `docs/metricas.md`: fila **Después de perder seguido** debajo de Curva de la sesion.

Desvios menores:
- El hint suma "Lado, operador y sitio no aplican: una partida tiene los dos
  lados." (lo pidio la revision ciega: el panel de arriba si los aplica).
- Test extra `test_lado_operador_y_sitio_no_cambian_las_filas` (revision
  ciega): con rondas solo de defensa y otro operador; cambiar
  `match_queryset` por `base_queryset` lo hace caer (mutacion probada).

Criterios -> tests: (1) `test_sesion_d_d_v_d_reparte_por_derrotas_previas`,
`test_la_primera_de_la_sesion_cae_en_cero`, `test_tres_o_mas_se_juntan_en_la_ultima_fila`,
`test_una_sesion_nueva_reinicia_la_racha`, `test_consultas_constantes`
(`assertNumQueries(3)`); (2) `test_incompleta_y_empate_no_suman_ni_cortan_ni_entran_al_winrate`;
(3) `test_filtro_de_mapa_cuenta_solo_esas_pero_la_racha_es_de_todas`,
`test_lado_operador_y_sitio_no_cambian_las_filas`; (4)
`test_sin_partidas_devuelve_las_cuatro_filas_vacias`, `test_api_sessions_trae_by_losing_streak`,
vitest `trasDerrotas.test.js` (6), e2e, fila de `metricas.md`.

TDD: los 9 tests Django se escribieron antes del codigo y fallaron
(`python manage.py test tests.test_tras_derrotas` -> `FAILED (errors=9)`,
`AttributeError: by_losing_streak`); el vitest tambien antes del helper
("no tests" al no existir el modulo).

`verificar.sh`: VERDE 33d94a9 (1367 tests backend, 449 vitest, 120 e2e).

Revision ciega (omc-code-reviewer, eje estandares): aprobar, 2 LOW, los dos
arreglados (hint y test de lado/operador/sitio).

Verificacion manual sugerida: `seed_demo` + `runserver`, Tendencias: el
panel con las 4 filas, 29 partidas en "Sin derrotas antes".

Skills: no aplica (agregado y tabla con precedente `by_session_position`).
Skills del repo: test-driven-development (rojo visto antes del codigo),
statistical-analysis (winrate sobre decididas, `n` a la vista, corte de 10
reusado), ux-copy (hint y nota con tildes, como los vecinos de Tendencias);
modern-web-guidance no se consulto: el panel copia el patron
`Panel` + `DataTable` + nota de Prórroga por lado en la misma pagina.
OMC: plan=— · revisión=2 LOW (2 arreglados) · verificación=—

## Revision 2026-11-14 sobre ca7c9f5

(revisor 20261114T0104Z-choi73m)

Veredicto: aprobar -> `revisado`.

Base: rama ya contiene `origin/dev` (f34baba); `verificar.sh`: VERDE ca7c9f542
(1367 tests backend, 449 vitest, 120 e2e).

Revision a ciegas, dos ejes (omc-code-reviewer x2; diff de 318 lineas):
- Estandares: aprobar, 1 LOW.
- Intencion: aprobar, los 4 criterios cubiertos (`test_tras_derrotas.py`, 10
  tests; `trasDerrotas.test.js`; e2e de Tendencias; fila en `metricas.md`);
  nada fuera de alcance; 2 LOW.

Confirmado por el lider:
- [test] LOW `frontend/e2e/humo.spec.js:101`: el e2e solo recorre el caso
  con datos (seed: 29 decididas en la fila 0); el aviso de muestra y la nota
  sin partidas solo se prueban en vitest. Opcional: un caso e2e con un rango
  de fechas vacio que afirme la nota y la consola limpia.

No confirmados o fuera de este diff:
- LOW `aggregates.py:3078` (`_sessions_raw`, `order_by("played_at")` sin
  desempate por `id`): dos partidas con el mismo `played_at` quedan en orden
  no garantizado y la racha depende del orden. Es previo al cambio (lo
  comparte `by_session_position`) y pide dos replays con la misma marca de
  tiempo; no se le carga a esta ficha. Arreglo barato si alguien lo toma:
  `order_by("played_at", "id")`.
- LOW `metricas.md:136` ("como *Margen final*" vs `PARTIDAS_CORTE` de
  `prorrogaPorLado.js`): descartado, Margen final tambien avisa con menos de
  10 (`metricas.md:123`); el texto es cierto.

Ficha: criterios cubiertos; el diff no sale de `archivos:`; fila en
`metricas.md`; identificadores sin tildes, UI con tildes; sin `print` ni
`console.log`.

Skills: no aplica.
Skills del repo: ninguna (revision con el prompt de `revision.md`).
OMC: plan=— · revisión=3 LOW (1 confirmado, 0 arreglados) · verificación=—


## QA 2026-11-14 sobre 3ba2768

(qa 20261114T0104Z-cWK4yQD)

Veredicto: `aprobado`. Los 4 criterios con evidencia.

- `verificar.sh` (rama con `origin/dev` f34baba): VERDE 3ba2768c4, 1367 tests
  backend, 449 vitest, 120 e2e.
- Base sembrada desde `factories.py` (script en el scratchpad, sin `.rec` ni
  `.sqlite3` al repo): sesion de 30 min entre partidas D Club, D Bank, V Club,
  D Club, D Bank, D Club, D Club, V Club, empate 4-4, incompleta (`won=None`);
  otra sesion a +10 h con una V. A mano: fila 0 = 5 partidas, 3 decididas, 1
  ganada (33.3); 1 = 2/2/0; 2 = 2/2/1 (50); 3+ = 2/2/1 (50).
  `SQLITE_PATH=<base> python manage.py runserver` y `curl /api/sessions/`:
  - sin filtros: exactamente eso (criterios 1 y 2: el empate y la incompleta
    caen en la fila 0 sin decidir ni cortar la racha).
  - `?map=bank`: solo fila 1, 2/2/0 (la racha se mide con todas: criterio 3).
    `?map=club-house`: 5/3/1, 0, 2/2/1, 2/2/1.
  - `?side=Defense`, `?operator=Ash&site=x`, `?until=foo`, `?page=-1`,
    `?map=`: 200 e iguales a sin filtros. `?since=2030-01-01`: 200, 4 filas
    en 0 con winrate `null`. Base vacia: 200, 4 filas vacias.
- Mutaciones (`by_losing_streak`), las tres mueren: sin `racha = 0` tras
  victoria -> cae `test_sesion_d_d_v_d_reparte_por_derrotas_previas`; racha
  solo con partidas filtradas -> cae
  `test_filtro_de_mapa_cuenta_solo_esas_pero_la_racha_es_de_todas`; empate
  como derrota -> cae `test_incompleta_y_empate_no_suman_ni_cortan_ni_entran_al_winrate`.
- `vite build`: chunk inicial 200459 B en dev y en la rama (sin cambio);
  chunk de Tendencias 34901 -> 36227 B.
- accessibility-review (Playwright en Chromium, base sembrada, `/tendencias`):
  tabla con rol y cabeceras (Tramo, Partidas, Decididas, Ganadas); filas
  "Sin derrotas antes 5 3 33%", "Tras 1 derrota 2 2 0%", "Tras 2 derrotas 2 2
  50%", "Tras 3 o más 2 2 50%"; aviso de muestra visible; contraste celdas
  14.17:1, nota y cabeceras 5.71:1; con Tab se llega a Descargar CSV y a los
  botones de orden; consola limpia. Sin hallazgos Critical ni Major.
  Con `?since=2030-01-01` la pagina entera muestra "Ninguna ronda con estos
  filtros." sin errores (la nota propia del panel queda en vitest).
- validate-data sobre la fila de `metricas.md`: winrate sobre decididas
  (`null` con 0, sin division por cero), `n` visible (Decididas), sin
  promedio de promedios; dos valores recalculados a mano (fila 0 33.3, fila 2
  50) iguales a la API.
- design-critique: el panel copia el patron de Prórroga por lado (Panel +
  DataTable + nota); nada que mandar a `ALCANCE.md`.

Skills del repo: accessibility-review (0 Critical, 0 Major, 0 Minor),
validate-data (2 valores recalculados, iguales), design-critique (sin
hallazgos).
OMC: plan=— · revisión=— · verificación=PASS (omc-verifier: 1, 2 y 3 PASS; 4 PARTIAL sin bloqueo: la nota propia del panel vacio solo en vitest, porque sin partidas la pagina entera muestra su aviso)


## Para el humano

(nada)
