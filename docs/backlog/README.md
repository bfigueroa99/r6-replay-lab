# Backlog del equipo de desarrollo autonomo

Desde el item 30, el backlog vive aca y no en `docs/roadmap.md` (que queda
como historia de los items 1 a 19). Cada item es **una ficha**,
`docs/backlog/NN-slug.md`, copiada de `PLANTILLA.md`. La ficha viaja en la
misma rama que su codigo y se mergea con el: en `main` solo hay fichas de
items terminados.

## Dos lugares

- **Rama `claude/equipo-dev/backlog`**: el papel. Fichas en `propuesto`,
  `disenado` y `descartado`, mas `ESTADO.md` (el tablero) y, si existe, el
  marcador `PAUSA`. Nunca tiene PR, nunca se mergea, no cuenta para la cola.
- **Rama `claude/equipo-dev/NN-slug`**: el trabajo de un item. Nace cuando un
  Dev reclama la ficha y termina cuando el humano la mergea.

## Estados

`propuesto` -> `disenado` -> `en curso <fecha>` -> `implementado` ->
`revisado` | `con hallazgos` -> `aprobado` | `con hallazgos` -> `entregado`.
Lateral: `descartado (<motivo>)`. "Hecho" no lo escribe nadie: hecho es que
la ficha esta en `main`.

## El tablero

`ESTADO.md` en la rama `backlog` tiene URL estable:
`https://github.com/bfigueroa99/r6-replay-lab/blob/claude/equipo-dev/backlog/docs/backlog/ESTADO.md`.
Cada turno lo regenera: cola con estados y links de compare, orden de merge
sugerido, ramas borrables con el comando listo, preguntas para el humano.

## Lo que hace el humano

- **Mergear** las ramas `entregado` (o abrir el PR desde el link de compare
  si la sesion no tenia herramientas de GitHub). Da igual merge, squash o
  rebase: el equipo detecta los tres.
- **Borrar la rama** al mergear (o activar "Automatically delete head
  branches" en el repo). El equipo nunca borra ramas, solo las lista.
- **Pedir algo**: un commit propio en la rama del item, o texto bajo
  `## Para el equipo` en `ESTADO.md` (editable desde la web). El equipo
  responde en la ficha y en el tablero en su proximo turno.
- **Pausar**: crear el archivo `docs/backlog/PAUSA` en la rama `backlog`
  desde la web de GitHub. Todo turno termina sin tocar nada mientras exista.
