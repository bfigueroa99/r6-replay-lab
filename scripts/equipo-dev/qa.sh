#!/usr/bin/env bash
# La bateria de QA del equipo en un comando, sobre el checkout (la rama bajo
# prueba o main): deriva de docs, fichas y ALCANCE.md, barrido de la API,
# fuzz del parser y la pasada por las paginas en Chromium. Es lo que el QA
# corre en cada ficha y en sus turnos sin trabajo (roles/qa.md); cada linea
# HALLAZGO que deja es candidata a ficha con el repro que ya trae.
# Uso:  qa.sh [--rapido] [--salida DIR] [--sin-paginas]
#       git show <ref>:scripts/equipo-dev/qa.sh | bash -s -- [...]
# --rapido: barrido solo con la lista fija y 150 casos de fuzz.
# Una linea por herramienta, `QA <herramienta>: <ultima linea>`, y al final
# `QA_OK` (salida 0) o `QA_HALLAZGOS: <herramientas>` (salida 1). El detalle
# de cada una queda en <salida>/<herramienta>.txt.
set -u
rapido=no; salida=""; paginas=si
while [ $# -gt 0 ]; do
    case "$1" in
        --rapido) rapido=si ;;
        --salida) salida=${2:-}; shift ;;
        --sin-paginas) paginas=no ;;
        *) echo "argumento desconocido: $1" >&2; exit 2 ;;
    esac
    shift
done
repo="$(git rev-parse --show-toplevel 2>/dev/null)" || { echo "no es un repo git" >&2; exit 2; }
cd "$repo"
yo_dir=""
if [ -n "${BASH_SOURCE[0]:-}" ] && [ -f "${BASH_SOURCE[0]}" ]; then yo_dir=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd); fi
salida=${salida:-$(mktemp -d)}
mkdir -p "$salida"
# Trae una herramienta a <salida> desde el mismo directorio o desde la ref.
traer() {
    if [ -n "$yo_dir" ] && [ -f "$yo_dir/$1" ]; then cp "$yo_dir/$1" "$salida/$1"
    else git show "${EQUIPO_REF:-origin/main}:scripts/equipo-dev/$1" > "$salida/$1"
    fi
}
py=python3; [ -x .venv/bin/python ] && py=.venv/bin/python
malas=""
correr() { # nombre comando...
    local n=$1; shift
    "$@" > "$salida/$n.txt" 2>&1
    local c=$?
    echo "QA $n: $(grep -vE '^\s*$' "$salida/$n.txt" | tail -1)"
    [ "$c" -eq 0 ] || malas="$malas $n"
}
for h in deriva-docs.sh fichas.sh barrido_api.py fuzz_parser.py qa-paginas.mjs; do traer "$h"; done
correr deriva bash "$salida/deriva-docs.sh"
correr fichas bash "$salida/fichas.sh"
correr alcance bash "$salida/fichas.sh" --alcance
if [ "$rapido" = si ]; then
    correr barrido "$py" "$salida/barrido_api.py" --rapido
    correr fuzz "$py" "$salida/fuzz_parser.py" --casos 150 --salida "$salida/fuzz"
else
    correr barrido "$py" "$salida/barrido_api.py"
    correr fuzz "$py" "$salida/fuzz_parser.py" --casos 1000 --salida "$salida/fuzz"
fi
if [ "$paginas" = si ]; then
    if [ ! -f frontend/dist/index.html ]; then (cd frontend && npm run build >/dev/null 2>&1); fi
    correr paginas node "$salida/qa-paginas.mjs" --salida "$salida/capturas"
fi
echo "QA_DETALLE en $salida"
if [ -n "$malas" ]; then echo "QA_HALLAZGOS:$malas"; exit 1; fi
echo "QA_OK"
exit 0
