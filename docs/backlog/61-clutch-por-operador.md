# 61. Clutch por operador

estado: entregado
candado: -
rama: claude/equipo-dev/61-clutch-por-operador
tipo: funcionalidad
epica: operadores
area: fullstack
prioridad: 3
fuente: ALCANCE.md O6 (siguiente tramo tras las fichas 55 y 59, ya en main)
archivos: backend/replays/analytics/aggregates.py, backend/replays/views.py, backend/tests/test_clutch.py, frontend/src/pages/Teammates.jsx, frontend/e2e/humo.spec.js, docs/metricas.md
turnos: po 20261024T1204Z, arquitecto 20261024T1605Z, dev 20261025T0004Z, revisor 20261025T0404Z, qa 20261026T0809Z, release 20261026T0809Z

## PR

Titulo: `[equipo-dev][fullstack] Clutch por operador en Compañeros`

### Que cambia

El panel "Clutches" de Compañeros suma la tabla "Clutch por operador":
cuantos clutches intentaste y ganaste con cada operador, separado por lado,
con un `*` en las filas de menos de 5 intentos y boton CSV
(`clutch-por-operador`). `/api/teammates/` trae la clave nueva
`clutch_by_operator`.

### Por que esto y no otra cosa

Ficha 61, tramo de la epica `operadores` (ALCANCE.md O6), despues de la
conversion de clutch (55) y el clutch por mapa y sitio (59). Es la misma
consulta que `clutch_by_site` con otro `values()`: sin migracion ni
columna nueva. Clutch por operador y mapa a la vez queda afuera: la muestra
no da.

### Como se probo

- `./scripts/check.sh` sobre la rama con `main` (19683ce) ya fusionado:
  `Todo en verde.` (770 tests backend, 120 frontend, build ok, 48 e2e).
- `ClutchPorOperadorTests` (7): filas por operador y lado, suma contra la
  conversion menos las rondas sin operador, borde `CLUTCH_OPERADOR_MIN - 1`
  / `CLUTCH_OPERADOR_MIN`, ronda sin ganador, fila sin lado (agregado por
  QA), filtro de lado por la API y base vacia.
- e2e `Compañeros muestra el clutch por operador`: 3 filas sobre
  `seed_demo`, `Rook Defensa 5 0 0%` sin `*` y Zofia Ataque 2 2 100% con `*`.
- QA: base vacia y sembrada, `curl` con `until=foo`, `page=-1`,
  `since` futuro, `side`, `map`, `operator`: cero 500, sumas cuadradas;
  CSV bajado en Chromium con el lado en texto; 4 mutaciones, todas caen.

### Riesgos y lo que no entra

Sin migracion, sin `recompute`, sin parser. Chunk inicial sin cambio
(187,83 kB); `Teammates` +0,95 kB, carga diferida. Fuera: "cuantos se
esperaban" (K3, depende de K1) y clutch por operador y mapa.

### Como probarlo en 2 minutos

```powershell
cd backend; python manage.py seed_demo --force; python manage.py runserver
```

Abrir http://127.0.0.1:8000/companeros, panel "Clutches": la tercera tabla
es "Clutch por operador" con Rook Defensa 5 0 0 %, Jager Defensa 3 0 0 % \*
y Zofia Ataque 2 2 100 % \*. El boton CSV de esa tabla baja
`clutch-por-operador-<fecha>.csv` con la columna Lado en texto. Con el
filtro Lado = Defensa en la barra quedan solo Rook y Jager.

### Para el humano

Calibrar con la base real el corte de muestra chica (`CLUTCH_OPERADOR_MIN = 5`).

### Candidatos descubiertos

Ninguno.

## Que gana quien usa la app

Hoy el panel "Clutches" dice cuantos clutches intentas y conviertes por 1vX
y por mapa y sitio, pero no con que operador. Esta tabla dice con cual
cierras las rondas que quedan en tus manos y con cual las sueltas, por lado.

## Criterios de aceptacion

- [x] `clutch_by_operator` en `/api/teammates/` con `operator`, `side`,
  `attempts`, `won`, `pct`, `low_sample`; mismo intento y ganado que
  `clutch_conversion`, suma igual menos las rondas sin operador (test).
- [x] Muestra chica con `CLUTCH_OPERADOR_MIN`, borde N-1 / N con test.
- [x] Respeta los filtros de la barra (test con `side=Attack`).
- [x] Base vacia: 200 y `[]`.
- [x] Tabla en Compañeros con `*`, orden por intentos y CSV; e2e.
- [x] Fila en `docs/metricas.md`.

## Diseno (resumen)

(arquitecto 20261024T1605Z) `clutch_by_site` con otro `values()`:
`base_queryset` filtrado por `clutch_vs > 0` y ganador conocido, sin
operador vacio, agrupado por operador y lado; filas sin lado Attack/Defense
afuera; orden `-attempts`, operador, lado. Tabla entre "por mapa y sitio" y
"Clutches ganados" para no mover los indices del e2e.

## Implementacion

(dev 20261025T0004Z) Diseno completo, sin desvios. `check.sh` en verde sobre
ff92c7d (769 tests, 120 vitest, e2e 48/48).

## Revision 2026-10-25 sobre ac5ce50

(revisor 20261025T0404Z) Rama fusionada con `origin/main`. Revision ciega
sin hallazgos; criterios y tests leidos contra el codigo; `check.sh` en
verde. Veredicto: aprobar.

## QA 2026-10-26 sobre f0a1bd3

(qa 20261026T0809Z) `check.sh` en verde; base vacia (8 combinaciones de
parametros borde: 200 y `[]`) y base sembrada (suma 10 = conversion 12 menos
sin operador y sin lado; sin ganador y `is_me=False` afuera; `side`, `map`,
`operator`, `since` futuro correctos; `until=foo` y `page=-1` sin 500).
UI en Chromium: filas, `*` y CSV con el lado en texto, consola limpia. Chunk
inicial sin cambio. Mutacion: sin el descarte de lados no caia ningun test;
agregado `test_una_fila_sin_lado_no_sale_por_operador`, que cae con ella.
El detalle de cada comando esta en el commit e32b9ad. Veredicto: aprobado.

## Para el humano

- Calibrar con la base real el corte `CLUTCH_OPERADOR_MIN = 5` (solo se
  probo con datos sinteticos).
