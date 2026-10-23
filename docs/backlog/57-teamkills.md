# 57. Teamkills: a quien mataste y quien te mato

estado: en curso 2026-10-23T04:04Z
candado: dev 2026-10-23T04:04Z
rama: claude/equipo-dev/57-teamkills
tipo: funcionalidad
epica: escuadra
area: fullstack
prioridad: 3
fuente: ALCANCE.md C7 ([Siege.GG](https://siege.gg/news/support-value-in-siege-explained-with-the-new-rating-model), "Teamkills per Round")
archivos: backend/replays/analytics/aggregates.py, backend/replays/views.py, backend/tests/test_teamkills.py, frontend/src/pages/Teammates.jsx, frontend/e2e/humo.spec.js, docs/metricas.md
turnos: po 20261019T0004Z, arquitecto 20261022T0804Z, dev 20261023T0404Z

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
