# 69. El 1vX cuenta cuando un compañero se fue

estado: aprobado
candado: release 2026-11-03T12:12Z
rama: claude/equipo-dev/69-clutch-cuenta-con-abandonos
tipo: bug
epica: -
area: backend
prioridad: 2
fuente: decision del humano 2026-10-28 en `## Para el equipo` de `ESTADO.md` (pregunta de la ficha 31); `pydissect/stats.py:100-104` arma `winners_alive` solo con `died`, que `PlayerLeave` no marca
archivos: backend/replays/analytics/metrics.py, backend/replays/recompute.py, backend/replays/management/commands/recompute.py, backend/tests/test_clutch.py, backend/tests/test_player_stats.py, backend/tests/test_recompute.py, docs/metricas.md
turnos: po 20261029T0004Z, arquitecto 20261030T1652Z, dev 20261103T0403Z-cYjVEvZ, revisor 20261103T0804Z-chGRfoT, qa 20261103T1205Z-cZPEnjG, release 20261103T1205Z-cZPEnjG

## PR

(La escribe el Release manager al final.)

## Que gana quien usa la app

Si un compañero abandona y despues quedas ultimo vivo y ganas la ronda, hoy
no te cuenta el clutch: el que se fue sigue figurando "vivo". Con el arreglo
ese 1vX suma en Clutch, en el record "Clutch mas grande" y en el rating, igual
que ya lo ve "Clutch: intentos y conversión" (`clutch_vs`, ficha 55).

## Criterios de aceptacion

- [ ] Ronda sintetica: equipo ganador de 5, tres mueren por `Kill`, uno sale
      por `PlayerLeave`, el ultimo mata a los 2 rivales que quedaban y gana:
      su `1vX` es 2 (hoy 0). Test en `backend/tests/test_clutch.py` o
      `test_pydissect.py`.
- [ ] Un rival que se fue tampoco cuenta como "vivo" al sumar el X del final
      de ronda: mismo escenario con un rival que sale por `PlayerLeave` y no
      muere da X sin el.
- [ ] Sin abandonos, el `1vX` de todas las rondas de los tests actuales no
      cambia (paridad con r6-dissect en el caso normal).
- [ ] Lo ya importado se corrige sin reparsear si los eventos guardados
      alcanzan (`Event` guarda `PlayerLeave`): `manage.py recompute`
      recalcula `one_vx` con la misma funcion que el import, `--dry-run`
      cuenta los cambios, segunda corrida sin cambios. Si el Arquitecto
      concluye que no alcanza, `## Verificar en el PC` pide
      `import_replays --force` y la fila lo dice.
- [ ] `docs/metricas.md`, fila **1vX (clutch)**: `PlayerLeave` cuenta como
      fuera de la ronda, y ya no es "exactamente" la logica de r6-dissect.

## Fuera de alcance

- `clutch_vs` (ya toma `PlayerLeave` como muerte) y la conversion de
  clutch: no cambian.
- Contar el abandono como muerte en `died`, K/D o Supervivencia.
- Abandonos como metrica propia (idea D3 de `ALCANCE.md`).

## Diseno

Arquitecto 20261030T1652Z sobre `origin/dev@0fedc7b`. Filtros duros: pasa
(dato del `.rec`: `PlayerLeave` en `Event`; sin red, sin dependencias, sin
migracion; cambia una metrica que se muestra, pero el humano lo decidio el
2026-10-28). Spike en el scratchpad, sin commitear: con la regla de abajo,
3000 rondas al azar sin abandonos dan el mismo 1vX que `pydissect.stats`
(625 con 1vX > 0), los escenarios de los criterios dan lo pedido y la suite
completa pasa salvo un dato de test que se corrige (punto 5 de Tests).
Skills: no aplica (el patron ya esta en `metrics.clutch_vs` y
`metrics.bajas_a_rivales`; arreglo con causa clara). Arena: no, una sola
forma obvia (la regla la fijo el humano, el lugar lo fijo la ficha 67).

**Implementar despues de que #68 se mergee**: pisa `recompute.py`,
`management/commands/recompute.py`, `test_recompute.py` y `metricas.md`
(otra fila). Prioriza, no bloquea.

**Alcance real.** El parser solo decodifica `PlayerLeave` de los mensajes de
texto, que Y9S1 dejo de emitir (`pydissect/events.py:292`). El arreglo cambia
partidas anteriores a Y9S1 con abandonos; en temporadas nuevas el abandono no
deja evento y el que se fue sigue contando como vivo. La fila de
`metricas.md` lo dice. La idea D3 de `ALCANCE.md` queda con el dato.

**Donde va la regla.** Como la 67: el parser sigue a r6-dissect
(`pydissect/stats.py` no se toca) y la app decide. Funcion nueva
`metrics.one_vx(eventos, team_of, ganador)`, unica implementacion, que usan el
import (`analyse_round`) y `recompute`. Lo importado se corrige sin reparsear:
`Event` guarda todo el feed, `PlayerLeave` incluido (`actor_name`), y
`Round.teams` guarda `won` de cada equipo desde el primer import (90a6746).
No hace falta `import_replays --force`.

**La regla** (port de `stats.player_round_stats`, lineas 99-137; cambios
marcados). Eventos planos `{"kind", "actor", "target"}` como `clutch_vs`; solo
cuentan los nicks de `team_of`.
1. `ganador` `None` (nadie gano, `.rec` cortado) se toma como 0, igual que
   r6-dissect (`1 if teams[1].won else 0`). No se cambia: seria redefinir el
   1vX sin decision del humano (P10).
2. Salidas, primer recorrido: `Kill` saca a `target`; `Death` y `PlayerLeave`
   sacan a `actor`. `salida[nick]` = indice del primer evento que lo saco.
   **Cambio:** `PlayerLeave` de alguien ya fuera (murio y despues se
   desconecto) no hace nada; `Kill`/`Death` sobre alguien que ya se fue no
   cuenta como salida ni como muerte. `ultima_muerte` = (indice, nick) del
   ultimo `Kill`/`Death` que cuenta, como `last_death` de r6-dissect (una baja
   repetida sobre el mismo jugador cuenta: paridad).
3. Ultimo en pie: si del ganador queda exactamente uno sin `salida`, es el.
   **Cambio (el arreglo):** antes era "no murio", ahora "no salio". Si no
   queda ninguno: `ultima_muerte`, si es del ganador **y** todos sus
   companeros salieron antes de ese evento (sin abandonos siempre se cumple:
   es la condicion de r6-dissect; con abandonos evita darle el clutch a quien
   murio con un companero en la ronda que despues se fue). Si no, nadie.
4. X, como r6-dissect: `quedan` arranca en el tamano del ganador y baja con
   cada evento que cuenta segun 2 sobre uno del ganador (todo `Kill` y `Death`,
   repetidos incluidos, salvo sobre alguien que ya se fue; el `PlayerLeave`
   solo si fue su salida). Cada `Kill` del ultimo en pie con `quedan < 2`
   (ya descontado ese mismo evento, como hoy) suma 1; al final, + rivales sin
   `salida`. **Cambio:** un rival que se fue ya no suma como vivo.
5. Devuelve todos los nicks de `team_of` en 0 salvo el ultimo en pie.

**Archivos** (y por que):
- `backend/replays/analytics/metrics.py`: `equipo_ganador(teams) -> int | None`
  (ultimo indice con `won`, `None` si ninguno; reemplaza el bucle de
  `analyse_round` en 283-286 para que import y `recompute` lean el ganador
  igual) y `one_vx(eventos, team_of, ganador: int | None) -> dict[str, int]`
  despues de `clutch_vs`, con docstring que diga en que difiere de
  r6-dissect. En `analyse_round` la linea 223 queda como valor inicial y,
  despues de `m["won"]` (317), `one_vx(events, team_of, winner)` pisa
  `metrics[nick]["one_vx"]`. Docstring del modulo: fila `one_vx`.
- `backend/replays/recompute.py`: `CAMPOS` suma `"one_vx"`; `_recompute_round`
  hace `one_vx(planos, team_of, equipo_ganador(rnd.teams))` (los `planos` ya
  traen `kind`, `actor` y `target`); docstrings del modulo y de `recompute()`.
- `backend/replays/management/commands/recompute.py`: docstring y `help`
  nombran el 1vX. El mensaje ya dice "(bajas, trades o clutch)": no cambia.
- `docs/metricas.md`: fila **1vX (clutch)**: "Rondas donde quedaste ultimo de
  tu equipo y ganaste. El `X` es la cantidad de rivales vivos cuando quedaste
  solo. Sigue la logica de r6-dissect con una diferencia: quien se fue de la
  partida (`PlayerLeave`), companero o rival, esta fuera de la ronda, como en
  Clutch: intentos y conversion. Sin ganador conocido cuenta el primer
  equipo, como en r6-dissect. Lo importado antes se corrige con `manage.py
  recompute`. Limite: el `.rec` trae `PlayerLeave` solo antes de Y9S1; desde
  ahi un abandono no deja rastro y el que se fue sigue contando como vivo."
  (con las tildes de la UI). En la fila de conversion, "el de `one_vx`, que
  r6-dissect calcula desde el final de la ronda" pasa a "el de `one_vx`, que
  se calcula desde el final de la ronda".

**Tests** (fallan sin el cambio salvo el de paridad, que fija lo que no cambia):
1. `backend/tests/test_clutch.py`, clase `OneVxTests`, 5v5 `A0..A4` (equipo 0,
   gana) contra `B0..B4`, eventos planos con `kill()` y un `leave()` nuevo:
   `test_un_companero_que_se_fue_no_cuenta_como_vivo` (criterio 1: A0-A2 matan
   a B0-B2, B3 mata a A0-A2, A3 se va, A4 mata a B3 y B4: A4 = 2, hoy 0);
   `test_un_rival_que_se_fue_no_suma_al_x` (criterio 2: B3 mata a A0-A3, B4 se
   va, A4 mata a B3: 1, r6-dissect da 2);
   `test_un_muerto_que_se_desconecta_no_cambia_nada` (mismo dict con y sin
   `PlayerLeave` de un companero ya muerto);
   `test_quien_se_fue_no_cobra_aunque_despues_figure_muerto` (A0-A3 muertos,
   A4 se va y despues `Death` de A4: todos 0);
   `test_si_un_companero_se_va_despues_de_la_ultima_muerte_nadie_cobra`
   (A0-A3 muertos, A4 se va al final: todos 0);
   `test_si_el_companero_se_fue_antes_el_ultimo_que_muere_cobra` (A4 se va
   primero, A0-A2 mueren, A3 mata a B1 y muere: A3 = 1 + 4);
   `test_sin_ganador_cuenta_el_equipo_cero_como_r6_dissect` (`None` = 0).
2. `test_clutch.py`, `ImportClutchTests`:
   `test_el_import_cuenta_el_clutch_con_un_companero_que_se_fue`: el
   escenario 1 por `analyse_round` con el `stats` del parser en `"1vX": 0`
   (lo que da r6-dissect): `one_vx` = 2.
3. `backend/tests/test_player_stats.py`: `test_sin_abandonos_da_lo_mismo_que_el_parser`
   (criterio 3): `random.Random(69)`, 3000 rondas sobre `LectorFalso` con
   ganador 0, 1 o ninguno (hoy `LectorFalso` solo arma 0/1: un indice fuera
   de rango sirve para "ninguno"), feed al azar de `Kill` (a veces repetida
   sobre el mismo jugador), `Death` (a veces de un nick que no esta) y
   `OperatorSwap`, sin `PlayerLeave`; normalizar con `EVENT_NAMES` y comparar
   con `metrics.one_vx`: cero diferencias, y `assertGreater` sobre las rondas
   con 1vX > 0 (625 en el spike) para que no pase vacio. Y
   `test_el_parser_sigue_contando_al_que_se_fue_como_vivo`: el escenario 1 en
   el parser da `{}` (sigue a r6-dissect, como el test de teamkills de la 67).
4. `backend/tests/test_recompute.py`, clase `RecomputeOneVxTests`: ronda de
   `make_round` con `rnd.teams` con `won` como la guarda el import (las
   factories no lo ponen), A0-A4 `won=True`, B0-B4 `won=False`, `make_event`
   del escenario 1 con `kind="PlayerLeave"` para A3 y `one_vx=0` guardado
   (criterio 4): `test_recompute_cuenta_el_clutch_con_un_companero_que_se_fue`
   (A4 = 2), `test_recompute_dry_run_cuenta_el_1vx_sin_escribir`,
   `test_recompute_de_1vx_es_idempotente`.
5. `ComandoTests.setUp`: el amigo lleva `one_vx=1`. No debilita el test: su
   comentario dice "como lo deja el import de hoy", y hoy r6-dissect ya le da
   1vX 1 (muero yo, queda 1v1 y mata al rival); sin el dato
   `test_sin_cambios_lo_dice` falla porque `recompute` ahora rehace `one_vx`.
   En el spike es el unico test existente que cambia.

**Orden:** tests 1-3 en rojo; `equipo_ganador` y `one_vx`; `analyse_round`;
`recompute`, comando y tests 4-5; `metricas.md`; `check.sh`.

**Que puede romperse.** `recompute` sobre la base real reescribe `one_vx`:
cambian solo rondas con abandonos (anteriores a Y9S1); `--dry-run` las cuenta.
`seed_demo` escribe `one_vx` directo y nadie corre `recompute` sobre la demo:
el e2e no se mueve. Sin `won` en `Round.teams` (solo datos sinteticos)
`equipo_ganador` da `None` y cuenta el equipo 0, como r6-dissect. Sin
migracion, sin frontend, sin build.

**Verificacion manual (QA).** Base de `factories` con la ronda del escenario 1
y `one_vx=0`: `manage.py recompute --dry-run` (1 fila), `recompute`, otra vez
`recompute` ("Nada que recalcular"), y `curl /api/matches/<id>/` muestra
`one_vx: 2` en la fila de A4. Va a `## Verificar en el PC`: `manage.py
backup`, `recompute --dry-run` y `recompute` sobre la base real.

**Fuera de alcance (anotado):** el teamkill del ultimo en pie, que r6-dissect
suma al X (la 67 no lo toco); rondas sin ganador, que siguen al equipo 0.
Tamano: unas 60 lineas de codigo y 150 de tests.

## Implementacion

Dev 20261103T0403Z-cYjVEvZ sobre `origin/dev@6aee89a`. #68 ya estaba en dev: sin espera.

Que quedo, segun el diseno:
- `metrics.equipo_ganador(teams)` y `metrics.one_vx(eventos, team_of, ganador)`
  (reglas 1-5 del diseno). `analyse_round` usa `equipo_ganador` para `winner`
  y pisa `one_vx` despues de `won`. Docstring del modulo con la fila `one_vx`.
- `recompute`: `CAMPOS` suma `one_vx`, `_recompute_round` llama a `one_vx`
  con `equipo_ganador(rnd.teams)`; docstrings del modulo, de `recompute()`, y
  docstring y `help` del comando.
- `docs/metricas.md`: fila **1vX (clutch)** y la frase de la fila de
  conversion.

Tests (nombres de los criterios):
- Criterio 1: `test_clutch.OneVxTests.test_un_companero_que_se_fue_no_cuenta_como_vivo`
  e `ImportClutchTests.test_el_import_cuenta_el_clutch_con_un_companero_que_se_fue`
  (por `analyse_round`, con el `stats` del parser en 0).
- Criterio 2: `test_un_rival_que_se_fue_no_suma_al_x` (da 1; r6-dissect 2).
  Desvio: el escenario del diseno no decia que pasaba con B0-B2; el test los
  mata primero (A0-A2 matan a B0-B2) para que el numero sea el 1 del diseno.
- Resto de la regla: `test_un_muerto_que_se_desconecta_no_cambia_nada`,
  `test_quien_se_fue_no_cobra_aunque_despues_figure_muerto`,
  `test_si_un_companero_se_va_despues_de_la_ultima_muerte_nadie_cobra`,
  `test_si_el_companero_se_fue_antes_el_ultimo_que_muere_cobra` (A3 = 5),
  `test_sin_ganador_cuenta_el_equipo_cero_como_r6_dissect`,
  `test_el_ganador_es_el_ultimo_equipo_con_won`.
- Criterio 3: `test_player_stats.OneVxParidadTests.test_sin_abandonos_da_lo_mismo_que_el_parser`
  (`Random(69)`, 3000 rondas, ganador 0/1/ninguno, bajas repetidas, `Death` de
  nick desconocido, `OperatorSwap`; cero diferencias y mas de 300 rondas con
  1vX) y `test_el_parser_sigue_contando_al_que_se_fue_como_vivo`. El revisor
  ciego corrio ademas un fuzz de 50.000 rondas con equipos de 1 a 5 y tamanos
  distintos: cero diferencias.
- Criterio 4: `test_recompute.RecomputeOneVxTests` (`..._cuenta_el_clutch_...`,
  `..._dry_run_cuenta_el_1vx_sin_escribir`, `..._de_1vx_es_idempotente`).
  `ComandoTests.setUp`: el amigo lleva `one_vx=1` (punto 5 del diseno).
- Criterio 5: la fila de `metricas.md`.

Test que falla primero (`tipo: bug`): `git stash -- replays` y
`manage.py test tests.test_clutch` da `ImportError` (no existe `one_vx`); el
comportamiento viejo lo fija `test_el_parser_sigue_contando_al_que_se_fue_como_vivo`,
que da `{}` en el escenario 1 donde la app ahora da `{"A4": 2}`.

Revision ciega (omc-code-reviewer via general-purpose, el tipo no cargo al
arrancar): 0 CRITICAL/HIGH. Arreglados: MEDIUM, la fila de `metricas.md`
decia "rivales vivos cuando quedaste solo" y "como en Clutch", pero el `X`
(de r6-dissect) se cuenta desde el final, y un rival que se va con vos ya
solo no suma (lo pide el criterio 2): la fila ahora lo dice. LOW: el fixture
de `test_un_muerto_que_se_desconecta_no_cambia_nada` no detectaba un doble
descuento; cambiado por uno que si (da 4, sin la guarda daria 5). No
arreglado (LOW, previo): nicks repetidos en una ronda se juntan en `team_of`,
como en todas las metricas que lo usan.

Sin migracion, sin frontend, sin cambios en `seed_demo`.

Skills: no aplica (el diseno ya resolvio el dominio).
OMC: plan=— · revisión=3 hallazgos (2 arreglados) · verificación=—

## Revision 2026-11-03 sobre 42bad97

Revisor 20261103T0804Z-chGRfoT. Rama ya al dia con `origin/dev@6aee89a`; `verificar.sh`:
VERDE 42bad97 (873 tests backend, 153 vitest, 54 e2e).

Revision a ciegas, dos ejes (diff de ~520 lineas):
- Estandares (omc-code-reviewer via general-purpose): 0 CRITICAL/HIGH/MEDIUM.
  - [estilo] LOW `backend/replays/analytics/metrics.py:305`: `analyse_round`
    sigue inicializando `"one_vx": int(s.get("1vX", 0))` del parser, que
    `one_vx(...)` siempre pisa (devuelve una clave por nick de `team_of`, los
    mismos de `metrics`). Confirmado leyendo el codigo. El diseno lo deja asi
    a proposito ("queda como valor inicial"); no cambia ningun numero.
    Arreglo opcional: inicializar en 0 como `clutch_vs`.
- Intencion (contra que gana, criterios y fuera de alcance): aprobar.
  - [intencion] LOW `backend/pydissect/events.py:292`: la ganancia se limita
    a replays anteriores a Y9S1 (el parser no emite `PlayerLeave` desde ahi).
    Ya esta en la fila de `metricas.md` y en el Diseno; va a la descripcion
    del PR para que el humano no espere cambios en partidas recientes.

Confirmado por el lider, ademas de los subagentes:
- `Round.teams` guarda `won` desde `0001_initial` / `ingest.py:217-226`, asi
  que `recompute` lee el ganador real en todo lo importado (sin `won`
  cambiaria clutch del equipo 1 al 0: no pasa).
- Los `Event` guardados traen `kind="PlayerLeave"` y `actor_name` con el nick
  (`pydissect/events.py:301-311`, `ingest.py:284`): alcanza sin reparsear.
- `one_vx` se lee al consultar solo para agregar (`aggregates.py:131,174,445,1687`,
  `views.py:483,590`, `narrative.py:155`): Clutch, record, rating y narrativa
  toman el valor nuevo sin cambios.

Criterios: 1 (`OneVxTests.test_un_companero_que_se_fue_no_cuenta_como_vivo`,
`ImportClutchTests.test_el_import_cuenta_el_clutch_con_un_companero_que_se_fue`),
2 (`test_un_rival_que_se_fue_no_suma_al_x`), 3
(`OneVxParidadTests.test_sin_abandonos_da_lo_mismo_que_el_parser`, 3000
rondas, no pasa vacio), 4 (`RecomputeOneVxTests`, tres tests), 5 (fila de
`metricas.md`): cubiertos. `archivos:` coincide con el diff. Sin tildes en
identificadores, sin `print`/`console.log`, sin dependencias, sin frontend.

Veredicto: aprobar -> `revisado`.

Skills: no aplica.
OMC: plan=— · revisión=2 hallazgos LOW (0 arreglados, ninguno bloquea) · verificación=—

## QA 2026-11-03 sobre d0a2649

QA 20261103T1205Z-cZPEnjG. Rama al dia con `origin/dev@6aee89a` (merge-tree sin conflicto).

- `verificar.sh` (check.sh completo): VERDE d0a2649 en 122 s, 873 tests
  backend, 153 vitest, 54 e2e.
- Base sembrada (script en el scratchpad, `SQLITE_PATH` temporal, nada al
  repo) con `factories`: escenario 1 (A0-A2 matan a B0-B2, B3 mata a A0-A2,
  A3 `PlayerLeave`, A4 mata a B3 y B4) y escenario 2 (B3 mata a A0-A3, B4
  `PlayerLeave`, A4 mata a B3), `one_vx` de A4 en 0 como el import viejo:
  - `manage.py recompute --dry-run`: "cambiarian 2 filas de jugador ... sobre 2 rondas".
  - `manage.py recompute`: "se actualizaron 2 filas"; otra vez: "Nada que
    recalcular ... las 2 rondas ya estan al dia" (idempotente).
  - `one_vx` de A4: escenario 1 = 2 (criterio 1), escenario 2 = 1 (criterio 2).
  - `runserver` + `curl /api/matches/1/`: A4 `one_vx: 2`, scoreboard
    `clutches: 1`. Con A4 como `is_me`: `/api/overview/` `clutch_rounds: 2`,
    `records.biggest_clutch.value: 2`; `/api/teammates/` `clutch_conversion`
    1v2 2/2 (no cambia: ya tomaba `PlayerLeave`).
  - Bordes: `/api/overview/?until=foo`, `/api/matches/?page=-1`,
    `/api/matches/?map=`, `/api/sessions/?days=99999999999`, `/api/coach/`,
    `/api/trends/`, `/api/compare/`, `/api/players/1/`,
    `/api/export/?table=rounds`: 200; `/api/matches/999/`: 404.
- Base vacia: `recompute` "Nada que recalcular ... 0 rondas"; `/api/overview/`,
  `/api/matches/`, `/api/teammates/` 200.
- Sin migracion, sin frontend (chunk sin cambios), sin parser (`pydissect/` no se toca).
- Mutacion (`tests.test_clutch tests.test_recompute tests.test_player_stats`,
  restaurado despues): M1 `PlayerLeave` ignorado en `one_vx` -> 10 fallan;
  M2 rival que se fue suma al X -> 2 fallan (`test_un_rival_que_se_fue_no_suma_al_x`);
  M3 sin la guarda `all(salida[n] < i ...)` -> 2 fallan
  (`test_si_un_companero_se_va_despues_de_la_ultima_muerte_nadie_cobra`);
  M4 `one_vx` fuera de `CAMPOS` de `recompute` -> 3 de `RecomputeOneVxTests` fallan.
- omc-verifier (general-purpose con su cuerpo): PASS, 5/5 VERIFIED; corrio
  ademas un fuzz de paridad de 200.000 rondas sin abandonos contra
  `pydissect.stats`: 0 diferencias.

Veredicto: `aprobado`.

Skills: no aplica.
OMC: plan=— · revisión=— · verificación=PASS

## Verificar en el PC

- `manage.py backup`, `manage.py recompute --dry-run` (cuenta las filas de
  jugador que cambian; solo partidas anteriores a Y9S1 con abandonos) y
  `manage.py recompute` sobre la base real.

## Pendiente

## Para el humano

Sin decision pendiente (la tomaste el 2026-10-28).
