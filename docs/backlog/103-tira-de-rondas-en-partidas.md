# 103. Tira de rondas en el listado de partidas

estado: implementado
candado: -
rama: claude/equipo-dev/103-tira-de-rondas-en-partidas
tipo: funcionalidad
epica: revision-de-rondas
area: fullstack
prioridad: 3
fuente: ALCANCE.md F4 (el PR #14, que tocaba Matches.jsx, se cerro sin merge el 2026-11-05)
archivos: backend/replays/views.py (match_list), backend/tests/test_tira_de_rondas.py, frontend/src/tiraRondas.js, frontend/src/tiraRondas.test.js, frontend/src/pages/Matches.jsx, frontend/src/styles.css, frontend/e2e/tira-rondas.spec.js
turnos: po 20261106T0530Z-ciXX3AM, arquitecto 20261106T0554Z-cFqJHEh, dev 20261106T0648Z-cYjqMjZ, dev 20261109T0345Z-c8x1kCc

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

## QA

## Para el humano

(nada)
