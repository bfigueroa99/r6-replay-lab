# 60. Racha de rondas dentro de la partida

estado: entregado
candado: -
rama: claude/equipo-dev/60-racha-de-rondas
tipo: funcionalidad
epica: lado-y-marcador
area: fullstack
prioridad: 3
fuente: ALCANCE.md B13
archivos: backend/replays/analytics/aggregates.py, backend/replays/views.py, backend/tests/test_rachas.py, frontend/src/rachas.js, frontend/src/rachas.test.js, frontend/src/records.js, frontend/src/records.test.js, frontend/src/pages/MatchDetail.jsx, frontend/e2e/humo.spec.js, docs/metricas.md
turnos: po 20261019T0325Z, arquitecto 20261019T0404Z, dev 20261021T0404Z, revisor 20261021T0804Z, qa 20261021T1204Z, dev 20261021T1605Z, revisor 20261021T2004Z, qa 20261022T0004Z, release 20261022T0403Z

## PR

Titulo: `[equipo-dev][fullstack] Racha de rondas en el detalle de partida y en Records`

### Que cambia

El detalle de cada partida muestra, debajo del titulo, la racha mas larga de
rondas ganadas y la de perdidas seguidas ("Racha: 4 ganadas desde R3 · 3
perdidas desde R8"). Tus records suman "Racha de rondas": la racha de rondas
ganadas mas larga de tu historial filtrado, con enlace a la partida.
`/api/matches/<id>/` trae `round_streaks` y `personal_records` trae
`longest_round_streak`.

### Por que esto y no otra cosa

Ficha 60, tramo de la epica `lado-y-marcador` (ALCANCE.md B13). Se arma al
consultar sobre `Round.my_team_won`, sin migracion. La racha de partidas
queda afuera: la tiene PR #14.

### Como se probo

- `./scripts/check.sh` sobre la rama con `main` (44c525b) ya fusionado:
  `Todo en verde.` (733 tests backend, 120 frontend, build ok, 44 e2e).
- `backend/tests/test_rachas.py` (12): `G G P G G G`, hueco y ronda sin
  resultado cortan, empate gana la primera, vacio, orden de entrada; API con
  `losses` nulo; record con dos partidas, desempate por fecha, sin ganadas y
  filtro de lado. `rachas.test.js` (singular, una nula, las dos nulas) y
  `records.test.js` (clave nueva y "desde R<n>").
- e2e: el detalle afirma "Racha: 1 ganada desde R1 · 1 perdida desde R2" y
  el Resumen la fila "Racha de rondas".
- QA: dos pasadas con base sembrada y vacia, `curl` con filtros borde, cero
  500; 8 mutaciones, todas caen; el e2e de records 10 de 10 en verde.

### Riesgos y lo que no entra

Sin migracion, sin `recompute`, sin parser. Chunk inicial +0,1 % (187,63 ->
187,83 kB). Fuera: racha de partidas (PR #14), rachas de compañeros o
rivales, prorroga aparte.

### Como probarlo en 2 minutos

```powershell
cd backend; python manage.py seed_demo --force; python manage.py runserver
```

Abrir cualquier partida en http://127.0.0.1:8000: debajo del titulo "Racha:
1 ganada desde R1 · 1 perdida desde R2" (el seed alterna el resultado). En el
Resumen, "Tus records" muestra "Racha de rondas: 1 ronda ganada".

### Para el humano

Nada.

### Candidatos descubiertos

Ninguno.

## Que gana quien usa la app

Un 0-4 seguido dice mas que el 3-4 final: en el detalle de cada partida se
ve la racha mas larga de rondas ganadas y la de perdidas, y en Records tu
mejor racha de rondas del historial con enlace a la partida.

## Criterios de aceptacion

- [x] `rachas_de_rondas` pura en `aggregates.py`; cortan una ronda nula y un
  hueco en la numeracion.
- [x] `/api/matches/<id>/` con `round_streaks` (`{length, from_round_label}`
  o `null`).
- [x] `personal_records.longest_round_streak`; a igual largo, la mas reciente.
- [x] UI en el detalle de partida y en Records, con e2e.
- [x] Fila "Racha de rondas" en `docs/metricas.md`.

## Diseno

Arquitecto 20261019T0404Z: funcion pura que ordena por `number`, sigue la
racha mientras el resultado se repite y el numero es el anterior + 1; vista
con `_racha_con_etiqueta`; record sobre todas las rondas de las partidas
filtradas (el filtro elige partidas, no rondas). Detalle completo en `git log`.

## Implementacion

Dev 20261021T0404Z segun el diseno, sin desvios; `test_records.py` suma la
clave nueva en el test de base vacia. Dev 20261021T1605Z corrigio el e2e
inestable de records (la fila se afirma antes del clic, sin segundo
`page.goto`) y el texto "desde R<n>" del record.

## Revision

Revisor 20261021T0804Z: aprobar, con un hallazgo menor ("ronda R3" vs "desde
R3"). Revisor 20261021T2004Z sobre 0611577: aprobar; los dos hallazgos
(menor y el e2e de QA) resueltos.

## QA

QA 20261021T1204Z: con hallazgos (e2e inestable, 8 de 16 fallaban). QA
20261022T0004Z sobre 6bca783: aprobado; 10 de 10 en verde, `curl` sobre base
sembrada y vacia sin 500, 4 mutaciones caen. Sin `## Verificar en el PC`.
