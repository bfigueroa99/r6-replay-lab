# 69. El 1vX cuenta cuando un compañero se fue

estado: propuesto
candado: arquitecto 2026-10-30 16:56 UTC
rama: -
tipo: bug
epica: -
area: backend
prioridad: 2
fuente: decision del humano 2026-10-28 en `## Para el equipo` de `ESTADO.md` (pregunta de la ficha 31); `pydissect/stats.py:100-104` arma `winners_alive` solo con `died`, que `PlayerLeave` no marca
archivos: -
turnos: po 20261029T0004Z

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

## Implementacion

## Revision <fecha> sobre <sha>

## QA <fecha> sobre <sha>

## Verificar en el PC

## Pendiente

## Para el humano

Sin decision pendiente (la tomaste el 2026-10-28).
