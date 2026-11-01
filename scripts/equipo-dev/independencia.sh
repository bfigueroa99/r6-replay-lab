#!/usr/bin/env bash
# Independencia entre etapas de una ficha (principio 4 del playbook): un mismo
# contexto firma como mucho una de implementar (dev), revisar (revisor) y
# probar (qa). Es la condicion b de la puerta de merge como script, y lo que
# estado.sh usa para no darle a una sesion una ficha que no puede avanzar.
#
# Por que existe. La puerta b comparaba a ojo los ids de `turnos:`, que eran
# solo el minuto de arranque (`20261030T1653Z`), y fallaba en los dos sentidos:
# el 2026-10-30 el po y el revisor de una tanda simultanea firmaron el mismo
# id, y el 2026-11-01 una misma conversacion de Claude corrio el dev de la 71
# (20261031T2135Z) y el turno siguiente como revisor (20261101T0331Z): ids
# distintos, misma memoria. Ese revisor no tenia otra cosa que revisar y el
# turno se perdio entero. Desde turno.sh el id es `AAAAMMDDTHHMMZ-<contexto>`.
# El contexto sale de CLAUDE_CODE_REMOTE_SESSION_ID: fijo para una misma sesion
# de la nube, aunque la Routine la retome muchas veces. Es conservador: los
# subagentes de una misma sesion lo comparten (la herramienta no los
# distingue), asi que un orquestador que lanza cada turno en un subagente nuevo
# le pasa a cada uno su propio `turno.sh --contexto <id>`. Sin sesion de la
# nube (OpenCode, el PC) el contexto es al azar: cada corrida arranca sin
# memoria. Las entradas viejas, sin contexto, se comparan por el id entero,
# como antes.
#
# Uso:  independencia.sh <rama> [--ficha <ruta>]          puerta b; salida 0 o 1
#       independencia.sh <rama> --puedo <rol> [--contexto C]
#           el contexto de este turno (EQUIPO_CONTEXTO o .git/equipo-dev.env)
#           puede firmar <rol> en la ficha de esa rama? salida 0 si, 1 no
#       independencia.sh --turnos "<linea turnos:>"        pares "rol id contexto"
#       independencia.sh --firmable "<linea turnos:>" <rol> <contexto>
#           lo mismo que --puedo pero sin git (lo usan estado.sh y pruebas.sh)
#       git show <ref>:scripts/equipo-dev/independencia.sh | bash -s -- ...
# Salida 2: uso invalido, rama o ficha que no existen.
set -u

etapas="dev revisor qa"

# Pares normalizados de una linea `turnos:`, uno por linea: "rol id contexto".
# Las notas entre parentesis se quitan antes de partir por comas (una nota
# puede llevar coma, como `(relevo de qa, P7)`). Lo que no es `rol id` sale
# como `ILEGIBLE <texto>`: leerlo a medias es lo que esto vino a evitar.
pares() {
    local linea=$1 e rol id ctx
    linea=${linea#turnos:}
    linea=$(printf '%s' "$linea" | sed -E 's/\([^)]*\)//g')
    while IFS= read -r e; do
        e=$(printf '%s' "$e" | sed -E 's/^[[:space:]]+//; s/[[:space:]]+$//')
        [ -n "$e" ] && [ "$e" != - ] || continue
        rol=$(printf '%s' "$e" | awk '{print tolower($1)}')
        id=$(printf '%s' "$e" | awk '{print $2}')
        case "$rol" in release|po|arquitecto|dev|revisor|qa|investigador) ;; *) echo "ILEGIBLE $e"; continue ;; esac
        if [[ "$id" =~ ^[0-9]{8}T[0-9]{4}Z-([A-Za-z0-9]{4,16})$ ]]; then ctx=${BASH_REMATCH[1]}
        elif [[ "$id" =~ ^[0-9]{8}T[0-9]{4}Z$ ]]; then ctx=$id
        else echo "ILEGIBLE $e"; continue
        fi
        echo "$rol $id $ctx"
    done <<< "$(printf '%s' "$linea" | tr ',' '\n')"
}

# Contextos (uno por linea, sin repetir) que firmaron un rol.
contextos() { printf '%s\n' "$1" | awk -v r="$2" '$1 == r { print $3 }' | sort -u; }

# 0 si el contexto puede firmar el rol: no firmo ninguna de las otras dos etapas.
firmable() {
    local p=$1 rol=$2 ctx=$3 otra
    case " $etapas " in *" $rol "*) ;; *) return 0 ;; esac
    for otra in $etapas; do
        [ "$otra" = "$rol" ] && continue
        contextos "$p" "$otra" | grep -qxF -- "$ctx" && { echo "no: este contexto ya firmo $otra"; return 1; }
    done
    echo "si"
    return 0
}

case "${1:-}" in
    --turnos) pares "${2:-}"; exit 0 ;;
    --firmable)
        [ $# -eq 4 ] && [ -n "$4" ] || { echo "uso: independencia.sh --firmable \"<turnos:>\" <rol> <contexto>" >&2; exit 2; }
        firmable "$(pares "$2")" "$3" "$4"; exit $? ;;
    ""|-*) echo "uso: independencia.sh <rama> [--puedo <rol>] [--contexto C] [--ficha <ruta>] | --turnos \"<linea>\" | --firmable \"<linea>\" <rol> <contexto>" >&2; exit 2 ;;
esac

rama=${1#origin/}; shift
puedo=""; ctx=""; ficha=""
while [ $# -gt 0 ]; do
    case "$1" in
        --puedo) puedo=${2:-}; shift 2 ;;
        --contexto) ctx=${2:-}; shift 2 ;;
        --ficha) ficha=${2:-}; shift 2 ;;
        *) echo "argumento desconocido: $1" >&2; exit 2 ;;
    esac
done
repo="$(git rev-parse --show-toplevel 2>/dev/null)" || { echo "no es un repo git" >&2; exit 2; }
cd "$repo" || exit 2
R="origin/$rama"
git rev-parse -q --verify "$R^{commit}" >/dev/null || { echo "no existe $R (git fetch?)" >&2; exit 2; }
if [ -z "$ficha" ]; then
    ficha=$(git -c core.quotePath=false diff --name-only --diff-filter=A "origin/dev...$R" -- docs/backlog 2>/dev/null | grep -E 'docs/backlog/[0-9]+-' | head -1)
fi
[ -n "$ficha" ] || { echo "la rama no agrega ninguna ficha docs/backlog/NN-*.md" >&2; exit 2; }
t=$(git show "$R:$ficha" 2>/dev/null | grep -m1 '^turnos:')
p=$(pares "$t")

if [ -n "$puedo" ]; then
    if [ -z "$ctx" ]; then
        ctx=${EQUIPO_CONTEXTO:-}
        env_file="$(git rev-parse --git-dir)/equipo-dev.env"
        [ -z "$ctx" ] && [ -f "$env_file" ] && ctx=$(sed -n 's/^export EQUIPO_CONTEXTO=//p' "$env_file" | head -1)
    fi
    [ -n "$ctx" ] || { echo "sin contexto: corre turno.sh o pasa --contexto" >&2; exit 2; }
    printf 'INDEPENDENCIA %s puede firmar %s en %s: ' "$ctx" "$puedo" "$ficha"
    firmable "$p" "$puedo" "$ctx"; exit $?
fi

det=""
ileg=$(printf '%s\n' "$p" | grep '^ILEGIBLE ' | sed 's/^ILEGIBLE //' | tr '\n' ';')
[ -n "$ileg" ] && det="$det entradas ilegibles en turnos: $ileg"
for e in $etapas; do [ -n "$(contextos "$p" "$e" | grep .)" ] || det="$det falta $e;"; done
set -- $etapas
while [ $# -gt 1 ]; do
    a=$1; shift
    for b in "$@"; do
        c=$(comm -12 <(contextos "$p" "$a" | grep .) <(contextos "$p" "$b" | grep .) | tr '\n' ' ')
        [ -n "$c" ] && det="$det $a y $b comparten contexto ${c% };"
    done
done
if [ -n "$det" ]; then echo "INDEPENDENCIA_FALLA $ficha:$det"; exit 1; fi
echo "INDEPENDENCIA_OK $ficha: dev, revisor y qa de contextos distintos"
