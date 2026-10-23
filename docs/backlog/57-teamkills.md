# 57. Teamkills: a quien mataste y quien te mato

estado: aprobado
candado: release 2026-10-23T16:10Z
rama: claude/equipo-dev/57-teamkills
tipo: funcionalidad
epica: escuadra
area: fullstack
prioridad: 3
fuente: ALCANCE.md C7 ([Siege.GG](https://siege.gg/news/support-value-in-siege-explained-with-the-new-rating-model), "Teamkills per Round")
archivos: backend/replays/analytics/aggregates.py, backend/replays/views.py, backend/tests/test_teamkills.py, frontend/src/pages/Teammates.jsx, frontend/e2e/humo.spec.js, docs/metricas.md
turnos: po 20261019T0004Z, arquitecto 20261022T0804Z, dev 20261023T0404Z, revisor 20261023T0805Z, qa 20261023T1205Z, release 20261023T1606Z

## PR

(La escribe el Release manager al final.)

## Que gana quien usa la app

Los teamkills estan en el feed pero ninguna pantalla los muestra: Duelos los
descarta y las Bajas los suman sin avisar. Ver cuantos compañeros mataste,
cuantas veces te mato uno, con quien, y cuanto se pierde la ronda cuando pasa,
dice si es un problema real o anecdota.

## Criterios de aceptacion

- [ ] Agregado nuevo en `aggregates.py` sobre `Event` (bajas `Kill` cuyo autor
  y victima estan en el mismo `team_index` en esa ronda, la condicion inversa
  de `_solo_rivales`): teamkills tuyos, teamkills sufridos, rondas con algun
  teamkill de tu equipo y winrate de esas rondas contra el resto. Test con
  una ronda sintetica con un teamkill tuyo y otra con uno sufrido.
- [ ] Una fila por compañero (nick y `player_id`) con teamkills hechos y
  sufridos, ordenada por el total. La misma persona como rival en otra ronda
  no cuenta (test: su baja sobre ti cuando era rival no suma).
- [ ] Respeta los filtros de la barra (mapa, fechas, lado, ranked). Test con
  `?side=attack`.
- [ ] Panel "Teamkills" en la pagina Compañeros con los tres numeros y la
  tabla; sin teamkills dice "Ningún teamkill en las rondas filtradas". Entra
  al e2e con `seed_demo` (si el seed no tiene teamkills, el e2e verifica el
  texto vacio y un test de Django cubre el caso con datos).
- [ ] Fila en `docs/metricas.md` ("Teamkills") con la definicion y la nota de
  que siguen contando en Bajas.

## Fuera de alcance

- Sacar los teamkills de Bajas, KPR, Rating o multikills: cambia numeros que
  ya se muestran (seria decision del humano, P10).
- Columna nueva en `RoundPlayer` o migracion: sale del feed al consultar,
  como Duelos.
- Teamkills de rivales entre ellos.

## Diseno

Una sola forma obvia: es el espejo de `_solo_rivales` en la seccion de
duelos de `aggregates.py`, servido en `/api/teammates/`. Sin migracion, sin
columna nueva (Fuera de alcance), se calcula del feed al consultar.

**Backend, `backend/replays/analytics/aggregates.py`**, seccion de duelos,
debajo de `_solo_rivales`:

1. `_equipo_de(campo)`: `Subquery(RoundPlayer.objects.filter(round_id=OuterRef("round_id"),
   player_id=OuterRef(campo)).values("team_index")[:1])` (factorizar si queda
   limpio reusarlo en `_solo_rivales`; si no, duplicar las dos lineas).
2. `_teamkills(mine)`: `_mis_bajas(mine)` anotado con `mi_equipo=_MI_EQUIPO`,
   `eq_autor=_equipo_de("actor_id")`, `eq_victima=_equipo_de("target_id")`;
   filtro `eq_autor=F("mi_equipo")`, `eq_victima=F("mi_equipo")`, excluye
   nulos y `actor_id=F("target_id")` (un suicidio no es teamkill). Son las
   bajas entre compañeros de **tu** equipo en esa ronda.
3. `teamkills(**filters) -> dict`, con `mine = base_queryset(**filters)` y
   `me_ids = _me_ids()` (sin `me_ids`, todo en cero y lista vacia):
   - `mine`: `tks.filter(actor_id__in=me_ids).count()`
   - `suffered`: `tks.filter(target_id__in=me_ids).count()`
   - `rounds_with`: `round_id` distintos de `tks`; `rounds_without` = el resto
     de `mine`; `winrate_with` y `winrate_without` con `_pct` de `won` sobre
     `mine.filter(round_id__in=...)` y su `exclude`. Mismo `won` que el
     winrate general.
   - `by_teammate`: por cada baja tuya, el compañero es `target`; por cada
     sufrida, `actor`. Fila `{player_id, username, made, suffered, total}`
     (username de `Player`, como `nemesis`), ordenada por `-total`, despues
     `username`. Los teamkills entre dos compañeros que no sos vos cuentan
     en `rounds_with` pero no en la tabla.
4. `views.teammates`: clave `"teamkills": agg.teamkills(**filters)`.

**Tests, `backend/tests/test_teamkills.py`** (factories de
`tests/factories.py`, rondas con `RoundPlayer` de los dos equipos y `Event`
`Kill`):
- `test_un_teamkill_tuyo_cuenta_como_hecho`
- `test_un_teamkill_sufrido_cuenta_como_sufrido`
- `test_la_misma_persona_como_rival_no_suma` (otra ronda donde el mismo
  `Player` esta en el equipo contrario y te mata)
- `test_las_rondas_con_teamkill_tienen_su_winrate_aparte`
- `test_un_teamkill_entre_companeros_cuenta_la_ronda_pero_no_la_tabla`
- `test_respeta_el_filtro_de_lado` (`/api/teammates/?side=Attack` con el
  teamkill en una ronda de defensa: todo en cero)
- `test_sin_teamkills_devuelve_ceros_y_lista_vacia`

**Frontend, `frontend/src/pages/Teammates.jsx`**: Panel "Teamkills" despues
de "Primero en caer" y antes de "Clutches". Arriba tres numeros en una linea
(`Hechos`, `Sufridos`, `Rondas con teamkill` con su winrate contra el de las
demas, `pct()`); abajo `DataTable` con Compañero (Link a `/jugadores/<id>`
como Sinergia), Hechos, Sufridos, Total, `csvName="teamkills"`. Sin
teamkills (`mine + suffered === 0` y `rounds_with === 0`):
`<p className="dim">Ningún teamkill en las rondas filtradas.</p>` en lugar de
todo el contenido. `hint`: que siguen contando en Bajas.

**e2e, `frontend/e2e/humo.spec.js`**: `seed_demo` no tiene teamkills (el
verdugo siempre es rival y tus bajas siempre sobre rivales), asi que
`test('Compañeros muestra el panel de teamkills')` afirma el heading
"Teamkills", el texto vacio y consola limpia. No cambiar `seed_demo`: mueve
numeros que otros e2e afirman.

**`docs/metricas.md`**, seccion `## Duelos`: fila "Teamkills" (baja del feed
con autor y victima en tu equipo esa ronda; hechos, sufridos, rondas con
teamkill de tu equipo y su winrate; siguen contando en Bajas, KPR, Rating y
multikills, que no cambian).

**Orden:** helper + `teamkills` -> tests -> vista -> Teammates.jsx -> e2e ->
metricas.md -> `check.sh`.

**Que puede romperse:** nada existente: es una clave nueva del JSON. Cuidar
que el `Exists` de `_mis_bajas` + dos subqueries no se vuelva lento con la
base real (mismo patron que Duelos, que ya anda).

**Verificacion manual:** `/companeros` con la base real; cruzar un teamkill
con el feed del detalle de esa partida.

**Archivos ocupados:** `aggregates.py`, `views.py`, `metricas.md`,
`humo.spec.js` tambien en la rama de la 60 (PR #48) y en las fichas 56 y 59:
zonas distintas, se puede implementar ya y resolver con `git merge
origin/main` (P3). Con la 59 comparte el `return` de `views.teammates`: una
linea cada una.

## Implementacion

Hecho segun el diseno, sin desvios de alcance:

- `aggregates.py`: helper `_equipo_de(campo)` (ahora tambien lo usa
  `_solo_rivales`), `_teamkills(mine)` y `teamkills(**filters)` en la seccion
  de duelos. Suicidios y bajas sin autor o sin victima no cuentan.
- `views.teammates`: clave `teamkills`.
- `Teammates.jsx`: Panel "Teamkills" entre "Primero en caer" y "Clutches",
  con tres `Stat` (Hechos, Sufridos, Rondas con teamkill con su winrate
  contra las demas) y `DataTable` por compañero (`csvName="teamkills"`).
  Sin teamkills: "Ningún teamkill en las rondas filtradas.". Si solo hubo
  teamkills entre otros dos compañeros, se ven los numeros y la tabla dice
  que fueron entre otros.
- e2e: `Compañeros muestra el panel de teamkills` (texto vacio, `seed_demo`
  no tiene teamkills; no se toco el seed).
- `docs/metricas.md`: fila "Teamkills" en `## Duelos`.
- Tests: `backend/tests/test_teamkills.py`, 12 casos (los 7 del diseno mas
  suicidio, bajas sobre rivales, orden con desempate por nick, baja sin
  autor o sin victima y base vacia).

Decision chica: el winrate de las rondas con y sin teamkill usa
`RoundPlayer.won`, el mismo que el Winrate general (lo pide el diseno). Una
ronda sin ganador conocido cuenta como no ganada; queda dicho en
`metricas.md`. La revision ciega lo marco como menor; si el humano prefiere
excluirlas, es cambiar dos filtros.

Verificacion manual pendiente (no se puede en la nube): `/companeros` con la
base real y cruzar un teamkill con el feed del detalle de la partida.


## Revision 2026-10-23 sobre 6c563d1

Veredicto: **aprobar** -> `revisado`.

- Revision a ciegas (subagente con `revision.md` sobre el diff sin
  `docs/backlog`): sin hallazgos. Confirmado por el lider: el refactor de
  `_solo_rivales` arma la misma subconsulta (`test_duels` verde); los
  filtros de la barra entran por `base_queryset` tanto en los teamkills
  (`_mis_bajas` exige `Exists` en `mine`) como en las rondas; varias
  cuentas propias se manejan con `me_ids` y `_MI_EQUIPO` por ronda.
- Criterios: los 5 cubiertos. Agregado y casos tuyo/sufrido
  (`test_un_teamkill_tuyo_cuenta_como_hecho`,
  `test_un_teamkill_sufrido_cuenta_como_sufrido`), rival en otra ronda
  (`test_la_misma_persona_como_rival_no_suma`), winrate aparte
  (`test_las_rondas_con_teamkill_tienen_su_winrate_aparte`), filtro
  (`test_respeta_el_filtro_de_lado`), panel y texto vacio en el e2e
  (`Compañeros muestra el panel de teamkills`), fila "Teamkills" en
  `docs/metricas.md`.
- Diff dentro de `archivos:`; identificadores sin tildes, UI con tildes;
  sin `print` ni `console.log`.
- Mutaciones: sacar la condicion de equipo del autor tumba 3 tests; sacar
  la exclusion de suicidios tumba `test_un_suicidio_no_es_teamkill`.
- `check.sh` en `Todo en verde.` (757 tests backend, 120 vitest, build,
  46 e2e). Rama al dia con `origin/main` (93fe22c).
- Nota para QA: el e2e solo recorre el estado vacio (`seed_demo` no tiene
  teamkills); las tarjetas y la tabla con datos conviene verlas con una
  base sembrada desde `factories.py`.

## QA 2026-10-23 sobre 8ee9f5b

Veredicto: **aprobado**. Rama al dia con `origin/main` (93fe22c), sin
conflicto.

- `./scripts/check.sh`: `Todo en verde.` (757 tests backend, 120 vitest,
  build, 46 e2e).
- Base sembrada desde `factories.py` (`build_dataset(matches=4)` mas una
  partida en Border con: teamkill tuyo en ataque perdido, sufrido en
  defensa perdido, entre dos companeros en defensa ganada, el mismo
  "amigo" como rival matandote, y un suicidio). Script en el scratchpad,
  `DATA_DIR=<tmp> python3 sembrar.py`, `runserver 127.0.0.1:8711`.
  - `curl /api/teammates/` -> `mine 1, suffered 1, rounds_with 3,
    rounds_without 26, winrate_with 33.3, winrate_without 53.8`,
    `by_teammate [amigo 1/1/2]`: el rival y el suicidio no cuentan, el de
    otros dos cuenta la ronda y no la tabla.
  - `?side=Attack` -> `1, 0, 1 ronda, 0.0 vs 71.4`; `?side=Defense` ->
    `0, 1, 2 rondas`. `?map=border` -> lo mismo que sin filtro (los
    teamkills son de Border); `?map=club-house`, `?since=2099-01-01`,
    `?side=foo` -> ceros, `winrate_* null`, lista vacia. `?until=foo`,
    `?page=-1`, `?side=`, `?map=`, `?ranked=1` -> 200 sin cambios.
  - Base vacia (`migrate` solo): `/api/teammates/` 200 con ceros; la
    pagina muestra el EmptyState de importar (como antes).
  - Vecino `/api/duels/`: `deaths 1` (la baja de "amigo" como rival); el
    teamkill sufrido no entra a Duelos. 47 ms en las dos vistas.
- UI (Playwright sobre la base sembrada, `/companeros`): tres tarjetas
  (Hechos 1, Sufridos 1, Rondas con teamkill 3 "ganaste 33% · 54% en las
  demas") y tabla `amigo 1 1 2` con CSV; con Lado = Ataque cambia a
  `1 / 0 / 1`, `0% · 71%`; con mapa Club House, "Ningún teamkill en las
  rondas filtradas.". Consola limpia.
- Chunk inicial `index-*.js` 187.83 kB igual que `main`; `Teammates-*.js`
  (lazy) 6.97 -> 8.22 kB.
- Mutaciones (distintas de las del Revisor), todas caen: sin condicion de
  equipo de la victima (2 tests), winrate con/sin cruzados
  (`test_las_rondas_con_teamkill_tienen_su_winrate_aparte`), orden de la
  tabla invertido (`test_ordena_por_total_y_despues_por_nick`), sin los
  filtros de la barra (`test_respeta_el_filtro_de_lado`).
- Sin migracion, parser, `recompute`, Electron ni `.ps1`.

## Verificar en el PC

`cd backend; python manage.py runserver` con la base real, abrir
`/companeros` y cruzar un teamkill de la tabla con el feed del detalle de
esa partida.
