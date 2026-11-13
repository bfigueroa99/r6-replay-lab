# 114. Qué operadores te abren

estado: revisado
candado: qa 2026-11-13T17:33Z
rama: claude/equipo-dev/114-que-operadores-te-abren
tipo: funcionalidad
epica: rivales
area: fullstack
prioridad: 3
fuente: ALCANCE.md D7
archivos: backend/replays/analytics/aggregates.py (openings_by_operator), backend/replays/views.py (duels), backend/tests/test_duels.py, frontend/src/operadoresQueTeAbren.js (nuevo), frontend/src/operadoresQueTeAbren.test.js (nuevo), frontend/src/pages/Duelos.jsx, frontend/e2e/humo.spec.js, docs/metricas.md
turnos: po 20261112T1204Z-chGLrtC, arquitecto 20261113T1203Z-cWfR3tT, dev 20261113T1643Z-c4P1LiD, revisor 20261113T1703Z-ctZvzXQ

## PR

## Que gana quien usa la app

En Duelos, por lado, que operadores rivales te sacan en el primer duelo de la
ronda (tu muerte de apertura) y a cuales abris tu, con cuantas veces y en que
proporcion de tus aperturas perdidas. La tabla "Por operador rival" cuenta
todos los duelos de la ronda; esta dice a que operador tenes que aprender a
jugarle la entrada.

## Criterios de aceptacion

- [ ] `/api/duels/` devuelve una clave nueva con filas por operador rival y
      tu lado: `opened_you` (rondas donde la primera baja de la ronda fue de
      ese operador sobre ti), `you_opened` (tuya sobre ese operador),
      `share` (`opened_you` sobre todas tus muertes de apertura de ese lado)
      y el balance. Test con rondas armadas: Ash te abre en dos y tu abres a
      Ash en una.
- [ ] Un teamkill o una baja sin autor como primera baja de la ronda no
      suma a ningun operador (mismo criterio que la columna De apertura de
      "Por rival"), y un operador rival vacio o `Unknown(...)` tampoco. Test.
- [ ] Respeta los filtros globales; el de lado separa (tu lado de esa ronda);
      muestra minima propia y documentada (aperturas con ese operador), y
      ordenada por `opened_you` descendente.
- [ ] La tabla se ve en Duelos; sin filas, un texto y no un error. El e2e
      de humo pasa por Duelos con la consola limpia.
- [ ] Fila nueva en `docs/metricas.md` ("Operadores que te abren").

## Fuera de alcance

- Rivales que te abren por persona: ya esta en la columna De apertura de
  "Por rival" (ficha 108, descartada por eso).
- Que operador te abre por mapa o sitio (D2).
- Aperturas entre compañeros.

## Diseno

(arquitecto 20261113T1203Z-cWfR3tT) Filtros duros: pasa. Usa el kill feed
(`Event`, primera baja por `order`) y el operador del rival en el scoreboard
de esa ronda (`RoundPlayer.operator`), que el `.rec` entrega; sin red, sin
dependencias, sin POST, sin migracion. Premisa verificada contra dev
(96fa2c1): `duels_by_operator` cuenta todos los duelos y no tiene columnas de
apertura; las de apertura solo estan por persona (`nemesis`). Una forma
obvia (~250 lineas, el mismo patron de `nemesis`): sin arena ni consenso.

**Backend, `backend/replays/analytics/aggregates.py`**, despues de
`duels_by_operator`:
- `openings_by_operator(min_openings: int = 3, **filters) -> list[dict]`:
  - `me_ids = _me_ids()`; sin ids, `[]`.
  - `contra_mi, a_favor = _duelos(base_queryset(**filters), me_ids)`, y de
    cada uno solo la apertura: `.filter(id=_PRIMER_EVENTO)` (lo mismo que
    `opening_deaths` / `opening_kills` de `nemesis`). Teamkills y bajas sin
    autor ya los saca `_solo_rivales` (`equipo_rival` nulo o igual al mio);
    un primer evento `Death` sin asesino no es `Kill` y no entra en ninguno.
  - Agrupar con `.values("op_rival", "round__my_side").annotate(n=Count("id"))`:
    `opened_you` desde `contra_mi`, `you_opened` desde `a_favor`. Saltar
    `round__my_side` vacio, `op_rival` vacio o nulo y los que empiezan con
    `UNKNOWN_PREFIX` (`replays/unknowns.py`, `"Unknown("`).
  - Denominador de `share`, por lado: **todas** tus muertes de apertura
    contra rivales de ese lado (`contra_mi` de apertura agrupado solo por
    `round__my_side`), incluidas las de operador vacio o desconocido; asi la
    suma de `share` de un lado puede quedar debajo de 100 y nunca encima.
  - Fila: `operator`, `side`, `opened_you`, `you_opened`,
    `openings = opened_you + you_opened`, `balance = you_opened - opened_you`,
    `winrate = _pct(you_opened, openings)`, `share = _pct(opened_you,
    muertes_de_apertura_del_lado)` (`None` con denominador 0).
  - Muestra minima: `openings >= min_openings`.
  - Orden: `(-opened_you, -openings, operator, side)`.
- El filtro de lado no necesita nada propio: `base_queryset(side=)` deja
  solo tus rondas de ese lado y `_mis_bajas` las toma con `Exists`, asi que
  solo salen filas de ese lado.

**`backend/replays/views.py`, `duels`**: `"opening_operators":
agg.openings_by_operator(min_openings=min_duels, **filters),` despues de
`"operators"`. Usa la misma `min_duels` que el selector "Muestra minima"
de la pagina: el selector manda sobre las dos tablas de operador.

**Tests backend, `backend/tests/test_duels.py`**, clase nueva
`OperadoresQueTeAbrenTests` (helper `_ronda(numero, operador_rival="Ash",
side="Attack")` como el de `DuelosTests`: tu fila y la del rival en
`team_index=1`):
- `test_ash_te_abre_en_dos_y_tu_le_abres_en_una`: tres rondas contra Ash;
  en dos la primera baja es Ash sobre ti, en una tuya sobre Ash ->
  `opened_you=2`, `you_opened=1`, `balance=-1`, `share=100.0`,
  `winrate=33.3`.
- `test_solo_cuenta_la_primera_baja_de_la_ronda`: Ash te mata como segundo
  evento (antes cae otro) -> sin fila de Ash con `min_openings=1`.
- `test_teamkill_que_abre_no_suma_a_ningun_operador`: primera baja de un
  companero (`team_index=0`) sobre ti -> `[]`.
- `test_muerte_sin_autor_que_abre_no_suma`: primer evento `kind="Death"`
  sin actor -> `[]`.
- `test_operador_vacio_o_desconocido_no_tiene_fila_pero_pesa_en_el_share`:
  una apertura de Ash, una de `""` y una de `"Unknown(123)"` -> solo la
  fila Ash, con `share=33.3`.
- `test_separa_por_tu_lado`: Thorn te abre en una ronda de ataque y en una
  de defensa -> dos filas (`Attack`, `Defense`), una apertura cada una.
- `test_el_filtro_de_lado_deja_solo_ese`: el mismo historial con
  `side="Defense"` -> una fila, `Defense`.
- `test_muestra_minima_y_orden`: Ash 3 aperturas, Thorn 1 -> con 3 solo
  Ash; con 1, Ash primero (mas `opened_you`).
- `test_la_api_devuelve_opening_operators_con_la_muestra_del_selector`:
  `GET /api/duels/?min_duels=1` trae `opening_operators` con la fila;
  sin parametro (3) no.

**Frontend.**
- `frontend/src/operadoresQueTeAbren.js` (logica pura, nuevo):
  `filasOperadoresQueTeAbren(rows)` -> `[]` sin filas; cada fila con
  `key: \`${operator}-${side}\`` y el resto tal cual (el lado lo pinta
  `SideChip`).
- `frontend/src/operadoresQueTeAbren.test.js` (vitest): vacio y `undefined`
  dan `[]`; la clave separa el mismo operador en dos lados; no reordena (el
  orden es el de la API).
- `frontend/src/pages/Duelos.jsx`: `Panel` nuevo "Operadores que te abren"
  justo despues de "Por operador rival", con `right={selector}` no (el
  selector ya esta en el panel de arriba y manda en los dos; el hint lo
  dice). `hint`: "La primera baja de la ronda, por operador rival y por tu
  lado. Te abre: te sacó a vos en el primer duelo; Le abres: lo sacaste
  vos. El % es sobre todas tus muertes de apertura de ese lado. Usa la
  muestra mínima de arriba, contada en aperturas." Tabla `DataTable`:
  Operador (`left`), Lado (`SideChip`), Te abre (`opened_you`), Le abres
  (`you_opened`), Balance (`<Balance>` de la pagina), Ganas (`columnaDuelos`
  no: `pct(row.winrate)`), De tus aperturas perdidas (`pct(row.share)`, con
  `help`). `initialSort={{ key: 'opened_you', dir: 'desc' }}`,
  `rowKey={(row) => row.key}`, `csvName="operadores-que-te-abren"`,
  `empty={\`Ningún operador llega a ${minDuels} aperturas con estos filtros.\`}`.
  Lee `data.opening_operators ?? []`.

**e2e, `frontend/e2e/humo.spec.js`**, test `Duelos muestra los operadores
que te abren` junto a los de Duelos: pedir `/api/duels/`
(`opening_operators`, muestra 3); en `/duelos`, el panel "Operadores que te
abren" visible; si la API trae filas, la tabla tiene esa cantidad de filas y
la primera muestra el `operator` y el `opened_you` de la API; si no, el
texto vacio. Consola limpia. Numeros de la API, no a mano: si cambia el
seed no se toca.

**`docs/metricas.md`**, seccion `## Duelos`, fila **Operadores que te
abren**: la apertura es la primera baja de la ronda (`Kill` o `Death` por
`order`, la misma de *Duelos de apertura*); cuenta solo si es una baja
entre rivales (sin teamkills ni muertes sin asesino). *Te abre*: esa baja
fue del rival con ese operador (scoreboard de la ronda) sobre ti; *Le
abres*: tuya sobre el. Por tu lado de la ronda (`Round.my_side`). *%*:
*Te abre* / todas tus muertes de apertura contra rivales de ese lado,
incluidas las de operador vacio o `Unknown(...)`, que no tienen fila (por
eso un lado puede sumar menos de 100). Muestra minima: aperturas (*Te abre*
+ *Le abres*) >= la *Muestra minima* de la pagina (3 por defecto). Pagina
Duelos, panel *Operadores que te abren*.

**Orden.** aggregates + tests, vista, `operadoresQueTeAbren.js` + vitest,
`Duelos.jsx`, e2e, metricas, `npm run build`.

**Que puede romperse.** Dos consultas mas en `/api/duels/` con la subquery
de `_PRIMER_EVENTO` (las mismas que ya corre `nemesis`); con bases grandes
es lo que cuesta, igual que alli. `duels_by_operator` y `nemesis` no se
tocan; sus tests siguen fijandolos. Si algun test compara la lista entera
de claves de `/api/duels/`, sumarle `opening_operators`
(`grep -n "rival_stacks" backend/tests`).

**Archivos ocupados.** `aggregates.py`, `views.py`, `humo.spec.js` y
`metricas.md` los tocan la 110, la 113 y la 115 (y la 79 sin `humo`) en
otras funciones, otras vistas y otros tests; `Duelos.jsx` y `test_duels.py`
no los toca ninguna rama abierta. Merge trivial; no se frena. La 79 cambia
`base_queryset`; esto lo usa como todos, asi que hereda la exclusion sin
cambios.

**Verificacion manual.** `seed_demo`, `/duelos`: panel con filas
(operador, lado, te abre); `?side=Defense` solo filas de defensa; bajar la
muestra a 1 suma filas en las dos tablas de operador.

Skills: no aplica (mismo patron que `nemesis` y `duels_by_operator`).
Skills del repo: statistical-analysis (denominador del %: todas las muertes de apertura del lado, no la suma de las filas; `n` minimo en aperturas con el selector existente, sin umbral nuevo que calibrar), testing-strategy (Django para la consulta y la vista, vitest para la clave de fila, e2e para el panel).
OMC: plan=— · revisión=— · verificación=—

## Implementacion

(dev 20261113T1643Z-c4P1LiD) Diseno completo, sin desvios de forma:

- `aggregates.py`: `openings_by_operator(min_openings=3, **filters)` despues de
  `duels_by_operator`, sobre `_duelos` + `_PRIMER_EVENTO` (como `nemesis`):
  agrupa por `op_rival` y `round__my_side`, salta lado vacio, operador vacio y
  `Unknown(...)`; `share` sobre todas tus muertes de apertura contra rivales
  del lado (incluidas las sin fila). 3 consultas agregadas, sin N+1.
  `views.duels` suma `opening_operators` con la misma `min_duels` del selector.
- `operadoresQueTeAbren.js`: `filasOperadoresQueTeAbren` (clave
  `operador-lado`, no reordena). `Duelos.jsx`: panel "Operadores que te abren"
  despues de "Por operador rival", con Lado (`SideChip`), Te abre, Le abres,
  Balance, Ganas y "De tus aperturas perdidas" (con `help`); CSV
  `operadores-que-te-abren`; vacio "Ningún operador llega a N aperturas con
  estos filtros.".
- Desvio menor de texto: el hint del diseno decia "te sacó a vos"; la pagina
  tutea ("Le ganas", "Te gana"), asi que va "te sacó a ti" / "lo sacaste tú".
- e2e: el seed trae 6 filas con muestra 3 (Rook/Attack 39 primero), asi que el
  test exige filas y compara la primera con la API (sin rama del texto vacio).

Tests, vistos en rojo antes del codigo: backend `OperadoresQueTeAbrenTests`
(10; los 10 caian con `AttributeError`), vitest `operadoresQueTeAbren.test.js`
(3; sin modulo no corrian). Criterios -> tests: Ash 2/1 con share 100 y
winrate 33.3 (`test_ash_te_abre_en_dos_y_tu_le_abres_en_una`); solo la
primera baja (`test_solo_cuenta_la_primera_baja_de_la_ronda`); teamkill,
muerte sin autor y operador vacio/desconocido
(`test_teamkill_...`, `test_muerte_sin_autor_...`,
`test_operador_vacio_o_desconocido_...`); lado, filtros, muestra y orden
(`test_separa_por_tu_lado`, `test_el_filtro_de_lado_deja_solo_ese`,
`test_el_filtro_de_mapa_aplica`, `test_muestra_minima_y_orden`); API
(`test_la_api_devuelve_opening_operators_con_la_muestra_del_selector`);
panel y consola (e2e `Duelos muestra los operadores que te abren`); fila en
`metricas.md`.

verificar.sh: VERDE ea46a9942 (1210 backend, 354 vitest, 99 e2e; el commit
siguiente solo toca esta ficha).

Revision ciega (`omc-code-reviewer`, estandares): aprobar, 3 LOW, los 3
arreglados (voseo en un docstring, el hint y el `help` del % ahora dicen
"contra rivales", e2e sin rama silenciosa). Pregunta que no bloquea:
`duels_by_operator` no descarta `Unknown(...)` y esta si; es anterior a esta
ficha.

Skills: no aplica.
Skills del repo: modern-web-guidance (leida; ninguna guia aplica: `Panel` y `DataTable` existentes, sin CSS ni componente nuevo), ux-copy (hint, vacio y `help` con la estructura que que es + por que; tuteo como el resto de Duelos).
OMC: plan=— · revisión=3 hallazgos (3 arreglados; 0 CRITICAL/HIGH) · verificación=—

## Revision 2026-11-13 sobre f0be4ed

(revisor 20261113T1703Z-ctZvzXQ) Punto de partida: la rama ya contiene
`origin/dev` (0293ade); `verificar.sh`: VERDE f0be4ed66 (1210 backend, 354
vitest, 99 e2e).

**Revision ciega, eje de estandares** (`omc-code-reviewer`, prompt de
`revision.md`, solo el diff): sin hallazgos. Confirmado leyendo el codigo:
reusa `_duelos`, `_solo_rivales` y `_PRIMER_EVENTO` como `nemesis`; un
`Death` sin autor que abre la ronda queda como primer evento y no matchea
ningun `Kill`; `share` con denominador 0 da `None` (`_pct`).

**Eje de intencion** (`omc-code-reviewer`, diff contra Que gana, Criterios y
Fuera de alcance; diff de ~340 lineas): aprobar, 4 LOW.
- L1 (denominador "contra rivales" y no todas las `opening_death`): es lo que
  dice el diseno y `metricas.md`; no es hallazgo.
- L2 (la muestra reusa `min_duels`): decision del diseno, documentada en el
  hint y en `metricas.md`; no es hallazgo.
- L3 (ningun test fija que un teamkill de apertura no infla el `share`):
  **confirmado y cubierto** con el test nuevo
  `test_un_teamkill_de_apertura_no_pesa_en_el_share` (Ash te abre una ronda,
  un compañero te mata abriendo otra del mismo lado -> solo la fila Ash,
  `share=100.0`). Verde; mutacion: sumar 1 al denominador por lado lo hace
  caer (`AssertionError: 50.0 != 100.0`).
- L4 (`openings` y `winrate` de mas): definidos en `metricas.md`; no es
  hallazgo.
- Pregunta abierta del revisor (filtro `side` sobre `RoundPlayer.side` y
  agrupado por `Round.my_side`): mismo patron que el resto de Duelos; tus dos
  lados coinciden por construccion al importar. Sin hallazgo.

**Ficha.** Criterio 1: `test_ash_te_abre_en_dos_y_tu_le_abres_en_una` y el
de la API. Criterio 2: tests de teamkill, muerte sin autor y operador vacio
o desconocido, mas el nuevo. Criterio 3: tests de lado, filtro de lado, de
mapa, muestra y orden. Criterio 4: e2e `Duelos muestra los operadores que te
abren` y `empty` en `Duelos.jsx`. Criterio 5: fila en `metricas.md` (seccion
Duelos). El diff no sale de `archivos:`; identificadores y comentarios sin
tildes, UI con tildes; sin `print` ni `console.log`.

Veredicto: aprobar.

Skills del repo: ninguna (revision con `revision.md`).
OMC: plan=— · revisión=4 hallazgos LOW (1 cubierto con test; 3 no son hallazgo) · verificación=—

## QA

## Para el humano

(nada)
