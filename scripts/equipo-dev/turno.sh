#!/usr/bin/env bash
# Decide que rol del equipo lidera esta iteracion: el que el pipeline necesita,
# leyendo la linea RESUMEN de `estado.sh --resumen` (sale de git y de nada
# mas: cero estado compartido que una sesion muerta pueda dejar a medias). El
# reloj UTC solo desempata cuando nada espera.
# Uso:  scripts/equipo-dev/turno.sh                  # el rol lo da el estado
#       scripts/equipo-dev/turno.sh revisor          # fuerza un rol (disparo manual)
#       scripts/equipo-dev/turno.sh --encadenar      # mismo turno, siguiente rol (ver abajo)
#       scripts/equipo-dev/turno.sh --simular "aprobado=1 hora=0905"   # prueba la regla, sin git
#       scripts/equipo-dev/turno.sh --encadenar --simular "roles=po queda=90 disenado=1 cola=1 total=1 hora=0305"
#       git show <ref>:scripts/equipo-dev/turno.sh | bash -s -- [rol] [--encadenar] [--simular "k=v ..."]
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
# --encadenar: los turnos cerraban a los ~5 minutos de un presupuesto de 135
# (medido sobre 33 turnos del 2026-10-08 al 2026-10-13), asi que una sesion
# que termino su rol con tiempo vuelve a elegir con el mismo RESUMEN, pero
# contado sin las fichas donde ya firmo una etapa incompatible (principio 4).
# Mantiene sesion, inicio y cierre; no repite rol; no pasa de
# max_roles_por_turno; no encadena con menos de minimo_para_encadenar minutos
# ni al rol del reloj por "nada tomable". max_roles_por_turno=1 apaga el
# encadenado (es la perilla de costo).
#
# --simular "k=v ...": toma los contadores dados en vez de leer git (hora=HHMM
# reemplaza al reloj, fecha=AAAA-MM-DD al dia; con --encadenar, roles=a,b y
# queda=<minutos>), imprime solo la decision y no escribe nada. Es lo que
# pruebas.sh usa para fijar la regla.
set -u
roles=(release po arquitecto dev revisor dev qa revisor)
# Largo del turno; SKILL.md (P9) repite el numero y pruebas.sh lo verifica.
minutos_turno=135
max_roles_por_turno=3
minimo_para_encadenar=40
# El Release que sigue a la QA que aprobo no repite su check.sh (puerta.sh f
# acepta el verde con solo docs encima): le alcanzan 20 minutos.
minimo_release=20

rol_pedido=""; simular=no; sim=""; encadenar=no
while [ $# -gt 0 ]; do
    case "$1" in
        --simular) simular=si; sim="${2:-}"; shift; [ $# -gt 0 ] && shift ;;
        --encadenar) encadenar=si; shift ;;
        *) rol_pedido="$1"; shift ;;
    esac
done
if [ -n "$rol_pedido" ]; then
    case "$rol_pedido" in
        release|po|arquitecto|dev|revisor|qa|investigador) ;;
        *) echo "rol desconocido: '$rol_pedido' (release|po|arquitecto|dev|revisor|qa|investigador, en minuscula)" >&2; exit 1 ;;
    esac
fi
yo_dir=""
if [ -n "${BASH_SOURCE[0]:-}" ] && [ -f "${BASH_SOURCE[0]}" ]; then yo_dir=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd); fi

# Contadores del pipeline. Lo que RESUMEN no traiga vale 0; los topes, lo que
# dice el playbook. Son siempre enteros validados: por eso se comparan sin comillas.
propuesto=0 disenado=0 en_curso=0 huerfanas=0 implementado=0 revisado=0 con_hallazgos=0
aprobado=0 entregado=0 espera_humano=0 cola=0 total=0
tope_cola=4 tope_total=6 tope_propuesto=6 tope_disenado=3
ideas_libres=0 sin_merge=no pausa=no sin_rastro_48h=0 papel_func=0 bug_p1=0
hora=""; fecha=""; sim_roles=""; sim_queda=""
# Carga pares k=v (de RESUMEN o de --simular). Solo nombres conocidos y solo
# valores con la forma esperada: lo demas se ignora y queda en su valor por defecto.
cargar() {
    local kv k v
    for kv in $1; do
        k=${kv%%=*}; v=${kv#*=}
        case "$k" in
            propuesto|disenado|en_curso|huerfanas|implementado|revisado|con_hallazgos|aprobado|entregado|espera_humano|cola|total|tope_cola|tope_total|tope_propuesto|tope_disenado|ideas_libres|sin_rastro_48h|papel_func|bug_p1)
                [[ "$v" =~ ^[0-9]+$ ]] && printf -v "$k" '%s' "$v" ;;
            sin_merge|pausa) printf -v "$k" '%s' "$v" ;;
            hora) [[ "$v" =~ ^[0-9]{4}$ ]] && hora=$v ;;
            fecha) [[ "$v" =~ ^[0-9]{4}-[0-9]{2}-[0-9]{2}$ ]] && fecha=$v ;;
            roles) [[ "$v" =~ ^[a-z,]+$ ]] && sim_roles=$v ;;
            queda) [[ "$v" =~ ^[0-9]+$ ]] && sim_queda=$v ;;
        esac
    done
}

con_resumen=si; ref=""; gitdir=""
EQUIPO_SESION="" EQUIPO_INICIO="" EQUIPO_ROLES="" EQUIPO_ROL="" EQUIPO_CIERRE_EPOCH="" EQUIPO_REF=""
if [ "$simular" = si ]; then
    cargar "$sim"
else
    gitdir="$(git rev-parse --git-dir 2>/dev/null)" || { echo "no es un repo git" >&2; exit 1; }
    if [ "$encadenar" = si ]; then
        # shellcheck disable=SC1091
        [ -f "$gitdir/equipo-dev.env" ] && . "$gitdir/equipo-dev.env"
        [ -n "$EQUIPO_SESION" ] || { echo "ENCADENAR=no motivo=sin .git/equipo-dev.env: el primer rol sale de turno.sh sin --encadenar"; exit 3; }
    fi
    # El playbook se lee de main si ya esta ahi; si no, de la rama donde vive.
    # Se prueba rutina.md y no SKILL.md: solo el playbook nuevo lo tiene, asi
    # que un main con un playbook viejo mergeado no gana la cadena.
    for ref in origin/main origin/claude/equipo-dev/playbook; do git cat-file -e "$ref:.claude/skills/equipo-dev/rutina.md" 2>/dev/null && break; done
    git cat-file -e "$ref:.claude/skills/equipo-dev/rutina.md" 2>/dev/null || {
        echo "SIN_PLAYBOOK: ni origin/main ni origin/claude/equipo-dev/playbook tienen .claude/skills/equipo-dev/rutina.md" >&2
        exit 2
    }
    args=(--resumen)
    [ "$encadenar" = si ] && args+=(--excluir-sesion "$EQUIPO_SESION")
    if [ -n "$yo_dir" ] && [ -f "$yo_dir/estado.sh" ]; then
        linea=$(bash "$yo_dir/estado.sh" "${args[@]}" 2>/dev/null | grep -m1 '^RESUMEN ')
    else
        linea=$(git show "$ref:scripts/equipo-dev/estado.sh" | bash -s -- "${args[@]}" 2>/dev/null | grep -m1 '^RESUMEN ')
    fi
    if [ -n "$linea" ]; then cargar "${linea#RESUMEN }"; else con_resumen=no; fi
fi

inicio=$(date -u +%s)
[ "$encadenar" = si ] && [ -n "$EQUIPO_INICIO" ] && inicio=$EQUIPO_INICIO
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
    # Un bug de prioridad 1 (numeros mal, importacion que se cae) salta al
    # papel nuevo y puede pasar la cola por uno, como el hotfix de P4.
    elif [ $bug_p1 -gt 0 ] && [ $cola -le $tope_cola ]; then rol=dev; motivo="por estado: $bug_p1 bug prioridad 1"
    # Lo "entregado (...)" espera al humano, pero el motivo puede ser transitorio
    # (sin herramientas, veto levantado): el Release del reloj lo reintenta.
    elif [ $espera_humano -gt 0 ] && [ "$reloj" = release ]; then rol=release; motivo="reloj: release, $espera_humano en espera"
    elif [ "$reloj" = investigador ]; then rol=investigador; motivo="reloj: investigador"
    elif [ $(( propuesto + disenado )) -eq 0 ]; then rol=po; motivo="papel vacio"
    # Directiva de alcance: un papel solo de tests y deuda se rellena con
    # funcionalidades antes de que el Dev lo convierta en codigo.
    elif [ $papel_func -eq 0 ] && [ $ideas_libres -gt 0 ]; then rol=po; motivo="papel sin funcionalidades: $ideas_libres ideas libres"
    elif [ $disenado -gt 0 ] && [ $cola -lt $tope_cola ] && [ $total -lt $tope_total ]; then rol=dev; motivo="por estado: $disenado disenado, lugar en cola"
    elif [ $propuesto -gt 0 ] && [ $disenado -lt $tope_disenado ]; then rol=arquitecto; motivo="por estado: $propuesto propuesto, $disenado disenado de $tope_disenado"
    elif [ $propuesto -lt $tope_propuesto ]; then rol=po; motivo="papel corto: $propuesto propuesto de $tope_propuesto"
    elif [ $ideas_libres -lt 10 ]; then rol=investigador; motivo="ideas libres: $ideas_libres de 10"
    else rol=$reloj; motivo="nada tomable: reloj"
    fi
}
elegir_rol

# Encadenar: decide si esta misma sesion sigue con otro rol.
no_encadena=""
if [ "$encadenar" = si ]; then
    ya=${sim_roles:-${EQUIPO_ROLES:-$EQUIPO_ROL}}
    if [ "$simular" = si ]; then queda=${sim_queda:-0}
    else queda=$(( (${EQUIPO_CIERRE_EPOCH:-0} - $(date -u +%s)) / 60 ))
    fi
    n_ya=$(echo "$ya" | tr ',' '\n' | grep -c .)
    if [ "$max_roles_por_turno" -le 1 ]; then no_encadena="encadenado apagado (max_roles_por_turno=1)"
    elif [ "$n_ya" -ge "$max_roles_por_turno" ]; then no_encadena="ya hizo $n_ya roles (tope $max_roles_por_turno)"
    elif [ "$rol" = release ] && [ "$queda" -lt "$minimo_release" ]; then no_encadena="quedan $queda minutos (minimo $minimo_release para release)"
    elif [ "$rol" != release ] && [ "$queda" -lt "$minimo_para_encadenar" ]; then no_encadena="quedan $queda minutos (minimo $minimo_para_encadenar)"
    elif [ -n "$rol_pedido" ]; then no_encadena="un rol pedido no encadena"
    elif [ "$con_resumen" = no ]; then no_encadena="sin resumen"
    elif [ "$motivo" = "nada tomable: reloj" ]; then no_encadena="nada tomable"
    elif echo ",$ya," | grep -q ",$rol,"; then no_encadena="el rol que sigue ($rol) ya lo hizo esta sesion"
    fi
fi

if [ "$simular" = si ]; then
    if [ "$encadenar" = si ]; then
        if [ -n "$no_encadena" ]; then echo "encadenar=no motivo=$no_encadena"; else echo "encadenar=si rol=$rol motivo=$motivo"; fi
    else
        echo "rol=$rol motivo=$motivo reloj=$reloj franja=$franja"
    fi
    exit 0
fi
if [ "$encadenar" = si ] && [ -n "$no_encadena" ]; then
    echo "ENCADENAR=no motivo=$no_encadena"
    exit 3
fi
[ "$con_resumen" = no ] && echo "# aviso: sin resumen, rol por reloj"

if [ "$encadenar" = si ]; then
    cierre=$EQUIPO_CIERRE_EPOCH
    roles_turno="$ya,$rol"
    sesion=$EQUIPO_SESION
else
    cierre=$(( inicio + minutos_turno * 60 ))
    tope_franja=$(( disparo + (180 - 15) * 60 ))
    [ "$tope_franja" -lt "$cierre" ] && cierre=$tope_franja
    roles_turno=$rol
    sesion=$(date -u -d "@$inicio" +%Y%m%dT%H%MZ)
fi
minutos=$(( (cierre - $(date -u +%s)) / 60 ))
env_file="$gitdir/equipo-dev.env"
{
    echo "export EQUIPO_ROL=$rol"
    echo "export EQUIPO_ROLES=$roles_turno"
    echo "export EQUIPO_FRANJA=$franja"
    echo "export EQUIPO_MOTIVO=\"$motivo\""
    echo "export EQUIPO_RELOJ=$reloj"
    echo "export EQUIPO_INICIO=$inicio"
    echo "export EQUIPO_SESION=$sesion"
    echo "export EQUIPO_CIERRE=$(date -u -d "@$cierre" +%H:%M)"
    echo "export EQUIPO_CIERRE_EPOCH=$cierre"
    echo "export EQUIPO_MINUTOS=$minutos"
    echo "export EQUIPO_REF=$ref"
} > "$env_file"
cat "$env_file"
[ "$encadenar" = si ] && echo "ENCADENAR=si rol=$rol motivo=$motivo"
echo "# turno: $roles_turno | motivo: $motivo | reloj: $reloj (franja $franja) | sesion $sesion | inicio $(date -u -d "@$inicio" +%H:%M) UTC | cerrar a las $(date -u -d "@$cierre" +%H:%M) UTC ($minutos min) | playbook $ref | variables en $env_file"
echo "# leer: git show $ref:.claude/skills/equipo-dev/roles/$rol.md"

# M11: la guardia de ramas (pre-push.sh), antes del primer push del turno,
# que es el del pulso: si la guardia estuviera rota se ve ahi. No pisa un
# pre-push ajeno ni escribe fuera de .git (core.hooksPath versionado).
if [ "$simular" = no ] && [ "${EQUIPO_SIN_GUARDIA:-}" != 1 ]; then
    hook=$(git rev-parse --git-path hooks/pre-push)
    case "$hook" in /*) ;; *) hook="$(pwd)/$hook" ;; esac
    gd=$(cd "$gitdir" && pwd)
    case "$hook" in
        "$gd"/*)
            if [ ! -e "$hook" ] || grep -q 'equipo-dev pre-push' "$hook" 2>/dev/null; then
                mkdir -p "$(dirname "$hook")"
                if [ -n "$yo_dir" ] && [ -f "$yo_dir/pre-push.sh" ]; then cp "$yo_dir/pre-push.sh" "$hook"
                else git show "$ref:scripts/equipo-dev/pre-push.sh" > "$hook" 2>/dev/null
                fi
                chmod +x "$hook" && echo "# guardia: pre-push del equipo instalado"
            else
                echo "# guardia: ya hay otro pre-push en $hook; no se pisa"
            fi ;;
        *) echo "# guardia: hooks fuera de .git ($hook); no se instala" ;;
    esac
fi

# M3: la linea de arranque en PULSO.md, antes de cualquier trabajo, para que
# una sesion que muera despues se distinga de un disparo perdido. Un fallo
# (proxy, sin backlog) no frena el turno: se anota y se sigue.
if [ "$encadenar" = no ] && [ "${EQUIPO_SIN_PULSO:-}" != 1 ] && [ "$pausa" != si ]; then
    if [ -n "$yo_dir" ] && [ -f "$yo_dir/pulso.sh" ]; then
        p=$(bash "$yo_dir/pulso.sh" arranque 2>&1 | tail -1)
    else
        p=$(git show "$ref:scripts/equipo-dev/pulso.sh" 2>/dev/null | bash -s -- arranque 2>&1 | tail -1)
    fi
    echo "# pulso: ${p:-sin salida}"
fi
exit 0
