# 138. El sitio con el que abres la defensa

estado: revisado
candado: qa 2026-11-21 01:38 UTC
rama: claude/equipo-dev/138-el-sitio-con-el-que-abres-la-defensa
tipo: funcionalidad
epica: posicionamiento
area: fullstack
prioridad: 3
fuente: ALCANCE.md S7
archivos: backend/replays/analytics/aggregates.py, backend/replays/views.py, backend/replays/urls.py, backend/tests/test_apertura_defensa.py, frontend/src/aperturaDefensa.js, frontend/src/aperturaDefensa.test.js, frontend/src/pages/Coach.jsx, frontend/e2e/humo.spec.js, docs/metricas.md
turnos: po 20261113T2157Z-cG2vDSe, arquitecto 20261114T0040Z-c3LsMAo, dev 20261115T0219Z-i32143169, revisor 20261118T1211Z-cMNRUxv

## PR

## Que gana quien usa la app

En el Coach, por mapa, que sitio defiende tu equipo en la primera ronda de
defensa de cada partida, cuantas veces y con que winrate esa ronda, contra el
winrate de ese sitio en el resto de tus rondas de defensa: si tu apertura en
defensa es predecible y si arrancar ahi te cuesta.

## Criterios de aceptacion

- [x] Agregado nuevo: primera ronda de defensa = la de menor `Round.number`
      con `my_side="Defense"` de la partida, leida de la partida entera (como
      `_primera_ronda`); si falta una ronda antes (hueco de numeracion desde
      la primera ronda de la partida) o no tiene sitio, la partida no entra.
      Por mapa (con su version) y sitio: `opens` (partidas que abrieron
      ahi), `opens_decided`, `opens_winrate`, y `rest_rounds`,
      `rest_winrate` del mismo sitio en las demas rondas de defensa. Test con
      tres partidas y un hueco.
- [x] Una ronda sin ganador cuenta en las rondas y no en el winrate. Test.
- [x] Filtros globales de partida (mapa, tipo, modo, fechas, sesion) aplican;
      lado y operador no (es siempre defensa y del equipo), como "Repetir el
      sitio tras perderlo". Test con filtro de mapa.
- [x] Se ve en el Coach, junto a "Repetir el sitio tras perderlo", con aviso
      de muestra (se avisa, no se oculta) y una nota sin datos; e2e sobre
      `seed_demo` con los numeros de la API y consola limpia.
- [x] Fila nueva en `docs/metricas.md`.

## Fuera de alcance

- El sitio con el que abres tras el cambio de lado o en prorroga.
- Recomendar un sitio.

## Diseno

(arquitecto 20261114T0040Z-c3LsMAo, sobre dev f34baba) Filtros duros: pasa (sitio de bomba y
lado de `Round`, que el `.rec` entrega; sin red, sin dependencias, sin POST,
sin migracion, sin `recompute`). Una sola forma obvia, con precedente
`site_after_loss`: sin arena ni consenso.

**Regla** (va tal cual a `metricas.md`). Se leen tus filas de la partida
(`base_queryset` sin `side`, `site` ni `operator`, ordenadas por
`round__match_id, round__number`), como `site_after_loss`. Por partida, la
**apertura de defensa** es tu primera fila con `side == "Defense"`, siempre
que: tu primera fila de la partida sea la ronda mas baja de la partida
(`Round.number` minimo de `Round` de esa partida, no solo de tus filas: si
falta tu fila de la ronda 0 no se sabe si la defensa empezo antes); los
numeros sean consecutivos desde ahi hasta la apertura (un hueco = ronda sin
`.rec` o sin fila tuya); ninguna fila antes tenga `side` vacio; y la apertura
tenga `round__site`. Si algo falla, la partida no aporta apertura (sus otras
rondas de defensa si entran al resto). El **resto** son todas tus demas
rondas de defensa con sitio de las partidas filtradas, aperturas excluidas.
Por (mapa con version, sitio): `opens`, `opens_decided`, `opens_won`,
`opens_winrate`, `rest_rounds`, `rest_decided`, `rest_winrate`, y
`opens_share` = `opens` / aperturas del mapa (que tan predecible es: 100 =
siempre abris ahi). Una ronda sin ganador (`my_team_won` nulo) cuenta en
`opens`/`rest_rounds` y no en el winrate. Mapa, tipo, modo, fechas y sesion
aplican; lado, operador y sitio no (la fila es de la defensa y del equipo; el
filtro de sitio partiria la comparacion contra el resto). Prorroga: no se
excluye; la apertura de defensa nunca cae en prorroga porque la defensa
empieza en la ronda 0 o 1 de tiempo regular.

**Archivos:**
- `backend/replays/analytics/aggregates.py`: debajo de `site_after_loss`,
  `APERTURA_DEFENSA_MIN_PARTIDAS = 5` y `defense_opener(**filters) -> dict`.
  Dos consultas fijas: tus filas (`values_list` de match_id, number, side,
  site, my_team_won y `*_MAPA`) y `Round.objects.values("match_id")
  .annotate(Min("number"))` filtrado a los match_id de las filas (o sin
  filtro: el `dict` es chico). Un solo recorrido. Devuelve
  `{"min_matches", "matches" (partidas con apertura), "skipped" (partidas
  con rondas de defensa que no aportan apertura), "maps": [{map, slug,
  map_id, "opens_total", "sites": [fila por sitio]}]}`, mapas por
  `opens_total` desc y sitios por `opens` desc, despues `rest_rounds` desc,
  despues nombre; un sitio con 0 aperturas y rondas en el resto tambien sale
  (con `opens 0`: es dato de que nunca abris ahi). `_etiquetar` para la
  version del mapa.
- `backend/replays/views.py` + `urls.py`: `GET
  /api/positioning/defense-opener/` -> `defense_opener(**_filters(request))`,
  al lado de `site-after-loss`.
- `backend/tests/test_apertura_defensa.py` (Django, `factories.py`): helper
  `_partida(index, lados_y_sitios, ganadas)` con `make_round(match, n,
  side=..., site=..., won=...)` + `make_round_player`. Tests:
  `test_tres_partidas_una_con_hueco_dan_dos_aperturas` (la del hueco entra
  al resto con su defensa y suma a `skipped`);
  `test_la_apertura_es_la_primera_defensa_aunque_arranques_en_ataque`;
  `test_sin_tu_fila_de_la_primera_ronda_no_hay_apertura` (`Round` 0 sin
  `RoundPlayer` tuyo);
  `test_una_ronda_sin_lado_antes_corta_la_apertura`;
  `test_una_apertura_sin_ganador_cuenta_y_no_entra_al_winrate`;
  `test_el_resto_es_el_mismo_sitio_sin_las_aperturas`;
  `test_el_porcentaje_de_aperturas_es_sobre_las_del_mapa`;
  `test_el_filtro_de_mapa_aplica_y_el_de_lado_no`;
  `test_consultas_constantes` (`assertNumQueries(2)` con 2 y con 6 partidas);
  `test_api_defense_opener_responde_con_filtros`.
- `frontend/src/aperturaDefensa.js` + `aperturaDefensa.test.js` (vitest):
  `hayAperturas(data)`, `filasAperturaDefensa(data)` (una fila por mapa y
  sitio, con `map` repetido y `poca: opens < min_matches`),
  `textoAperturas(n)` ("1 partida con apertura de defensa" / "N partidas
  ..."). Tests: sin datos; plural; marca `poca`; orden.
- `frontend/src/pages/Coach.jsx`: `PanelAperturaDefensa` justo debajo de
  `PanelRepetirSitio` (mismo patron: `useApi`, `ErrorBox`, `Loading`, nota
  sin datos). Titulo "El sitio con el que abres la defensa"; hint: "En cada
  partida, el sitio que tu equipo defendió en su primera ronda de defensa,
  cuántas veces y cuánto la ganó, contra ese mismo sitio en el resto de tus
  rondas de defensa. Lado, operador y sitio de la barra no aplican." Tabla:
  Mapa, Sitio, Abre (`opens` con `opens_share` en %), Winrate abriendo
  (con "pocas partidas" si `poca`, como `winrateConMuestra`), Resto (rondas),
  Winrate resto. Nota sin datos: "Con estos filtros no hay partidas con su
  primera ronda de defensa completa."
- `frontend/e2e/humo.spec.js`: test "Coach muestra el sitio con el que
  abres la defensa": panel por `section.panel` + heading; numeros contra
  `/api/positioning/defense-opener/` sobre `seed_demo` (ahi la ronda 1 es
  siempre defensa y perdida: `opens_winrate` 0 en todas las filas; el Dev
  confirma con el seed en una base temporal); consola limpia.
- `docs/metricas.md`: fila **El sitio con el que abres la defensa** debajo
  de **Repetir el sitio tras perderlo** (linea ~215) y su corte en la tabla
  de muestras minimas (linea ~429): "5 partidas por apertura
  (`APERTURA_DEFENSA_MIN_PARTIDAS`): no se oculta, se avisa".

**Numero (statistical-analysis):** winrate de ronda sobre decididas, con el
`n` (`opens`) a la vista; el porcentaje de aperturas es sobre las aperturas
del mapa, no sobre todas las partidas (un mapa poco jugado no diluye a otro).
Corte de 5 partidas para avisar (una apertura por partida: juntar 8 como
`site_after_loss` tarda mucho en un mapa); no hay delta ni veredicto contra
el resto: con 5 a 20 aperturas la diferencia es ruido casi siempre y un
veredicto engañaria. Umbral sin calibrar con datos reales: anotado abajo.

**Orden:** tests Django en rojo -> `defense_opener` -> vista/URL -> vitest
-> helper -> panel -> e2e -> `metricas.md` -> `npm run build`.

**Puede romperse:** el e2e del Coach que cuente paneles por posicion (ubicar
por heading); `Round.number` minimo cuando una partida tiene rondas
importadas sin fila tuya (es justo el caso que corta; test).

**Archivos ocupados:** `aggregates.py`, `views.py`, `urls.py`,
`humo.spec.js` y `metricas.md` los tocan 134, 135 y 79 con agregados
lejanos; `Coach.jsx` no lo toca ninguna rama abierta. No se frena.

**Verificacion manual:** `seed_demo` + `runserver`, Coach: el panel con una
fila por mapa y sitio, `Abre` sumando 100 % por mapa.

Skills: no aplica (panel con precedente `PanelRepetirSitio`).
Skills del repo: statistical-analysis (winrate sobre decididas, `n` a la vista, porcentaje sobre las aperturas del mapa, sin veredicto por ruido), testing-strategy (Django para la regla, vitest para el helper, e2e para el panel).
OMC: plan=— · revisión=— · verificación=—

## Implementacion

(dev 20261115T0219Z-i32143169)

Quedo el diseno completo:

- `aggregates.defense_opener(**filters)` debajo de `site_after_loss`, con
  `APERTURA_DEFENSA_MIN_PARTIDAS = 5`. Dos consultas fijas: el `Min("number")`
  de `Round` por partida (acotado con una subconsulta a tus partidas
  filtradas, no con una lista de ids: sin tope de parametros de SQLite) y tus
  filas ordenadas por partida y numero. Un recorrido: la apertura es tu
  primera fila de defensa si tu primera fila es la ronda mas baja, los
  numeros siguen sin hueco ni lado vacio hasta ella y tiene sitio; el resto,
  las demas rondas de defensa con sitio (tambien las de partidas sin
  apertura). Devuelve `min_matches`, `matches`, `skipped` y `maps` (con
  `opens_total` y `sites`: `opens`, `opens_decided`, `opens_won`,
  `opens_winrate`, `opens_share`, `rest_rounds`, `rest_decided`, `rest_won`,
  `rest_winrate`), mapas por aperturas y sitios por aperturas, resto y
  nombre; `_etiquetar` para la version del mapa.
- `GET /api/positioning/defense-opener/` (`views.defense_opener`, url
  `defense-opener`) al lado de `site-after-loss`.
- `frontend/src/aperturaDefensa.js`: `hayAperturas`, `filasAperturaDefensa`
  (una fila por mapa y sitio, `orden` de la API, `poca` con
  `opens < min_matches`), `textoWinrateApertura`, `textoAperturas` y
  `textoSinApertura`.
- `Coach.jsx`: `PanelAperturaDefensa` justo debajo de `PanelRepetirSitio`,
  con el titulo y el hint del diseno; tabla Mapa, Sitio, Abre ("5 (50%)"),
  Winrate abriendo (con "· pocas partidas"), Resto y Winrate resto; nota sin
  datos; CSV `sitio-con-el-que-abres-la-defensa`.
- e2e "el Coach muestra el sitio con el que abres la defensa" con los
  numeros de `/api/positioning/defense-opener/` (formateados a mano, sin
  importar el helper) y la suma de `opens_total` por mapa igual a `matches`.
- `docs/metricas.md`: fila **El sitio con el que abres la defensa** debajo de
  **Repetir el sitio tras perderlo** y su corte en `## Muestra minima`.

Desvios menores del diseno:

- `rest_won` tambien va en la salida (el diseno listaba `opens_won` y no su
  par): sirve para recalcular el winrate del resto a mano.
- Nota aparte con `skipped` ("N partidas con defensa no entran: falta una
  ronda antes de su primera defensa, o les falta lado o sitio."), tambien en
  el estado sin aperturas: sin ella el total de partidas no cierra.
- "pocas partidas" en vez del "pocas rondas" de `textoWinrate`: el corte es
  por partidas. Sin winrate (0 aperturas) la celda es raya y no avisa.
- Un mapa con rondas de defensa y ninguna apertura sale igual, con
  `opens_total` 0 y `opens_share` nulo (test).
- Tests extra: `test_una_apertura_sin_sitio_no_entra_y_su_defensa_tampoco`,
  `test_un_mapa_sin_aperturas_sale_con_su_resto_y_sin_porcentaje`,
  `test_sin_partidas_devuelve_vacio`.

Criterios -> tests (`backend/tests/test_apertura_defensa.py`, 13): (1)
`test_tres_partidas_una_con_hueco_dan_dos_aperturas`,
`test_la_apertura_es_la_primera_defensa_aunque_arranques_en_ataque`,
`test_sin_tu_fila_de_la_primera_ronda_no_hay_apertura`,
`test_una_ronda_sin_lado_antes_corta_la_apertura`,
`test_el_resto_es_el_mismo_sitio_sin_las_aperturas`,
`test_el_porcentaje_de_aperturas_es_sobre_las_del_mapa`; (2)
`test_una_apertura_sin_ganador_cuenta_y_no_entra_al_winrate`; (3)
`test_el_filtro_de_mapa_aplica_y_el_de_lado_no` (lado, operador y sitio de la
barra no cambian nada), `test_api_defense_opener_responde_con_filtros`; (4)
`aperturaDefensa.test.js` (4 tests) y el e2e del Coach; (5) fila en
`metricas.md`. Ademas `test_consultas_constantes` (`assertNumQueries(2)` con
2 y con 6 partidas).

TDD: los 13 tests Django en rojo antes del agregado (12 errores por la
funcion que faltaba, 1 fallo por la ruta en 404); el vitest en rojo antes de
`aperturaDefensa.js` (suite sin modulo).

Sobre `seed_demo` (base del e2e): 29 partidas con apertura, 0 afuera; Bank
10 (B Lockers 5, 50 %; A Executive 5), Club House 10 (B Church 6, 60 %),
Border 9 (B Armory 5, 55,6 %); winrate abriendo 0 % en todas las filas, como
anticipaba el diseno.

Revision ciega: no disponible (esta sesion no tiene herramienta para lanzar
`omc-code-reviewer`). En su lugar, pasada propia con la lista de
`revision.md` sobre `git diff origin/dev...HEAD -- . ':(exclude)docs/backlog'`:
sin hallazgos (identificadores y comentarios sin tildes, UI con tildes, sin
`print` ni `console.log`, fila en `metricas.md`, sin dependencias ni POST).
El Revisor hace la revision independiente.

Verificacion: `verificar.sh` VERDE 4e2a48cba (1403 tests backend, 459
vitest, 122 e2e). El primer intento, sobre 390993bd9, cayo solo en
`accesibilidad.spec.js` ("ninguna tabla deja una columna sin nombre") por una
request abortada de `/api/trends/?limit=25` en `/tendencias`, una pagina que
este cambio no toca, con el contenedor cargado (443 s); al repetir, verde.

Verificacion manual sugerida: `seed_demo`, `/coach`: el panel debajo de
"Repetir el sitio tras perderlo", una fila por mapa y sitio y Abre sumando
100 % por mapa.

Skills: no aplica (panel con precedente `PanelRepetirSitio`).
Skills del repo: test-driven-development (rojo visto en Django y vitest),
testing-strategy (regla y API en `TestCase`, helper en vitest, panel en e2e),
statistical-analysis (winrate sobre decididas, `n` en Abre, porcentaje sobre
las aperturas del mapa, sin veredicto contra el resto), ux-copy (textos del
diseno con tildes; "pocas partidas" y la nota de las que no entran, sin
afirmar la causa exacta de cada una), modern-web-guidance
(`guides/accessibility/accessibility.md`, "Lists and tables": tabla de datos
con `th` por la `DataTable` existente); sql-queries no hizo falta (patron
vecino `site_after_loss`, con `assertNumQueries`).
OMC: plan=— · revisión=no disponible (sin subagentes) · verificación=—

## Revision 2026-11-18 sobre 1f3455d

(revisor 20261118T1211Z-cMNRUxv)

Veredicto: aprobar -> `revisado`.

Base: rama con `origin/dev` (2611d85, con la 137) fusionado sin conflicto
(1f3455d); `verificar.sh`: `VERDE 1f3455da2 en 418s: 1417 tests backend,
463 vitest, 123 e2e. Todo en verde.` (incluye `el Coach muestra el sitio con
el que abres la defensa`).

Revision a ciegas: sin herramienta para lanzar subagentes en esta sesion,
asi que la hizo el lider con el prompt de `revision.md` como lista, sobre
`git diff origin/dev...HEAD -- . ':(exclude)docs/backlog'` (9 archivos,
+487), antes de leer la ficha. Un tema (un agregado de lectura, su endpoint
GET y su panel), sin vista POST, `.rec`, rutas de archivos ni dependencias:
no suma eje de intencion ni de seguridad.

Sondas (test temporal en el worktree, borrado despues; `git status` limpio):
- Partida con cambio de lado y prorroga (0-5 ataque, 6-11 defensa en B, 12
  defensa en A): 1 apertura en B (ronda 6, ganada, 100 %), resto de B 5
  rondas al 40 % (8 y 10 ganadas), A solo en el resto (1 ronda): la
  prorroga no abre.
- `/api/positioning/defense-opener/` con `until=foo`, `page=-1`, `side=`,
  `map=`, `side=%00`, `days=99999999999`, `match_type=Ranked`: 200 y la
  apertura; `session=abc`, `since=2030-01-01`, `map=%E2%80%AE`: 200 y 0.

Mutaciones (codigo roto a mano y restaurado, `tests.test_apertura_defensa`):
- Sin mirar huecos de numeracion: 3 tests caen.
- La primera ronda es tu primera fila y no la de la partida: cae
  `test_sin_tu_fila_de_la_primera_ronda_no_hay_apertura`.
- Las aperturas sumadas al winrate del resto: 3 tests caen.

Hallazgos: ninguno.

Sin hallazgos en: la apertura exige la ronda mas baja de `Round` (no de tus
filas), numeros sin hueco y lado hasta ella y sitio en ella; el resto excluye
las aperturas e incluye las defensas de partidas sin apertura; sin ganador
cuenta y no entra al winrate (test); `opens_share` sobre las aperturas del
mapa; filtros: los que quedan tras quitar `side`, `site` y `operator` son
todos de partida (`base_queryset`), asi que no recortan rondas de una
partida a medias; 2 consultas fijas (`assertNumQueries`, subconsulta y no
lista de ids); agrupado por mapa con su version (`_MAPA`, `_etiquetar`, como
los vecinos); fila en `metricas.md` y su corte en `## Muestra minima`;
calculado al consultar como su vecino `site_after_loss` (precedente del
mismo panel del Coach); identificadores y comentarios sin tildes, UI con
tildes ("defendió", "cuántas", "demás"); sin `print` ni `console.log`; el
diff no sale de `archivos:`.

Ficha: criterios 1 a 5 cubiertos por los tests que lista
`## Implementacion` (corridos en el verde de arriba), las sondas y las
mutaciones. El corte de 5 partidas queda en `## Para el humano` (calibrar).

Skills: no aplica.
Skills del repo: ninguna (revision con el prompt de `revision.md`).
OMC: plan=— · revisión=0 hallazgos · verificación=— (sin subagentes: revision del lider)

## QA

## Para el humano

- Calibrar con la base real el corte de 5 partidas por apertura (`APERTURA_DEFENSA_MIN_PARTIDAS`), puesto solo con datos sinteticos.
