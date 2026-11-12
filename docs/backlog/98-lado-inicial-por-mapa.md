# 98. Lado inicial por mapa

estado: entregado
candado: -
rama: claude/equipo-dev/98-lado-inicial-por-mapa
tipo: funcionalidad
epica: lado-y-marcador
area: fullstack
prioridad: 3
fuente: B17 de ALCANCE.md; [Siege.GG, win probability](https://siege.gg/news/how-analysts-estimate-win-probability-in-pro-siege-matches) (2026-04-27: "A team starting on defense may carry a higher early probability simply because of the map's structure"); investigador 2026-11-03
archivos: backend/replays/analytics/aggregates.py (by_start_side_map, MIN_PARTIDAS_LADO_INICIAL), backend/replays/views.py (trends), backend/tests/test_mitades.py, frontend/src/ladoInicialMapa.js, frontend/src/ladoInicialMapa.test.js, frontend/src/pages/Trends.jsx, frontend/e2e/humo.spec.js, docs/metricas.md
turnos: po 20261106T0319Z-cqz8j6p, arquitecto 20261106T0345Z-cgK76Zp, dev 20261106T0411Z-cHA9KBb, revisor 20261106T0438Z-cWo3KEB, qa 20261106T0503Z-cNp9Adt, release 20261106T0503Z-cNp9Adt

## PR

Titulo: `[equipo-dev][fullstack] Lado inicial por mapa en Tendencias`

### Que cambia

Tendencias suma la tabla "Lado inicial por mapa": por cada version de mapa,
partidas y winrate arrancando en ataque y en defensa, la diferencia con su
margen de ruido y un veredicto ("Mejor arrancando en ataque", "Dentro del
ruido", "Poca muestra"). `GET /api/trends/` agrega `by_start_side_map`.

### Por que esto y no otra cosa

Ficha 98 (B17 de `ALCANCE.md`). El lado que conviene cambia por mapa y el
panel "Lado inicial" los juntaba. La banda usa la proporcion combinada de
los dos lados y no `_ruido` (Wald): con 3 a 5 partidas por lado un 100 % o un
0 % es lo normal y Wald daria veredicto por azar.

### Como se probo

- `check.sh` (con `verificar.sh`): VERDE 9b41bdaf2, 1077 tests backend, 262 vitest, 76 e2e.
- Tests nuevos: `LadoInicialPorMapaTests` en `test_mitades.py` (cuenta por
  mapa, lado bajo el minimo, `won=None`, filtro de lado y de mapa, versiones
  en filas distintas, veredicto y ruido), `ladoInicialMapa.test.js` (5) y el
  e2e de Tendencias (tabla, celda `Bank`, "Poca muestra").
- QA: runserver con base vacia y sembrada, bordes de filtros, 4 de 4
  mutaciones detectadas, chunk inicial sin cambio, Playwright sin errores.
- OMC: plan=— · revisión=3 hallazgos LOW (3 arreglados) · verificación=— (implementacion)
- OMC: plan=— · revisión=2 hallazgos LOW (0 arreglados) · verificación=— (revision)
- OMC: plan=— · revisión=— · verificación=PASS (QA)

### Riesgos y lo que no entra

Sin migracion ni `recompute`: se calcula al consultar. Fuera: lado inicial
por sitio u operador, llevarlo al Coach, cambiar `by_start_side`.

### Como probarlo en 2 minutos

```
cd backend; python manage.py seed_demo; python manage.py runserver
```

Tendencias, panel "Lado inicial": debajo de "Según el lado con que
arrancas", la tabla "Lado inicial por mapa" con Club House, Border y Bank,
defensa en "—" y veredicto "Poca muestra" (en `seed_demo` todas arrancan en
ataque). `curl -s localhost:8000/api/trends/` trae `by_start_side_map`.

### Para el humano

Calibrar con la base real el minimo de 3 partidas por lado. Aviso, no bloquea.

### Candidatos descubiertos

Ninguno.

## Que gana quien usa la app

Ver, mapa por mapa, si te va mejor arrancando en defensa o en ataque ("en
Bank gano mas arrancando en defensa"), con la muestra a la vista.

## Criterios de aceptacion

- [x] `by_start_side_map` por version de mapa, con `matches`, `decided`,
      `wins`, `winrate` por lado; `won=None` cuenta en partidas y no en el %.
- [x] Diferencia con banda de ruido; un lado bajo `MIN_PARTIDAS_LADO_INICIAL`
      (3) sale sin porcentaje ni veredicto.
- [x] Filtros como en `by_start_side`; el de lado no parte la partida.
- [x] Tabla en Tendencias con texto de vacio; e2e con consola limpia.
- [x] Fila en `docs/metricas.md`.

## Revision 2026-11-06 sobre a5d41f7

Revisor 20261106T0438Z-cWo3KEB: aprobar, sin CRITICAL, HIGH ni MEDIUM. Dos
LOW que no se arreglaron: el test del filtro de lado no cubre una partida
truncada de un solo lado (sale con `side=` del lado que no tiene, igual que
`by_start_side`), y `MIN_PARTIDAS_LADO` del frontend es un espejo literal del
backend sin test de paridad. El detalle esta en `git log`.

## QA 2026-11-06 sobre 9b41bdaf2

QA 20261106T0503Z-cNp9Adt: aprobado. Base vacia -> `[]`; base sembrada
desde `factories.py`: Bank 8-0 contra 0-8 -> `ataque`, margen 50.0; Oregon
3-1 contra 2-2 -> `ruido`, margen 68.4; `won=None` fuera del %; versiones
separadas; bordes (`until=foo`, `page=-1`, `map=`, `days` enorme) en 200.
Mutaciones 4 de 4. Chunk inicial 194.59 kB sin cambio. Comandos completos
en el commit `Prueba: 98 lado inicial por mapa`.

## Para el humano

- Calibrar con la base real el minimo de 3 partidas por lado
  (`MIN_PARTIDAS_LADO_INICIAL`). Aviso, no bloquea.
