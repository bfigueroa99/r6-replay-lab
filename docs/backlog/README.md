# Backlog del equipo de desarrollo autonomo

Desde el item 30, el backlog vive aca y no en `docs/roadmap.md` (que queda
como historia de los items 1 a 19). Cada item es **una ficha**,
`docs/backlog/NN-slug.md`, copiada de `PLANTILLA.md`. La ficha viaja en la
misma rama que su codigo y se mergea con el: en `main` solo hay fichas de
items terminados.

## Dos lugares

- **Rama `claude/equipo-dev/backlog`**: el papel. Fichas en `propuesto`,
  `disenado` y `descartado`, mas `ESTADO.md` (el tablero) y, si existe, el
  marcador `PAUSA`, el veto `SIN_MERGE` y un espejo `en curso` de cada ficha
  reclamada. Nunca tiene PR, nunca se mergea, no cuenta para la cola.
- **Rama `claude/equipo-dev/NN-slug`**: el trabajo de un item. Nace cuando un
  Dev reclama la ficha y termina cuando el release manager la mergea (o el
  humano, en los casos de abajo).

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

## Quien mergea

El **release manager** mergea por PR lo que paso dev, revision y QA en tres
sesiones distintas, con `check.sh` en verde sobre la rama ya fusionada con
`main`, sin pedidos tuyos sin responder y sin veto. Despues borra esa rama.

Lo mergeas vos cuando el cambio toca lo que la nube no puede verificar o las
reglas del propio equipo: `frontend/electron/`, `packaging/`, `scripts/*.ps1`,
`.github/`, `CLAUDE.md`, `.claude/`, `scripts/equipo-dev/` y las plantillas de
esta carpeta. Esas fichas quedan `entregado (PR pendiente de merge: ...)` y
aparecen en `ESTADO.md` con el motivo. Da igual merge, squash o rebase: el
equipo detecta los tres. Borra la rama al mergear.

## Lo que hace el humano

- **Vetar el merge automatico**: crear `docs/backlog/SIN_MERGE` en la rama
  `backlog` desde la web. El equipo sigue trabajando pero deja todo en
  `entregado` para que lo mergees vos. Borrar el archivo lo reactiva.
- **Pedir algo**: un commit propio en la rama del item, o texto bajo
  `## Para el equipo` en `ESTADO.md` (editable desde la web). El equipo
  responde en la ficha y en el tablero en su proximo turno.
- **Pausar**: crear el archivo `docs/backlog/PAUSA` en la rama `backlog`
  desde la web de GitHub. Ningun turno nuevo hace nada mientras exista, y uno
  que ya arranco lo ve antes de su proximo push y cierra.
