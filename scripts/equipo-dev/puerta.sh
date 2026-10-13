#!/usr/bin/env bash
# La puerta de merge del playbook (condiciones a-f de roles/release.md) como
# script que falla solo. Antes cada Release la verificaba a mano y un `turnos:`
# con notas, como `revisor 20261012T1640Z (QA sin revisado en cola)` en la
# ficha 35, se leia distinto en cada sesion.
#
# Uso:  puerta.sh <rama>                       la puerta entera, antes de mergear
#       puerta.sh <rama> --solo b               independencia (Revisor y QA antes de candar)
#       puerta.sh <rama> --solo d               rutas que mergea el humano
#       puerta.sh <rama> --como <rol> <sesion>  b mirada desde ese rol y sesion
#       puerta.sh --turnos "<linea turnos:>"    imprime los pares normalizados
#       puerta.sh --rutas-del-humano            imprime la lista de la condicion d
#       git show <ref>:scripts/equipo-dev/puerta.sh | bash -s -- <rama> ...
# Sin --como, el rol y la sesion salen de .git/equipo-dev.env (turno.sh).
#
# Una linea `PUERTA <x> OK|FALLA|MANUAL: detalle` por condicion y al final
# `PUERTA_OK` (salida 0; si hubo MANUAL, las nombra) o `PUERTA_FALLA: <letras>`
# (salida 1). MANUAL es lo que el script no puede ver sin herramientas de
# GitHub (el PR y sus comentarios): lo confirma el Release a mano.
set -u
B=origin/claude/equipo-dev/backlog

# Condicion d: lo que mergea el humano porque la nube no lo puede verificar o
# porque son las reglas del propio equipo. Termina en / = carpeta; con * =
# patron; si no, archivo exacto. estado.sh repite la lista y pruebas.sh
# verifica que coincidan.
RUTAS_DEL_HUMANO="CLAUDE.md .claude/ scripts/equipo-dev/ docs/backlog/README.md docs/backlog/PLANTILLA.md docs/backlog/ESTADO.plantilla.md docs/backlog/ALCANCE.md docs/backlog/INVESTIGACION.md docs/backlog/MAQUINARIA.md frontend/electron/ frontend/electron-builder.json packaging/ scripts/*.ps1 .github/"

# Pares "rol sesion" de una linea `turnos:`, uno por linea. Las notas entre
# parentesis se descartan antes de partir por comas (una nota puede llevar
# coma). Una entrada que no es `rol AAAAMMDDTHHMMZ` sale como `ILEGIBLE <texto>`:
# leerla a medias es justo lo que esto vino a evitar.
pares_turnos() {
    local linea=$1 e rol ses
    linea=${linea#turnos:}
    linea=$(printf '%s' "$linea" | sed -E 's/\([^)]*\)//g')
    while IFS= read -r e; do
        e=$(printf '%s' "$e" | sed -E 's/^[[:space:]]+//; s/[[:space:]]+$//')
        [ -n "$e" ] || continue
        [ "$e" = "-" ] && continue
        rol=$(printf '%s' "$e" | awk '{print tolower($1)}')
        ses=$(printf '%s' "$e" | awk '{print $2}')
        case "$rol" in release|po|arquitecto|dev|revisor|qa|investigador) ;; *) echo "ILEGIBLE $e"; continue ;; esac
        if [[ "$ses" =~ ^[0-9]{8}T[0-9]{4}Z$ ]]; then echo "$rol $ses"; else echo "ILEGIBLE $e"; fi
    done <<< "$(printf '%s' "$linea" | tr ',' '\n')"
}

es_del_humano() {
    # set -f: `scripts/*.ps1` es un patron para case, no un glob contra el disco.
    local f=$1 r -
    set -f
    for r in $RUTAS_DEL_HUMANO; do
        case "$r" in
            */) case "$f" in "$r"*) return 0 ;; esac ;;
            *'*'*) # shellcheck disable=SC2254
                case "$f" in $r) return 0 ;; esac ;;
            *) [ "$f" = "$r" ] && return 0 ;;
        esac
    done
    return 1
}

case "${1:-}" in
    --turnos) pares_turnos "${2:-}"; exit 0 ;;
    --rutas-del-humano) set -f; printf '%s\n' $RUTAS_DEL_HUMANO; exit 0 ;;
    ""|-*) echo "uso: puerta.sh <rama> [--solo a|b|c|d|e|f] [--como <rol> <sesion>] [--ficha <ruta>]" >&2; exit 2 ;;
esac

rama=${1#origin/}; shift
solo=""; como_rol=""; como_ses=""; ficha=""
while [ $# -gt 0 ]; do
    case "$1" in
        --solo) solo=${2:-}; shift 2 ;;
        --como) como_rol=${2:-}; como_ses=${3:-}; shift 3 ;;
        --ficha) ficha=${2:-}; shift 2 ;;
        *) echo "argumento desconocido: $1" >&2; exit 2 ;;
    esac
done

repo="$(git rev-parse --show-toplevel 2>/dev/null)" || { echo "no es un repo git" >&2; exit 2; }
cd "$repo"
gitdir="$(git rev-parse --git-dir)"
R="origin/$rama"
git rev-parse -q --verify "$R^{commit}" >/dev/null || { echo "PUERTA_FALLA: no existe $R (git fetch?)"; exit 1; }
env_file="$gitdir/equipo-dev.env"
EQUIPO_ROL=""; EQUIPO_SESION=""; EQUIPO_INICIO=""
# shellcheck disable=SC1090
[ -f "$env_file" ] && . "$env_file"
[ -n "$como_rol" ] || { como_rol=$EQUIPO_ROL; como_ses=$EQUIPO_SESION; }

if [ -z "$ficha" ]; then
    ficha=$(git -c core.quotePath=false diff --name-only --diff-filter=A "origin/main...$R" -- docs/backlog 2>/dev/null | grep -E 'docs/backlog/[0-9]+-' | head -1)
fi

fallas=""; manuales=""
linea() { # condicion estado detalle
    echo "PUERTA $1 $2: $3"
    case "$2" in FALLA) fallas="$fallas $1" ;; MANUAL) manuales="$manuales $1" ;; esac
}
toca() { [ -z "$solo" ] || [ "$solo" = "$1" ]; }

if toca a; then
    det=""
    git cat-file -e "$B:docs/backlog/PAUSA" 2>/dev/null && det="$det PAUSA en backlog;"
    git cat-file -e "$B:docs/backlog/SIN_MERGE" 2>/dev/null && det="$det SIN_MERGE en backlog;"
    if [ -n "$det" ]; then linea a FALLA "${det# }"; else linea a OK "sin PAUSA ni SIN_MERGE"; fi
fi

if toca b; then
    if [ -z "$ficha" ]; then
        linea b FALLA "la rama no agrega ninguna ficha docs/backlog/NN-*.md"
    else
        t=$(git show "$R:$ficha" 2>/dev/null | grep -m1 '^turnos:')
        pares=$(pares_turnos "$t")
        det=""
        ileg=$(printf '%s\n' "$pares" | grep '^ILEGIBLE ' | sed 's/^ILEGIBLE //' | tr '\n' ';')
        [ -n "$ileg" ] && det="$det entradas ilegibles en turnos: $ileg"
        ses_de() { printf '%s\n' "$pares" | awk -v r="$1" '$1 == r {print $2}' | sort -u; }
        D=$(ses_de dev); Rv=$(ses_de revisor); Q=$(ses_de qa)
        comun() { comm -12 <(printf '%s\n' "$1" | grep .) <(printf '%s\n' "$2" | grep .) | tr '\n' ' '; }
        x=$(comun "$D" "$Rv"); [ -n "$x" ] && det="$det dev y revisor en la misma sesion: $x;"
        x=$(comun "$D" "$Q"); [ -n "$x" ] && det="$det dev y qa en la misma sesion: $x;"
        x=$(comun "$Rv" "$Q"); [ -n "$x" ] && det="$det revisor y qa en la misma sesion: $x;"
        if [ -n "$como_rol" ] && [ -n "$solo" ]; then
            # Mirada desde un rol que va a firmar: que esta sesion no haya
            # firmado otra etapa de la misma ficha.
            otras=""
            case "$como_rol" in
                revisor) otras="$D $Q" ;;
                qa) otras="$D $Rv" ;;
                dev) otras="$Rv $Q" ;;
                release) otras="$D $Rv $Q" ;;
            esac
            for s in $otras; do [ "$s" = "$como_ses" ] && det="$det esta sesion ($como_ses) ya firmo otra etapa de la ficha;"; done
        else
            [ -n "$D" ] || det="$det falta dev en turnos;"
            [ -n "$Rv" ] || det="$det falta revisor en turnos;"
            [ -n "$Q" ] || det="$det falta qa en turnos;"
            # La revision tiene que ser posterior a la ultima implementacion y la
            # QA posterior a la ultima revision: si no, se mergea algo que nadie vio.
            ult() { printf '%s\n' "$pares" | grep -v '^ILEGIBLE' | awk -v r="$1" '$1 == r {n=NR} END {print n+0}'; }
            ud=$(ult dev); ur=$(ult revisor); uq=$(ult qa)
            if [ "$ud" -gt 0 ] && [ "$ur" -gt 0 ] && [ "$ur" -lt "$ud" ]; then det="$det la ultima revision es anterior al ultimo dev;"; fi
            if [ "$ur" -gt 0 ] && [ "$uq" -gt 0 ] && [ "$uq" -lt "$ur" ]; then det="$det la ultima QA es anterior a la ultima revision;"; fi
            if [ "$como_rol" = release ] && [ -n "$como_ses" ]; then
                for s in $D $Rv $Q; do [ "$s" = "$como_ses" ] && det="$det el Release ($como_ses) firmo una etapa de la ficha: no la mergea;"; done
            fi
            git log -p --format= "origin/main..$R" -- "$ficha" | grep -q '^+estado: aprobado' \
                || det="$det la ficha nunca estuvo en aprobado en esta rama;"
        fi
        if [ -n "$det" ]; then linea b FALLA "${det# }"; else linea b OK "dev, revisor y qa de sesiones distintas, en orden"; fi
    fi
fi

if toca c; then
    det=""
    # Un commit humano (sin merges: un "Update branch" no es un pedido) esta
    # respondido si despues hay un commit de Claude que toca la ficha.
    hum=$(git log --no-merges "origin/main..$R" --format='%ct %an' 2>/dev/null | grep -vE '^[0-9]+ Claude' | head -1)
    if [ -n "$hum" ]; then
        th=${hum%% *}
        tc=0; [ -n "$ficha" ] && tc=$(git log -1 --format=%ct "origin/main..$R" --author='^Claude' -- "$ficha" 2>/dev/null)
        [ "${tc:-0}" -gt "$th" ] || det="$det commit de ${hum#* } sin respuesta en la ficha;"
    fi
    if [ -n "$ficha" ]; then
        abiertas=$(git show "$R:$ficha" 2>/dev/null | sed -n '/^## Para el humano/,/^## /p' | sed '1d;/^## /d' \
            | grep '?' | grep -viE '~~|respondid|resuelt' | head -3 | tr '\n' ' ')
        [ -n "$abiertas" ] && det="$det pregunta abierta en Para el humano: $abiertas;"
    fi
    if [ -n "$det" ]; then linea c FALLA "${det# }"; else linea c OK "sin commits humanos sin respuesta ni preguntas abiertas en la ficha"; fi
    [ -n "$solo" ] || linea c2 MANUAL "comentarios del PR y 'changes requested': mirarlos con mcp__github"
fi

if toca d; then
    det=""
    while IFS= read -r f; do
        [ -n "$f" ] || continue
        es_del_humano "$f" && det="$det $f"
    done <<< "$(git -c core.quotePath=false diff --name-only "origin/main...$R" 2>/dev/null)"
    if [ -n "$det" ]; then linea d FALLA "toca lo que mergea el humano:$det"; else linea d OK "no toca lo que mergea el humano"; fi
fi

if toca e && [ -z "$solo" ]; then
    linea e MANUAL "PR abierto contra main: confirmarlo con mcp__github (sin herramientas no se mergea)"
fi

if toca f; then
    det=""
    sha=$(git rev-parse "$R")
    git merge-base --is-ancestor origin/main "$R" || det="$det origin/main no esta fusionado en la rama;"
    if [ "$(git rev-parse --abbrev-ref HEAD 2>/dev/null)" = "$rama" ] && [ "$(git rev-parse HEAD)" != "$sha" ]; then
        det="$det el HEAD local no esta empujado (o origin se movio);"
    fi
    # El verde que vale es el de check.sh completo, con e2e, sobre este commit
    # exacto y en esta sesion (sin env: en las ultimas 3 horas).
    desde=${EQUIPO_INICIO:-0}
    [ "$desde" -gt 0 ] || desde=$(( $(date -u +%s) - 10800 ))
    verde=$(awk -v s="$sha" -v d="$desde" '$1 == s && $2 >= d && $3 == "e2e"' "$gitdir/check-verde" 2>/dev/null | tail -1)
    [ -n "$verde" ] || det="$det sin check.sh completo en verde sobre ${sha:0:7} en esta sesion;"
    if [ -n "$det" ]; then linea f FALLA "${det# }"; else linea f OK "main fusionado, empujado y check.sh en verde sobre ${sha:0:7}"; fi
fi

if [ -n "$fallas" ]; then echo "PUERTA_FALLA:$fallas"; exit 1; fi
if [ -n "$manuales" ]; then echo "PUERTA_OK (a confirmar a mano:$manuales)"; else echo "PUERTA_OK"; fi
exit 0
