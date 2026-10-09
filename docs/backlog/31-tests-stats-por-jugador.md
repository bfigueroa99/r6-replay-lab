# 31. Tests de stats por jugador: 1vX, headshots y agregado por partida

estado: aprobado
candado: release 2026-10-09T00:04Z
rama: claude/equipo-dev/31-tests-stats-por-jugador
area: parser
prioridad: 3
fuente: hueco de tests en pydissect: `stats.player_round_stats` (incluido el calculo de 1vX) y `stats.player_match_stats` no tienen ningun test unitario (main dc0188b)
archivos: backend/tests/test_player_stats.py
turnos: po 20261008T0302Z, arquitecto 20261008T0602Z, dev 20261008T0902Z, revisor 20261008T1202Z, qa 20261008T1802Z

## PR

(La escribe el Release manager al final: titulo `[equipo-dev][area] Titulo`,
cuerpo segun `.claude/skills/equipo-dev/plantilla-pr.md` y una seccion
"Como probarlo en 2 minutos" con comandos exactos.)

## Que gana quien usa la app

Los clutch (1vX), las kills, las muertes y el % de headshots que muestran el
Resumen, Operadores y la pagina de jugador salen de estas dos funciones, y la
logica del 1vX es la mas enredada del parser. Con tests, un cambio ahi deja de
poder inflar o borrar clutches sin que la suite lo note.

## Criterios de aceptacion

Con un lector falso (`players`, `teams`, `scoreboard`, `match_feedback`),
sin `.rec`. Los numeros esperados se verificaron contra main dc0188b:

- [ ] Gana el equipo 1; B0-B3 mueren, B4 mata a A0, A1 y A2 y A3/A4 siguen
      vivos -> B4 tiene `1vX == 5` (3 kills con su equipo ya reducido a el,
      mas 2 rivales vivos), `kills == 3`, `died == False`; nadie mas tiene 1vX.
- [ ] Gana el equipo 0; A0-A3 mueren y A4 mata al ultimo rival -> A4 tiene
      `1vX == 1`.
- [ ] El equipo ganador no pierde a nadie -> ningun jugador tiene 1vX.
- [ ] El ultimo sobreviviente del equipo ganador muere al final (ronda ganada
      por plant): A0-A3 mueren, A4 mata a B0 y despues B1 mata a A4, gana el
      equipo 0 -> A4 tiene `1vX == 5` (1 kill mas 4 rivales vivos; rama
      `last_death_was_winner`).
- [ ] `headshotPercentage` por ronda: 1 headshot en 2 kills -> `50.0`; 0
      kills -> `0.0` sin dividir por cero.
- [ ] `player_match_stats` sobre dos rondas iguales de un jugador con 2 kills
      (1 headshot) -> `rounds == 2`, `kills == 4`, `headshots == 2`,
      `headshotPercentage == 50.0`; una ronda con `died=True` suma 1 a
      `deaths`; `assists` suma `assistsFromRound` del scoreboard.

## Fuera de alcance

- Cambiar el calculo de 1vX. Si un test muestra un caso dudoso (por ejemplo,
  un `PLAYER_LEAVE` del equipo ganador), se deja escrito en `## Para el
  humano` con el input exacto y se propone ficha aparte.
- Quien gana la ronda (`round_end`): es la ficha 30.
- Las metricas derivadas de `analytics/metrics.py` (rating, trades): ya
  tienen sus tests.

## Diseno

(Arquitecto 20261008T0602Z, sobre main dc0188b. Los numeros de abajo salen de
correr cada escenario contra `stats.py` de main en un spike.)

**Archivos:** uno solo, nuevo: `backend/tests/test_player_stats.py`. No se
toca `pydissect/` ni `test_pydissect.py` (asi no choca con la ficha 30, que
crea `test_round_end.py`). Sin migracion, sin frontend, sin fila en
`docs/metricas.md` (los numeros ya existen y ya tienen fila).

**Lector falso** en el mismo archivo, sin primitivas de bytes (aca no se
leen): `class LectorFalso` con `players = Reader.players` y
`teams = Reader.teams` como atributos de clase (properties del `Reader` real
sobre `self.header`), y `__init__(self, ganador)` que arma `header` con 10
jugadores `A0..A4` (teamIndex 0) y `B0..B4` (teamIndex 1), `teams` con
`won = (i == ganador)`, `match_feedback=[]` y `scoreboard` con 10 dicts
`{"score": 0, "assistsFromRound": 0}`. Helpers `kill(autor, victima,
headshot=False)` y `de(stats, username)` que devuelve el dict del jugador.
No se comparte con la ficha 30 a proposito: son ~15 lineas y compartirlas
obligaria a mergear una antes de la otra.

**Tests** (`class PlayerRoundStatsTests(SimpleTestCase)` y
`class PlayerMatchStatsTests(SimpleTestCase)`):

1. `test_ultimo_vivo_que_gana_suma_sus_kills_y_los_rivales_vivos`: gana el
   1; `A0` mata `B0..B3`, despues `B4` mata `A0`, `A1`, `A2` -> `B4` con
   `1vX == 5`, `kills == 3`, `died is False`; todos los demas con `1vX == 0`.
2. `test_uno_contra_uno_ganado_vale_uno`: gana el 0; `A0` mata `B0..B3`,
   `B4` mata `A0..A3`, `A4` mata `B4` -> `A4` con `1vX == 1`. Ojo, desvio
   del criterio de la PO: "A0-A3 mueren y A4 mata al ultimo rival" es
   ambiguo; si `A4` mata a los 5 rivales el resultado es 5, no 1. Este es el
   escenario que da 1 y el que hay que escribir.
3. `test_sin_bajas_en_el_ganador_no_hay_1vx`: gana el 0; `A0` mata
   `B0..B4` -> ningun jugador con `1vX` distinto de 0.
4. `test_el_ultimo_del_ganador_que_muere_igual_cobra_el_1vx`: gana el 0
   (ronda ganada por plant); `B0` mata `A0..A3`, `A4` mata `B0`, `B1` mata
   `A4` -> `A4` con `1vX == 5`, `died is True` (rama
   `last_death_was_winner`).
5. `test_porcentaje_de_headshots_por_ronda`: `A0` mata `B0` con headshot y
   `B1` sin -> `headshotPercentage == 50.0`; un jugador sin kills ->
   `0.0` (y no `ZeroDivisionError`).
6. `test_agregado_de_dos_rondas`: las stats de la ronda del test 5 pasadas
   dos veces a `player_match_stats` -> para `A0`: `rounds == 2`,
   `kills == 4`, `headshots == 2`, `headshotPercentage == 50.0`,
   `deaths == 0`.
7. `test_agregado_cuenta_muertes_y_asistencias`: dos rondas armadas a mano
   como listas de dicts (no hace falta lector) para un jugador, una con
   `died=True, assists=1` y otra con `died=False, assists=2` ->
   `deaths == 1`, `assists == 3`. Mas un caso con lector: `scoreboard[0]`
   con `assistsFromRound=2` -> `player_round_stats` da `assists == 2` para
   `A0`.

**Orden:** falso y helpers -> 3 (el mas simple) -> 1, 2, 4 -> 5 a 7 ->
`ruff check backend` -> `manage.py test tests.test_player_stats` ->
`check.sh`.

**Que puede romperse:** nada en runtime. Si el Dev encuentra que un
escenario da otro numero, no ajusta el codigo: lo anota en Implementacion y
`## Para el humano` (fuera de alcance cambiar el 1vX).

**Caso dudoso ya visto (no va como test):** ver `## Para el humano`.

**Verificacion manual:** `cd backend && python manage.py test
tests.test_player_stats -v 2` -> 7 tests ok. Mutacion sugerida para QA:
cambiar `team_left < 2` por `team_left < 1` en `stats.py` y ver caer los
tests 1, 2 y 4; quitar la suma de rivales vivos y ver caer 1 y 4.

**Tamano:** ~130 lineas de test. Cabe en un turno.

## Implementacion

(Dev 20261008T0902Z, sobre main dc0188b, commits a39852f y e6e030e)

Quedo: `backend/tests/test_player_stats.py` con `LectorFalso` (`players` y
`teams` tomados de `Reader`), `PlayerRoundStatsTests` (8) y
`PlayerMatchStatsTests` (2). 10 tests verdes; ningun archivo fuera de
`archivos:`.

Criterio -> test:
- ultimo vivo que gana (B4, `1vX == 5`, 3 kills, vivo) ->
  `test_ultimo_vivo_que_gana_suma_sus_kills_y_los_rivales_vivos`.
- 1v1 ganado -> `test_uno_contra_uno_ganado_vale_uno` (escenario del diseno,
  no el ambiguo de la PO).
- ganador sin bajas -> `test_sin_bajas_en_el_ganador_no_hay_1vx`.
- ultimo del ganador que muere (`last_death_was_winner`) ->
  `test_el_ultimo_del_ganador_que_muere_igual_cobra_el_1vx`.
- hs% por ronda y sin kills -> `test_porcentaje_de_headshots_por_ronda`,
  `test_porcentaje_de_headshots_sin_kills_no_divide_por_cero`.
- agregado por partida -> `test_agregado_de_dos_rondas`,
  `test_agregado_cuenta_muertes_y_asistencias`; asistencias del marcador ->
  `test_las_asistencias_salen_del_marcador`.

Desvios del diseno (por la revision ciega, cada uno confirmado con mutacion):
- Test nuevo `test_las_kills_antes_de_quedar_solo_no_cuentan_para_el_1vx`
  (B4 mata a A0 con su equipo entero, despues queda solo y mata a A2 ->
  `1vX == 4`). Sin el, cambiar `team_left < 2` por nada dejaba toda la suite
  verde: en los otros escenarios todas las kills del clutcher son posteriores
  a quedar solo.
- `test_agregado_de_dos_rondas` usa dos rondas distintas (1 kill con HS y 3
  sin -> `25.0`) en vez de la misma dos veces (`50.0`): con rondas iguales no
  se distingue hs% sobre el total de un promedio de los hs% por ronda. Por eso
  el criterio de la PO (`headshots == 2`, `50.0`) queda como `headshots == 1`,
  `25.0`.
- El 0.0 sin kills se prueba directo sobre `headshot_percentage(0, 0)`: en
  la fila de un jugador sin kills nunca se llama y el 0.0 es solo el inicial.
- Test 7 del diseno partido en dos (asistencias del marcador por un lado,
  agregado de muertes y asistencias por otro).

Mutaciones corridas (y revertidas): `team_left < 2` -> `< 1` tira 3 tests;
`team_left < 2` -> sin condicion tira 1; quitar la suma de rivales vivos tira 2.

No se toco `pydissect/`. El caso dudoso de `PLAYER_LEAVE` sigue en
`## Para el humano`, sin test.

Verificacion: `check.sh` -> `Todo en verde.` (376 tests backend, 53 vitest,
build ok, 17 e2e) sobre e6e030e.

## Revision 2026-10-08 sobre c7cd309

(Revisor 20261008T1202Z. Revision ciega con `revision.md` sobre el diff sin
`docs/backlog`; cada hallazgo confirmado con mutacion por el lider. Los
valores esperados de 1vX se recalcularon a mano contra `stats.py` y
coinciden.)

Hallazgos:

- [test] backend/tests/test_player_stats.py
  (`test_las_kills_antes_de_quedar_solo_no_cuentan_para_el_1vx`)
  Que pasa: la unica kill "antes de quedar solo" ocurre con el equipo ganador
  completo (5 vivos), asi que el limite real del umbral (un companero vivo)
  no se prueba.
  Como reproducirlo: en `pydissect/stats.py`, `team_left < 2` -> `< 3` o
  `<= 4` deja los 10 tests de la rama en verde; B4 cobraria una kill hecha
  con B3 todavia vivo.
  Arreglo: lo agrega el revisor (test de caso borde, pasa en main):
  `test_la_kill_con_un_companero_vivo_no_cuenta_para_el_1vx` (gana el 1; A1
  mata B0..B2; B4 mata A0 con B3 vivo; A1 mata B3; B4 mata A1 -> `1vX == 4`,
  `kills == 2`). Con `< 3` y con `<= 4` cae; sin mutacion pasa.

Sin hallazgos de reglas, formato ni estilo: un solo archivo de test nuevo,
dentro de `archivos:`, sin tildes en identificadores, sin `print`, sin tocar
`pydissect/`. Nota sin hallazgo: las ramas `DEATH` y `PLAYER_LEAVE` del
conteo de 1vX (suicidio o desconexion de un companero) no tienen test; ningun
test lo promete y el caso de `PLAYER_LEAVE` ya esta en `## Para el humano`.

Criterios de aceptacion: los seis cubiertos por tests con nombre (ver
Implementacion; los desvios del criterio de la PO estan justificados alli y
los numeros nuevos se verificaron). 11 tests en el archivo.

`check.sh` -> `Todo en verde.` sobre c7cd309 (antes de agregar el test) y
sobre el commit de esta revision.

Veredicto: aprobar (el unico hallazgo quedo cubierto por el test que agrego
el revisor) -> `revisado`.

## QA 2026-10-08 sobre 10126b8

(QA 20261008T1802Z. La rama ya contiene `origin/main` dc0188b; sin `.env`.)

Suite y pasos de `ci.yml`, tal cual:

- `./scripts/check.sh` (el de `origin/claude/great-cray-7o9tvf`) sobre
  10126b8 -> `Todo en verde.`: ruff `All checks passed!`, `Ran 377 tests ...
  OK (skipped=4)`, vitest 53 passed, build ok, e2e 17 passed. Ese mismo
  script corre `ruff check backend`, `manage.py test tests` sin `.env`,
  `npm test` y `npm run build`, que son los pasos de `ci.yml`.
- `cd backend && python manage.py test tests.test_player_stats -v 2` -> 11
  tests ok (12 con el que agrega esta QA).

Endpoints y base: la rama solo agrega un archivo de test; no toca vistas,
modelos, migraciones, `frontend/src` ni `pydissect/`. `runserver` + `curl`,
migracion y tamano del chunk no aplican (el e2e de `check.sh` ya levanto la
app sembrada y paso).

Criterios (cada uno con su test; los numeros los recalcule a mano contra
`stats.py` y coinciden):

- [x] ultimo vivo que gana: `B4` con `1vX == 5`, `kills == 3`, vivo ->
      `test_ultimo_vivo_que_gana_suma_sus_kills_y_los_rivales_vivos` ok.
- [x] 1v1 ganado -> `test_uno_contra_uno_ganado_vale_uno` ok (escenario del
      diseno; el de la PO era ambiguo, ver Diseno).
- [x] ganador sin bajas -> `test_sin_bajas_en_el_ganador_no_hay_1vx` ok.
- [x] ultimo del ganador que muere -> `test_el_ultimo_del_ganador_que_muere_igual_cobra_el_1vx` ok.
- [x] hs% por ronda y sin kills -> `test_porcentaje_de_headshots_por_ronda`,
      `test_porcentaje_de_headshots_sin_kills_no_divide_por_cero` ok.
- [x] agregado por partida -> `test_agregado_de_dos_rondas` (25.0, desvio
      justificado en Implementacion), `test_agregado_cuenta_muertes_y_asistencias`,
      `test_las_asistencias_salen_del_marcador` ok.

Mutaciones propias en `backend/pydissect/stats.py` (distintas de las del Dev
y el Revisor; cada una con `manage.py test tests.test_player_stats` y
revertida, `git status` limpio despues):

| mutacion | cae |
|---|---|
| `winning_team = 0` fijo | 3 tests |
| `elif not winners_alive and last_death_was_winner` -> `elif False` | `test_el_ultimo_del_ganador_que_muere_igual_cobra_el_1vx` |
| KILL no marca `died` a la victima | 5 |
| quitar el filtro `u.get("username") != username` (cuenta kills de todos) | 5 |
| rivales vivos cuenta tambien a los muertos | 5 |
| el agregado no suma `deaths` | `test_agregado_cuenta_muertes_y_asistencias` |
| hs% agregado = hs% de la ultima ronda | `test_agregado_de_dos_rondas` |
| `assists` ignora `assistsFromRound` | `test_las_asistencias_salen_del_marcador` |
| headshot no suma | 2 |
| `DEATH` no baja `team_left` (`(DEATH, PLAYER_LEAVE)` -> `(PLAYER_LEAVE,)`) | **ninguno** con los tests de la rama |

La ultima sobrevivia: un companero del clutcher que muere sin KILL
(suicidio, caida) no tenia test. Agregue el test de borde
`test_un_companero_muerto_sin_asesino_tambien_deja_solo_al_clutcher` (gana
el 1; A0 mata B0..B2; B3 `DEATH`; B4 mata A0..A4 -> `1vX == 5`). Pasa sobre
main; con esa mutacion cae (B4 queda en 0), y tambien cae si `DEATH` no
marca `died`. `ruff check backend` limpio y `ruff format --check` sin
cambios. La rama `PLAYER_LEAVE` sigue sin test a proposito: su caso dudoso
esta en `## Para el humano`.

`check.sh` -> `Todo en verde.` tambien sobre el commit de esta QA.

Veredicto: `aprobado`.

## Verificar en el PC

No hace falta: solo agrega tests; no toca parser, migraciones, `recompute`,
Electron ni `.ps1`. Si se quiere repetir: `cd backend; python manage.py test
tests.test_player_stats -v 2` -> 12 tests ok.

## Pendiente

## Para el humano

- (Arquitecto 20261008T0602Z, aviso, no bloquea) Caso dudoso del 1vX en
  main dc0188b: gana el 0; `A0` mata `B0..B3`; `B4` mata `A0`; `A1` sale de
  la partida (`PLAYER_LEAVE`); `B4` mata `A2` y `A3`; `A4` mata `B4`. `A4`
  gano solo contra uno y queda con `1vX == 0`, porque `A1` no figura como
  muerto y el codigo cree que quedan dos vivos. Si eso debe contar como 1v1
  es una decision de producto; no entra en esta ficha (fuera de alcance), se
  puede proponer aparte.
