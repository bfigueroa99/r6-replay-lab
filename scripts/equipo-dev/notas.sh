#!/usr/bin/env bash
# Notas de version desde las fichas que llegaron a main desde el ultimo tag
# v* (M7 de MAQUINARIA.md). Lo que llega a main no dejaba notas: el humano
# armaba la Release a mano desde los PRs. Cada ficha ya trae su `## PR` con
# titulo y "Que cambia", asi que las notas salen de ahi, agrupadas por tipo,
# sin un CHANGELOG.md que cada rama tocaria (y chocaria) en el mismo lugar.
# Uso:  notas.sh [--desde <ref>]      (por defecto, el ultimo tag v* de origin/main)
#       git show <ref>:scripts/equipo-dev/notas.sh | bash -s -- [...]
# Imprime markdown listo para pegar en la Release, o `NOTAS_VACIAS` si no
# llego nada. Salida 0 siempre que pudo leer git.
set -u
repo="$(git rev-parse --show-toplevel 2>/dev/null)" || { echo "no es un repo git" >&2; exit 2; }
cd "$repo"
desde=""
[ "${1:-}" = --desde ] && desde=${2:-}
[ -n "$desde" ] || desde=$(git describe --tags --abbrev=0 --match 'v*' origin/main 2>/dev/null)
rango=origin/main; [ -n "$desde" ] && rango="$desde..origin/main"
fichas=$(git log "$rango" --first-parent -m --diff-filter=A --name-only --format= -- docs/backlog 2>/dev/null | grep -E '/[0-9]+-[^/]*\.md$' | sort -u)
[ -n "$fichas" ] || { echo "NOTAS_VACIAS (nada nuevo en main desde ${desde:-el inicio})"; exit 0; }
func=""; bugs=""; otros=""
for f in $fichas; do
    t=$(git show "origin/main:$f" 2>/dev/null) || continue
    tipo=$(printf '%s\n' "$t" | grep -m1 '^tipo:' | sed 's/^tipo:[[:space:]]*//')
    # titulo: el del PR sin el prefijo [equipo-dev][area]; si no hay PR, el de la ficha
    titulo=$(printf '%s\n' "$t" | grep -m1 -E '^\*?\*?Titulo:?\*?\*?' | grep -oE '`[^`]+`' | head -1 | tr -d '`' | sed -E 's/^(\[[^]]*\])+ *//')
    [ -n "$titulo" ] || titulo=$(printf '%s\n' "$t" | head -1 | sed -E 's/^# [0-9]+\. *//')
    # primer parrafo de "Que cambia" (dentro del PR) o de "Que gana quien usa la app"
    cambia=$(printf '%s\n' "$t" | awk '/^#+ Que cambia/ {f=1; next} f && /^#/ {exit} f && NF {printf "%s ", $0; n++} f && !NF && n {exit}')
    [ -n "$cambia" ] || cambia=$(printf '%s\n' "$t" | awk '/^## Que gana quien usa la app/ {f=1; next} f && /^#/ {exit} f && NF {printf "%s ", $0; n++} f && !NF && n {exit}')
    num=$(basename "$f" | cut -d- -f1)
    linea="- **$titulo** (ficha $num). ${cambia% }"
    case "$tipo" in
        funcionalidad) func="$func$linea"$'\n' ;;
        bug) bugs="$bugs$linea"$'\n' ;;
        *) otros="$otros$linea"$'\n' ;;
    esac
done
echo "## Novedades desde ${desde:-el inicio}"
[ -n "$func" ] && { echo; echo "### Lo nuevo"; echo; printf '%s' "$func"; }
[ -n "$bugs" ] && { echo; echo "### Arreglos"; echo; printf '%s' "$bugs"; }
[ -n "$otros" ] && { echo; echo "### Por dentro (tests y deuda)"; echo; printf '%s' "$otros"; }
exit 0
