#!/usr/bin/env bash
# Decide que rol del equipo lidera esta iteracion: el que el pipeline necesita,
# leyendo la linea RESUMEN de `estado.sh --resumen` (sale de git y de nada
# mas: cero estado compartido que una sesion muerta pueda dejar a medias). El
# reloj UTC solo desempata cuando nada espera.
# Uso:  scripts/equipo-dev/turno.sh                  # el rol lo da el estado
#       scripts/equipo-dev/turno.sh revisor          # fuerza un rol (disparo manual)
#       scripts/equipo-dev/turno.sh --simular "aprobado=1 hora=0905"   # prueba la regla, sin git
#       git show <ref>:scripts/equipo-dev/turno.sh | bash -s -- [rol] [--simular "k=v ..."]
#
# Las variables de shell no sobreviven entre comandos de Claude Code ni llegan
# a los subagentes, asi que el resultado se guarda en .git/equipo-dev.env (no
# se commitea nunca) y cada comando que lo necesite empieza con
#   source "$(git rev-parse --git-dir)/equipo-dev.env"
# Ademas se imprime entero, para que quede a la vista en la salida.
#
# La franja es la de 3 horas mas cercana, no la que contiene al minuto actual:
# asi un arranque demorado hasta 88 minutos cae en la franja que le tocaba.
#
# El cierre es lo que llegue primero: 135 minutos desde el arranque, o 15
# minutos antes del disparo de la franja siguiente. El turno largo deja que un
# tramo de funcionalidad quepa en un solo Dev; el tope por franja evita que un
# arranque demorado se coma el turno del rol que viene.
#
# La franja 7 se alterna: los dias pares (contados desde 1970, por el disparo
# y no por el arranque) investiga, los impares revisa. Ocho franjas de 3 horas
# no dejan lugar para un rol mas, y el revisor de las 12:01 sigue todos los dias.
#
# --simular "k=v ...": toma los contadores dados en vez de leer git (hora=HHMM
# reemplaza al reloj, fecha=AAAA-MM-DD al dia), imprime solo la decision y no
# escribe nada. Es lo que pruebas.sh usa para fijar la regla.
set -u
roles=(release po arquitecto dev revisor dev qa revisor)

rol_pedido=""; simular=no; sim=""
while [ $# -gt 0 ]; do
    case "$1" in
        --simular) simular=si; sim="${2:-}"; shift; [ $# -gt 0 ] && shift ;;
        *) rol_pedido="$1"; shift ;;
    esac
done
if [ -n "$rol_pedido" ]; then
    case "$rol_pedido" in
        release|po|arquitecto|dev|revisor|qa|investigador) ;;
        *) echo "rol desconocido: '$rol_pedido' (release|po|arquitecto|dev|revisor|qa|investigador, en minuscula)" >&2; exit 1 ;;
    esac
fi

# Contadores del pipeline. Lo que RESUMEN no traiga vale 0; los topes, lo que
# dice el playbook. Son siempre enteros validados: por eso se comparan sin comillas.
propuesto=0 disenado=0 en_curso=0 huerfanas=0 implementado=0 revisado=0 con_hallazgos=0
aprobado=0 entregado=0 espera_humano=0 cola=0 total=0
tope_cola=4 tope_total=6 tope_propuesto=6 tope_disenado=3
ideas_libres=0 sin_merge=no pausa=no sin_rastro_48h=0
hora=""; fecha=""
# Carga pares k=v (de RESUMEN o de --simular). Solo nombres conocidos y solo
# valores con la forma esperada: lo demas se ignora y queda en su valor por defecto.
cargar() {
    local kv k v
    for kv in $1; do
        k=${kv%%=*}; v=${kv#*=}
        case "$k" in
            propuesto|disenado|en_curso|huerfanas|implementado|revisado|con_hallazgos|aprobado|entregado|espera_humano|cola|total|tope_cola|tope_total|tope_propuesto|tope_disenado|ideas_libres|sin_rastro_48h)
                [[ "$v" =~ ^[0-9]+$ ]] && printf -v "$k" '%s' "$v" ;;
            sin_merge|pausa) printf -v "$k" '%s' "$v" ;;
            hora) [[ "$v" =~ ^[0-9]{4}$ ]] && hora=$v ;;
            fecha) [[ "$v" =~ ^[0-9]{4}-[0-9]{2}-[0-9]{2}$ ]] && fecha=$v ;;
        esac
    done
}

con_resumen=si; ref=""; gitdir=""
if [ "$simular" = si ]; then
    cargar "$sim"
else
    gitdir="$(git rev-parse --git-dir 2>/dev/null)" || { echo "no es un repo git" >&2; exit 1; }
    # El playbook se lee de main si ya esta ahi; si no, de la rama donde vive.
    for ref in origin/main origin/claude/equipo-dev/playbook; do git cat-file -e "$ref:.claude/skills/equipo-dev/SKILL.md" 2>/dev/null && break; done
    git cat-file -e "$ref:.claude/skills/equipo-dev/SKILL.md" 2>/dev/null || {
        echo "SIN_PLAYBOOK: ni origin/main ni origin/claude/equipo-dev/playbook tienen .claude/skills/equipo-dev/SKILL.md" >&2
        exit 2
    }
    linea=$(git show "$ref:scripts/equipo-dev/estado.sh" | bash -s -- --resumen 2>/dev/null | grep -m1 '^RESUMEN ')
    if [ -n "$linea" ]; then cargar "${linea#RESUMEN }"; else con_resumen=no; fi
fi

inicio=$(date -u +%s)
if [ -n "$hora" ]; then
    min=$(( 10#${hora:0:2} * 60 + 10#${hora:2:2} ))
else
    min=$(( 10#$(date -u +%H) * 60 + 10#$(date -u +%M) ))
fi
franja=$(( (min + 90) / 180 % 8 ))
medianoche=$(date -u -d "${fecha:-$(date -u -d "@$inicio" +%F)}" +%s)
# Sin el % 8: cerca de medianoche la franja 0 que toca es la del dia siguiente.
disparo=$(( medianoche + ((min + 90) / 180 * 180 + 1) * 60 ))
[ "$franja" -eq 7 ] && [ $(( disparo / 86400 % 2 )) -eq 0 ] && roles[7]=investigador
reloj=${roles[$franja]}

# Unica copia de la regla: el primero que aplique. Terminar antes que empezar:
# lo que ya tiene codigo avanza (release, qa, revisor, dev) antes de abrir
# papel nuevo; el reloj decide solo cuando nada espera.
rol=""; motivo=""
elegir_rol() {
    if [ -n "$rol_pedido" ]; then rol=$rol_pedido; motivo=pedido
    elif [ "$con_resumen" = no ]; then rol=$reloj; motivo="sin resumen: reloj"
    elif [ $aprobado -gt 0 ]; then rol=release; motivo="por estado: $aprobado aprobado"
    elif [ $entregado -gt 0 ]; then rol=release; motivo="por estado: $entregado entregado"
    elif [ $revisado -gt 0 ]; then rol=qa; motivo="por estado: $revisado revisado"
    elif [ $implementado -gt 0 ]; then rol=revisor; motivo="por estado: $implementado implementado"
    elif [ $con_hallazgos -gt 0 ] || [ $huerfanas -gt 0 ]; then rol=dev; motivo="por estado: $con_hallazgos con_hallazgos, $huerfanas huerfanas"
    elif [ "$reloj" = investigador ]; then rol=investigador; motivo="reloj: investigador"
    elif [ $(( propuesto + disenado )) -eq 0 ]; then rol=po; motivo="papel vacio"
    elif [ $disenado -gt 0 ] && [ $cola -lt $tope_cola ] && [ $total -lt $tope_total ]; then rol=dev; motivo="por estado: $disenado disenado, lugar en cola"
    elif [ $propuesto -gt 0 ] && [ $disenado -lt $tope_disenado ]; then rol=arquitecto; motivo="por estado: $propuesto propuesto, $disenado disenado de $tope_disenado"
    elif [ $propuesto -lt $tope_propuesto ]; then rol=po; motivo="papel corto: $propuesto propuesto de $tope_propuesto"
    elif [ $ideas_libres -lt 10 ]; then rol=investigador; motivo="ideas libres: $ideas_libres de 10"
    else rol=$reloj; motivo="nada tomable: reloj"
    fi
}
elegir_rol

if [ "$simular" = si ]; then
    echo "rol=$rol motivo=$motivo reloj=$reloj franja=$franja"
    exit 0
fi
[ "$con_resumen" = no ] && echo "# aviso: sin resumen, rol por reloj"

cierre=$(( inicio + 135 * 60 ))
tope_franja=$(( disparo + (180 - 15) * 60 ))
[ "$tope_franja" -lt "$cierre" ] && cierre=$tope_franja
minutos=$(( (cierre - inicio) / 60 ))
env_file="$gitdir/equipo-dev.env"
{
    echo "export EQUIPO_ROL=$rol"
    echo "export EQUIPO_FRANJA=$franja"
    echo "export EQUIPO_MOTIVO=\"$motivo\""
    echo "export EQUIPO_RELOJ=$reloj"
    echo "export EQUIPO_INICIO=$inicio"
    echo "export EQUIPO_SESION=$(date -u -d "@$inicio" +%Y%m%dT%H%MZ)"
    echo "export EQUIPO_CIERRE=$(date -u -d "@$cierre" +%H:%M)"
    echo "export EQUIPO_MINUTOS=$minutos"
    echo "export EQUIPO_REF=$ref"
} > "$env_file"
cat "$env_file"
echo "# turno: $rol | motivo: $motivo | reloj: $reloj (franja $franja) | sesion $(date -u -d "@$inicio" +%Y%m%dT%H%MZ) | inicio $(date -u -d "@$inicio" +%H:%M) UTC | cerrar a las $(date -u -d "@$cierre" +%H:%M) UTC ($minutos min) | playbook $ref | variables en $env_file"
