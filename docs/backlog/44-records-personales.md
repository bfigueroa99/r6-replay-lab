# 44. Records personales en el Resumen

estado: entregado
candado: -
rama: claude/equipo-dev/44-records-personales
tipo: funcionalidad
epica: progreso
area: fullstack
prioridad: 3
fuente: ALCANCE.md E4 (idea del PO 20261013T1915Z); epica progreso en curso (E3 en main por la ficha 40)
archivos: backend/replays/analytics/aggregates.py, backend/replays/views.py, backend/tests/test_records.py, frontend/src/pages/Dashboard.jsx, frontend/src/records.js, frontend/src/records.test.js, frontend/e2e/humo.spec.js, docs/metricas.md
turnos: po 20261014T0911Z, arquitecto 20261014T1012Z, dev 20261014T1115Z, revisor 20261014T1211Z, qa 20261014T1312Z, release 20261014T1411Z

## PR

Titulo: `[equipo-dev][fullstack] Tus records en el Resumen`

### Que cambia

El Resumen suma el panel **"Tus récords"**: tu mejor partida por rating, mas
bajas en una partida y en una ronda, el clutch mas grande y el mejor dia por
winrate, cada uno con un enlace para volver a mirar esa partida. Marca el
techo a superar y saca provecho del historial acumulado ronda por ronda.

### Por que esto y no otra cosa

Ficha 44, tramo E4 de la epica `progreso` (`ALCANCE.md`). Agrega columnas que
`metrics.py` ya escribe en `RoundPlayer` y `Match`: sin migracion ni
`recompute`. Va en `/api/overview/` (clave `records`) calculado en la vista,
para que el coach no pague las consultas. Descartado: la racha actual (es del
PR #14) e historial de cuando se batio cada record.

### Como se probo

- `./scripts/check.sh` sobre la rama con main fusionado (ya trae la ficha 42):
  ruff, 541 tests backend, 80 vitest, build, 31 e2e. `Todo en verde.`
- Tests nuevos: `backend/tests/test_records.py` (12: cada record con su
  `match_id`, empate a la partida mas reciente, filtro de mapa, minimos de 6
  rondas por partida y 20 por dia, clutch solo ganado, nulos sin candidato y
  sin bajas, base vacia y filtros raros dan 200); `frontend/src/records.test.js`
  (5); e2e `el Resumen muestra tus records y enlaza a la partida`, reforzado
  por QA para exigir el id exacto de la partida del record.
- QA con base sembrada a mano: los cinco records coinciden con el calculo a
  mano bajo todos los filtros; las mutaciones del agregado y del enlace caen.

### Riesgos y lo que no entra

`/api/overview/` con 2.000 partidas sinteticas tarda ~0,29 s (los records
suman ~0,16 s). Chunk inicial +0,7 % (185,47 -> 186,80 kB). Sin migracion,
parser ni Electron. Fuera: racha, historial de records, records de otros.

### Como probarlo en 2 minutos

```powershell
cd backend; python manage.py seed_demo; python manage.py runserver
```

Abrir `http://127.0.0.1:8000/`: debajo de "Ultimas partidas" aparece "Tus
récords" con cinco filas. Clic en el enlace de "Más bajas en una partida"
lleva al detalle de esa partida. Con filtros (mapa, lado) los records cambian.

### Para el humano

- Los minimos (6 rondas por partida, 20 por dia) son a ojo y se probaron con
  datos sinteticos: si con tu base real el mejor dia o la mejor partida se ven
  raros, se calibran.
- Si el Resumen se siente lento con tu base, los records pueden ir a su
  propia request.

### Candidatos descubiertos

Ninguno.

## Que gana quien usa la app

Ver de un vistazo tus mejores marcas, cada una con un enlace para volver a
mirarla.

## Criterios de aceptacion

- [x] Agregado `personal_records` en `/api/overview/` con los cinco records.
- [x] Empates: gana la partida mas reciente.
- [x] Respeta los filtros de siempre.
- [x] Base vacia o sin candidato: `null`, sin 500.
- [x] Panel "Tus récords" con enlaces; e2e en verde.
- [x] Seccion `## Records` en `docs/metricas.md`.

## Revision y QA (condensado; el detalle en `git log`)

- Revision (20261014T1211Z, sobre 1f48922): sin bugs; dos menores. El e2e que
  no afirmaba la partida correcta lo reforzo QA; la seccion `## Records` mal
  ubicada en `metricas.md` la movio el Release al armar el PR. Veredicto:
  `revisado`.
- QA (20261014T1312Z, sobre af000a3): criterios verificados con base
  sembrada; las cinco mutaciones del agregado caen; rendimiento medido.
  Veredicto: `aprobado`.

## Para el humano

- Umbrales a ojo (6 rondas por partida, 20 por dia): calibrar con la base real
  (aviso, no bloquea).
- Si `/api/overview/` se siente lento con la base real, mover los records a
  su propia request (aviso, no bloquea).
