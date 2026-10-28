---
description: Un turno del equipo de desarrollo autonomo, como la rutina de Claude Code pero en OpenCode (lo lanza scripts/equipo-dev/opencode.sh)
---
La rutina del equipo, tal cual esta en `origin/dev` (la misma que dispara Claude Code; `main` y la rama playbook son su respaldo, en el mismo orden que la rutina):

!`git show origin/dev:.claude/skills/equipo-dev/rutina.md 2>/dev/null || git show origin/main:.claude/skills/equipo-dev/rutina.md 2>/dev/null || git show origin/claude/equipo-dev/playbook:.claude/skills/equipo-dev/rutina.md`

Mensaje de este disparo: $ARGUMENTS

Corres en OpenCode (lo lanza `scripts/equipo-dev/opencode.sh`, normalmente con un modelo detras de OmniRoute), no en una sesion de Claude Code. El playbook manda igual; cambia esto:

- **Arranque**: ya estas en el worktree del equipo (`git rev-parse --show-toplevel`). Si en esta maquina existe `/home/user/r6-replay-lab` y no es este worktree, salta ese `cd` del arranque y quedate aca.
- **GitHub**: aca `gh` si tiene credenciales (las del humano; `gh auth status`) y es la herramienta de GitHub. Donde el playbook dice "con herramientas" o nombra `mcp__github__*`:
  - abrir el PR: `gh pr create --base dev --head <rama> --title "<titulo>" --body-file <archivo>`
  - merge del Release (solo con la puerta de merge): `gh pr merge <n> --merge --subject "<titulo del PR>" --body-file <archivo con ## Que cambia>`; nunca `--squash`, `--rebase`, `--admin` ni `--auto`
  - review del Revisor: `gh pr review <n> --comment --body-file <archivo>`; nunca `--approve` ni `--request-changes`
  - comentarios: `gh pr view <n> --comments` y `gh api repos/bfigueroa99/r6-replay-lab/pulls/<n>/comments`
  - PRs abiertos del equipo: `gh pr list --state open --search "[equipo-dev] in:title"`
  Si `gh auth status` falla, es "sin herramientas", como dice el playbook.
- **La rutina de Claude Code** (paso 9 del Release, `get_trigger`/`update_trigger`): no hay; `sin herramientas para comparar`.
- **Subagentes** (revision ciega, dev de backend y frontend, investigador por familia, la arena): la herramienta `task` con `subagent_type: "general"`; `revision.md` va tal cual como su prompt.
- **Scratchpad**: `/tmp/opencode` o un `mktemp -d`, nunca dentro del repo.
- **Autor**: los commits salen como `OpenCode` (lo fija `opencode.sh`) y `estado.sh` lo cuenta como del equipo. No lo cambies: con otro autor, cada commit pareceria un pedido del humano.
- **Comandos largos**: la herramienta `bash` corta a los 2 minutos; a `./scripts/check.sh` pasale `timeout: 1800000`.
- **Web** (Investigador): `webfetch` si; `websearch` solo si OpenCode la trae activada. Sin busqueda, el camino "Sin red" del playbook.
- **Commits y PR**: sin las lineas de Claude Code (`Co-Authored-By: Claude...`, `Claude-Session: ...`).
