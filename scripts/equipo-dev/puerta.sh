#!/usr/bin/env bash
# Puerta de merge del Release como script (MAQUINARIA M2). Por ahora corre la
# condicion d: lo que una rama no puede tocar ni debilitar para entrar a dev.
# La juzga frontera.py (copia vendorizada, la misma en todos los proyectos del
# dueno; no se edita aca) con frontera.json, los dos leidos de la ref del
# playbook y nunca de la rama: una rama que afloja frontera.json no se juzga
# con su propia version.
#
# Por que existe. La condicion d era una lista de rutas que el Release miraba
# a ojo con `git diff --name-only`, y "saltar, desactivar o borrar un test"
# solo estaba prohibido en prosa: una rama podia llegar a check.sh en verde
# borrando la prueba que fallaba, o subiendo los reintentos del e2e.
# frontera.py mira merge-base(origin/dev, rama)..rama y marca pruebas borradas
# o con menos definiciones, saltos (skip, only, skipTest, fixme...),
# supresiones en blanco (las que callan todo el lint o la cobertura), archivos
# protegidos (la puerta y lo que mergea el humano) y umbrales que se aflojan.
#
# Una linea `Frontera: <motivo>` en un commit hace pasar a frontera.py, pero
# no a esta puerta: lo que el equipo declara lo mergea el humano, igual que
# todo lo que antes caia en la lista de la condicion d. La declaracion le
# explica el cambio al humano; no lo salta. Un umbral flojo no se declara.
#
# Uso:  puerta.sh <rama> [--ref REF]     REF: --ref, EQUIPO_REF, .git/equipo-dev.env u origin/dev
#       git show $EQUIPO_REF:scripts/equipo-dev/puerta.sh | bash -s -- <rama> --ref $EQUIPO_REF
# Salida: 0 `PUERTA_OK d` · 1 `PUERTA_FALLA d: <motivo>`, con el detalle de
#         frontera.py arriba · 2 uso invalido, rama o ref que no existen.
set -u

uso() { echo "puerta: $1 (uso: puerta.sh <rama> [--ref REF])" >&2; exit 2; }
rama="" ref="${EQUIPO_REF:-}"
while [ $# -gt 0 ]; do
    case "$1" in
        --ref) [ $# -ge 2 ] || uso "--ref necesita una ref"; ref=$2; shift 2 ;;
        -*) uso "opcion desconocida: $1" ;;
        *) [ -z "$rama" ] || uso "una sola rama"; rama=${1#origin/}; shift ;;
    esac
done
[ -n "$rama" ] || uso "falta la rama"
repo="$(git rev-parse --show-toplevel 2>/dev/null)" || uso "no es un repo git"
cd "$repo" || exit 2
if [ -z "$ref" ]; then
    env="$(git rev-parse --git-dir)/equipo-dev.env"
    [ -f "$env" ] && ref=$(sed -n 's/^export EQUIPO_REF=//p' "$env" | tail -1)
fi
ref=${ref:-origin/dev}
R="origin/$rama"
git rev-parse -q --verify "$R^{commit}" >/dev/null || R=$rama
git rev-parse -q --verify "$R^{commit}" >/dev/null || uso "no existe la rama $rama"
command -v python3 >/dev/null || uso "falta python3"

tmp=$(mktemp -d)
trap 'git worktree remove --force "$tmp/w" >/dev/null 2>&1; rm -rf "$tmp"; git worktree prune 2>/dev/null' EXIT
for f in frontera.py frontera.json; do
    git show "$ref:scripts/equipo-dev/$f" > "$tmp/$f" 2>/dev/null || uso "$ref no tiene scripts/equipo-dev/$f"
done
# Sin checkout: frontera.py solo lee git, y la rama queda como HEAD de un
# arbol aparte sin tocar el checkout de este turno.
git worktree add -q --detach --no-checkout "$tmp/w" "$R" 2>/dev/null || uso "no pude abrir $R aparte"
salida=$(python3 "$tmp/frontera.py" -C "$tmp/w" 2>&1); codigo=$?
printf '%s\n' "$salida"
marcas=$(printf '%s\n' "$salida" | grep -c '✗')
primera=$(printf '%s\n' "$salida" | grep -m1 '✗' | sed 's/^ *✗ *//')
case "$codigo" in
    0) if [ "$marcas" -eq 0 ]; then echo "PUERTA_OK d"; exit 0; fi
       echo "PUERTA_FALLA d: declarado con Frontera: ($primera; $marcas en total), lo mergea el humano"; exit 1 ;;
    1) echo "PUERTA_FALLA d: $primera ($marcas en total)"; exit 1 ;;
    *) echo "puerta: frontera.py no pudo juzgar $R (salida $codigo; con un clon superficial, git fetch --unshallow origin)" >&2; exit 2 ;;
esac
