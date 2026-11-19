# 135. Partida despues de perder seguido

estado: entregado
candado: -
rama: claude/equipo-dev/135-partida-despues-de-perder-seguido
tipo: funcionalidad
epica: progreso
area: backend
prioridad: 3
fuente: ALCANCE.md E6; el Coach ya aconseja "si son tres derrotas seguidas, corta la sesión" (`coach.py`, `_form`) sin mostrar el dato que lo respalda
archivos: backend/replays/analytics/aggregates.py, backend/replays/views.py, backend/tests/test_tras_derrotas.py, frontend/src/trasDerrotas.js, frontend/src/trasDerrotas.test.js, frontend/src/pages/Trends.jsx, frontend/e2e/humo.spec.js, docs/metricas.md
turnos: po 20261113T1954Z-cfZTvvE, arquitecto 20261114T0040Z-chQsvnq, dev 20261114T0040Z-c3LsMAo, revisor 20261114T0104Z-choi73m, qa 20261114T0104Z-cWK4yQD, release 20261114T0104Z-cWK4yQD

## PR

Titulo: `[equipo-dev][fullstack] Partida después de perder seguido en Tendencias`

### Que cambia

En Tendencias, debajo de *Curva de la sesión*, el panel **Después de perder
seguido**: tu winrate en la partida siguiente según cuántas derrotas seguidas
llevabas en esa sesión (0, 1, 2, 3 o más), con partidas y decididas por fila y
aviso de muestra chica. Es el dato que respalda (o no) el consejo del Coach de
cortar la sesión tras varias derrotas.

### Por que esto y no otra cosa

Ficha 135 (ALCANCE E6, épica progreso). Clave nueva en `/api/sessions/`, que
Tendencias ya pide, y no endpoint aparte. La racha se mide con todas las
partidas de la sesión y los filtros solo eligen cuáles se cuentan: si no, un
filtro de mapa inventaría rachas.

### Como se probo

- `check.sh` (con `verificar.sh`): VERDE 3ba2768, 1367 tests backend, 449 vitest, 120 e2e.
- Tests nuevos (`test_tras_derrotas.py`, 10): sesión D,D,V,D; la primera cae
  en 0; 3+ junta las de más; una sesión nueva reinicia; empate e incompleta no
  suman ni cortan ni entran al winrate; filtro de mapa cuenta solo esas con la
  racha de todas; lado, operador y sitio no cambian las filas; sin partidas, 4
  filas vacías; la API trae la clave; 3 consultas fijas. Vitest
  `trasDerrotas.test.js` (6) y e2e `Tendencias muestra la partida después de
  perder seguido`.
- QA: base sembrada desde `factories.py` con dos valores recalculados a mano
  iguales a la API, `curl` con filtros borde (mapa, lado, `until=foo`,
  `page=-1`, base vacía), 3 mutaciones muertas, Playwright (tabla, teclado,
  contraste 14.17:1 y 5.71:1, consola limpia), chunk inicial sin cambio.
- OMC: plan=— · revisión=— · verificación=— (diseno)
- OMC: plan=— · revisión=2 LOW (2 arreglados) · verificación=— (implementacion)
- OMC: plan=— · revisión=3 LOW (1 confirmado, 0 arreglados) · verificación=— (revision)
- OMC: plan=— · revisión=— · verificación=PASS (QA)
- Skills del repo: statistical-analysis, testing-strategy (diseno); test-driven-development, statistical-analysis, ux-copy (implementacion); ninguna (revision); accessibility-review, validate-data, design-critique (QA).

### Riesgos y lo que no entra

Sin migración ni `recompute`: se calcula al consultar sobre `Match`, con una
consulta más por request de `/api/sessions/`. Dos partidas con el mismo
`played_at` quedan en orden no garantizado (`_sessions_raw`, previo a este
cambio; arreglo barato: `order_by("played_at", "id")`). Fuera: minutos desde
la partida anterior, rachas entre sesiones, cambiar la señal del Coach.

### Como probarlo en 2 minutos

```
cd backend; python manage.py seed_demo; python manage.py runserver
```
Abrir `/tendencias`: panel *Después de perder seguido* con 4 filas; con
`seed_demo`, 29 partidas en "Sin derrotas antes" y el resto en 0 (el seed
separa sus partidas 3 h y las gana todas). Con datos reales, un filtro de mapa
cambia las partidas de cada fila pero ninguna salta de fila.

### Para el humano

Nada.

### Candidatos descubiertos

Ninguno.

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

(arquitecto 20261114T0040Z-chQsvnq) Detalle completo en `git log`.

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

Skills: no aplica (agregado y tabla en una pagina existente, con precedente `by_session_position`).
Skills del repo: statistical-analysis (winrate sobre decididas, `n` a la vista, corte de 10 reusado, sin promedio de promedios), testing-strategy (Django para la regla, vitest para el helper, e2e para el panel).
OMC: plan=— · revisión=— · verificación=—

## Implementacion

(dev 20261114T0040Z-c3LsMAo) El diseño completo: `by_losing_streak` en
`aggregates.py` (3 consultas fijas, siempre 4 filas), clave en
`/api/sessions/`, `trasDerrotas.js`, panel en `Trends.jsx`, e2e y fila en
`metricas.md`. Desvíos: el hint suma que lado, operador y sitio no aplican, y
un test extra para eso (revisión ciega). TDD con el rojo visto.

Skills: no aplica (agregado y tabla con precedente `by_session_position`).
OMC: plan=— · revisión=2 LOW (2 arreglados) · verificación=—

## Revision 2026-11-14 sobre ca7c9f5

(revisor 20261114T0104Z-choi73m) Aprobar -> `revisado`. Dos ejes a ciegas:
sin hallazgos que bloqueen; 1 LOW confirmado sin arreglar (el e2e no recorre
el aviso de muestra ni la nota sin partidas, cubiertos en vitest).
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
