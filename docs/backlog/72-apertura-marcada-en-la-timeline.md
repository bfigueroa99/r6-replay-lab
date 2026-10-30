# 72. La apertura marcada en la timeline de la ronda

estado: disenado
candado: -
rama: -
tipo: funcionalidad
epica: paridad-referencia
area: frontend
prioridad: 2
fuente: idea R4 de `ALCANCE.md`; fila "Kill feed por ronda con la apertura destacada" de `replica/features.csv` (`must`, `clone: partial`), [r6-replay.com](https://r6-replay.com/) ("See exactly who got the opening pick, who traded it"). Hoy la timeline de `frontend/src/pages/MatchDetail.jsx:271-274` solo marca HS y tradeada; la apertura la dicen la tabla de jugadores ("1a baja", "1a muerte") y el resumen en texto
archivos: frontend/src/aperturas.js, frontend/src/aperturas.test.js, frontend/src/casosApertura.json, frontend/src/pages/MatchDetail.jsx, frontend/e2e/humo.spec.js, backend/tests/test_casos_apertura.py
turnos: po 20261030T1653Z, arquitecto 20261030T1652Z

## PR

(La escribe el Release manager al final.)

## Que gana quien usa la app

En la timeline de cada ronda, la baja que abrio la ronda lleva un chip
"apertura" y la primera baja de tu equipo un chip "entry" (si no es la
misma), junto a HS y tradeada: se ve de un vistazo quien abrio y cuanto
tardo tu equipo en responder, sin cruzar la timeline con la tabla de
jugadores. Es un `must` de la referencia que la app tiene a medias.

## Criterios de aceptacion

- [ ] Logica pura en un modulo de `frontend/src/` con vitest: dados los
      eventos de una ronda y el equipo de cada nick, marca como apertura el
      primer evento `Kill` o `Death` por `order`, la misma regla que
      `opening_kill`/`opening_death` en `replays/analytics/metrics.py`
      (bloque "aperturas"), aunque el array venga desordenado.
- [ ] Entry: el primer `Kill` de un jugador de tu equipo, con la misma regla
      que `entry_kill` en `metrics.py` (sobre `kill_events`); si es el mismo
      evento que la apertura, lleva solo "apertura". Vitest con los dos
      casos.
- [ ] Ronda sin bajas: ningun chip. Ronda que abre con un `Death` sin autor
      rival: ese evento lleva "apertura" y el entry sigue siendo el primer
      `Kill` de tu equipo. Ronda sin jugador `is_me` (partida de otro): se
      usa el equipo que ya calcula `myTeam` en `MatchDetail.jsx`; sin equipo,
      solo "apertura". Vitest por caso.
- [ ] Coherencia con lo guardado: con `seed_demo`, en cada ronda con bajas
      el autor del evento "apertura" es el jugador con "1a baja" (o la
      victima, el que tiene "1a muerte") en la tabla de jugadores de esa
      ronda. Lo afirma el e2e (`frontend/e2e/`) sobre una partida sembrada,
      junto con que hay exactamente un chip "apertura" por ronda con bajas.
- [ ] Sin cambios de backend: `/api/matches/<id>/` ya trae `order`, `kind`,
      `actor` y `target` de cada evento. Sin numero nuevo en la UI, asi que
      sin fila nueva en `docs/metricas.md`.

## Fuera de alcance

- El chip "TK" para teamkills en la timeline (idea F14).
- Marcar quien tradeo la apertura (el chip "tradeada" ya existe).
- La apertura en otras pantallas o como filtro de rondas (F1).
- Cambiar como se calculan `opening_kill`, `opening_death` o `entry_kill`.

## Diseno

Arquitecto 20261030T1652Z sobre `origin/dev@0fedc7b`. Filtros duros: pasa
(eventos que `/api/matches/<id>/` ya devuelve; sin backend de produccion, sin
red, sin dependencias, sin numero nuevo). Skills: no aplica (el patron esta en
`frontend/src/matrizDuelos.js`, que ya repite la regla de la apertura en JS,
y en `frontend/e2e/humo.spec.js`). Arena: no, una sola forma obvia. Spike en
el scratchpad, sin commitear: el modulo de abajo y los 6 casos compartidos
pasan en vitest y en Django contra `analyse_round`.

**El criterio 4 no se puede cumplir tal como esta con `seed_demo`.** Medido
sobre una base sembrada (`seed_demo --force`, 29 partidas, 203 rondas): en las
203 rondas, las banderas guardadas no son las del primer evento: `seed_demo`
escribe `opening_kill`/`opening_death` con formulas propias
(`indice % 6`, `indice % 5`, `seed_demo.py:239-240`), nunca marca a un rival, y su
primer evento cuando mueres es el rival que te mata. Arreglar el seed mueve los
numeros de varias pruebas del e2e (Duelos de apertura, "Cuándo llega la
apertura", matriz "Solo aperturas"): queda fuera (candidato a ficha `deuda`,
anotado en el Papel de `ESTADO.md`). El criterio se cubre asi, sin bajar lo
que pide (que la marca de la timeline y la bandera guardada sean la misma
regla):
- **Casos compartidos**: `frontend/src/casosApertura.json`, los mismos
  datos para vitest (sobre el modulo JS) y para un test de Django (sobre
  `analyse_round`, el import de verdad). Si alguien cambia una de las dos
  reglas, cae el test de ese lado.
- **e2e sobre `seed_demo`**: lo que el seed si sostiene, la regla visible:
  un solo chip "apertura" por ronda con bajas, en la primera fila de baja de
  la timeline, y al menos un "entry" en la partida.

**Archivos** (y por que):
- `frontend/src/aperturas.js` (nuevo, logica pura, como `matrizDuelos.js`):
  `export function marcasDeApertura(ronda, miEquipo)` -> `{ apertura, entry }`,
  `order` del evento o `null`. Bajas = eventos `Kill` o `Death`, copiados y
  ordenados por `order` (el array puede venir desordenado). `apertura` = la
  primera (bloque "aperturas" de `metrics.analyse_round`). `entry`: solo si
  `miEquipo` es un numero >= 0; equipo de cada nick desde `ronda.players`
  (`team_index`); el primer `Kill` cuyo autor es de `miEquipo` (regla de
  `entry_kill` sobre `kill_events`: un teamkill de tu equipo tambien cuenta,
  un nick sin equipo no); si es el mismo `order` que `apertura`, `null`.
  Comentario: la regla es la de `metrics.py` y los casos compartidos lo
  vigilan.
- `frontend/src/casosApertura.json` (nuevo): lista de
  `{nombre, mi_equipo, jugadores: [[nick, equipo]], eventos: [[kind, actor, target]], apertura, entry}`,
  con `order` = posicion y `entry` crudo (antes de quitarlo por coincidir con
  la apertura). Seis casos: abre tu equipo (apertura 0, entry 0); abre el
  rival y tu equipo responde (0, 1); `OperatorSwap` y despues un `Death` sin
  autor (1, 3); teamkill primero (0, 0); nick sin equipo abre (0, 1); sin
  bajas (`null`, `null`).
- `frontend/src/aperturas.test.js` (nuevo): por cada caso compartido, las
  marcas esperadas (entry `null` si coincide con la apertura), las mismas con
  el array al reves y entry `null` con `miEquipo` -1; mas
  `it('una ronda sin eventos no marca nada')` (sin `events`) y
  `it('sin equipo propio solo marca la apertura')` (`undefined` y -1).
- `backend/tests/test_casos_apertura.py` (nuevo, `SimpleTestCase`): lee el
  JSON con `Path(__file__).resolve().parents[2] / "frontend" / "src" /
  "casosApertura.json"`, arma `round_data` (`matchFeedback` con
  `{"type": {"name": kind}, "username", "target", "timeInSeconds"}`
  decreciente) y por caso (`subTest`) compara con `analyse_round`:
  `opening_kill` = {autor} y `opening_death` = {victima} del evento
  `apertura` (solo nicks de la ronda; un `Death` no tiene `opening_kill`),
  nadie si es `null`; `entry_kill` dentro de `mi_equipo` = {autor del evento
  `entry`}. Nombre: `test_los_casos_de_la_timeline_son_los_del_import`.
- `frontend/src/pages/MatchDetail.jsx`, `Timeline` (lineas 243-280):
  `const marcas = marcasDeApertura(round, myTeam(round))` una vez por ronda;
  en `.tags`, antes de HS: `<span className="chip" title="Primera baja de la
  ronda">apertura</span>` si `event.order === marcas.apertura`, y
  `<span className="chip" title="Primera baja de tu equipo">entry</span>` si
  `event.order === marcas.entry`. `myTeam` ya devuelve -1 sin fila tuya ni
  equipo marcado: ahi solo sale "apertura" (criterio 3). Chip neutro, como
  HS y tradeada: sin CSS nuevo.
- `frontend/e2e/humo.spec.js`, test nuevo
  `el timeline marca la apertura de cada ronda`, despues del de la matriz:
  `/partidas`, primera partida; por cada `.round-tab` (clic): las filas de
  baja son `.timeline li` con "mato a" o "murio"; exactamente un chip con
  texto exacto "apertura" en la timeline y esta en la primera fila de baja;
  como mucho un "entry" y nunca en la misma fila que "apertura". Al final,
  al menos un "entry" en la partida (en el seed, toda ronda donde mueres y
  tambien matas lo tiene). `vigilarConsola` sin errores.
- `docs/metricas.md`: nada (sin numero nuevo, criterio 5).

**Orden:** `casosApertura.json` y los dos tests en rojo; `aperturas.js`;
`MatchDetail.jsx`; e2e; `check.sh` completo (toca la pagina).

**Que puede romperse.** El chunk de `MatchDetail` crece unas lineas (QA mira
el 10 %). Si cambia la regla de `metrics.py` (apertura o entry), cae
`test_casos_apertura.py` y hay que tocar el JSON y `aperturas.js` juntos: es
lo que se busca. Sin migracion, sin recompute, sin backend de produccion.
Ninguna rama abierta toca estos archivos (68: backend; 69 y 71: backend).

**Verificacion manual (QA).** `seed_demo`, `runserver`, una partida: en cada
ronda un "apertura" en la primera baja y, donde mueres primero y despues tu
equipo mata, un "entry" en esa baja; en una partida de `factories` sin fila
`is_me` ni equipo marcado, solo "apertura".

**Fuera de alcance (anotado):** que `seed_demo` escriba banderas de apertura
coherentes con sus eventos (mueve numeros del e2e: ficha `deuda` aparte).
Tamano: unas 40 lineas de JS, 30 de JSX, 120 de tests.

## Implementacion

## Revision <fecha> sobre <sha>

## QA <fecha> sobre <sha>

## Verificar en el PC

## Pendiente

## Para el humano

Nada pendiente.
