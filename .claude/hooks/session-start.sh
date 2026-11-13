#!/bin/bash
# Deja listas las dependencias en las sesiones cloud de Claude Code, para que
# `scripts/check.sh` funcione desde el primer minuto. En el PC no hace nada:
# ahi el entorno lo arma scripts/setup.ps1 y no hay que tocarlo.
set -euo pipefail

if [ "${CLAUDE_CODE_REMOTE:-}" != "true" ]; then
    exit 0
fi

repo="${CLAUDE_PROJECT_DIR:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)}"
cd "$repo"

# Sin matcher, el hook corre en todo SessionStart, tambien tras una
# compactacion (`"source": "compact"` en la entrada). Ahi la sesion es la misma
# y las dependencias ya estan; lo que se perdio es lo que el turno leyo con
# `git show` (playbook, rol, ficha), que ninguna herramienta vuelve a adjuntar
# porque la rutina lo lee por Bash y no con la herramienta Skill. Lo que este
# hook imprime entra al contexto: el rol y el playbook del turno y que releer.
entrada=""
[ -t 0 ] || entrada=$(cat 2>/dev/null || true)
if printf '%s' "$entrada" | grep -qE '"source"[[:space:]]*:[[:space:]]*"compact"'; then
    gd=$(git rev-parse --git-dir 2>/dev/null || true)
    env_file="$gd/equipo-dev.env"
    if [ -n "$gd" ] && [ -f "$env_file" ]; then
        valor() { sed -n "s/^export $1=//p" "$env_file" | tr -d '"' | head -1; }
        rol=$(valor EQUIPO_ROL); ref=$(valor EQUIPO_REF)
        echo "equipo-dev: la sesion se compacto en medio del turno $(valor EQUIPO_SESION): rol $rol, roles de la sesion: $(valor EQUIPO_ROLES), cierre a las $(valor EQUIPO_CIERRE) UTC, playbook $ref."
        echo "Lo leido con git show (estado.sh, SKILL.md, roles/$rol.md, alcance.md, la ficha) ya no esta en el contexto, y el playbook pide releerlo antes de la proxima accion, cada linea en su propia llamada a Bash:"
        echo "  source \"\$(git rev-parse --git-dir)/equipo-dev.env\""
        echo "  git show $ref:.claude/skills/equipo-dev/SKILL.md"
        echo "  git show $ref:.claude/skills/equipo-dev/roles/$rol.md"
        echo "  la ficha con candado de este turno, desde su rama: git show origin/<rama>:docs/backlog/<NN-slug>.md"
        echo "Las dependencias ya estan instaladas en esta sesion."
    fi
    exit 0
fi

echo "=> dependencias de Python"
python3 -m pip install --quiet --disable-pip-version-check \
    -r requirements.txt -r requirements-dev.txt

echo "=> dependencias del frontend"
if command -v npm >/dev/null 2>&1; then
    # `npm install` y no `npm ci`: el contenedor cachea node_modules entre
    # sesiones y asi no se reinstala todo cada vez.
    (cd frontend && npm install --no-audit --no-fund --loglevel=error)
else
    echo "   npm no esta en el PATH: la parte de frontend no se puede verificar"
fi

echo "=> listo"
