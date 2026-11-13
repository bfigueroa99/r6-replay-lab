# 118. "Ver esas rondas" desde las señales del Coach

estado: entregado
candado: -
rama: claude/equipo-dev/118-ver-esas-rondas-desde-el-coach
tipo: funcionalidad
epica: revision-de-rondas
area: fullstack
prioridad: 3
fuente: ALCANCE.md F15 (salio del PR #14, cerrado sin merge el 2026-11-05; complementa la 112, que salta a una ronda puntual)
archivos: backend/replays/analytics/coach.py (_insight, reglas), backend/tests/test_coach.py, frontend/src/enlaceSenal.js (nuevo), frontend/src/enlaceSenal.test.js (nuevo), frontend/src/pages/Coach.jsx, frontend/e2e/humo.spec.js, docs/metricas.md
turnos: po 20261113T0404Z-cnRfz4a, arquitecto 20261113T0804Z-cJw5MQs, dev 20261113T1651Z-cxTme8t, revisor 20261113T1732Z-cdpsq83, qa 20261113T1802Z-c8dAf7p, release 20261113T1802Z-c8dAf7p

## PR

**Titulo:** [equipo-dev][frontend] Ver esas rondas desde las señales del Coach

### Que cambia

Cada señal del Coach que habla de un mapa, un lado, un operador o un sitio
trae un enlace "Ver esas rondas" que abre el Resumen ya filtrado por eso,
sumado a los filtros de la barra (fechas, tipo, modo, sesion); las de un
rival ("Ver en Duelos") abren Duelos con los filtros de la barra. Las
señales generales no llevan enlace.

### Por que esto y no otra cosa

Ficha 118, idea F15 de `ALCANCE.md` (salio del PR #14, cerrado sin merge).
Solo enlaza a filtros que la API ya acepta: sin filtro de spawn, el spawn
abre mapa + ataque; sin filtro de rival, Duelos abre con la barra. El mapa
va por slug (todas sus versiones), salvo que la barra ya tenga mapa: ahi la
señal no lo pisa.

### Como se probo

- `check.sh` (con `verificar.sh`): VERDE f10604491 (QA), 1239 tests backend, 377 vitest, 103 e2e; VERDE sobre el commit final, abajo.
- Tests nuevos: `EnlaceDeLasSenalesTests` (9: mapa, operador y lado, sitio, desbalance, spawn, general sin filtros, todas con `filters`/`target` en `FILTER_KEYS`, rival a `/duelos`, mapa de la barra no pisado); `test_posicion.py` (filtros de las zonas); `enlaceSenal.test.js` (8 vitest); e2e `una señal del Coach abre el Resumen filtrado` y `el sitio que trae una señal del Coach se ve en la barra y se quita`.
- Verificacion manual (QA): base sintetica, cada señal cruzada contra `/api/overview/` con sus filtros: misma `n` y mismo winrate; Playwright: clic, teclado, consola limpia, contraste 12.92:1.
- OMC: diseno `plan=— · revisión=— · verificación=—`; implementacion `plan=— · revisión=5 hallazgos (5 arreglados; 1 HIGH) · verificación=—`; revision `plan=— · revisión=3 hallazgos MEDIUM (1 cubierto con test, 1 decision del diseno al humano) y 2 LOW (1 cubierto) · verificación=—`; QA `plan=— · revisión=— · verificación=PASS`.
- Skills del repo: testing-strategy (arquitecto); ux-copy (dev); accessibility-review y validate-data (qa).

### Riesgos y lo que no entra

Sin migracion, sin `recompute`, sin red. Las claves nuevas de la señal son
aditivas. En un mapa rehecho la señal habla de una version y el enlace abre
las dos (decision del diseno, abajo). Fuera: saltar a una ronda puntual
(112), lista de rondas (F1), el bloque de señales del Resumen.

### Como probarlo en 2 minutos

```
cd backend; python manage.py seed_demo; python manage.py runserver
```
Abrir `http://127.0.0.1:8000/coach`: "Con Jager rindes..." -> "Ver esas
rondas" abre el Resumen con Operador y Lado puestos en la barra; la señal
del spawn/sitio abre con Mapa (y Sitio visible); la de rival dice "Ver en
Duelos"; `kst` no tiene enlace. Con Tipo = Ranked en la barra, el enlace lo
conserva.

### Para el humano

Nada que bloquee. Mejora posible: en un mapa rehecho, mandar `map=<map_id>`
en vez del slug cuando el slug tiene mas de una version (cuidando `map_id=0`).

### Candidatos descubiertos

Ninguno.

## Que gana quien usa la app

Cada señal del Coach que habla de un mapa, un lado, un operador o un sitio
lleva un enlace "Ver esas rondas" que abre el Resumen ya filtrado por eso, y la
de un rival abre Duelos: de "Kafe es tu peor mapa" se pasa a los numeros de
Kafe en un clic, sin armar los filtros a mano.

## Criterios de aceptacion

- [x] Cada señal de `build_insights` (`coach.py`) trae un campo `filters`
      (dict, vacio si la señal es general) con los filtros que la definen,
      en los mismos nombres que la API acepta (`map` como slug, `side`,
      `operator`, `site`); test: la señal `mapa-debil` trae `{"map":
      <slug>}` y una general trae `{}`.
- [x] Los filtros globales que ya tenia la consulta del Coach (fechas, tipo,
      modo, sesion) se suman al enlace: abrir el enlace no pierde el periodo
      que estaba mirando. Vitest de la funcion pura que arma el `href`.
- [x] En Coach, una señal con `filters` no vacio muestra el enlace "Ver esas
      rondas" a `/?<query>`; una de rival (`nemesis`, duelos por operador)
      enlaza a `/duelos?<query>`; una general no muestra enlace.
- [x] e2e: desde `/coach` con `seed_demo`, el enlace de una señal de mapa
      abre el Resumen con el filtro de mapa puesto (selector y URL), consola
      limpia.

## Fuera de alcance

- Saltar a una ronda puntual (eso es la 112, `#ronda-N`).
- Señales nuevas o cambiar el texto de las que hay.
- Enlazar a una lista de rondas (no existe; es F1).

## Diseno

(arquitecto 20261113T0804Z-cJw5MQs) `_insight` suma `filters` (nombres de
`FILTER_KEYS`) y `target` (`/` o `/duelos`); cada regla pasa los filtros de
la fila que eligio (lado, mapa por slug, sitio con su mapa, operador con su
lado, spawn como mapa + ataque); rival a `/duelos` sin filtros propios.
`enlaceSenal.js` puro suma los de la señal a los de la barra (la señal
pisa). Detalle completo en `git log` de la rama.

Skills del repo: testing-strategy (Django para el mapeo señal -> filtros, vitest para armar el enlace, e2e para el clic y la barra).
OMC: plan=— · revisión=— · verificación=—

## Implementacion

(dev 20261113T1651Z-cxTme8t) Diseno completo, mas tres desvios por revision
ciega: `Filters.jsx` muestra Sitio cuando viene puesto (HIGH: el `site` de la
señal quedaba invisible); `build_insights` no pisa el mapa de la barra
(MEDIUM); tests de spawn y lados, `test_posicion.py` (LOW).
verificar.sh: VERDE 95c5d88fc (1209 backend, 368 vitest, 101 e2e).

Skills del repo: ux-copy (dev: "Ver esas rondas" / "Ver en Duelos" empiezan con verbo y nombran el destino).
OMC: plan=— · revisión=5 hallazgos (5 arreglados; 1 HIGH) · verificación=—

## Revision 2026-11-13 sobre c29903c

(revisor 20261113T1732Z-cdpsq83) Aprobar. M1 (mapa rehecho: slug une
versiones) es decision del diseno, al humano. I1 (el e2e no comprobaba el
mapa) e I3 (vitest sin fechas ni modo) cubiertos con tests del revisor.
verificar.sh: VERDE c29903c38 (1220 backend, 372 vitest, 102 e2e).

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
