#!/usr/bin/env bash
# Un turno del equipo de desarrollo en OpenCode, con un modelo detras de OmniRoute: lo
# mismo que dispara la rutina de Claude Code cada 3 horas, pero en una maquina propia
# (Linux, macOS o WSL) y desde un cron.
# Uso:  bash scripts/equipo-dev/opencode.sh            # el rol lo decide turno.sh
#       bash scripts/equipo-dev/opencode.sh dev        # pide un rol (el `rol: dev` de la rutina)
#       bash scripts/equipo-dev/opencode.sh --plan     # dice que haria, sin tocar nada
#
# Por que un worktree: el turno cambia de rama (backlog, NN-slug) y limpia; en la copia
# de trabajo del humano eso pisaria lo suyo. Es persistente (EQUIPO_OPENCODE_DIR, por
# defecto al lado del repo con -equipo) para no rearmar el entorno en cada turno: .venv
# y frontend/node_modules quedan, y se reinstalan solo si cambian sus requirements o su
# package-lock. Todo lo demas vuelve a origin/dev (la base de integracion del equipo) antes
# del turno, como en una sesion nueva.
#
# El modelo es EQUIPO_OPENCODE_MODEL, por defecto omniroute/${OMNIROUTE_MODEL:-auto} (el
# combo automatico de OmniRoute); opencode_proveedor.py le da a OpenCode ese proveedor
# (OMNIROUTE_URL, OMNIROUTE_API_KEY) si su configuracion no lo trae. Los commits salen con
# autor `OpenCode`, que estado.sh cuenta como del equipo igual que `Claude`: con otro, cada
# commit del turno pareceria un pedido del humano.
#
# Salida: la de opencode (124 si se corto por tiempo) | 1 no se pudo preparar | 2 ya hay
# un turno corriendo en ese worktree.
set -uo pipefail

export PATH="$HOME/.opencode/bin:$HOME/.local/bin:$PATH:/usr/local/bin:/usr/bin:/bin"
aqui="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
comun="$(git -C "$aqui" rev-parse --path-format=absolute --git-common-dir)" || exit 1
repo="${comun%/.git}"
dir="${EQUIPO_OPENCODE_DIR:-$repo-equipo}"
opencode="${OPENCODE_BIN:-opencode}"
modelo="${EQUIPO_OPENCODE_MODEL:-omniroute/${OMNIROUTE_MODEL:-auto}}"
techo=$(( ${EQUIPO_OPENCODE_MINUTOS:-150} * 60 ))

plan=no; rol=""
for a in "$@"; do
    case "$a" in
        --plan) plan=si ;;
        -h|--help) sed -n '2,22p' "$0"; exit 0 ;;
        release|po|arquitecto|dev|revisor|qa|investigador) rol="$a" ;;
        *) echo "uso: opencode.sh [--plan] [release|po|arquitecto|dev|revisor|qa|investigador]" >&2; exit 1 ;;
    esac
done

if ! command -v "$opencode" >/dev/null 2>&1; then
    echo "FALLA: no encuentro opencode (npm i -g opencode-ai, o OPENCODE_BIN con su ruta)" >&2
    exit 1
fi
if [ "$plan" = si ]; then
    echo "Correria, en el worktree $dir (origin/dev):"
    echo "  $opencode run --command equipo-dev -m $modelo --auto${rol:+ rol: $rol}"
    echo "autor OpenCode | techo $(( techo / 60 )) min"
    exit 0
fi

# Candado con mkdir (macOS no trae flock): un cron que se solapa no pisa el turno vivo.
candado="$comun/equipo-dev-opencode.lock"
if ! mkdir "$candado" 2>/dev/null; then
    pid=$(cat "$candado/pid" 2>/dev/null)
    if [ -n "$pid" ] && kill -0 "$pid" 2>/dev/null; then
        echo "Ya hay un turno corriendo en $dir (pid $pid): este no arranca."
        exit 2
    fi
    rm -rf "$candado"; mkdir "$candado" || exit 1
fi
echo $$ > "$candado/pid"
trap 'rm -rf "$candado"' EXIT

if ! git -C "$repo" fetch -q origin dev main '+refs/heads/claude/*:refs/remotes/origin/claude/*'; then
    echo "FALLA: sin acceso a origin" >&2
    exit 1
fi
if [ ! -d "$dir" ]; then
    git -C "$repo" worktree prune
    echo "=> worktree nuevo en $dir"
    git -C "$repo" worktree add -q --detach "$dir" origin/dev || exit 1
else
    suyo="$(git -C "$dir" rev-parse --path-format=absolute --git-common-dir 2>/dev/null)"
    if [ "$suyo" != "$comun" ]; then
        echo "FALLA: $dir existe y no es un worktree de este repo (EQUIPO_OPENCODE_DIR elige otro)" >&2
        exit 1
    fi
    git -C "$dir" merge --abort >/dev/null 2>&1
    git -C "$dir" checkout -q -f --detach origin/dev || exit 1
    git -C "$dir" clean -q -fdx -e .venv -e node_modules || exit 1
fi
cd "$dir" || exit 1

# El entorno que estado.sh exige (si falta, el turno no empuja codigo).
sello=$(cat requirements.txt requirements-dev.txt | git hash-object --stdin)
if [ "$(cat .venv/.sello-equipo 2>/dev/null)" != "$sello" ]; then
    echo "=> dependencias de Python"
    { [ -x .venv/bin/python ] || python3 -m venv .venv; } &&
        .venv/bin/python -m pip install -q --disable-pip-version-check -r requirements.txt -r requirements-dev.txt &&
        echo "$sello" > .venv/.sello-equipo || echo "aviso: pip fallo; estado.sh lo va a decir"
fi
sello=$(git hash-object frontend/package-lock.json)
if [ "$(cat frontend/node_modules/.sello-equipo 2>/dev/null)" != "$sello" ]; then
    echo "=> dependencias del frontend"
    (cd frontend && npm ci --no-audit --no-fund --loglevel=error) &&
        echo "$sello" > frontend/node_modules/.sello-equipo || echo "aviso: npm ci fallo; estado.sh lo va a decir"
fi
if ! ls -d "${PLAYWRIGHT_BROWSERS_PATH:-$HOME/.cache/ms-playwright}"/chromium-* >/dev/null 2>&1; then
    echo "=> Chromium para el e2e"
    (cd frontend && npm run e2e:browser) || echo "aviso: sin Chromium; estado.sh lo va a decir"
fi

# El proveedor de OmniRoute para este turno, solo en el entorno de opencode (nada en disco).
if cfg=$(python3 "$aqui/opencode_proveedor.py" "$modelo"); then
    [ -n "$cfg" ] && export OPENCODE_CONFIG_CONTENT="$cfg"
else
    echo "aviso: no pude armar el proveedor de $modelo; opencode usa su configuracion" >&2
fi
export GIT_AUTHOR_NAME=OpenCode GIT_AUTHOR_EMAIL=opencode@localhost
export GIT_COMMITTER_NAME=OpenCode GIT_COMMITTER_EMAIL=opencode@localhost
export EQUIPO_OPENCODE_MODELO="$modelo"

# Arreglos vacios con la forma ${a[@]+...}: el bash 3.2 de macOS los da por no definidos con set -u.
techo_cmd=()
command -v timeout >/dev/null 2>&1 && techo_cmd=(timeout --kill-after=60 "$techo")
mensaje=()
[ -n "$rol" ] && mensaje=("rol:" "$rol")
echo "=> turno en $dir con $modelo${rol:+ (rol: $rol)}"
# La entrada va cerrada: con una tuberia abierta, `opencode run` se queda esperando leerla.
${techo_cmd[@]+"${techo_cmd[@]}"} "$opencode" run --command equipo-dev -m "$modelo" --auto ${mensaje[@]+"${mensaje[@]}"} </dev/null
rc=$?
echo "=> opencode termino con $rc"
exit "$rc"
