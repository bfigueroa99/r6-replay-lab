# 54. Solo, en duo o en stack

estado: en curso
candado: -
rama: claude/equipo-dev/54-solo-duo-o-stack
tipo: funcionalidad
epica: escuadra
area: fullstack
prioridad: 3
fuente: ALCANCE.md C5 (historial acumulado: la app es la unica que ve con quien jugaste cada partida)
archivos: backend/replays/analytics/aggregates.py, backend/replays/views.py, backend/tests/test_grupo.py, backend/tests/test_api.py, frontend/src/grupo.js, frontend/src/grupo.test.js, frontend/src/pages/Teammates.jsx, frontend/e2e/humo.spec.js, docs/metricas.md
turnos: po 20261017T1204Z, arquitecto 20261017T1603Z

## PR

(La escribe el Release manager al final.)

## Que gana quien usa la app

En Compañeros, tu winrate de partida y de ronda y tu rating segun cuantos
compañeros habituales jugaron esa partida con vos: solo (0), en duo (1),
con dos (2) o en stack de tres o mas. Responde si te conviene entrar solo o
esperar a tu grupo; `teammate_synergy` hoy lo mira de a un compañero.

## Criterios de aceptacion

- [ ] Habitual = un `Player` (no `is_me`) que estuvo en tu equipo
      (`team_index` igual al tuyo en la misma ronda) en 5 o mas partidas
      distintas de todo tu historial, sin aplicar los filtros de la consulta
      (asi un filtro de mapa no cambia quien es habitual). El 5 es una
      constante del modulo, sin ajuste en la UI.
- [ ] `/api/teammates/` (`views.teammates`) trae la clave
      nueva `by_stack`: filas `solo`, `duo`, `trio` y `stack` (3 o mas
      habituales), cada una con `matches`, `matches_won`, `match_winrate`,
      `rounds`, `rounds_won`, `winrate` y `rating`. Una partida cuenta en
      una sola fila, por los habituales distintos que aparecen en tu equipo
      en cualquiera de sus rondas.
- [ ] Partida sin resultado (`Match.result` vacio o empate) cuenta en
      `matches` y en las rondas, no en `match_winrate`. Test con una partida
      de cada fila, un empate y un cambio de nick de un habitual (sigue
      siendo el mismo `Player`).
- [ ] Los filtros de siempre recortan que partidas y rondas entran; con base
      vacia o sin habituales, `by_stack` existe con las cuatro filas y todo
      en `solo` o en 0.
- [ ] Compañeros muestra el panel "Solo, en duo o en stack" con las cuatro
      filas; el e2e lo encuentra con datos de `seed_demo` y la consola queda
      limpia.
- [ ] `docs/metricas.md` tiene la fila **Tamaño del grupo** con la
      definicion de habitual y el aviso de que el umbral se mide sobre todo
      el historial.

## Fuera de alcance

- Winrate por grupo exacto de compañeros (C1).
- Umbral de habitual configurable.
- Lado (C10) o mapa por tamaño de grupo.

## Diseno

(Arquitecto 20261017T1603Z, sobre main 9e3d660)

**Filtros duros de CLAUDE.md: pasan todos.** No toca `pydissect/` ni `externo/`, no sale
a la red, sin dependencias nuevas, `views.teammates` sigue siendo GET plano con
`JsonResponse`. No usa coordenadas, armas ni MMR: solo `RoundPlayer.team_index`,
`player_id` y `Match.won`. Sobre "las metricas se calculan al importar": esto es
agregacion, no metrica de ronda. Que alguien sea habitual depende de **todo** el
historial y cambia con cada import, asi que guardarlo en `RoundPlayer` obligaria a
recomputar la base entera en cada importacion; va en `aggregates.py` como agrupacion,
igual que `teammate_synergy`. Sin migracion ni `recompute`.

**Premisas verificadas**

- *Companero = `team_index` igual al tuyo en la misma ronda.* Cierto, y es lo que ya
  hace `teammate_synergy` (`aggregates.py:921-955`): `Exists` correlacionado sobre tu
  `RoundPlayer` con el mismo `round_id` y `team_index`, filas `is_me=False`. `team_index`
  es el equipo, no el lado: no se da vuelta entre mitades (comentario en
  `_partidas_compartidas`, `aggregates.py:1902-1903`). Un jugador que entro por abandono
  en el otro equipo solo cuenta en las rondas que estuvo en el tuyo.
- *Identidad con cambio de nick.* Cierto: `Player` se identifica por `profile_id`
  (`models.py:23-27`); el nick por ronda vive en `RoundPlayer.username`. Agrupar por
  `player_id` basta (mismo criterio que `test_un_cambio_de_nick_no_parte_la_fila`,
  `test_aggregates.py:175`).
- *"is_me" puede variar.* Hay dos: `RoundPlayer.is_me` (por ronda, por `profileID` del
  grabador, `ingest.py:235-237`) y `Player.is_me` (puede ser mas de uno: `_me_ids()`
  devuelve lista si grabaste con dos cuentas). Se usa `RoundPlayer.is_me=False`, igual
  que `teammate_synergy`: si una cuenta tuya la jugo otra persona en tu equipo, es un
  companero de verdad en esa partida. Se deja asi para que Sinergia y este panel no
  discrepen sobre quien es companero.
- *`Match.result` vacio o empate.* **Premisa falsa en la forma.** `result` es un
  `@property` (`models.py:79-81`), nunca vacio. La ingesta pone `won=None` cuando
  `my_score == opponent_score` (`ingest.py:169`) y tambien en partidas incompletas, y
  `match_result` mira `won is None` antes que el empate (`models.py:13-20`), asi que la
  rama `"empate"` es inalcanzable: un empate se muestra como "incompleta" en toda la
  app (bug latente, fuera de esta ficha; aviso al PO). No hay campo de empate. El
  criterio se implementa como **`Match.won is None`** = sin resultado: cuenta en
  `matches` y en las rondas, no en `match_winrate`. Ojo en tests: `make_match` calcula
  `won = my_score > opponent_score` (`factories.py:49`), o sea un 3-3 queda `False`; hay
  que hacer `Match.objects.filter(pk=m.pk).update(won=None)` como ya hacen
  `test_remontadas.py:129` y `test_margen.py:84`. No se toca la factory.
- *Minimo de `teammate_synergy`.* No hay constante de partidas que reusar:
  `teammate_synergy` corta por **rondas** filtradas (`min_rounds=10`, ajustable desde
  la UI con el selector "Muestra minima", `views.py:250`). Habitual mide otra cosa
  (partidas distintas, sin filtros), asi que entra una constante nueva
  `MIN_PARTIDAS_HABITUAL = 5`. Es coherente: 5 partidas son 30+ rondas en la practica,
  asi que todo habitual aparece en Sinergia con el minimo por defecto sin filtros; lo
  inverso no (dos partidas largas juntas dan 14 rondas y no hacen habitual). Se
  documenta la diferencia en metricas.md.
- *Filtros en teammates.* `views._filters` (`views.py:57`) arma el dict y
  `base_queryset` (`aggregates.py:44`) lo aplica sobre tus `RoundPlayer`. `side`,
  `operator` y `site` recortan rondas; `map`, `match_type`, `ranked_only`, fechas y
  `session` recortan partidas enteras. `min_rounds` no aplica a `by_stack`.

**Decision sobre filtros (criterio 4, definido aca).** Tres cosas distintas:

1. *Quien es habitual*: todo el historial, sin filtros (criterio 1).
2. *En que fila cae una partida*: los habituales distintos que estuvieron en tu
   equipo en **cualquier ronda de la partida**, sin filtros. El grupo es un dato de la
   partida, no de la ronda. Medido sobre seed_demo: si se calculara solo con las rondas
   filtradas, `side=Attack` partiria las 29 partidas en 15 stack + 14 trio (en ataque
   de la mitad de las partidas falta Nico) aunque jugaste con los mismos tres; eso es
   leer el filtro como si cambiara con quien jugaste.
3. *Que entra en cada fila*: partidas con al menos una ronda tuya que pase los filtros
   (`matches`), sus rondas filtradas (`rounds`, `rounds_won`, `winrate`, `rating`), y
   el resultado **entero** de esas partidas (`matches_won`, `match_winrate`). Con
   `side=Attack`, la partida cuenta como ganada si la ganaste, aunque se lean solo sus
   rondas de ataque: es lo mismo que hace `by_start_side` (`aggregates.py:863`). No se
   ignora `side` como en `by_margin` porque aca las rondas si se recortan.

**Nombres de filas.** Coherentes: `solo` = 0 habituales (vos), `duo` = 1 (vos + 1),
`trio` = 2 (vos + 2), `stack` = 3 o mas (vos + 3 o 4; puede pasar de 3 si un habitual
entro por abandono). En la UI: "Solo", "Dúo", "Trío", "Stack" y una columna
"Habituales" con 0, 1, 2 y "3 o más", para que nadie lea "stack" como 5-stack.

**seed_demo (corrido contra una base temporal, `SQLITE_PATH` en el scratchpad).** 29
partidas de 7 rondas (Club House 10, Border 9, Bank 10), 203 rondas tuyas. Chamo y Seba
juegan todas las rondas; Nico las de `indice` par; Pauli ninguna. Como cada partida tiene
7 rondas consecutivas, los tres aparecen en las 29: los tres son habituales con 29
partidas y **las 29 caen en `stack`**. Resultado sin filtros: solo/duo/trio en 0 (rating
y winrates `None`); stack 29 partidas, 29 ganadas, 100 %, 203 rondas, 116 ganadas,
57.1 %, rating 1.00. Con `side=Attack`: stack 29 partidas, 100 %, 116 rondas, 116
ganadas, 100 %, rating 1.05. Con `map=bank`: stack 10 partidas, 70 rondas, 57.1 %,
rating 1.04. El umbral de 5 no se puede calibrar con el seed (cualquier valor de 1 a 29
da lo mismo) y no hay base real en esta maquina. Unica pista: el roadmap (item 7) cita
al companero habitual del usuario con 133 de 151 rondas, asi que en datos reales no se
espera "todo en solo". Se deja 5. **No se toca `seed_demo`**: darle partidas solo/duo
cambiaria los 203 / 53 que afirman otros e2e; el e2e afirma las filas vacias y la de stack.

**Archivos**

- `backend/replays/analytics/aggregates.py`, justo despues de `teammate_synergy`
  (linea ~956, antes de `LADOS_PRIMERA_CAIDA`): misma familia, misma pagina.
  - `MIN_PARTIDAS_HABITUAL = 5` con comentario de por que se mide sin filtros (que un
    filtro de mapa no cambie con quien jugas).
  - `GRUPOS = ("solo", "duo", "trio", "stack")`: orden fijo, el indice es la cantidad
    de habituales (`GRUPOS[min(n, 3)]`).
  - `by_stack(**filters) -> dict`. Cinco consultas fijas, sin N+1 (lo mide un test):
    1. `mia = RoundPlayer.objects.filter(is_me=True, round_id=OuterRef("round_id"),
       team_index=OuterRef("team_index"))`; `companeros = RoundPlayer.objects.filter(
       is_me=False).filter(Exists(mia))`. Sin filtros a proposito. Correlacionada y no
       `IN` de round_ids, por el mismo motivo que `teammate_synergy` (tope de
       parametros de SQLite).
    2. Habituales: `companeros.values("player_id", "player__username").annotate(
       n=Count("round__match_id", distinct=True)).filter(n__gte=MIN_PARTIDAS_HABITUAL)
       .order_by("-n", "player__username")` -> lista `regulars` y `ids_hab`. Nombre
       desde `Player`, no desde `RoundPlayer.username` (cambio de nick).
    3. `por_partida = _por_partida(**filters)` (`aggregates.py:1186`): tus rondas
       filtradas agregadas por partida en una consulta. Sus claves son las partidas
       que entran.
    4. `ids = base_queryset(**filters).values("round__match_id")` (subconsulta, no
       lista) y `grupo = Counter(m for m, _ in companeros.filter(player_id__in=ids_hab,
       round__match_id__in=ids).values_list("round__match_id", "player_id").distinct())`:
       habituales distintos por partida, sobre **todas** las rondas de la partida
       (decision 2). Si `ids_hab` esta vacio, se saltea (todo va a `solo`).
    5. `won = dict(Match.objects.filter(id__in=ids).values_list("id", "won"))`.
    6. `baseline = rating_baseline()` una vez. En Python: cada `match_id` de
       `por_partida` va a `GRUPOS[min(grupo.get(mid, 0), 3)]`. Por fila:
       `t = _fold([por_partida[m] for m in mids], baseline)` (pondera `rating_points`
       por rondas, no promedia promedios); `decididas = [won[m] for m in mids if
       won[m] is not None]`.
    7. Devuelve `{"rows": [{"group": g, "regulars": i, "matches": len(mids),
       "matches_decided": len(decididas), "matches_won": sum(decididas),
       "match_winrate": _pct(sum(decididas), len(decididas)), "rounds": t["rounds"],
       "rounds_won": t["rounds_won"], "winrate": t["winrate"], "rating": t["rating"]}
       for i, g in enumerate(GRUPOS)], "regulars": [{"player_id", "username",
       "matches"}], "min_matches": MIN_PARTIDAS_HABITUAL}`. Ajuste al criterio 2:
       `by_stack` es un dict con `rows` (las cuatro filas, con las claves pedidas) mas
       `matches_decided` (denominador del winrate de partida, como `decided` en
       `by_start_side`), la lista de habituales y el umbral, para que la UI diga quien
       cuenta sin repetir la constante. Fila vacia: 0 y `None` (lo que ya da `_fold([])`).
- `backend/replays/views.py` (`teammates`, linea 246): `"by_stack": agg.by_stack(**filters)`.
  Sin `min_rounds`.
- `backend/tests/test_grupo.py` (nuevo; estilo `test_margen.py`, con `make_match /
  make_round / make_round_player`). Helper `_partida(index, companeros, *, mapa="Club
  House", mi=4, rival=2, rondas=2)` que crea tus rondas, una fila `team_index=0` por
  companero y un rival `team_index=1`. Tests:
  - `test_cinco_partidas_juntas_hacen_habitual_y_cuatro_no`
  - `test_las_cuatro_filas_salen_en_orden_aunque_esten_vacias`
  - `test_cada_partida_cae_en_una_sola_fila_segun_sus_habituales` (una partida con 0,
    1, 2 y 3 habituales; sumar `matches` de las filas da el total)
  - `test_cuatro_habituales_tambien_es_stack`
  - `test_un_habitual_que_jugo_una_sola_ronda_cuenta_para_la_partida`
  - `test_un_companero_no_habitual_no_cambia_la_fila`
  - `test_un_rival_frecuente_no_es_habitual` (5 partidas en `team_index=1`)
  - `test_un_empate_cuenta_en_partidas_y_rondas_pero_no_en_el_winrate_de_partida`
    (3-3 con `update(won=None)`; `matches` 2, `matches_decided` 1)
  - `test_un_cambio_de_nick_no_parte_al_habitual` (renombra `RoundPlayer.username` de
    la mitad y `Player.username`; sigue un habitual y la partida sigue en `duo`)
  - `test_el_filtro_de_mapa_no_cambia_quien_es_habitual` (5 partidas juntas en dos
    mapas; con `map=` del que tiene 2, esas 2 siguen en `duo`)
  - `test_el_filtro_de_lado_recorta_rondas_pero_no_el_grupo_de_la_partida` (habitual
    solo en la ronda de defensa; con `side="Attack"` la partida sigue en `duo`, con
    solo las rondas de ataque y su resultado entero)
  - `test_sin_habituales_todo_cae_en_solo`
  - `test_base_vacia_devuelve_las_cuatro_filas_en_cero`
  - `test_el_rating_de_la_fila_pondera_por_rondas` (dos partidas de distinto largo en
    la misma fila contra `totals` de esas rondas)
  - `test_la_cantidad_de_consultas_no_crece_con_las_partidas` (`assertNumQueries(5)`
    con 3 y con 8 partidas)
- `backend/tests/test_api.py`: `test_teammates_trae_by_stack` (con datos: 200, cuatro
  `rows` con las claves del criterio) y `test_teammates_trae_by_stack_con_base_vacia`
  (en `EmptyApiTests`: cuatro filas en 0 y `regulars` vacio).
- `frontend/src/grupo.js` + `frontend/src/grupo.test.js` (nuevos, como `margen.js`):
  - `etiquetaGrupo(group)`: `solo` -> "Solo", `duo` -> "Dúo", `trio` -> "Trío",
    `stack` -> "Stack"; uno desconocido pasa tal cual.
  - `filasDeGrupo(byStack)`: filas con `orden` y `etiqueta`, y `habituales` legible
    (0, 1, 2, "3 o más"); `byStack` ausente -> `[]`.
  - `textoHabituales(byStack)`: "Habituales: Chamo, Nico, Seba." o, sin ninguno,
    "Ningún compañero llega a 5 partidas contigo: todo cae en Solo." (el 5 sale de
    `min_matches`).
  - Tests: `nombra los cuatro grupos y deja pasar uno desconocido`, `conserva las
    cuatro filas en el orden del backend aunque esten en cero`, `una respuesta ausente
    devuelve una lista vacia`, `lista los habituales o avisa que no hay ninguno`.
- `frontend/src/pages/Teammates.jsx`: panel **"Solo, en dúo o en stack"** justo
  **despues** de "Sinergia" y antes de "Primero en caer" (ver Que puede romperse).
  `DataTable` con columnas Grupo, Habituales, Partidas, Winrate partida (%), Rondas,
  Winrate rondas (%), Rating (`digits: 2`); `initialSort={{ key: 'orden', dir: 'asc' }}`,
  `rowKey` por `group`, `csvName="solo-duo-stack"`. Hint: "Habitual: jugó en tu
  equipo en 5 o más partidas de todo tu historial; los filtros no lo cambian. Una
  partida cuenta por los habituales que estuvieron en cualquiera de sus rondas. El
  winrate de partida deja fuera empates e incompletas." Debajo, `<p className="note">`
  con `textoHabituales`. Si alguna fila con partidas tiene menos de `MUESTRA_PARTIDAS`
  (10, de `margen.js`), aviso de varianza via `filasConPocaMuestra(filas.map((f) =>
  ({ rounds: f.matches })), MUESTRA_PARTIDAS)`.
- `frontend/e2e/humo.spec.js`: `test('Compañeros muestra solo, en dúo o en stack')`,
  despues de `Compañeros muestra quien cae primero`. Panel `section.panel` con
  `hasText: 'Solo, en dúo o en stack'`; 4 `tbody tr`; la fila `hasText: 'Stack'`
  contiene `29`, `100%`, `203`, `57%` y `1.00`; la fila `Solo` contiene `—`; el panel
  contiene `Chamo`; consola limpia.
- `docs/metricas.md`: fila **Tamaño del grupo** en `## Cortes`, debajo de
  **Compañero**: habitual = jugó en tu equipo (`team_index`) en 5 o más partidas
  distintas de **todo** tu historial, medido sin filtros (aviso explicito); por
  profileID; solo/dúo/trío/stack = 0/1/2/3+ habituales en cualquier ronda de la
  partida; los filtros eligen partidas y rondas pero no cambian ni quién es habitual
  ni la fila de una partida; winrate de partida sin `won` nulo (empates e
  incompletas); distinto del mínimo de rondas de Sinergia.

**Orden:** aggregates + test_grupo -> vista + test_api -> grupo.js + test -> Teammates.jsx
+ `npm run build` -> e2e -> metricas.md -> `scripts/check.sh` (o `check.ps1`).

**Que puede romperse**

- El e2e `el perfil de un jugador se abre desde Compañeros` hace click en el primer
  link de `table tbody tr` **de la pagina**: si el panel nuevo quedara antes de
  Sinergia, su primera fila no tiene link y el test cae. Por eso va despues.
- El hint del panel no puede decir "Primero en caer" (el otro e2e busca el panel por
  ese texto) ni "Sinergia".
- `_fold` suma todas las claves de `AGGREGATES` que no estan en `_PROMEDIOS`: si la 53
  agrega un `Avg` a `AGGREGATES` sin registrarlo en `_PROMEDIOS`, rompe `by_stack` (y
  `sessions`). Avisarle al que implemente la 53.
- Nada de datos: sin migracion, sin recompute, `seed_demo` intacto. `/api/teammates/`
  suma 5 consultas cortas.

**Verificacion manual:** sobre `seed_demo`, `curl -s localhost:8000/api/teammates/ |
python -m json.tool | grep -A80 by_stack`: stack 29 / 29 / 203 / 116, las otras en 0,
`regulars` Chamo, Nico, Seba con 29. Con `?side=Attack`: stack 29 partidas y 116
rondas al 100 %. Con `?map=bank`: stack 10 y 70. En la UI, /companeros muestra el
panel debajo de Sinergia y el CSV baja las cuatro filas.

**Archivos ocupados:** ninguna rama abierta. Comparte archivo con las que se disenan en
paralelo, sin pisar funciones: `aggregates.py` (52 agrega `by_round_length` cerca de
los cortes de Tendencias; 53 toca `AGGREGATES`/`derive`, lineas 132-215; la 54 inserta
despues de `teammate_synergy`, linea ~956), `views.py` (52 `trends`, 221-243; 53
`_match_scoreboard`, 515; la 54 una linea dentro de `teammates`, 250-253: hunks
separados por pocas lineas, merge limpio si nadie reformatea), `humo.spec.js` y
`metricas.md` (las tres agregan tests/filas en lugares distintos). `Teammates.jsx` es
solo de la 54.

## Para el humano

El umbral de 5 partidas sale de C5 y no se calibro con la base real. Si en
tu historial casi todo cae en `solo`, se baja en el diseno; es reversible.

- Arquitecto 2026-10-17: bug latente fuera de esta ficha: un empate queda con `won=None` (`ingest.py:169`) y `match_result` mira `won is None` antes que el empate (`models.py:13-20`), asi que en toda la app un empate se muestra como "incompleta". Candidato a ficha `bug` del PO.
