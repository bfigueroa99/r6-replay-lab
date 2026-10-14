# 42. Como se cierran tus rondas: por eliminacion o sin ella, por lado

estado: entregado
candado: -
rama: claude/equipo-dev/42-como-se-cierran-tus-rondas
tipo: funcionalidad
epica: lado-y-marcador
area: fullstack
prioridad: 3
fuente: ALCANCE.md B6 (idea del PO 20261013T0511Z); epica lado-y-marcador en curso (B1, B4 y B2 tramo 1 en main por #25, 39 y 41)
archivos: backend/replays/analytics/aggregates.py, backend/replays/views.py, backend/tests/test_cierres.py, frontend/src/pages/Trends.jsx, frontend/src/cierres.js, frontend/src/cierres.test.js, frontend/e2e/humo.spec.js, docs/metricas.md
turnos: po 20261014T0911Z, arquitecto 20261014T1012Z, dev 20261014T1115Z, revisor 20261014T1211Z, qa 20261014T1312Z, release 20261014T1411Z

## PR

Titulo: `[equipo-dev][fullstack] Como se cierran tus rondas, por lado, en Tendencias`

### Que cambia

Tendencias suma el panel **"Cómo se cierran tus rondas"**: por lado, que parte
de tus rondas ganadas y perdidas terminan por eliminacion y cuantas sin ella
(objetivo o tiempo, inferido), mas las rondas sin dato. Sirve para ver si en
defensa pierdes porque te quedas sin gente o porque no llegas a tiempo; hasta
ahora la condicion solo se veia ronda por ronda en el detalle de una partida.

### Por que esto y no otra cosa

Ficha 42, tramo B6 de la epica `lado-y-marcador` (`ALCANCE.md`). Lee
`Round.win_condition` y `Round.my_team_won`, que la ingesta ya guarda: sin
migracion ni `recompute`. Descartado: partir "sin eliminacion" en plant,
defuse o tiempo (el `.rec` de temporadas nuevas no lo trae); contar con
`RoundPlayer.won` (manda las rondas sin ganador a perdidas).

### Como se probo

- `./scripts/check.sh` sobre la rama al dia con main 3438ab2: ruff, 529 tests
  backend, 75 vitest, build, 30 e2e. `Todo en verde.`
- Tests nuevos: `backend/tests/test_cierres.py` (9: ronda ganada por
  eliminacion suma solo ahi, dos filas en orden fijo, ganada y perdida sin
  eliminacion, sin ganador o sin condicion a `unknown`, cada fila suma sus
  rondas, sin claves de plant ni defuse, filtro de mapa, porcentajes nulos sin
  dato, base vacia y filtros raros dan 200); `frontend/src/cierres.test.js`
  (6, incluido que los enteros en pantalla suman 100 aunque el porcentaje
  termine en ,5); e2e `Tendencias muestra como se cierran tus rondas`.
- QA con base sembrada a mano: los numeros de la API y de la tabla coinciden
  con lo sembrado bajo todos los filtros; mutaciones del agregado y de
  `cierres.js` hacen caer los tests.

### Riesgos y lo que no entra

`/api/trends/` crece con la clave `round_endings`; nada mas la consume. Sin
migracion, parser ni Electron. El panel vive en el chunk perezoso de
Tendencias (14,6 -> 16,6 kB); el chunk inicial no cambia. Fuera: separar
plant/defuse/tiempo, una tabla mapa x lado.

### Como probarlo en 2 minutos

```powershell
cd backend; python manage.py seed_demo; python manage.py runserver
```

Abrir `http://127.0.0.1:8000/tendencias`: despues de "Según el marcador"
aparece "Cómo se cierran tus rondas" con Ataque y Defensa (con `seed_demo`,
todo por eliminacion). Con tu base real, Defensa deberia mostrar perdidas sin
eliminacion (rondas perdidas por plant). Pasar el mouse sobre "sin
eliminación" muestra la aclaracion de que es inferido.

### Para el humano

Nada.

### Candidatos descubiertos

Ninguno.

## Que gana quien usa la app

Ver, por lado, cuantas de tus rondas ganadas y perdidas se cierran eliminando
al otro equipo y cuantas sin eliminacion (objetivo o tiempo).

## Criterios de aceptacion

- [x] `round_endings` en `/api/trends/` con una fila por lado y las cinco cuentas.
- [x] Cada fila suma sus rondas; `""` y `my_team_won` nulo a `unknown`.
- [x] Sin claves de plant ni defuse; la UI lo rotula como inferido.
- [x] Respeta `map`, `operator`, `side`, `since`, `match_type`, `session`.
- [x] Panel en Tendencias con banda de muestra chica; e2e en verde.
- [x] Fila en `docs/metricas.md`.

## Revision y QA (condensado; el detalle en `git log`)

- Revision (20261014T1211Z, sobre 3b0d7df): sin hallazgos en la revision
  ciega; la revision previa del Dev corrigio el 101 % en pantalla, el CSV sin
  conteos y lineas en blanco. Veredicto: `revisado`.
- QA (20261014T1312Z, sobre 00b6007): criterios verificados con base
  sembrada, API y Chromium; mutantes caen salvo uno equivalente. Veredicto:
  `aprobado`.

## Para el humano
