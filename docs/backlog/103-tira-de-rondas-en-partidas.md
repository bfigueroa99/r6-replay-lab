# 103. Tira de rondas en el listado de partidas

estado: aprobado
candado: release 2026-11-09T16:35Z
rama: claude/equipo-dev/103-tira-de-rondas-en-partidas
tipo: funcionalidad
epica: revision-de-rondas
area: fullstack
prioridad: 3
fuente: ALCANCE.md F4 (el PR #14, que tocaba Matches.jsx, se cerro sin merge el 2026-11-05)
archivos: backend/replays/views.py (match_list), backend/tests/test_tira_de_rondas.py, frontend/src/tiraRondas.js, frontend/src/tiraRondas.test.js, frontend/src/pages/Matches.jsx, frontend/src/styles.css, frontend/e2e/tira-rondas.spec.js
turnos: po 20261106T0530Z-ciXX3AM, arquitecto 20261106T0554Z-cFqJHEh, dev 20261106T0648Z-cYjqMjZ, dev 20261109T0345Z-c8x1kCc, revisor 20261109T1205Z-cP2rEUw, qa 20261109T1604Z-cyu4hFR, release 20261109T1604Z-cyu4hFR

## PR

## Que gana quien usa la app

En Partidas, cada fila muestra la secuencia de rondas ganadas y perdidas, con
el lado de cada una, y no solo el marcador final: las remontadas, los
derrumbes y la mitad que se cayo se ven sin abrir la partida.

## Criterios de aceptacion

- [ ] Cada fila de `/api/matches/` trae `strip`: la lista de rondas en orden
      (`number`) con `won` (`my_team_won`, puede ser `null`), `side`
      (`my_side`) y `overtime` (`overtime_number > 0`). Se arma con una sola
      consulta para toda la pagina, no una por partida (test con
      `assertNumQueries` o contando que no crece con el largo de la pagina).
- [ ] La tira es de la partida entera: el filtro de lado o de sitio elige que
      partidas salen, pero no recorta sus rondas (test: con `side=attack` la
      tira sigue trayendo las rondas de defensa).
- [ ] En `Matches.jsx` cada fila dibuja la tira: un cuadradito por ronda,
      ganada y perdida con colores distintos, ronda sin ganador claro
      (`won=null`, ficha 38) en gris, el lado marcado (borde o letra) y la
      prorroga separada; `title` con "R5 · ataque · ganada". Una partida sin
      rondas (ficha 82) muestra la fila sin tira y sin error.
- [ ] Los filtros de Partidas (ficha 78, resultado) y la paginacion siguen
      igual; el e2e de Partidas ve la tira en una partida de `seed_demo` y la
      consola limpia.

## Fuera de alcance

- Hacer clic en un cuadradito para ir a esa ronda (eso es F6, aparte).
- Mostrar la tira en el Inicio (R1) o en Sesiones.
- Bajas por ronda en la tira.

## Diseno

Arquitecto 20261106T0554Z-cFqJHEh.

**Backend, `backend/replays/views.py`, `match_list`:** despues de armar
`page`, una sola consulta para toda la pagina:

```python
tiras: dict[int, list[dict]] = {m.id: [] for m in page}
for match_id, number, won, side, overtime in (
    Round.objects.filter(match__in=page)
    .order_by("match_id", "number")
    .values_list("match_id", "number", "my_team_won", "my_side", "overtime_number")
):
    tiras[match_id].append({"number": number, "won": won, "side": side,
                            "overtime": overtime > 0})
```

y en cada fila `"strip": tiras.get(match.id, [])`. Va con `Round`, no con
`RoundPlayer`: la tira es de la partida y una partida sin tu fila igual
tiene rondas. `order_by` explicito porque el `ordering` de `Round`
(`match__played_at`) agrega un JOIN que no hace falta. `side` es el valor
crudo (`Attack`/`Defense`, o `""` si el import no lo supo). La tira no lee
los filtros: `match_queryset` ya ignora `side`, `operator` y `site` (su
docstring lo explica), y esta consulta filtra solo por `match__in=page`.

**Tests, `backend/tests/test_tira_de_rondas.py` (nuevo), con
`tests/factories.py`:**

- `test_cada_partida_trae_su_tira_en_orden` (rondas creadas desordenadas,
  `number` 0..n en orden, `won`, `side`, `overtime`).
- `test_ronda_sin_ganador_viaja_como_null` (`my_team_won=None`).
- `test_la_prorroga_se_marca` (`overtime_number=1` -> `overtime: true`).
- `test_partida_sin_rondas_trae_tira_vacia`.
- `test_el_filtro_de_lado_no_recorta_la_tira` (`?side=Attack`: la tira trae
  tambien las de `Defense`; idem `?site=`).
- `test_la_tira_no_suma_una_consulta_por_partida`: contar consultas con
  `CaptureQueriesContext` para una pagina de 2 partidas y otra de 6; el
  numero tiene que ser el mismo (no fijar el numero absoluto con
  `assertNumQueries`: otras fichas agregan consultas a `match_list` y lo
  romperian sin motivo).

**Frontend:**

- `frontend/src/tiraRondas.js` (nuevo, puro): `celdasDeTira(strip)` ->
  `[{clave, clase, letra, titulo, corteAntes}]`. `clase`: `win`, `loss` o
  `nula` (`won === null`); `letra`: `A`/`D`/`?` segun `side`; `titulo`:
  `"R5 · ataque · ganada"` (`R${number + 1}`, `ataque`/`defensa`/`lado
  desconocido`, `ganada`/`perdida`/`sin ganador claro`, y `· prórroga` si
  `overtime`); `corteAntes: true` en la primera ronda de prorroga (separador).
  Con `strip` vacio o ausente -> `[]`.
- `frontend/src/tiraRondas.test.js` (nuevo): `ganada perdida y sin ganador
  tienen clases distintas`, `el titulo dice ronda lado y resultado`,
  `la prorroga se separa una sola vez`, `tira vacia o ausente no rompe`,
  `lado desconocido se marca con signo de pregunta`.
- `frontend/src/pages/Matches.jsx`: columna nueva `{ key: 'strip', label:
  'Secuencia', sortable: false, csv: (row) => <texto compacto> }` despues de
  "Resultado"; el CSV lleva la secuencia como texto (`G G P | P G`,
  con `|` antes de la prorroga) para no exportar `[object Object]`. Se
  llama **"Secuencia"**: "Rondas" ya es la columna del conteo y se queda
  igual. Render: `<span className="tira">`
  con un `<span className={'tira-celda ' + clase} title={titulo}>{letra}</span>`
  por celda y un `<span className="tira-corte" />` donde `corteAntes`.
  Partida sin rondas: celda vacia.
- `frontend/src/styles.css`: `.tira { display: inline-flex; gap: 2px }`,
  `.tira-celda` 14x14 px con la letra del lado en 9px, `win` fondo
  `var(--good)`, `loss` fondo `var(--bad)`, `nula` fondo `var(--muted)`;
  `.tira-corte` 6px de ancho. El lado va solo en la letra (A/D): un borde de
  color ademas compite con el verde y el rojo. Clases nuevas, **no** `.round-tab`:
  el detalle y la matriz de duelos ya la usan y el e2e la busca.
- `frontend/e2e/humo.spec.js` (el caso que ya entra a `/partidas`) o
  `frontend/e2e/tira-rondas.spec.js` nuevo: en `/partidas`, la primera fila
  tiene tantos `.tira-celda` como `strip.length` de la primera partida
  de `/api/matches/?limit=1` (y ese largo es mayor que 0), el `title` de la primera celda empieza con `R1 ·`,
  y la consola queda limpia. Pedir los datos a la API, no fijar numeros de
  `seed_demo`.

**Orden:** vista + tests de backend -> `tiraRondas.js` + vitest ->
`Matches.jsx` y CSS -> e2e -> `npm run build`.

**Que puede romperse:** `DataTable` ordena por `key` si no hay
`sortable: false` (ordenar arrays da cualquier cosa); el CSV sin `csv:`
exporta `[object Object] / ...`; una partida de la pagina borrada entre las
dos consultas (el `tiras.get(..., [])` lo cubre). Peso: 50 partidas x ~9
rondas son unos 450 objetos chicos por pagina, aceptable.

**Ramas abiertas:** la 79 (espera al humano) tambien agrega una clave a las
filas de `match_list` en `views.py`, y la 100 toca `_filters` en el mismo
archivo: conflictos de texto de una linea, sin migracion. Implementar
despues de que #79 se mergee si esta lista (prioriza, no bloquea).

**Metricas:** ninguna nueva (la tira muestra `my_team_won` y `my_side` por
ronda, sin agregar). Sin fila en `docs/metricas.md`.

**Verificacion manual:** en la base real, una partida con prorroga y una
ronda sin ganador claro (ficha 38) se ven distintas; exportar CSV de
Partidas y abrirlo: la columna Secuencia es legible.

Skills: no aplica (una columna de tabla y CSS; sin dominio nuevo, sin
busqueda).
Arena: no (una forma obvia).
OMC: plan=— · revisión=— · verificación=— (ficha chica, sin consenso)

## Implementacion

Dev 20261109T0345Z-c8x1kCc (retoma: el reclamo de cYjqMjZ quedo sin codigo
y con el candado muerto 68 h). Hecho el diseno completo, en 136fc61 y 71655cf:

- `backend/replays/views.py`, `match_list`: `strip` por fila con una sola
  consulta a `Round` para la pagina (`order_by("match_id", "number")`), tal
  como el diseno; `won` crudo (puede ser `null`), `side` crudo (`""` si el
  import no lo supo) y `overtime` = `overtime_number > 0`.
- `backend/tests/test_tira_de_rondas.py` (8 tests): los 6 del diseno, mas
  `test_cada_tira_es_de_su_partida` y `test_lado_desconocido_viaja_vacio`.
  El de filtros prueba `side=Attack`, `side=Defense`, `site=` y `operator=`.
  Mutantes vistos caer: una consulta por partida (`8 != 12` en el conteo de
  consultas de 2 contra 6 partidas) y ordenar por `id` en vez de `number`.
- `frontend/src/tiraRondas.js`: `celdasDeTira(strip)` como el diseno y
  `textoDeTira(strip)` para el CSV (`G G P - | P G`). Vitest
  `tiraRondas.test.js` (7): los 5 del diseno, mas claves unicas con prorroga
  y el texto del CSV.
- `frontend/src/pages/Matches.jsx`: columna "Secuencia" despues de
  "Resultado", `sortable: false`, `csv:` con `textoDeTira`; componente
  `TiraRondas` en el mismo archivo. Partida sin rondas: celda vacia.
- `frontend/src/styles.css`: `.tira`, `.tira-celda` (14x14, letra de 9 px
  en el color de fondo) con `win`/`loss`/`nula` y `.tira-corte` de 6 px,
  despues de los `.chip` y no al final del archivo: al final chocaba con el
  bloque `comparar` que la 101 agrega ahi (71655cf).
- `frontend/e2e/tira-rondas.spec.js` (nuevo): la fila de la partida mas
  nueva de `/api/matches/?limit=1` tiene tantos `.tira-celda` como su
  `strip`, la primera con `title` `R1 · ...`, tantas `.win` como rondas
  ganadas; "Descargar CSV" trae la columna Secuencia con el formato legible
  en cada fila con rondas; consola limpia. Sin el `csv:` cae con
  `[object Object] / ...` (visto).

Desvios del diseno:

- **Ronda sin ganador en el CSV: `-`.** El diseno daba `G`/`P` y `|`; faltaba
  la letra de `won=null`. `-` no se confunde con el `?` del lado desconocido
  de la celda.
- La letra de la celda va en `var(--bg)` (el fondo oscuro) y no en un color
  fijo, por contraste sobre verde, rojo y gris.

Revision ciega: sin subagente en esta sesion (no tiene la herramienta para
lanzar `omc-code-reviewer`); la hizo el Dev con el prompt de `revision.md`
sobre el diff sin `docs/backlog`: sin hallazgos CRITICAL ni HIGH. Lo unico
que salio, el e2e buscaba el encabezado por rol `columnheader` y la tabla
lo expone como `cell`: corregido antes del commit. Queda para el Revisor de
otra sesion la revision ciega de verdad.

Verificacion: `verificar.sh` VERDE 71655cf2c (1100 tests backend, 283
vitest, 83 e2e). `merge-tree` limpio contra dev 32fb68d y contra la 79 y la
101.

Verificar en el PC: una partida con prorroga y una ronda sin ganador claro
(ficha 38) se ven distintas en Partidas; "Descargar CSV" y abrirlo en Excel:
la columna Secuencia se lee.

Skills: no aplica (el diseno ya decia que no; sin dominio nuevo).
Arena: no (el diseno no deja puntos abiertos).
OMC: plan=— · revisión=1 hallazgo (1 arreglado; sin subagente, la hizo el Dev) · verificación=—

## Revision

## Revision 2026-11-09 sobre c25627e

Revisor 20261109T1205Z-cP2rEUw. Rama fusionada con dev (c25627e, merge limpio) antes de revisar.

Revision ciega en dos ejes (receta 2 de OMC), cada uno con su propio
`omc-code-reviewer` sobre `git diff origin/dev...HEAD -- . ':(exclude)docs/backlog'`:

- **Estandares:** sin hallazgos. Una consulta por pagina, `won=null` no se
  cuenta como perdida, lado vacio -> `?`, `overtime_number` no admite nulo,
  partida sin rondas -> `[]`. Sin Django en `pydissect/`, sin dependencias,
  sin escrituras, sin numeros nuevos (no corresponde fila en `metricas.md`),
  sin tildes en identificadores, UI con tildes, sin `print`/`console.log`
  (confirmado con grep). Veredicto: aprobar.
- **Intencion** (contra Que gana, Criterios y Fuera de alcance): los cuatro
  criterios cumplidos. Dos LOW, confirmados y no bloqueantes:
  - `Matches.jsx`: la columna Secuencia en el CSV no la pide la ficha. Es lo
    que el diseno pidio para no exportar `[object Object]` (`DataTable`
    exporta toda columna); no es alcance nuevo.
  - `tira-rondas.spec.js`: el e2e no afirma en la app real la celda gris
    (`won=null`) ni el corte de prorroga; esos casos los cubre solo vitest.
    El criterio pide "ve la tira y la consola limpia", y eso lo hace. Mejora
    opcional: contar tambien `.tira-celda.loss` y `.tira-celda.nula` contra
    `strip`.

Criterios contra tests:

- `strip` en orden con `won`/`side`/`overtime` y una sola consulta:
  `test_cada_partida_trae_su_tira_en_orden`, `test_ronda_sin_ganador_viaja_como_null`,
  `test_la_prorroga_se_marca`, `test_la_tira_no_suma_una_consulta_por_partida`
  (compara paginas de 2 y 6 filas de verdad; fallaria con una consulta por partida).
- Filtros no recortan: `test_el_filtro_de_lado_no_recorta_la_tira` (`side`,
  `site`, `operator`; la partida tiene una ronda de cada lado y sitio).
- Render en `Matches.jsx`: vitest `tiraRondas.test.js` (clases, titulo
  `R5 · ataque · ganada`, prorroga una vez, tira vacia, lado `?`) y el e2e.
- Filtros y paginacion igual: suite completa y e2e de `humo.spec.js` verdes.

`archivos:` cubre todo el diff. Nada fuera de alcance (sin clic a la ronda,
sin Inicio ni Sesiones, sin bajas).

Verificacion: `verificar.sh` VERDE c25627eb5 (1100 tests backend, 295
vitest, 84 e2e).

Veredicto: **aprobar** -> `revisado`.

Skills: no aplica.
OMC: plan=— · revisión=2 hallazgos LOW (0 arreglados, no bloquean) · verificación=—

## QA

## QA 2026-11-09 sobre 32988db

QA 20261109T1604Z-cyu4hFR. La rama ya contenia `origin/dev` 580e6da
(`merge-tree` limpio). Base sintetica desde `tests/factories.py`
(script en el scratchpad, nada al repo): Bank con 7 rondas (`won`
True/False/None, `side` Attack/""/Defense, `overtime_number` 1 y 2),
Oregon con 4 rondas creadas desordenadas (3, 0, 2, 1) y Border sin rondas.

- **check.sh completo:** `verificar.sh` VERDE 32988dbbe (1100 tests
  backend, 295 vitest, 84 e2e), exit 0.
- **Base vacia:** `SQLITE_PATH=<vacia> manage.py migrate` + `runserver`;
  `curl /api/matches/` -> 200 `{"total": 0, ..., "matches": []}`.
- **Criterio 1 (strip en orden, crudo):** `curl /api/matches/` sobre la
  sembrada: Bank `number` 0..6, `won: null` en R3, `side: ""` en R5,
  `overtime: true` solo en R6 y R7; Oregon sale 0..3 aunque se creo
  desordenada; Border `strip: []`. La consulta unica la cubre
  `test_la_tira_no_suma_una_consulta_por_partida`.
- **Criterio 2 (filtros no recortan):** `?side=Attack`, `?side=Defense`,
  `?site=B%20Church`, `?operator=Ash`, `?side=` -> 200 y largos `[0, 4, 7]`.
- **Bordes:** `until=foo`, `page=-1`, `offset=-1`, `limit=99999`,
  `days=99999999` -> 200 con tiras completas; `limit=0` -> 1 fila (como en
  dev). `result=victoria` -> Oregon 4 y Bank 7; `result=empate` -> Border 0;
  `result=victoria&limit=1&offset=1` -> Bank con 7. Vecinos:
  `/api/matches/1/` 200, `/api/matches/999/` 404, `/api/sessions/` 200.
  Logs del server sin traceback.
- **Criterio 3 (UI):** Chromium en `/partidas` con la base sembrada: Bank
  dibuja 7 `.tira-celda` `win loss nula win loss win win`, letras
  `A A A D ? D A`, `title` `R3 · ataque · sin ganador claro`,
  `R5 · lado desconocido · perdida`, `R6 · defensa · ganada · prórroga`,
  un solo `.tira-corte`; Border sin celdas; consola con 0 errores. Columna
  "Secuencia" despues de "Resultado"; "Rondas" sigue con el conteo.
- **Criterio 4 (filtros, paginacion, e2e):** los de arriba y
  `tira-rondas.spec.js` + `humo.spec.js` dentro de los 84 e2e verdes.
- **Peso:** chunk inicial `index-*.js` 195615 bytes en la rama y en dev
  (sin crecer); chunk lazy de Matches 3057 -> 4067; CSS 13505 -> 13896.
- **Mutaciones (todas caen):** `overtime > 0` -> `>= 0` (2 tests backend);
  tira filtrada por el `side` de la request
  (`test_el_filtro_de_lado_no_recorta_la_tira`, Attack y Defense);
  `won=null` -> clase `loss` (2 vitest); corte en cada ronda de prorroga
  (2 vitest).

Como repetirlo: `SQLITE_PATH=/tmp/x.sqlite3 python manage.py migrate`,
sembrar con `make_match`/`make_round` como arriba en `manage.py shell`,
`runserver` y los `curl` de esta seccion.

Veredicto: **aprobar** -> `aprobado`. Sin migracion, parser, Electron ni
`.ps1`: nada nuevo para Verificar en el PC (queda el de Implementacion).

OMC: plan=— · revisión=— · verificación=PASS (omc-verifier, 4 criterios VERIFIED)

## Para el humano

(nada)
