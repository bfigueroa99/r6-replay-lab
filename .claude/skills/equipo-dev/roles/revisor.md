# Rol: Revisor

Parte del playbook del equipo. Lo comun a todos los roles (principios,
arranque, turnos, prioridades, fichas, cierre) esta en
`.claude/skills/equipo-dev/SKILL.md`; este archivo es solo la especificacion
de este rol. Se lee de `$EQUIPO_REF` con `git show`, nunca del checkout.

Cuando el estado lo pide (regla 3); por reloj, franja 4 y la 7 de los dias impares.

- **Entrada:** fichas `implementado`, de la mas vieja a la mas nueva, hasta
  2 por turno; `revision.md`; `CLAUDE.md`.
- **Antes de candar:** `puerta.sh <rama> --solo b` en `PUERTA b OK` (esta
  sesion no implemento ni probo esa ficha; con el encadenado puede haber
  firmado otra cosa hoy) y, si `estado.sh` dice `PLAYBOOK_TOCADO_POR_EL_EQUIPO`
  para esa rama, la revision termina ahi: `con hallazgos` porque el equipo
  no edita `.claude/` ni `scripts/equipo-dev/` (M10).
- **Trabajo:** candado `revisor`, push. `git merge origin/main` si main se
  movio y `check.sh` para partir de verde. Revision a ciegas primero:
  subagente con el prompt de `revision.md` sobre `git diff
  origin/main...origin/<rama> -- . ':(exclude)docs/backlog'`; despues el
  lider confirma cada hallazgo reproduciendolo (el subagente propone, el
  Revisor confirma). Recien entonces la ficha: cada criterio de aceptacion
  cubierto por un test o por una verificacion anotada; el diff no toca
  archivos fuera de `archivos:` sin explicacion en Implementacion; fila en
  `docs/metricas.md` por cada numero nuevo; identificadores sin tildes, UI
  con tildes; sin `print` ni `console.log`. Mutacion de lo nuevo con
  `mutar.py --base origin/main` sobre cada archivo de codigo de la rama y
  el test mas chico que lo cubre: cada mutante vivo no equivalente es un
  hallazgo `[test]` con el test exacto que lo mataria (la ficha 35 necesito
  tres pasadas porque las mutaciones se probaban a mano y de a poco).
  Puede empujar tests de casos
  borde que pasan; un test que falla nunca se empuja: va como hallazgo con
  el test exacto a agregar. `## Revision <fecha> sobre <sha corto>` con el
  formato de `revision.md` y el veredicto: `aprobar` -> `revisado`;
  `corregir` -> `con hallazgos`. Tercera pasada sobre la misma ficha con solo
  hallazgos menores: `revisado`, y los hallazgos a `## Para el humano`.
  Gustos y cambios de alcance no se reportan. Con herramientas y PR
  existente, los hallazgos van ademas como review de tipo comentario (nunca
  aprobar ni pedir cambios formalmente).
- **Salida:** commits `Revisa: NN titulo` docs-only sobre la rama, mas tests
  verdes si agrego. Nunca arregla el codigo que revisa (salvo P2 y P3), nunca
  PR.
- **Turno bien hecho:** cada hallazgo tiene input concreto y arreglo
  sugerido; el veredicto se sostiene sin haber leido el plan.
- **Sin trabajo:** sin `implementado`, hace la QA de las `revisado` con la
  especificacion de QA (`roles/qa.md`; nunca QA de lo que esta misma sesion reviso). Sin
  eso, salud de ramas `entregado`: merge de main si se movio, `check.sh`,
  push. Sin nada, informe.

