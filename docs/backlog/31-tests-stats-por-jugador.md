# 31. Tests de stats por jugador: 1vX, headshots y agregado por partida

estado: propuesto
candado: -
rama: -
area: parser
prioridad: 3
fuente: hueco de tests en pydissect: `stats.player_round_stats` (incluido el calculo de 1vX) y `stats.player_match_stats` no tienen ningun test unitario (main dc0188b)
archivos: -
turnos: po 20261008T0302Z

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
      por plant) -> igual se le cuenta el 1vX (rama `last_death_was_winner`).
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
