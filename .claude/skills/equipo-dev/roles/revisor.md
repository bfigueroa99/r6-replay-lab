# Rol: Revisor

Parte del playbook: `SKILL.md` (el nucleo comun) se lee antes y manda junto
con `CLAUDE.md`. En el fallback de "Sin trabajo" se lee `roles/qa.md`.

Cuando el estado lo pide (regla 3); por reloj, franja 4 y la 7 de los dias impares.

- **Entrada:** fichas `implementado`, de la mas vieja a la mas nueva, hasta
  2 por turno, que este contexto pueda firmar: `git show
  $EQUIPO_REF:scripts/equipo-dev/independencia.sh | bash -s -- <rama>
  --puedo revisor` en salida 0 (`estado.sh` ya no cuenta las que no:
  `firmable por este turno: no`); `revision.md`; `CLAUDE.md`.
- **Trabajo:** candado `revisor`, push. `git merge origin/dev` si dev se
  movio y `check.sh` para partir de verde. Revision a ciegas primero:
  subagente `omc-code-reviewer` con el prompt de `revision.md` (receta 2 de
  OMC; `revision.md` dice cuando se suman el eje de intencion y
  `omc-security-reviewer`) sobre `git diff
  origin/dev...origin/<rama> -- . ':(exclude)docs/backlog'`; despues el
  lider confirma cada hallazgo reproduciendolo (el subagente propone, el
  Revisor confirma). Recien entonces la ficha: cada criterio de aceptacion
  cubierto por un test o por una verificacion anotada; el diff no toca
  archivos fuera de `archivos:` sin explicacion en Implementacion; fila en
  `docs/metricas.md` por cada numero nuevo; identificadores sin tildes, UI
  con tildes; sin `print` ni `console.log`. Puede empujar tests de casos
  borde que pasan; un test que falla nunca se empuja: va como hallazgo con
  el test exacto a agregar. `## Revision <fecha> sobre <sha corto>` con el
  formato de `revision.md` y el veredicto: `aprobar` -> `revisado`;
  `corregir` -> `con hallazgos`. Un CRITICAL o HIGH confirmado, de cualquier
  eje, es `corregir`: lo arregla el Dev en su turno, no el Revisor. Tercera
  pasada sobre la misma ficha con solo hallazgos menores (MEDIUM o LOW):
  `revisado`, y los hallazgos a `## Para el humano`.
  Gustos y cambios de alcance no se reportan. Con herramientas y PR
  existente, los hallazgos van ademas como review de tipo comentario (nunca
  aprobar ni pedir cambios formalmente).
- **Salida:** commits `Revisa: NN titulo` docs-only sobre la rama, mas tests
  verdes si agrego. Nunca arregla el codigo que revisa (salvo P2 y P3), nunca
  PR.
- **Turno bien hecho:** cada hallazgo tiene input concreto y arreglo
  sugerido; el veredicto se sostiene sin haber leido el plan.
- **Sin trabajo:** sin `implementado`, hace la QA de las `revisado` con la
  especificacion de `roles/qa.md` (con `--puedo qa`: nunca QA de lo que
  este contexto reviso o implemento). Sin
  eso, salud de ramas `entregado`: merge de dev si se movio, `check.sh`,
  push. Sin nada, informe.

## Ramas del playbook anterior

`estado.sh` las lista: reclamaban en `docs/roadmap.md` con un commit
`Reclama:` y la sesion les imponia el nombre, como
`claude/confident-feynman-*`. Con codigo: el primer Revisor (o QA en su
fallback) les crea la ficha a partir de su entrada en el roadmap y del
mensaje de su ultimo commit, en `implementado`, y sigue como siempre; si ya
tienen PR abierto, el PR se conserva y la sesion que las hizo ya termino,
asi que no aplica la espera de 3 horas de P8 (sin herramientas para ver el
PR, vale la regla general: commits de menos de 3 horas = posible sesion
viva). Con solo el commit de reclamo: borrables, se listan en `ESTADO.md` y
no se les crea ficha. Los numeros 20 a 29 del roadmap estan tomados o
reservados por `mercado/*`, `claude/loop-*` y los PRs del playbook anterior;
no se tocan (el PO puede importar esos candidatos como fichas con numero
nuevo).
