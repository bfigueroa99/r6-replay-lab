# 69. El 1vX cuenta cuando un compañero se fue

estado: disenado
candado: -
rama: -
tipo: bug
epica: -
area: backend
prioridad: 2
fuente: decision del humano 2026-10-28 en `## Para el equipo` de `ESTADO.md` (pregunta de la ficha 31); `pydissect/stats.py:100-104` arma `winners_alive` solo con `died`, que `PlayerLeave` no marca
archivos: backend/replays/analytics/metrics.py, backend/replays/recompute.py, backend/replays/management/commands/recompute.py, backend/tests/test_clutch.py, backend/tests/test_player_stats.py, backend/tests/test_recompute.py, docs/metricas.md
turnos: po 20261029T0004Z, arquitecto 20261030T1652Z

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

## Revision <fecha> sobre <sha>

## QA <fecha> sobre <sha>

## Verificar en el PC

## Pendiente

## Para el humano

Sin decision pendiente (la tomaste el 2026-10-28).
