# 120. Puesto en el lobby

estado: aprobado
candado: -
rama: claude/equipo-dev/120-puesto-en-el-lobby
tipo: funcionalidad
epica: progreso
area: fullstack
prioridad: 3
fuente: ALCANCE.md E7
archivos: backend/replays/analytics/aggregates.py (lobby_rank), backend/replays/views.py (trends), backend/tests/test_puesto_en_el_lobby.py (nuevo), frontend/src/puestoLobby.js (nuevo), frontend/src/puestoLobby.test.js (nuevo), frontend/src/pages/Trends.jsx (panel Puesto en el lobby), frontend/e2e/humo.spec.js, docs/metricas.md
turnos: po 20261113T1603Z-cHj1H4k, arquitecto 20261113T1733Z-cudo1Sw, dev 20261113T1802Z-c8dAf7p, revisor 20261113T1830Z-c2rHpej, qa 20261113T1858Z-cxQ3TuB

## PR

## Que gana quien usa la app

En Tendencias, cuantas veces fuiste el mejor de la partida por Rating, el
mejor de tu equipo y el ultimo de los diez: el Rating suelto no dice si
arrastraste al equipo o te arrastraron. Solo sale de tus replays, que traen
a los diez jugadores.

## Criterios de aceptacion

- [ ] Un agregado nuevo en `aggregates.py` calcula, por partida, tu puesto
      entre los jugadores de la partida y dentro de tu equipo por el rating
      de la partida (`rating_points_expr` sobre las filas `RoundPlayer` de
      todos, como `trend_by_match`), y devuelve `matches`, `best_in_lobby`,
      `best_in_team` y `last_in_lobby` (conteo y %). Test con una partida
      armada de 10 jugadores de rating conocido.
- [ ] Empate de rating con otro jugador: cuenta como mejor (o ultimo) solo
      si nadie te supera (o nadie esta por debajo); regla en
      `docs/metricas.md` y test.
- [ ] Partidas con menos de 10 jugadores (abandonos) entran con los que hay;
      una partida en la que solo estas vos no cuenta. Test.
- [ ] Los filtros globales de partida (mapa, tipo, modo, fechas) aplican;
      los de ronda (lado, operador, sitio) recortan las rondas de todos por
      igual. Test con filtro de mapa.
- [ ] En Tendencias, una fila de tres stats (Mejor de la partida, Mejor de
      tu equipo, Último de la partida) con el % y el conteo; sin partidas,
      un texto y no ceros. e2e de humo con los numeros de `seed_demo` y la
      consola limpia.
- [ ] Fila nueva en `docs/metricas.md` ("Puesto en el lobby").

## Fuera de alcance

- El puesto en el detalle de cada partida (otro tramo, chico, despues de este).
- Comparar contra el promedio del lobby (E9, otra idea).
- Puesto por score de la partida: el `.rec` ya no lo atribuye.

## Diseno

Arquitecto 20261113T1733Z-cudo1Sw, sobre `origin/dev@7892cc3`. Una forma obvia
(sin arena ni consenso): sin migracion, sin `recompute`, sin parser, sin ruta
nueva. Filtros duros: pasa (los diez jugadores ya estan en `RoundPlayer` con
las columnas del rating; sin red, sin dependencias).

**Decision: se calcula al consultar, con `rating_points_expr` sobre las filas de
todos**, como `trend_by_match` lo hace sobre las tuyas. Guardar el puesto al
importar pediria migracion y lo dejaria detras de la 79. El rating de cada
jugador en la partida es el promedio de sus puntos por ronda en las rondas
filtradas; dividir por `rating_baseline()` no cambia el orden, asi que se
ordena por los puntos y no se divide.

### Archivos y por que

1. `backend/replays/analytics/aggregates.py`: `lobby_rank(**filters) -> dict`,
   despues de `trend_by_match` (es el mismo dato, partido por jugador).
   - `mias = base_queryset(**filters)`: las rondas que dejan los filtros, de
     partida y de ronda (los de ronda recortan las rondas de todos por igual).
   - Lobby: `RoundPlayer.objects.filter(Exists(mias.filter(round_id=OuterRef("round_id"))))
     .values("round__match_id", "player_id").annotate(points=Avg(rating_points_expr()), rounds=Count("id"))`.
     Correlacionada, sin `round_id__in` (tope de SQLite), como `teammate_synergy`.
   - Compañeros: la misma base con `is_me=False` y un `Exists` sobre
     `mias.filter(round_id=OuterRef("round_id"), team_index=OuterRef("team_index"))`,
     solo `values_list("round__match_id", "player_id").distinct()` a un set:
     compañero = estuvo en tu equipo en alguna ronda filtrada de esa partida.
   - Vos: `set(Player.objects.filter(is_me=True).values_list("id", flat=True))`.
     Si en una partida hubiera dos jugadores `is_me`, se toma el de mas rondas
     filtradas y el otro cuenta como uno mas del lobby (el import no lo produce
     hoy; basta con que no rompa).
   - Por partida con vos y al menos otro jugador: *mejor de la partida* si ningun
     otro tiene `points` mayor que los tuyos (empate cuenta como mejor);
     *ultimo de la partida* si ningun otro tiene `points` menor (empate cuenta;
     con dos empatados sos mejor y ultimo a la vez). *Mejor de tu equipo* solo
     en las partidas con al menos un compañero, si ninguno tiene `points`
     mayor. Partida con solo vos: no entra en ninguno. Comparar con tolerancia
     `1e-9` (promedios en float de SQLite: dos iguales no se desempatan por
     redondeo).
   - Salida: `{"best_in_lobby": caso, "best_in_team": caso, "last_in_lobby": caso}`
     con `caso = {"count": c, "matches": n, "pct": _pct(c, n)}`; `matches` del
     lobby es el mismo en sus dos casos (partidas con otro jugador), el del
     equipo son las partidas con compañero.
2. `backend/replays/views.py`: clave `"lobby_rank": agg.lobby_rank(**filters)`
   al final del dict de `trends`. Sin ruta nueva: la guardia de la 79
   (`test_toda_ruta_esta_clasificada`) no cambia, `trends` ya esta en sus
   `COMPARADAS` y la exclusion le llega sola por `base_queryset`.
3. `frontend/src/puestoLobby.js` (logica pura, vitest): `statsDePuesto(data)`
   -> `[]` sin `data` o con `best_in_lobby.matches` 0; si no, tres filas en este
   orden: `best_in_lobby` "Mejor de la partida", `best_in_team` "Mejor de tu
   equipo", `last_in_lobby` "Último de la partida"; cada una `{key, label, pct,
   sub}` con `sub` = `"<count> de <matches> partidas"`. `avisoPuesto(data)`:
   `"Pocas partidas: con menos de 10 el porcentaje se mueve mucho por azar."`
   si `best_in_lobby.matches < MUESTRA_PARTIDAS` (de `margen.js`), si no `null`.
4. `frontend/src/pages/Trends.jsx`: `Panel` "Puesto en el lobby" justo despues
   del panel "Por partida", hint "Tu rating en cada partida contra el de los
   demás jugadores, y contra tus compañeros. Empatar con el mejor cuenta como
   ser el mejor.", y una `div className="kpis"` con un `Stat` de `ui.jsx` por
   fila (`value={pct(fila.pct)}`, `sub={fila.sub}`), sin `tone`: un puesto no
   es bueno o malo sin el resto. Sin filas: `<p className="note">No hay
   partidas con otros jugadores con estos filtros.</p>`. El aviso, como `note`
   debajo.
5. `frontend/e2e/humo.spec.js`: test `Tendencias muestra el puesto en el lobby`:
   leer `/api/trends/`, `expect(lobby_rank.best_in_lobby.matches).toBeGreaterThan(0)`,
   y en el panel los tres label y el `sub` de `best_in_lobby` armado con los
   numeros de la API (no a mano). Consola limpia (`vigilarConsola`).
6. `docs/metricas.md`: fila en `## Progreso` (texto abajo) y en
   `## Muestra minima` ("Puesto en el lobby | 10 partidas: no se oculta, se avisa").

### Tests (`backend/tests/test_puesto_en_el_lobby.py`, con `factories`)

Partidas armadas (5 por `team_index` salvo donde se dice) con `kills`, `died`,
`opening_*` elegidos para un orden de puntos conocido.
- `test_mejor_de_la_partida_y_de_tu_equipo`: vos arriba de los nueve.
- `test_mejor_de_tu_equipo_sin_ser_mejor_de_la_partida`: solo un rival te supera.
- `test_ultimo_de_la_partida`: todos te superan.
- `test_empatar_con_el_mejor_cuenta_como_mejor`.
- `test_partida_con_menos_de_diez_entra_con_los_que_hay`: vos, un compañero y un rival.
- `test_partida_solo_con_vos_no_cuenta`: `matches` 0 y `pct` None en los tres.
- `test_sin_companeros_no_entra_en_mejor_de_tu_equipo`: vos y un rival.
- `test_filtro_de_mapa_aplica`: dos partidas en mapas distintos.
- `test_filtro_de_lado_recorta_las_rondas_de_todos`: en ataque ganas, en
  defensa un rival te supera por mucho; `side=Attack` te deja mejor, sin filtro no.
- `test_consultas_acotadas`: `assertNumQueries` fijo con dos partidas y el mismo con cinco.
- `test_trends_trae_lobby_rank`: base vacia, la clave con los tres casos en 0.

vitest `puestoLobby.test.js`: tres filas en orden con label y sub; `[]` sin
datos y con `matches` 0; aviso con 9 partidas y sin aviso con 10.

### Orden

aggregates + tests -> clave en `trends` + test -> `puestoLobby.js` + vitest ->
panel en Trends -> humo -> `metricas.md` -> `verificar.sh`.

### Que puede romperse

- Rendimiento: una consulta agrupada sobre las filas de todos en tus rondas
  filtradas (10 por ronda), la escala de `teammate_synergy`.
- Archivos de otras ramas: la 119 (`en curso`) toca `Trends.jsx` en la tabla
  Sesiones y `humo.spec.js`; la 79 toca `aggregates.py` (`base_queryset`) y
  `views.py` (ruta nueva). Zonas distintas: hunks separados, P3 si aparece
  algo; no se frena (mismo criterio que la 116 y la 121). `metricas.md` lo
  tocan todas, cada una con su fila.

### Verificacion manual

`seed_demo`, `runserver`, `curl -s localhost:8000/api/trends/` y mirar
`lobby_rank`; abrir `/tendencias`, panel despues de "Por partida"; con
`?map=<slug>` cambian los numeros; con un filtro sin partidas, la vista vacia
de siempre.

### Fila de `docs/metricas.md` (## Progreso)

| **Puesto en el lobby** | Panel de Tendencias (`lobby_rank` en `/api/trends/`). En cada partida, el rating de cada jugador es el promedio de sus puntos por ronda (los de **Rating**) en las rondas que dejan los filtros; los de ronda (lado, operador, sitio) recortan las mismas rondas para todos. *Mejor de la partida*: ningun otro jugador tiene mas; *Último de la partida*: ninguno tiene menos; empatar cuenta (con dos empatados sos mejor y ultimo). *Mejor de tu equipo*: ningun compañero (estuvo en tu equipo en alguna de esas rondas) tiene mas. Porcentaje sobre las partidas con al menos otro jugador (con al menos un compañero, en el de equipo); una partida con solo tu fila no cuenta. Partidas con menos de 10 jugadores entran con los que hay. Muestra minima 10 partidas: no se oculta, se avisa. |

Skills del repo: statistical-analysis (cada porcentaje con su `n` propio y a la
vista; empates definidos; el porcentaje es un conteo de partidas, no un
promedio de promedios), testing-strategy (Django para el agregado y la clave de
`trends`, vitest para las filas y el aviso, humo e2e para el panel). dataviz no
aplica: tres stats, sin grafico.
Skills: no aplica (sin tabla, migracion ni flujo e2e nuevos).
OMC: plan=— · revisión=— · verificación=—

## Implementacion

(dev 20261113T1802Z-c8dAf7p) Diseno completo, sobre `origin/dev@1de3c54`:

- `aggregates.py`: `lobby_rank(**filters)` despues de `trend_by_match`. Una
  consulta agrupada por partida y jugador sobre las rondas que dejan los
  filtros (`Exists` correlacionado con `base_queryset`, sin `IN`), con
  `Avg(rating_points_expr())`; otra con los compañeros (mismo `team_index`
  en alguna de esas rondas). Mejor/ultimo con tolerancia `EMPATE_RATING`
  (`1e-9`); salida `{count, matches, pct}` por caso. 2 consultas fijas.
- `views.py`: `"lobby_rank"` al final de `trends`.
- `puestoLobby.js`: `statsDePuesto` (tres filas en orden; `[]` sin partidas
  con otro jugador; "partida" en singular con 1) y `avisoPuesto` (menos de
  `MUESTRA_PARTIDAS`).
- `Trends.jsx`: panel "Puesto en el lobby" despues de "Por partida", tres
  `Stat` sin `tone`, nota sin partidas y aviso de muestra.
- `metricas.md`: fila en `## Progreso` (texto del diseno) y en
  `## Muestra minima`.

Desvio del diseno (revision ciega, MEDIUM, corregido): el diseno tomaba "vos"
de `Player.is_me`; `base_queryset` usa `RoundPlayer.is_me`, y las dos pueden
no coincidir (import sin `recordingProfileID` deja el `Player` sin marcar;
un compañero que grabo replays queda marcado). Ahora tu fila es la que tiene
rondas `is_me=True` en la partida (`mine` en la misma consulta), y sobra la
consulta de `Player`. Test `test_tu_fila_sale_de_la_ronda_y_no_de_la_marca_del_jugador`
(cae sin el arreglo). LOW corregido: el aviso interpola `MUESTRA_PARTIDAS`.

Tests vistos en rojo antes del codigo: backend (13 con `AttributeError:
lobby_rank`), vitest (`puestoLobby.js` inexistente); despues, el de la
marca y `assertNumQueries(2)`. Criterios -> tests: agregado con 10
jugadores (`test_mejor_de_la_partida_y_de_tu_equipo`,
`..._sin_ser_mejor_de_la_partida`, `test_ultimo_de_la_partida`); empates
(`test_empatar_con_el_mejor_cuenta_como_mejor`,
`test_empatar_con_todos_es_mejor_y_ultimo`); menos de 10 y solo vos
(`test_partida_con_menos_de_diez_entra_con_los_que_hay`,
`test_partida_solo_con_vos_no_cuenta`,
`test_sin_companeros_no_entra_en_mejor_de_tu_equipo`); filtros
(`test_filtro_de_mapa_aplica`, `test_filtro_de_lado_recorta_las_rondas_de_todos`);
consultas (`test_consultas_acotadas`); clave en la API
(`test_trends_trae_lobby_rank`); UI: vitest (7) + e2e `Tendencias muestra
el puesto en el lobby` (etiquetas y `sub` armado con la API, consola
limpia); fila en `metricas.md`.

verificar.sh: VERDE 8571ad34c (1253 backend, 384 vitest, 104 e2e).

Skills: no aplica.
Skills del repo: statistical-analysis (cada % con su `n` a la vista, empate definido, conteo de partidas y no promedio de promedios), testing-strategy (Django, vitest, e2e como dice el diseno), ux-copy (etiquetas y nota del diseno, con tildes), modern-web-guidance no leida (un `Panel` y `Stat` que ya existen, sin CSS nuevo), sql-queries (patron vecino de `teammate_synergy`; `assertNumQueries(2)` fijo con 2 y 5 partidas).
OMC: plan=— · revisión=4 hallazgos (1 MEDIUM, 3 LOW; 3 arreglados, 1 cubierto con test) · verificación=—

## Revision 2026-11-13 sobre dc941a9

(revisor 20261113T1830Z-c2rHpej) Punto de partida: la rama chocaba con `origin/dev` (1de3c54..72fad68,
la 119 mergeada) en el import de `resumenSesion.js` en `Trends.jsx`; resuelto
(P3) juntando los dos imports, merge dc941a9. `verificar.sh`: VERDE dc941a9b0
(1253 backend, 387 vitest, 105 e2e).

**Eje de estandares** (`omc-code-reviewer`, prompt de `revision.md`, 438 lineas
de diff): aprobar, 1 LOW **confirmado leyendo el codigo**:
- L1 [estilo, LOW] `aggregates.py:2135` y `test_puesto_en_el_lobby.py:116`: dos
  comentarios dicen "compañero" con ñ; `CLAUDE.md` pide comentarios sin tildes
  (el resto del archivo escribe "companeros"). Arreglo: "companero". No bloquea.
Verifico ademas: bordes (partida de un jugador, sin compañeros, empates con
`EMPATE_RATING`, ronda sin bajas sin NULL), tu fila desde `RoundPlayer.is_me`
con test que cae sin el arreglo, 2 consultas fijas (`assertNumQueries`), sin
dependencias ni escritura nueva, nada que el `.rec` no traiga.

**Eje de intencion** (`omc-code-reviewer`, contra Que gana, Criterios y Fuera de
alcance): los 6 criterios cumplidos, nada fuera de alcance; aprobar. 2 LOW que no
reporto como hallazgo: `matches` va dentro de cada caso (el de equipo cuenta
partidas con compañero, distinto del de lobby, y `metricas.md` lo dice: es el
diseno) y el e2e toma los numeros de la API (decision del diseno: sigue al seed).

**Ficha.** Criterio 1: `test_mejor_de_la_partida_y_de_tu_equipo` (10 jugadores);
2: `test_empatar_con_el_mejor_cuenta_como_mejor` + fila de `metricas.md`; 3:
`test_partida_con_menos_de_diez...`, `test_partida_solo_con_vos_no_cuenta`; 4:
`test_filtro_de_mapa_aplica`, `test_filtro_de_lado_recorta...`; 5: vitest
`puestoLobby.test.js` + e2e `Tendencias muestra el puesto en el lobby`; 6: filas
en `## Progreso` y `## Muestra minima`. Diff dentro de `archivos:`; UI con tildes;
sin `print` ni `console.log`.

Veredicto: aprobar.

Skills del repo: ninguna (revision con `revision.md`).
OMC: plan=— · revisión=3 hallazgos LOW (0 arreglados: 1 al humano, 2 decisiones del diseno) · verificación=—



## QA 2026-11-13 sobre aec18f7

(qa 20261113T1858Z-cxQ3TuB) Rama fusionada con `origin/dev@ed7bb52` (la 121 mergeada) sin
conflictos, merge aec18f7. Script de siembra y de accesibilidad en el
scratchpad (`sembrar.py`, `a11y.js`); sin `.rec` ni `.sqlite3` en el repo.

- **check.sh**: `verificar.sh` -> `VERDE aec18f7fe en 196s: 1253 tests backend, 395 vitest, 106 e2e. Todo en verde.`
- **Base vacia** (`SQLITE_PATH=<tmp>/vacia.sqlite3 manage.py migrate`, `runserver 8761`):
  `curl -s localhost:8761/api/trends/` -> `lobby_rank` con `count 0, matches 0, pct None` en los tres; `/tendencias` muestra el vacio de la pagina, consola limpia.
- **Base sembrada** (`manage.py shell < sembrar.py` con `factories`): 0 Club House vos mejor de 10;
  1 Border vos ultimo de 10; 2 Club House vos + un rival que te supera, sin compañeros;
  3 Oregon solo vos; 4 Border empatas con un rival el mejor; 5 Bank vos = compañero,
  dos rivales con el mismo nick "Repetido" (profiles distintos, 2 y 0 kills).
  Recalculado a mano: lobby 5 partidas (la 3 no entra), mejor 2 (0 y 4) = 40 %,
  ultimo 2 (1 y 2) = 40 %, equipo 4 partidas (0, 1, 4, 5), mejor de tu equipo 3
  (0, 4, 5) = 75 %. API: `best_in_lobby (2,5,40.0)`, `best_in_team (3,4,75.0)`,
  `last_in_lobby (2,5,40.0)`: igual. El nick repetido cuenta como dos jugadores
  (si se juntaran, empatarias con el mejor y el peor de la 5).
- **Filtros y bordes** (`curl "localhost:8762/api/trends/?<q>"`, todos 200):
  `map=club-house` -> (1,2,50) (1,1,100) (1,2,50) y `map=border` -> (1,2,50) x3,
  los dos iguales a mano; `map=oregon`, `map=nada`, `side=Defense`,
  `since=2030-01-01`, `operator=Ash`, `match_type=Casual` -> ceros con `pct None`;
  `until=foo`, `page=-1`, `map=` -> sin filtro (como el resto de `trends`).
- **Bundle**: chunk inicial `index-*.js` 200116 bytes en dev y en la rama (0 %);
  `Trends-*.js` 33030 -> 34185 (+3,5 %).
- **accessibility-review** (Playwright sobre la base sembrada): `heading "Puesto en el lobby" [level=2]`,
  hint, aviso y nota como `paragraph`; contraste medido h2 5.71, hint 5.71, label
  5.21, valor 12.92, sub 5.21, nota 5.71 (todos >= 4.5:1, WCAG 1.4.3); el panel no
  agrega controles y Tab recorre la pagina sin trampas; consola limpia. Con
  `?map=oregon`, "No hay partidas con otros jugadores con estos filtros.". Sin
  Critical ni Major. Menor ya existente: las `kpis` de `Stat` no son lista (patron
  de toda la app; no es de esta ficha).
- **design-critique**: tres stats sin tono, con su `n` en el sub, despues de "Por
  partida": legible; nada que llevar a `ALCANCE.md`.
- **validate-data** sobre la fila de `metricas.md` (367 y 418): division por cero
  -> `pct None` y la UI muestra la nota; no hay promedio de promedios en el
  porcentaje (conteo de partidas); cada tasa con su `n` propio a la vista;
  redondeo: API 1 decimal, UI `pct` sin decimales.
- **Mutacion** (`manage.py test tests.test_puesto_en_el_lobby`, codigo restaurado,
  `git status` limpio): empate estricto (`<` sin tolerancia) -> caen 2 tests de
  empate; compañero sin `team_index` -> caen 6; quitar `if not otros: continue` ->
  cae `test_partida_solo_con_vos_no_cuenta`.
- **omc-verifier**: PASS, confianza alta, 6/6 criterios VERIFIED; gap LOW: los dos
  comentarios con ñ que ya anoto el revisor.

Sin migracion, `recompute`, parser, Electron ni `.ps1`: nada para verificar en el PC.

Veredicto: aprobado.

Skills del repo: accessibility-review (sin Critical/Major; contrastes 5.21 a 12.92), design-critique (sin hallazgos), validate-data (2 valores recalculados a mano por filtro + total, iguales a la API), testing-strategy (mutacion 3/3 detectadas).
OMC: plan=— · revisión=— · verificación=PASS

## Para el humano

- (revisor 2026-11-13, no bloquea) Dos comentarios con "compañero" (ñ) en `aggregates.py:2135` y `test_puesto_en_el_lobby.py:116`; `CLAUDE.md` los quiere sin tildes. Lo puede corregir el Release al entregar o un Dev despues.

(nada)
