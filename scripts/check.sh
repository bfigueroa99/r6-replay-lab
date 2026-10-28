#!/usr/bin/env bash
# Lo mismo que check.ps1 (lint, tests, build y e2e) pero para Linux/macOS y
# para las sesiones cloud de Claude Code (el equipo de desarrollo corre ahi).
# Uso:  ./scripts/check.sh              todo
#       SIN_E2E=1 ./scripts/check.sh    sin el end to end (mas rapido)
#
# Solo `ruff check`, no `ruff format`: el formateador reescribiria medio repo
# para pelear con un estilo que ya es consistente. Cada paso anota si fallo y
# el resumen final es lo que decide el codigo de salida.
set -uo pipefail
# Primero git, para que tambien funcione leido por stdin
# (`git show <rama>:scripts/check.sh | bash`), que es como lo usa el equipo de
# desarrollo mientras el script no este en dev.
repo="$(git rev-parse --show-toplevel 2>/dev/null || { cd "$(dirname "${BASH_SOURCE[0]:-$0}")/.." && pwd; })"

# El venv es opcional aca: en el PC vive en .venv, en la nube las dependencias
# van al interprete del sistema.
if [ -x "$repo/.venv/bin/python" ]; then
    python="$repo/.venv/bin/python"
else
    python="$(command -v python3 || command -v python)"
fi
if [ -x "$repo/.venv/bin/ruff" ]; then
    ruff="$repo/.venv/bin/ruff"
else
    ruff="$(command -v ruff || true)"
fi

fallos=()

# El e2e pide el Chromium de la version exacta de @playwright/test. Si falta y
# hay otro instalado (la imagen de la nube trae uno mas nuevo y cada turno del
# equipo perdia tiempo armando enlaces a mano), imprime la ruta de ese otro para
# E2E_CHROMIUM, que playwright.config.js usa como executablePath. Si esta el
# suyo, como en el PC, no imprime nada y Playwright elige como siempre.
chromium_alternativo() {
    local raiz rev d n mejor=0 exe
    raiz="${PLAYWRIGHT_BROWSERS_PATH:-${HOME:-}/.cache/ms-playwright}"
    rev=$(cd "$repo/frontend" && node -p "JSON.parse(require('fs').readFileSync('node_modules/playwright-core/browsers.json', 'utf8')).browsers.find(b => b.name === 'chromium-headless-shell').revision" 2>/dev/null) || return 0
    [ -n "$rev" ] && [ ! -d "$raiz/chromium_headless_shell-$rev" ] || return 0
    for d in "$raiz"/chromium_headless_shell-*/; do
        n=${d%/}; n=${n##*-}
        [[ "$n" =~ ^[0-9]+$ ]] && [ "$n" -gt "$mejor" ] || continue
        exe=$(find "$d" -maxdepth 2 -type f \( -name headless_shell -o -name chrome-headless-shell \) 2>/dev/null | head -1)
        [ -n "$exe" ] && [ -x "$exe" ] && { mejor=$n; echo "$exe"; }
    done | tail -1
}

echo
echo "[1/5] ruff"
if [ -n "$ruff" ]; then
    "$ruff" check "$repo/backend" || fallos+=(ruff)
else
    # Sin lint no hay verde: en la nube un verde a medias pasa por verde.
    echo "  ruff no esta instalado: pip install -r requirements-dev.txt"
    fallos+=(ruff)
fi

echo
echo "[2/5] tests del backend"
(cd "$repo/backend" && "$python" manage.py test tests) || fallos+=(tests)

if [ -d "$repo/frontend/node_modules" ]; then
    echo
    echo "[3/5] tests del frontend"
    (cd "$repo/frontend" && npm test) || fallos+=("tests del frontend")

    echo
    echo "[4/5] build del frontend"
    (cd "$repo/frontend" && npm run build) || fallos+=(build)

    echo
    echo "[5/5] end to end"
    if [ "${SIN_E2E:-}" = 1 ]; then
        echo "  omitido por SIN_E2E=1"
    else
        # Levanta Django con una base sembrada aparte y maneja la app en
        # Chromium: es el unico paso que ve la pagina de verdad.
        if [ -z "${E2E_CHROMIUM:-}" ]; then
            alternativo=$(chromium_alternativo)
            if [ -n "$alternativo" ]; then
                export E2E_CHROMIUM="$alternativo"
                echo "  falta el Chromium de esta version de Playwright: el e2e usa $alternativo"
            fi
        fi
        (cd "$repo/frontend" && npm run e2e) || {
            fallos+=(e2e)
            echo "  Si falta el navegador: cd frontend && npm run e2e:browser"
        }
    fi
else
    # A diferencia de check.ps1, aca falta de node_modules es un fallo: en la
    # nube un verde a medias se confunde con un verde, y el equipo autonomo
    # solo empuja codigo con todos los pasos pasados.
    echo
    echo "[3/5] [4/5] [5/5] falta frontend/node_modules: corre 'npm install' en frontend/"
    fallos+=("frontend sin instalar")
fi

echo
if [ "${#fallos[@]}" -gt 0 ]; then
    echo "Fallo: $(printf '%s, ' "${fallos[@]}" | sed 's/, $//')"
    exit 1
fi
echo "Todo en verde."
