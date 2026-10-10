# 35. Tests de como el parser decide que equipo ataca

estado: propuesto
candado: -
rama: -
area: tests
prioridad: 3
fuente: hueco de tests en `pydissect/header.py`: `derive_team_roles` (decide el lado de cada equipo por mayoria de operadores, descarta jugadores con operador 0 y anota el lado inferido de los operadores nuevos en `inferredOperatorSides`) solo lo ejercita `RealReplayTests` de `tests/test_pydissect.py`, que se salta sin `R6_TEST_REPLAY` (en la nube y en `check.sh` siempre). Es justo el codigo que tiene que aguantar una temporada nueva con operadores desconocidos.
archivos: -
turnos: po 20261010T0301Z

## PR

(La escribe el Release manager al final: titulo `[equipo-dev][area] Titulo`,
cuerpo segun `.claude/skills/equipo-dev/plantilla-pr.md` y una seccion
"Como probarlo en 2 minutos" con comandos exactos.)

## Que gana quien usa la app

Trabajo interno: si una temporada nueva trae operadores que la app no conoce,
el lado de cada equipo (y con el todo lo que se filtra por ataque y defensa)
depende de esta funcion, y hoy ningun test que corre la cubre. Baja el riesgo
de que un cambio en el parser invierta ataque y defensa sin que nada avise.

## Criterios de aceptacion

- [ ] Con un lector falso (`header`, `players`, `teams`, sin `.rec`), un equipo con mayoria de operadores de ataque conocidos queda `Attack` y el otro `Defense`, tambien cuando el equipo atacante es el `teamIndex` 1 (test en `tests/test_pydissect.py`).
- [ ] Un jugador con operador 0 sale de `header["players"]` y del `scoreboard` (test).
- [ ] Un operador con nombre conocido pero sin lado en `OPERATOR_SIDES` (el caso de un operador nuevo etiquetado en overrides) hereda el lado de su equipo en `header["inferredOperatorSides"]`; un Recluta no se anota ahi, y un ID sin nombre tampoco (test).
- [ ] Si ningun operador tiene lado conocido, los equipos quedan sin `role` y la funcion no revienta (test que afirma tambien el `log.warning`).
- [ ] Los tests no dejan estado: `operator_name` anota los IDs sin nombre en el registro en memoria de `overrides.record_unknown`, asi que cada test que use un ID desconocido llama a `reset_unknown()` al terminar, y `unknown_ids()` queda vacio despues de la clase (test).

## Fuera de alcance

- Cambiar la regla de desempate (`score0 >= score1` hace atacar al equipo 0): si el diseno ve que el empate da un resultado dudoso, va a `## Para el humano`, no se cambia en esta ficha.
- Tests con `.rec` reales o fixtures binarias.
- Otras funciones de `header.py` sin test directo (`read_header`, `gamemode_name`).

## Diseno

(Arquitecto) Archivos exactos y por que esos; tests nuevos con nombre en
espanol; orden de implementacion; que puede romperse (migracion, recompute,
build, instalador); verificacion manual; fila de `docs/metricas.md` si hay
numero nuevo. Si pisa archivos de otra rama abierta o agrega migracion
mientras otra ya la agrega: "Implementar despues de que #NN se mergee".

## Implementacion

(Dev) Que quedo, que no, desvios del diseno y por que.

## Revision <fecha> sobre <sha>

(Revisor) Formato de `revision.md`. Veredicto al final.

## QA <fecha> sobre <sha>

(QA) Un comando y un resultado por criterio de aceptacion.

## Verificar en el PC

(QA, solo si toca migraciones, recompute, parser, Electron o `.ps1`.)

## Pendiente

(Solo si alguien dejo trabajo a medias: que falta y donde se trabo.)

## Para el humano

(Cualquiera, solo si hace falta una decision suya.)
