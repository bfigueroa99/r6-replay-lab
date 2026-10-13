# Rol: Release manager

Parte del playbook del equipo. Lo comun a todos los roles (principios,
arranque, turnos, prioridades, fichas, cierre) esta en
`.claude/skills/equipo-dev/SKILL.md`; este archivo es solo la especificacion
de este rol. Se lee de `$EQUIPO_REF` con `git show`, nunca del checkout.

Cuando el estado lo pide (reglas 1 y 6 de Turnos); por reloj, franja 0.

- **Entrada:** `estado.sh` completo; `## Para el equipo`; con herramientas,
  PRs `[equipo-dev]`, sus comentarios y si alguno fue cerrado sin mergear.
- **Trabajo, en orden:**
  - (0) **Entorno.** Con `ENTORNO_INCOMPLETO`, instalar (Arranque comun).
    Si sigue incompleto, no hay verde posible: cada `aprobado` pasa a
    `entregado (PR pendiente de merge: entorno incompleto)` con una linea en
    la ficha, y el turno sigue con (8), (9) y el cierre (`--resultado
    parcial`). Asi la regla 6 de Turnos la reintenta una vez por dia en vez
    de que cada disparo sea un Release que no puede avanzar (M12). En el
    reintento, esa ficha pasa por (3) completo.
  - (1) P2 y P3 sobre todas las ramas de trabajo, de la mas vieja a la mas
    nueva.
  - (2) PR cerrado por el humano sin merge: `estado: descartado (cerrado
    por el humano <fecha>)` en la rama; no se mantiene mas.
  - (3) Por cada ficha `aprobado`, hasta 2 por turno, la mas vieja primero:
    candado `release`; `puerta.sh <rama> --solo b` (independencia, orden de
    las etapas y que esta sesion no firmo ninguna: un Release encadenado no
    mergea lo que reviso o probo). Si falla por falta de revision posterior
    al ultimo dev, la ficha vuelve a `implementado`; por falta de QA
    posterior a la ultima revision, a `revisado`; se anota en la ficha y se
    pasa a la siguiente. Despues `git merge origin/main` si main se movio;
    `check.sh` en verde; `README.md` solo si cambia algo que el usuario hace;
    escribir `## PR` arriba de todo (titulo `[equipo-dev][area] Titulo`,
    cuerpo de `plantilla-pr.md` armado desde Implementacion, Revision y QA,
    "Como probarlo en 2 minutos" con comandos exactos, "Verificar en el PC"
    si existe); recortar la ficha a unas 80 lineas (Revision condensada al
    veredicto y a los hallazgos corregidos; el detalle queda en `git log`);
    ultimo commit con el titulo del PR como mensaje; `estado: entregado`;
    push.
  - (4) Con herramientas: abrir el PR con `## PR` tal cual a toda ficha
    `entregado` que no lo tenga (incluidas las `entregado (PR pendiente de
    abrir)` que dejo un turno sin herramientas); sin herramientas:
    `entregado (PR pendiente de abrir)`. No se usa `subscribe_pr_activity`:
    la sesion termina con el turno y nadie atenderia esos avisos.
  - (5) **Puerta de merge** sobre cada `entregado`, de la mas vieja a la mas
    nueva, con el script y no a mano:

    ```bash
    git show "$EQUIPO_REF:scripts/equipo-dev/puerta.sh" | bash -s -- <rama>
    ```

    Las condiciones: a. sin `SIN_MERGE` ni `PAUSA`; b. `turnos:` con `dev`,
    `revisor` y `qa` de tres sesiones distintas, en ese orden despues del
    ultimo dev, el estado venia de `aprobado` y esta sesion no firmo
    ninguna; c. sin commits del humano sin responder en la rama y sin
    preguntas abiertas en `## Para el humano` de la ficha; d. el diff no
    toca lo que mergea el humano (la lista exacta es `RUTAS_DEL_HUMANO` de
    `puerta.sh`: `CLAUDE.md`, `.claude/`, `scripts/equipo-dev/`, las semillas
    de `docs/backlog/`, Electron, `packaging/`, `scripts/*.ps1`, `.github/`);
    e. hay herramientas de GitHub y el PR esta abierto contra `main`; f.
    `origin/main` fusionado y empujado, y `check.sh` completo (con e2e) en
    `Todo en verde.` sobre ese commit exacto en esta sesion (`check.sh` lo
    deja anotado en `.git/check-verde`). El script imprime `MANUAL` para lo
    que no puede ver: c2 (comentarios y "changes requested" del PR) y e;
    esos dos se confirman con `mcp__github`. `PUERTA_FALLA` en cualquier
    letra: la ficha queda `entregado (PR pendiente de merge: <motivo>)` y
    el motivo sale solo en el tablero. Merge: `mcp__github__merge_pull_request`
    con metodo `merge`, titulo del commit = titulo del PR, cuerpo = `## Que
    cambia` del PR. Despues `git fetch origin main`, confirmar que la ficha
    existe en `origin/main`, borrar la rama recien mergeada (`git push origin
    --delete <rama>`, la unica rama que el equipo borra; si el proxy corta el
    push de borrado no se reintenta: el tablero la lista sola en el comando
    unico de borrables) y, si el espejo de la ficha sigue en `backlog`,
    quitarlo. Maximo 2 merges por turno.
  - (6) El orden de merge por pares, las borrables, `## Alcance` y el cuello
    de botella si `MAIN_7D` dice `funcionalidad:0` los escribe el tablero
    (`pulso.sh cierre`): el Release no los copia a mano.
  - (7) Notas de version: si `RELEASE_PENDIENTE` de `estado.sh` tiene alguna
    funcionalidad o bug, `notas.sh` arma las notas desde las fichas que
    llegaron a `main` desde el ultimo tag; van al informe y, si el humano no
    tiene un pedido abierto de version, como pedido `H<n>` "hay version para
    publicar" con el comando de `release.ps1` (una sola vez).
  - (8) Playbook: `git show $EQUIPO_REF:scripts/equipo-dev/pruebas.sh | bash
    -s -- $EQUIPO_REF`. El resultado va al informe (`**Playbook:**
    <ref>@<sha corto> (pruebas: ok | FALLAN k)`); un fallo va ademas como
    pedido (`--humano "Playbook: pruebas.sh fallo: <linea FALLA>"`): el
    equipo no toca `scripts/equipo-dev/`, lo arregla una sesion que el humano
    inicie.
  - (9) Rutina: con `mcp__claude-code-remote__get_trigger` disponible, leer
    `trig_01SLH6dc1rT5C6ZLMXPEsckN`, guardar `derived_state.prompt` en el
    scratchpad y compararlo con `git show
    $EQUIPO_REF:.claude/skills/equipo-dev/rutina.md` (`diff`, ignorando el
    salto de linea final). Si difiere y el texto de `$EQUIPO_REF` contiene
    los literales `turno.sh`, `estado.sh` y `rol:`:
    `mcp__claude-code-remote__update_trigger` con `trigger_id` y solo
    `prompt` (nunca `cron_expression`, `enabled` ni `model`), y el cierre
    lleva `--rutina "prompt sincronizado con rutina.md@<sha corto>"`. Si
    `enabled` es false: `--humano "la rutina esta apagada; el equipo no la
    enciende"` (una vez). Si el trigger no aparece (`not found`): `--rutina
    "trigger no encontrado desde esta sesion"`. Sin herramientas o sin
    permiso: `--rutina "sin herramientas para comparar"`.
- **Salida:** merges a `main` de lo que paso la puerta; pushes a las ramas
  entregadas y mantenidas; PRs si hay herramientas; cierre con el tablero;
  informe.
- **Turno bien hecho:** ninguna rama con conflicto contra main; toda
  `aprobado` que encontro esta mergeada, o `entregado` con el motivo exacto
  por el que no; el tablero dice que le queda al humano y que borrar.
- **No hace:** implementar, revisar, abrir ramas de trabajo (salvo P4 y P6);
  mergear una ficha en la que esta sesion firmo dev, revisor o qa.
- **Sin trabajo:** mantenimiento, (7), (8), (9), cierre e informe; despues,
  si quedan 40 minutos, encadenar (SKILL.md, Turnos).
