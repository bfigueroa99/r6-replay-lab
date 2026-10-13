# 38. Una ronda de Y9S4+ con defuse del perdedor queda con dos ganadores

estado: propuesto
candado: -
rama: -
tipo: bug
epica: -
area: parser
prioridad: 2
fuente: aviso de la ficha 30 (`## Para el humano`, ya en main) y de `ESTADO.md`; `round_end` en `backend/pydissect/events.py:378`
archivos: backend/pydissect/events.py, backend/tests/test_round_end.py, docs/formato-rec.md
turnos: po 20261013T0511Z

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

(Arquitecto)

## Implementacion

(Dev) Que quedo, que no, desvios del diseno y por que.

## Revision <fecha> sobre <sha>

(Revisor) Formato de `revision.md`. Veredicto al final.

## QA <fecha> sobre <sha>

(QA) Un comando y un resultado por criterio de aceptacion.

## Verificar en el PC

(QA, solo si toca migraciones, recompute, parser, Electron o `.ps1`.)
Toca el parser: confirmar con `.rec` reales de Y9S4+ que el ganador de cada
ronda coincide con el marcador, y correr `manage.py recompute --dry-run`
para ver cuantas rondas cambian antes del `recompute` real.

## Pendiente

## Para el humano

Decision tomada por el PO con la variante conservadora: **manda la
cabecera**, porque es la misma fuente que el marcador de la partida y el
comentario de `round_end` ya la trata como la verdad desde Y9S4. La
alternativa (manda el feed y se corrige el marcador) es mas invasiva y no se
hace sin que lo pidas en `## Para el equipo`. El cambio es reversible: no
toca datos hasta que corras `recompute`.
