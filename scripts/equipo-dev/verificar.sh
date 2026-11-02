#!/usr/bin/env bash
# Corre scripts/check.sh sobre el commit actual y lo espera en PRIMER PLANO,
# en tramos que caben en una llamada a Bash. Es la unica forma en que el equipo
# corre check.sh en la nube.
#
# Por que existe: check.sh completo tarda 192 s en la nube (852 tests de
# backend, 133 de vitest, build y 53 e2e, medido el 2026-11-01 en un
# contenedor de 4 CPU; con sesiones simultaneas tarda mas). La herramienta Bash
# de Claude Code manda a segundo plano todo comando que pase de 120 s sin
# `timeout`, corta en 600 s aun con `timeout`, y bloquea un `sleep` suelto. Y en
# una Routine el turno terminado es la corrida terminada: el 2026-11-01 una
# Routine de otro proyecto del dueno lanzo su puerta en segundo plano, cerro el
# turno con "espero a que termine" y dejo un reclamo empujado sin nada
# mergeado. Este script lanza check.sh desacoplado (sobrevive al corte de la
# llamada), espera hasta --max segundos y sale 124 si sigue corriendo: se
# vuelve a llamar igual, mientras salga 124, y retoma la misma corrida.
#
# Uso (desde la raiz del checkout que se quiere verificar):
#   bash scripts/equipo-dev/verificar.sh [--sin-e2e] [--max S] [--de-nuevo]
#   bash scripts/equipo-dev/verificar.sh --estado     # hay un verde completo para HEAD?
#   git show <ref>:scripts/equipo-dev/verificar.sh | bash -s -- [opciones]
#     --sin-e2e   SIN_E2E=1 (no vale para empujar codigo; solo para iterar)
#     --max S     tope de ESTA llamada (default 570: entra en un Bash de 600 s)
#     --de-nuevo  descarta un resultado guardado para HEAD y corre otra vez
#     --estado    no lanza nada: sale 0 si check.sh completo termino en verde
#                 sobre HEAD con el arbol limpio (la condicion f del Release)
# Desde Claude Code: herramienta Bash con `timeout: 600000`. Nunca Monitor,
# `sleep` suelto, run_in_background ni "espero la notificacion".
#
# La corrida se identifica por HEAD, mas un hash del diff si el arbol esta
# sucio, mas `-sin-e2e`: dos llamadas sobre el mismo estado comparten corrida,
# y un resultado ya terminado se informa sin volver a correr. Log y resultado
# en $(git rev-parse --git-dir)/equipo-dev-verificar/ (nunca se commitea).
#
# Salida: 0 verde (`VERDE ...`) · 1 rojo (`ROJO ...` y el final del log) ·
#         124 sigue corriendo: volver a llamar · 2 uso invalido o sin repo.
# EQUIPO_CHECK_CMD reemplaza a `bash scripts/check.sh` (gancho de pruebas.sh).
set -u

MAX=570 SIN_E2E=no DE_NUEVO=no ESTADO=no CADA=60
uso() { echo "verificar: $1" >&2; exit 2; }
while [ $# -gt 0 ]; do
    case "$1" in
        --max) [ $# -ge 2 ] && [[ "$2" =~ ^[0-9]+$ ]] || uso "--max necesita segundos"; MAX=$2; shift 2 ;;
        --sin-e2e) SIN_E2E=si; shift ;;
        --de-nuevo) DE_NUEVO=si; shift ;;
        --estado) ESTADO=si; shift ;;
        *) uso "opcion desconocida: $1 (--sin-e2e, --max S, --de-nuevo, --estado)" ;;
    esac
done

repo="$(git rev-parse --show-toplevel 2>/dev/null)" || uso "no es un repo git"
cd "$repo" || exit 2
dir="$(git rev-parse --absolute-git-dir)/equipo-dev-verificar"
mkdir -p "$dir" || exit 2
sha=$(git rev-parse HEAD 2>/dev/null) || uso "el repo no tiene commits"
corto=${sha:0:9}
# Solo archivos versionados: check.sh deja dist/, node_modules y la base del
# e2e, que no son cambios del turno.
sucio=$(git status --porcelain --untracked-files=no)

if [ "$ESTADO" = si ]; then
    if [ -n "$sucio" ]; then echo "SIN_VERDE $corto: el arbol tiene cambios sin commitear"; exit 1; fi
    if [ -f "$dir/$sha.fin" ] && [ "$(cut -d' ' -f1 < "$dir/$sha.fin")" = 0 ] \
        && sed 's/\x1b\[[0-9;]*m//g' "$dir/$sha.log" 2>/dev/null | grep -q '^Todo en verde\.'; then
        echo "VERDE $corto: check.sh completo en verde ($(cut -d' ' -f2- < "$dir/$sha.fin"))"; exit 0
    fi
    echo "SIN_VERDE $corto: no hay un check.sh completo en verde sobre este commit"; exit 1
fi

clave=$sha
[ -n "$sucio" ] && clave="$sha-sucio-$(git diff HEAD | git hash-object --stdin | cut -c1-12)"
[ "$SIN_E2E" = si ] && clave="$clave-sin-e2e"
log="$dir/$clave.log" fin="$dir/$clave.fin" pidf="$dir/$clave.pid"

vivo() { [ -f "$pidf" ] && kill -0 "$(cat "$pidf" 2>/dev/null)" 2>/dev/null; }

if [ "$DE_NUEVO" = si ] && ! vivo; then rm -f "$fin" "$pidf" "$log"; fi

# Un candado de lanzamiento de mas de un minuto es de una llamada que murio a
# mitad de lanzar: sin esto, ninguna llamada posterior volveria a lanzar.
[ -n "$(find "$dir" -maxdepth 1 -name "$clave.lanzando" -mmin +1 2>/dev/null)" ] && rmdir "$dir/$clave.lanzando" 2>/dev/null

if [ ! -f "$fin" ] && ! vivo; then
    # Sin resultado y sin proceso vivo: nunca corrio, o la corrida murio con el
    # contenedor. El candado (mkdir es atomico) evita que dos llamadas
    # simultaneas lancen dos corridas sobre el mismo estado.
    if mkdir "$dir/$clave.lanzando" 2>/dev/null; then
        [ -f "$pidf" ] && echo "la corrida anterior sobre $corto murio sin terminar: se relanza"
        rm -f "$log" "$pidf"
        cmd=${EQUIPO_CHECK_CMD:-bash scripts/check.sh}
        envs=""; [ "$SIN_E2E" = si ] && envs="SIN_E2E=1"
        # El hijo escribe "<codigo> <segundos>s" en .fin al terminar: es lo
        # unico que se mira para saber si termino, asi no depende de reapear
        # procesos. setsid (si esta) lo saca del grupo de la llamada.
        lanzador=(nohup); command -v setsid >/dev/null 2>&1 && lanzador=(setsid nohup)
        "${lanzador[@]}" bash -c '
            inicio=$(date +%s)
            env '"$envs"' '"$cmd"'
            codigo=$?
            echo "$codigo $(( $(date +%s) - inicio ))s" > "$1.tmp" && mv "$1.tmp" "$1"
        ' verificar "$fin" > "$log" 2>&1 < /dev/null &
        echo $! > "$pidf"
        rmdir "$dir/$clave.lanzando"
        echo "lanzado: check.sh sobre $corto$([ -n "$sucio" ] && echo ' (arbol sucio)')$([ "$SIN_E2E" = si ] && echo ', sin e2e'); log en $log"
    fi
fi

limpio() { sed 's/\x1b\[[0-9;]*m//g' "$log" 2>/dev/null; }
resumen() {
    local n_back n_front n_e2e
    n_back=$(limpio | grep -oE '^Ran [0-9]+ tests?' | tail -1 | grep -oE '[0-9]+')
    n_front=$(limpio | grep -oE '^[[:space:]]*Tests[[:space:]]+[0-9]+ passed' | tail -1 | grep -oE '[0-9]+')
    n_e2e=$(limpio | grep -oE '^[[:space:]]*[0-9]+ passed \(' | tail -1 | grep -oE '[0-9]+')
    printf '%s tests backend, %s vitest, %s e2e' "${n_back:-?}" "${n_front:-?}" "${n_e2e:-?}"
}
cola() { limpio | tail -n 1 | tr -d '\r' | cut -c1-120; }

inicio=$SECONDS ultimo=0
while :; do
    t=$(( SECONDS - inicio ))
    if [ -f "$fin" ]; then
        read -r codigo dur < "$fin"
        if [ "$codigo" = 0 ] && limpio | grep -q '^Todo en verde\.'; then
            echo "VERDE $corto en $dur: $(resumen). Todo en verde. (log: $log)"
            exit 0
        fi
        echo "ROJO $corto en $dur (salida $codigo): $(limpio | grep -m1 '^Fallo:' || echo 'sin linea Fallo')"
        echo "--- ultimas 40 lineas de $log"
        limpio | tail -n 40
        exit 1
    fi
    if ! vivo && [ ! -d "$dir/$clave.lanzando" ]; then
        # Murio sin escribir .fin (kill, contenedor reiniciado): la proxima
        # llamada la relanza.
        rm -f "$pidf"
        echo "la corrida de $corto murio sin terminar; vuelve a llamarme para relanzarla"
        exit 124
    fi
    if [ "$t" -ge "$MAX" ]; then
        echo "sigue corriendo tras ${MAX}s: vuelve a llamarme igual (tail: $(cola))"
        exit 124
    fi
    if [ $(( t - ultimo )) -ge "$CADA" ]; then
        echo "esperando check.sh sobre $corto (${t}s; tail: $(cola))"
        ultimo=$t
    fi
    sleep 1
done
