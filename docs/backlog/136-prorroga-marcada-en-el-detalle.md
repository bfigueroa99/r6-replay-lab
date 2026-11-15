# 136. La prorroga marcada en el detalle de la partida

estado: con hallazgos
candado: -
rama: claude/equipo-dev/136-prorroga-marcada-en-el-detalle
tipo: funcionalidad
epica: revision-de-rondas
area: fullstack
prioridad: 3
fuente: ALCANCE.md F25 (la tira de Partidas, ficha 103, ya corta antes de la prorroga; el detalle no)
archivos: backend/replays/views.py, backend/tests/test_prorroga_en_detalle.py, frontend/src/prorrogaDetalle.js, frontend/src/prorrogaDetalle.test.js, frontend/src/pages/MatchDetail.jsx, frontend/src/styles.css, frontend/e2e/humo.spec.js
turnos: po 20261113T2157Z-cG2vDSe, arquitecto 20261114T0040Z-chQsvnq, dev 20261114T0104Z-choi73m, revisor 20261114T0104Z-cWK4yQD, qa 20261115T0219Z-i32143169

## PR

## Que gana quien usa la app

En el detalle de una partida, las rondas de prorroga llevan una marca y un
separador antes de la primera, como ya hace la tira de rondas del listado de
Partidas: hoy en el detalle una ronda de prorroga se lee como una mas y no se
ve donde termino el tiempo reglamentario.

## Criterios de aceptacion

- [x] `/api/matches/<id>/` devuelve en cada ronda `overtime` (`true` si
      `Round.overtime_number > 0`), la misma regla que la tira de
      `/api/matches/`. Test Django con una partida de 3 rondas normales y 2 de
      prorroga, y otro sin prorroga (todas `false`).
- [x] En el detalle, la lista o pestañas de rondas muestran un separador
      (texto "Prórroga") antes de la primera ronda de prorroga y cada ronda de
      prorroga con una marca visible y nombre accesible que diga "prórroga".
      Logica pura en un helper con vitest (sin prorroga no hay separador; el
      separador va una sola vez).
- [x] La tira o el selector de ronda siguen funcionando con teclado igual que
      antes (las flechas no se detienen en el separador). Test vitest o e2e.
- [x] e2e: `seed_demo` no tiene prorroga; el e2e abre un detalle del seed y
      verifica que no aparece el separador y la consola queda limpia.

## Fuera de alcance

- Cambiar la tira de Partidas (ya lo hace).
- Metricas de prorroga nuevas (ficha 127, Tendencias).

## Diseno

(arquitecto 20261114T0040Z-chQsvnq) Filtros duros: pasa (`Round.overtime_number`
ya esta en la base; sin red, sin dependencias, sin POST, sin migracion). Una
sola forma: la misma regla de la tira de Partidas (ficha 103,
`tiraRondas.js`), llevada al selector de rondas del detalle.

**Archivos:**
- `backend/replays/views.py`, `match_detail`: en el dict `datos` de cada
  ronda, `"overtime": rnd.overtime_number > 0`, al lado de `"number"`. Es la
  regla de `/api/matches/` (`views.py`, la tira: `overtime > 0`). Nada mas
  cambia en el payload.
- `backend/tests/test_prorroga_en_detalle.py` (Django, `factories.py`):
  `test_detalle_marca_las_rondas_de_prorroga` (3 rondas normales + 2 con
  `overtime_number` 1 y 2: `[False, False, False, True, True]`);
  `test_detalle_sin_prorroga_las_marca_todas_false`;
  `test_overtime_del_detalle_coincide_con_la_tira_del_listado` (misma
  partida, `/api/matches/` y `/api/matches/<id>/` dan la misma lista).
- `frontend/src/prorrogaDetalle.js`: `pestanasDeRondas(rounds)` -> por ronda
  `{prorroga: bool, corteAntes: bool}`; `corteAntes` solo en la primera con
  `overtime` (la misma logica de `celdasDeTira`, sin importarla: aquella
  recibe el `strip` del listado con otros campos). Con `rounds` vacio o
  nulo, `[]`. Misma longitud y orden que `rounds`: el JSX las recorre juntas
  por indice.
- `frontend/src/prorrogaDetalle.test.js` (vitest):
  `sin prorroga no hay corte`; `el corte va una sola vez, antes de la
  primera de prorroga`; `cada ronda de prorroga queda marcada y las
  normales no`; `sin rondas devuelve lista vacia`.
- `frontend/src/pages/MatchDetail.jsx`, bloque `.round-tabs`
  (`MatchDetail.jsx:172`): antes del boton de la primera de prorroga, un
  `<span className="round-tabs-corte">Prórroga</span>` (texto visible, no
  focusable, no es `button` ni `.round-tab`: el e2e cuenta `.round-tab` y el
  teclado sigue por indice); el boton de una ronda de prorroga suma la clase
  `overtime` y, dentro, `<span className="solo-lector"> · prórroga</span>`
  (la clase que ya existe en `styles.css:36`). No `aria-label`: pisaria el
  texto visible "R4 ATK" y romperia label-in-name (WCAG 2.5.3). El `title`
  queda como esta; con prorroga suma " · prórroga". Las flechas, `p` y
  el ancla `#ronda-N` no cambian: navegan por indice de `rounds`
  (`navegacionRondas.js`) y el separador no es una ronda.
- `frontend/src/styles.css` (el CSS de `.round-tabs`, linea ~406):
  `.round-tabs-corte` (texto chico, `color: var(--muted)`, `align-self:
  center`, borde izquierdo que separa) y `.round-tab.overtime` con una marca
  que no dependa solo del color (por ejemplo `border-style: dashed`), con
  contraste medido por QA.
- `frontend/e2e/humo.spec.js`: en el test del detalle de partida, afirmar
  que `seed_demo` (sin prorroga) no muestra `.round-tabs-corte` y que
  ninguna `.round-tab` tiene la clase `overtime`; consola limpia. La prorroga
  con datos la cubre el test Django y el vitest: el seed no la tiene y
  cambiarlo cambiaria los numeros de todo el e2e.

**Orden:** test Django -> clave en la vista -> vitest -> helper -> JSX + CSS
-> e2e -> `npm run build`.

**Puede romperse:** el `title` del boton que lee algun e2e (se mantiene);
una `.round-tab` nueva que el e2e de flechas contaria (por eso el separador
es un `span` con otra clase).

**Archivos ocupados:** `MatchDetail.jsx` y `views.py` los toca la 79 (en
espera del humano) en la cabecera de la pagina y en el POST de exclusion,
no en `.round-tabs` ni en el dict de la ronda: sin pisada, no se frena. La
140 (`propuesto`) va a tocar el mismo selector: si se disena despues, que
diga "Implementar despues de que #136 se mergee".

**Verificacion manual:** abrir una partida real con prorroga: el separador
aparece una vez, las flechas pasan de la ultima ronda normal a la primera
de prorroga sin frenar.

Skills: no aplica (una marca en un selector existente, con precedente en la tira de Partidas).
Skills del repo: testing-strategy (Django para la clave, vitest para la regla del corte, e2e solo para la ausencia sobre el seed); dataviz y statistical-analysis no aplican (no hay numero ni grafico nuevo).
OMC: plan=— · revisión=— · verificación=—

## Implementacion

(dev 20261114T0104Z-choi73m) Quedo el diseno completo, sin desvios:

- `match_detail` devuelve `overtime` (`overtime_number > 0`) en cada ronda, la
  regla de la tira de `/api/matches/`.
- `prorrogaDetalle.js`: `pestanasDeRondas(rounds)` -> `{prorroga, corteAntes}`
  por ronda, mismo orden y longitud; `[]` con `null`/vacio.
- `MatchDetail.jsx`: `<span className="round-tabs-corte">Prórroga</span>`
  antes de la primera de prorroga (no es `.round-tab`, asi las flechas, `p` y
  `#ronda-N` siguen por indice); el boton de prorroga suma la clase `overtime`,
  `<span className="solo-lector"> · prórroga</span>` y " · prórroga" en el
  `title`. Sin `aria-label`.
- `styles.css`: `.round-tab.overtime` con borde punteado (no solo color) y
  `.round-tabs-corte` (texto chico, `--muted`, borde izquierdo).
- e2e: en "el detalle de una partida se abre desde la lista", el seed sin
  prorroga no muestra `.round-tabs-corte` ni `.round-tab.overtime`; consola
  limpia.

Criterios -> tests: (1) `test_detalle_marca_las_rondas_de_prorroga`,
`test_detalle_sin_prorroga_las_marca_todas_false`,
`test_overtime_del_detalle_coincide_con_la_tira_del_listado`
(`backend/tests/test_prorroga_en_detalle.py`); (2) `prorrogaDetalle.test.js`
(corte una vez, marca por ronda, vacio, `overtime` ausente); (3) los e2e de
flechas y de `p` existentes siguen verdes (cuentan `.round-tab`, el separador
no lo es); (4) e2e del detalle sobre el seed.

TDD: los 3 tests Django en rojo (KeyError `overtime`) y el vitest sin modulo
antes del codigo.

Revision ciega (omc-code-reviewer, `revision.md`): aprobar, 1 LOW sin
arreglar: el e2e no renderiza una prorroga en Chromium (el seed no la tiene y
cambiarlo mueve los numeros de todo el e2e, como dice el diseno); la rama del
JSX la ve QA con una partida real o la verificacion manual.

Verificacion: `verificar.sh` VERDE 3417a0ad0 (1360 tests backend, 448 vitest,
119 e2e).

Skills: no aplica (sin dominio nuevo).
Skills del repo: test-driven-development (rojo visto en Django y vitest),
testing-strategy (clave en Django, regla del corte en vitest, ausencia en
e2e), ux-copy ("Prórroga" calcado de la tira de Partidas);
modern-web-guidance no se consulto: el marcado sigue el patron del propio
selector y de `.solo-lector`.
OMC: plan=— · revisión=1 LOW (0 arreglados) · verificación=—

## Revision 2026-11-14 sobre 5053227

(revisor 20261114T0104Z-cWK4yQD)

Veredicto: aprobar -> `revisado`.

Base: `origin/dev` (f34baba con la 135, 7e7e8c6) fusionado sin conflicto;
`verificar.sh`: VERDE 5053227ed (1370 tests backend, 454 vitest, 120 e2e).

Revision a ciegas (omc-code-reviewer, eje estandares; diff de 132 lineas, un
tema: no suma eje de intencion): aprobar, 3 LOW.

Confirmado por el lider (grep sobre el diff):
- [estilo] LOW `frontend/src/styles.css:425`, `frontend/src/pages/MatchDetail.jsx:178`,
  `frontend/e2e/humo.spec.js:794`: comentarios con ñ ("pestaña", "pestañas");
  `CLAUDE.md` pide comentarios sin tildes. Arreglo: "pestana(s)". No bloquea.

Sin hallazgos en: la regla `overtime_number > 0` es la de la tira (un test la
compara contra `/api/matches/`); partida sin rondas y `overtime` ausente
cubiertos en vitest; el corte es un `<span>` fuera de los `.round-tab` y
`.round-tabs` no tiene `role="tablist"`, asi que no queda un hijo ARIA
invalido ni frena las flechas (navegan por indice: `pasoDeTecla`); marca con
trazo y no solo color; textos de UI con tilde; sin numero nuevo (no pide fila
en `metricas.md`); sin `print` ni `console.log`.

Ficha: criterios 1, 2 y 4 con test; el 3 lo sostienen los e2e de flechas
existentes (`navegar-partidas.spec.js`), que con `seed_demo` no renderizan el
corte: lo anota tambien la Implementacion; QA puede mirarlo con una partida
sembrada con prorroga. El diff no sale de `archivos:` sin explicacion.

Skills: no aplica.
Skills del repo: ninguna (revision con el prompt de `revision.md`).
OMC: plan=— · revisión=3 LOW (0 arreglados, confirmados) · verificación=—

## QA 2026-11-15 sobre f7a821d

(qa 20261115T0219Z-i32143169)

Veredicto: `con hallazgos`. Un criterio falla: la marca de cada ronda de
prorroga no se ve en reposo (1,26:1 contra el fondo). Todo lo demas pasa.

Base: rama con `origin/dev` (b2991fe) fusionado sin conflicto (82b5c14).

- **check.sh**: `git show origin/dev:scripts/equipo-dev/verificar.sh | bash -s --`
  -> `VERDE f7a821db7 en 261s: 1370 tests backend, 454 vitest, 120 e2e. Todo en verde.`
- **Base sembrada** (`factories.py`, script temporal en el scratchpad, base
  en `SQLITE_PATH`/`DATA_DIR` propios): partida 1 con 6 rondas normales y 2
  de prorroga (`overtime_number` 1 y 2), 2 sin prorroga, 3 sin rondas, 4 con
  una sola ronda que es de prorroga, 5 con la prorroga sin ganador.
  `runserver 127.0.0.1:8123 --noreload` sembrada y `:8124` vacia.
  - `curl /api/matches/<id>/` -> `overtime` por ronda: 1 `[F,F,F,F,F,F,T,T]`,
    2 `[F,F,F]`, 3 `[]`, 4 `[T]`, 5 `[F,F,F,T]`; la tira de `/api/matches/`
    da las mismas listas para las 5.
  - Bordes: `/api/matches/999/`, `/0/`, `/-1/`, `/abc/` -> 404;
    `/api/matches/1/?until=foo`, `?side=Attack`, `/api/matches/?page=-1`,
    `?until=foo`, `?map=`, `?days=99999999999` -> 200. Base vacia:
    `/api/matches/` 200 con `matches: []`, `/api/matches/1/` 404 con
    `{"error": "partida no encontrada"}`.
- **Chunk inicial** (`vite build`): `index-*.js` 200.34 kB en `origin/dev` y
  en la rama (sin cambio); `index-*.css` 14.57 -> 14.75 kB (+1,2 %).
- **accessibility-review** (Chromium con Playwright, script en el
  scratchpad, sobre la base sembrada; consola sin errores ni warnings en las
  5 partidas):
  - Nombre y rol: `ariaSnapshot` de la tira -> `button "R6 DEF"`,
    `text: Prórroga`, `button "R7 ATK · prórroga"`, `button "R8 DEF ·
    prórroga"`; ningun boton normal dice prorroga. El corte es un `SPAN`
    sin rol ni `tabIndex`. `title` de R7: "B Church, B Arsenal Room · ataque
    · prórroga". Pasa.
  - Teclado: desde R6, flecha derecha -> R7 -> R8 -> R8 (tope); dos
    izquierdas -> R6; Tab desde R6 va a R7 (el corte no toma foco);
    `#ronda-8` abre R8; foco visible (`outline auto 1px`). Pasa.
  - Corte: una sola vez y justo antes de R7 (partida 1); con una sola ronda
    de prorroga va primero (partida 4: `round-tabs-corte`, `round-tab ...
    overtime`); sin prorroga, ni corte ni `overtime` (partida 2); prorroga
    sin ganador se marca igual (partida 5); partida sin rondas abre sin
    pestañas y sin error (partida 3). Pasa.
  - Contraste: texto "Prórroga" `rgb(139,152,169)` sobre `rgb(23,30,41)`,
    11 px -> **5,71:1** (pide 4,5:1). Pasa. Borde punteado de una pestaña de
    prorroga no activa: `dashed 1px rgb(38,48,65)` sobre `rgb(23,30,41)` ->
    **1,26:1** (WCAG 1.4.11 pide 3:1); es el mismo color del borde liso de
    las normales, asi que en reposo R7 y R8 se ven igual que R6 (captura en
    el scratchpad: el punteado no se distingue). Solo se ve en la pestaña
    activa, donde el borde es el acento.
- **Mutaciones** (codigo roto a mano y restaurado con `git checkout`):
  `overtime_number >= 0` en `match_detail` -> los 3 tests de
  `tests.test_prorroga_en_detalle` caen; `corteAntes = prorroga` (sin
  `!enProrroga`) -> cae "el corte va una sola vez"; `prorroga` siempre
  `false` -> caen 2 de 5 de `prorrogaDetalle.test.js`.
- Sin migracion, `recompute`, parser, Electron ni `.ps1`: no hace falta
  `## Verificar en el PC`. Sin numero nuevo: `validate-data` no aplica. Sin
  pagina ni panel nuevo: `design-critique` no aplica.

### Hallazgo

- [a11y] **Major** (WCAG 1.4.11; criterio 2 "cada ronda de prorroga con una
  marca visible") `frontend/src/styles.css`, `.round-tab.overtime`.
  Que pasa: la marca es solo `border-style: dashed` con el color de borde de
  siempre (`--border`, 1,26:1 contra el fondo): en reposo una pestaña de
  prorroga no se distingue de una normal. El corte "Prórroga" si se ve, pero
  el criterio pide ademas la marca por ronda, y el diseno dejo su contraste
  para que lo midiera QA.
  Repro: base de arriba, `/partidas/1`, sin pasar el mouse: R7 y R8 se ven
  como R6; en Chromium,
  `getComputedStyle(document.querySelector('#rondas .round-tab.overtime:not(.active)')).borderTopColor`
  -> `rgb(38, 48, 65)` sobre el fondo `rgb(23, 30, 41)` de `.panel`.
  Arreglo sugerido: un color de borde de 3:1 o mas para la pestaña de
  prorroga no activa (por ejemplo `--muted`, 5,71:1), sin pisar el acento de
  la activa: `.round-tab.active` va antes en `styles.css` y tiene la misma
  especificidad, asi que la regla nueva necesita `:not(.active)` o ir antes.
  Test a agregar: un e2e no puede (el seed no tiene prorroga); medirlo de
  nuevo en la proxima QA con la misma base.

Skills: no aplica.
Skills del repo: accessibility-review (1 Major: borde de prorroga 1,26:1;
corte 5,71:1, teclado y nombres pasan); design-critique y validate-data no
aplican (sin panel ni numero nuevo).
OMC: plan=— · revisión=— · verificación=— (no se llega a `aprobado`)

## Para el humano

(nada)
