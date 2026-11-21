# 138. El sitio con el que abres la defensa

estado: entregado
candado: -
rama: claude/equipo-dev/138-el-sitio-con-el-que-abres-la-defensa
tipo: funcionalidad
epica: posicionamiento
area: fullstack
prioridad: 3
fuente: ALCANCE.md S7
archivos: backend/replays/analytics/aggregates.py, backend/replays/views.py, backend/replays/urls.py, backend/tests/test_apertura_defensa.py, frontend/src/aperturaDefensa.js, frontend/src/aperturaDefensa.test.js, frontend/src/pages/Coach.jsx, frontend/e2e/humo.spec.js, docs/metricas.md
turnos: po 20261113T2157Z-cG2vDSe, arquitecto 20261114T0040Z-c3LsMAo, dev 20261115T0219Z-i32143169, revisor 20261118T1211Z-cMNRUxv, qa 20261121T0136Z-s7f07u7, release 20261121T0136Z-s7f07u7

## PR

Titulo: `[equipo-dev][fullstack] El sitio con el que abres la defensa, en el Coach`

### Que cambia

En el Coach, debajo de *Repetir el sitio tras perderlo*, el panel **El
sitio con el que abres la defensa**: por mapa (con su versión) y sitio,
cuántas partidas abriste la defensa ahí y qué parte de las aperturas del
mapa son, el winrate de esa primera ronda de defensa y, al lado, el mismo
sitio en el resto de tus rondas de defensa. Dice si tu apertura en defensa
es predecible y si arrancar ahí te cuesta.

### Por que esto y no otra cosa

Ficha 138 (ALCANCE S7, épica posicionamiento). Sale del sitio de bomba y
el lado de `Round`, que el `.rec` entrega; se calcula al consultar como su
vecino `site_after_loss` (sin migración, sin `recompute`, sin POST), con
`GET /api/positioning/defense-opener/`. Una partida solo aporta apertura si
se sabe que fue su primera defensa (sin huecos ni rondas sin lado antes, y
con sitio); si no, sus defensas van al resto y se cuentan aparte. Sin
veredicto contra el resto: con 5 a 20 aperturas la diferencia es ruido.

### Como se probo

- `check.sh` (con `verificar.sh`): VERDE 143ec6a5e, 1417 tests backend, 463 vitest, 123 e2e.
- Tests nuevos: `test_apertura_defensa.py` (13: tres partidas con un hueco,
  apertura tras arrancar en ataque, sin tu fila de la primera ronda, ronda
  sin lado antes, apertura sin ganador fuera del winrate, resto sin las
  aperturas, porcentaje sobre las aperturas del mapa, filtro de mapa sí y de
  lado no, apertura sin sitio, mapa sin aperturas, sin partidas, 2 consultas
  fijas, la API con filtros); `aperturaDefensa.test.js` (4); e2e "el Coach
  muestra el sitio con el que abres la defensa" con los números de la API.
- Verificación manual (QA): base vacía y base sembrada con `factories.py`
  (9 partidas con hueco, ronda sin lado, sin tu fila, un solo jugador, nick
  repetido, sin ganador, dos versiones de mapa); dos valores recalculados con
  `sqlite3` = API; parámetros borde en 200; teclado, contraste (5.71:1) y
  zoom 200 % en Chromium; 5 mutaciones, las 5 caen.
- OMC: plan=— · revisión=— · verificación=— (diseño)
- OMC: plan=— · revisión=no disponible (sin subagentes) · verificación=— (implementación)
- OMC: plan=— · revisión=0 hallazgos · verificación=— (sin subagentes: revision del lider)
- OMC: plan=— · revisión=— · verificación=no disponible (sin herramienta de subagentes: el lider cruzo los 5 criterios contra la evidencia de arriba, los 5 con evidencia)
- Skills del repo: statistical-analysis, testing-strategy (diseño); test-driven-development, testing-strategy, statistical-analysis, ux-copy, modern-web-guidance (implementación); ninguna (revisión); accessibility-review, validate-data, design-critique, verification-before-completion (QA).

### Riesgos y lo que no entra

Sin migración ni `recompute`. Dos consultas fijas por pedido
(`assertNumQueries`). Fuera: la apertura tras el cambio de lado o en
prórroga, y recomendar un sitio.

### Como probarlo en 2 minutos

```
cd backend; python manage.py test tests.test_apertura_defensa
$env:SQLITE_PATH="$env:TEMP\r6-demo.sqlite3"; python manage.py migrate; python manage.py seed_demo; python manage.py runserver
```

Abrir `/coach`: debajo de "Repetir el sitio tras perderlo", una fila por
mapa y sitio, con *Abre* sumando 100 % por mapa y "pocas partidas" junto al
winrate abriendo de los sitios con menos de 5 aperturas.

### Para el humano

Calibrar con la base real el corte de 5 partidas por apertura
(`APERTURA_DEFENSA_MIN_PARTIDAS`), puesto solo con datos sintéticos (aviso,
no frena).

### Candidatos descubiertos

Ficha 148 (`propuesto`, bug): el e2e anota como error las requests que corta
un `page.goto` con el contenedor cargado.

## Que gana quien usa la app

En el Coach, por mapa, que sitio defiende tu equipo en la primera ronda de
defensa de cada partida, cuantas veces y con que winrate esa ronda, contra el
winrate de ese sitio en el resto de tus rondas de defensa: si tu apertura en
defensa es predecible y si arrancar ahi te cuesta.

## Criterios de aceptacion

- [x] Agregado nuevo: primera ronda de defensa = la de menor `Round.number`
      con `my_side="Defense"` de la partida, leida de la partida entera (como
      `_primera_ronda`); si falta una ronda antes (hueco de numeracion desde
      la primera ronda de la partida) o no tiene sitio, la partida no entra.
      Por mapa (con su version) y sitio: `opens` (partidas que abrieron
      ahi), `opens_decided`, `opens_winrate`, y `rest_rounds`,
      `rest_winrate` del mismo sitio en las demas rondas de defensa. Test con
      tres partidas y un hueco.
- [x] Una ronda sin ganador cuenta en las rondas y no en el winrate. Test.
- [x] Filtros globales de partida (mapa, tipo, modo, fechas, sesion) aplican;
      lado y operador no (es siempre defensa y del equipo), como "Repetir el
      sitio tras perderlo". Test con filtro de mapa.
- [x] Se ve en el Coach, junto a "Repetir el sitio tras perderlo", con aviso
      de muestra (se avisa, no se oculta) y una nota sin datos; e2e sobre
      `seed_demo` con los numeros de la API y consola limpia.
- [x] Fila nueva en `docs/metricas.md`.

## Fuera de alcance

- El sitio con el que abres tras el cambio de lado o en prorroga.
- Recomendar un sitio.

## Diseno

(arquitecto 20261114T0040Z-c3LsMAo, sobre dev f34baba) Precedente
`site_after_loss`, sin arena. Apertura de defensa = tu primera fila de
defensa de la partida si tu primera fila es la ronda mas baja de `Round`,
los numeros siguen sin hueco ni lado vacio hasta ella y tiene sitio; si no,
la partida no aporta apertura y sus defensas van al resto. Por (mapa con
version, sitio): `opens`, `opens_decided`, `opens_won`, `opens_winrate`,
`opens_share` (sobre las aperturas del mapa), `rest_rounds`,
`rest_decided`, `rest_winrate`. Sin ganador cuenta en las rondas y no en el
winrate. Mapa, tipo, modo, fechas y sesion aplican; lado, operador y sitio
no. Corte de aviso 5 partidas (`APERTURA_DEFENSA_MIN_PARTIDAS`), sin
veredicto contra el resto.
Skills del repo: statistical-analysis, testing-strategy.
OMC: plan=— · revisión=— · verificación=—

## Implementacion

(dev 20261115T0219Z-i32143169) `aggregates.defense_opener` (2 consultas
fijas: `Min("number")` de `Round` acotado por subconsulta y tus filas
ordenadas), `GET /api/positioning/defense-opener/`, `aperturaDefensa.js`,
`PanelAperturaDefensa` en `Coach.jsx` con CSV, e2e del panel y fila en
`metricas.md` con su corte en `## Muestra minima`. Desvios menores:
`rest_won` en la salida, nota con `skipped` (las partidas con defensa que
no entran), "pocas partidas" en vez de "pocas rondas", un mapa sin
aperturas sale con `opens_share` nulo. TDD con rojo visto (13 Django, 4
vitest).
Skills del repo: test-driven-development, testing-strategy, statistical-analysis, ux-copy, modern-web-guidance.
OMC: plan=— · revisión=no disponible (sin subagentes) · verificación=—

## Revision 2026-11-18 sobre 1f3455d

(revisor 20261118T1211Z-cMNRUxv) Aprobar, sin hallazgos: sondas con cambio
de lado y prorroga y con parametros borde, 3 mutaciones que caen. Detalle
en `git log` (35cae16).
OMC: plan=— · revisión=0 hallazgos · verificación=— (sin subagentes: revision del lider)

## QA 2026-11-21 sobre 143ec6a

(qa 20261121T0136Z-s7f07u7) Aprobado. `verificar.sh`: VERDE 143ec6a5e
(1417 backend, 463 vitest, 123 e2e; una corrida previa cayo en un e2e ajeno
por `net::ERR_ABORTED`, ficha 148). Base vacia y base sembrada con
`factories.py` (9 partidas con los casos borde), API igual al calculo a
mano, dos valores recalculados con `sqlite3` (66.7 y 60.0) iguales a la API,
filtros y parametros borde en 200, chunk inicial +0.06 %, teclado, foco,
`aria-sort`, contraste 5.71:1 y zoom 200 % en Chromium, nota sin datos con
`?map=border`, 5 mutaciones que caen. Detalle en `git log` (14fdb2d).
Skills del repo: accessibility-review (0 Critical, 0 Major, 1 Minor ya existente), validate-data (2 valores recalculados = API, 0 hallazgos), design-critique (2 ideas a `ALCANCE.md`), verification-before-completion.
OMC: plan=— · revisión=— · verificación=no disponible (sin herramienta de subagentes: el lider cruzo los 5 criterios contra la evidencia de arriba, los 5 con evidencia)

## Para el humano

- Calibrar con la base real el corte de 5 partidas por apertura (`APERTURA_DEFENSA_MIN_PARTIDAS`), puesto solo con datos sinteticos.
