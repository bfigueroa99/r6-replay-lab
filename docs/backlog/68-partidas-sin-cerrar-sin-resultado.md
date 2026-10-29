# 68. Partidas con marcador que no cierra quedan sin resultado

estado: propuesto
candado: -
rama: -
tipo: bug
epica: -
area: backend
prioridad: 2
fuente: decision del humano 2026-10-28 en `## Para el equipo` de `ESTADO.md` (aviso de la ficha 50, idea G7 de `ALCANCE.md`); `ingest.py:169` decide `won` solo por quien tiene mas rondas
archivos: -
turnos: po 20261029T0004Z

## PR

(La escribe el Release manager al final.)

## Que gana quien usa la app

Si falta el `.rec` de la ultima ronda, hoy una ranked que iba 3-2 entra como
victoria (o derrota) por 1 y mueve tu winrate de partidas. Con el arreglo esa
partida queda "incompleta": sigue en el listado, pero no suma ni resta en los
winrates de partida.

## Criterios de aceptacion

- [ ] Importar una partida `Ranked` (regla de `reglas_partida.py`) con
      marcador final 3-2 deja `Match.won = None` y `result == "incompleta"`;
      4-2, 2-4 y 5-4 (prorroga) siguen en `True`/`False`; 4-3 (sin cerrar,
      la prorroga va a 5) queda `None`. La comprobacion vive en
      `reglas_partida.py` (sin Django) con test propio.
- [ ] Un tipo de partida sin regla (`regla_para` devuelve None, p. ej.
      `Unranked` o `Custom`) se comporta como hoy: gana el que tiene mas
      rondas, empate = `None`.
- [ ] Lo ya importado se corrige sin reparsear: `manage.py recompute`
      (o el camino que elija el Arquitecto, sin migracion de esquema)
      recalcula `Match.won` con la misma funcion; `--dry-run` cuenta las
      partidas que cambian y una segunda corrida no cambia nada.
- [ ] Con una partida 3-2 Ranked y otra 4-1 Ranked ganada, el winrate de
      partidas de `/api/overview/` (`matches_summary`, ficha 64) es 100 %
      sobre 1 partida, y el listado `/api/matches/` muestra la 3-2 como
      incompleta.
- [ ] `docs/metricas.md`: la fila que define el resultado de partida dice
      cuando una partida queda incompleta (marcador que no cierra segun la
      regla del tipo).

## Fuera de alcance

- La lista de partidas dudosas en Datos (resto de la idea G7): otra ficha si
  hace falta.
- Reglas para otros tipos de partida sin fuente citable (`reglas_partida.py`
  solo admite reglas con fuente).
- Abandonos o rendiciones que cierran la partida antes de tiempo: si el
  marcador no llega, queda incompleta (se anota como limite en `metricas.md`).
- El winrate de rondas: no cambia.

## Diseno

## Implementacion

## Revision <fecha> sobre <sha>

## QA <fecha> sobre <sha>

## Verificar en el PC

## Pendiente

## Para el humano

Sin decision pendiente (la tomaste el 2026-10-28). Aviso: una ranked que
termino por rendicion del rival (sin llegar a 4) tambien queda incompleta;
si eso pasa seguido en tus replays, avisa y se busca otra señal.
