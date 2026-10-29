# 67. Teamkills fuera de las bajas

estado: disenado
candado: -
rama: -
tipo: bug
epica: -
area: backend
prioridad: 1
fuente: decision del humano 2026-10-28 en `## Para el equipo` de `ESTADO.md` (pregunta de la ficha 53); `pydissect/stats.py:81-85` suma todo `Kill` del autor; `docs/metricas.md` filas Bajas, Multikill, Teamkills y Mejor ronda
archivos: backend/replays/analytics/metrics.py, backend/replays/recompute.py, backend/replays/management/commands/recompute.py, backend/replays/analytics/aggregates.py (comentario l.133), backend/tests/test_metrics.py, backend/tests/test_recompute.py, backend/tests/test_player_stats.py (comentario), backend/tests/test_teamkills.py, docs/metricas.md
turnos: po 20261029T0004Z, arquitecto 20261029T0404Z

## PR

(La escribe el Release manager al final.)

## Que gana quien usa la app

Hoy matar a un compañero suma una baja: sube tu K/D, tu KPR y tu rating, y
puede convertir una ronda de 4 rivales en un "ace". Con el arreglo las bajas,
y todo lo que sale de ellas, cuentan solo rivales; los teamkills siguen a la
vista en su propio panel (Compañeros, ficha 57).

## Criterios de aceptacion

- [ ] `analyse_round` sobre una ronda con 2 bajas a rivales y 1 a un
      compañero (mismo `teamIndex`) deja `kills == 2` al autor; si la del
      compañero fue headshot, `headshots` tampoco la cuenta (el HS% nunca
      pasa de 100). Una ronda cuya unica baja es un teamkill no da `kst` por
      matar (test en `backend/tests/test_metrics.py`).
- [ ] `manage.py recompute` corrige lo ya importado sin reparsear: una
      `RoundPlayer` sembrada con `kills=3` y un evento `Kill` sobre un
      compañero queda en 2, `--dry-run` lo cuenta sin escribir, y una segunda
      corrida no cambia nada. La regla vive en una sola funcion que usan el
      import y `recompute` (como `clutch_vs`).
- [ ] Con esa ronda, 2K/3K/ace, K/D, KPR y rating de `/api/overview/`, el
      perfil de un jugador y el scoreboard de `/api/matches/<id>/` cuentan 2
      bajas y no 3; el test `test_un_teamkill_suma_a_las_bajas_del_autor` se
      invierte (decision del humano, no se borra) y el panel de Teamkills
      sigue devolviendo el mismo conteo.
- [ ] `docs/metricas.md` al dia: Bajas, Multikill, Teamkills ("siguen
      contando en Bajas..." deja de ser cierto), Cuando matas y Mejor ronda
      dicen que las bajas son solo a rivales; el comentario de
      `aggregates.py:133` sobre el ace tambien.
- [ ] Suite, vitest y e2e en verde sin tocar los numeros de `seed_demo`
      (no siembra teamkills; si alguno cambia, se explica en Implementacion).

## Fuera de alcance

- Apertura y entry (`opening_kill`, `entry_kill`) cuando la primera baja es
  un teamkill: sigue como hoy; si hace falta, otra ficha.
- El `1vX` de r6-dissect (`one_vx`) y la ficha del 1vX con `PlayerLeave`.
- Cambiar `pydissect/` si la regla puede vivir en `metrics.py` (el parser
  sigue entregando lo que entrega r6-dissect); lo decide el Arquitecto.
- Migracion: no hay columna nueva.

## Diseno

Arquitecto 20261029T0404Z, sobre `origin/dev@c3597f4`. Ninguna rama de
trabajo abierta: no pisa archivos de nadie.

**Decision: la regla vive en `metrics.py`, no en `pydissect/`.** El parser
sigue siendo un port de r6-dissect y entrega `kills` como el (todo `Kill` del
autor); la app decide que es una baja. Ademas `recompute` tiene que poder
rehacerla desde `Event` sin abrir un `.rec`, y eso solo es posible si la regla
esta del lado de la app, igual que `clutch_vs`. Consecuencia sobre el criterio
3: `test_un_teamkill_suma_a_las_bajas_del_autor`
(`tests/test_player_stats.py:45`) prueba el parser, no la app, y **queda**:
se le reescribe el comentario ("el parser sigue a r6-dissect; la app los
saca en `metrics.bajas_a_rivales`"). La inversion pedida es un test nuevo del
lado de la app, `test_un_teamkill_no_suma_a_las_bajas_del_autor`, en
`test_metrics.py`. Borrar el del parser no corresponde (nunca se borra un test).

`archivos:` y por que:

- `backend/replays/analytics/metrics.py`: funcion nueva
  `bajas_a_rivales(eventos, team_of) -> dict[str, dict]` con
  `{"kills": n, "headshots": h}` por nick de `team_of`. Cuenta cada evento
  `kind == KILL` cuyo `actor` esta en `team_of` y cuya victima no es del mismo
  equipo: `team_of.get(target)` distinto de `team_of[actor]`. Una victima que
  no esta en `team_of` (nick vacio o jugador que no figura) **cuenta**, como
  hoy: no hay como saber que es compañero, y asi la paridad sin teamkills es
  exacta. Un suicidio registrado como `Kill` (autor == victima) cae solo por
  la misma regla (mismo equipo). `headshots` suma solo esas bajas con
  `headshot` verdadero. En `analyse_round`, despues de armar `metrics` y
  **antes** de `annotate_trades` (que calcula `kst` con `kills`), se pisan
  `kills` y `headshots` de cada nick con lo que devuelve la funcion. Docstring
  del modulo: una linea `kills  bajas a rivales; los teamkills no cuentan`.
  `annotate_trades` no se toca: `trade_kills` y `was_traded` quedan como hoy
  (fuera de alcance). Caso raro que sigue igual: si un compañero mata al que
  hizo el teamkill dentro de la ventana, cuenta como trade; va a
  `## Para el humano` como aviso, no como pregunta.
- `backend/replays/recompute.py`: `CAMPOS` suma `kills` y `headshots`; en
  `_recompute_round`, antes de `annotate_trades`, se llama a la misma
  `bajas_a_rivales` con los eventos (`kind`, `actor_name`, `target_name`,
  `headshot`) y se escriben en `metrics[nick]`, que es lo que lee
  `annotate_trades` para `kst`. Docstring del modulo y de `recompute()`:
  "tambien saca los teamkills de `kills`".
- `backend/replays/management/commands/recompute.py`: `help` y docstring
  dicen que tambien corrige bajas y headshots. El texto de salida: "filas de
  jugador (bajas, trades o clutch)".
- `backend/replays/analytics/aggregates.py:133`: el comentario del ace pasa
  a "Ace es 5 o mas y no 5 justo: un modo con respawn la pasa de 5". Nada mas
  en ese archivo: K/D, KPR, rating, multikills y "Mejor ronda" leen la
  columna y se corrigen solos.
- `backend/tests/test_metrics.py`, `backend/tests/test_recompute.py`,
  `backend/tests/test_player_stats.py` (solo el comentario),
  `backend/tests/test_teamkills.py` (un test de no regresion).
- `docs/metricas.md`: filas **Bajas / muertes** (l.16: "Las bajas son solo a
  rivales: un teamkill o un suicidio no cuentan"), **Multikill** (l.233: sacar
  "teamkills incluidos" y el caso del ace con teamkill), **Teamkills**
  (l.215: "Siguen contando en Bajas..." pasa a "No cuentan en Bajas, KPR,
  Rating ni multikills"), **Cuando matas** (l.234: la suma de los tramos ya es
  la de la columna Bajas; sacar el parentesis), **Mejor ronda** (l.285:
  sacar "teamkills incluidos"). La fila **HS%** si existe: los headshots son
  de bajas a rivales.

Tests nuevos (nombres exactos):

- `test_metrics.py`:
  `test_un_teamkill_no_suma_a_las_bajas_del_autor` (2 rivales + 1 compañero
  -> `kills == 2`),
  `test_un_teamkill_con_headshot_no_suma_headshots` (headshots 1 de 2 rivales
  + compañero con HS -> `headshots == 1`, nunca mas que `kills`),
  `test_una_ronda_con_solo_un_teamkill_no_da_kst_por_matar` (el autor murio
  despues sin trade: `kst` False),
  `test_una_baja_a_un_nick_desconocido_sigue_contando`,
  `test_un_suicidio_como_kill_no_es_baja`.
- `test_recompute.py`:
  `test_recompute_saca_los_teamkills_de_las_bajas` (RoundPlayer sembrado con
  `kills=3, headshots=1` y 3 `Event` Kill, uno sobre compañero con HS ->
  queda `kills=2, headshots=0`), `test_recompute_dry_run_cuenta_las_bajas_sin_escribir`,
  `test_recompute_de_bajas_es_idempotente` (segunda corrida
  `players_changed == 0`).
- `test_teamkills.py`:
  `test_el_panel_de_teamkills_no_cambia_al_sacarlos_de_las_bajas`: con la
  base de los tests existentes, despues de `recompute()` el dict de
  `agg.teamkills()` es identico al de antes (lee `Event`, no `kills`).
- Un test de API (en `test_metrics.py` o `test_api.py`, con `factories`):
  `test_overview_y_scoreboard_cuentan_dos_bajas_con_un_teamkill`: importar via
  `analyse_round` -> `RoundPlayer` (o sembrar y correr `recompute`) una ronda
  2 rivales + 1 compañero y afirmar `kills == 2` en `/api/overview/`
  (`overall`), `k2 == 1` y `k3 == 0`, y la fila del autor en
  `/api/matches/<id>/`.

Orden de implementacion: (1) `bajas_a_rivales` + tests puros; (2) enchufarla
en `analyse_round`; (3) `recompute` + tests; (4) test de API y de teamkills;
(5) comentarios y `metricas.md`; (6) `check.sh`.

Que puede romperse:

- Tests existentes que siembran `RoundPlayer.kills` a mano y despues corren
  `recompute()` (`test_recompute.py`, `test_clutch.py`): si sus `Event` no
  tienen los `Kill` que justifican esos `kills`, `recompute` los bajaria a 0.
  **Revisar cada test que llama `recompute`**; si un test siembra bajas sin
  eventos, el arreglo es sembrar los eventos, no aflojar la regla. Si
  aparecen muchos, alternativa aceptable: `recompute` solo pisa `kills` y
  `headshots` en rondas que tienen al menos un `Event` Kill (anotarlo como
  desvio y en `metricas.md`), porque una ronda sin eventos es una ronda que
  no se puede recalcular.
- `seed_demo`: no siembra teamkills; los numeros del e2e no deberian moverse.
  Si alguno cambia, explicarlo en Implementacion.
- Rating: la formula usa `kills`; bajara donde hubo teamkills. Esperado.

Verificacion manual: `manage.py seed_demo`, `manage.py recompute --dry-run`
-> "Nada que recalcular". En una base con un teamkill (script del QA con
`factories`), `--dry-run` cuenta 1 fila, `recompute` la corrige, la segunda
corrida no cambia nada.

Sin migracion, sin umbral nuevo, sin fila nueva de `metricas.md` (se corrigen
las que existen).

Skills: no aplica (backend puro; el repo ya resuelve la misma forma con
`clutch_vs` en import y `recompute`). Sin arena: una sola forma razonable.

Implementar antes que #68 y #69: las tres tocan `recompute.py`.

## Implementacion

## Revision <fecha> sobre <sha>

## QA <fecha> sobre <sha>

## Verificar en el PC

## Pendiente

## Para el humano

Aviso del Arquitecto (no bloquea): `trade_kills` sigue contando el caso de un
compañero que mata al que hizo el teamkill dentro de la ventana de trade. Es
raro y queda fuera de esta ficha; si molesta, otra ficha.

Sin decision pendiente (la tomaste el 2026-10-28). Al bajar este cambio:
`manage.py backup` y `manage.py recompute` en el PC para corregir el
historial; K/D, KPR y rating bajan un poco donde hubo teamkills.
