# 38. Una ronda de Y9S4+ con defuse del perdedor queda con dos ganadores

estado: aprobado
candado: release 2026-10-13 14:15Z
rama: claude/equipo-dev/38-dos-ganadores-por-ronda
tipo: bug
epica: -
area: parser
prioridad: 2
fuente: aviso de la ficha 30 (`## Para el humano`, ya en main) y de `ESTADO.md`; `round_end` en `backend/pydissect/events.py:378`
archivos: backend/pydissect/events.py, backend/tests/test_round_end.py, docs/formato-rec.md
turnos: po 20261013T0511Z, arquitecto 20261013T0611Z, dev 20261013T1111Z, revisor 20261013T1213Z, qa 20261013T1312Z

## PR

(La escribe el Release manager al final: titulo `[equipo-dev][area] Titulo`,
cuerpo segun `.claude/skills/equipo-dev/plantilla-pr.md` y una seccion
"Como probarlo en 2 minutos" con comandos exactos.)

## Que gana quien usa la app

Desde Y9S4, `round_end` primero toma el ganador de la cabecera
(`startingScore < score`) y despues, si el feed trae un
`DEFUSER_DISABLE_COMPLETE` (o un `DEFUSER_PLANT_COMPLETE`) de un jugador del
otro equipo, marca **tambien** a ese equipo con `won=True`. Con dos
ganadores, `analyse_round` (`replays/analytics/metrics.py:205`) se queda con
el ultimo, el equipo 1: la ronda puede sumar como ganada mientras el
marcador de la partida (que sale de la cabecera) dice lo contrario. Arreglado,
el winrate de ronda, la condicion de victoria y todo lo que cuelga de
`my_team_won` dejan de contradecir al marcador.

## Criterios de aceptacion

- [ ] Con `code_version >= Y9S4`, cabecera dando la ronda al equipo 0 y un
      `DEFUSER_DISABLE_COMPLETE` de un jugador del equipo 1, `round_end`
      deja **exactamente un** equipo con `won=True`: el de la cabecera. Test
      en `test_round_end.py` (hoy sin test a proposito, ver ficha 30).
- [ ] Lo mismo con `DEFUSER_PLANT_COMPLETE` (rama `planter`): la cabecera
      manda y queda un solo ganador.
- [ ] Cuando feed y cabecera coinciden, la condicion sigue saliendo del
      feed (`DISABLED_DEFUSER` / `DEFUSED_BOMB`), como hoy: los 14 tests de
      `test_round_end.py` siguen verdes sin tocarlos.
- [ ] Cuando no coinciden, la condicion del ganador se infiere como en el
      resto de Y9S4+ (`KILLED_OPPONENTS` o `TIME`) y la ronda queda con
      `winConditionCertain` (o el campo equivalente que ya exista) en falso
      o con un aviso en `warnings`, segun elija el Arquitecto; test que lo
      afirma.
- [ ] Antes de Y9S4 (sin ganador en la cabecera) el comportamiento no
      cambia: test con `code_version` vieja y defuse que sigue dando el
      ganador por el feed.
- [ ] `docs/formato-rec.md` dice en una linea que desde Y9S4 la cabecera
      manda sobre el feed para el ganador.

## Fuera de alcance

- El caso de `PLAYER_LEAVE` en 1vX (otro aviso de la ficha 31): decision
  aparte del humano.
- Recalcular la base del usuario: lo hace el humano con `manage.py
  recompute` (va a `## Verificar en el PC`), nunca la app sola.
- Cambiar la inferencia de plant por reloj.

## Diseno

(Arquitecto 20261013T0611Z, sobre main e5bad5b)

**Causa exacta.** En `round_end` (`backend/pydissect/events.py:378`) la rama
Y9S4 fija `won` desde la cabecera antes del loop, pero el loop sigue
escribiendo `won=True` en el equipo de un `DEFUSER_DISABLE_COMPLETE` (y
`return`) y, despues del loop, en el del `planter`. Ninguno pone `False` al
otro, asi que quedan dos ganadores. `analyse_round`
(`replays/analytics/metrics.py:205`) recorre los equipos y se queda con el
ultimo `won`, el 1.

**Cambio (solo `events.py`, ~20 lineas).** Separar "quien gano" de "por que":

1. En el loop, para `DEFUSER_DISABLE_COMPLETE`, guardar el indice del jugador
   en una variable local `disabler` (como ya se hace con `planter`) en vez de
   escribir `won` y salir. Para mantener el comportamiento previo a Y9S4 tal
   cual, el `return` temprano sigue existiendo **solo** cuando
   `r.code_version < Y9S4`: ahi se escribe `won`/`winCondition` y se sale,
   exactamente como hoy (mismo orden: el disable gana al plant).
2. Despues del loop, si `r.code_version >= Y9S4`: el ganador `w` es el de la
   cabecera (ya escrito). La condicion se elige asi, en este orden:
   - `disabler > -1` y su `teamIndex == w` -> `DISABLED_DEFUSER`;
   - si no, `planter > -1` y su `teamIndex == w` -> `DEFUSED_BOMB`;
   - si no, la inferencia que ya existe (`KILLED_OPPONENTS` / `TIME`, solo en
     `BOMB`, sin tocar).
   Nunca se escribe `won` desde el feed en Y9S4+.
3. El bloque `if planter > -1` de hoy pasa a correr solo antes de Y9S4.

**Marca de incertidumbre (criterio 4), eleccion del Arquitecto:** no se
agrega campo nuevo al parser. Cuando feed y cabecera no coinciden, la
condicion queda en la inferida (`KILLED_OPPONENTS`/`TIME`) y no hace falta
mas: la columna `Round.win_condition_certain` **no** sale del parser sino de
`analyse_round`, que ya la pone en `False` en todo lo que no es eliminacion
(`metrics.py:226-234`). Agregar un aviso en el parser no llegaria a ninguna
pantalla. El test del criterio 4 afirma la condicion inferida y que hay un
solo ganador. Un comentario de una linea en el codigo explica por que el feed
no manda (la cabecera es la misma fuente que el marcador de la partida).

**Tests nuevos** en `backend/tests/test_round_end.py` (clase `RoundEndTests`,
reusan `LectorFalso`, `resultado` y la convencion "el feed apunta al otro
equipo que el marcador"):

- `test_y9s4_un_defuse_del_perdedor_no_crea_un_segundo_ganador`: `Y9S4`,
  `score=(1, 0)`, feed `DEFUSER_DISABLE_COMPLETE` de `B0` ->
  `[(True, TIME), (False, "")]`.
- `test_y9s4_un_plant_del_perdedor_no_crea_un_segundo_ganador`: `Y9S4`,
  `roles=(DEFENSE, ATTACK)`, `score=(1, 0)`, feed `DEFUSER_PLANT_COMPLETE`
  de `B0` -> `[(True, TIME), (False, "")]`.
- `test_y9s4_sin_coincidencia_y_con_eliminacion_la_condicion_es_eliminacion`:
  como el primero mas 5 muertes de `B*` -> `[(True, KILLED_OPPONENTS), (False, "")]`.
- `test_y9s4_defuse_del_ganador_da_la_condicion_desactivar`: `score=(0, 1)`,
  feed plant de `A0` y disable de `B0` -> `[(False, ""), (True, DISABLED_DEFUSER)]`.
- `test_y9s4_plant_del_ganador_da_la_condicion_bomba`: `score=(1, 0)`, plant
  de `A0` -> `[(True, DEFUSED_BOMB), (False, "")]`.
- `test_previo_y9s4_el_defuse_sigue_decidiendo_el_ganador`: `Y9S3`,
  `score=(1, 0)` (que antes de Y9S4 se ignora), disable de `B0` ->
  `[(False, ""), (True, DISABLED_DEFUSER)]`. Los 14 tests existentes no se
  tocan.
- En `test_metrics.py` (si hay donde) no hace falta nada: con un solo
  ganador `analyse_round` ya funciona.

**Orden:** tests primero (los dos primeros fallan hoy con dos `True`),
despues el cambio, despues `docs/formato-rec.md`: una linea en la seccion
"La cabecera", junto a `startingteamscore0/1 (desde Y9S4)`: "desde Y9S4 el
ganador de la ronda sale de comparar `teamscore` con `startingteamscore`, y
manda sobre el kill feed; el feed solo aporta la condicion si apunta al mismo
equipo".

**Que puede romperse.** Ninguna migracion. Cambia el resultado de rondas ya
importadas de Y9S4+ con defuse/plant del perdedor, pero solo despues de
`manage.py recompute` (lo corre el humano; ya esta en `## Verificar en el PC`).
`test_pydissect` con fixtures sinteticas tiene que seguir verde. No toca
frontend, no hay fila de `metricas.md` (no hay numero nuevo).

**Verificacion manual.** `cd backend && python manage.py test tests.test_round_end -v 2`.

**Archivos:** los de la cabecera, sin cambios.

## Implementacion

(Dev 20261013T1111Z)

- `round_end` (`backend/pydissect/events.py`): el loop guarda `disabler`
  como ya guardaba `planter`; el `return` temprano del defuse y el bloque
  del plant quedan solo antes de Y9S4, sin cambios de orden. Desde Y9S4 el
  ganador es el de la cabecera y el feed solo aporta `DISABLED_DEFUSER` o
  `DEFUSED_BOMB` si apunta al ganador; si no, la inferencia de bomba de
  siempre (`KILLED_OPPONENTS` / `TIME`). Ningun camino Y9S4+ escribe `won`
  desde el feed.
- Tests: los 6 del diseno en `test_round_end.py`, con los nombres del
  diseno. Los 3 de "perdedor"/"sin coincidencia" fallan sobre main (dos
  `True`) y pasan con el cambio; los 14 existentes no se tocaron.
- `docs/formato-rec.md`: parrafo bajo las claves de la cabecera.
- Desvio del diseno: ninguno en codigo. **Si en la verificacion**: el
  diseno y la ficha dicen que las rondas ya importadas se corrigen con
  `manage.py recompute`, pero `recompute` no abre ningun `.rec` (solo
  recalcula trades desde la base). Las rondas Y9S4+ ya importadas se
  corrigen reimportando: `manage.py import_replays --force <carpeta>`.
  Corregido abajo en `## Verificar en el PC`.
- Revision ciega (subagente con `revision.md`): aprobar, sin hallazgos;
  confirmo con mutacion (events.py de main) que los tests nuevos caen.
- `check.sh`: `Todo en verde.` (484 tests backend, 65 frontend, build, 24 e2e).

## Revision 2026-10-13 sobre 0b96635

(Revisor 20261013T1213Z) Revision ciega con `revision.md` y confirmacion del
lider. `check.sh` en el revisor: `Todo en verde.` (484 backend, 65 frontend,
build, 24 e2e). `origin/main` ya estaba fusionado.

Confirmado: desde Y9S4 `round_end` solo escribe `won` desde la cabecera, que
siempre deja exactamente un ganador (`events.py:392-394`); antes de Y9S4 el
orden disable > plant > inferencia queda intacto. Los dos tests "del
perdedor" fallan sobre main (dos `True`) y pasan con el cambio. Criterios 1 a
6 cubiertos por los 6 tests nuevos de `test_round_end.py` y el parrafo de
`docs/formato-rec.md`; los 14 tests previos sin tocar. `pydissect/` sigue
sin importar Django.

- [formato, menor, no bloqueante] backend/pydissect/events.py:431-435
  Que pasa: en Y9S4+, plant del atacante y ronda ganada por la defensa sin
  defuse en el feed ni eliminacion completa deja `winCondition = TIME`, que
  no puede pasar despues de un plant (lo fija
  `test_y9s4_un_plant_del_perdedor_no_crea_un_segundo_ganador`, como pedia el
  diseno).
  Por que no bloquea: el `winCondition` de pydissect no se guarda ni se lee
  (`grep winCondition backend/replays` vacio; `analyse_round` calcula su
  propia condicion), asi que no cambia ningun dato de la base ni de la UI.
  Arreglo posible a futuro: con plant del perdedor, condicion vacia o
  `DISABLED_DEFUSER` en vez de `TIME`.

Veredicto: aprobar.

## QA 2026-10-13 sobre a6febeb

(QA 20261013T1312Z) Codigo de 0b96635; `origin/main` (3e42126) ya fusionado.
Scripts en el scratchpad de la sesion, base temporal (`SQLITE_PATH`), sin
`.rec` reales.

- `./scripts/check.sh` -> `Todo en verde.` (484 tests backend, 65 frontend,
  build, 24 e2e). Sin migraciones ni `frontend/src`: chunk sin cambios.
- Criterios 1 y 2: `python manage.py test tests.test_round_end -v 2` -> 20
  OK, incluidos `test_y9s4_un_defuse_del_perdedor_no_crea_un_segundo_ganador`
  y `test_y9s4_un_plant_del_perdedor_no_crea_un_segundo_ganador`.
  Propiedad sobre 3456 combinaciones (version Y9S3/Y9S4 x marcador x roles x
  disable de A0/B0/ninguno/desconocido x plant de A1/B1/ninguno x 0-5 bajas
  por lado): en Y9S4 siempre **un** ganador, el de la cabecera, y el
  perdedor sin condicion. Con `events.py` de main la misma propiedad falla
  (`[(True, ''), (True, 'DefusedBomb')]` con plant de B1).
- Criterio 3: los 14 tests previos de `test_round_end.py` verdes sin tocar;
  `test_y9s4_defuse_del_ganador_da_la_condicion_desactivar` y
  `test_y9s4_plant_del_ganador_da_la_condicion_bomba` verdes.
- Criterio 4: `test_y9s4_sin_coincidencia_y_con_eliminacion_la_condicion_es_eliminacion`
  verde; la incertidumbre la pone `analyse_round` (`win_condition_certain=False`,
  `ObjectiveOrTime`), confirmado en la importacion de abajo.
- Criterio 5: `test_previo_y9s4_el_defuse_sigue_decidiendo_el_ganador` verde.
- Criterio 6: `docs/formato-rec.md:72-74`.
- Cadena completa: partida sintetica Y9S4 de 3 rondas (ronda 1 = cabecera
  al rival + defuse propio, ronda 2 = defuse propio y ganada, ronda 3 =
  eliminacion del rival) importada por `ingest.import_match_folder` con
  `MatchReader` reemplazado. Rama: rondas con `my_team_won` = 1 y marcador
  1-2, coinciden; `GET /api/matches/1/` -> 200 con lo mismo. Con
  `events.py` de main: 2 rondas ganadas contra un marcador 1-2 (el bug).
- Endpoints con base vacia y parametros borde (`/api/overview/?until=foo`,
  `/api/matches/?page=-1`, `/api/trends/`, `/api/coach/`): 200;
  `/api/matches/1/` sin datos: 404.
- Mutacion (`python manage.py test tests.test_round_end`): (1) el disable
  vuelve a escribir `won` en Y9S4 -> caen 2 tests; (2) sin chequear el equipo
  del disabler -> caen 2; (3) sin chequear el equipo del planter -> cae 1.
- `tests.test_pydissect`: verde; `test_parsea_una_ronda_completa` se salta
  sin `R6_TEST_REPLAY` (ver abajo).

Veredicto: aprobado. El hallazgo menor del Revisor (`TIME` tras un plant del
perdedor) sigue sin efecto en datos: `winCondition` de pydissect no se guarda.

## Verificar en el PC

(QA, solo si toca migraciones, recompute, parser, Electron o `.ps1`.)
Toca el parser: confirmar con `.rec` reales de Y9S4+ que el ganador de cada
ronda coincide con el marcador. `recompute` no reparsea: las rondas ya
importadas se corrigen con `cd backend; python manage.py import_replays
--force <carpeta de replays>` (hacer `manage.py backup` antes).
Y el test con replay real: `$env:R6_TEST_REPLAY="<ruta a un .rec Y9S4+>"; cd backend; python manage.py test tests.test_pydissect`.

## Pendiente

## Para el humano

Decision tomada por el PO con la variante conservadora: **manda la
cabecera**, porque es la misma fuente que el marcador de la partida y el
comentario de `round_end` ya la trata como la verdad desde Y9S4. La
alternativa (manda el feed y se corrige el marcador) es mas invasiva y no se
hace sin que lo pidas en `## Para el equipo`. El cambio es reversible: no
toca datos hasta que reimportes con `import_replays --force` (`recompute` no reparsea).
