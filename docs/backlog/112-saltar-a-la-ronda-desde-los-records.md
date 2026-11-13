# 112. Saltar a la ronda desde los records

estado: entregado
candado: -
rama: claude/equipo-dev/112-saltar-a-la-ronda-desde-los-records
tipo: funcionalidad
epica: revision-de-rondas
area: frontend
prioridad: 3
fuente: ALCANCE.md F6 (el PR #14 que lo frenaba se cerro sin merge el 2026-11-05)
archivos: backend/replays/analytics/aggregates.py (_record_de_ronda, record de racha), backend/tests/test_records.py, frontend/src/navegacionRondas.js, frontend/src/navegacionRondas.test.js, frontend/src/records.js, frontend/src/records.test.js, frontend/src/pages/MatchDetail.jsx, frontend/e2e/humo.spec.js, docs/metricas.md, frontend/src/components/ui.jsx (Panel acepta id)
turnos: po 20261112T1128Z-cKKCvKD, arquitecto 20261112T2004Z-cbaTGDt, dev 20261113T0003Z-cVnayJ8, revisor 20261113T0404Z-cnRfz4a, qa 20261113T0804Z-cJw5MQs, release 20261113T0804Z-cJw5MQs

## PR

Titulo: `[equipo-dev][frontend] Saltar a la ronda desde los records`

### Que cambia

En el Inicio, los records de ronda ("Más bajas en una ronda", "Clutch más
grande" y "Racha de rondas") abren el detalle de la partida ya parado en esa
ronda, con el panel de Rondas en la vista. El detalle acepta el ancla
`/partidas/<id>#ronda-<n>`; un ancla invalida lo deja como siempre.

### Por que esto y no otra cosa

Ficha 112, primer tramo de F6 (`ALCANCE.md`): deja el ancla `#ronda-N` que
despues pueden usar Remontadas, el Coach y las listas. Se busca la ronda por
su `number` y no por la posicion, porque con un `.rec` faltante se separan.

### Como se probo

- `check.sh` (con `verificar.sh`): VERDE (ver el commit `Entrega`), 1165 tests backend, 334 vitest, 95 e2e.
- Tests nuevos: `test_los_records_de_ronda_traen_el_numero_de_ronda` y
  `test_la_racha_trae_el_numero_de_su_primera_ronda` (backend); vitest de
  `indiceDeAncla` (hash vacio, no entero, ceros, ronda inexistente, rondas con
  hueco), `anclaDeRonda` y `un record de ronda enlaza a su ronda y uno de
  partida no`; e2e `un record de ronda abre la partida en esa ronda` (valores
  de `/api/overview/`, `#ronda-999` deja R1 con la consola limpia).
- Verificacion manual (QA): base sembrada en Chromium, por teclado el enlace
  abre R7; 8 anclas invalidas dejan R1; 3 mutaciones hacen caer sus tests.
- OMC: plan=— · revisión=— · verificación=— (diseno)
- OMC: plan=— · revisión=2 hallazgos (2 arreglados; 0 CRITICAL/HIGH) · verificación=— (implementacion)
- OMC: plan=— · revisión=1 hallazgo LOW (0 arreglados) · verificación=— (revision)
- OMC: plan=— · revisión=— · verificación=PASS (QA)
- Skills del repo: ninguna (implementacion); accessibility-review (0 Critical, 0 Major en lo nuevo; 1 Minor previo a ALCANCE), validate-data (no aplica: sin numero nuevo) (QA).

### Riesgos y lo que no entra

Sin migracion, `recompute`, parser ni Electron. `Panel` acepta un `id`
opcional. Fuera: enlaces desde Remontadas, Clutches y el Coach; reescribir el
hash al cambiar de ronda; flechas entre rondas.

### Como probarlo en 2 minutos

```powershell
cd backend; python manage.py seed_demo; python manage.py runserver
```

Abrir `http://localhost:8000/`, en "Tus récords" clic en "Más bajas en una
ronda": abre `/partidas/28#ronda-7` con R7 activa. `/partidas/28#ronda-abc`
abre como siempre, en R1.

### Para el humano

Nada.

### Candidatos descubiertos

Ninguno (la idea de `aria-selected` en las pestañas de ronda va a `ALCANCE.md`).
## Que gana quien usa la app

En el Inicio, un record de ronda ("Mejor ronda" y los demas que traen
`round_label`) abre el detalle de la partida ya parado en esa ronda, y no
arriba de todo con la ronda 1. Es el primer tramo de F6: deja el ancla
`#ronda-N` en el detalle, que despues pueden usar Remontadas, el Coach y las
listas.

## Criterios de aceptacion

- [x] `_record_de_ronda` (`aggregates.py`) devuelve tambien el numero de
      ronda (`round_number`, el mismo que usa el detalle); test sobre
      `personal_records`.
- [x] El detalle de partida acepta `/partidas/<id>#ronda-<n>`: selecciona o
      despliega esa ronda y la lleva a la vista; un `n` que no existe o no
      es numero deja el detalle como siempre, sin error. Logica de leer el
      hash en una funcion pura con vitest.
- [x] Los records de ronda del Inicio enlazan a `#ronda-<n>`; los de
      partida siguen enlazando a la partida sola.
- [x] e2e: desde el Inicio del seed, el enlace de "Mejor ronda" abre el
      detalle con esa ronda seleccionada (afirmar por el texto de la ronda
      seleccionada, no por scroll); y `#ronda-999` no ensucia la consola.

## Fuera de alcance

- Enlaces desde Remontadas, Clutches y el Coach (tramos siguientes de F6 y
  de F15).
- Flechas o atajos de teclado entre rondas.

## Diseno

(arquitecto 20261112T2004Z-cbaTGDt) `round_number` (0-based) en los records de
ronda y de racha; `indiceDeAncla(hash, rounds)` busca por `number + 1 === n`;
`records.js` agrega el ancla si `round_number` es entero; `MatchDetail.jsx`
selecciona la ronda y lleva `#rondas` a la vista. Detalle en `git log`.
OMC: plan=— · revisión=— · verificación=—

## Implementacion

(dev 20261113T0003Z-cVnayJ8) Diseno completo. Desvios: `id` opcional en
`Panel` (`ui.jsx`) en vez de un `div` envolvente; `location.key` en las
dependencias del efecto, para re-aplicar el ancla al volver a clicar el mismo
record. verificar.sh: VERDE 140e5fd (1165 backend, 334 vitest, 95 e2e).
Skills del repo: ninguna.
OMC: plan=— · revisión=2 hallazgos (2 arreglados; 0 CRITICAL/HIGH) · verificación=—

## Revision 2026-11-13 sobre db81dc9

(revisor 20261113T0404Z-cnRfz4a) Cuatro criterios cubiertos, reglas del repo
cumplidas. Un LOW de estilo sin arreglar (comentario de
`MatchDetail.jsx:51-53` sin punto). Veredicto: `revisado`.
OMC: plan=— · revisión=1 hallazgo LOW (0 arreglados) · verificación=—

## QA 2026-11-13 sobre 3627c3c

(qa 20261113T0804Z-cJw5MQs) verificar.sh VERDE 3627c3c39 (1165 backend, 334
vitest, 95 e2e). Base vacia: records `null`. Base `seed_demo`:
`most_kills_round` 28/R7/`round_number` 6 y `biggest_clutch` 22/R7/6,
recalculados en SQLite. Chromium: por teclado el enlace abre R7 con `#rondas`
en la vista; `#ronda-abc`, `-0`, `-007`, `-999`, `-`, `-3.5`, `--2` y
`#RONDA-3` dejan R1; contraste del enlace 14.17:1. Chunk inicial +0.4 %.
Mutaciones (3) caen. Veredicto: `aprobado`.
Skills del repo: accessibility-review (0 Critical, 0 Major en lo nuevo; 1 Minor previo a ALCANCE), validate-data (no aplica: sin numero nuevo); valores recalculados: most_kills_round 28/R7 y biggest_clutch 22/R7.
OMC: plan=— · revisión=— · verificación=PASS

## Para el humano

(nada)
