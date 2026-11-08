# Backlog del equipo de desarrollo autonomo

Desde el item 30, el backlog vive aca y no en `docs/roadmap.md` (que queda
como historia de los items 1 a 19). Cada item es **una ficha**,
`docs/backlog/NN-slug.md`, copiada de `PLANTILLA.md`. La ficha viaja en la
misma rama que su codigo y se mergea con el: en `dev` (y en `main`, cuando
lo promovés) solo hay fichas de items terminados.

## Dos lugares

- **Rama `claude/equipo-dev/backlog`**: el papel. Fichas en `propuesto`,
  `disenado` y `descartado`, mas `ESTADO.md` (el tablero), `ALCANCE.md` (el
  mapa de lo que la app todavia no hace), `INVESTIGACION.md` (la bitacora del
  investigador) y, si existe, el
  marcador `PAUSA`, el veto `SIN_MERGE` y un espejo `en curso` de cada ficha
  reclamada. Nunca tiene PR, nunca se mergea, no cuenta para la cola.
- **Rama `claude/equipo-dev/NN-slug`**: el trabajo de un item. Nace cuando un
  Dev reclama la ficha y termina cuando el release manager la mergea (o el
  humano, en los casos de abajo).

## Estados

`propuesto` -> `disenado` -> `en curso <fecha>` -> `implementado` ->
`revisado` | `con hallazgos` -> `aprobado` | `con hallazgos` -> `entregado`.
Lateral: `descartado (<motivo>)`. "Hecho" no lo escribe nadie: hecho es que
la ficha esta en `dev`.

## El tablero

`ESTADO.md` en la rama `backlog` tiene URL estable:
`https://github.com/bfigueroa99/r6-replay-lab/blob/claude/equipo-dev/backlog/docs/backlog/ESTADO.md`.
Cada turno lo regenera: cola con estados y links de compare, orden de merge
sugerido, ramas borrables con el comando listo, preguntas para el humano.

## Quien mergea

El **release manager** mergea en `dev`, por PR, lo que paso dev, revision y
QA en tres sesiones distintas, con `check.sh` en verde sobre la rama ya
fusionada con `dev`, sin pedidos tuyos sin responder y sin veto. Despues borra
esa rama.

`main` es la release: solo recibe `dev` cuando vos lo promovés (un PR `dev` ->
`main` con commit de merge; `scripts/release.ps1` publica desde `main`). El
equipo nunca abre PR contra `main`, ni mergea ni empuja ahi; `ESTADO.md` te
deja en `## Para el humano` la linea `RELEASE` de `estado.sh`: cuantos commits
lleva `dev` sin promover y el link para hacerlo.

Lo mergeas vos cuando el cambio toca lo que la nube no puede verificar o las
reglas del propio equipo: `frontend/electron/`, `packaging/`, `scripts/*.ps1`,
`.github/`, `CLAUDE.md`, `.claude/`, `.opencode/`, `scripts/equipo-dev/` y las
plantillas de esta carpeta. Esas fichas quedan `entregado (PR pendiente de merge: ...)` y
aparecen en `ESTADO.md` con el motivo. Da igual merge, squash o rebase: el
equipo detecta los tres. Borra la rama al mergear.

Las reglas del equipo (playbook) viven en `dev` cuando las mergeas, que es de
donde las lee la rutina; `main` y la rama `claude/equipo-dev/playbook` quedan
de respaldo.
Nadie del equipo empuja ahi: la mueven tu merge o una sesion que vos inicies.
Lo pendiente de la maquinaria del loop esta en `MAQUINARIA.md`.

## Guardia y frontera

Dos frenos que no dependen de que el turno se acuerde de la prosa:

- **Guardia** (`.claude/hooks/guardia.py`, hook `PreToolUse` de
  `.claude/settings.json`): antes de cada comando de Bash y de cada escritura
  con el MCP de GitHub frena el push forzado (`--force`, `-f`, `+rama`,
  `--mirror`), todo push a `main` o a `dev` (`.claude/hooks/guardia.json`; la
  rama del playbook no, porque la puede mover una sesion tuya), `--no-verify`,
  `git commit -n`, `core.hooksPath` y `rm -r` sobre `/`, `~` o `.git`. Sale 2,
  el turno ve el motivo y el bloqueo queda en `.git/guardia.log`. Ve lo que
  escribe el agente, no lo que corre un script por dentro. Rige en las
  sesiones que arrancan en una rama que la tenga: para la Routine, desde que
  mergees este cambio en `dev`. OpenCode no lee los hooks de Claude Code: ahi
  no corre. En tu PC con Windows, si no hay `python3` en el PATH el hook sale
  127: Claude Code lo muestra como error del hook, no bloquea nada y la
  sesion sigue, pero ahi la guardia no frena.
- **Frontera** (`scripts/equipo-dev/frontera.py` con `frontera.json`, la
  condicion d de la puerta de merge, que corre `scripts/equipo-dev/puerta.sh`):
  sobre `origin/dev...<rama>` marca pruebas borradas, podadas o saltadas
  (`skip`, `only`, `skipTest`, `fixme`), supresiones en blanco (`noqa`,
  `eslint-disable`, `pragma: no cover`), archivos protegidos (la puerta:
  `check.sh`, `ruff.toml`, la configuracion de vitest y Playwright,
  `package.json`; y todo lo que mergeas vos) y umbrales que se aflojan
  (reintentos del e2e, largo de linea de ruff, topes de `pruebas.sh`). Un
  commit con la linea `Frontera: <motivo>` declara el cambio: frontera.py lo
  da por bueno, pero el Release igual no lo mergea; te lo deja con el motivo a
  la vista. Un umbral flojo no se declara nunca: lo cambias vos.

## Alcance

Desde el 2026-10-10 el equipo trabaja con una **directiva de alcance**: la
prioridad es funcionalidad nueva, no solo endurecer lo que existe (ver
`.claude/skills/equipo-dev/alcance.md`). Cada ficha
lleva `tipo:` (`funcionalidad`, `bug`, `tests`, `deuda`) y, si es parte de
algo grande, `epica:`. El product owner propone al menos una funcionalidad por
turno; tests y deuda sueltos solo entran con 3 funcionalidades esperando; los
bugs reales entran siempre.

`ALCANCE.md` es el mapa: epicas por tema, cada idea con que gana el usuario,
que datos del `.rec` usa, tamano y estado (`idea`, `ficha NN`, `en dev`,
`PR #n`, `no`). Lo hace crecer el product owner en cada turno con lo que ve
adentro del repo, y el **investigador** (cuando el estado lo pide; por
reloj, la franja 7 de los dias pares) con lo que trae de afuera: parsers abiertos del `.rec` (primero
r6-dissect), otras herramientas de replay, trackers, herramientas de otros
juegos, la comunidad, las notas de parche de Ubisoft y la analitica de
esports. Cada idea de afuera llega con su link, y su bitacora (que fuentes se
miraron, que dieron, que salio seco) es `INVESTIGACION.md`.

Una vez por semana el investigador tambien mide la **paridad con la app de
referencia** con el pack Replica (`.claude/skills/replica-*`): mapa de lo que
la referencia hace, matriz de funciones con lo que la app ya tiene, puntaje de
`parity.py` y resenas reales de sus usuarios. Lo que la referencia tiene y el
`.rec` no puede dar queda como `skip`; los `must` que faltan entran a
`ALCANCE.md` en la epica `paridad-referencia`. Los archivos quedan en
`docs/backlog/replica/*` de la rama `backlog`. La referencia es **r6-replay.com y
Aurelix**, y el procedimiento completo esta en
`.claude/skills/equipo-dev/replica.md`. Las semillas de
los dos archivos estan en `docs/backlog/` del playbook y se copian a
`backlog` la primera vez. `ESTADO.md` muestra en `## Alcance` cuantas funcionalidades llegaron a
`dev` en la ultima semana y, si fueron cero, por que.

## Lo que hace el humano

- **Dirigir el crecimiento**: editar `ALCANCE.md` en la rama `backlog` desde
  la web. Lo que subas en una tabla se propone antes; una idea con estado `no`
  o tachada no se propone nunca.
- **Cambiar la referencia de Replica**: editar el bloque "Referencia" de
  `.claude/skills/equipo-dev/replica.md` en un PR y mergearlo. La pasada
  siguiente ve que no coincide con la de `recon.md` y rehace el recon con la
  referencia nueva.
- **Vetar el merge automatico**: crear `docs/backlog/SIN_MERGE` en la rama
  `backlog` desde la web. El equipo sigue trabajando pero deja todo en
  `entregado` para que lo mergees vos. Borrar el archivo lo reactiva.
- **Pedir algo**: un commit propio en la rama del item, o texto bajo
  `## Para el equipo` en `ESTADO.md` (editable desde la web). El equipo
  responde en la ficha y en el tablero en su proximo turno.
- **Cambiar el prompt de la rutina**: editar
  `.claude/skills/equipo-dev/rutina.md` (llega por merge o por una sesion
  tuya); lo que edites a mano en claude.ai lo revierte el Release al
  compararlo.
- **Crear o reanudar la rutina**: el equipo nunca crea, enciende ni borra
  Routines; si no hay ninguna, el loop solo corre cuando alguien lo lanza (asi
  quedo desde el 2026-10-30 20:13 UTC, cuando la del equipo dejo de existir).
  Para recrearla en claude.ai: repositorio `bfigueroa99/r6-replay-lab`, un
  nombre que lleve `r6-replay-lab` (el Release la busca por nombre), prompt =
  `rutina.md` tal cual, **una sesion nueva por disparo** (con una sesion
  persistente cada turno hereda la memoria del anterior y la independencia
  entre dev, revisor y QA bloquea las fichas que esa sesion ya toco) y
  cadencia de 3 o 4 horas (`1 */3 * * *` calza con la tabla del reloj; con
  otra, `estado.sh` mide la real). Conviene que su permiso incluya `bash`
  sobre `scripts/equipo-dev/*.sh` y las herramientas
  `mcp__claude-code-remote__list_triggers` y `update_trigger` (paso 9 del
  Release). Un orquestador que lance turnos en subagentes de una misma
  sesion le pasa a cada uno su contexto: `turno.sh --contexto <id>`.
- **Pausar**: crear el archivo `docs/backlog/PAUSA` en la rama `backlog`
  desde la web de GitHub. Ningun turno nuevo hace nada mientras exista, y uno
  que ya arranco lo ve antes de su proximo push y cierra.
- **Correr turnos en OpenCode** (ademas de la rutina de la nube, o en su
  lugar), con un modelo detras de OmniRoute:
  `bash scripts/equipo-dev/opencode.sh [rol]` en Linux, macOS o WSL. Arma un
  worktree al lado del repo (`../r6-replay-lab-equipo`, o
  `EQUIPO_OPENCODE_DIR`), le pone el entorno que pide `estado.sh` (venv,
  `frontend/node_modules`, Chromium) y corre
  `opencode run --command equipo-dev --auto` con la rutina de `origin/dev`.
  Hace falta OpenCode 1.19 o mas nuevo (`npm i -g opencode-ai`), OmniRoute
  (`npm i -g omniroute` y `omniroute`, con un proveedor conectado en
  http://localhost:20128) y `gh auth login`: ahi `gh` es la herramienta de
  GitHub del equipo. El proveedor lo deja `omniroute setup-opencode` en la
  configuracion de OpenCode; si no, `scripts/equipo-dev/opencode_proveedor.py`
  lo arma en cada turno con `OMNIROUTE_URL` y `OMNIROUTE_API_KEY` (la clave
  nunca queda escrita). El modelo es `omniroute/auto`; `OMNIROUTE_MODEL` o
  `EQUIPO_OPENCODE_MODEL` lo cambian. Sus commits firman `OpenCode`, que el
  equipo reconoce como propio. En un cron, cada 3 horas como la rutina:
  `1 */3 * * * bash /ruta/a/r6-replay-lab/scripts/equipo-dev/opencode.sh >> ~/equipo-dev.log 2>&1`.
