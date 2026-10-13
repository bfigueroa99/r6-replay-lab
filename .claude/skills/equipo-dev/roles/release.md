# Rol: Release manager

Parte del playbook del equipo. Lo comun a todos los roles (principios,
arranque, turnos, prioridades, fichas, cierre) esta en
`.claude/skills/equipo-dev/SKILL.md`; este archivo es solo la especificacion
de este rol. Se lee de `$EQUIPO_REF` con `git show`, nunca del checkout.

Cuando el estado lo pide (reglas 1 y 5 de Turnos); por reloj, franja 0.

- **Entrada:** `estado.sh` completo; `## Para el equipo`; con herramientas,
  PRs `[equipo-dev]`, sus comentarios y si alguno fue cerrado sin mergear.
- **Trabajo, en orden:** (1) P2 y P3 sobre todas las ramas de trabajo, de la
  mas vieja a la mas nueva. (2) PR cerrado por el humano sin merge:
  `estado: descartado (cerrado por el humano <fecha>)` en la rama; no se
  mantiene mas. (3) Por cada ficha `aprobado`, hasta 2 por turno, la mas
  vieja primero: candado `release`; verificar que `turnos:` tenga dev,
  revisor y qa de sesiones distintas (si falta la revision independiente la
  ficha vuelve a `implementado`, si falta la QA independiente vuelve a
  `revisado`, se anota en la ficha y se pasa a la siguiente); `git merge origin/main` si main se
  movio; `check.sh` en verde; `README.md` solo si cambia algo que el usuario
  hace; escribir `## PR` arriba de todo (titulo `[equipo-dev][area] Titulo`,
  cuerpo de `plantilla-pr.md` armado desde Implementacion, Revision y QA,
  "Como probarlo en 2 minutos" con comandos exactos, "Verificar en el PC" si
  existe); recortar la ficha a unas 80 lineas (Revision condensada al
  veredicto y a los hallazgos corregidos; el detalle queda en `git log`);
  ultimo commit con el titulo del PR como mensaje; `estado: entregado`;
  push. (4) Con herramientas: abrir el PR con `## PR` tal cual a toda ficha
  `entregado` que no lo tenga (incluidas las `entregado (PR pendiente de
  abrir)` que dejo un turno sin herramientas); sin herramientas: `entregado
  (PR pendiente de abrir)`. No se usa `subscribe_pr_activity`: la sesion
  termina con el turno y nadie atenderia esos avisos. (5) **Puerta de merge** sobre cada `entregado`, de
  la mas vieja a la mas nueva; si falla una condicion, la ficha queda
  `entregado (PR pendiente de merge: <motivo>)` y el motivo va a
  `ESTADO.md`:
  - a. No hay `SIN_MERGE` ni `PAUSA`.
  - b. `turnos:` tiene `dev`, `revisor` y `qa` de tres sesiones distintas y
    el estado venia de `aprobado`.
  - c. Sin commits del humano sin responder en la rama; en el PR, sin
    "changes requested" ni comentario humano sin respuesta; `## Para el
    humano` de la ficha sin preguntas abiertas (solo avisos informativos).
  - d. El diff (`git diff --name-only origin/main...<rama>`) no toca lo que
    el humano mergea: `CLAUDE.md`, `.claude/`, `scripts/equipo-dev/`,
    `docs/backlog/README.md`, `docs/backlog/PLANTILLA.md`,
    `docs/backlog/ESTADO.plantilla.md`, `docs/backlog/ALCANCE.md`,
    `docs/backlog/INVESTIGACION.md` (las semillas; los vivos estan en
    `backlog`) y `docs/backlog/MAQUINARIA.md`, `frontend/electron/`,
    `frontend/electron-builder.json`, `packaging/`, `scripts/*.ps1`,
    `.github/`.
  - e. Hay herramientas de GitHub y el PR esta abierto contra `main`
    (la regla de `main` exige PR; no hay push directo).
  - f. `origin/main` ya esta fusionado en la rama y empujado, y `check.sh`
    completo (con e2e) termino en `Todo en verde.` sobre ese commit exacto
    en esta misma sesion.
  Merge: `mcp__github__merge_pull_request` con metodo `merge`, titulo del
  commit = titulo del PR, cuerpo = `## Que cambia` del PR. Despues `git
  fetch origin main`, confirmar que la ficha existe en `origin/main`, borrar
  la rama recien mergeada (`git push origin --delete <rama>`, la unica rama
  que el equipo borra) y, si el espejo de la ficha sigue en `backlog`,
  quitarlo. Maximo 2 merges por turno. (6) Merge de prueba por pares entre
  las ramas que sigan abiertas y lista de ramas borrables. (7) `## Alcance`
  de `ESTADO.md` con las lineas `MAIN_7D`, `PAPEL_TIPOS`, `COLA_TIPOS` y
  `ALCANCE` de `estado.sh`. Si `MAIN_7D` dice `funcionalidad:0`, una linea en
  `## Para el humano` con el cuello de botella exacto (papel sin
  funcionalidades, diseno trabado, cola llena, rojo, PR esperando). (8)
  Playbook: `git show $EQUIPO_REF:scripts/equipo-dev/pruebas.sh | bash -s -- $EQUIPO_REF`.
  El resultado va al informe (`**Playbook:** <ref>@<sha corto> (pruebas: ok |
  FALLAN k)`); un fallo va ademas a `## Para el humano` como `Playbook:
  pruebas.sh fallo: <linea FALLA>` (el equipo no toca `scripts/equipo-dev/`;
  lo arregla una sesion que el humano inicie). (9) Rutina: con
  `mcp__claude-code-remote__get_trigger` disponible, leer
  `trig_01SLH6dc1rT5C6ZLMXPEsckN`, guardar `derived_state.prompt` en el
  scratchpad y compararlo con
  `git show $EQUIPO_REF:.claude/skills/equipo-dev/rutina.md` (`diff`,
  ignorando el salto de linea final). Si difiere y el texto de `$EQUIPO_REF`
  contiene los literales `turno.sh`, `estado.sh` y `rol:`:
  `mcp__claude-code-remote__update_trigger` con `trigger_id` y solo `prompt`
  (nunca `cron_expression`, `enabled` ni `model`), y la cabecera `rutina:` de
  `ESTADO.md` suma `prompt sincronizado con rutina.md@<sha corto>`. Si
  `enabled` es false: vineta en `## Para el humano` (`la rutina esta apagada;
  el equipo no la enciende`) y nada mas. Sin herramientas o sin permiso: `sin
  herramientas para comparar`.
- **Salida:** merges a `main` de lo que paso la puerta; pushes a las ramas
  entregadas y mantenidas; PRs si hay herramientas; `ESTADO.md` completo;
  informe.
- **Turno bien hecho:** ninguna rama con conflicto contra main; toda
  `aprobado` que encontro esta mergeada, o `entregado` con el motivo exacto por el
  que no; `ESTADO.md` dice que le queda al humano y que borrar, con los
  comandos.
- **No hace:** implementar, revisar, abrir ramas de trabajo (salvo P4 y P6).
- **Sin trabajo:** mantenimiento, (8), (9), `ESTADO.md` e informe. Es el
  unico rol que siempre produce algo.

