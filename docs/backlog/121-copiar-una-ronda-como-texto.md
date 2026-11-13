# 121. Copiar una ronda como texto

estado: aprobado
candado: release 2026-11-13T18:38Z
rama: claude/equipo-dev/121-copiar-una-ronda-como-texto
tipo: funcionalidad
epica: exportar
area: frontend
prioridad: 3
fuente: ALCANCE.md H10
archivos: frontend/src/textoRonda.js (nuevo), frontend/src/textoRonda.test.js (nuevo), frontend/src/pages/MatchDetail.jsx (componente CopiarRonda en el encabezado de la ronda), frontend/e2e/humo.spec.js
turnos: po 20261113T1603Z-cHj1H4k, arquitecto 20261113T1703Z-ctZvzXQ, dev 20261113T1733Z-cudo1Sw, revisor 20261113T1802Z-c8dAf7p, qa 20261113T1830Z-cTivbSq

## PR

## Que gana quien usa la app

En la pestaña de una ronda del detalle de partida, un boton copia la ronda
en texto plano (numero, lado, sitio, resultado y la linea de tiempo con
reloj, autor, victima, HS, apertura y trade) para pegarla en Discord al
revisarla con el equipo. Hoy se copia la partida entera (ficha 66) pero no
se baja a una ronda.

## Criterios de aceptacion

- [ ] Funcion pura nueva que arma el texto desde la ronda de
      `/api/matches/<id>/` (`rounds[].events`): primera linea con mapa,
      numero de ronda, lado, sitio y resultado; una linea por baja en orden
      con reloj, autor, victima y marcas (HS, apertura, tradeada); sin HTML
      ni espacios al final de linea. Vitest con una ronda de tres bajas.
- [ ] Una ronda sin bajas copia la primera linea y "Sin bajas"; vitest.
- [ ] Los teamkills y las bajas sin autor (caidas, bomba) salen con la misma
      etiqueta que la linea de tiempo de la pagina; vitest.
- [ ] Sin `navigator.clipboard` el boton avisa que no se pudo copiar, como
      "Copiar resumen" de la partida.
- [ ] e2e: en una partida de `seed_demo`, abrir una ronda, copiar, y el
      texto copiado empieza con la linea de la ronda y contiene el nick de
      una baja de esa ronda; consola limpia.

## Fuera de alcance

- Copiar varias rondas a la vez o un rango.
- Exportar la ronda a archivo o imagen.
- Backend: `/api/matches/<id>/` ya trae todo.

## Diseno

(arquitecto 20261113T1703Z-ctZvzXQ) Filtros duros: pasa. Solo frontend, sobre
lo que `/api/matches/<id>/` ya devuelve (`match.map`, `rounds[].label`,
`my_side`, `site`, `my_team_won`, `players`, `events`); portapapeles local,
sin red, sin dependencias, sin POST, sin migracion. Una forma obvia y chica
(~150 lineas) con el patron de "Copiar resumen" (`resumenPartida.js` +
`copiarResumen` de `MatchDetail.jsx`): sin arena ni consenso.

**`frontend/src/textoRonda.js`** (logica pura, nuevo; sin React):

- `export function textoRonda(ronda, mapa, miEquipo)` -> string, lineas
  unidas con `\n`, sin espacio al final de ninguna linea.
- Linea 1: `<mapa> · <ronda.label> · <lado> · sitio <site> · <resultado>`.
  `lado`: `Attack` -> `ataque`, `Defense` -> `defensa`, otro o vacio ->
  `lado desconocido`. `site` vacio -> `desconocido` (como la pagina:
  `Sitio: desconocido`). `resultado`: `my_team_won` `true` -> `ganada`,
  `false` -> `perdida`, `null`/`undefined` -> `sin resultado`. `mapa` vacio
  o nulo: la linea arranca en el label (filtrar partes vacias antes de unir).
- Despues, una linea por evento `Kill` o `Death` de `ronda.events`, ordenados
  por `order` (copiar `porOrden` de `aperturas.js`; no exportarlo de ahi
  para no tocar ese archivo). Los demas `kind` (cambio de operador, mensajes
  del feed) no salen: la ficha pide las bajas.
  - `Kill`: `<reloj> <actor> mató a <target>`; `Death`:
    `<reloj> <actor> murió`. Es la misma etiqueta que `Timeline` de la
    pagina: un teamkill sale como `mató a` (la timeline no lo distingue) y una
    caida o la bomba como `murió` (criterio 3). `reloj` = `clock_raw` o `—`.
  - Marcas, en el orden de los chips de la timeline: `apertura` si
    `order === marcas.apertura`, `entry` si `order === marcas.entry`, `HS`
    si `headshot`, `tradeada` si `traded`, con
    `marcas = marcasDeApertura(ronda, miEquipo)` (`aperturas.js`, la misma
    regla que la pagina). Con alguna marca, la linea termina en
    ` (apertura, HS)` (unidas con `, `); sin marcas, sin parentesis.
- Sin ningun `Kill` ni `Death`: segunda y ultima linea `Sin bajas`.
- Sin `ronda` (nulo): `null`.

**`frontend/src/textoRonda.test.js`** (vitest), con una ronda armada a mano
(dos jugadores por equipo en `players` con `team_index` 0 y 1, `is_me` en el
equipo 0):
- `la primera linea dice mapa, ronda, lado, sitio y resultado`
  (`Bank · R3 · ataque · sitio CEO Office · ganada`).
- `una ronda de tres bajas sale en orden con sus marcas`: eventos dados
  desordenados por `order`; la primera baja (del rival) lleva
  `(apertura, HS)`, la primera de tu equipo `(entry)`, una con `traded`
  `(tradeada)`; tres lineas despues de la cabecera, en orden de `order`.
- `sin bajas dice Sin bajas` (sin eventos, y con solo un evento de otro
  `kind`: en los dos casos dos lineas, la segunda `Sin bajas`).
- `un teamkill y una muerte sin autor usan la etiqueta de la timeline`
  (`A mató a B` con A y B del mismo equipo; `C murió`).
- `sin resultado ni sitio ni lado lo dice` (`lado desconocido`,
  `sitio desconocido`, `sin resultado`).
- `ninguna linea termina en espacio` y `sin ronda no hay texto` (`null`).

**`frontend/src/pages/MatchDetail.jsx`**:

- `import { textoRonda } from '../textoRonda.js'` junto al import de
  `resumenPartida.js`.
- Componente nuevo al final del archivo, `function CopiarRonda({ round, mapa,
  miEquipo })`, con su propio `useState(null)` y `copiar()` igual a
  `copiarResumen` (sin `navigator.clipboard?.writeText` ->
  `setCopia('error')`; `try`/`catch` sin `console`). Renderiza el aviso
  `<span className="note">` (`Ronda copiada` / `No se pudo copiar: el
  navegador no dio acceso al portapapeles.`) y
  `<button type="button" className="btn small" onClick={copiar}
  title="Copia esta ronda y sus bajas en texto plano.">Copiar ronda</button>`.
  El aviso dice `Ronda copiada` y no `Copiado` para no confundirse con el de
  la partida (y para que el e2e de "Copiar resumen", que busca `Copiado`
  exacto, siga encontrando uno solo).
- Uso: dentro del `<h3>` de la ronda, despues de
  `<ResultChip won={round.my_team_won} />`:
  `<CopiarRonda key={round.number} round={round} mapa={match.map} miEquipo={myTeam(round)} />`.
  El `key` reinicia el aviso al cambiar de ronda (si no, "Ronda copiada"
  quedaria pegado a la ronda siguiente). El estado vive en el componente y
  no arriba de `DetallePartida`: asi no hay hook nuevo antes de los returns
  tempranos y no se toca la zona que modifica la 79 (ver abajo).

**e2e, `frontend/e2e/humo.spec.js`**, test `el detalle de partida copia una
ronda`, justo despues de `el detalle de partida copia el resumen`:
`grantPermissions(['clipboard-read', 'clipboard-write'])`; tomar
`matches[0]` de `/api/matches/?limit=200` y su detalle de
`/api/matches/<id>/`; `i` = indice de la primera ronda con algun evento
`Kill`; `page.goto('/partidas/<id>')`; clic en `.round-tab` `nth(i)`; clic en
`Copiar ronda`; `Ronda copiada` visible (`exact: true`); el texto del
portapapeles empieza con `` `${detalle.match.map} · ${ronda.label} · ` `` y
contiene el `actor` del primer `Kill` de esa ronda. Consola limpia
(`vigilarConsola`). El criterio 4 (sin portapapeles) no se puede forzar en
Chromium sin borrar `navigator.clipboard`; es la misma rama de una linea que
`copiarResumen`, que tampoco la prueba el e2e.

**`docs/metricas.md`**: no hay numero nuevo (el texto copia datos de la
timeline). Nada que agregar.

**Orden.** `textoRonda.js` + vitest, `MatchDetail.jsx`, e2e, `npm run build`.

**Que puede romperse.** Un `useState` de mas en `DetallePartida` despues de
los returns tempranos romperia el orden de hooks: por eso va en
`CopiarRonda`. El boton dentro del `<h3>` suma "Copiar ronda" (y el aviso) al texto del
encabezado de la ronda. Los e2e que lo leen (`humo.spec.js`,
`#rondas .round-detail h3` con `toHaveText(/^R1\b/)` y con la etiqueta del
record) anclan solo el comienzo: siguen pasando. No usar `toHaveText` exacto
sobre ese `h3` en el test nuevo.

**Archivos ocupados.** La 79 (`entregado`, espera al humano) toca
`MatchDetail.jsx` en el import de `api.js`, los `useState` de
`DetallePartida` y el `page-head`; este diseno toca otro import, el `<h3>`
de la ronda y el final del archivo: hunks separados, merge limpio. La 111,
la 114 y la 116 agregan tests en otros puntos de `humo.spec.js`; ninguna
toca `MatchDetail.jsx`. No se frena.

**Verificacion manual.** `seed_demo`, abrir una partida, elegir una ronda
con bajas, `Copiar ronda`, pegar en un editor: cabecera con mapa, ronda,
lado, sitio y resultado, y una linea por baja con las mismas marcas que la
timeline; cambiar de ronda y el aviso desaparece.

Skills: no aplica (copiar al portapapeles ya resuelto tres veces en el repo).
Skills del repo: testing-strategy (vitest para el texto, e2e para el boton y el portapapeles; sin test de Django: no toca el backend).
OMC: plan=— · revisión=— · verificación=—

## Implementacion

Dev 20261113T1733Z-cudo1Sw, sobre `origin/dev@7892cc3`. Diseno completo, sin desvios de fondo.

- `frontend/src/textoRonda.js`: `textoRonda(ronda, mapa, miEquipo)`, cabecera
  `<mapa> · <label> · <lado> · sitio <site> · <resultado>` y una linea por
  `Kill`/`Death` ordenada por `order`, con las marcas de `marcasDeApertura`
  (apertura, entry, HS, tradeada) en el orden de los chips; `Sin bajas` si no
  hay; `null` sin ronda. `porOrden` copiada de `aperturas.js` como dice el diseno.
- `MatchDetail.jsx`: `CopiarRonda` al final del archivo, con su propio estado y
  `key={round.number}` dentro del `<h3>` de la ronda; aviso `Ronda copiada` o
  el de portapapeles negado de "Copiar resumen".
- e2e `el detalle de partida copia una ronda` en `humo.spec.js`, despues del de
  "copia el resumen": cabecera y nick de la primera baja leidos de la API, y
  ademas que el aviso desaparece al cambiar de ronda.

Desvios menores: un test vitest extra (`un evento sin reloj usa la raya de la
timeline`); el aviso dentro del `h3` lleva `fontWeight: normal`.

Criterios -> tests: texto y tres bajas con marcas (`la primera linea dice...`,
`una ronda de tres bajas sale en orden con sus marcas`, `ninguna linea termina
en espacio`); sin bajas (`sin bajas dice Sin bajas`); teamkill y muerte sin
autor (`un teamkill y una muerte sin autor usan la etiqueta de la timeline`);
sin portapapeles: misma rama que `copiarResumen` (el diseno ya dice que
Chromium no la puede forzar); e2e con consola limpia. Tests vistos en rojo
antes del codigo (`npx vitest run src/textoRonda.test.js`: modulo inexistente).

Revision ciega (`omc-code-reviewer`, eje de estandares): aprobar, 3 LOW.
Arreglado: el e2e pide de forma explicita dos rondas antes de cambiar de
pestaña. Sin cambio: `porOrden` duplicada (decision del diseno para no tocar
`aperturas.js`); el tooltip de la pestaña dice "defensa" con lado vacio y el
texto "lado desconocido" (ya estaba en la pagina; el texto coincide con el
`SideChip` "?").

Verificacion: `verificar.sh` VERDE 389abb4cb (1230 tests backend, 378 vitest, 102 e2e).

Skills del repo: testing-strategy (vitest para el texto, e2e para boton,
portapapeles y aviso; sin backend). modern-web-guidance y ux-copy no leidas: el
JSX y los textos copian el patron de "Copiar resumen" de la misma pagina.
Skills: ninguna de afuera.
OMC: plan=— · revisión=3 hallazgos LOW (1 arreglado) · verificación=—

## Revision 2026-11-13 sobre 6c4a6a5

(revisor 20261113T1802Z-c8dAf7p) Punto de partida: merge de `origin/dev`
(1de3c54, con la 118; sin conflictos); `verificar.sh`: VERDE bfa74506d
(1239 backend, 385 vitest, 104 e2e).

**Revision ciega, eje de estandares** (`omc-code-reviewer`, prompt de
`revision.md`, solo el diff): aprobar, sin hallazgos (casos borde mirados:
ronda sin bajas, sin `round`, partida sin "yo", mapa y lado vacios, aviso al
cambiar de ronda).

**Eje de intencion** (`omc-code-reviewer`, diff contra Que gana, Criterios y
Fuera de alcance; el diff pasa de 150 lineas): aprobar, los 5 criterios
cumplidos, 2 LOW:
- B1 [bug, LOW] el texto ordena por `order` y la timeline usa el orden de la
  API. **No se reproduce**: `Event.Meta.ordering = ["round", "order"]`
  (`models.py:231`), la API ya entrega en ese orden.
- T1 [test, LOW] el e2e solo exigia el nick del autor: un texto sin
  victimas seguia en verde. **Confirmado y cubierto por el revisor**: el e2e
  exige la linea `<reloj> <autor> mató a <victima>` de la primera baja.

Sin `omc-security-reviewer`: el diff no toca red, POST, `.rec` ni rutas.

**Ficha.** Criterio 1: vitest `la primera linea dice...`, `una ronda de
tres bajas sale en orden con sus marcas` (eventos desordenados, igualdad
exacta), `ninguna linea termina en espacio`. Criterio 2: `sin bajas dice Sin
bajas`. Criterio 3: `un teamkill y una muerte sin autor usan la etiqueta de
la timeline` (misma etiqueta que `Timeline`, `MatchDetail.jsx`). Criterio 4:
misma rama y aviso que `copiarResumen` (Chromium no puede forzar la falta de
portapapeles; verificacion de lectura). Criterio 5: e2e `el detalle de
partida copia una ronda` (cabecera, autor y victima, consola limpia). El
diff no sale de `archivos:`; sin numero nuevo (no pide `metricas.md`);
identificadores sin tildes, UI con tildes; sin `console.log`.

`verificar.sh` con el test del revisor: VERDE 6c4a6a575 (1239 backend,
385 vitest, 104 e2e).

Veredicto: aprobar.

Skills del repo: ninguna (revision con `revision.md`).
OMC: plan=— · revisión=2 hallazgos LOW (1 cubierto con test, 1 refutado) · verificación=—

## QA 2026-11-13 sobre 50c6ac7

(qa 20261113T1830Z-cTivbSq) Rama sin atraso contra `origin/dev` (1de3c54) y
sin conflicto (`git merge-tree --write-tree origin/dev HEAD`: salida 0).

- **check.sh**: `git show origin/dev:scripts/equipo-dev/verificar.sh | bash -s --`
  -> `VERDE 50c6ac708 en 193s: 1239 tests backend, 385 vitest, 104 e2e. Todo en verde.`
- **Chunk inicial**: `npx vite build` de `origin/dev` y de la rama: `index-*.js`
  200.00 kB en los dos (sin cambio); `MatchDetail-*.js` lazy 17.52 -> 18.97 kB.
- **Base vacia** (`SQLITE_PATH=<scratchpad>/qa121.sqlite3`, `migrate`,
  `runserver 127.0.0.1:8765`): `/api/matches/` 200, `/api/matches/1/` 404,
  `/api/matches/abc/` 404, `/api/matches/?limit=-1` 200, `/partidas/1` 200.
- **Base sembrada**: `seed_demo` (29 partidas, 203 rondas) y, con
  `tests/factories.py` (`make_round`, `make_event`) en `manage.py shell`, dos
  rondas mas en la partida 1: R9 sin bajas, lado y sitio vacios y
  `my_team_won=None`; R10 con un teamkill con HS, un `Death` sin victima, una
  baja `traded` y un `OperatorSwap`. `?until=foo` 200, `?page=-1` 200.
- **Ejercicio en Chromium** (Playwright, script en el scratchpad, sobre
  `/partidas/1`, portapapeles con permiso):
  - R1: `Club House · R1 · ataque · sitio B Church, B Arsenal Room · ganada` /
    `2:25 Thorn.exe mató a BearF99 (apertura, HS)`.
  - R9: `Club House · R9 · lado desconocido · sitio desconocido · sin resultado` / `Sin bajas`.
  - R10: `... · R10 · defensa · sitio 2F Office · ganada` / `2:30 Seba mató a
    BearF99 (apertura, HS)` / `1:40 Kaid_ murió` / `1:00 Thorn.exe mató a Chamo
    (tradeada)`: mismas etiquetas y chips que la timeline de la pagina; el
    `OperatorSwap` (que la timeline muestra) no se copia, como pide la ficha.
  - Ningun texto con espacio final, `undefined`, `null`, `NaN` ni `<`.
  - El aviso `Ronda copiada` desaparece al cambiar de ronda (0 apariciones).
  - Sin portapapeles (`navigator.clipboard = undefined` por `addInitScript`):
    `No se pudo copiar: el navegador no dio acceso al portapapeles.` (criterio 4,
    que el e2e no puede forzar).
  - Consola sin errores ni warnings.
- **Accesibilidad** (`accessibility-review`, mismas pantallas): el boton se
  alcanza con Tab justo despues de las pestañas de ronda y Enter copia; foco
  visible (outline del navegador); rol `button`, nombre `Copiar ronda`;
  contraste medido 12.92:1 el boton y 5.71:1 el aviso. Sin Critical ni Major.
  Minor: el aviso no tiene `role="status"`/`aria-live` (WCAG 4.1.3), igual que
  el `Copiado` que ya tenia "Copiar resumen"; va como idea a `ALCANCE.md` para
  los dos.
- **Mutacion** (`npx vitest run src/textoRonda.test.js`, archivo restaurado
  despues): sin `.sort(porOrden)` -> 1 falla; sin `Sin bajas` -> 1 falla; sin
  `tradeada` -> 1 falla; `Death` como `Kill` -> 1 falla.
- **Sin numero nuevo** en la UI: `validate-data` no aplica. Sin migracion,
  parser, Electron ni `.ps1`: nada para verificar en el PC.
- **omc-verifier** (receta 3, criterios + esta evidencia + diff): PASS, los 5
  criterios PASS, confianza alta; gaps de riesgo bajo: el `aria-live` de arriba
  y `porOrden` duplicada (decision del diseno).

Veredicto: aprobado.

Skills del repo: accessibility-review (0 Critical, 0 Major, 1 Minor
preexistente en el patron), testing-strategy (mutacion: 4 de 4 mutantes
muertos). validate-data y design-critique no aplican (sin numero ni panel nuevo).
OMC: plan=— · revisión=— · verificación=PASS

## Para el humano

(nada)
