# 137. Cuantas de tus muertes son headshot

estado: aprobado
candado: release 2026-11-18T12:23Z
rama: claude/equipo-dev/137-cuantas-de-tus-muertes-son-headshot
tipo: funcionalidad
epica: rivales
area: fullstack
prioridad: 3
fuente: ALCANCE.md D8
archivos: backend/replays/analytics/aggregates.py, backend/replays/views.py, backend/tests/test_muertes_headshot.py, frontend/src/muertesHeadshot.js, frontend/src/muertesHeadshot.test.js, frontend/src/pages/Duelos.jsx, frontend/e2e/humo.spec.js, docs/metricas.md
turnos: po 20261113T2157Z-cG2vDSe, arquitecto 20261114T0040Z-chQsvnq, dev 20261114T0316Z-cwWsU9i, revisor 20261115T0219Z-i32143169, qa 20261118T1211Z-cMNRUxv, release 20261118T1211Z-cMNRUxv

## PR

## Que gana quien usa la app

El HS% que muestra la app es el tuyo al matar; el reverso no existe. En Duelos,
de tus muertes a manos de rivales, cuantas fueron headshot, por lado, al lado
del mismo numero para tus compañeros en las mismas rondas: si te enganchan la
cabeza mas que al resto del equipo, te asomas expuesto.

## Criterios de aceptacion

- [x] Agregado nuevo: de los `Event` de baja cuyo `target` eres tu y cuyo
      autor es rival (`_solo_rivales`, sin teamkills), `deaths`,
      `with_data` (`headshot` no nulo), `headshots` y `pct` =
      headshots / with_data, por lado de tu fila (`Attack`, `Defense`) y
      total. `headshot` nulo no entra en el porcentaje. Test con muertes con
      y sin dato y un teamkill que no cuenta.
- [x] La referencia: el mismo calculo sobre las muertes de tus compañeros
      (tu `team_index`, `is_me=False`) en tus rondas filtradas. Test.
- [x] Los filtros globales aplican sobre tu fila de la ronda; test con
      filtro de lado.
- [x] Se ve en Duelos (clave nueva en el endpoint que ya usa la pagina o uno
      nuevo de lectura) como una tabla chica Tú / Tus compañeros por lado, con
      el `n` (muertes con dato) a la vista y aviso si es chico; sin dato,
      una nota. e2e sobre `seed_demo` con los numeros de la API y consola
      limpia.
- [x] Fila nueva en `docs/metricas.md`.

## Fuera de alcance

- Partirlo por operador rival (otro tramo).
- Señal del Coach.

## Diseno

(arquitecto 20261114T0040Z-chQsvnq) Filtros duros: pasa (`Event.headshot`,
`Event.target`, `team_index` por ronda; sin red, sin dependencias, sin POST,
sin migracion; se calcula al consultar como `nemesis` y `death_state`: es
conteo de eventos, no columna nueva). Una sola forma: sin arena ni consenso.

**Regla** (va tal cual a `metricas.md`). Universo: tus rondas filtradas,
`mine = base_queryset(**filters)` (los filtros aplican sobre tu fila,
incluido el lado). Eventos: `_mis_bajas(mine)` (los `Kill` de esas rondas)
pasados por `_solo_rivales(qs, "actor_id")` (autor con fila en la ronda y en
el equipo contrario al tuyo: fuera teamkills y bajas sin autor). *Tú*:
`target_id` en `_me_ids()`. *Tus compañeros*: `target_id` fuera de
`_me_ids()` y con `_equipo_de("target_id") == mi_equipo` (victima con fila
en la ronda y en tu equipo). Lado de la fila: el `side` de tu `RoundPlayer`
de esa ronda (tus compañeros juegan el mismo lado). Por grupo y por lado
(`Attack`, `Defense`, y `total`): `deaths` (todas), `with_data`
(`headshot` no nulo), `headshots` (`headshot=True`) y
`pct = _pct(headshots, with_data)` (None con 0). Conteos sumados, nunca
promedio por partida ni por compañero.

**Archivos:**
- `backend/replays/analytics/aggregates.py`: `headshot_deaths(**filters) ->
  dict` despues de `death_state`. Forma:
  `{"me": {"Attack": {...}, "Defense": {...}, "total": {...}},
    "teammates": {...mismo...}}`, las seis celdas siempre presentes. Una
  consulta con `.values("lado", "es_mia").annotate(deaths=Count("id"),
  with_data=Count("id", filter=Q(headshot__isnull=False)),
  headshots=Count("id", filter=Q(headshot=True)))`, donde `lado` es un
  `Subquery` del `side` de tu fila (como `_MI_EQUIPO`) y `es_mia` un
  `Case` sobre `target_id__in=me_ids`; el `total` se suma en Python.
- `backend/replays/views.py`, `duels()`: clave `"headshot_deaths"`. No hay
  URL nueva (urls.py lo toca la 134).
- `backend/tests/test_muertes_headshot.py` (Django, `factories.py`):
  `test_cuenta_tus_muertes_headshot_sobre_las_que_tienen_dato`;
  `test_headshot_nulo_cuenta_en_muertes_y_no_en_el_porcentaje`;
  `test_un_teamkill_no_cuenta_ni_para_ti_ni_para_tus_companeros`;
  `test_muerte_sin_autor_no_cuenta`;
  `test_las_muertes_de_tus_companeros_van_aparte`;
  `test_un_rival_no_cuenta_como_companero` (bajas entre rivales: nada);
  `test_parte_por_tu_lado_y_suma_el_total`;
  `test_filtro_de_lado_deja_solo_ese_lado`;
  `test_sin_dato_el_porcentaje_es_nulo`;
  `test_api_duels_trae_headshot_deaths`;
  `assertNumQueries` fijo sobre `headshot_deaths`.
- `frontend/src/muertesHeadshot.js`: `filasMuertesHeadshot(data)` -> filas
  `{clave, grupo: 'Tú' | 'Tus compañeros', ataque, defensa, total}` con cada
  celda `{pct, with_data}`; `[]` si los dos grupos tienen `with_data` 0 en
  `total` (para la nota y no ceros). `conPocaMuestra(filas)`: alguna celda
  con `0 < with_data < 30`, con `MUESTRA_CORTE` de `muestra.js` (no se
  define otro numero).
- `frontend/src/muertesHeadshot.test.js` (vitest): sin datos `[]`; orden Tú
  y despues compañeros; celda sin dato queda con `pct` null; aviso solo con
  muestra entre 1 y 29.
- `frontend/src/pages/Duelos.jsx`: Panel "Muertes por headshot" despues de
  "Por rival" (`Duelos.jsx:218`) y antes de "Rivales repetidos", con
  `data.headshot_deaths`. Tabla con columnas Quién, Ataque, Defensa, Total;
  cada celda `NN % (n)` y "—" sin dato; `hint`: "De tus muertes a manos de
  rivales, cuántas fueron headshot, al lado del mismo número para tus
  compañeros en las mismas rondas. Sin teamkills. n = muertes con dato de
  headshot." Nota de muestra chica si `conPocaMuestra`; sin filas,
  `<p className="note">` "No hay muertes con dato de headshot con estos
  filtros." Sin grafico (dataviz: no aplica, dos filas).
- `frontend/e2e/humo.spec.js`: test "Duelos muestra las muertes por
  headshot": panel por `section.panel` + heading, numeros de la fila Tú
  iguales a los de `/api/duels/` sobre `seed_demo` (el seed crea tu muerte
  con `headshot=indice % 4 == 0` y no crea muertes de compañeros, asi que
  esa fila queda en "—"; calcular los valores corriendo el seed en una base
  temporal), consola limpia.
- `docs/metricas.md`: fila **Muertes por headshot** en la tabla de Duelos,
  con la regla de arriba, junto a **HS%** dejando claro que es el reverso.

**Orden:** tests Django en rojo -> `headshot_deaths` -> clave -> vitest ->
helper -> panel -> e2e -> `metricas.md` -> `npm run build`.

**Puede romperse:** `_solo_rivales` anota `op_rival` (Subquery extra, sin
costo de filas); si el `.values()` agrupa tambien por esas anotaciones,
el conteo se parte: agrupar solo por `lado` y `es_mia` (test de totales lo
cubre). Rondas sin tu fila no entran (salen de `mine`).

**Archivos ocupados:** la 132 (en QA) toca `Duelos.jsx` en la columna
"Revanchas esa noche" de Rivales repetidos y `aggregates.py` en
`repeated_rivals`; este panel va en otro bloque y la funcion es nueva: sin
pisada real, no se frena. Si la 132 ya esta en dev al reclamar, nada que
hacer; si no, el que mergee segundo resuelve el contexto del `Panel`.

**Verificacion manual:** en una base real, el total de *Tú* con dato no
pasa de tus muertes de Resumen; con `side=Attack`, la columna Defensa
queda en "—".

Skills: no aplica (conteo sobre el feed con precedentes `nemesis` y `death_state`).
Skills del repo: statistical-analysis (denominador = muertes con dato, `n` en cada celda, corte de 30 de `muestra.js`, conteos sumados y no promedio de promedios), testing-strategy (Django para la regla, vitest para el helper, e2e para el panel).
OMC: plan=— · revisión=— · verificación=—

## Implementacion

(dev 20261114T0316Z-cwWsU9i)

Quedo el diseno completo:

- `aggregates.headshot_deaths(**filters)`: los `Kill` de tus rondas
  filtradas (`_mis_bajas`) por `_solo_rivales(..., "actor_id")`, victima tuya
  (`_me_ids()`) o de tu equipo con fila en la ronda (`_equipo_de("target_id")
  == mi_equipo`); una consulta agrupada solo por `lado` (`_MI_LADO`, el `side`
  de tu fila) y `es_mia` (`Case` sobre `target_id__in`), con `deaths`,
  `with_data` (`headshot` no nulo) y `headshots`; `total` y `pct =
  _pct(headshots, with_data)` en Python. Las seis celdas siempre presentes.
  `GROUP BY 1, 2` visto en el SQL: las anotaciones de `_solo_rivales` no
  parten el conteo.
- `views.duels`: clave `headshot_deaths` (sin URL nueva).
- `frontend/src/muertesHeadshot.js`: `filasMuertesHeadshot` (Tú y despues
  Tus compañeros, `orden` fijo, `[]` sin muertes con dato), `textoCelda`
  ("67% (3)", raya sin dato) y `conPocaMuestra` (con `MUESTRA_CORTE`).
- `Duelos.jsx`: panel "Muertes por headshot" entre "Por rival" y "Rivales
  repetidos", tabla Quién / Ataque / Defensa / Total, nota sin datos y aviso
  de muestra.
- e2e "Duelos muestra las muertes por headshot" con los numeros de
  `/api/duels/`, formateados a mano en el test (no importa el helper).
- `docs/metricas.md`: fila **Muertes por headshot** en la tabla de Duelos y
  su corte en `## Muestra minima`.

Desvios menores del diseno:

- `headshot_deaths` va despues de `_duelos` (seccion duelos, junto a
  `_mis_bajas` y `_solo_rivales`) y no despues de `death_state`: la 134
  (`revisado`) mete `kill_state` justo ahi y el que mergeara segundo tendria
  conflicto. Por lo mismo la fila de `metricas.md` va antes de **Rival
  repetido** (y no al lado de **HS%**, que esta en la tabla Base): la fila
  abre diciendo que es el reverso de HS%.
- Boton "Descargar CSV" (`muertes-por-headshot`) como el resto de las tablas
  de Duelos; el CSV lleva el texto de la celda y vacio donde va la raya.
- Tests extra: `test_una_victima_sin_fila_en_la_ronda_no_cuenta`,
  `test_un_lado_desconocido_solo_suma_al_total` (un `side` que no es ataque
  ni defensa solo suma al total) y `test_el_filtro_de_mapa_aplica_sobre_tus_rondas`.
  `assertNumQueries(2)` (los ids tuyos y la agregada) con 1 y con 5 rondas.

Criterios -> tests (`backend/tests/test_muertes_headshot.py`, 14): (1)
`test_cuenta_tus_muertes_headshot_sobre_las_que_tienen_dato`,
`test_headshot_nulo_cuenta_en_muertes_y_no_en_el_porcentaje`,
`test_un_teamkill_no_cuenta_ni_para_ti_ni_para_tus_companeros`,
`test_muerte_sin_autor_no_cuenta`, `test_sin_dato_el_porcentaje_es_nulo`;
(2) `test_las_muertes_de_tus_companeros_van_aparte`,
`test_un_rival_no_cuenta_como_companero`,
`test_una_victima_sin_fila_en_la_ronda_no_cuenta`; (3)
`test_filtro_de_lado_deja_solo_ese_lado`,
`test_el_filtro_de_mapa_aplica_sobre_tus_rondas`,
`test_parte_por_tu_lado_y_suma_el_total`; (4)
`test_api_duels_trae_headshot_deaths`, `muertesHeadshot.test.js` (4 tests),
e2e `Duelos muestra las muertes por headshot`; (5) fila en `metricas.md`.

TDD: los 13 tests Django en rojo antes del agregado (12 `AttributeError` por
la funcion que faltaba, 1 `KeyError` por la clave de `/api/duels/`); el
vitest en rojo antes de `muertesHeadshot.js` (suite sin modulo).

Mutaciones (codigo roto a mano y restaurado, `tests.test_muertes_headshot`):
victima de cualquier equipo con fila en vez de la tuya -> 1 falla;
`with_data` contando tambien `headshot` nulo -> 3 fallan; sin
`_solo_rivales` (teamkills adentro) -> 1 falla.

Sobre `seed_demo` (la base del e2e): Tú 24.9% (173) en total, 26.5% (98) en
ataque y 22.7% (75) en defensa; 173 = tus muertes del seed, asi que el total
con dato no pasa de las muertes del Resumen. Tus compañeros queda en raya:
el seed no crea muertes de compañeros en el feed.

Revision ciega: no disponible (esta sesion no tiene herramienta de
subagentes para `omc-code-reviewer`). En su lugar, pasada propia con la
lista de `revision.md` sobre `git diff origin/dev...HEAD -- .
':(exclude)docs/backlog'`: saco dos tildes de comentario y de nombre de
test; sin otros hallazgos. El Revisor hace la revision independiente.

Verificacion manual sugerida: `seed_demo`, `/duelos`: el panel entre Por
rival y Rivales repetidos con Tú 25% (173); con lado Ataque, Defensa queda en
raya.

Skills: no aplica (conteo sobre el feed con precedentes `nemesis` y `death_state`).
Skills del repo: test-driven-development (rojo visto en Django y vitest),
testing-strategy (regla y API en `TestCase`, helper en vitest, panel en e2e),
statistical-analysis (denominador = muertes con dato, `n` en cada celda,
corte de 30 de `muestra.js`, conteos sumados), ux-copy (textos del diseno con
tildes; aviso calcado de Estado al morir), modern-web-guidance
(`guides/accessibility/accessibility.md`, "Lists and tables": tabla de datos
con `th` por la `DataTable` existente, sin tabla de layout); sql-queries no
hizo falta (patron vecino `_solo_rivales`, con `assertNumQueries`).
OMC: plan=— · revisión=no disponible (sin subagentes) · verificación=—

## Revision 2026-11-15 sobre d5009f8

(revisor 20261115T0219Z-i32143169)

Veredicto: aprobar -> `revisado`.

Base: rama con `origin/dev` (4d90645, con la 134) fusionado sin conflicto
(27d7177; `Duelos.jsx` y `humo.spec.js` se fusionaron solos);
`verificar.sh`: `VERDE d5009f84d en 479s: 1404 tests backend, 459 vitest,
122 e2e` (incluye `Duelos muestra las muertes por headshot`).

Revision a ciegas: sin herramienta para lanzar subagentes en esta sesion,
asi que la hizo el lider con el prompt de `revision.md` como lista, sobre
`git diff 4d90645...d5009f8 -- . ':(exclude)docs/backlog'` (8 archivos,
+364), antes de leer la ficha. Un tema, sin vista POST ni lectura de `.rec`:
no suma eje de intencion ni de seguridad.

Sondas (test temporal en un worktree aparte, borrado despues):
- El mismo jugador rival en una ronda y compañero en otra (`camaleon`): en
  R1 su baja sobre `mate0` (headshot) cuenta en Tus compañeros, ataque; en
  R2 su muerte a manos de `rival0` cuenta en Tus compañeros, defensa; su
  teamkill sobre vos en R2 no cuenta. Resultado: Tú 0, compañeros total
  2 muertes, 1 headshot, 50 %. El equipo se lee por ronda.
- Partida de un jugador (solo tu fila, autor sin fila): Tú 0 muertes; la
  muerte no se atribuye a un rival que la ronda no tiene, como `nemesis`.

Mutaciones (codigo roto a mano y restaurado):
- Sin la celda por lado (solo total): 2 tests caen.
- `es_mia` invertido (tus muertes a compañeros y al reves): 8 tests caen.

Hallazgos:
- [test] LOW `frontend/e2e/humo.spec.js:707`
  Que pasa: con `seed_demo` la fila Tus compañeros sale en raya (el seed no
  crea muertes de compañeros en el feed), asi que el e2e solo ve numeros en
  la fila Tú; el texto "NN% (n)" de la fila de compañeros lo cubre el vitest.
  Como reproducirlo: `/api/duels/` sobre la base del e2e da
  `teammates.total.with_data == 0`.
  Arreglo sugerido: ninguno en esta ficha (cambiar el seed mueve los numeros
  de todo el e2e); QA puede mirarlo con una base sembrada desde
  `factories.py`. No frena.

Sin hallazgos en: autor rival por `_solo_rivales` (teamkills y bajas sin
autor fuera, test de cada uno); victima de tu equipo con fila en la ronda;
`headshot` nulo cuenta en muertes y no en el porcentaje; `pct` sobre muertes
con dato, sin promedio de promedios; lado de tu fila (un lado raro solo al
total, test); filtros sobre tu fila (lado y mapa, tests); 2 consultas fijas
(`assertNumQueries`); `headshot` del feed es dato que el `.rec` entrega (el
HS% ya lo usa); fila en `metricas.md` y su corte en `## Muestra minima`;
identificadores y comentarios sin tildes, UI con tildes ("Tú", "Tus
compañeros", "cuántas"); sin `print` ni `console.log`; el diff no sale de
`archivos:`. Calculado al consultar: el precedente de `nemesis` y
`death_state`, dicho en el docstring.

Ficha: criterios 1 a 5 cubiertos por los tests que lista
`## Implementacion` (corridos en el verde de arriba) y por las sondas.

Skills: no aplica.
Skills del repo: ninguna (revision con el prompt de `revision.md`).
OMC: plan=— · revisión=1 LOW (0 arreglados) · verificación=— (sin subagentes: revision del lider)

## QA 2026-11-18 sobre ede9b12

(qa 20261118T1211Z-cMNRUxv)

Veredicto: todos los criterios pasan -> `aprobado`.

- **check.sh completo** (`verificar.sh`, `E2E_PORT=46010`):
  `VERDE ede9b1244 en 273s: 1404 tests backend, 459 vitest, 122 e2e.
  Todo en verde.`; en el log, `✓ 58 [chromium] › e2e/humo.spec.js:707:1 ›
  Duelos muestra las muertes por headshot`.
- **Base sembrada desde `factories.py`** (script en el scratchpad, no en el
  repo): 5 partidas. A (Club House, 6 rondas: tus muertes con headshot
  si/no/nulo, compañeros con si/no/nulo, un teamkill sobre ti y otro entre
  compañeros, una baja sin autor, una ronda sin bajas); B (Oregon: baja de
  rival sobre rival, victima `fantasma` sin fila); C (Bank: partida de un
  jugador, solo tu fila); D (Kafe: **nick repetido**, otro profileID llamado
  `mate0` como rival te mata con headshot, y el `mate0` compañero muere sin
  headshot); E (Chalet: tu baja con dato y tu unica muerte con `headshot`
  nulo). Mas una base vacia. `runserver` en 46020 (sembrada) y 46021 (vacia).
- **API** (`curl /api/duels/?<q>`, celda `muertes/con dato/headshots pct`):
  sin filtros, Tú A `4/3/2 66.7` D `3/2/2 100.0` T `7/5/4 80.0`, compañeros
  A `5/4/2 50.0` D `1/1/1 100.0` T `6/5/3 60.0`; los mismos con `until=foo`,
  `page=-1`, `side=`, `map=`, `min_duels=-1|foo`, `days=999999999999`,
  `operator=Zofia`, `ranked_only=1`, `until=2026-09-01`. `side=Attack`:
  Defensa `0/0/0 None` en los dos grupos; `side=Defense`: Ataque en cero.
  `map=oregon`: Tú D `1/1/1`, compañeros A `1/1/1` (rival sobre rival y
  victima sin fila no cuentan). `map=kafe`: Tú A `1/1/1`, compañeros A
  `1/1/0 0.0` (el homonimo rival no se cuenta como compañero). `map=bank`
  (un jugador): todo en cero. `map=chalet`: Tú `1/0/0 None`.
  `since=2026-09-01T21:30`: solo D. `operator=Mute`, `session=abc|-1`,
  `side=%00`, `map=%E2%80%AE`, `map=NoExiste`: ceros. Base vacia: las seis
  celdas en `0/0/0 None`. Todo 200; `death-state`, `kill-state` y
  `thrown-advantage` con `until=foo`: 200.
- **validate-data** sobre la fila **Muertes por headshot** de `metricas.md`:
  denominador = muertes con dato (Tú T: 7 muertes, 5 con dato), division por
  cero = celda nula y raya, conteos sumados (total = ataque + defensa: 4+3,
  3+2, 2+2), el `n` en cada celda, filtros sobre tu fila. Recalculo a mano en
  SQL crudo sobre la sqlite sembrada, sin el ORM: **Tú total** 7 muertes, 5
  con dato, 4 headshots, 80.0 (API: `7/5/4 80.0`); **Tus compañeros
  ataque** 5, 4, 2, 50.0 (API: `5/4/2 50.0`). Redondeo: API a un decimal, UI
  a entero (`66.7` -> `67% (3)`), el mismo de `pct` de `ui.jsx`. Sin
  hallazgos.
- **Pantalla** (Chromium 1243 con Playwright, base sembrada, `/duelos`):
  panel entre Por rival y Rivales repetidos; filas `Tú | 67% (3) | 100% (2)
  | 80% (5)` y `Tus compañeros | 50% (4) | 100% (1) | 60% (5)`; aviso de
  muestra chica visible; `?side=Attack` deja Defensa en `—`;
  `?map=chalet` muestra "No hay muertes con dato de headshot con estos
  filtros." sin tabla; consola sin errores ni avisos. CSV por teclado (foco
  en "Descargar CSV" + Enter): `muertes-por-headshot-2026-11-18.csv` con
  `Tú;67% (3);100% (2);80% (5)`.
- **accessibility-review** (WCAG 2.1 AA, lo que agrego la ficha): 0
  Critical, 0 Major. Contraste medido: titulo y `hint` 5.71:1 (`#8b98a9`
  sobre `#171e29`, 15 y 12 px), encabezados 5.71:1, celdas 14.17:1, nota
  de muestra 5.71:1, boton 12.92:1. Nombre y rol: `h2` "Muertes por
  headshot", tabla con `columnheader` QUIÉN/ATAQUE/DEFENSA/TOTAL en el arbol
  de accesibilidad de Chromium (CDP), boton "Descargar CSV". Teclado: un
  solo tope en el panel (el boton), foco visible (anillo `auto`), Enter
  descarga. 320 px: la pagina no desborda (`scrollWidth` 320), la tabla
  desplaza dentro de su caja (`overflow-x: auto`). Minor que ya estaba en
  toda `DataTable`: la primera columna es `td`, no encabezado de fila
  (1.3.1) -> idea T10 en `ALCANCE.md`.
- **design-critique** (panel nuevo, no frena): se lee de un vistazo y el
  `n` de cada celda esta a la vista; lo que falta es la comparacion que da
  sentido al panel: hay que restar Tú menos compañeros de cabeza -> idea D21
  en `ALCANCE.md` (diferencia en puntos por lado). A 320 px la columna Total
  queda fuera de la vista hasta desplazar (patron de todas las tablas).
- **Build**: chunk inicial `index-*.js` 200.34 kB en `origin/dev` (4d90645)
  y en la rama (sin cambio); `Duelos-*.js` 17.17 -> 18.70 kB (chunk diferido).
- **Mutaciones** (codigo roto a mano y restaurado; `git status` limpio
  despues): `hs` contando toda muerte con dato -> 5 tests caen; victima de
  cualquier equipo con fila en vez del tuyo -> cae
  `test_un_rival_no_cuenta_como_companero`; el total sin las filas de
  Defensa -> caen 2; vitest: `conPocaMuestra` avisando tambien con 0 -> cae
  "avisa la muestra chica solo entre 1 y 29".
- Sin migracion, `recompute`, parser, Electron ni `.ps1`: no hay
  "Verificar en el PC". El corte de 30 es `MUESTRA_CORTE`, no un umbral
  nuevo. El LOW del Revisor (fila de compañeros en raya en el e2e) queda
  cubierto por la base sembrada de arriba.

Repetir: `cd backend && SQLITE_PATH=/tmp/qa/db.sqlite3 DATA_DIR=/tmp/qa
R6_ENV_FILE=/tmp/qa/.env ../.venv/bin/python manage.py migrate`, sembrar con
`tests.factories` (`make_match`, `make_round`, `make_round_player`,
`make_event(..., headshot=True|False|None)`), `runserver 127.0.0.1:46020
--noreload` con el mismo entorno y `curl
'http://127.0.0.1:46020/api/duels/?side=Attack' | python3 -m json.tool`.

Skills del repo: accessibility-review (0 Critical, 0 Major, 1 Minor que ya estaba -> T10), design-critique (1 idea -> D21), validate-data (Tú total 7/5/4 80.0 y compañeros ataque 5/4/2 50.0 recalculados en SQL = API), verification-before-completion (cada linea con su salida de este turno).
OMC: plan=— · revisión=— · verificación=no disponible (sin herramienta de subagentes: tabla de criterios del lider con la vara de omc-verifier, 5 de 5 VERIFIED)

## Para el humano

(nada)
