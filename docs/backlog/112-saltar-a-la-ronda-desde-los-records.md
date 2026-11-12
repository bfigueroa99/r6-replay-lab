# 112. Saltar a la ronda desde los records

estado: disenado
candado: -
rama: -
tipo: funcionalidad
epica: revision-de-rondas
area: frontend
prioridad: 3
fuente: ALCANCE.md F6 (el PR #14 que lo frenaba se cerro sin merge el 2026-11-05)
archivos: backend/replays/analytics/aggregates.py (_record_de_ronda, record de racha), backend/tests/test_records.py, frontend/src/navegacionRondas.js, frontend/src/navegacionRondas.test.js, frontend/src/records.js, frontend/src/records.test.js, frontend/src/pages/MatchDetail.jsx, frontend/e2e/humo.spec.js, docs/metricas.md
turnos: po 20261112T1128Z-cKKCvKD, arquitecto 20261112T2004Z-cbaTGDt

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

## Revision

## QA

## Para el humano

(nada)
