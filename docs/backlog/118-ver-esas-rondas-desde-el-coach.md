# 118. "Ver esas rondas" desde las señales del Coach

estado: aprobado
candado: -
rama: claude/equipo-dev/118-ver-esas-rondas-desde-el-coach
tipo: funcionalidad
epica: revision-de-rondas
area: fullstack
prioridad: 3
fuente: ALCANCE.md F15 (salio del PR #14, cerrado sin merge el 2026-11-05; complementa la 112, que salta a una ronda puntual)
archivos: backend/replays/analytics/coach.py (_insight, reglas), backend/tests/test_coach.py, frontend/src/enlaceSenal.js (nuevo), frontend/src/enlaceSenal.test.js (nuevo), frontend/src/pages/Coach.jsx, frontend/e2e/humo.spec.js, docs/metricas.md
turnos: po 20261113T0404Z-cnRfz4a, arquitecto 20261113T0804Z-cJw5MQs, dev 20261113T1651Z-cxTme8t, revisor 20261113T1732Z-cdpsq83, qa 20261113T1802Z-c8dAf7p

## PR

## Que gana quien usa la app

Cada señal del Coach que habla de un mapa, un lado, un operador o un sitio
lleva un enlace "Ver esas rondas" que abre el Resumen ya filtrado por eso, y la
de un rival abre Duelos: de "Kafe es tu peor mapa" se pasa a los numeros de
Kafe en un clic, sin armar los filtros a mano.

## Criterios de aceptacion

- [ ] Cada señal de `build_insights` (`coach.py`) trae un campo `filters`
      (dict, vacio si la señal es general) con los filtros que la definen,
      en los mismos nombres que la API acepta (`map` como slug, `side`,
      `operator`, `site`); test: la señal `mapa-debil` trae `{"map":
      <slug>}` y una general trae `{}`.
- [ ] Los filtros globales que ya tenia la consulta del Coach (fechas, tipo,
      modo, sesion) se suman al enlace: abrir el enlace no pierde el periodo
      que estaba mirando. Vitest de la funcion pura que arma el `href`.
- [ ] En Coach, una señal con `filters` no vacio muestra el enlace "Ver esas
      rondas" a `/?<query>`; una de rival (`nemesis`, duelos por operador)
      enlaza a `/duelos?<query>`; una general no muestra enlace.
- [ ] e2e: desde `/coach` con `seed_demo`, el enlace de una señal de mapa
      abre el Resumen con el filtro de mapa puesto (selector y URL), consola
      limpia.

## Fuera de alcance

- Saltar a una ronda puntual (eso es la 112, `#ronda-N`).
- Señales nuevas o cambiar el texto de las que hay.
- Enlazar a una lista de rondas (no existe; es F1).

## Diseno

(arquitecto 20261113T0804Z-cJw5MQs) Filtros duros: pasa. Solo enlaza a filtros que la
API ya acepta (`FILTER_KEYS`); sin red, sin dependencias, sin POST, sin
migracion. Una forma obvia (~200 lineas): sin arena ni consenso.

**Correcciones de premisa.**
- No hay filtro por operador rival ni por rival en la barra (`operator` es
  **tu** operador). Las señales `operador-rival` y `nemesis` enlazan a
  `/duelos` con los filtros globales y `filters: {}`, sin filtro propio.
- No hay filtro de spawn: `spawn-debil` y la `zona-*` de un spawn enlazan
  con `map` + `side=Attack` (el corte mas fino que la barra tiene).
- La barra filtra el mapa por **slug** (todas las versiones; `/api/filters/`
  no ofrece versiones). El enlace usa `slug`: en un mapa rehecho, "Ver esas
  rondas" abre las dos versiones juntas. Aceptable y reversible.
- seed_demo no produce `mapa-debil` (produce `operador-debil` Jager,
  `desbalance-lados`, `zona-dormidero`...): el e2e usa `operador-debil`.

**Backend, `backend/replays/analytics/coach.py`.**
- `_insight(..., filters: dict | None = None, target: str = "/")` agrega dos
  claves a cada señal: `"filters": filters or {}` y `"target"` (`"/"` o
  `"/duelos"`). Las señales que no pasan nada quedan `{}` y `"/"`.
- Constante `LADO = {"ataque": "Attack", "defensa": "Defense"}`.
- Que pasa cada regla (los valores salen de la fila que ya eligio la regla):
  - `duelos-apertura-{label}`, `muerte-temprana-{label}`,
    `muertes-tempranas-{label}`: `{"side": LADO[label]}`.
  - `sin-tiempo-ataque`: `{"side": "Attack"}`.
  - `desbalance-lados`: `{"side": LADO[weak]}`.
  - `mapa-debil` / `mapa-fuerte`: `{"map": fila["slug"]}`.
  - `sitio-debil`: `{"map": worst["slug"], "site": worst["site"]}`.
  - `operador-debil` / `operador-fuerte`: `{"operator": fila["operator"],
    "side": fila["side"]}` (las filas de `by_operator` son operador + lado).
  - `spawn-debil`: `{"map": worst["slug"], "side": "Attack"}`.
  - `zona-dormidero` / `zona-solida`: la tupla de `zonas` suma un 5.o
    elemento con los filtros: sitio -> `{"map": fila["slug"], "site":
    fila["site"]}`; spawn -> `{"map": fila["slug"], "side": "Attack"}`.
  - `operador-rival`, `nemesis`: `target="/duelos"`, `filters` vacio.
  - El resto (`sin-datos`, `kst`, `headshots*`, `muertes-*` generales,
    `sin-clutches`, `rondas-finales`, `fatiga-sesion`, `bajon`,
    `racha`, `duelos-apertura`, `duelos-apertura-fuerte`): nada.
- El texto de las señales no cambia.

**Tests backend, `backend/tests/test_coach.py`**, clase nueva
`EnlaceDeLasSenalesTests` (con `seed` y `make_*` del archivo):
- `test_la_senal_de_mapa_trae_el_slug`: dos mapas, uno flojo -> `mapa-debil`
  con `filters == {"map": <slug>}` y `target == "/"`.
- `test_la_senal_de_operador_trae_operador_y_lado`.
- `test_la_senal_de_sitio_trae_mapa_y_sitio`.
- `test_el_desbalance_de_lados_filtra_el_lado_flojo`.
- `test_una_senal_general_no_trae_filtros` (`kst` o `sin-datos`: `{}`).
- `test_todas_las_senales_traen_filters_y_target`: sobre un historial que
  dispara varias, cada señal tiene las dos claves y los `filters` solo usan
  claves de `aggregates.FILTER_KEYS`.
- `test_las_senales_de_rival_van_a_duelos` (`nemesis` u `operador-rival`
  con `target == "/duelos"`; si armarlas es caro, una de las dos).

**Frontend.**
- `frontend/src/enlaceSenal.js` (nuevo, puro): `enlaceDeSenal(insight,
  filtros)` -> `null` si `insight.target` es `"/"` y `filters` vacio o
  ausente; si no, `conFiltros(target, { ...filtros, ...insight.filters })`
  de `filtrosUrl.js` (las claves de la señal pisan las globales: `map` de
  la señal gana al `map` de la barra; fechas, tipo, modo y sesion se
  conservan). Un `target` que no sea `"/"` ni `"/duelos"` -> `null`.
- `frontend/src/enlaceSenal.test.js` (vitest): señal general -> `null`;
  señal de mapa con `{days: '30', match_type: 'Ranked'}` globales -> `to`
  con `pathname: '/'` y la query con las tres; la señal pisa el `map`
  global; señal de rival -> `pathname: '/duelos'` con los globales; target
  desconocido -> `null`.
- `frontend/src/pages/Coach.jsx`: en cada `.insight`, si
  `enlaceDeSenal(insight, filters)` no es `null`,
  `<Link className="btn small" to={...}>Ver esas rondas</Link>` (en la
  señal de rival el texto es `Ver en Duelos`) al final de la linea de
  `metric`/`sample`/`scope`. La ficha **111** (`disenado`, sin rama)
  tambien toca `Coach.jsx` (mueve `GROUPS` y `format`): no es rama abierta,
  no frena, pero el segundo que llegue mergea `dev` primero.
- `frontend/src/pages/Dashboard.jsx` ("Lo que hay que corregir"): fuera de
  alcance (no lo pide la ficha).

**e2e, `frontend/e2e/humo.spec.js`**, test `una senal del Coach abre el
Resumen filtrado`: leer `/api/coach/`, tomar la señal `operador-debil`
(seed_demo: Jager, lado de la fila); en `/coach`, clic en "Ver esas rondas"
de la tarjeta con su `title`; la URL es `/` con `operator=<op>` y
`side=<lado>`; el `h1` dice "Resumen" y el selector de operador de la barra
tiene ese valor. Consola limpia. Valores desde la API, no a mano.

**`docs/metricas.md`**: no hay numero nuevo. Una frase donde se describe el
Coach (o en Cortes): "Ver esas rondas abre el Resumen con los filtros que
definen la señal, sumados a los de la barra; las de rival abren Duelos".

**Orden.** `coach.py` + tests, `enlaceSenal.js` + vitest, `Coach.jsx`,
e2e, metricas, `npm run build`.

**Que puede romperse.** Las claves nuevas no rompen a nadie que lea las
señales (Resumen, Coach, export): son aditivas. `App.jsx` ya aplica la query
de un `Link` interno con filtros (ficha 96): no se toca. Un valor de
operador con caracteres raros pasa por `queryDeFiltros`, que valida y
recorta como cualquier URL pegada.

**Archivos ocupados.** Ramas abiertas (79, 110, 113, 117): ninguna toca
`coach.py`, `test_coach.py`, `Coach.jsx` ni `enlaceSenal.js`; la 110 y la
113 tocan `humo.spec.js` en otros tests. No se frena.

**Verificacion manual.** `seed_demo`, `/coach`: "Con Jager rindes..." ->
"Ver esas rondas" abre `/?operator=Jager&side=Defense` (o el lado de su
fila) con la barra puesta; una señal de rival abre `/duelos`; `kst` no
tiene enlace. Con `?days=30` en la barra, el enlace lo conserva.

Skills: no aplica (enlaces a filtros que la app ya tiene; `filtrosUrl.js` resuelve la query).
Skills del repo: testing-strategy (Django para el mapeo señal -> filtros, vitest para armar el enlace, e2e para el clic y la barra).
OMC: plan=— · revisión=— · verificación=—

## Implementacion

(dev 20261113T1651Z-cxTme8t) Diseno completo:

- `coach.py`: `_insight` suma `filters` (por defecto `{}`) y `target` (`"/"`);
  constante `LADO`; cada regla pasa los filtros que dice el Diseno (lado,
  mapa por slug, sitio con su mapa, operador con su lado, spawn como mapa en
  ataque, zonas por la tupla de `_posicion`); `operador-rival` y `nemesis`
  van a `/duelos`. El texto de las señales no cambia.
- `enlaceSenal.js`: `enlaceDeSenal` (suma los filtros de la señal a los de
  la barra, los de la señal pisan; `null` en el Resumen sin filtros propios
  y con destino desconocido) y `textoDelEnlace` ("Ver esas rondas" / "Ver en
  Duelos"). `Coach.jsx`: `Link` con `btn small` al final de `.meta`.
- `metricas.md`: parrafo "Ver esas rondas" bajo la muestra minima.

Desvios del diseno (revision ciega, corregidos):
- HIGH: ninguna pagina muestra el selector de Sitio, asi que el `site` de
  `sitio-debil` y de las zonas quedaba puesto y sin verse en todas las
  paginas. `Filters.jsx` (fuera de `archivos:`) muestra Sitio tambien cuando
  `value.site` viene puesto; e2e `el sitio que trae una señal del Coach se ve
  en la barra y se quita` (cae sin el arreglo).
- MEDIUM: con una version elegida en la barra (`map=<map_id>`) el slug de la
  señal la pisaba y el enlace abria las dos versiones. `build_insights` quita
  `map` de los filtros de la señal si la barra ya trae mapa (la señal se
  calculo dentro de el); test `test_con_mapa_en_la_barra_la_senal_no_lo_pisa`
  (cae sin el arreglo).
- LOW: tests de `spawn-debil` y de los valores de `side`; comentarios sin
  tildes. `test_posicion.py` (fuera de `archivos:`) suma los `filters` de las
  zonas de sitio y de spawn.

Tests vistos en rojo antes del codigo: backend (7 con `KeyError: 'filters'`),
vitest `enlaceSenal.test.js` (sin modulo). Criterios -> tests: `filters` por
señal y `{}` en las generales (`EnlaceDeLasSenalesTests`, 9, y
`test_posicion.py`); filtros globales conservados (vitest "conserva el
periodo y el tipo", "pisa el de la barra"); enlace a `/` o `/duelos` o
ninguno (vitest y `test_las_senales_de_rival_van_a_duelos`); e2e `una señal
del Coach abre el Resumen filtrado` (operador-debil del seed: URL, `h1` y
selector de operador; `kst` sin enlace; consola limpia) mas el de sitio.

verificar.sh: VERDE 95c5d88fc (1209 backend, 368 vitest, 101 e2e).

Skills: no aplica.
Skills del repo: ux-copy (dev: "Ver esas rondas" / "Ver en Duelos" empiezan con verbo y nombran el destino), modern-web-guidance no corrida (pide `npx` con red; el cambio es un `Link` con la clase `btn small` que ya existe, sin CSS nuevo).
OMC: plan=— · revisión=5 hallazgos (5 arreglados; 1 HIGH) · verificación=—

## Revision 2026-11-13 sobre c29903c

(revisor 20261113T1732Z-cdpsq83) Punto de partida: merge de `origin/dev`
(09c86a4, sin conflictos); `verificar.sh`: VERDE 09c86a4e5 (1220 backend,
371 vitest, 102 e2e).

**Revision ciega, eje de estandares** (`omc-code-reviewer`, prompt de
`revision.md`, solo el diff): aprobar, 1 MEDIUM.
- M1 [bug, MEDIUM] `coach.py:447` (y las señales de sitio, spawn y zona):
  las filas de `by_map`/`by_site`/`positioning` agrupan por `(slug,
  map_id)`, asi que en un mapa rehecho la señal habla de una version y el
  enlace por slug abre las dos (otro winrate en el Resumen). **Confirmado
  leyendo el codigo**, pero es la decision del diseno ("Aceptable y
  reversible") y esta documentado en `metricas.md`; con una version ya
  elegida en la barra la señal no la pisa
  (`test_con_mapa_en_la_barra_la_senal_no_lo_pisa`). No bloquea: va a
  `## Para el humano` como mejora (mandar `map=<map_id>` cuando el slug
  tiene mas de una version, cuidando `map_id=0`).

**Eje de intencion** (`omc-code-reviewer`, diff contra Que gana, Criterios
y Fuera de alcance): pidio corregir por 1 MEDIUM, mas 2 LOW.
- I1 [MEDIUM] el e2e del criterio 4 nunca comprobaba el **mapa**: uno usa
  `operador-debil` y el otro solo miraba `site`. **Confirmado** (en
  `seed_demo` no sale `mapa-debil`; la señal con `site` es `zona-dormidero`,
  que trae `map: club-house`). **Cubierto por el revisor** con aserciones
  que pasan: el e2e del sitio ahora exige `map` en la URL y en el selector
  Mapa (`getByLabel('Mapa')`).
- I2 [LOW] el enlace de rival dice "Ver en Duelos": el criterio no fija ese
  texto; no es hallazgo.
- I3 [LOW] el vitest no cubria fechas ni modo: **cubierto** con
  `conserva las fechas y el modo de la barra` (`since`, `until`,
  `gamemode` mas el `map` de la señal).

**Ficha.** Criterio 1: `test_la_senal_de_mapa_trae_el_slug`,
`test_una_senal_general_no_trae_filtros`,
`test_todas_las_senales_traen_filters_y_target`. Criterio 2: vitest de
`enlaceSenal.test.js` (7). Criterio 3: `enlaceDeSenal` + e2e (general sin
enlace, rival a `/duelos` en vitest). Criterio 4: los dos e2e de Coach ->
Resumen (operador y lado; mapa y sitio, selector y URL), consola limpia. El
diff no sale de `archivos:` salvo `Filters.jsx` y `test_posicion.py`,
explicados en Implementacion; fila en `metricas.md`; sin tildes en
identificadores, UI con tildes; sin `print` ni `console.log`.

`verificar.sh` con los tests del revisor: VERDE c29903c38 (1220 backend,
372 vitest, 102 e2e).

Veredicto: aprobar.

Skills del repo: ninguna (revision con `revision.md`).
OMC: plan=— · revisión=3 hallazgos MEDIUM (1 cubierto con test, 1 decision del diseno al humano) y 2 LOW (1 cubierto) · verificación=—

## QA 2026-11-13 sobre f106044

(qa 20261113T1802Z-c8dAf7p) Punto de partida: merge de `origin/dev`
(7892cc3, sin conflictos) sobre la rama.

- **check.sh** (`verificar.sh`): VERDE f10604491 en 177 s (1239 backend,
  377 vitest, 103 e2e).
- **Base sembrada** (script en el scratchpad con `factories.py`: Club House
  fuerte, Border flojo con 1F Armory y Mute en defensa, Consulate con
  `map_id` 1 y 2, un rival; `migrate` + `recompute`) en `runserver :8118`, y
  base vacia en `:8119`. `curl /api/coach/`: 11 señales; con `filters`:
  `mapa-debil {map: border}`, `sitio-debil {map: border, site: 1F Armory}`,
  `operador-debil {operator: Mute, side: Defense}`, `zona-dormidero` y
  `zona-solida {map, side: Attack}`, `mapa-fuerte {map: club-house}`;
  `nemesis {}` a `/duelos`; `kst`, `muertes-sin-trade`, `rondas-finales`,
  `bajon` con `{}` y `/`. Base vacia: 200, `sin-datos` con `{}` y `/`.
- **El enlace abre lo que la señal dice** (script `cruzar.py`: cada señal
  contra `/api/overview/?<sus filters>`, solos y con
  `days=99999&match_type=Ranked`): rondas == `sample` y winrate == `value`
  en `mapa-debil` (30, 20.0), `sitio-debil` (30, 20.0), `operador-debil`
  (15, 20.0), `mapa-fuerte` (40, 70.0). A mano en la base: Border/1F Armory
  30 rondas 6 ganadas; Mute en defensa 15 rondas 3 ganadas.
- **Bordes** `/api/coach/?`: `until=foo`, `page=-1`, `map=`, `side=`,
  `operator=`, `site=`, `days=abc` -> 200 con señales; `map=nope`,
  `side=Nada`, `since=2030-01-01`, `session=999` -> 200 `sin-datos`. Con
  `map=border` en la barra ninguna señal trae `map`. Con `map=consulate`
  (slug de dos versiones) `sitio-debil` trae `{site: 2F Workshop}` con
  `sample` 10 y su Resumen da 20 rondas 40 %: es el M1 del revisor
  (decision del diseno, ya en `## Para el humano`); no bloquea.
- **UI** (Playwright sobre la base sembrada): `/coach?match_type=Ranked`
  -> 7 `<a>` (6 "Ver esas rondas", 1 "Ver en Duelos") con `match_type` en
  el href; `since`/`until`/`gamemode` se conservan. Clic en 1F Armory ->
  `/?map=border&site=1F+Armory`, `h1` Resumen, Mapa=border, Sitio=1F
  Armory. "Ver en Duelos" -> `/duelos`. Consola sin errores ni warnings.
  (`days` fuera de 7/30/90 no viaja: lo descarta `filtrosUrl.js`, previo.)
- **Accesibilidad** (`accessibility-review`): enlace alcanzable con Tab,
  foco visible (`outline auto`), Enter navega; nombre accesible = texto;
  rol link; contraste 12.92:1 (rgb 230,237,243 sobre 29,38,50) a 12 px.
  Sin Critical ni Major.
- **Chunk inicial** `index-*.js`: dev 200100 B -> rama 200116 B (+0,008 %).
- **Mutaciones** (restauradas, `git status` limpio): sin el `pop("map")` ->
  cae `test_con_mapa_en_la_barra_la_senal_no_lo_pisa`; `sitio-debil` sin
  `site` -> caen 2; `nemesis`/`operador-rival` a `/` -> cae
  `test_las_senales_de_rival_van_a_duelos`; la barra pisando a la señal ->
  cae 1 vitest; sin filtros globales -> caen 4 vitest.
- **validate-data**: no hay numero nuevo; el parrafo de `metricas.md`
  describe el enlace, y el cruce de arriba prueba que el Resumen abierto
  tiene la misma `n` y el mismo winrate que la señal.

Veredicto: aprobado.

Skills del repo: accessibility-review (qa: teclado, nombre, contraste 12.92:1; 0 hallazgos), validate-data (qa: 2 valores recalculados a mano, n de la señal == n del Resumen), design-critique no aplica (sin pagina ni panel nuevo).
OMC: plan=— · revisión=— · verificación=PASS

## Para el humano

- (revisor 2026-11-13, no bloquea) En un mapa rehecho la señal de mapa, sitio o zona habla de una version y el enlace abre las dos (va por slug, como decidio el diseno). Si se quiere exacto: mandar `map=<map_id>` cuando el slug tiene mas de una version (cuidando `map_id=0`).
