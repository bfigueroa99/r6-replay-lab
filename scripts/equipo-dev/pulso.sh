#!/usr/bin/env bash
# Escribe en la rama backlog sin tocar el checkout del turno (worktree
# temporal): una linea de arranque o de cierre en PULSO.md y, al cerrar,
# ESTADO.md entero desde `estado.sh --tablero`. Es M3 y el cierre de M4.
#
# Por que: TURNOS_SIN_RASTRO veia que un disparo no dejo commit, pero no
# distinguia un disparo perdido (la Routine no arranco la sesion) de una sesion
# que arranco y murio. Con la linea de arranque, que turno.sh escribe al
# empezar, la diferencia queda en git. Y el tablero se regeneraba a mano en
# cada turno, la parte mas repetida y la que mas se desviaba de la plantilla.
#
# Uso:  pulso.sh arranque
#       pulso.sh cierre --resultado entrego|nada|parcial --turno "<que hizo>"
#             [--humano "<pedido>"]... [--cerrar H<n> "<motivo>"]...
#             [--maquinaria "<idea>"]... [--rutina "<estado del prompt>"]
#       git show <ref>:scripts/equipo-dev/pulso.sh | bash -s -- cierre ...
# Lee rol, roles, sesion, motivo y franja de .git/equipo-dev.env (turno.sh).
# Imprime `PULSO_OK <sha>` o `CIERRE_OK <sha>` (salida 0), `PULSO_PAUSA` (no
# escribe: P1) o `PULSO_FALLA: <motivo>` (salida 1). Hasta 3 intentos: cada
# uno parte del backlog de origin recien traido, asi no hay nada que mergear.
set -u
B=claude/equipo-dev/backlog
RB=origin/$B
# Lineas de PULSO.md que se guardan: lo que estado.sh mira son 7 dias.
DIAS_PULSO=14
yo_dir=""
if [ -n "${BASH_SOURCE[0]:-}" ] && [ -f "${BASH_SOURCE[0]}" ]; then yo_dir=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd); fi

tipo=${1:-}; shift || true
case "$tipo" in arranque|cierre) ;; *) echo "uso: pulso.sh arranque | cierre --resultado ... --turno ..." >&2; exit 2 ;; esac
resultado=""; turno=""; extra=()
while [ $# -gt 0 ]; do
    case "$1" in
        --resultado) resultado=${2:-}; shift 2 ;;
        --turno) turno=${2:-}; extra+=(--turno "${2:-}"); shift 2 ;;
        --humano|--maquinaria|--rutina) extra+=("$1" "${2:-}"); shift 2 ;;
        --cerrar) extra+=(--cerrar "${2:-}" "${3:-}"); shift 3 ;;
        *) echo "argumento desconocido: $1" >&2; exit 2 ;;
    esac
done
if [ "$tipo" = cierre ]; then
    case "$resultado" in entrego|nada|parcial) ;; *) echo "PULSO_FALLA: --resultado tiene que ser entrego, nada o parcial"; exit 1 ;; esac
    [ -n "$turno" ] || { echo "PULSO_FALLA: falta --turno \"<que hizo>\""; exit 1; }
fi

repo="$(git rev-parse --show-toplevel 2>/dev/null)" || { echo "PULSO_FALLA: no es un repo git"; exit 1; }
cd "$repo"
gitdir="$(git rev-parse --git-dir)"; case "$gitdir" in /*) ;; *) gitdir="$repo/$gitdir" ;; esac
EQUIPO_ROL="" EQUIPO_ROLES="" EQUIPO_SESION="" EQUIPO_MOTIVO="" EQUIPO_RELOJ="" EQUIPO_FRANJA="" EQUIPO_REF=""
# shellcheck disable=SC1090
[ -f "$gitdir/equipo-dev.env" ] && . "$gitdir/equipo-dev.env"
[ -n "$EQUIPO_SESION" ] || { echo "PULSO_FALLA: sin .git/equipo-dev.env (correr turno.sh primero)"; exit 1; }
roles=${EQUIPO_ROLES:-$EQUIPO_ROL}
ahora=${EQUIPO_AHORA:-$(date -u +%s)}
iso=$(date -u -d "@$ahora" +%FT%H:%MZ)
una_linea() { printf '%s' "$1" | tr '\n|' ' /' | cut -c1-240; }
if [ "$tipo" = arranque ]; then
    linea="$iso $EQUIPO_SESION arranque $roles | $(una_linea "$EQUIPO_MOTIVO") | reloj $EQUIPO_RELOJ franja $EQUIPO_FRANJA"
    mensaje="Pulso: arranque $roles $EQUIPO_SESION"
else
    linea="$iso $EQUIPO_SESION cierre $roles | $resultado | $(una_linea "$turno")"
    mensaje="Estado: turno $roles $EQUIPO_SESION"
fi

hermano() { # script args...
    local s=$1; shift
    if [ -n "$yo_dir" ] && [ -f "$yo_dir/$s" ]; then bash "$yo_dir/$s" "$@"
    else git show "${EQUIPO_REF:-origin/main}:scripts/equipo-dev/$s" | bash -s -- "$@"
    fi
}

# El tablero muestra todas las ramas: se traen frescas una vez; en los
# reintentos alcanza con la de backlog.
git fetch -q origin main '+refs/heads/claude/*:refs/remotes/origin/claude/*' 2>/dev/null
wt=$(mktemp -d)
limpiar() { git worktree remove --force "$wt" >/dev/null 2>&1; rm -rf "$wt"; git worktree prune >/dev/null 2>&1; }
trap limpiar EXIT
intento=0; ultimo_error=""
while [ "$intento" -lt 3 ]; do
    intento=$((intento + 1))
    git fetch -q origin "+refs/heads/$B:refs/remotes/$RB" 2>/dev/null
    if ! git rev-parse -q --verify "$RB" >/dev/null; then
        echo "PULSO_FALLA: no existe $RB (la crea el primer turno, ver Fichas en SKILL.md)"; exit 1
    fi
    # P1: con PAUSA nadie empuja nada, tampoco el pulso.
    if git cat-file -e "$RB:docs/backlog/PAUSA" 2>/dev/null; then echo "PULSO_PAUSA"; exit 0; fi
    limpiar; wt=$(mktemp -d)
    git worktree add -q --detach "$wt" "$RB" 2>/dev/null || { ultimo_error="worktree"; continue; }
    p="$wt/docs/backlog/PULSO.md"
    mkdir -p "$wt/docs/backlog"
    # union: dos turnos que agregan una linea a la vez no chocan si alguien
    # mergea a mano la rama backlog.
    grep -qx 'PULSO.md merge=union' "$wt/docs/backlog/.gitattributes" 2>/dev/null \
        || echo 'PULSO.md merge=union' >> "$wt/docs/backlog/.gitattributes"
    if [ ! -f "$p" ]; then
        cat > "$p" <<'EOF'
# Pulso del equipo

Una linea por arranque y por cierre de cada turno: la escribe
`scripts/equipo-dev/pulso.sh` y nadie la edita a mano. `estado.sh` la lee
para separar un disparo perdido (sin arranque) de una sesion que arranco y
murio (arranque sin cierre), y para ver roles que cierran sin entregar nada.
Formato: `<hora UTC> <sesion> arranque|cierre <roles> | <motivo o resultado> | <detalle>`.
Se guardan 14 dias.

EOF
    fi
    corte=$(date -u -d "@$(( ahora - DIAS_PULSO * 86400 ))" +%FT%H:%MZ)
    awk -v c="$corte" '!/^[0-9]{4}-[0-9]{2}-[0-9]{2}T/ || $1 >= c' "$p" > "$p.tmp" && mv "$p.tmp" "$p"
    echo "$linea" >> "$p"
    if [ "$tipo" = cierre ]; then
        previo=$(git show "$RB:docs/backlog/ESTADO.md" 2>/dev/null | sed -n '/^## Para el equipo/,$p')
        if ! hermano estado.sh --tablero --sin-fetch "${extra[@]}" > "$wt/docs/backlog/ESTADO.md.nuevo" 2>/dev/null; then
            ultimo_error="estado.sh --tablero fallo"; continue
        fi
        nuevo=$(sed -n '/^## Para el equipo/,$p' "$wt/docs/backlog/ESTADO.md.nuevo")
        # `## Para el equipo` es del humano: si el tablero no lo trae igual,
        # no se escribe nada.
        if [ -n "$previo" ] && [ "$previo" != "$nuevo" ]; then
            echo "PULSO_FALLA: el tablero no conserva \`## Para el equipo\` tal cual; no se escribe"; exit 1
        fi
        grep -q '^# Estado del equipo' "$wt/docs/backlog/ESTADO.md.nuevo" || { ultimo_error="tablero vacio"; continue; }
        mv "$wt/docs/backlog/ESTADO.md.nuevo" "$wt/docs/backlog/ESTADO.md"
    fi
    archivos=(docs/backlog/PULSO.md docs/backlog/.gitattributes)
    [ "$tipo" = cierre ] && archivos+=(docs/backlog/ESTADO.md)
    git -C "$wt" add "${archivos[@]}"
    git -C "$wt" commit -q -m "$mensaje" || { ultimo_error="commit"; continue; }
    if git -C "$wt" push -q origin "HEAD:refs/heads/$B" 2>/dev/null; then
        sha=$(git -C "$wt" rev-parse --short HEAD)
        git fetch -q origin "+refs/heads/$B:refs/remotes/$RB" 2>/dev/null
        if [ "$tipo" = arranque ]; then echo "PULSO_OK $sha"; else echo "CIERRE_OK $sha"; fi
        exit 0
    fi
    ultimo_error="push rechazado"
    sleep $(( intento * 2 ))
done
echo "PULSO_FALLA: $ultimo_error tras $intento intentos"
exit 1
