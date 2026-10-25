# 39. Inercia entre rondas: como juegas despues de ganar y despues de perder

estado: entregado
candado: -
rama: claude/equipo-dev/39-inercia-entre-rondas
tipo: funcionalidad
epica: lado-y-marcador
area: fullstack
prioridad: 2
fuente: ALCANCE.md B4 (idea del PO 20261013T0511Z); epica lado-y-marcador en curso (B1 en main por #25)
archivos: backend/replays/analytics/aggregates.py, backend/replays/views.py, frontend/src/muestra.js, frontend/src/muestra.test.js, frontend/src/pages/Trends.jsx, docs/metricas.md, backend/tests/test_ronda_anterior.py, frontend/e2e/humo.spec.js
turnos: po 20261013T1915Z, arquitecto 20261013T2011Z, dev 20261013T2112Z, revisor 20261013T2211Z, qa 20261013T2311Z, release 20261014T0012Z

## PR

Titulo: `[equipo-dev][fullstack] Inercia entre rondas en Tendencias`

### Que cambia

Tendencias suma el panel "Después de ganar o perder la ronda anterior": tu
winrate, rating, KPR y aperturas en las rondas que siguen a una ganada, a una
perdida y las que no tienen ronda anterior. Dice si una ronda perdida te
arrastra a la siguiente, un dato que solo sale del historial acumulado.

### Por que esto y no otra cosa

Ficha 39, tramo de la epica `lado-y-marcador` (idea B4 de `ALCANCE.md`).
Deja armados `_filas_por_tramo` y `TablaDeCorte` + `muestra.js`, que reusan
las fichas 41 (marcador) y 40 (hora y dia). Rachas de varias rondas quedan
fuera hasta ver si esta sirve.

### Como se probo

- `./scripts/check.sh`: 503 tests backend, 69 vitest, build ok, 27 e2e.
- `backend/tests/test_ronda_anterior.py`: orden fijo, ganar/perder, primera
  ronda y anterior faltante, anterior sin resultado, filtros de lado y de
  operador que no cambian la anterior, sin cruce entre partidas, suma igual a
  `overview`, base vacia y filtros raros con 200.
- `frontend/src/muestra.test.js`: aviso de muestra chica (menos de 30 rondas).
- e2e `Tendencias muestra la inercia entre rondas`: 0 % despues de ganar y
  100 % despues de perder con `seed_demo`.
- QA: base vacia y base sembrada a mano (2 / 1 / 4 esperado y obtenido),
  5 mutaciones que tumban los tests, chunk inicial sin cambio (185.47 kB).

### Riesgos y lo que no entra

Sin migracion ni `recompute`: la ronda anterior se calcula al consultar con
una subconsulta (es un corte, como el lado inicial de "Por mitad"). `by_half`
pasa a usar `_filas_por_tramo` con el mismo resultado. Fuera: rachas de
varias rondas, marcador antes de la ronda (ficha 41), cambios al Coach.

### Como probarlo en 2 minutos

```powershell
cd backend; python manage.py seed_demo; python manage.py runserver
curl -s localhost:8000/api/trends/ | python -m json.tool | Select-String -Context 0,3 by_previous_round
```

Abrir `http://localhost:8000/tendencias`: panel "Después de ganar o perder la
ronda anterior" con "Después de ganar" 0 % y "Después de perder" 100 %
(87 rondas cada una; `seed_demo` alterna).

### Para el humano

Nada que decidir. Aviso: el umbral de 30 rondas del aviso de muestra se
calibro con datos sinteticos; con la base real, mirar si sale siempre o nunca.

### Candidatos descubiertos

Ninguno (40 y 41 ya estan `disenado` en `backlog`).

## Que gana quien usa la app

Ver en Tendencias si una ronda perdida te arrastra a la siguiente: winrate y
rating en las rondas que vienen despues de ganar contra las que vienen
despues de perder.

## Criterios de aceptacion

- [x] `GET /api/trends/` devuelve `by_previous_round` con `after_win`,
      `after_loss`, `no_previous` en orden fijo y las metricas de `totals()`.
- [x] Primera ronda, anterior no importada o sin resultado van a
      `no_previous`; las tres filas suman `rounds` de `/api/overview/`.
- [x] La anterior se lee de la partida entera (`?side=` no la cambia).
- [x] Panel en Tendencias con CSV y aviso de muestra chica (< 30 rondas).
- [x] Fila en `docs/metricas.md`; e2e de Tendencias con consola limpia.
- [x] Base vacia y filtros raros: 200 con tres filas en 0.

## Diseno

(Arquitecto 20261013T2011Z.) `_filas_por_tramo` y `by_previous_round` en
`aggregates.py` con subconsulta `number - 1` sobre `Round`; clave en
`/api/trends/`; `TablaDeCorte` y `muestra.js` en el frontend; seccion
`## Contexto de la ronda` en `metricas.md`. Detalle completo en `git log`.

## Implementacion

(Dev 20261013T2112Z.) Diseno completo sin desvios de alcance, mas dos tests
extra (sin cruce entre partidas, API con datos). Desvio menor: la fila de
muestra minima dice solo "(ronda anterior)"; 40 y 41 la amplian.

## Revision 2026-10-13 sobre 5f23d8f

(Revisor 20261013T2211Z.) Ciega sin hallazgos; criterios cubiertos; agrego
`test_el_filtro_de_operador_no_cambia_la_ronda_anterior`. Veredicto: aprobar.

## QA 2026-10-13 sobre d2f1dc7

(QA 20261013T2311Z.) `check.sh` verde; base vacia y sembrada con resultados
iguales a lo esperado a mano; UI en Chromium sin errores; chunk inicial
igual; 5 mutaciones detectadas. Veredicto: aprobado.

## Release 2026-10-14

(Release 20261014T0012Z.) `origin/main` (5d2aecc) ya fusionado;
`check.sh` en `Todo en verde.` sobre la rama (503 backend, 69 vitest,
build ok, 27 e2e).

## Para el humano

Aviso: el umbral de 30 rondas se probo solo con datos sinteticos: calibrar
con la base real.
