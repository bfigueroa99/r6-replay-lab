# 37. Rivales repetidos con tu record contra cada uno

estado: con hallazgos
candado: -
rama: claude/equipo-dev/37-rivales-repetidos
tipo: funcionalidad
epica: rivales
area: fullstack
prioridad: 3
fuente: ALCANCE.md D1; `nemesis` (`backend/replays/analytics/aggregates.py:640`) cuenta duelos pero no partidas ganadas o perdidas contra cada rival
archivos: backend/replays/analytics/aggregates.py, backend/replays/views.py, frontend/src/pages/Duelos.jsx, docs/metricas.md, backend/tests/, frontend/e2e/
turnos: po 20261013T0511Z, arquitecto 20261013T0611Z, dev 20261013T1111Z, revisor 20261013T1213Z

## PR

(La escribe el Release manager al final: titulo `[equipo-dev][area] Titulo`,
cuerpo segun `.claude/skills/equipo-dev/plantilla-pr.md` y una seccion
"Como probarlo en 2 minutos" con comandos exactos.)

## Que gana quien usa la app

En Duelos ve la lista de rivales que le tocaron en 2 o mas partidas, con
cuantas les gano y cuantas perdio, y entra al perfil de cada uno con un
clic. Hoy solo sabe a quien mata o quien lo mata, no contra quien pierde
partidas.

## Criterios de aceptacion

- [ ] `GET /api/duels/` devuelve una clave nueva `rivals`: una fila por
      jugador que estuvo en el equipo contrario en al menos `min_matches`
      partidas (por defecto 2), con `player_id`, `username`, `matches`,
      `wins`, `losses` y `winrate` de partida. Se agrupa por jugador
      (`Player`, es decir `profileID`), no por nick: un rival que se cambio
      el nick sigue siendo una fila.
- [ ] Un jugador que en una partida fue compañero y en otra rival cuenta
      solo las partidas en que fue rival. Test con dos partidas armadas a
      mano que lo afirma.
- [ ] Las partidas sin resultado (`Match.won` nulo) cuentan en `matches` y
      no en `wins` ni `losses`; el `winrate` se calcula sobre las que tienen
      resultado.
- [ ] Los filtros comunes aplican y `?min_matches=` acepta 1 a 1000; un
      valor fuera de rango o no numerico no da 500 (mismo helper que
      `min_duels`).
- [ ] La pagina Duelos muestra la tabla "Rivales repetidos" con enlace a
      `/jugadores/<id>` (la ruta del perfil que ya existe, `App.jsx:140`), y el e2e la
      renderiza sin errores de consola. Con `seed_demo` la tabla no queda
      vacia o, si queda, muestra un texto de vacio en vez de nada.
- [ ] `docs/metricas.md` tiene la fila de "record contra un rival".

## Fuera de alcance

- Cualquier dato de rivales que no salga de tus replays (Ubisoft, trackers):
  esto no es scouting.
- Operadores o mapas por rival: ya estan en el perfil del jugador.
- Avisos del coach sobre rivales.

## Diseno

(Arquitecto 20261013T0611Z, sobre main e5bad5b)

**Definicion de rival** (la misma que `player_profile`, `aggregates.py:1102`,
y que `_solo_rivales`): una persona es rival en una partida si en al menos
una de **mis rondas filtradas** de esa partida tiene una fila de
`RoundPlayer` con `team_index` distinto del mio en esa ronda. Se agrupa por
`player_id` (`Player`, profileID), nunca por nick. Si en una partida fue
compañero en unas rondas y rival en otras (no deberia pasar, pero los datos
son de replays), cuenta como rival en esa partida.

**Backend, `backend/replays/analytics/aggregates.py`**, funcion nueva
`repeated_rivals(min_matches: int = 2, **filters) -> list[dict]` debajo de
`nemesis` (antes de `_agregar_mapas`, linea ~699):

```python
mine = base_queryset(**filters)
me_ids = _me_ids()
if not me_ids:
    return []
de_rival = (
    RoundPlayer.objects.filter(Exists(mine.filter(round_id=OuterRef("round_id"))))
    .exclude(player_id__in=me_ids)
    .annotate(mi_equipo=_MI_EQUIPO)
    .exclude(mi_equipo=None)
    .exclude(team_index=F("mi_equipo"))
    .values("player_id", "round__match_id").distinct()
)
```

`_MI_EQUIPO` ya existe (`aggregates.py:582`): verificar que su `OuterRef`
apunta a `round_id` y sirve sobre un queryset de `RoundPlayer` (hoy se usa
sobre `Event`, que tambien tiene `round_id`); si no encaja, un Subquery
local identico sobre `mine.filter(round_id=OuterRef("round_id")).values("team_index")[:1]`.
Despues, en Python: `won` por partida con un solo
`Match.objects.filter(id__in=<ids>).values_list("id", "won")`; nombre con
`Player.objects.filter(id__in=<ids>).values_list("id", "username")` (el nick
actual del `Player`, como el perfil). Fila: `player_id`, `username`,
`matches`, `wins`, `losses`, `winrate = _pct(wins, wins + losses)` (las de
`won` nulo cuentan en `matches` y no en el denominador). Filtra
`matches >= min_matches`. Orden: `(-matches, -losses, username)` (los que mas
te ganan primero a igual cantidad).

**`backend/replays/views.py`** (`duels`, linea ~304): `min_matches =
_int_param(request, "min_matches", 2, minimum=1, maximum=1000)` y clave
nueva `"rivals": agg.repeated_rivals(min_matches=min_matches, **filters)`.

**Tests nuevos** en `backend/tests/test_duels.py` (ya tiene el armado de
rivales con `factories`; seguir su estilo):

- `test_rivales_repetidos_cuenta_partidas_ganadas_y_perdidas`: un rival en 3
  partidas (2 ganadas, 1 perdida) -> `matches 3, wins 2, losses 1, winrate 66.7`
  (el redondeo que use `_pct`).
- `test_un_rival_en_una_sola_partida_no_aparece_con_el_minimo_por_defecto`.
- `test_quien_fue_companero_en_una_partida_y_rival_en_otra_cuenta_solo_la_de_rival`:
  dos partidas, en una es compañero, en otra rival, `min_matches=1` -> `matches 1`.
- `test_partida_sin_resultado_cuenta_en_matches_y_no_en_el_winrate`:
  `Match.won=None` en una de dos -> `matches 2`, `wins + losses == 1`.
- `test_un_cambio_de_nick_no_parte_la_fila_de_rivales`: mismo `Player` con
  dos nicks en dos partidas -> una fila.
- `test_min_matches_fuera_de_rango_o_texto_no_da_500`: `?min_matches=0`,
  `-5`, `abc`, `99999` -> 200.
- `test_el_filtro_de_mapa_aplica_a_rivales`: `?map=` deja solo las partidas
  de ese mapa.

**Frontend, `frontend/src/pages/Duelos.jsx`**: Panel nuevo **despues** de
"Por rival" (linea ~210), titulo `Rivales repetidos`, hint `Personas que te
tocaron en el equipo contrario en 2 o más partidas, con el resultado de esas
partidas. Es tu récord contra ellas, no su nivel: el resto lo deciden los
otros ocho.` `DataTable` con `Rival` (`Link` a `/jugadores/${row.player_id}`,
igual que "Por rival" en la linea 180), `Partidas`, `Ganadas`, `Perdidas`,
`Récord` (`${wins}-${losses}`, `sortable: false`), `Winrate` (%);
`rowKey=player_id`, `csvName="rivales-repetidos"`,
`initialSort={{ key: 'matches', dir: 'desc' }}`,
`empty="Nadie te tocó de rival en 2 o más partidas con estos filtros."`.
Usar `data.rivals ?? []`. Ojo: la pagina hace `return <EmptyState>` si
`totals.duels` es 0 (linea 42); no cambiar eso.

**e2e, `frontend/e2e/humo.spec.js`**: test nuevo `'Duelos muestra rivales
repetidos'`: `goto('/duelos')`, texto `Rivales repetidos` visible, y o bien
una fila con un enlace a `/jugadores/` o bien el texto de vacio (el seed
reusa 3 rivales en todas las partidas, `seed_demo.py:253`, asi que deberia
haber filas; si las hay, afirmar al menos una con `toHaveAttribute('href',
/\/jugadores\/\d+$/)`). Consola limpia.

**`docs/metricas.md`**, tabla de `## Duelos` (linea ~119), dos filas:
**Rival repetido** (persona en el equipo contrario en al menos una de tus
rondas filtradas de N partidas distintas; por profileID) y **Récord contra
un rival** (partidas ganadas-perdidas; winrate sobre las que tienen
resultado).

**Orden:** tests backend (rojos) -> `aggregates.py` -> `views.py` -> verdes
-> `Duelos.jsx` -> build -> e2e -> `metricas.md`.

**Que puede romperse.** Sin migracion. `Exists` + `Subquery` por fila de
`RoundPlayer` de todos los jugadores en mis rondas (~10x mis filas): mismo
orden que `player_profile`, aceptable; si `/api/duels/` pasa de ~1 s en la
base real, anotarlo para el humano. Un rival que solo aparece en rondas
excluidas por filtros (`side`, `site`) no cuenta en esa partida: es
coherente con el resto de la pagina, decirlo en el hint de `metricas.md`.

**Choque con otras fichas.** Sin ramas abiertas. La 36 toca los mismos
archivos (`aggregates.py`, `views.py`, `metricas.md`, `humo.spec.js`) en
otras funciones y secciones: se puede implementar en paralelo.

**Archivos:** los de la cabecera, sin cambios.

## Implementacion

(Dev 20261013T1111Z)

- `repeated_rivals` en `aggregates.py`, debajo de `nemesis`, con la consulta
  del diseno; `_MI_EQUIPO` sirvio tal cual sobre `RoundPlayer`. Nick: el
  actual del `Player`. Orden `(-matches, -losses, username)`.
- `views.duels`: clave `rivals`, `min_matches` con `_int_param` (1 a 1000,
  default 2).
- `Duelos.jsx`: panel "Rivales repetidos" despues de "Por rival", con las
  columnas del diseno. Desvio menor: `Winrate` como porcentaje simple con
  `help` (sin barra), para no confundirlo con la columna "Ganas" de duelos.
  El `EmptyState` de la pagina (`totals.duels == 0`) no se toco, como pide el
  diseno: con un filtro que deja rivales sin ninguna baja la tabla no se ve.
- e2e `'Duelos muestra rivales repetidos con enlace al perfil'` en
  `humo.spec.js`: con `seed_demo` hay filas (3 rivales, 29 partidas), afirma
  el `href` y que el clic abre el perfil.
- Tests en `test_duels.py` (clase `RivalesRepetidosTests`): los 7 del diseno
  mas `test_sin_datos_no_revienta` y
  `test_endpoint_trae_los_rivales_con_enlace_al_jugador`.
- `docs/metricas.md`: filas "Rival repetido" y "Récord contra un rival" en
  `## Duelos`.
- Revision ciega (subagente con `revision.md`): aprobar; un hallazgo menor
  corregido (la fila de metricas nombraba `side`/`site` y no `operator`).
- `check.sh`: `Todo en verde.` (487 tests backend, 65 frontend, build, 25 e2e).

## Revision 2026-10-13 sobre a4a2213

(Revisor 20261013T1213Z) Revision ciega con `revision.md` y confirmacion del
lider. `check.sh` en el revisor: `Todo en verde.` (487 backend, 65 frontend,
build, 25 e2e). `origin/main` ya estaba fusionado.

- [bug] frontend/src/pages/Duelos.jsx:233
  Que pasa: la columna "Récord" sale vacia en el CSV que baja el boton de la
  tabla "Rivales repetidos".
  Como reproducirlo o por que es cierto: la columna tiene `key: 'record'` y
  solo `render`; las filas de `/api/duels/` no traen `record`, y `celdaCsv`
  (`frontend/src/components/ui.jsx:85`) lee `row[col.key]` -> `undefined` ->
  `''`. Confirmado leyendo `celdaCsv`; `Jugador.jsx:220` y `Trends.jsx:129`
  ya resuelven este caso con `csv:`.
  Arreglo sugerido: agregar `csv: (row) => \`${row.wins}-${row.losses}\`` a
  esa columna (o `csv: false`, porque Ganadas y Perdidas ya se exportan), y
  un caso en `frontend/src/logica.test.js` o en el e2e que afirme el valor
  `2-1` en el CSV.

Criterios: los 6 cubiertos (tests `RivalesRepetidosTests` en `test_duels.py`
para 1 a 4, e2e `Duelos muestra rivales repetidos con enlace al perfil` para
el 5, filas en `docs/metricas.md` para el 6). Diff dentro de `archivos:`.
Sin tildes en identificadores, UI con tildes, sin `print`/`console.log`.
Consulta por ronda contra `is_me`, agrupada por `player_id`: correcta.

Veredicto: corregir (el hallazgo de CSV, una linea).

## QA <fecha> sobre <sha>

(QA) Un comando y un resultado por criterio de aceptacion.

## Verificar en el PC

(QA, solo si toca migraciones, recompute, parser, Electron o `.ps1`.)

## Pendiente

## Para el humano

- En `seed_demo` todas las partidas son ganadas, asi que la tabla demo
  muestra records 29-0. Cambiar el seed movera numeros que afirma el e2e:
  queda como idea, no se toco.
