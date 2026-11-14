# 135. Partida despues de perder seguido

estado: en curso 2026-11-14T00:57Z
candado: dev 2026-11-14T00:57Z
rama: claude/equipo-dev/135-partida-despues-de-perder-seguido
tipo: funcionalidad
epica: progreso
area: backend
prioridad: 3
fuente: ALCANCE.md E6; el Coach ya aconseja "si son tres derrotas seguidas, corta la sesión" (`coach.py`, `_form`) sin mostrar el dato que lo respalda
archivos: backend/replays/analytics/aggregates.py, backend/replays/views.py, backend/tests/test_tras_derrotas.py, frontend/src/trasDerrotas.js, frontend/src/trasDerrotas.test.js, frontend/src/pages/Trends.jsx, frontend/e2e/humo.spec.js, docs/metricas.md
turnos: po 20261113T1954Z-cfZTvvE, arquitecto 20261114T0040Z-chQsvnq, dev 20261114T0040Z-c3LsMAo

## PR

## Que gana quien usa la app

En Tendencias, tu winrate en la partida siguiente segun cuantas derrotas
seguidas llevabas en la sesion (0, 1, 2, 3 o mas): saber con tus propios
numeros si conviene cortar despues de dos derrotas, que hoy el Coach dice
como regla general.

## Criterios de aceptacion

- [ ] Un agregado ordena las partidas de cada sesion (el corte de sesion
      que ya usan `sessions` y `by_session_position`) y devuelve, por
      derrotas seguidas previas en esa sesion (0, 1, 2, 3+), `matches`,
      `wins` y `winrate` de la partida siguiente. La primera partida de la
      sesion cae en 0. Test con una sesion D, D, V, D.
- [ ] Una partida con `won` nulo o empatada no suma ni corta la racha y
      no entra al winrate de su fila (como `match_result`). Test.
- [ ] Los filtros globales aplican a la partida que se cuenta; la racha
      previa se mide sobre todas las partidas de la sesion, sin filtros
      (si no, un filtro de mapa inventaria rachas). Test con filtro de mapa.
- [ ] Panel en Tendencias cerca de "Curva de la sesión", con su `n` por
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

## Revision

## QA

## Para el humano

(nada)
