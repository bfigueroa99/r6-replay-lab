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
