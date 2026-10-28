# 64. Partidas en el Inicio: ganadas, rondas por partida y mejor y peor mapa

estado: aprobado
candado: release 2026-10-28T04:10Z
rama: claude/equipo-dev/64-partidas-en-el-inicio
tipo: funcionalidad
epica: paridad-referencia
area: fullstack
prioridad: 3
fuente: ALCANCE.md R1 (replica/features.csv fila 11, must, clone partial; [aurelix](https://aurelix.app/))
archivos: backend/replays/analytics/aggregates.py, backend/replays/views.py, frontend/src/pages/Dashboard.jsx, backend/tests/test_resumen_partidas.py, frontend/e2e/humo.spec.js, docs/metricas.md
turnos: po 20261027T1205Z, arquitecto 20261027T1605Z, dev 20261027T2005Z, revisor 20261028T0004Z, qa 20261028T0404Z

## PR

(La escribe el Release manager al final.)

## Que gana quien usa la app

El Inicio hoy cuenta todo en rondas; lo primero que uno quiere saber es
cuantas partidas gano. Este item suma una fila de partida al Inicio: partidas
ganadas sobre jugadas, rondas promedio por partida y tu mejor y peor mapa por
winrate de partida, con los mismos filtros que el resto de la pagina.

## Criterios de aceptacion

- [ ] `GET /api/overview/` trae en `total` (o en una clave nueva `matches_summary`)
      `matches_won`, `matches_lost`, `matches_decided` (con ganador) y
      `match_winrate` = ganadas / decididas; empates e incompletas
      (`Match.won` nulo) quedan fuera del denominador y se cuentan aparte
      (`matches_undecided`). Test con 3 ganadas, 1 perdida y 1 con `won=None`:
      75 %.
- [ ] Trae `rounds_per_match` = rondas importadas / partidas (un decimal),
      sobre las mismas partidas que cuentan los filtros. Test con partidas de 7 y 9
      rondas: 8.0.
- [ ] Trae `best_map` y `worst_map` (nombre, slug, partidas decididas y winrate
      de partida) entre los mapas con al menos la muestra minima de partidas que
      fije el diseno; con un solo mapa que la pase, el mismo mapa no sale como
      mejor y peor (el peor va `null`); sin ninguno, los dos `null`. Test con
      cada caso.
- [ ] Base vacia y filtros que no dejan partidas: 200, `match_winrate` y los
      mapas `null`, sin dividir por cero.
- [ ] El Inicio (`Dashboard.jsx`) muestra la fila nueva con textos en
      castellano ("Partidas ganadas", "Rondas por partida", "Mejor mapa", "Peor
      mapa"), y el e2e (`frontend/e2e/`) afirma que aparece con los numeros de
      `seed_demo`.
- [ ] Cada numero nuevo tiene fila en `docs/metricas.md`, con la muestra
      minima del mapa.

## Fuera de alcance

- "Partidas cerradas" (margen de 1 ronda): ya esta en Tendencias (ficha 50).
- Cambiar como se calcula `Match.won` o el empate que hoy se ve como
  "incompleta" (aviso de la ficha 54 en ESTADO.md): este item solo cuenta lo
  que `won` ya dice.
- Winrate de partida por lado, por operador o por compañero.

## Diseno

(Arquitecto 20261027T1605Z, sobre origin/dev 2532ed1.) Sin migracion, sin
recompute, sin parser. Ninguna rama de trabajo abierta: no pisa nada.

Skills: no aplica (fila de `Stat3` en el Inicio y un agregado por partida;
el repo ya resuelve los dos: `by_margin`, `by_stack`). Sin arena: una sola
forma obvia.

**Decisiones (para que el Dev no tenga que tomar ninguna):**

- Clave nueva `matches_summary` en el payload de `/api/overview/`, puesta en
  la **vista** (como `records`), no en `agg.overview`: `coach.py` llama a
  `agg.overview` y no la usa.
- Las partidas se eligen como en `by_margin`: `base_queryset(**filtros)`
  **sin `side`** (un lado no parte una partida) -> `round__match_id`
  distintos. Cada partida se lee entera.
- `matches` = esas partidas; `matches_won` = `won=True`; `matches_lost` =
  `won=False`; `matches_undecided` = `won` nulo (empates e incompletas, lo que
  `won` ya dice; no se toca `match_result`); `matches_decided` = ganadas +
  perdidas; `match_winrate` = `_pct(ganadas, decididas)` (None sin decididas).
- `rounds` = `RoundPlayer.objects.filter(is_me=True, round__match_id__in=ids).count()`
  (todas tus rondas de esas partidas, sin recortar por operador ni sitio, como
  `by_margin`); `rounds_per_match` = `_ratio(rounds, matches, 1)`.
- Mapas: se agrupa por `map_slug` (las variantes de temporada colapsan) sobre
  las partidas **decididas**; nombre = `map_name` de la partida mas reciente
  del slug. Entra un mapa con `MIN_PARTIDAS_MAPA = 3` partidas decididas o mas
  (constante nueva en `aggregates.py`, al lado de `MIN_PARTIDAS_HABITUAL`).
  Cada candidato: `{"map", "slug", "matches", "wins", "winrate"}`.
  `best_map` = el primero ordenando por `(-winrate, -matches, map)`;
  `worst_map` = el primero ordenando por `(winrate, -matches, map)`, **solo si
  su winrate es menor que el del mejor**; si no, `null`. Eso cubre el caso de
  un solo mapa y tambien el empate de todos (con `seed_demo` todos los mapas
  estan en 100 %: el peor va `null`, que es lo honesto).
- Sin partidas: `matches=0`, `rounds=0`, `rounds_per_match`, `match_winrate`,
  `best_map`, `worst_map` en `None`.

**Archivos:**

1. `backend/replays/analytics/aggregates.py`: `MIN_PARTIDAS_MAPA` y
   `def matches_summary(**filters) -> dict`, en la seccion de vistas despues
   de `by_margin`. Una query por partidas (`values("id","map_slug","map_name",
   "played_at","won")`), un `count()` de rondas; el agrupado por mapa en
   Python (son pocas partidas por mapa, como `by_margin`).
2. `backend/replays/views.py` (`overview`): `payload["matches_summary"] =
   agg.matches_summary(**filters)` con un comentario de una linea del por que
   va en la vista (el mismo de `records`).
3. `frontend/src/pages/Dashboard.jsx`: una segunda fila `.kpis` justo debajo
   de la primera, con cuatro `Stat3`:
   - "Partidas ganadas": `pct(s.match_winrate)`, sub `` `${s.matches_won} de
     ${s.matches_decided}` `` + `` ` · ${s.matches_undecided} sin resultado` ``
     solo si `matches_undecided > 0`; `value_={s.match_winrate}` (tono).
   - "Rondas por partida": `fmt(s.rounds_per_match, 1)`, sub `` `${s.rounds}
     rondas en ${s.matches} partidas` ``, `value_={null}`.
   - "Mejor mapa" y "Peor mapa": value = nombre o `'—'`; sub `` `${pct(m.winrate)}
     en ${m.matches} partidas` ``; sin mapa: sub "Ningún mapa con 3+ partidas"
     si los dos son null, "Ningún mapa por debajo" si solo falta el peor.
     `value_={null}` (el nombre no tiene tono).
   Si `overview.data.matches_summary` no viene, la fila no se pinta (no rompe
   con un backend viejo).
4. `backend/tests/test_resumen_partidas.py` (nuevo), con `factories`:
   - `test_partidas_ganadas_sobre_decididas` (3 ganadas, 1 perdida, 1 con
     `won=None` -> 75.0, decididas 4, sin resultado 1)
   - `test_rondas_por_partida` (partidas de 7 y 9 rondas -> 8.0)
   - `test_mejor_y_peor_mapa` (dos mapas con 3+ partidas y winrates distintos)
   - `test_mapa_bajo_la_muestra_no_cuenta` (un mapa con 2 partidas queda fuera)
   - `test_un_solo_mapa_no_es_mejor_y_peor` (peor `None`)
   - `test_mapas_empatados_no_tienen_peor` (peor `None`)
   - `test_variantes_del_mapa_cuentan_juntas` (mismo slug, dos `map_name`;
     el nombre es el de la mas reciente)
   - `test_el_lado_no_parte_la_partida` (`side="Defense"` no cambia nada)
   - `test_base_vacia_y_filtro_sin_partidas` (los dos por la API: 200, nulos,
     sin `ZeroDivisionError`)
   - `test_overview_trae_resumen_de_partidas` (la clave esta en el payload)
   `make_match` pone `won = my_score > opponent_score`: para `won=None` crear
   la partida y hacer `Match.objects.filter(pk=...).update(won=None)`.
5. `frontend/e2e/humo.spec.js`: test `el Resumen muestra tus partidas` en el
   estilo del de multikills: con `seed_demo` (29 partidas, todas ganadas 4-3,
   203 rondas; Bank 10, Border 9, Club House 10, todas al 100 %):
   - `.stat` "Partidas ganadas": value `100%`, sub `29 de 29`
   - "Rondas por partida": value `7.0`, sub `203 rondas en 29 partidas`
   - "Mejor mapa": value `Bank`, sub `100% en 10 partidas`
   - "Peor mapa": value `—`, sub `Ningún mapa por debajo`
   Para ubicar el `.stat` usar `.label` con `hasText: /^Partidas ganadas$/`
   (evita chocar con "Rondas ganadas").
6. `docs/metricas.md`, seccion `## Base`, filas nuevas despues de "Rondas
   ganadas (winrate)": **Partidas ganadas** (ganadas / decididas, sin `won`
   nulo, partidas elegidas por los filtros menos el lado), **Rondas por
   partida** (todas tus rondas de esas partidas / partidas) y **Mejor y peor
   mapa** (winrate de partida, 3+ partidas decididas, desempate por partidas y
   nombre, el peor solo si esta por debajo del mejor).

**Orden:** 1-2 con sus tests (4) -> `python manage.py test tests` -> 3 ->
`npm run build` -> 5 -> 6 -> `./scripts/check.sh`.

**Que puede romperse:** `test_api` que compare el payload de overview entero
(hoy no lo hace: solo mira claves). El e2e de multikills del Resumen sigue
igual (otra `.stat`). Con filtro `session`, `base_queryset` ya resuelve las
partidas de la sesion.

**Verificacion manual:** `seed_demo --force`, abrir `/`: la fila nueva bajo
los KPI; `/?map=bank`: "1 mapa" -> Mejor Bank, Peor "—"; `curl
'localhost:8000/api/overview/?since=2030-01-01'` -> `matches_summary` con
nulos.

**Calibrar con la base real:** `MIN_PARTIDAS_MAPA = 3` es bajo a proposito
(un mapa por semana alcanza); con la base real puede convenir 5.

## Implementacion

(Dev 20261027T2005Z, sobre origin/dev 2532ed1.)

Skills: no aplica (el Arquitecto ya lo descarto; nada fuera del repo).

Quedo todo el diseno, sin desvios de alcance:

- `aggregates.py`: `MIN_PARTIDAS_MAPA = 3` y `matches_summary(**filters)`
  despues de `by_margin`. Una query de partidas ordenada por fecha (asi el
  nombre del mapa queda el de la mas reciente) y un `count()` de rondas.
- `views.py` (`overview`): clave `matches_summary`, puesta en la vista.
- `Dashboard.jsx`: componente `ResumenPartidas`, una segunda fila `.kpis`
  bajo la primera con "Partidas ganadas", "Rondas por partida", "Mejor mapa"
  y "Peor mapa". Si el backend no trae la clave, no se pinta.
- `test_resumen_partidas.py`: 12 tests (los 10 del diseno mas
  `test_las_sin_resultado_no_llegan_a_la_muestra_del_mapa` y
  `test_los_filtros_eligen_las_partidas`).
- e2e `el Resumen muestra tus partidas` con los numeros de `seed_demo`
  (29 de 29, 7.0, 203 rondas en 29 partidas, Bank 100 % en 10, peor "—").
- `docs/metricas.md`: tres filas en `## Base` despues de "Rondas ganadas".

Desvios menores:

- El payload suma `min_matches_map` para que el texto "Ningún mapa con 3+
  partidas" no repita la constante en el frontend.
- "Rondas por partida" dice "1 partida" en singular (hallazgo de la revision
  ciega).

Revision ciega (subagente con `revision.md`): aprobar. Confirmo los numeros
del e2e contra `seed_demo` y que `won` sirve antes de Y9S4 (sale de
`teamscore`). Aviso no corregido: con `seed_demo` (todo ganado) el e2e no
ejercita un peor mapa con valor ni "· N sin resultado"; los dos casos los
cubren los tests de backend. Cambiar `seed_demo` moveria los numeros de
otros e2e.

Verificacion: `./scripts/check.sh` en `Todo en verde.` (800 tests backend,
120 frontend, build, 51 e2e).

## Revision 2026-10-28 sobre 19b6759

(Revisor 20261028T0004Z, sobre origin/dev 2532ed1; dev no se movio.)

Revision ciega (subagente con `revision.md`): un hallazgo, confirmado por
mutacion y corregido con un test (el Revisor puede empujar tests que pasan):

- [test] `test_el_lado_no_parte_la_partida` pasaba igual sin la linea que saca
  `side` de los filtros en `matches_summary` (`aggregates.py:924`): las dos
  partidas del fixture tienen rondas de defensa. Agregado
  `test_una_partida_sin_rondas_del_lado_filtrado_igual_cuenta` (una partida
  de una sola ronda de ataque; con `side="Defense"` sigue en `matches` y en
  `rounds`). Con la mutacion `filtros = dict(filters)` cae solo el test nuevo.

Criterios: los seis cubiertos. Ganadas/decididas 75 % con `won=None` aparte
(`test_partidas_ganadas_sobre_decididas`); 8.0 rondas por partida
(`test_rondas_por_partida`); mejor y peor mapa, muestra minima, un solo mapa,
empate (`test_mejor_y_peor_mapa`, `test_mapa_bajo_la_muestra_no_cuenta`,
`test_un_solo_mapa_no_es_mejor_y_peor`, `test_mapas_empatados_no_tienen_peor`);
base vacia y filtro sin partidas por la API (`test_base_vacia_y_filtro_sin_partidas`);
fila en el Inicio y e2e `el Resumen muestra tus partidas`; tres filas en
`docs/metricas.md` con la muestra de 3.

Reglas: el diff no sale de `archivos:`; sin dependencias ni escrituras
nuevas; identificadores sin tildes, UI con tildes; sin `print` ni
`console.log`. Mapas desconocidos no se mezclan (slug `unknown-<id>`).

Verificacion: `./scripts/check.sh` en `Todo en verde.` sobre 19b6759 (800 tests
backend, 120 frontend, build, 51 e2e) y suite backend con el test nuevo en
verde (801).

Veredicto: aprobar.

## QA 2026-10-28 sobre 1a24d91

(QA 20261028T0404Z, sobre origin/dev 2532ed1; dev no se movio.)

`./scripts/check.sh` en `Todo en verde.` antes (801 tests backend, 120
frontend, build, 51 e2e) y despues del test agregado (802).

Base sembrada con `factories` (script en el scratchpad, `SQLITE_PATH` y
`R6_ENV_FILE` aparte; nada al repo): Bank 3 ganadas + 1 perdida + 1 sin
resultado, Border 1 de 3, Club House 2 de 2, Oregon 4-4 (`won` nulo), Kafe
4-1 solo con rondas de ataque; 12 partidas, 70 rondas.
`python manage.py runserver 127.0.0.1:8077 --noreload`:

- Criterio 1: `curl localhost:8077/api/overview/` -> `matches 12, won 7,
  lost 3, decided 10, undecided 2, match_winrate 70.0`. 200.
- Criterio 2: `rounds 70, rounds_per_match 5.8` (70/12, sin resultado
  incluidas). `?map=border` -> 19 rondas en 3, 6.3.
- Criterio 3: mejor Bank 75 % en 4 (la sin resultado no entra a la
  muestra), peor Border 33.3 % en 3; Club House (2) y Kafe (1) fuera.
  `?map=bank` -> peor `null`; `?map=oregon` -> los dos `null`,
  `match_winrate null`, `rounds_per_match 8.0`.
- Criterio 4: base vacia (`migrate` sobre un `.sqlite3` nuevo, puerto
  8078): 200 y todo `null`/0 con y sin `?side=Attack`. Filtros sin
  partidas (`?map=nada`, `?since=2030-01-01`, `?operator=Ash`,
  `?session=foo`, `?site=nada`, `?match_type=Casual`): 200, nulos.
  `?side=Defense` y `?side=Attack` dan lo mismo que sin filtro (Kafe sigue
  en `matches`). `?until=foo`, `?since=foo`, `?page=-1`, `?session=0`: 200,
  se ignoran como en el resto de la API.
- Criterio 5: Chromium (playwright) sobre el build: la fila aparece bajo los
  KPI con "Partidas ganadas 70 % · 7 de 10 · 2 sin resultado", "Rondas por
  partida 5.8 · 70 rondas en 12 partidas", "Mejor mapa Bank · 75% en 4
  partidas", "Peor mapa Border · 33% en 3 partidas". Selector Mapa = Bank ->
  peor "— · Ningún mapa por debajo"; Club House -> "Ningún mapa con 3+
  partidas" en los dos; Oregon -> "— · 0 de 0 · 1 sin resultado" y "8 rondas
  en 1 partida" (singular). A 390 px sin scroll horizontal. Consola limpia.
  Base vacia: pantalla de bienvenida, sin errores. El e2e `el Resumen
  muestra tus partidas` pasa dentro de `check.sh`.
- Criterio 6: tres filas en `docs/metricas.md` `## Base` con la muestra de 3.
- Bundle: chunk inicial `index-*.js` 187.83 kB en dev -> 188.72 kB (+0.5 %).

Mutacion sobre `matches_summary`: sacar el `continue` de las sin resultado
(cae `test_las_sin_resultado_no_llegan_a_la_muestra_del_mapa`); `>=` por `>`
en el peor (caen 3); muestra `>` en vez de `>=` (caen 3); winrate sobre
todas las partidas (cae `test_partidas_ganadas_sobre_decididas`).
**Sobrevivia** `rounds_per_match` dividido por las decididas: ningun test
mezclaba partidas sin resultado con rondas por partida. Agregado
`test_las_sin_resultado_cuentan_en_rondas_por_partida` (6 + 9 rondas, una
sin resultado -> 7.5); con la mutacion cae solo ese.

Fuera de la ficha (preexistente en dev, no bloquea): el Inicio no lee los
filtros de la URL (`/?map=bank` muestra todo); el filtro se aplica con el
selector.

Sin migracion, sin `recompute`, sin parser: no hay `## Verificar en el PC`.

Veredicto: aprobado.

## Para el humano

- Calibrar con la base real: `MIN_PARTIDAS_MAPA = 3` (aviso del
  Arquitecto); probado solo con datos sinteticos.
