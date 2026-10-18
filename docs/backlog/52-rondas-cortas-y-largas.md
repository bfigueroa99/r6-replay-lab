# 52. Rondas cortas y rondas largas

estado: entregado
candado: release 2026-10-18T08:04Z
rama: claude/equipo-dev/52-rondas-cortas-y-largas
tipo: funcionalidad
epica: lado-y-marcador
area: fullstack
prioridad: 3
fuente: ALCANCE.md B9 (y B12, que entra como columna de este tramo)
archivos: backend/replays/analytics/aggregates.py, backend/replays/views.py, backend/tests/factories.py, backend/tests/test_duracion.py, backend/tests/test_api.py, backend/tests/test_seed_demo.py, frontend/src/duracion.js, frontend/src/duracion.test.js, frontend/src/pages/Trends.jsx, frontend/e2e/humo.spec.js, docs/metricas.md, docs/formato-rec.md
turnos: po 20261017T1204Z, arquitecto 20261017T1603Z, dev 20261017T2004Z, revisor 20261018T0004Z, qa 20261018T0404Z, release 20261018T0804Z

## PR

Titulo: `[equipo-dev][fullstack] Rondas cortas y rondas largas`

### Que cambia

Tendencias suma el panel **Rondas cortas y largas**: tu winrate, rating y KPR segun cuanto
duro la fase de accion (0-45 s, 45-90 s, 90-135 s, 135 s o mas), por ataque, defensa y
total, y una tabla de cuanto tardas en ganar y en perder en cada lado. `/api/trends/` trae
la clave nueva `by_round_length`.

### Por que esto y no otra cosa

Ficha 52, tramo de la epica `lado-y-marcador` (ALCANCE.md B9 y B12). La duracion ya se
guardaba en cada `Round` y ningun agregado la usaba. Descartado: tramos configurables (sin
base real para calibrarlos), separar por condicion de victoria (ya lo hace "Como se cierran
tus rondas") y cualquier metrica sobre el plant inferido (CLAUDE.md).

### Como se probo

- `./scripts/check.sh`: Todo en verde (661 tests backend, 106 frontend, build ok, 40 e2e).
- `backend/tests/test_duracion.py` (15 tests: orden de tramos, bordes de 45 y 135 s, final
  del reloj, posible plant solo contado, reloj desconocido fuera, promedios, rondas sin
  ganador y sin lado, filtros de lado y mapa, base vacia); `test_trends_trae_by_round_length`;
  `test_todas_las_rondas_duran_lo_que_afirma_el_e2e`; `frontend/src/duracion.test.js` (7);
  e2e `Tendencias muestra rondas cortas y largas`.
- Revision a ciegas: aprobar. QA con base sembrada de 12 rondas borde y `curl` a
  `/api/trends/` con filtros (`side`, `map`, `since`, `session`, `days`, `until=foo`):
  todos los criterios con evidencia; mutacion sobre 4 tests de backend y 2 de vitest.

### Riesgos y lo que no entra

Sin migracion ni `recompute`: la duracion es `clock_start - clock_end`, dos columnas que ya
se guardan. `/api/trends/` suma ~14 consultas. Un plant seguido de barrida no se marca
`possible_plant` y cae en un tramo con la duracion hasta el plant (documentado en
`docs/metricas.md`). Fuera: tramos configurables, CSV dedicado, lectura del momento del plant.

### Como probarlo en 2 minutos

```
cd backend; python manage.py seed_demo; python manage.py runserver
curl -s localhost:8000/api/trends/ | python -m json.tool | grep -A40 by_round_length
```

Con `seed_demo` todo cae en `135+`: Ataque 116 rondas, Defensa 87, total 203. Abrir
Tendencias -> panel "Rondas cortas y largas", fila "135 s o más" con `100% (116)`, `0% (87)`,
`57% (203)`; bajar el CSV de las dos tablas.

### Para el humano

Avisos, no preguntas: los tramos de 45 s se probaron solo con datos sinteticos (calibrar con
la base real; es una constante). `rounds_won` de la fila `plant` sale 0 y no `null` (la UI no
lo muestra; cambio de una linea si se prefiere `null`).

### Candidatos descubiertos

Ninguno.

## Que gana quien usa la app

En Tendencias, tu winrate de ronda segun cuanto duro la fase de accion,
separado por lado: si en ataque solo ganas las ejecuciones rapidas o si en
defensa te quiebras cuando la ronda se alarga. Hoy la duracion solo aparece
como texto suelto en cada ronda del detalle (`MatchDetail.jsx:98`) y ningun
agregado la usa.

## Criterios de aceptacion

- [x] `/api/trends/` trae la clave nueva `by_round_length`: una fila por
      tramo fijo de duracion (`0-45 s`, `45-90 s`, `90-135 s`, `135 s o mas`)
      y una fila aparte `Posible plant`, cada una con `rounds`, `rounds_won`,
      `winrate`, `rating` y `kpr`, por lado (`Attack`, `Defense`) y total.
      Tramo con 0 rondas: fila con `rounds: 0` y `winrate: null`, no se omite.
- [x] La duracion es `Round.duration` (`clock_start - clock_end`). Una ronda
      con `possible_plant=True` cuenta solo en la fila `Posible plant` y en
      ningun tramo (despues del plant el reloj no mide la misma fase,
      `docs/formato-rec.md`); una ronda con `clock_start == 0` (reloj
      desconocido) no cuenta en ninguna fila. Test con una ronda de cada caso.
- [x] Los filtros de siempre (`map`, `side`, `since`/`until`, `ranked`,
      sesion) recortan la tabla igual que al resto de Tendencias; con base
      vacia la clave existe y todas las filas tienen `rounds: 0`.
- [x] Cada fila trae `avg_duration_won` y `avg_duration_lost` (segundos con
      un decimal, `null` sin rondas): cuanto tardas en ganar y en perder en
      ese lado (B12, sin separar por condicion de victoria).
- [x] Tendencias muestra el panel "Rondas cortas y largas" con los tramos
      en filas y ataque, defensa y total en columnas; el e2e
      (`frontend/e2e/`) lo encuentra con datos de `seed_demo` y la consola
      queda limpia. La logica de armado de la tabla vive en un modulo puro con
      su test de vitest.
- [x] `docs/metricas.md` tiene la fila **Duracion de la ronda** con los
      tramos, la exclusion de posible plant y de reloj desconocido.

## Fuera de alcance

- Tramos configurables desde la UI o el `.env`.
- Separar las rondas por condicion de victoria (eliminacion, objetivo,
  tiempo): `round_endings` ya lo hace por otro eje.
- Cualquier lectura del momento del plant: solo se infiere y no entra en
  metricas.
- CSV dedicado (va con H3 si alguien lo pide).

## Diseno

(Arquitecto 20261017T1603Z, sobre main 9e3d660; detalle completo en `git log`.)
`aggregates.by_round_length()` despues de `round_endings()`, forma `{rows, summary,
rounds_unknown_clock}`; fila `plant` solo con conteo; reloj desconocido = `clock_start <= 0`
o `clock_end <= 0`; panel en `Trends.jsx` despues de "Cómo se cierran tus rondas".

## Implementacion

(Dev 20261017T2004Z) Diseno completo. Desvio tecnico: la duracion va con `alias()` (una
anotacion entra al GROUP BY de `values("side")`) y los promedios arman su propia
`_duracion()` dentro de `Avg`. Test extra:
`test_un_clock_end_en_cero_con_inicio_cuenta_como_reloj_desconocido`.

## Revision 2026-10-18 sobre 7795ad2

(Revisor 20261018T0004Z) Veredicto: aprobar. Un hallazgo menor no bloqueante: `rounds_won`
de la fila `plant` en 0 en vez de `null` (lo pidio el diseno), pasado a `## Para el humano`.

## QA 2026-10-18 sobre 920bbdb

(QA 20261018T0404Z) `check.sh` en verde; chunk inicial sin cambio (186.78 kB); base
sembrada con 12 rondas borde, los 6 criterios con evidencia por `curl`; mutacion: caen los
tests de plant, borde de 45 s, rondas sin ganador y `clock_end=0`. Veredicto: `aprobado`.

## Para el humano

- Tramos de 45 s probados solo con datos sinteticos: calibrar con la base real (reversible).
- `rounds_won` de la fila `plant` sale 0 y no `null`; la UI no lo muestra.
