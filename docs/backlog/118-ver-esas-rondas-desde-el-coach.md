# 118. "Ver esas rondas" desde las señales del Coach

estado: implementado
candado: revisor 2026-11-13T17:44Z
rama: claude/equipo-dev/118-ver-esas-rondas-desde-el-coach
tipo: funcionalidad
epica: revision-de-rondas
area: fullstack
prioridad: 3
fuente: ALCANCE.md F15 (salio del PR #14, cerrado sin merge el 2026-11-05; complementa la 112, que salta a una ronda puntual)
archivos: backend/replays/analytics/coach.py (_insight, reglas), backend/tests/test_coach.py, frontend/src/enlaceSenal.js (nuevo), frontend/src/enlaceSenal.test.js (nuevo), frontend/src/pages/Coach.jsx, frontend/e2e/humo.spec.js, docs/metricas.md
turnos: po 20261113T0404Z-cnRfz4a, arquitecto 20261113T0804Z-cJw5MQs, dev 20261113T1651Z-cxTme8t

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

## Para el humano

(nada)
