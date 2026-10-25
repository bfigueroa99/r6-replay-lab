# 61. Clutch por operador

estado: revisado
candado: -
rama: claude/equipo-dev/61-clutch-por-operador
tipo: funcionalidad
epica: operadores
area: fullstack
prioridad: 3
fuente: ALCANCE.md O6 (siguiente tramo tras las fichas 55 y 59, ya en main)
archivos: backend/replays/analytics/aggregates.py, backend/replays/views.py, backend/tests/test_clutch.py, frontend/src/pages/Teammates.jsx, frontend/e2e/humo.spec.js, docs/metricas.md
turnos: po 20261024T1204Z, arquitecto 20261024T1605Z, dev 20261025T0004Z, revisor 20261025T0404Z

## Que gana quien usa la app

Hoy el panel "Clutches" de Compañeros dice cuantos clutches intentas y
conviertes por 1vX y por mapa y sitio, pero no con que operador. Esta tabla
dice con que operador cierras las rondas que quedan en tus manos y con cual
las sueltas, separado por lado.

## Criterios de aceptacion

- [ ] `/api/teammates/` trae una clave nueva `clutch_by_operator`: una fila
  por operador y lado con `operator`, `side`, `attempts`, `won`, `pct` y
  `low_sample`; intento y ganado con la misma definicion que
  `clutch_conversion` (`clutch_vs > 0`, rondas con `my_team_won` nulo
  afuera), asi que la suma de `attempts` de todas las filas es igual a la
  suma de `attempts` de `clutch_conversion` con los mismos filtros (menos
  las rondas sin operador, que no salen en ninguna fila: test).
- [ ] Las filas con menos intentos que el minimo (constante en
  `aggregates.py`, como `CLUTCH_SITIO_MIN`) salen igual con
  `low_sample: true`; borde N-1 / N con test.
- [ ] Respeta los filtros de la barra (`side`, `map`, `ranked_only`,
  `since`, `until`): test con `side=Attack` que deja solo filas de ataque.
- [ ] Base vacia: 200 y `clutch_by_operator: []`.
- [ ] Compañeros, panel "Clutches": tabla "Clutch por operador" (Operador,
  Lado, Intentos, Ganados, Conversión) con `*` en muestra chica, orden por
  intentos y boton CSV `clutch-por-operador`; e2e sobre `seed_demo` que la
  encuentra con al menos una fila.
- [ ] Fila nueva en `docs/metricas.md` junto a las de clutch.

## Fuera de alcance

- "Cuantos se esperaban" (parte de K3 que depende de la tabla K1).
- Clutch por operador y mapa a la vez: la muestra no da.
- Migracion o columna nueva: `clutch_vs` ya existe (ficha 55).

## Diseno

(arquitecto 20261024T1605Z) Una sola forma obvia: es `clutch_by_site` con
otro `values()`. Sin arena, sin migracion, sin columna nueva.

**Archivos y por que**

- `backend/replays/analytics/aggregates.py`: debajo de `clutch_by_site`,
  constante `CLUTCH_OPERADOR_MIN = 5` (propia, con el mismo comentario de
  "por debajo de esto el % es anecdota"; no reusar `CLUTCH_SITIO_MIN`, son
  cortes distintos que pueden calibrarse por separado) y funcion
  `clutch_by_operator(**filters) -> list[dict]`:
  `base_queryset(**filters).filter(clutch_vs__gt=0, round__my_team_won__isnull=False).exclude(operator="").values("operator", "side").annotate(attempts=Count("id"), won=Count("id", filter=Q(round__my_team_won=True)))`.
  Filas con `side` fuera de `("Attack", "Defense")` se descartan (igual que
  `clutch_conversion`, que solo las suma al total; aca el lado es parte de
  la clave). Cada fila: `operator`, `side`, `attempts`, `won`,
  `pct=_pct(won, attempts)`, `low_sample=attempts < CLUTCH_OPERADOR_MIN`.
  Orden: `-attempts`, despues `operator`, despues `side`. Docstring: "mismo
  intento y ganado que `clutch_conversion`; las rondas sin operador no
  salen".
- `backend/replays/views.py`, `teammates`: `"clutch_by_operator": agg.clutch_by_operator(**filters)` despues de `clutch_by_site`.
- `backend/tests/test_clutch.py`: clase nueva `ClutchPorOperadorTests`
  con un `_ronda` como el de `ClutchPorSitioTests` que acepte `operator` y
  `side`. Tests:
  - `test_una_fila_por_operador_y_lado_con_intentos_y_ganados`
  - `test_los_intentos_suman_lo_mismo_que_la_conversion_menos_sin_operador`
    (una ronda con `operator=""` que esta en `clutch_conversion` y no en
    ninguna fila)
  - `test_cuatro_intentos_son_muestra_chica_y_cinco_no` (borde con
    `CLUTCH_OPERADOR_MIN - 1` y `CLUTCH_OPERADOR_MIN`, no con literales)
  - `test_una_ronda_sin_ganador_no_cuenta_como_intento_por_operador`
  - `test_clutch_por_operador_respeta_el_filtro_de_lado` (`side="Attack"`
    deja solo filas `Attack`)
  - `test_la_api_de_companeros_trae_clutch_por_operador_vacio_sin_datos`
    (`/api/teammates/` en base vacia: 200 y `[]`).
- `frontend/src/pages/Teammates.jsx`, panel "Clutches": `<h3>Clutch por
  operador</h3>` y un `DataTable` **entre** "Clutch por mapa y sitio" y
  "Clutches ganados" (el e2e existente usa `table.first()` y `nth(1)`:
  insertar despues de la segunda tabla no los mueve). Columnas: Operador
  (`left`), Lado (`<SideChip side={row.side} />`, `csv` con el texto
  Ataque/Defensa), Intentos, Ganados, Conversion con `<Bar>` y el `*`
  `.muestra-chica` copiado de la tabla por sitio (help con "menos de 5
  intentos"). `initialSort={{ key: 'attempts', dir: 'desc' }}`,
  `rowKey={(row) => `${row.operator}-${row.side}`}`,
  `csvName="clutch-por-operador"`, mismo `empty` que las otras dos.
  Encabezado de columna "Conversión" con tilde.
- `frontend/e2e/humo.spec.js`: `test('Compañeros muestra el clutch por
  operador', ...)` con el patron del de mapa y sitio: panel "Clutches",
  heading "Clutch por operador", `panel.locator('table').nth(2)` con al
  menos una fila en `tbody`, consola limpia. Si el Dev quiere afirmar una
  fila exacta, sacar el numero corriendo `seed_demo` (los intentos salen de
  `OPERADORES[lado][indice % 3]`), no a ojo.
- `docs/metricas.md`, tabla `## Impacto`, fila **Clutch por operador**
  debajo de "Clutch por mapa y sitio": mismo intento y ganado, agrupado por
  `RoundPlayer.operator` y lado; las rondas sin operador no salen (por eso
  la suma puede ser menor que la de la conversion); `*` con menos de 5
  intentos (`CLUTCH_OPERADOR_MIN`); respeta los filtros de la barra.

**Orden:** aggregates + test backend, views, `manage.py test tests`,
Teammates.jsx, `npm run build`, e2e, metricas.md, `check.sh`.

**Que puede romperse:** nada persistente (ni migracion ni recompute). El
riesgo es el indice de tablas del e2e de Compañeros si la tabla se pone en
otro lugar. Con el filtro `operator` de la barra la tabla queda en un solo
operador: es correcto, no se esconde.

**Verificacion manual:** `/companeros` con la base demo, la tabla aparece
tercera en el panel, el CSV baja `clutch-por-operador.csv` con la columna
Lado en texto; `curl -s localhost:8000/api/teammates/?side=Defense | python -m json.tool`
solo trae `Defense`.

**Paralelo:** toca `aggregates.py`, `views.py`, `metricas.md` y
`humo.spec.js` igual que 62 y 63, pero en otras funciones y otras filas: se
puede implementar en paralelo; quien mergea segundo resuelve un conflicto
de lineas vecinas, si aparece.

## Implementacion

(dev 20261025T0004Z) Diseno completo, sin desvios.

- `aggregates.py`: `CLUTCH_OPERADOR_MIN = 5` y `clutch_by_operator(**filters)`
  debajo de `clutch_by_site`, con el mismo filtro de intento
  (`clutch_vs > 0`, `my_team_won` no nulo), `exclude(operator="")` y las
  filas sin lado Attack/Defense descartadas. Orden `-attempts`, operador, lado.
- `views.py`: `clutch_by_operator` en `/api/teammates/` despues de `clutch_by_site`.
- `test_clutch.py`: `ClutchPorOperadorTests` con los seis tests del diseno;
  el borde de muestra chica usa `CLUTCH_OPERADOR_MIN` y no literales.
- `Teammates.jsx`: tabla "Clutch por operador" tercera en el panel Clutches
  (entre por sitio y ganados), CSV `clutch-por-operador` con el lado en texto.
- `humo.spec.js`: `Compañeros muestra el clutch por operador`, con numeros
  sacados de correr `seed_demo`: 3 filas, Rook Defensa 5 0 0% sin `*` y
  Zofia Ataque 2 2 100% con `*` (la suma, 10, es igual a la de la conversion:
  el demo no tiene rondas sin operador).
- `docs/metricas.md`: fila **Clutch por operador** debajo de la de mapa y sitio.
- Revision ciega con `revision.md`: sin bloqueantes. Corregido lo real: la
  doc y el docstring ahora dicen que tambien quedan afuera las filas sin lado.
  El `nth(2)` del e2e sigue el patron de las otras dos tablas del panel.

**Verificacion:** `check.sh` en `Todo en verde.` sobre ff92c7d (ruff ok, 769
tests backend con 4 skip, 120 vitest, build, e2e 48/48). Como en los turnos
anteriores, el e2e pide `chromium_headless_shell-1194` y la imagen trae la
1243: se corrio con `PLAYWRIGHT_BROWSERS_PATH` apuntando a enlaces en el
scratchpad, sin tocar el repo.

## Revision 2026-10-25 sobre ac5ce50

(revisor 20261025T0404Z) Rama fusionada con `origin/main` (19683ce) antes de
revisar. Revision ciega con `revision.md` sobre el diff sin `docs/backlog`:
sin hallazgos. Confirmado por el lider:

- `clutch_by_operator` parte de `base_queryset` (solo filas `is_me`, filtros
  de la barra) con el mismo intento y ganado que `clutch_conversion`;
  `operator` es `CharField` sin `null`, asi que `exclude(operator="")`
  alcanza.
- Criterios: los seis tests de `ClutchPorOperadorTests` cubren filas, suma
  contra la conversion menos sin operador, borde `MIN-1`/`MIN` con la
  constante, ronda sin ganador, filtro de lado por la API y base vacia. Cada
  uno cae si se quita la regla que nombra (leido contra el codigo).
- UI: tabla tercera del panel Clutches, CSV `clutch-por-operador` con el
  lado en texto, `*` en muestra chica; el e2e afirma 3 filas y los numeros
  de `seed_demo` (el subagente los reprodujo: Rook D 5-0, Jager D 3-0 `*`,
  Zofia A 2-2 `*`).
- Fila en `docs/metricas.md`; diff dentro de `archivos:`; sin tildes en
  identificadores, UI con tildes, sin `print` ni `console.log`.

**Verificacion:** `check.sh` en `Todo en verde.` sobre ac5ce50 (ruff ok, 769
tests backend con 4 skip, 120 vitest, build, e2e 48/48).

Veredicto: aprobar.
