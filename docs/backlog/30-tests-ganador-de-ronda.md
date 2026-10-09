# 30. Tests de quien gana la ronda y por que

estado: aprobado
candado: release 2026-10-09T00:04Z
rama: claude/equipo-dev/30-tests-ganador-de-ronda
area: parser
prioridad: 2
fuente: hueco de tests en pydissect: `events.round_end` y `events.read_defuser_timer` no tienen ningun test (main dc0188b; el unico que los ejercita es `RealReplayTests`, que se salta sin `R6_TEST_REPLAY`)
archivos: backend/tests/test_round_end.py
turnos: po 20261008T0302Z, arquitecto 20261008T0602Z, dev 20261008T0902Z, revisor 20261008T1202Z, qa 20261008T1802Z

## PR

(La escribe el Release manager al final: titulo `[equipo-dev][area] Titulo`,
cuerpo segun `.claude/skills/equipo-dev/plantilla-pr.md` y una seccion
"Como probarlo en 2 minutos" con comandos exactos.)

## Que gana quien usa la app

El winrate, la condicion de victoria de cada ronda y las rondas "por tiempo"
salen de `round_end`; hoy un cambio en esa funcion o en el reloj del defuser
pasa la suite en verde aunque deje de atribuir bien las rondas. Con estos tests
un refactor del parser o el soporte de una temporada nueva no puede romper el
ganador de la ronda en silencio.

## Criterios de aceptacion

Todos con un lector falso (objeto con `players`, `teams`, `header`,
`code_version`, `match_feedback` y `player_index_by_username`), sin `.rec`. Los cuatro primeros y el ultimo se verificaron contra main dc0188b:

- [ ] Version previa a Y9S4: los 5 de un equipo mueren (KILL o DEATH) ->
      el otro equipo queda `won=True` con `winCondition == "KilledOpponents"`.
- [ ] Version previa a Y9S4: hay `DEFUSER_PLANT_COMPLETE` y nadie lo
      desactiva -> gana el equipo del que planto con `"DefusedBomb"`; si
      despues hay `DEFUSER_DISABLE_COMPLETE`, gana el equipo del que desactivo
      con `"DisabledDefuser"`.
- [ ] Version previa a Y9S4 sin muertes completas ni defuser -> gana el
      equipo con `role == "Defense"` con `"Time"`.
- [ ] Version Y9S4 o posterior en modo bomba: el ganador sale de
      `startingScore < score` del equipo 0 (el equipo 1 queda con el valor
      contrario); si el perdedor perdio a todos sus jugadores la condicion es
      `"KilledOpponents"`, si no `"Time"`.
- [ ] `read_defuser_timer` con un lector falso que entrega timers `"7.00"` y
      `"0.00"`: la primera secuencia agrega `DEFUSER_PLANT_START` y despues
      `DEFUSER_PLANT_COMPLETE` y deja `planted=True`; una segunda secuencia
      sobre el mismo lector agrega `DEFUSER_DISABLE_START` y
      `DEFUSER_DISABLE_COMPLETE`.
- [ ] Un KILL con `usernameFromScoreboard` queda con `username` corregido
      despues de `round_end`.

## Fuera de alcance

- Cambiar el comportamiento de `round_end`. Si un test destapa un bug (por
  ejemplo: en Y9S4+ un `DEFUSER_DISABLE_COMPLETE` pone `won=True` al que
  desactivo sin poner `False` al otro equipo, que ya venia marcado por el
  marcador), se documenta con el test que lo muestra en `## Para el humano` y
  se propone como ficha aparte; no se arregla aca.
- Stats por jugador y 1vX: eso es la ficha 31.
- Fixtures binarias o `.rec` reales.

## Diseno

(Arquitecto 20261008T0602Z, sobre main dc0188b. Cada numero de abajo se corrio
en un spike contra el parser de main; ninguno es supuesto.)

**Archivos:** uno solo, nuevo: `backend/tests/test_round_end.py`. No se toca
`pydissect/` (fuera de alcance) ni `test_pydissect.py`, para que esta ficha y
la 31 se puedan implementar en paralelo sin pisarse. Sin migracion, sin
frontend, sin fila en `docs/metricas.md` (no hay numero nuevo).

**Lector falso** (clase `LectorFalso` en el mismo archivo, ~25 lineas). Reusa
los accesos del `Reader` real tomandolos como atributos de clase, asi el test
ejercita exactamente la misma logica de indices y propiedades:

```python
class LectorFalso:
    players = Reader.players            # properties sobre self.header
    teams = Reader.teams
    code_version = Reader.code_version
    player_index_by_id = Reader.player_index_by_id
    player_index_by_username = Reader.player_index_by_username
    skip = Reader.skip                  # primitivas sobre self.b / self.offset
    bytes = Reader.bytes
    int = Reader.int
    string = Reader.string
```

`__init__(self, version=Y9S3, roles=(ATTACK, DEFENSE), score=(0, 0),
telemetria=b"")` arma `header` con `codeVersion`, `gamemode=BOMB`, 10
jugadores `A0..A4` (teamIndex 0) y `B0..B4` (teamIndex 1) con
`dissectID = bytes([equipo, n, 0, 0])`, y `teams` con `role`,
`startingScore=0`, `score`, `won=False`, `winCondition=""`. Ademas
`match_feedback=[]`, `time=0.0`, `time_raw=""`, `planted=False`,
`last_defuser_player_index=-1`, `b=telemetria`, `offset=0`. Helper
`kill(autor, victima)` que devuelve el dict de KILL.

**Tests** (`class RoundEndTests(SimpleTestCase)` y
`class DefuserTimerTests(SimpleTestCase)`), con lo que devuelve main hoy:

1. `test_previo_y9s4_cinco_muertes_da_la_ronda_al_rival_por_eliminacion`:
   `B0` mata `A0..A4` -> `teams == [(False, ""), (True, "KilledOpponents")]`
   (comparar `(won, winCondition)` de cada equipo).
2. `test_previo_y9s4_muertes_por_death_tambien_cuentan`: cinco eventos
   `DEATH` con `username` `A0..A4` -> equipo 1 gana con `"KilledOpponents"`.
3. `test_previo_y9s4_plant_sin_desactivar_gana_el_que_planto`:
   `DEFUSER_PLANT_COMPLETE` de `A0` -> `(True, "DefusedBomb")` para el 0.
4. `test_previo_y9s4_desactivar_despues_del_plant_gana_el_que_desactivo`:
   plant de `A0` y despues `DEFUSER_DISABLE_COMPLETE` de `B0` ->
   `[(False, ""), (True, "DisabledDefuser")]`.
5. `test_previo_y9s4_sin_muertes_ni_defuser_gana_la_defensa_por_tiempo`:
   roles `(ATTACK, DEFENSE)` -> equipo 1 `(True, "Time")`; y con roles
   `(DEFENSE, ATTACK)` -> equipo 0 `(True, "Time")` (dos asserts o
   `subTest`, para que no pase solo por ser el indice 1).
6. `test_y9s4_el_marcador_decide_y_la_eliminacion_da_la_condicion`:
   version `Y9S4`, `score=(1, 0)`, `A0` mata `B0..B4` ->
   `[(True, "KilledOpponents"), (False, "")]`.
7. `test_y9s4_sin_eliminacion_la_condicion_es_tiempo`: version `Y9S4`,
   `score=(0, 1)`, sin eventos -> `[(False, ""), (True, "Time")]`. Esto
   cubre ademas que el equipo 1 recibe el valor contrario al 0.
8. `test_kill_corregida_por_el_marcador_toma_el_autor_del_marcador`: KILL
   `B0 -> A0` con `usernameFromScoreboard="B1"` -> despues de `round_end`
   el dict tiene `username == "B1"`.
9. `test_defuser_plant_y_despues_desactivar` (DefuserTimerTests). Telemetria
   = cuatro bloques `bytes([len(t)]) + t + b"\0" * 34 + dissect_id`, con
   `t` = `b"7.00"`, `b"0.00"` (id de `A0`), `b"7.00"`, `b"0.00"` (id de
   `B1`), **mas un byte de relleno al final** (`Reader.skip` lanza
   `EndOfFile` si el offset llega justo al final). Dos llamadas a
   `events.read_defuser_timer` -> tipos y autores en `match_feedback` ==
   `[(PLANT_START, "A0"), (PLANT_START, "A0"), (PLANT_COMPLETE, "A0")]` y
   `planted is True`. Ojo: el criterio de la ficha dice "agrega START y
   despues COMPLETE"; en main cada lectura del timer agrega un START, asi que
   son dos START. Se afirma la lista exacta. Dos llamadas mas -> la lista
   sigue con `[(DISABLE_START, "B1"), (DISABLE_START, "B1"),
   (DISABLE_COMPLETE, "B1")]`.
10. `test_defuser_con_id_desconocido_no_agrega_eventos`: un solo bloque
    `"0.00"` con id `bytes([9, 9, 9, 9])` -> `match_feedback == []`. Main
    deja `planted is True` igual (marca el plant aunque no sepa quien); el
    test lo afirma tal cual, con un comentario de una linea que explica por
    que (el plant existio aunque el autor no se pueda atribuir).

**Orden:** clase falsa -> tests 1 a 8 -> 9 y 10 -> `ruff check backend` ->
`manage.py test tests.test_round_end` -> `check.sh`.

**Que puede romperse:** nada en runtime (solo tests). Riesgo real: que el
falso diverja del `Reader` si cambian sus atributos; por eso se toman los
metodos del `Reader` y no copias. Los atributos `bytes` e `int` pisan
builtins dentro de la clase; `ruff.toml` no selecciona las reglas `A`, asi
que no hace falta `noqa`.

**No va como test:** el bug de Y9S4 con `DEFUSER_DISABLE_COMPLETE` (ver
`## Para el humano`). Un test que afirme un comportamiento incorrecto lo
congelaria; uno que afirme el correcto fallaria. Queda documentado aca y
para una ficha aparte.

**Verificacion manual:** `cd backend && python manage.py test
tests.test_round_end -v 2` -> 10 tests ok. Prueba de mutacion sugerida para
QA: cambiar `TIME` por `KILLED_OPPONENTS` en la rama de Y9S4 de `round_end` y
ver caer el test 7; invertir `r.planted = True` y ver caer el 9.

**Tamano:** ~150 lineas de test. Cabe holgado en un turno de Dev.

## Implementacion

(Dev 20261008T0902Z, sobre main dc0188b, commits a63d828 y a65069c)

Quedo: `backend/tests/test_round_end.py` con `LectorFalso` (accesos tomados de
`Reader`), `RoundEndTests` (9 tests) y `DefuserTimerTests` (2). 11 tests,
todos verdes; ningun archivo fuera de `archivos:`.

Criterio -> test:
- 5 muertes (KILL) -> `test_previo_y9s4_cinco_muertes_da_la_ronda_al_rival_por_eliminacion`;
  por DEATH -> `test_previo_y9s4_muertes_por_death_tambien_cuentan`.
- plant / desactivar -> `test_previo_y9s4_plant_sin_desactivar_gana_el_que_planto`,
  `test_previo_y9s4_desactivar_despues_del_plant_gana_el_que_desactivo`.
- defensa por tiempo (los dos ordenes de roles, con `subTest`) ->
  `test_previo_y9s4_sin_muertes_ni_defuser_gana_la_defensa_por_tiempo`.
- Y9S4+ -> `test_y9s4_el_marcador_decide_y_la_eliminacion_da_la_condicion`,
  `test_y9s4_sin_eliminacion_la_condicion_es_tiempo`,
  `test_y9s4_el_marcador_gana_aunque_el_feed_diga_eliminacion`.
- reloj del defuser -> `test_defuser_plant_y_despues_desactivar`,
  `test_defuser_con_id_desconocido_no_agrega_eventos`.
- autor corregido por el marcador -> `test_kill_corregida_por_el_marcador_toma_el_autor_del_marcador`.

Desvios del diseno:
- Tests 6 y 7 del diseno cambiados: la revision ciega mostro que con los
  datos del diseno (`score=(1,0)` + A mata a los B; `score=(0,1)` sin eventos)
  la logica previa a Y9S4 da el mismo resultado, asi que pasaban aunque se
  anulara la rama del marcador. Ahora el feed apunta al equipo contrario al
  marcador (mueren los diez con `score=(1,0)`; atacante gana por tiempo con
  `score=(1,0)`), y se agrego un test 11 (`..._el_marcador_gana_aunque_el_feed_diga_eliminacion`,
  el caso que sugirio la revision).
- `zip(..., strict=True)` en el falso porque ruff selecciona B905.

Mutaciones corridas (y revertidas): `TIME` -> `KILLED_OPPONENTS` en la rama
Y9S4 tira 1 test; `r.planted = True` -> `False` en `read_defuser_timer` tira
2; `if r.code_version >= Y9S4:` -> `if False:` tira los 3 de Y9S4.

No se toco `pydissect/` (fuera de alcance). El bug de Y9S4 con
`DEFUSER_DISABLE_COMPLETE` sigue en `## Para el humano`, sin test.

Verificacion: `check.sh` -> `Todo en verde.` (377 tests backend, 53 vitest,
build ok, 17 e2e) sobre a65069c.

## Revision 2026-10-08 sobre 0de3a3c

(Revisor 20261008T1202Z. Revision ciega con `revision.md` sobre el diff sin
`docs/backlog`; cada hallazgo confirmado con mutacion por el lider.)

Hallazgos:

- [test] backend/tests/test_round_end.py (tests de Y9S4)
  Que pasa: los tres tests de Y9S4 usan `score=(1, 0)` con `startingScore=0`:
  siempre gana el equipo 0 y nunca se compara contra un marcador inicial
  distinto de cero.
  Como reproducirlo: en `pydissect/events.py`, `team0_won = True` o
  `team0_won = r.teams[0]["score"] > 0` dejan la suite de la rama en verde. La
  segunda es un bug realista: desde la segunda ronda el equipo que ya trae
  puntos apareceria ganando rondas que perdio.
  Arreglo: lo agrega el revisor (tests de casos borde, pasan en main):
  `test_y9s4_gana_el_equipo_1_si_el_marcador_del_0_no_sube` (`score=(0, 1)`,
  defensa en el 0 para que la logica previa diera lo contrario) y
  `test_y9s4_el_marcador_se_compara_contra_el_inicial_de_la_ronda` (2 -> 2
  contra 1 -> 2). Con `team0_won = True` caen los dos; con `score > 0` cae el
  segundo; sin mutacion pasan.

Sin hallazgos de reglas, formato ni estilo: un solo archivo de test nuevo,
dentro de `archivos:`, sin tildes en identificadores, sin `print`, sin tocar
`pydissect/`. Nota sin hallazgo: los cambios al conteo de `sizes` (equipos de
menos de 5) no los detecta ningun test, pero ninguno lo promete.

Criterios de aceptacion: los seis cubiertos por tests con nombre (ver
Implementacion), ahora 13 tests en el archivo.

`check.sh` -> `Todo en verde.` sobre 0de3a3c (antes de agregar tests) y
sobre el commit de esta revision.

Veredicto: aprobar (el unico hallazgo quedo cubierto por los tests que agrego
el revisor) -> `revisado`.

## QA 2026-10-08 sobre 6e48e43

(QA 20261008T1802Z. La rama ya contiene `origin/main` dc0188b; sin `.env`.)

Suite y pasos de `ci.yml`, tal cual:

- `./scripts/check.sh` (el de `origin/claude/great-cray-7o9tvf`) sobre
  6e48e43 -> `Todo en verde.`: ruff `All checks passed!`, `Ran 379 tests ...
  OK (skipped=4)`, vitest 53 passed, build ok, e2e 17 passed. Ese script
  corre `ruff check backend`, `manage.py test tests` sin `.env`, `npm test`
  y `npm run build`, los pasos de `ci.yml`.
- `cd backend && python manage.py test tests.test_round_end tests.test_pydissect -v 2`
  -> 31 tests ok, 1 skipped (`RealReplayTests`, sin `R6_TEST_REPLAY`): la
  fixture sintetica del parser sigue verde.

Endpoints y base: la rama solo agrega un archivo de test; no toca vistas,
modelos, migraciones, `frontend/src` ni `pydissect/`. `runserver` + `curl`,
migracion y tamano del chunk no aplican (el e2e de `check.sh` levanto la app
sembrada y paso).

Criterios:

- [x] previo a Y9S4, 5 muertes -> `..._cinco_muertes_da_la_ronda_al_rival_por_eliminacion`
      y `..._muertes_por_death_tambien_cuentan` ok.
- [x] plant / desactivar -> `..._plant_sin_desactivar_gana_el_que_planto`,
      `..._desactivar_despues_del_plant_gana_el_que_desactivo` ok.
- [x] defensa por tiempo, los dos ordenes de roles -> `..._sin_muertes_ni_defuser_gana_la_defensa_por_tiempo` ok.
- [x] Y9S4+ en bomba -> los cinco `test_y9s4_*` ok.
- [x] reloj del defuser -> `test_defuser_plant_y_despues_desactivar`,
      `test_defuser_con_id_desconocido_no_agrega_eventos` ok.
- [x] autor corregido por el marcador -> `test_kill_corregida_por_el_marcador_toma_el_autor_del_marcador` ok.

Mutaciones propias en `backend/pydissect/events.py` (distintas de las del Dev
y el Revisor; cada una con `manage.py test tests.test_round_end` y
revertida, `git status` limpio despues):

| mutacion | cae |
|---|---|
| no copiar `usernameFromScoreboard` a `username` | `test_kill_corregida_...` |
| `DEATH` no suma muertes | 2 tests |
| sin `return` despues del plant (sigue a la regla de tiempo) | `..._plant_sin_desactivar_gana_el_que_planto` |
| eliminacion Y9S4 con `>` en vez de `>=` | `test_y9s4_el_marcador_decide_y_la_eliminacion_da_la_condicion` |
| tiempo siempre al equipo 1 (`i = 1`) | `..._gana_la_defensa_por_tiempo` (subTest `Defense, Attack`) |
| el reloj no agrega `*_START` | `test_defuser_plant_y_despues_desactivar` |
| `DISABLE_COMPLETE` sin `return` | `..._desactivar_despues_del_plant_gana_el_que_desactivo` |
| cualquier timer completa (`if not timer.startswith("0.00")` -> `if False`) | `test_defuser_plant_y_despues_desactivar` |
| Y9S4 sin el chequeo `gamemode == BOMB` | **ninguno** con los tests de la rama |
| Y9S4 sin `and not any(t["winCondition"] ...)` | ninguno: mutante equivalente (en Y9S4 solo el plant y el disable ponen condicion, y los dos hacen `return` antes) |

Para la del modo agregue el test de borde
`test_y9s4_fuera_de_bomba_el_marcador_decide_sin_inventar_condicion`
(Y9S4, `SecureArea`, `score=(1, 0)`, A0 mata B0..B4 ->
`[(True, ""), (False, "")]`). Pasa sobre main; sin el chequeo del modo cae
(pone `KilledOpponents`). Afirma lo que el codigo ya hace a proposito: las
condiciones de victoria se deducen con reglas de bomba. `ruff check backend`
limpio, `ruff format --check` sin cambios. 14 tests en el archivo.

`check.sh` -> `Todo en verde.` tambien sobre el commit de esta QA.

Veredicto: `aprobado`.

## Verificar en el PC

No hace falta: solo agrega tests; no toca parser, migraciones, `recompute`,
Electron ni `.ps1`. Para repetir: `cd backend; python manage.py test
tests.test_round_end -v 2` -> 14 tests ok.

## Pendiente

## Para el humano

- (Arquitecto 20261008T0602Z, aviso, no bloquea) Bug confirmado en main
  dc0188b: en version `Y9S4` o posterior, con `score=(1, 0)` (gano el equipo 0
  segun la cabecera) y un `DEFUSER_DISABLE_COMPLETE` de un jugador del equipo
  1, `round_end` deja **los dos** equipos con `won=True`
  (`[(True, ""), (True, "DisabledDefuser")]`). El `return` dentro del bucle
  sale antes de que nadie apague al otro. Que la cabecera y el feed se
  contradigan es raro, pero si pasa la ronda cuenta como ganada por ambos.
  Queda para que el PO lo proponga como ficha aparte (decidir cual manda en
  Y9S4+: la cabecera o el feed). No entra en esta ficha.
