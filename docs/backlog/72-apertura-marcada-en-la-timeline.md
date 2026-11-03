# 72. La apertura marcada en la timeline de la ronda

estado: entregado
candado: -
rama: claude/equipo-dev/72-apertura-marcada-en-la-timeline
tipo: funcionalidad
epica: paridad-referencia
area: frontend
prioridad: 2
fuente: idea R4 de `ALCANCE.md`; fila "Kill feed por ronda con la apertura destacada" de `replica/features.csv` (`must`, `clone: partial`), [r6-replay.com](https://r6-replay.com/) ("See exactly who got the opening pick, who traded it"). Hoy la timeline de `frontend/src/pages/MatchDetail.jsx:271-274` solo marca HS y tradeada; la apertura la dicen la tabla de jugadores ("1a baja", "1a muerte") y el resumen en texto
archivos: frontend/src/aperturas.js, frontend/src/aperturas.test.js, frontend/src/casosApertura.json, frontend/src/pages/MatchDetail.jsx, frontend/e2e/humo.spec.js, backend/tests/test_casos_apertura.py
turnos: po 20261030T1653Z, arquitecto 20261030T1652Z, dev 20261102T1626Z-cDEQrsE, revisor 20261102T2004Z-cS7svm1, qa 20261103T0004Z-cRkutk1, release 20261103T0004Z-cRkutk1

## PR

Titulo: `[equipo-dev][frontend] La apertura marcada en la timeline de la ronda`

### Que cambia

En la timeline de cada ronda (detalle de partida), la primera baja de la
ronda lleva un chip "apertura" y la primera baja de tu equipo un chip
"entry" (si no es la misma), junto a HS y tradeada. Se ve de un vistazo
quien abrio y cuanto tardo tu equipo en responder.

### Por que esto y no otra cosa

Ficha 72, idea R4 de `ALCANCE.md` (fila `must` de la referencia). Logica
pura en JS con casos compartidos con Django, sin tocar el backend: la API ya
trae `order`, `kind`, `actor` y `target`. Descartado leer las banderas
guardadas del scoreboard: con `seed_demo` no son coherentes con sus eventos.

### Como se probo

- `check.sh` (verificar.sh): VERDE, 859 tests backend, 153 vitest, 54 e2e.
- Tests nuevos: `frontend/src/aperturas.test.js` (6 casos compartidos al
  derecho, al reves y sin equipo; ronda sin eventos; sin equipo propio);
  `backend/tests/test_casos_apertura.py`
  (`test_los_casos_de_la_timeline_son_los_del_import`, los mismos casos
  contra `analyse_round`); e2e `el timeline marca la apertura de cada ronda`.
- Manual (QA): base de `factories.py` en Chromium: apertura y entry en las
  filas correctas, `Death` sin autor como apertura, ronda sin eventos sin
  chips, partida ajena solo "apertura". Mutaciones en `aperturas.js` y
  `metrics.py` hacen caer los tests.
- OMC: plan=— · revisión=3 hallazgos (3 arreglados) · verificación=— (implementacion)
- OMC: plan=— · revisión=2 hallazgos (0 arreglados, ninguno bloquea) · verificación=— (revision)
- OMC: plan=— · revisión=— · verificación=PASS (QA)

### Riesgos y lo que no entra

Sin migracion, sin `recompute`, sin backend de produccion. Chunk inicial
+0.03 %. Con `seed_demo` el chip puede no coincidir con "1a baja" del
scoreboard porque el seed escribe esas banderas con formulas propias; con
replays importados es la misma regla. Fuera: chip TK (F14), quien tradeo la
apertura, apertura como filtro (F1), arreglar `seed_demo` (ficha `deuda`
pendiente de abrir).

### Como probarlo en 2 minutos

```
cd backend; python manage.py seed_demo; python manage.py runserver
```
Abrir http://127.0.0.1:8000/partidas, una partida, recorrer las rondas: un
chip "apertura" en la primera baja de cada ronda con bajas; "entry" en la
primera baja de tu equipo cuando no abriste vos.

### Para el humano

Nada.

### Candidatos descubiertos

Ninguno nuevo (la ficha `deuda` de `seed_demo` la abre el PO).

## Que gana quien usa la app

Chips "apertura" y "entry" en la timeline, junto a HS y tradeada, sin
cruzar la timeline con la tabla de jugadores.

## Criterios de aceptacion

- [x] Logica pura `frontend/src/aperturas.js` con vitest: apertura = primer
      `Kill`/`Death` por `order`, como `metrics.py`, aunque venga desordenado.
- [x] Entry = primer `Kill` de tu equipo; si coincide con la apertura, solo
      "apertura".
- [x] Ronda sin bajas sin chips; `Death` sin autor abre; sin equipo propio
      solo "apertura".
- [x] Coherencia con lo guardado: casos compartidos `casosApertura.json`
      (vitest + Django contra `analyse_round`) y e2e de la regla visible
      (redefinido en el Diseno: `seed_demo` no sostiene la comparacion).
- [x] Sin backend de produccion ni fila nueva en `docs/metricas.md`.

## Diseno

Arquitecto 20261030T1652Z: modulo puro `marcasDeApertura(ronda, miEquipo)`,
casos compartidos JSON para vitest y Django, chips en `Timeline` de
`MatchDetail.jsx`, e2e en `humo.spec.js`. El criterio 4 se cubre con casos
compartidos porque `seed_demo` escribe `opening_kill`/`opening_death` con
formulas propias (`seed_demo.py:239-241`).

## Implementacion

Dev 20261102T1626Z-cDEQrsE: lo del diseno sin desvios; revision ciega con 3
LOW arreglados. VERDE ffbec2b (859/153/54).

## Revision 2026-11-02 sobre baa00f8

Revisor 20261102T2004Z-cS7svm1: aprobar. Hallazgos no bloqueantes: con
`seed_demo` el chip contradice las banderas del scoreboard (MEDIUM, deuda del
seed); el e2e compara con la regla JS y no con la API (LOW, sumar cuando
exista la ficha del seed).

## QA 2026-11-03 sobre bb96a02

QA 20261103T0004Z-cRkutk1: VERDE bb96a02 (859/153/54); chunk inicial
+0.03 %; mutaciones en `aperturas.js` (caen 3 a 6 tests) y `metrics.py`
(caen 5 subTests); `runserver` con base vacia y bordes (`page=-1`,
`until=foo`, `map=`, 404) y con base de `factories.py` en Chromium: todos
los casos del criterio 3 se ven bien. `omc-verifier`: PASS. Aprobado.
OMC: plan=— · revisión=— · verificación=PASS

## Verificar en el PC

Nada (sin migracion, parser, Electron ni `.ps1`).

## Para el humano

Nada pendiente.
