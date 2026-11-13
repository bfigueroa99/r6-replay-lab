# 112. Saltar a la ronda desde los records

estado: aprobado
candado: -
rama: claude/equipo-dev/112-saltar-a-la-ronda-desde-los-records
tipo: funcionalidad
epica: revision-de-rondas
area: frontend
prioridad: 3
fuente: ALCANCE.md F6 (el PR #14 que lo frenaba se cerro sin merge el 2026-11-05)
archivos: backend/replays/analytics/aggregates.py (_record_de_ronda, record de racha), backend/tests/test_records.py, frontend/src/navegacionRondas.js, frontend/src/navegacionRondas.test.js, frontend/src/records.js, frontend/src/records.test.js, frontend/src/pages/MatchDetail.jsx, frontend/e2e/humo.spec.js, docs/metricas.md, frontend/src/components/ui.jsx (Panel acepta id)
turnos: po 20261112T1128Z-cKKCvKD, arquitecto 20261112T2004Z-cbaTGDt, dev 20261113T0003Z-cVnayJ8, revisor 20261113T0404Z-cnRfz4a, qa 20261113T0804Z-cJw5MQs

## PR

## Que gana quien usa la app

En el Inicio, un record de ronda ("Mejor ronda" y los demas que traen
`round_label`) abre el detalle de la partida ya parado en esa ronda, y no
arriba de todo con la ronda 1. Es el primer tramo de F6: deja el ancla
`#ronda-N` en el detalle, que despues pueden usar Remontadas, el Coach y las
listas.

## Criterios de aceptacion

- [ ] `_record_de_ronda` (`aggregates.py`) devuelve tambien el numero de
      ronda (`round_number`, el mismo que usa el detalle); test sobre
      `personal_records`.
- [ ] El detalle de partida acepta `/partidas/<id>#ronda-<n>`: selecciona o
      despliega esa ronda y la lleva a la vista; un `n` que no existe o no
      es numero deja el detalle como siempre, sin error. Logica de leer el
      hash en una funcion pura con vitest.
- [ ] Los records de ronda del Inicio enlazan a `#ronda-<n>`; los de
      partida siguen enlazando a la partida sola.
- [ ] e2e: desde el Inicio del seed, el enlace de "Mejor ronda" abre el
      detalle con esa ronda seleccionada (afirmar por el texto de la ronda
      seleccionada, no por scroll); y `#ronda-999` no ensucia la consola.

## Fuera de alcance

- Enlaces desde Remontadas, Clutches y el Coach (tramos siguientes de F6 y
  de F15).
- Flechas o atajos de teclado entre rondas.

## Diseno

(arquitecto 20261112T2004Z-cbaTGDt) Filtros duros: pasa. Usa `Round.number`, que
ya viaja en el detalle; sin red, sin dependencias, sin POST, sin migracion.
Una forma obvia y chica (~150 lineas): sin arena ni consenso.

**Correccion de premisa.** No hay record "Mejor ronda": los records de ronda
que traen `round_label` son `most_kills_round` ("Más bajas en una ronda"),
`biggest_clutch` ("Clutch más grande") y `longest_round_streak` ("Racha de
rondas", la ronda donde empieza). Los tres enlazan a su ronda; el e2e usa
"Más bajas en una ronda".

**Ancla.** `/partidas/<id>#ronda-<n>` con `n` = numero humano de la ronda, el
mismo de la etiqueta `R<n>` (`Round.number + 1`). Se busca la ronda cuyo
`number + 1 === n`, **no** la posicion en la lista: con un `.rec` faltante
la posicion y el numero se separan.

**Backend, `backend/replays/analytics/aggregates.py`.**
- `_record_de_ronda`: agrega `"round_number": rp.round.number` (0-based,
  el mismo `number` del detalle).
- `_record_de_racha` (el dict que arma `"round_label": f"R{racha['from_number'] + 1}"`):
  agrega `"round_number": racha["from_number"]`.
- Nada mas cambia; las claves viejas se quedan (otras pantallas las usan).

**Frontend.**
- `frontend/src/navegacionRondas.js` (ya tiene `rondaVecina` y
  `pasoDeTecla`): `export function indiceDeAncla(hash, rounds)` devuelve el
  indice en `rounds` de la ronda con `number + 1 === n` si `hash` es
  exactamente `#ronda-<entero positivo>`; si no, `null` (hash vacio,
  `#ronda-abc`, `#ronda-0`, `#ronda-999`, `rounds` vacio o indefinido).
  `export const anclaDeRonda = (number) => `#ronda-${number + 1}``.
- `frontend/src/navegacionRondas.test.js`: casos de arriba, mas una lista
  con hueco (`numbers` 0, 1, 3): `#ronda-4` da indice 2 y `#ronda-3` null.
- `frontend/src/records.js`: en `filasDeRecords`, `href` =
  `/partidas/<id>` + `anclaDeRonda(record.round_number)` cuando
  `record.round_number` es un numero (`Number.isInteger`); si no, como hoy.
  Records de partida y `best_day` no cambian.
- `frontend/src/records.test.js`: un record de ronda con `round_number: 6`
  da `href` `/partidas/<id>#ronda-7`; uno de partida sigue sin ancla.
- `frontend/src/pages/MatchDetail.jsx`, en `DetallePartida`:
  `const { hash } = useLocation()` (de `react-router-dom`, ya importado
  `Link` y `useParams` de ahi); `useEffect` con dependencias
  `[hash, data]`: si hay `data?.rounds` y `indiceDeAncla(hash, data.rounds)`
  no es `null`, `setSelected(indice)` y llevar el panel de rondas a la
  vista (`document.getElementById('rondas')?.scrollIntoView({ block: 'start' })`;
  el `Panel` de Rondas va envuelto en un `<div id="rondas">` o recibe el
  id si `Panel` lo acepta). Un ancla invalida no hace nada. Hacer clic en
  otra ronda no reescribe el hash (no ensucia el historial; fuera de
  alcance).

**e2e, `frontend/e2e/humo.spec.js`**, test `un record de ronda abre la
partida en esa ronda` junto a `el Resumen muestra tus records y enlaza a la
partida`: leer `/api/overview/` -> `records.most_kills_round`
(`seed_demo`: partida 28, Bank, `round_label` R7, `round_number` 6); clic en
el enlace de la fila "Más bajas en una ronda"; URL termina en
`/partidas/<id>#ronda-7`; el `h3` del detalle de ronda
(`.round-detail h3`) empieza con `R7` y la pestaña activa
(`.round-tab.active`) dice `R7`. Despues `page.goto('/partidas/<id>#ronda-999')`:
el detalle carga con `R1` activa. Consola limpia. Afirmar con los valores
que devuelve la API, no con 28/R7 escritos a mano.

**`docs/metricas.md`**: no hay numero nuevo. Una frase en la fila de
**Records** (o la que describe el panel "Tus récords"): "los records de ronda
abren el detalle de la partida en esa ronda".

**Orden.** aggregates + test, `navegacionRondas.js` + vitest, `records.js` +
vitest, `MatchDetail.jsx`, e2e, metricas, `npm run build`.

**Tests backend**, en `backend/tests/test_records.py`:
`test_los_records_de_ronda_traen_el_numero_de_ronda` (most_kills_round y
biggest_clutch con `round_number` igual al `Round.number` armado) y
`test_la_racha_trae_el_numero_de_su_primera_ronda`.

**Que puede romperse.** `DetallePartida` va con `key={id}`: al saltar a otra
partida se remonta y el efecto corre otra vez, bien. Si el efecto corre antes
de que lleguen los datos no hace nada; por eso depende de `data`. El
`useEffect` del teclado no cambia. Un `scrollIntoView` en jsdom no existe,
pero la logica probada es la pura; el componente solo lo ve el e2e.

**Archivos ocupados.** La 107 toca `aggregates.py` y `humo.spec.js` en
otras funciones y otros tests; la 113 lo mismo. Ninguna toca `records.js`,
`navegacionRondas.js` ni `MatchDetail.jsx`. No se frena.

**Verificacion manual.** `seed_demo`, Inicio, "Más bajas en una ronda" ->
detalle con R7 activa; `/partidas/1#ronda-abc` igual que sin ancla.

Skills: no aplica (enlace y seleccion en una pagina existente; el repo ya
tiene la seleccion de ronda y la navegacion por teclado).
OMC: plan=— · revisión=— · verificación=—

## Implementacion

(dev 20261113T0003Z-cVnayJ8) Diseno completo:

- `aggregates.py`: `round_number` (el `Round.number` 0-based del detalle) en
  `_record_de_ronda` (mas bajas en una ronda, clutch mas grande) y en el record
  de racha (`from_number`, la ronda donde empieza).
- `navegacionRondas.js`: `anclaDeRonda(number)` (`#ronda-<number+1>`) e
  `indiceDeAncla(hash, rounds)` (busca por `number`, no por posicion; `null`
  con hash vacio, no entero positivo, ceros a la izquierda, ronda inexistente
  o sin rondas). `records.js`: `href` con ancla si `round_number` es entero.
- `MatchDetail.jsx`: `useEffect` con `[hash, location.key, data]` que elige la
  ronda del ancla y lleva el panel a la vista; un ancla invalida no hace nada.
- e2e `un record de ronda abre la partida en esa ronda` (valores de
  `/api/overview/`, exige `round_number > 0` para que el salto se distinga de
  R1; `#ronda-999` tras `about:blank` deja R1). Frase en `metricas.md` (Records).

Desvios del diseno:
- **`id` en `Panel`** (`components/ui.jsx`, fuera de `archivos:`): el panel de
  Rondas recibe `id="rondas"` en vez de envolverse en un `div`, para no
  alterar el espaciado entre paneles. Prop opcional; el resto no cambia.
- **`location.key` en las dependencias** (revision ciega, LOW): volver a clicar
  el mismo record tras cambiar de ronda re-aplica el ancla.
- El e2e acota los locators a `#rondas`: "Fases de la ronda" tambien tiene una
  `.round-tab.active` ("Todas") y el detalle otro `h3`.

Tests: backend `test_los_records_de_ronda_traen_el_numero_de_ronda`,
`test_la_racha_trae_el_numero_de_su_primera_ronda` (vistos en rojo antes del
codigo); vitest `indiceDeAncla` (3), `anclaDeRonda` (1) y `un record de ronda
enlaza a su ronda y uno de partida no` (vistos en rojo); e2e (arriba).
Criterios -> tests: `round_number` (los dos backend); ancla en el detalle y
anclas invalidas (vitest `indiceDeAncla` + e2e `#ronda-999`); enlaces del
Inicio (vitest de `records.js` + e2e); e2e con consola limpia.

verificar.sh: VERDE 140e5fd (1165 backend, 334 vitest, 95 e2e).

Skills: no aplica (seleccion de ronda y navegacion ya resueltas en el repo).
Skills del repo: ninguna (sin texto nuevo para el usuario; JSX minimo sobre un componente existente).
OMC: plan=— · revisión=2 hallazgos (2 arreglados; 0 CRITICAL/HIGH) · verificación=—

## Revision 2026-11-13 sobre db81dc9

(20261113T0404Z-cnRfz4a) La rama ya tiene `origin/dev` (fcba457), sin conflictos.
Partida: verificar.sh sobre db81dc9 -> ROJO solo por
`e2e/accesibilidad.spec.js:226` (94 e2e pasan, incluido el de esta ficha). Ese
test cae tambien en `origin/dev` (7 de 8 aislado); es una carrera con la
animacion de recharts y lo arregla el hotfix 117 (rama
`claude/equipo-dev/117-hotfix-graficos-punteados`). Con el parche de la 117
aplicado en el arbol sin commitear: verificar.sh VERDE db81dc953-sucio (1165
backend, 334 vitest, 95 e2e). Revision a ciegas, eje de estandares
(`omc-code-reviewer`, diff de codigo ~140 lineas y un tema: sin eje de
intencion ni de seguridad, no toca POST, `.rec`, rutas ni Electron).

Reglas: sin dependencias, sin escritura en la API, sin numero nuevo en la UI
(el campo `round_number` solo arma el enlace; frase en `metricas.md`),
identificadores sin tildes, sin `print` ni `console.log`. `ui.jsx` esta en
`archivos:` y el desvio esta explicado.
Criterios: los cuatro cubiertos. `round_number` = `Round.number` del detalle
(`views.py` expone `"number": rnd.number`; tests de records y racha, la
racha arranca en la ronda 2 para que un off-by-one caiga); ancla por
`number` y no por posicion (vitest con rondas 0, 1, 3); anclas invalidas y
partida sin rondas -> `null` sin error; e2e exige `round_number > 0` y
`#ronda-999` deja R1 con la consola limpia. El `useEffect` nuevo esta antes
de los `return` tempranos.

Hallazgos (ninguno CRITICAL, HIGH ni MEDIUM):

- [estilo] LOW `frontend/src/pages/MatchDetail.jsx:51-53`
  Que pasa: el comentario de tres lineas se lee como una sola frase ("como
  siempre con `key` volver a clicar...").
  Arreglo sugerido: punto al final de la linea 52.

Veredicto: aprobar -> `revisado`.

Skills: no aplica.
OMC: plan=— · revisión=1 hallazgo LOW (0 arreglados) · verificación=—

## QA 2026-11-13 sobre 3627c3c

(qa 20261113T0804Z-cJw5MQs) Se ejercito el sistema: base vacia y base `seed_demo` en
`runserver`, Chromium con Playwright, mutaciones. Scripts en el scratchpad
(no van al repo).

- **check.sh**: `git show origin/dev:scripts/equipo-dev/verificar.sh | bash -s --`
  -> `VERDE 3627c3c39 en 191s: 1165 tests backend, 334 vitest, 95 e2e` (el
  `accesibilidad.spec.js` que cae a veces en dev paso esta vez).
- **API, base vacia** (`SQLITE_PATH=<tmp> manage.py migrate; runserver`):
  `curl /api/overview/` -> los cinco records y `best_day` en `null`, 200.
- **API, base sembrada** (`manage.py seed_demo`: 29 partidas, 203 rondas):
  `most_kills_round` = partida 28, 2, R7, `round_number` 6; `biggest_clutch`
  = 22, 1, R7, 6; `longest_round_streak` = 29, R1, 0. `?until=foo`,
  `?page=-1`, `?days=`, `?since=2099-01-01` -> 200; con `since=2099` los
  records quedan en `null`.
- **Recalculo a mano** (SQLite sobre la base sembrada): max de `kills` por
  ronda del jugador `is_me` = 2 en la partida 28, rondas `number` 1 y 6
  (empate; el record toma la 6 y su `round_label` R7 coincide); `one_vx > 0`:
  (15, 4) y (22, 6) con 1 -> coincide con `biggest_clutch` 22/6.
  `/api/matches/28/` y `/22/` traen `number` 0..6 = R1..R7.
- **Navegador** (Chromium, base sembrada): el Inicio tiene 3 enlaces con
  ancla (`/partidas/28#ronda-7`, `/partidas/22#ronda-7`,
  `/partidas/29#ronda-1`) y 22 a partidas sin ancla. Solo con Tab el foco
  llega a `/partidas/28#ronda-7`; Enter abre el detalle con la pestaña activa
  R7, `h3` "R7 Ataque Ganada" y `#rondas` en la vista. `#ronda-abc`,
  `#ronda-0`, `#ronda-007`, `#ronda-999`, `#ronda-`, `#ronda-3.5`,
  `#ronda--2` y `#RONDA-3` -> R1; `#ronda-3` -> R3. Clic en R2 no reescribe
  el hash. `/partidas/99999#ronda-2` -> "Esa partida no existe". Consola:
  solo el 404 esperado de esa partida inexistente.
- **Accesibilidad** (skill `accessibility-review`, lo que agrego la ficha):
  el enlace es un `<a>` alcanzable por teclado, con nombre "ronda R7 · Bank ·
  2026-08-05"; contraste del enlace 14.17:1, pestaña activa 4.61:1. Sin
  Critical ni Major. Previo a la ficha: las pestañas de ronda son `<button>`
  sin `aria-selected`/`aria-pressed` (WCAG 4.1.2), va como idea a `ALCANCE.md`.
- **Chunk inicial** (`vite build` de dev y de la rama): 196.87 kB -> 197.63 kB
  (+0.4 %).
- **Mutaciones** (las 3 caen y se restauraron): `indiceDeAncla` por posicion
  -> cae vitest "busca la ronda por su numero y no por la posicion";
  `records.js` sin ancla -> cae "un record de ronda enlaza a su ronda y uno de
  partida no"; `round_number + 1` en `aggregates.py` -> `tests.test_records`
  FAILED (failures=1).
- Sin migracion, parser, Electron ni `.ps1`: nada para verificar en el PC.
- `validate-data`: no aplica, no hay numero nuevo en la UI (la frase de
  `metricas.md` linea 149 describe el enlace).

Veredicto: `aprobado`.

Skills: no aplica.
Skills del repo: accessibility-review (0 Critical, 0 Major en lo nuevo; 1 Minor previo a ALCANCE), validate-data (no aplica: sin numero nuevo); valores recalculados: most_kills_round 28/R7 y biggest_clutch 22/R7.
OMC: plan=— · revisión=— · verificación=PASS

## Para el humano

(nada)
