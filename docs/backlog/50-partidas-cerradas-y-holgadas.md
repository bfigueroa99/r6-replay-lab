# 50. Partidas cerradas y partidas holgadas

estado: entregado
candado: -
rama: claude/equipo-dev/50-partidas-cerradas-y-holgadas
tipo: funcionalidad
epica: lado-y-marcador
area: fullstack
prioridad: 3
fuente: ALCANCE.md B10 ([aurelix](https://aurelix.app), tarjeta "Close games")
archivos: backend/replays/analytics/aggregates.py, backend/replays/views.py, backend/tests/test_margen.py, backend/tests/test_api.py, frontend/src/margen.js, frontend/src/margen.test.js, frontend/src/pages/Trends.jsx, frontend/e2e/humo.spec.js, docs/metricas.md
turnos: po 20261015T1711Z, arquitecto 20261015T1811Z, dev 20261015T2004Z, revisor 20261016T0004Z, dev 20261016T0404Z, revisor 20261016T0805Z, qa 20261016T1204Z, release 20261016T1604Z

## PR

Titulo: `[equipo-dev][fullstack] Partidas cerradas y partidas holgadas`

### Que cambia

Tendencias suma el panel "Partidas cerradas y holgadas": winrate de partida,
rating y KPR segun el margen final (prórroga, 1 ronda, 2 rondas, 3 o más).
Dice si cierras las partidas parejas o solo ganas las que vas sobrado.
`/api/trends/` trae la clave nueva `by_margin`.

### Por que esto y no otra cosa

Ficha 50, epica `lado-y-marcador` (ALCANCE.md B10, tarjeta "Close games" de
aurelix). Remontadas (ficha 45) mira la trayectoria; esto mira el margen
final. El margen sale de `Match.my_score/opponent_score`, ya resuelto a
tuyo/suyo, con el mismo corte `code_version >= Y9S4` que `comebacks`.

### Como se probo

- `./scripts/check.sh`: `Todo en verde.` (644 tests backend, 90 vitest, build ok, 38 e2e) sobre la rama con `origin/main` 2a6c86b fusionado.
- `tests/test_margen.py` (10): orden de tramos, prórroga antes que margen, Y9S3 fuera, empate y sin resultado fuera, `side` ignorado (incluida una partida solo de defensa), filtro de mapa, rating sobre todas tus rondas, base vacía; `test_api.test_trends_trae_by_margin`; `src/margen.test.js` (4); e2e `Tendencias muestra partidas cerradas y holgadas`.
- QA con base sembrada de 9 partidas (prórroga, Y9S3, empate, solo defensa): tramos correctos, `side` no cambia nada, filtros raros dan 200, sin 500; mutaciones en `aggregates.py` y `margen.js` hacen caer los tests que corresponden.

### Riesgos y lo que no entra

Sin migración, sin `recompute`, sin parser ni Electron. El chunk de Trends
crece 1.5 kB; el inicial no cambia. Fuera: margen por mapa o lado, CSV
dedicado, umbrales configurables.

### Como probarlo en 2 minutos

```
cd backend; python manage.py seed_demo; python manage.py runserver
```
Abrir `http://localhost:8000/tendencias`: debajo de "Remontadas y derrumbes"
aparece "Partidas cerradas y holgadas" con 4 filas; "1 ronda" tiene 29
partidas al 100 % (el demo gana todas 4-3).

### Para el humano

Nada. Aviso: `ingest.py` toma el marcador del último `.rec` importado; si
falta el de la ronda final, la partida cuenta como ganada por 1. Es el mismo
dato que ya usa toda la app; candidato a ficha `bug` aparte.

### Candidatos descubiertos

Ninguno (el aviso de arriba queda en ESTADO.md).

## Que gana quien usa la app

En Tendencias, tu winrate y rating en las partidas que se definieron por una
ronda o fueron a prorroga, contra las que se definieron por 3 o mas: si
cierras las parejas o solo ganas las que vas sobrado. Remontadas (ficha 45)
mira la trayectoria; esto mira el margen final.

## Criterios de aceptacion

- [x] `/api/trends/` trae una clave nueva (p. ej. `by_margin`) con tramos
      fijos: `prorroga`, `1 ronda`, `2 rondas`, `3 o mas`; cada uno con
      partidas, partidas ganadas, winrate de partida y rating (test).
- [x] El margen sale del marcador final (`Round.score_after` de la ultima
      ronda) con el mismo corte `code_version >= Y9S4` que `by_score_state`;
      las partidas anteriores o sin marcador no cuentan y la respuesta dice
      cuantas quedaron fuera (test con una partida Y9S3).
- [x] Una partida con `overtime_number` en alguna ronda cae en `prorroga`
      aunque el margen final sea 2 (test).
- [x] Los filtros de partida de siempre (mapa, `since`/`until`, ranked,
      sesion) recortan las partidas; `side` no parte una partida y se ignora.
      Base vacia devuelve 200 con los tramos en 0 (test).
- [x] Panel en `Trends.jsx` con la tabla y la banda de ruido como las demas
      tablas de partida; e2e en `frontend/e2e/` que lo ve con `seed_demo`.
- [x] Fila en `docs/metricas.md`.

## Fuera de alcance

- Margen por mapa o por lado.
- Exportarlo a CSV (H3 lo junta con las demas tablas nuevas).
- Umbrales configurables desde la UI.

## Diseno

(Arquitecto 20261015T1811Z) `aggregates.by_margin(**filters)` despues de
`comebacks()`: descarta `side`, elige partidas con `base_queryset`, separa las
conocidas (Y9S4+, con resultado), prórroga si alguna ronda tiene
`overtime_number > 0`, si no margen 1/2/3+; rating con `totals()` sobre todas
tus rondas de la partida. Vista `trends`, `margen.js`, panel en `Trends.jsx`,
fila **Margen final** en `docs/metricas.md`. Detalle en `git log`.

## Implementacion

(Dev 20261015T2004Z) Todo el diseño sin desvíos; `MUESTRA_PARTIDAS = 10`
exportado en `margen.js`. Revisión ciega previa con 3 menores corregidos.

## Revision

- 20261016T0004Z: corregir. [test] `test_el_filtro_de_lado_no_parte_la_partida`
  pasaba aunque no se descartara `side`. Corregido por el Dev 20261016T0404Z
  en 269f464 con `test_una_partida_solo_de_defensa_sigue_contando_con_filtro_de_ataque`
  (la mutación del revisor lo hace caer).
- 20261016T0805Z: aprobar, sin hallazgos.

## QA

(QA 20261016T1204Z sobre fc452e6) Aprobado: check.sh verde, base sembrada de
9 partidas con resultados esperados a mano, base vacía 200, UI en Chromium con
consola limpia, chunk inicial sin cambio, 5 mutaciones cazadas.
