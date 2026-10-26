# 62. Cuando matas

estado: entregado
candado: -
rama: claude/equipo-dev/62-cuando-matas
tipo: funcionalidad
epica: lado-y-marcador
area: fullstack
prioridad: 3
fuente: ALCANCE.md B11 ([tracker.gg](https://tracker.gg/r6siege/articles/r6-ow-v3-0), "number of kills in the first 30 seconds")
archivos: backend/replays/analytics/aggregates.py, backend/replays/views.py, backend/tests/test_deaths.py, frontend/src/pages/Trends.jsx, frontend/e2e/humo.spec.js, docs/metricas.md
turnos: po 20261024T1204Z, arquitecto 20261024T1605Z, dev 20261026T1206Z, revisor 20261026T1605Z, qa 20261026T2004Z, release 20261026T2004Z

## PR

Titulo: `[equipo-dev][fullstack] Cuándo matas en Tendencias`

### Que cambia

Tendencias suma el panel "Cuándo matas", justo antes de "Cuando mueres": tus
bajas a rivales por tramos de 30 s de la fase de accion (el ultimo abierto en
150s+), apiladas por lado, con tabla y boton CSV (`cuando-matas`). Dice si tu
impacto esta en la apertura o en el cierre de la ronda. `/api/trends/` trae
la clave nueva `kills_by_time`.

### Por que esto y no otra cosa

Ficha 62, tramo de la epica `lado-y-marcador` (ALCANCE.md B11): el espejo de
"Cuando mueres". Se calcula al consultar desde el feed, como Duelos
(`RoundPlayer` no guarda el segundo de cada baja): sin migracion ni columna
nueva. Cruzarlo con el winrate o la primera baja es la ficha 63.

### Como se probo

- `./scripts/check.sh` sobre la rama con `main` (b3412cb) ya fusionado:
  `Todo en verde.` (780 tests backend, 120 frontend, build ok, 49 e2e).
- `CuandoMatasTests` (10): tramos 0-30/30-60/150s+, teamkill afuera, tus
  muertes no cuentan, suma igual a `duel_totals` sin filtro y con
  `side=Defense`, separacion por lado, ataque en 0 con `side=Defense`, base
  vacia y la API; QA sumo el lado leido de tu fila con el rival cargado
  primero y el porcentaje sobre el total.
- e2e `Tendencias muestra cuando matas`: 4 tramos sobre `seed_demo`, fila
  `90-120s 53 · 54% · 34 · 19` (99 bajas = Bajas de Duelos).
- QA: base vacia y base borde sembrada; `curl` con `until=foo`, `page=-1`,
  `side=`, `side=Bogus`, `since` futuro, `map`, `match_type`, nick
  repetido: cero 500 y sumas iguales a `/api/duels/`. 7 mutaciones, todas
  caen.

### Riesgos y lo que no entra

Sin migracion, sin `recompute`, sin parser. Chunk inicial sin cambio
(187,83 kB); `Trends` +1,1 kB, carga diferida. Una baja sin reloj
(`Event.elapsed = 0`) cae en 0-30s, igual que en "Cuando mueres". Fuera:
cruce con winrate y primera baja (ficha 63).

### Como probarlo en 2 minutos

```powershell
cd backend; python manage.py seed_demo --force; python manage.py runserver
```

Abrir http://127.0.0.1:8000/tendencias: el panel "Cuándo matas" esta justo
antes de "Cuando mueres", con 4 tramos de 30-60s a 120-150s; la fila 90-120s
dice 53 bajas, 54 %, 34 en ataque y 19 en defensa. Con Lado = Defensa en la
barra, la columna Ataque queda en 0 en todas las filas.

### Para el humano

Nada.

### Candidatos descubiertos

Ninguno.

## Que gana quien usa la app

En Tendencias ya esta "Cuando mueres"; falta el otro lado: en que momento de
la fase de accion sacas tus bajas. Dice si tu impacto esta en la apertura o
en el cierre de la ronda, y en defensa cuantas bajas tempranas consigues.

## Criterios de aceptacion

- [x] `kills_by_time` en `/api/trends/`: tramos de 30 s con el ultimo
  abierto en 150s+, con `start`, `end`, `label`, `kills`, `attack`,
  `defense` y `pct`; lado de tu fila `RoundPlayer` (tests).
- [x] Teamkills afuera (test).
- [x] Suma igual a las bajas de Duelos con los mismos filtros; `side=Defense`
  deja `attack` en 0 (tests).
- [x] Base vacia: 200 y `[]`.
- [x] Panel "Cuándo matas" al lado de "Cuando mueres"; e2e sobre `seed_demo`.
- [x] Fila en `docs/metricas.md`.

## Diseno (resumen)

(arquitecto 20261024T1605Z) Histograma de `deaths_by_time` alimentado por
las bajas a favor de `_duelos` (teamkills ya afuera), con el lado de tu
`RoundPlayer` por subquery; `_tramo_vacio` compartido sin cambiar la salida
de `deaths_by_time`. 63 toca el mismo panel: va despues de esta.

## Implementacion

(dev 20261026T1206Z) Diseno completo, sin desvios. `check.sh` en verde (778
tests backend, 120 frontend, build ok, 49 e2e).

## Revision 2026-10-26 sobre 9926b27

(revisor 20261026T1605Z) Revision ciega sin hallazgos; criterios contra el
codigo, numeros del e2e recalculados sobre `seed_demo`; mutaciones del tope
y del lado caen. Veredicto: aprobar.

## QA 2026-10-26 sobre b6a5cbb

(qa 20261026T2004Z) `check.sh` en verde; base vacia (3 combinaciones: 200 y
`[]`) y base borde (bajas a 10/45/200 s, teamkill, ronda sin bajas, nick
repetido): tramos y lados esperados, sumas iguales a `/api/duels/` con
`map`, `side` y `match_type`; bordes sin 500. Chunk inicial sin cambio.
Mutacion: `_pct` sobre total 1 y el lado leido de una fila ajena
sobrevivian a los unit tests (el segundo tambien al e2e); agregados
`test_el_lado_sale_de_tu_fila_aunque_el_rival_este_primero` y
`test_el_porcentaje_es_sobre_el_total_de_tramos`, que caen con ellas. El
detalle de cada comando esta en el commit f0e98b1. Veredicto: aprobado.
