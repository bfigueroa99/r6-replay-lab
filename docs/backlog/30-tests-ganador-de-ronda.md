# 30. Tests de quien gana la ronda y por que

estado: propuesto
candado: arquitecto 2026-10-08 06:02 UTC
rama: -
area: parser
prioridad: 2
fuente: hueco de tests en pydissect: `events.round_end` y `events.read_defuser_timer` no tienen ningun test (main dc0188b; el unico que los ejercita es `RealReplayTests`, que se salta sin `R6_TEST_REPLAY`)
archivos: -
turnos: po 20261008T0302Z

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

(Arquitecto)

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
