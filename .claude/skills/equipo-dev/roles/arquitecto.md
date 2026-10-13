# Rol: Arquitecto

Parte del playbook del equipo. Lo comun a todos los roles (principios,
arranque, turnos, prioridades, fichas, cierre) esta en
`.claude/skills/equipo-dev/SKILL.md`; este archivo es solo la especificacion
de este rol. Se lee de `$EQUIPO_REF` con `git show`, nunca del checkout.

Cuando el estado lo pide (regla 9); por reloj, franja 2.

- **Entrada:** fichas `propuesto` en `backlog`, mayor prioridad primero; a
  igual prioridad, el tramo de una epica en curso y despues `funcionalidad`
  antes que `tests` o `deuda`, y la mas vieja; hasta 3 por turno; `git diff --name-only origin/main...<rama>` de
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
  descarte; solo lo son los filtros duros. Spikes en el scratchpad, nunca
  codigo commiteado. `estado: disenado`, `candado: -`.
- **Salida:** commits `Disena: NN titulo` en `backlog`. Nunca PR, nunca codigo.
- **Turno bien hecho:** un Dev en sesion nueva implementa el diseno sin tomar
  ninguna decision de alcance.
- **Sin trabajo:** con 3 `disenado` esperando, no disena mas: revalida esos
  disenos contra el main actual y anota los ajustes. Sin `propuesto` que
  disenar: hace el paso 2 del PO (`roles/po.md`) sobre `ALCANCE.md` (ideas nuevas con los
  archivos y campos exactos que usarian), que es lo que el proximo PO
  convierte en fichas. Nunca escribe fichas `propuesto` el mismo.

