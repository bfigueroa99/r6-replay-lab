# 31. Tests de stats por jugador: 1vX, headshots y agregado por partida

estado: disenado
candado: -
rama: -
area: parser
prioridad: 3
fuente: hueco de tests en pydissect: `stats.player_round_stats` (incluido el calculo de 1vX) y `stats.player_match_stats` no tienen ningun test unitario (main dc0188b)
archivos: backend/tests/test_player_stats.py
turnos: po 20261008T0302Z, arquitecto 20261008T0602Z

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

(Dev)

## Revision <fecha> sobre <sha>

(Revisor)

## QA <fecha> sobre <sha>

(QA)

## Verificar en el PC

(QA, solo si toca migraciones, recompute, parser, Electron o `.ps1`.)

## Pendiente

## Para el humano

- (Arquitecto 20261008T0602Z, aviso, no bloquea) Caso dudoso del 1vX en
  main dc0188b: gana el 0; `A0` mata `B0..B3`; `B4` mata `A0`; `A1` sale de
  la partida (`PLAYER_LEAVE`); `B4` mata `A2` y `A3`; `A4` mata `B4`. `A4`
  gano solo contra uno y queda con `1vX == 0`, porque `A1` no figura como
  muerto y el codigo cree que quedan dos vivos. Si eso debe contar como 1v1
  es una decision de producto; no entra en esta ficha (fuera de alcance), se
  puede proponer aparte.
