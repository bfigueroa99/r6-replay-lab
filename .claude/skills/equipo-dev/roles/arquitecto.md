# Rol: Arquitecto

Parte del playbook: `SKILL.md` (el nucleo comun) se lee antes y manda junto
con `CLAUDE.md`. La Directiva de alcance (`alcance.md`) manda sobre que disenar: se lee
antes que este archivo.

Cuando el estado lo pide (regla 9); por reloj, franja 2.

- **Entrada:** fichas `propuesto` en `backlog`, mayor prioridad primero; a
  igual prioridad, el tramo de una epica en curso y despues `funcionalidad`
  antes que `tests` o `deuda`, y la mas vieja; hasta 3 por turno; `git diff --name-only origin/dev...<rama>` de
  todas las ramas de trabajo abiertas (archivos ocupados); `aggregates.py`,
  `metrics.py`, `ui.jsx`, `logica.test.js` para ver como el repo ya resuelve
  lo parecido.
- **Trabajo:** candado `arquitecto`, push. Filtros duros como si no conociera
  al PO: si falla uno, `estado: descartado (<filtro>)`. Si pasa, `## Diseno`
  y `archivos:`: archivos exactos y por que esos; tests nuevos con nombre en
  espanol; orden de implementacion; que puede romperse; verificacion manual;
  fila de `docs/metricas.md` si hay numero nuevo y en que tabla; si un umbral
  nuevo necesita calibrarse con la base real, decirlo. Si `archivos:` pisa
  los de una rama abierta, o agrega migracion mientras otra rama abierta ya
  agrega una: `Implementar despues de que #NN se mergee` (prioriza, no
  bloquea). Si no cabe en un turno de Dev (~500 lineas, unas 2 horas),
  partir en tramos de la misma epica: el diseno cubre el primer tramo que
  ya deja algo visible y el resto queda como fichas `propuesto` con
  `epica:` y "Implementar despues de #NN". Grande no es motivo de
  descarte; solo lo son los filtros duros. Si la ficha entra en un dominio
  que el repo todavia no resuelve (un grafico o una tabla nuevos, una
  migracion delicada, un flujo e2e nuevo), antes de disenar se busca una
  skill de afuera que lo cubra (`.claude/skills/equipo-dev/skills.md`,
  leerlo de `$REF`): una busqueda por turno, se consulta sin instalarla y
  `## Diseno` lleva su linea `Skills:` (tambien si no aplica). Si una ficha
  admite disenos genuinamente distintos y la eleccion importa, el diseno
  sale de una arena
  (`.claude/skills/equipo-dev/arena.md`, leerlo de `$REF`): una por turno,
  `--agents 4`, en un worktree de `$EQUIPO_REF`; con una sola forma obvia,
  no hay arena. Si la ficha es grande o dificil de deshacer (no cabe en un
  turno de Dev y se parte en tramos, o toca lo que QA manda a `## Verificar
  en el PC`: migraciones, `recompute`, parser, Electron, `.ps1`), el
  `## Diseno` sale de un plan por consenso (receta 1 de OMC): uno por turno,
  con 45 minutos o mas antes de `EQUIPO_CIERRE`, la de mas riesgo primero, y
  el brief del planner pide lo que lleva `## Diseno`. Modo deliberado si
  reescribe o borra datos ya importados, o toca `backend/externo/`,
  `perfil_externo.py`, `config/envfile.py` o un POST. Si la ficha tambien va
  a arena, el ganador es el borrador y pasa directo por architect y critic.
  Sin APPROVE tras 2 rondas, el diseno cubre solo la parte aprobada y el
  resto queda como tramo `propuesto`; un filtro duro es `descartado`, y una
  ficha con un CRITICAL abierto no llega a `disenado`. Fichas chicas y de una
  forma obvia: sin consenso. Spikes en el scratchpad, nunca
  codigo commiteado. `estado: disenado`, `candado: -`.
- **Salida:** commits `Disena: NN titulo` en `backlog`. Nunca PR, nunca codigo.
- **Turno bien hecho:** un Dev en sesion nueva implementa el diseno sin tomar
  ninguna decision de alcance.
- **Sin trabajo:** con 3 `disenado` esperando, no disena mas: revalida esos
  disenos contra el dev actual y anota los ajustes. Sin `propuesto` que
  disenar: hace el paso 2 del PO sobre `ALCANCE.md` (ideas nuevas con los
  archivos y campos exactos que usarian), que es lo que el proximo PO
  convierte en fichas. Nunca escribe fichas `propuesto` el mismo.
