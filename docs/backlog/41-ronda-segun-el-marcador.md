# 41. Rondas segun el marcador: adelante, empatado o atras

estado: entregado
candado: -
rama: claude/equipo-dev/41-ronda-segun-el-marcador
tipo: funcionalidad
epica: lado-y-marcador
area: fullstack
prioridad: 3
fuente: ALCANCE.md B2 (rondas bajo presion), primer tramo; el match point queda para el segundo
archivos: backend/replays/analytics/aggregates.py, backend/replays/views.py, backend/replays/management/commands/seed_demo.py, backend/tests/factories.py, frontend/src/pages/Trends.jsx, docs/metricas.md, backend/tests/test_marcador.py, frontend/e2e/humo.spec.js
turnos: po 20261013T1915Z, arquitecto 20261013T2011Z, dev 20261014T0111Z, revisor 20261014T0211Z, qa 20261014T0311Z, release 20261014T0411Z

## PR

**Titulo:** `[equipo-dev][fullstack] Rondas segun el marcador en Tendencias`

### Que cambia

Tendencias suma el panel "Según el marcador": como rindes en las rondas que
empezaste adelante, empatado o atras en el marcador (con CSV y aviso de
muestra chica). `/api/trends/` devuelve `by_score_state` con cuatro filas
fijas `ahead`, `tied`, `behind`, `unknown`.

### Por que esto y no otra cosa

Ficha 41, primer tramo de la epica `lado-y-marcador` (ALCANCE B2, rondas
bajo presion). Es la parte que no depende de las reglas de cada modo; match
point y ronda decisiva quedan para el segundo tramo.

### Como se probo

- `./scripts/check.sh` en `Todo en verde.` sobre la rama con `main` fusionado:
  512 tests backend (4 skipped), 69 frontend, build ok, 28 e2e.
- Tests nuevos (`backend/tests/test_marcador.py`): orden fijo de filas;
  0-0/1-0/1-1/1-2 desde tu lado; equipo 1 lee el marcador al reves; `[]`,
  `[1]`, `[1,2,3]` y equipo fuera de 0/1 van a sin marcador; replays antes
  de Y9S4 (que siempre traen 0-0) van a sin marcador y no a empate; la suma
  de filas es igual a las rondas de `/api/overview/`; base vacia y filtros
  raros dan 200. E2E `Tendencias muestra las rondas segun el marcador`.
- QA: con la semilla 87 adelante / 116 empatado / 0 atras / 0 sin marcador
  (203 rondas); mutacion de 4 puntos de `by_score_state`, todas caen; chunk
  inicial sin cambio (185503 bytes).

### Riesgos y lo que no entra

Sin migracion ni `recompute`: el estado se calcula al consultar desde
`Round.score_before` y `Match.code_version`, asi que bases ya importadas lo
ven sin reimportar. Replays anteriores a Y9S4 no traen el marcador real y
caen en "Sin marcador" (visible solo si tiene rondas). `seed_demo` ahora
llena `score_before` y `code_version=Y9S4`; ningun otro numero del seed
cambia. Fuera: match point y ronda decisiva.

### Como probarlo en 2 minutos

```
cd backend; python manage.py seed_demo; python manage.py runserver
```

Abrir `http://localhost:8000/tendencias`: panel "Según el marcador" con
"Adelante" y "Empatado" y sin fila "Sin marcador". En
`http://localhost:8000/api/trends/`, `by_score_state` trae 87 / 116 / 0 / 0.

### Para el humano

Nada. Con tu base real, si la mayoria de las rondas cae en "Sin marcador"
es porque son replays anteriores a Y9S4: es lo esperado.

### Candidatos descubiertos

Ninguno.

## Que gana quien usa la app

Ver como rindes segun como va la partida antes de la ronda: yendo adelante,
empatado o atras. Sirve igual en ranked, unranked o rapida.

## Diseno (resumen)

`aggregates.by_score_state` lee `score_before` (`[equipo0, equipo1]`) con
`KeyTransform` + `Cast`, lo orienta segun tu `team_index` y exige largo 2 y
`code_version >= Y9S4`; el resto va a `unknown`. Usa `_filas_por_tramo` y
`TablaDeCorte` de la ficha 39. Detalle en `git log` de la rama.

## Implementacion

(Dev 20261014T0111Z.) Todo el diseno, mas el filtro Y9S4 (desvio confirmado
por la revision: `pydissect/header.py:146` fuerza `startingScore = 0` antes
de Y9S4). `factories.make_match` acepta `code_version` (default Y9S4).

## Revision 2026-10-14 sobre 7838fdc

(Revisor 20261014T0211Z.) Sin hallazgos; cada criterio cubierto por un test
con nombre; desvio Y9S4 confirmado. Veredicto: aprobar.

## QA 2026-10-14 sobre 3d6efd0

(QA 20261014T0311Z.) check.sh verde; base vacia y filtros raros 200; semilla
87/116/0/0; bordes con `factories.py` correctos; suma igual al resumen;
pantalla limpia en Chromium; mutacion 4/4. Veredicto: aprobado.

## Para el humano

Nada por ahora.
