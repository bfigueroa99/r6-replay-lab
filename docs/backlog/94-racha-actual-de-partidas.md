# 94. Racha actual de partidas

estado: entregado
candado: -
rama: claude/equipo-dev/94-racha-actual-de-partidas
tipo: funcionalidad
epica: progreso
area: fullstack
prioridad: 3
fuente: E14 de ALCANCE.md (salio del PR #14, cerrado sin merge el 2026-11-05; la rama `claude/dazzling-einstein-w3qcyq` sirve de referencia)
archivos: backend/replays/analytics/aggregates.py, frontend/src/rachas.js, frontend/src/rachas.test.js, frontend/src/pages/Dashboard.jsx, backend/tests/test_racha_actual.py, frontend/e2e/humo.spec.js, docs/metricas.md
turnos: po 20261105T1945Z-cvqUYh1, arquitecto 20261106T0015Z-cR6uHk3, dev 20261106T0041Z-cJuLRWM, revisor 20261106T0109Z-cGwrEvi, qa 20261106T0135Z-cJAGtBp, release 20261106T0135Z-cJAGtBp

## PR

Titulo: `[equipo-dev][backend] Racha actual de partidas en el Inicio`

### Que cambia

En el Inicio, panel Últimas partidas, una linea dice cuantas partidas seguidas
llevas ganando o perdiendo ahora ("Racha actual: 3 victorias seguidas desde
2026-11-05", "Racha actual: 1 derrota (2026-11-05)"). Sale de
`matches_summary.current_streak` de `/api/overview/`, sobre las partidas del
filtro sin el lado; las partidas sin resultado (`won` nulo) no cortan ni suman.

### Por que esto y no otra cosa

Ficha 94, idea E14 de `ALCANCE.md` (salio del PR #14, cerrado sin merge). La
rama de ese PR no se reuso: es anterior a `won=None` (ficha 68) y a
`matches_summary`. Una racha que respete el lado partiria partidas: se
descarto, como en Partidas ganadas.

### Como se probo

- `check.sh` (con `verificar.sh`): VERDE sobre el commit de entrega (ver QA de
  la ficha; 1011 tests backend, 215 vitest, 67 e2e).
- Tests nuevos (`backend/tests/test_racha_actual.py`, 11): racha nula sin
  partidas o solo sin resultado; tres ganadas al final; G, None, G da 2; las
  sin resultado no entran en `match_ids`; la ultima perdida da 1 derrota; el
  filtro de mapa cambia la racha; el lado no parte la partida; la API la trae.
  Vitest (`rachas.test.js`, 5): nula sin texto, singular y plural de victoria y
  derrota. e2e `humo.spec.js`: "29 victorias seguidas desde 2026-08-01".
- QA: `curl` con base vacia y sembrada (filtros de mapa, lado, `until=foo`,
  `page=-1`, `days` borde), UI en Chromium con el selector de mapa (singular y
  plural, consola limpia), chunk inicial +655 B (+0,3 %), 7 mutaciones que caen.
- OMC: plan=— (ficha chica, una forma obvia) · revisión=— · verificación=—
- OMC: plan=— · revisión=0 hallazgos (0 arreglados) · verificación=— (implementacion)
- OMC: plan=— · revisión=0 hallazgos (0 arreglados) · verificación=— (revision)
- OMC: plan=— · revisión=— · verificación=PASS (omc-verifier, 6/6 VERIFIED)

### Riesgos y lo que no entra

Sin migracion, `recompute` ni parser: una clave mas en `matches_summary`. Con
filtro de lado, los puntos de la forma reciente (que si usan el lado) pueden no
coincidir con la racha; es a proposito y esta en `metricas.md`. Fuera: racha
mas larga (E4) y señal del Coach (E6).

### Como probarlo en 2 minutos

```powershell
cd backend; python manage.py seed_demo; python manage.py runserver
```

Abrir http://127.0.0.1:8000/ : en Últimas partidas, "Racha actual: 29
victorias seguidas desde 2026-08-01". Con la base real: la racha coincide con
los ultimos puntos de la forma reciente (sin filtro de lado) y un filtro de
mapa la cambia.

### Para el humano

Nada.

### Candidatos descubiertos

Ninguno.

## Que gana quien usa la app

En el Inicio, cuantas partidas seguidas llevas ganando o perdiendo ahora
("3 victorias seguidas", "2 derrotas seguidas"), al lado de la forma
reciente: saber de un vistazo si conviene seguir jugando o cortar. Hoy hay
que contar los puntos de la forma reciente a mano, y solo se ven 10.

## Criterios de aceptacion

- [x] `GET /api/overview/` trae en `matches_summary` una clave
      `current_streak`: `{"result": "win"|"loss", "length": n, "since": <fecha
      de la primera partida de la racha>, "match_ids": [...]}`, o `null` si no
      hay ninguna partida decidida.
- [x] Orden por `played_at` y `id` (igual que `matches_summary`); las
      partidas con `won=None` (incompletas o empate, ficha 68) no cortan ni
      suman la racha: test con G, None, G -> racha de 2 victorias.
- [x] Se calcula sobre las partidas del filtro, como el resto de
      `matches_summary` (el lado no parte una partida): test con filtro de
      mapa que cambia la racha.
- [x] Una racha de 1 se muestra igual ("1 victoria"); singular y plural
      correctos en la UI.
- [x] El Inicio muestra la racha junto a la forma reciente, sin renderizar
      nada con `current_streak: null`; e2e con el numero que fija
      `seed_demo`.
- [x] Fila nueva en `docs/metricas.md`.

## Fuera de alcance

- La racha mas larga de partidas (record): otra idea, junto a los records (E4).
- Racha de rondas (ya existe, ficha 60).
- Señal del Coach sobre la racha (E6 cubre "despues de perder seguido").

## Diseno

(arquitecto 20261106T0015Z-cR6uHk3) Funcion pura `racha_actual_de_partidas`
en `aggregates.py` que recorre desde la ultima las filas de `matches_summary`
(orden `played_at`, `id`, filtro sin lado), salta las `won=None` y corta en el
primer resultado distinto; clave `current_streak` en `matches_summary`;
`textoRachaActual` en `rachas.js`; `.racha-actual` en el panel Últimas
partidas de `Dashboard.jsx`; fila en `metricas.md` (`## Base`). Detalle en
`git log` de esta ficha.

## Implementacion

(dev 20261106T0041Z-cJuLRWM) El diseno completo, sin desvios. VERDE 692b47fb3.
OMC: plan=— · revisión=0 hallazgos (0 arreglados) · verificación=—

## Revision 2026-11-06 sobre 24c968d

(revisor 20261106T0109Z-cGwrEvi) Aprobar, sin hallazgos; los seis criterios
cubiertos por tests. VERDE 6f70db827.
OMC: plan=— · revisión=0 hallazgos (0 arreglados) · verificación=—

## QA 2026-11-06 sobre 46f257a

(qa 20261106T0135Z-cJAGtBp) VERDE 46f257a92 (1011/215/67). `curl` a
`/api/overview/` con base vacia (`null`) y sembrada con `factories.py` (P, G,
sin resultado, G, G y una sin rondas): win 3 `[2, 4, 5]`; `?map=club-house`
win 2; `?map=border` win 1; `?side=Attack|Defense` igual a sin filtro;
`?map=oregon`, `?since=2099-01-01`, `?days=-1` `null`; `until=foo`, `page=-1`
200. UI en Chromium: nada con base vacia, singular y plural con el selector de
mapa, consola limpia. Chunk inicial +655 B. Mutaciones: 7 de 7 caen. Sin
"Verificar en el PC". Veredicto: `aprobado`.
OMC: plan=— · revisión=— · verificación=PASS (omc-verifier, 6/6 VERIFIED)

## Release

(release 20261106T0135Z-cJAGtBp, mismo turno que la QA) Puerta de merge: ver `ESTADO.md`.

## Pendiente

## Para el humano
