# 64. Partidas en el Inicio: ganadas, rondas por partida y mejor y peor mapa

estado: disenado
candado: -
rama: -
tipo: funcionalidad
epica: paridad-referencia
area: fullstack
prioridad: 3
fuente: ALCANCE.md R1 (replica/features.csv fila 11, must, clone partial; [aurelix](https://aurelix.app/))
archivos: backend/replays/analytics/aggregates.py, backend/replays/views.py, frontend/src/pages/Dashboard.jsx, backend/tests/test_resumen_partidas.py, frontend/e2e/humo.spec.js, docs/metricas.md
turnos: po 20261027T1205Z, arquitecto 20261027T1605Z

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

## Para el humano

(Nada por ahora.)
