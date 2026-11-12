#!/usr/bin/env bash
# Decide que rol del equipo lidera esta iteracion: el que el pipeline necesita,
# leyendo la linea RESUMEN de `estado.sh --resumen` (sale de git y de nada
# mas: cero estado compartido que una sesion muerta pueda dejar a medias). El
# reloj UTC solo desempata cuando nada espera.
# Uso:  scripts/equipo-dev/turno.sh                  # el rol lo da el estado
#       scripts/equipo-dev/turno.sh revisor          # fuerza un rol (disparo manual)
#       scripts/equipo-dev/turno.sh --simular "aprobado=1 hora=0905"   # prueba la regla, sin git
#       scripts/equipo-dev/turno.sh --contexto <id>  # contexto propio (ver independencia.sh)
#       scripts/equipo-dev/turno.sh --seguir         # el rol siguiente de esta misma sesion, o `# fin:`
#       scripts/equipo-dev/turno.sh --seguir --simular "hechos=revisor,dev restante=80 disenado=1"
#       EQUIPO_AHORA=<epoch> scripts/equipo-dev/turno.sh [--seguir]   # fija el reloj (gancho de pruebas)
#       git show <ref>:scripts/equipo-dev/turno.sh | bash -s -- [rol] [--seguir] [--simular "k=v ..."]
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
# El cierre es lo que llegue primero: minutos_turno desde el arranque, o 15
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
#
# EQUIPO_SESION es `AAAAMMDDTHHMMZ-<contexto>`: el minuto solo no distinguia
# dos sesiones lanzadas juntas ni una misma conversacion retomada por la
# Routine (independencia.sh explica el contexto). estado.sh recibe el
# contexto y no cuenta como tomable una ficha cuya etapa siguiente este turno
# no puede firmar (`bloqueadas=` en RESUMEN): asi el rol no recae en un turno
# que no tiene nada que hacer.
#
# --seguir: la sesion encadena roles mientras le quede reloj. Un turno era un
# rol y un disparo: de 137 turnos medidos (2026-10-26 a 2026-11-12) la mediana
# uso 6 minutos de los 135 (p90 14, maximo 32), y a un disparo cada 4 horas
# cada ficha ocupaba tres disparos seguidos (dev, revisor, QA): 8 horas de dev
# a `dev`, 44 de mediana desde que el PO la propuso y 1,4 fichas por dia
# (fichas 61 a 74).
# Al terminar su rol, la sesion llama a --seguir: lee .git/equipo-dev.env,
# vuelve a pedir RESUMEN y aplica la misma regla sobre un estado al que se le
# quita lo que esta sesion no debe tomar. Cada rol se lidera una sola vez por
# sesion, y la sesion no hace dos etapas de una misma ficha: quien propuso no
# disena (el Arquitecto es el segundo filtro del PO), quien diseno no
# implementa (el diseno lo lee en frio otra sesion), y quien reviso o probo no
# arregla hallazgos (un dev del mismo contexto que reviso deja la puerta b sin
# salida). Los contadores no dicen de que ficha son, asi que el veto es por
# rol: lo que una sesion deja, lo toma la siguiente, y lo que encadena es
# trabajo de fichas distintas (probar una, revisar otra, implementar otra). El
# reloj no elige en --seguir: sin nada por estado, la sesion cierra. Tampoco
# se sigue con PAUSA, sin RESUMEN, si el rol vino pedido a mano, pasado
# tope_roles o si no quedan los minutos que el rol pide (minimo_de). Imprime
# el env y las lineas `# leer:` del rol nuevo (SKILL.md ya esta leido), o una
# sola linea `# fin: <motivo>`: ahi va el cierre comun, una vez por sesion.
#
# Al final imprime las lineas `# leer:`, cada una para su propia llamada a
# Bash: estado.sh, SKILL.md y el archivo del rol juntos pasan de 30 KB, y la
# herramienta guarda en un archivo la salida que pasa de ese tamano y muestra
# solo los primeros 2 KB.
set -u
roles=(release po arquitecto dev revisor dev qa revisor)
# Largo del turno; SKILL.md (P9) repite el numero y pruebas.sh lo verifica.
minutos_turno=135
# Roles que una sesion puede liderar (el primero y los que encadena --seguir).
# Con 4 entran QA y merge de una ficha, la revision de otra, un Dev y el
# Arquitecto o el PO que reponen el papel. SKILL.md (Seguir) repite el numero
# y pruebas.sh lo verifica.
tope_roles=4
# Minutos que tienen que quedar antes del cierre para empezar un rol
# encadenado: cerca del doble del turno mas largo medido de cada uno (dev 21,
# qa 19, revisor 32 con dos fichas, arquitecto 31, release 16, po 5). Si el
# reloj igual se acaba, vale P9.
minimo_de() {
    case "$1" in
        dev) echo 45 ;; qa) echo 35 ;; revisor|arquitecto|investigador) echo 30 ;;
        release) echo 20 ;; *) echo 15 ;;
    esac
}

rol_pedido=""; simular=no; sim=""; seguir=no; contexto=${EQUIPO_CONTEXTO:-}
while [ $# -gt 0 ]; do
    case "$1" in
        --simular) simular=si; sim="${2:-}"; shift; [ $# -gt 0 ] && shift ;;
        --contexto) contexto="${2:-}"; shift; [ $# -gt 0 ] && shift ;;
        --seguir) seguir=si; shift ;;
        *) rol_pedido="$1"; shift ;;
    esac
done
if [ -n "$rol_pedido" ]; then
    case "$rol_pedido" in
        release|po|arquitecto|dev|revisor|qa|investigador) ;;
        *) echo "rol desconocido: '$rol_pedido' (release|po|arquitecto|dev|revisor|qa|investigador, en minuscula)" >&2; exit 1 ;;
    esac
fi
# --seguir continua el turno que ya arranco: su contexto, su reloj y los roles
# que ya lidero salen de .git/equipo-dev.env, no de los argumentos.
hechos=""; restante=$minutos_turno; pedido_antes=no
if [ "$seguir" = si ]; then
    [ -z "$rol_pedido" ] || { echo "--seguir no lleva rol: lo decide el estado" >&2; exit 1; }
    if [ "$simular" = no ]; then
        gd="$(git rev-parse --git-dir 2>/dev/null)" || { echo "no es un repo git" >&2; exit 1; }
        [ -f "$gd/equipo-dev.env" ] || { echo "sin turno en curso: no existe $gd/equipo-dev.env (correr turno.sh sin --seguir)" >&2; exit 1; }
        # shellcheck disable=SC1091
        . "$gd/equipo-dev.env"
        [ -n "${EQUIPO_INICIO:-}" ] && [ -n "${EQUIPO_MINUTOS:-}" ] && [ -n "${EQUIPO_ROL:-}" ] \
            || { echo "$gd/equipo-dev.env incompleto (correr turno.sh sin --seguir)" >&2; exit 1; }
        contexto=${EQUIPO_CONTEXTO:-$contexto}
        hechos=${EQUIPO_ROLES:-$EQUIPO_ROL}
        restante=$(( (EQUIPO_INICIO + EQUIPO_MINUTOS * 60 - ${EQUIPO_AHORA:-$(date -u +%s)}) / 60 ))
        [ "${EQUIPO_MOTIVO:-}" = pedido ] && pedido_antes=si
    fi
fi
if [ -n "$contexto" ] && ! [[ "$contexto" =~ ^[A-Za-z0-9]{4,16}$ ]]; then
    echo "contexto invalido: '$contexto' (4 a 16 letras o digitos)" >&2; exit 1
fi
if [ -z "$contexto" ]; then
    sid=${CLAUDE_CODE_REMOTE_SESSION_ID:-}; sid=$(printf '%s' "${sid##*_}" | tr -cd 'A-Za-z0-9')
    if [ "${#sid}" -ge 6 ]; then contexto="c${sid: -6}"
    else contexto="r$(LC_ALL=C tr -dc 'a-z0-9' < /dev/urandom 2>/dev/null | head -c 6)"
    fi
fi

# Contadores del pipeline. Lo que RESUMEN no traiga vale 0; los topes, lo que
# dice el playbook. Son siempre enteros validados: por eso se comparan sin comillas.
propuesto=0 disenado=0 en_curso=0 huerfanas=0 implementado=0 revisado=0 con_hallazgos=0
aprobado=0 entregado=0 espera_humano=0 cola=0 total=0 bloqueadas=0
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
            propuesto|disenado|en_curso|huerfanas|implementado|revisado|con_hallazgos|aprobado|entregado|espera_humano|cola|total|tope_cola|tope_total|tope_propuesto|tope_disenado|ideas_libres|sin_rastro_48h|bloqueadas)
                [[ "$v" =~ ^[0-9]+$ ]] && printf -v "$k" '%s' "$v" ;;
            sin_merge|pausa) printf -v "$k" '%s' "$v" ;;
            hora) [[ "$v" =~ ^[0-9]{4}$ ]] && hora=$v ;;
            fecha) [[ "$v" =~ ^[0-9]{4}-[0-9]{2}-[0-9]{2}$ ]] && fecha=$v ;;
            # Solo para --seguir --simular: lo que en una sesion sale del env.
            hechos) [[ "$v" =~ ^[a-z,]+$ ]] && hechos=${v//,/ } ;;
            restante) [[ "$v" =~ ^-?[0-9]+$ ]] && restante=$v ;;
            pedido_antes) pedido_antes=$v ;;
        esac
    done
}

con_resumen=si; ref=""; gitdir=""
if [ "$simular" = si ]; then
    cargar "$sim"
else
    gitdir="$(git rev-parse --git-dir 2>/dev/null)" || { echo "no es un repo git" >&2; exit 1; }
    # El playbook se lee de dev, donde el equipo integra; main (release) y la
    # rama del playbook quedan de respaldo. Se prueba rutina.md y no SKILL.md:
    # solo el playbook nuevo lo tiene, asi que una ref con uno viejo no gana.
    for ref in origin/dev origin/main origin/claude/equipo-dev/playbook; do git cat-file -e "$ref:.claude/skills/equipo-dev/rutina.md" 2>/dev/null && break; done
    git cat-file -e "$ref:.claude/skills/equipo-dev/rutina.md" 2>/dev/null || {
        echo "SIN_PLAYBOOK: ninguna ref de la cadena (dev, main, rama del playbook) tiene .claude/skills/equipo-dev/rutina.md" >&2
        exit 2
    }
    linea=$(git show "$ref:scripts/equipo-dev/estado.sh" | EQUIPO_CONTEXTO=$contexto bash -s -- --resumen 2>/dev/null | grep -m1 '^RESUMEN ')
    if [ -n "$linea" ]; then cargar "${linea#RESUMEN }"; else con_resumen=no; fi
fi

# EQUIPO_AHORA fija el reloj, como en estado.sh: sin el, una prueba contra un
# repo de verdad daria otro rol segun la hora a la que corra (el reloj elige
# release o investigador antes que el papel en dos franjas del dia).
inicio=${EQUIPO_AHORA:-$(date -u +%s)}
if [ -n "$hora" ]; then
    min=$(( 10#${hora:0:2} * 60 + 10#${hora:2:2} ))
else
    min=$(( 10#$(date -u -d "@$inicio" +%H) * 60 + 10#$(date -u -d "@$inicio" +%M) ))
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
    # Lo "entregado (...)" espera al humano, pero el motivo puede ser transitorio
    # (sin herramientas, veto levantado): el Release del reloj lo reintenta.
    elif [ $espera_humano -gt 0 ] && [ "$reloj" = release ]; then rol=release; motivo="reloj: release, $espera_humano en espera"
    elif [ "$reloj" = investigador ]; then rol=investigador; motivo="reloj: investigador"
    elif [ $(( propuesto + disenado )) -eq 0 ]; then rol=po; motivo="papel vacio"
    elif [ $disenado -gt 0 ] && [ $cola -lt $tope_cola ] && [ $total -lt $tope_total ]; then rol=dev; motivo="por estado: $disenado disenado, lugar en cola"
    elif [ $propuesto -gt 0 ] && [ $disenado -lt $tope_disenado ]; then rol=arquitecto; motivo="por estado: $propuesto propuesto, $disenado disenado de $tope_disenado"
    elif [ $propuesto -lt $tope_propuesto ]; then rol=po; motivo="papel corto: $propuesto propuesto de $tope_propuesto"
    elif [ $ideas_libres -lt 10 ]; then rol=investigador; motivo="ideas libres: $ideas_libres de 10"
    else rol=$reloj; motivo="nada tomable: reloj"
    fi
}
# --seguir: la misma regla, sobre el estado sin lo que esta sesion no debe
# tomar, y sin reloj. `fin` queda con el motivo si la sesion no sigue.
fin=""
seguir_rol() {
    local h reloj_real=$reloj
    if [ "$pausa" = si ]; then fin="PAUSA"; return; fi
    if [ "$con_resumen" = no ]; then fin="sin resumen (fetch caido)"; return; fi
    if [ "$pedido_antes" = si ]; then fin="el rol vino pedido a mano: no encadena"; return; fi
    if [ "$(echo $hechos | wc -w)" -ge "$tope_roles" ]; then fin="tope de $tope_roles roles por sesion"; return; fi
    for h in $hechos; do
        case "$h" in
            release) aprobado=0; entregado=0 ;;
            # Quien reviso o probo no arregla en la misma sesion.
            qa) revisado=0; con_hallazgos=0; huerfanas=0 ;;
            revisor) implementado=0; con_hallazgos=0; huerfanas=0 ;;
            # Quien ya implemento no abre otra rama: para la regla, cola llena.
            dev) con_hallazgos=0; huerfanas=0; cola=$tope_cola ;;
            # Quien diseno no implementa lo que diseno (puede arreglar los
            # hallazgos de otra ficha), y quien propuso no disena.
            arquitecto) tope_disenado=0; cola=$tope_cola ;;
            po) tope_propuesto=0; tope_disenado=0 ;;
            investigador) ideas_libres=10 ;;
        esac
    done
    reloj=ninguno; elegir_rol; reloj=$reloj_real
    if [ "$rol" = ninguno ]; then fin="nada mas que tomar por estado"
    elif [[ " $hechos " == *" $rol "* ]]; then fin="lo que sigue es $rol, que esta sesion ya lidero"
    elif [ "$restante" -lt "$(minimo_de "$rol")" ]; then fin="quedan $restante min y $rol pide $(minimo_de "$rol")"
    else motivo="sigue: $motivo"
    fi
}
if [ "$seguir" = si ]; then seguir_rol; else elegir_rol; fi
# Lo que este contexto no puede firmar no conto arriba; se dice para que el
# informe explique por que no le toco revisar o probar.
[ "$bloqueadas" -gt 0 ] && [ "$motivo" != pedido ] && motivo="$motivo; $bloqueadas bloqueadas por independencia"

if [ "$simular" = si ]; then
    if [ "$seguir" = no ]; then echo "rol=$rol motivo=$motivo reloj=$reloj franja=$franja"
    elif [ -n "$fin" ]; then echo "fin=$fin"
    else echo "sigue=$rol motivo=$motivo"
    fi
    exit 0
fi
if [ -n "$fin" ]; then
    echo "# fin: $fin | roles de esta sesion: $hechos | ahora el cierre comun (ESTADO.md e informe, una sola vez)"
    exit 0
fi
[ "$con_resumen" = no ] && echo "# aviso: sin resumen, rol por reloj"

if [ "$seguir" = si ]; then
    # El reloj, la sesion y la franja son los del arranque: se copian del env.
    inicio=$EQUIPO_INICIO; minutos=$EQUIPO_MINUTOS; franja=${EQUIPO_FRANJA:-$franja}; reloj=${EQUIPO_RELOJ:-$reloj}
    sesion=${EQUIPO_SESION:-$(date -u -d "@$inicio" +%Y%m%dT%H%MZ)-$contexto}
    cierre_hm=${EQUIPO_CIERRE:-$(date -u -d "@$(( inicio + minutos * 60 ))" +%H:%M)}
    roles_sesion="$hechos $rol"
else
    cierre=$(( inicio + minutos_turno * 60 ))
    tope_franja=$(( disparo + (180 - 15) * 60 ))
    [ "$tope_franja" -lt "$cierre" ] && cierre=$tope_franja
    minutos=$(( (cierre - inicio) / 60 ))
    sesion=$(date -u -d "@$inicio" +%Y%m%dT%H%MZ)-$contexto
    cierre_hm=$(date -u -d "@$cierre" +%H:%M)
    roles_sesion=$rol
fi
env_file="$gitdir/equipo-dev.env"
{
    echo "export EQUIPO_ROL=$rol"
    echo "export EQUIPO_FRANJA=$franja"
    echo "export EQUIPO_MOTIVO=\"$motivo\""
    echo "export EQUIPO_RELOJ=$reloj"
    echo "export EQUIPO_INICIO=$inicio"
    echo "export EQUIPO_SESION=$sesion"
    echo "export EQUIPO_CONTEXTO=$contexto"
    echo "export EQUIPO_CIERRE=$cierre_hm"
    echo "export EQUIPO_MINUTOS=$minutos"
    echo "export EQUIPO_REF=$ref"
    echo "export EQUIPO_ROLES=\"$roles_sesion\""
} > "$env_file"
cat "$env_file"
if [ "$seguir" = si ]; then
    echo "# turno: sigue como $rol | motivo: $motivo | roles de esta sesion: $roles_sesion | sesion $sesion | quedan $restante de $minutos min, cerrar a las $cierre_hm UTC | playbook $ref | variables en $env_file"
else
    echo "# turno: $rol | motivo: $motivo | reloj: $reloj (franja $franja) | sesion $sesion | inicio $(date -u -d "@$inicio" +%H:%M) UTC | cerrar a las $cierre_hm UTC ($minutos min) | playbook $ref | variables en $env_file"
fi
# Lo que sigue, cada linea en su propia llamada a Bash (ver arriba). po,
# arquitecto e investigador leen ademas la Directiva de alcance. Al seguir,
# SKILL.md ya esta leido (y alcance.md, si un rol anterior lo leyo), y del
# estado alcanza con lo que cambio: papel, ramas de trabajo, destraba, cola y
# resumen. El resto (ramas borrables, `## Para el equipo`, rutina, alcance,
# entorno) son 3 de cada 4 bytes de la salida y ya se leyeron al arrancar; el
# Release lo lee entero igual, y el cierre comun tambien.
filtro=""
if [ "$seguir" = si ] && [ "$rol" != release ]; then
    filtro=" | sed -n '/^== papel/,/^== ramas del playbook/p;/^== destraba/,/^== alcance/p;/^== resumen/,/^== entorno/p'"
fi
echo "# leer: git show $ref:scripts/equipo-dev/estado.sh | EQUIPO_CONTEXTO=$contexto bash$filtro"
[ "$seguir" = si ] || echo "# leer: git show $ref:.claude/skills/equipo-dev/SKILL.md"
case "$rol" in po|arquitecto|investigador)
    case " $hechos " in *" po "*|*" arquitecto "*|*" investigador "*) ;; *) echo "# leer: git show $ref:.claude/skills/equipo-dev/alcance.md" ;; esac ;;
esac
echo "# leer: git show $ref:.claude/skills/equipo-dev/roles/$rol.md"
# Un rol pedido a mano no encadena: quien lo pidio quiere ese rol.
[ "$motivo" = pedido ] || echo "# al terminar el rol, antes del cierre comun: git show $ref:scripts/equipo-dev/turno.sh | bash -s -- --seguir"
