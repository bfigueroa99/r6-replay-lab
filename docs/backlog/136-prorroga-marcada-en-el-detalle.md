# 136. La prorroga marcada en el detalle de la partida

estado: en curso 2026-11-14T01:05Z
candado: -
rama: claude/equipo-dev/136-prorroga-marcada-en-el-detalle
tipo: funcionalidad
epica: revision-de-rondas
area: fullstack
prioridad: 3
fuente: ALCANCE.md F25 (la tira de Partidas, ficha 103, ya corta antes de la prorroga; el detalle no)
archivos: backend/replays/views.py, backend/tests/test_prorroga_en_detalle.py, frontend/src/prorrogaDetalle.js, frontend/src/prorrogaDetalle.test.js, frontend/src/pages/MatchDetail.jsx, frontend/src/styles.css, frontend/e2e/humo.spec.js
turnos: po 20261113T2157Z-cG2vDSe, arquitecto 20261114T0040Z-chQsvnq

## PR

## Que gana quien usa la app

En el detalle de una partida, las rondas de prorroga llevan una marca y un
separador antes de la primera, como ya hace la tira de rondas del listado de
Partidas: hoy en el detalle una ronda de prorroga se lee como una mas y no se
ve donde termino el tiempo reglamentario.

## Criterios de aceptacion

- [ ] `/api/matches/<id>/` devuelve en cada ronda `overtime` (`true` si
      `Round.overtime_number > 0`), la misma regla que la tira de
      `/api/matches/`. Test Django con una partida de 3 rondas normales y 2 de
      prorroga, y otro sin prorroga (todas `false`).
- [ ] En el detalle, la lista o pestañas de rondas muestran un separador
      (texto "Prórroga") antes de la primera ronda de prorroga y cada ronda de
      prorroga con una marca visible y nombre accesible que diga "prórroga".
      Logica pura en un helper con vitest (sin prorroga no hay separador; el
      separador va una sola vez).
- [ ] La tira o el selector de ronda siguen funcionando con teclado igual que
      antes (las flechas no se detienen en el separador). Test vitest o e2e.
- [ ] e2e: `seed_demo` no tiene prorroga; el e2e abre un detalle del seed y
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

## Revision

## QA

## Para el humano

(nada)
