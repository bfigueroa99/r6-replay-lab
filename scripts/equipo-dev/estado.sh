#!/usr/bin/env bash
# Lista el estado del equipo leyendo solo git: fichas en papel (rama backlog),
# ramas de trabajo con su ficha y estado, cola, techo, rutina, salud del loop y
# entorno. Es lo primero que corre cada rol y lo unico que necesita para decidir.
# Uso:  scripts/equipo-dev/estado.sh                       (hace fetch de origin)
#       scripts/equipo-dev/estado.sh --resumen             (solo la linea RESUMEN; la lee turno.sh)
#       scripts/equipo-dev/estado.sh --resumen --excluir-sesion <S>
#             cuenta sin las fichas en las que la sesion S ya firmo una etapa
#             que le impide la siguiente (turno.sh --encadenar)
#       scripts/equipo-dev/estado.sh --tablero [--turno "<que hizo>"] [--humano "<pedido>"]...
#             [--cerrar H<n> "<motivo>"]... [--maquinaria "<idea>"]... [--rutina "<estado del prompt>"]
#             imprime ESTADO.md entero (M4); lo usa pulso.sh cierre
#       git show <ref>:scripts/equipo-dev/estado.sh | bash [-s -- --resumen]
#       EQUIPO_AHORA=<epoch> ... (fija "ahora"; gancho de pruebas)   --sin-fetch (no actualiza origin)
set -u
modo=normal; excluir=""; sin_fetch=no
turno_txt=""; rutina_txt=""; humanos=(); cerrar=(); maquinas=()
while [ $# -gt 0 ]; do
    case "$1" in
        --resumen) modo=resumen ;;
        --tablero) modo=tablero ;;
        --sin-fetch) sin_fetch=si ;;
        --excluir-sesion) excluir=${2:-}; shift ;;
        --turno) turno_txt=${2:-}; shift ;;
        --rutina) rutina_txt=${2:-}; shift ;;
        --humano) humanos+=("${2:-}"); shift ;;
        --cerrar) cerrar+=("${2:-}|${3:-}"); shift 2 ;;
        --maquinaria) maquinas+=("${2:-}"); shift ;;
        *) echo "argumento desconocido: $1" >&2; exit 2 ;;
    esac
    shift
done
# Los scripts hermanos (fichas.sh) se corren del mismo directorio si este se
# corrio como archivo, o de la misma ref si vino por `git show | bash`.
yo_dir=""
if [ -n "${BASH_SOURCE[0]:-}" ] && [ -f "${BASH_SOURCE[0]}" ]; then yo_dir=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd); fi
# Con --resumen o --tablero todo lo demas va a /dev/null y lo pedido sale por
# el descriptor 3, que conserva la salida original.
if [ "$modo" != normal ]; then exec 3>&1; exec >/dev/null; fi
repo="$(git rev-parse --show-toplevel 2>/dev/null)" || { echo "no es un repo git" >&2; exit 1; }
cd "$repo"
# El + fuerza la actualizacion aunque el humano haya reescrito una rama
# (por ejemplo "Update with rebase" en un PR).
fetch_fallo=no
if [ "$sin_fetch" = no ] && ! git fetch -q origin main '+refs/heads/claude/*:refs/remotes/origin/claude/*' 2>/dev/null; then
    echo "FETCH_FALLO: no se pudo actualizar origin; lo que sigue puede estar viejo" >&2
    echo "== fetch"; echo "FETCH_FALLO"; fetch_fallo=si
fi
git rev-parse -q --verify 'origin/main^{commit}' >/dev/null || { echo "sin origin/main: no se puede decidir nada" >&2; exit 1; }
B=origin/claude/equipo-dev/backlog
ahora=${EQUIPO_AHORA:-$(date -u +%s)}
arbol_main=$(git rev-parse 'origin/main^{tree}')
# Topes de la cola y del papel. SKILL.md y ESTADO.plantilla.md repiten los
# numeros en prosa; pruebas.sh verifica que coincidan con estos.
tope_cola=4 tope_total=6 tope_propuesto=6 tope_disenado=3
# Lo que mergea el humano (condicion d de la puerta). Copia de
# RUTAS_DEL_HUMANO de puerta.sh; pruebas.sh verifica que sean iguales.
RUTAS_DEL_HUMANO="CLAUDE.md .claude/ scripts/equipo-dev/ docs/backlog/README.md docs/backlog/PLANTILLA.md docs/backlog/ESTADO.plantilla.md docs/backlog/ALCANCE.md docs/backlog/INVESTIGACION.md docs/backlog/MAQUINARIA.md frontend/electron/ frontend/electron-builder.json packaging/ scripts/*.ps1 .github/"
env_file="$(git rev-parse --git-dir)/equipo-dev.env"
EQUIPO_ROL="" EQUIPO_ROLES="" EQUIPO_SESION="" EQUIPO_MOTIVO="" EQUIPO_RELOJ="" EQUIPO_FRANJA=""
# shellcheck disable=SC1090
[ -f "$env_file" ] && . "$env_file"

# La ficha que la rama AGREGA (no la primera que toca): una rama puede ademas
# editar una ficha que ya esta en main.
# core.quotePath=false: una ficha con nombre no ASCII saldria citada e invisible.
ficha_de() { git -c core.quotePath=false diff --name-only --diff-filter=A "origin/main...$1" -- docs/backlog 2>/dev/null | grep -E 'docs/backlog/[0-9]+-' | head -1; }
# Las tres formas en que el humano integra: merge commit, squash o rebase.
mergeada() {
    git merge-base --is-ancestor "$1" origin/main 2>/dev/null && return 0
    [ "$(git merge-tree --write-tree origin/main "$1" 2>/dev/null | head -1)" = "$arbol_main" ] && return 0
    local f; f=$(ficha_de "$1")
    [ -n "$f" ] && git cat-file -e "origin/main:$f" 2>/dev/null
}
edad_h() { echo $(( (ahora - $(git log -1 --format=%ct "$1")) / 3600 )); }
campo() { git show "$1:$2" 2>/dev/null | grep -m1 "^$3:" | sed "s/^$3:[[:space:]]*//"; }
# La rama del playbook (y sus variantes playbook-2, playbook/x) no es trabajo
# del equipo: no cuenta ni se le crea ficha.
es_playbook() { case "$1" in origin/claude/equipo-dev/playbook|origin/claude/equipo-dev/playbook[-/]*) return 0 ;; esac; return 1; }
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
# Sesiones que firmaron una etapa en la linea `turnos:` de una ficha. Las notas
# entre parentesis no cambian el par; puerta.sh hace el parseo estricto.
sesiones() { # contenido-turnos rol...
    local t=$1 r; shift
    for r in "$@"; do printf '%s\n' "$t" | grep -oE "(^|[ ,:])$r [0-9]{8}T[0-9]{4}Z" | grep -oE '[0-9]{8}T[0-9]{4}Z'; done
}
# Con --excluir-sesion, una ficha no cuenta para la etapa que sigue si esa
# sesion ya firmo una etapa incompatible (principio 4). Asi un turno encadenado
# nunca elige un rol cuyo unico trabajo seria violar la independencia.
excluida() { # turnos rol-que-sigue
    [ -n "$excluir" ] || return 1
    local roles
    case "$2" in
        revisor) roles="dev qa" ;;
        qa) roles="dev revisor" ;;
        dev) roles="revisor qa" ;;
        release) roles="dev revisor qa" ;;
        arquitecto) roles="po" ;;
        *) return 1 ;;
    esac
    # shellcheck disable=SC2086
    sesiones "$1" $roles | grep -qx "$excluir"
}
hermano() { # script args...
    local s=$1; shift
    if [ -n "$yo_dir" ] && [ -f "$yo_dir/$s" ]; then bash "$yo_dir/$s" "$@"
    elif [ -n "${ref:-}" ] && git cat-file -e "$ref:scripts/equipo-dev/$s" 2>/dev/null; then git show "$ref:scripts/equipo-dev/$s" | bash -s -- "$@"
    else return 127
    fi
}

echo "== playbook"
# Se prueba rutina.md y no SKILL.md: solo el playbook nuevo lo tiene, asi que
# un main con un playbook viejo mergeado no gana la cadena.
for ref in origin/main origin/claude/equipo-dev/playbook; do git cat-file -e "$ref:.claude/skills/equipo-dev/rutina.md" 2>/dev/null && break; done
playbook_linea="SIN_PLAYBOOK"; candidato=""
if git cat-file -e "$ref:.claude/skills/equipo-dev/rutina.md" 2>/dev/null; then
    playbook_linea="$ref@$(git rev-parse --short "$ref")"
    echo "$playbook_linea"
    # Si main gano la cadena con un playbook viejo y la rama del playbook trae
    # otro que main todavia no tiene, hay que decirlo. Una rama del playbook
    # ya mergeada (ancestro de main) no es candidata aunque difiera.
    pb=origin/claude/equipo-dev/playbook
    if [ "$ref" = origin/main ] && git cat-file -e "$pb:.claude/skills/equipo-dev/rutina.md" 2>/dev/null \
        && ! git merge-base --is-ancestor "$pb" origin/main 2>/dev/null \
        && [ "$(git rev-parse "origin/main:.claude/skills/equipo-dev/SKILL.md")" != "$(git rev-parse "$pb:.claude/skills/equipo-dev/SKILL.md")" ]; then
        candidato="$pb@$(git rev-parse --short "$pb")"
        echo "PLAYBOOK_CANDIDATO=$candidato"
    fi
else
    echo "SIN_PLAYBOOK"
fi
# M10: una rama del equipo que cambia el playbook o lo que mergea el humano se
# ve aca, en el Revisor, y no recien en la puerta del Release.
tocado=""; del_humano=""
for r in $(git branch -r --list 'origin/claude/equipo-dev/*' --no-merged origin/main --format='%(refname:short)'); do
    es_playbook "$r" && continue
    [ "$r" = "$B" ] && continue
    pb_f=""; hu_f=""
    while IFS= read -r f; do
        [ -n "$f" ] || continue
        case "$f" in .claude/*|scripts/equipo-dev/*) pb_f="$pb_f $f"; continue ;; esac
        es_del_humano "$f" && hu_f="$hu_f $f"
    done <<< "$(git -c core.quotePath=false diff --name-only "origin/main...$r" 2>/dev/null)"
    [ -n "$pb_f" ] && { echo "PLAYBOOK_TOCADO_POR_EL_EQUIPO=${r#origin/}:$pb_f"; tocado="$tocado ${r#origin/}"; }
    [ -n "$hu_f" ] && { echo "MERGE_DEL_HUMANO=${r#origin/}:$hu_f"; del_humano="$del_humano ${r#origin/}"; }
done

echo "== pausa"
pausa=no
if git cat-file -e "$B:docs/backlog/PAUSA" 2>/dev/null; then pausa=si; echo "PAUSA"; else echo "no"; fi
echo "== sin_merge (veto del humano al merge automatico)"
sin_merge=no
if git cat-file -e "$B:docs/backlog/SIN_MERGE" 2>/dev/null; then sin_merge=si; echo "SIN_MERGE"; else echo "no"; fi

# Sin tipo: no cuenta como funcionalidad (Directiva de alcance del playbook).
tipo_de() { local t; t=$(campo "$1" "$2" tipo); echo "${t:-sin tipo}"; }
echo "== papel (rama backlog)"
papel_func=0; papel_otro=0; propuesto=0; disenado=0; bug_p1=0
papel_filas=""; papel_viejo=""
if git rev-parse -q --verify "$B" >/dev/null 2>&1; then
    for f in $(git -c core.quotePath=false ls-tree -r --name-only "$B" docs/backlog/ | grep -E '/[0-9]+-'); do
        estado=$(campo "$B" "$f" estado); tipo=$(tipo_de "$B" "$f"); epica=$(campo "$B" "$f" epica)
        prio=$(campo "$B" "$f" prioridad); area=$(campo "$B" "$f" area); candado=$(campo "$B" "$f" candado)
        printf '%s | estado: %s | tipo: %s | epica: %s | prioridad: %s | candado: %s | rama: %s\n' "$f" "$estado" \
            "$tipo" "${epica:--}" "${prio:--}" "$candado" "$(campo "$B" "$f" rama)"
        papel_filas="$papel_filas$(basename "$f" .md)|$estado|$tipo|${epica:--}|${prio:--}|${area:--}|${candado:--}"$'\n'
        t=$(campo "$B" "$f" turnos)
        case "$estado" in
            propuesto*|disenado*)
                if [ "$tipo" = funcionalidad ]; then papel_func=$((papel_func + 1)); else papel_otro=$((papel_otro + 1)); fi
                # Un bug grave salta la cola (Severidad en SKILL.md): turno.sh lo mira aparte.
                if [ "$tipo" = bug ] && [ "${prio:-9}" = 1 ]; then bug_p1=$((bug_p1 + 1)); fi
                u=$(git log -1 --format=%ct "$B" -- "$f"); u=${u:-$ahora}
                [ $(( ahora - u )) -ge 604800 ] && papel_viejo="$papel_viejo $(basename "$f" .md)($(( (ahora - u) / 86400 ))d)" ;;
        esac
        # Solo el papel cuenta aca; el espejo "en curso" de una ficha reclamada
        # no manda: la rama de trabajo si.
        case "$estado" in
            propuesto*) excluida "$t" arquitecto || propuesto=$((propuesto + 1)) ;;
            disenado*) disenado=$((disenado + 1)) ;;
        esac
    done
else
    echo "sin rama backlog (la crea el primer turno que no la encuentra)"
fi

echo "== ramas de trabajo (origin/claude/* no mergeadas con ficha)"
cola=0; total=0; cola_func=0; cola_espera=0
en_curso=0; huerfanas=0; implementado=0; revisado=0; con_hallazgos=0; aprobado=0; entregado=0; espera_humano=0
cola_filas=""; borrables=""; atascadas=""; espera_lista=""
for r in $(git branch -r --list 'origin/claude/*' --no-merged origin/main --format='%(refname:short)'); do
    es_playbook "$r" && continue
    [ "$r" = "$B" ] && continue
    f=$(ficha_de "$r"); [ -z "$f" ] && continue
    if mergeada "$r"; then echo "$r | mergeada efectivamente: borrable"; borrables="$borrables ${r#origin/}"; continue; fi
    estado=$(campo "$r" "$f" estado)
    edad=$(edad_h "$r")
    if [[ "$estado" == descartado* ]]; then echo "$r | $f | $estado | no cuenta: borrable"; borrables="$borrables ${r#origin/}"; continue; fi
    total=$((total + 1))
    reciente=no
    if [[ "$estado" == "entregado ("* ]]; then
        # M6: lo que espera al humano ocupa como mucho un lugar de COLA entre
        # todas: si no, unos PRs esperando merge frenan al Dev aunque el equipo
        # no tenga nada a medio verificar.
        reciente=si
        [ "$cola_espera" -eq 0 ] && cola=$((cola + 1))
        cola_espera=$((cola_espera + 1))
        espera_lista="$espera_lista${r#origin/}|$estado"$'\n'
    elif [ "$edad" -lt 336 ] || [[ "$estado" == entregado* ]]; then
        reciente=si; cola=$((cola + 1))
    fi
    tipo=$(tipo_de "$r" "$f")
    [ "$tipo" = funcionalidad ] && cola_func=$((cola_func + 1))
    candado=$(campo "$r" "$f" candado)
    t=$(campo "$r" "$f" turnos)
    # P8: un candado con mas de 3 h sin commits sobre la ficha (los de
    # ESTADO.md no cuentan) es una sesion muerta.
    ult=$(git log -1 --format=%ct "$r" -- "$f"); ult=${ult:-0}
    muerto=no
    [ "$candado" != "-" ] && [ $(( ahora - ult )) -ge 10800 ] && muerto=si
    # Una ficha con mas de 48 h quieta en una etapa del equipo es un atasco
    # (lo que espera al humano va aparte).
    if [[ "$estado" != "entregado ("* ]] && [ $(( ahora - ult )) -ge 172800 ]; then
        atascadas="$atascadas ${r#origin/claude/equipo-dev/}($estado, $(( (ahora - ult) / 3600 ))h)"
    fi
    case "$estado" in
        aprobado*) excluida "$t" release || aprobado=$((aprobado + 1)) ;;
        entregado) excluida "$t" release || entregado=$((entregado + 1)) ;;
        "entregado ("*) espera_humano=$((espera_humano + 1)) ;;
        revisado*) excluida "$t" qa || revisado=$((revisado + 1)) ;;
        implementado*) excluida "$t" revisor || implementado=$((implementado + 1)) ;;
        "con hallazgos"*) excluida "$t" dev || con_hallazgos=$((con_hallazgos + 1)) ;;
        "en curso"*)
            en_curso=$((en_curso + 1))
            # Huerfana: nadie la tiene (candado suelto) o quien la tenia murio.
            if [ "$candado" = "-" ] || [ $(( ahora - ult )) -ge 10800 ]; then excluida "$t" dev || huerfanas=$((huerfanas + 1)); fi ;;
    esac
    # Sin merges: un "Update branch" del humano desde GitHub no es un pedido.
    humano=$(git log --no-merges "origin/main..$r" --format=%an | grep -v '^Claude' | sort -u | tr '\n' ' ')
    printf '%s | %s | estado: %s | tipo: %s | candado: %s | %sh | cuenta en cola: %s | commits humanos: %s | candado muerto: %s\n' \
        "$r" "$f" "$estado" "$tipo" "$candado" "$edad" "$reciente" "${humano:-ninguno}" "$muerto"
    cola_filas="$cola_filas${r#origin/}|$(basename "$f" .md)|$estado|$tipo|$edad|$candado|${humano:-ninguno}"$'\n'
done

# Las ramas del equipo ya mergeadas con merge commit no salen en --no-merged
# pero siguen siendo borrables (el proxy de la nube corta el push --delete).
for r in $(git branch -r --list 'origin/claude/equipo-dev/[0-9]*' --merged origin/main --format='%(refname:short)'); do
    echo "$r | mergeada: borrable"; borrables="$borrables ${r#origin/}"
done

echo "== ramas del playbook anterior (sin ficha; reclamo en el roadmap)"
# El playbook anterior reclamaba en docs/roadmap.md con un commit "Reclama:" y
# la sesion podia imponer el nombre de la rama, asi que no alcanza con el glob.
for r in $(git branch -r --list 'origin/claude/*' --no-merged origin/main --format='%(refname:short)'); do
    es_playbook "$r" && continue
    [ "$r" = "$B" ] && continue
    [ -n "$(ficha_de "$r")" ] && continue
    case "$r" in origin/claude/equipo-dev/*) vieja=si ;; *) vieja=no ;; esac
    git log "origin/main..$r" --format=%s | grep -q '^Reclama:' && vieja=si
    [ "$vieja" = si ] || continue
    mergeada "$r" && { echo "$r | mergeada efectivamente: borrable"; borrables="$borrables ${r#origin/}"; continue; }
    n=$(git rev-list --count "origin/main..$r")
    edad=$(edad_h "$r")
    if [ "$n" -le 1 ]; then
        echo "$r | ${edad}h | solo el commit de reclamo, sin codigo: borrable, no cuenta, no se le crea ficha"
        borrables="$borrables ${r#origin/}"
    else
        total=$((total + 1))
        # Con codigo es trabajo que espera al humano, igual que una rama con ficha.
        [ "$edad" -lt 336 ] && cola=$((cola + 1))
        echo "$r | ${edad}h | $n commits sin ficha: el primer Revisor le crea una en implementado | cuenta en cola: $([ "$edad" -lt 336 ] && echo si || echo no) | $(git log -1 --format=%s "$r")"
    fi
done

echo "== otras ramas claude/* sin ficha ni reclamo (del humano u otras sesiones; no se tocan)"
for r in $(git branch -r --list 'origin/claude/*' --no-merged origin/main --format='%(refname:short)'); do
    [ "$r" = "$B" ] && continue
    [ -n "$(ficha_de "$r")" ] && continue
    case "$r" in origin/claude/equipo-dev/*) continue ;; esac
    git log "origin/main..$r" --format=%s | grep -q '^Reclama:' && continue
    echo "$r | $(edad_h "$r")h | $(git log -1 --format=%s "$r")"
done

echo "== pedidos del humano en backlog (commits suyos y seccion Para el equipo)"
estado_previo=""
if git rev-parse -q --verify "$B" >/dev/null 2>&1; then
    git log --no-merges -5 "$B" --format='%an %ci | %s' -- docs/backlog | grep -v '^Claude' || echo "sin commits humanos recientes"
    estado_previo=$(git show "$B:docs/backlog/ESTADO.md" 2>/dev/null)
    printf '%s\n' "$estado_previo" | sed -n '/^## Para el equipo/,$p' | head -30
else
    echo "sin rama backlog"
fi

echo "== rutina (disparos \`1 */3 * * *\` sin commit de ESTADO.md ni cierre en PULSO.md en las 3 h siguientes)"
# Cada turno que termina deja un commit de ESTADO.md (y desde M3 una linea de
# cierre en PULSO.md); un disparo sin ninguno en sus 3 horas es una sesion que
# no corrio o murio antes de cerrar. PULSO.md separa las dos: una linea de
# arranque sin cierre es una sesion que murio; sin arranque, el disparo se perdio.
sin_rastro_48h=0; rutina_linea="TURNOS_SIN_RASTRO=?"; pulso_linea=""; perdidos=0; murieron=0
pulso=$(git show "$B:docs/backlog/PULSO.md" 2>/dev/null | grep -E '^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}Z [0-9]{8}T[0-9]{4}Z (arranque|cierre) ')
ses_epoch() { date -u -d "${1:0:4}-${1:4:2}-${1:6:2} ${1:9:2}:${1:11:2}" +%s 2>/dev/null; }
# epoch de sesion, tipo: "1760000000 arranque" por linea
pulso_ev=""
while IFS= read -r l; do
    [ -n "$l" ] || continue
    s=$(echo "$l" | awk '{print $2}'); ti=$(echo "$l" | awk '{print $3}')
    e=$(ses_epoch "$s") && pulso_ev="$pulso_ev$e $ti"$'\n'
done <<< "$pulso"
rastros=$(git log --format='%ct %s' "$B" -- docs/backlog/ESTADO.md 2>/dev/null)
cierres=$(printf '%s' "$pulso_ev" | awk '$2 == "cierre" {print $1}')
cts=$( { echo "$rastros" | cut -d' ' -f1; echo "$cierres"; } | grep -E '^[0-9]+$' | sort -n)
if [ -z "$cts" ]; then
    echo "$rutina_linea (sin ESTADO.md en backlog)"
else
    primero=$(echo "$cts" | head -1)
    ultimo=$(echo "$rastros" | awk -v a="$ahora" '$1 <= a { print; exit }')
    if [ -n "$ultimo" ]; then
        echo "ULTIMO_RASTRO=$(date -u -d "@${ultimo%% *}" +%FT%H:%MZ) (${ultimo#* })"
    else
        echo "ULTIMO_RASTRO=ninguno"
    fi
    # Un disparo tiene rastro si algun commit de ESTADO.md o cierre cae en [d, d + 3 h).
    en_ventana() { local t; for t in $2; do [ "$t" -ge "$1" ] && [ "$t" -lt $(( $1 + 10800 )) ] && return 0; done; return 1; }
    # Cuenta los disparos de la ventana ($1 segundos) cuya ventana de 3 h ya
    # cerro: el turno en curso commitea ESTADO.md al cerrar, hasta 135 min
    # despues del disparo, y no puede contarse como perdido a si mismo.
    # Arranca en el disparo de la franja que contiene el limite, asi el turno
    # del primer rastro cuenta entero. Imprime "sin total lista".
    contar() {
        local desde d sin=0 tot=0 lista=""
        desde=$(( ahora - $1 )); [ "$desde" -lt "$primero" ] && desde=$primero
        d=$(( desde / 10800 * 10800 + 60 ))
        while [ "$d" -le $(( ahora - 10800 )) ]; do
            tot=$((tot + 1))
            en_ventana "$d" "$cts" || { sin=$((sin + 1)); lista="$lista $(date -u -d "@$d" +%m-%dT%H:%MZ)"; }
            d=$(( d + 10800 ))
        done
        echo "$sin $tot$lista"
    }
    read -r sin_rastro_48h _ lista48 <<< "$(contar 172800)"
    read -r sin7 tot7 _ <<< "$(contar 604800)"
    if [ "$sin_rastro_48h" -gt 0 ]; then
        rutina_linea="TURNOS_SIN_RASTRO=$sin_rastro_48h en 48 h ($lista48) | $sin7 de $tot7 en 7 dias"
    else
        rutina_linea="TURNOS_SIN_RASTRO=0 en 48 h | $sin7 de $tot7 en 7 dias"
    fi
    echo "$rutina_linea"
    # Con PULSO.md, cada disparo sin cierre se separa en perdido o murio.
    if [ -n "$pulso_ev" ]; then
        arranques=$(printf '%s' "$pulso_ev" | awk '$2 == "arranque" {print $1}')
        p0=$(printf '%s' "$pulso_ev" | awk '{print $1}' | sort -n | head -1)
        desde=$(( ahora - 172800 )); [ "$desde" -lt "$p0" ] && desde=$p0
        d=$(( desde / 10800 * 10800 + 60 )); cerr=0; lper=""; lmur=""
        while [ "$d" -le $(( ahora - 10800 )) ]; do
            if en_ventana "$d" "$cts"; then cerr=$((cerr + 1))
            elif en_ventana "$d" "$arranques"; then murieron=$((murieron + 1)); lmur="$lmur $(date -u -d "@$d" +%m-%dT%H:%MZ)"
            else perdidos=$((perdidos + 1)); lper="$lper $(date -u -d "@$d" +%m-%dT%H:%MZ)"
            fi
            d=$(( d + 10800 ))
        done
        pulso_linea="PULSO=48 h: $cerr con cierre, $murieron murieron${lmur:+ (${lmur# })}, $perdidos perdidos${lper:+ (${lper# })}"
        echo "$pulso_linea"
    else
        echo "PULSO=sin PULSO.md en backlog todavia (lo escribe pulso.sh)"
    fi
fi

echo "== cola"
echo "COLA=$cola (tope $tope_cola)  TOTAL=$total (tope $tope_total)$([ "$cola_espera" -gt 0 ] && echo "  ESPERA_HUMANO=$cola_espera (ocupan 1 lugar de COLA)")"

echo "== alcance"
echo "PAPEL_TIPOS=funcionalidad:$papel_func otros:$papel_otro (propuesto y disenado; la directiva pide 3 funcionalidades antes de tests sueltos)"
echo "COLA_TIPOS=funcionalidad:$cola_func de $total ramas de trabajo"
# --first-parent -m fecha cada ficha por el merge que la trajo a main, no por
# el commit "Reclama:" de su rama, que puede tener mas de una semana.
main_func=""; main_otro=0
for f in $(git log --since="@$(( ahora - 604800 ))" --first-parent -m origin/main --diff-filter=A --name-only --format= -- docs/backlog | grep -E '/[0-9]+-' | sort -u); do
    if [ "$(tipo_de origin/main "$f")" = funcionalidad ]; then main_func="$main_func $(basename "$f" .md)"; else main_otro=$((main_otro + 1)); fi
done
main_func_n=$(echo $main_func | wc -w)
# Tiempo de ciclo: de la primera firma de `turnos:` al merge en main, por
# ficha llegada en 7 dias. Es el numero con el que se decide la cadencia (M1)
# y se mide si el encadenado sirvio.
ciclos=""
while IFS=' ' read -r ct f; do
    [ -n "${f:-}" ] || continue
    s=$(campo origin/main "$f" turnos | grep -oE '[0-9]{8}T[0-9]{4}Z' | head -1)
    [ -n "$s" ] || continue
    e=$(date -u -d "${s:0:4}-${s:4:2}-${s:6:2} ${s:9:2}:${s:11:2}" +%s 2>/dev/null) || continue
    [ "$ct" -gt "$e" ] && ciclos="$ciclos $(( (ct - e) / 3600 ))"
done <<< "$(git log --since="@$(( ahora - 604800 ))" --first-parent -m origin/main --diff-filter=A --name-only --format='C %ct' -- docs/backlog \
    | awk '/^C [0-9]+$/ {c=$2; next} /\/[0-9]+-[^\/]*\.md$/ {print c, $0}' | sort -k2,2 -u)"
if [ -n "$ciclos" ]; then
    n_c=$(echo $ciclos | wc -w)
    mediana=$(printf '%s\n' $ciclos | sort -n | awk '{a[NR]=$1} END {print a[int((NR+1)/2)]}')
    ciclo_linea="CICLO_7D=mediana ${mediana} h, de la primera firma al merge ($n_c fichas: ${ciclos# } h)"
else
    ciclo_linea="CICLO_7D=sin fichas llegadas a main en 7 dias"
fi
echo "$ciclo_linea"
main7_linea="MAIN_7D=funcionalidad:$main_func_n${main_func:+ (${main_func# })} otros:$main_otro (fichas que llegaron a main en 7 dias)"
echo "$main7_linea"
libres=0
if git cat-file -e "$B:docs/backlog/ALCANCE.md" 2>/dev/null; then
    # Una idea libre es una fila de tabla cuya ultima columna dice "idea".
    libres=$(git show "$B:docs/backlog/ALCANCE.md" | grep -cE '\|[[:space:]]*idea[[:space:]]*\|[[:space:]]*$')
    alcance_linea="ALCANCE=backlog, ideas libres: $libres"
else
    alcance_linea="ALCANCE=falta en backlog: copiar docs/backlog/ALCANCE.md desde el playbook"
fi
echo "$alcance_linea"
if git cat-file -e "$B:docs/backlog/INVESTIGACION.md" 2>/dev/null; then
    ultima=$(git show "$B:docs/backlog/INVESTIGACION.md" | grep -m1 -oE '^### [0-9]{4}-[0-9]{2}-[0-9]{2}' | cut -c5-)
    invest_linea="INVESTIGACION=backlog, ultima entrada: ${ultima:-ninguna}"
else
    invest_linea="INVESTIGACION=falta en backlog: copiar docs/backlog/INVESTIGACION.md desde el playbook"
fi
echo "$invest_linea"
# M7: lo que llego a main desde la ultima version publicada (tag v*), para
# que el humano sepa cuando vale la pena correr release.ps1. notas.sh arma
# las notas de version con esas mismas fichas.
tag=$(git describe --tags --abbrev=0 --match 'v*' origin/main 2>/dev/null)
rp_func=0; rp_bug=0; rp_otro=0
for f in $(git log ${tag:+"$tag..origin/main"} ${tag:-origin/main} --first-parent -m --diff-filter=A --name-only --format= -- docs/backlog 2>/dev/null | grep -E '/[0-9]+-' | sort -u); do
    case "$(tipo_de origin/main "$f")" in funcionalidad) rp_func=$((rp_func + 1)) ;; bug) rp_bug=$((rp_bug + 1)) ;; *) rp_otro=$((rp_otro + 1)) ;; esac
done
release_linea="RELEASE_PENDIENTE=$((rp_func + rp_bug + rp_otro)) fichas en main desde ${tag:-el inicio (sin tags v*)}: funcionalidad:$rp_func bug:$rp_bug otros:$rp_otro"
echo "$release_linea"

echo "== salud (el loop mirandose a si mismo; ver Salud del loop en SKILL.md)"
salud=()
[ -n "$pulso_linea" ] && { [ "$perdidos" -ge 2 ] || [ "$murieron" -ge 1 ]; } && salud+=("SALUD_RUTINA=$pulso_linea")
[ -n "$atascadas" ] && salud+=("SALUD_ATASCADA=${atascadas# } (mas de 48 h sin commits sobre la ficha)")
[ -n "$papel_viejo" ] && salud+=("SALUD_PAPEL_VIEJO=${papel_viejo# } (papel sin tocar en 7 dias: afinar, partir o descartar)")
# Un rol que cierra sin entregar nada 3 de sus ultimos 4 turnos pide cambiar
# la regla que lo elige, no seguir eligiendolo.
for rr in release po arquitecto dev revisor qa investigador; do
    ult4=$(printf '%s\n' "$pulso" | grep -E " cierre ([a-z]+,)*$rr(,[a-z]+)* " | tail -4)
    [ -n "$ult4" ] || continue
    n4=$(printf '%s\n' "$ult4" | grep -c .)
    nada=$(printf '%s\n' "$ult4" | grep -c '| nada |')
    [ "$n4" -ge 4 ] && [ "$nada" -ge 3 ] && salud+=("SALUD_ROL_OCIOSO=$rr: $nada de sus ultimos $n4 cierres sin entregar nada")
done
# Pedidos al humano que llevan mas de 3 dias abiertos: se dicen una vez en
# un solo lugar, no se repiten en cada turno con otras palabras.
pedidos=$(printf '%s\n' "$estado_previo" | sed -n '/^### Pedidos abiertos/,/^##/p' | grep -E '^- H[0-9]+ \(desde [0-9]{4}-[0-9]{2}-[0-9]{2}\)')
viejos=""
while IFS= read -r l; do
    [ -n "$l" ] || continue
    id=$(echo "$l" | grep -oE '^- H[0-9]+' | cut -c3-); fe=$(echo "$l" | grep -oE '[0-9]{4}-[0-9]{2}-[0-9]{2}' | head -1)
    dias=$(( (ahora - $(date -u -d "$fe" +%s)) / 86400 ))
    [ "$dias" -ge 3 ] && viejos="$viejos $id(${dias}d)"
done <<< "$pedidos"
[ -n "$viejos" ] && salud+=("SALUD_PEDIDO_VIEJO=${viejos# } (abiertos hace 3 dias o mas en Para el humano)")
[ -n "$tocado" ] && salud+=("SALUD_PLAYBOOK_TOCADO=${tocado# } (el equipo no edita el playbook: lo frena el Revisor)")
fichas_mal=$(hermano fichas.sh --resumen 2>/dev/null | grep -m1 '^FICHAS_' || true)
case "$fichas_mal" in FICHAS_MAL*) salud+=("SALUD_$fichas_mal (correr fichas.sh para el detalle)") ;; esac
nb=$(echo $borrables | wc -w)
[ "$nb" -ge 5 ] && salud+=("SALUD_BORRABLES=$nb ramas mergeadas o sin codigo esperando que el humano las borre")
if [ "${#salud[@]}" -eq 0 ]; then echo "SALUD_OK"; else printf '%s\n' "${salud[@]}"; fi

echo "== resumen"
# Una linea con todo lo que turno.sh necesita para elegir el rol. Mismo orden
# siempre; los pares nuevos van al final. pruebas.sh cuenta los pares.
linea_resumen="RESUMEN propuesto=$propuesto disenado=$disenado en_curso=$en_curso huerfanas=$huerfanas implementado=$implementado revisado=$revisado con_hallazgos=$con_hallazgos aprobado=$aprobado entregado=$entregado espera_humano=$espera_humano cola=$cola total=$total tope_cola=$tope_cola tope_total=$tope_total tope_propuesto=$tope_propuesto tope_disenado=$tope_disenado ideas_libres=$libres sin_merge=$sin_merge pausa=$pausa sin_rastro_48h=$sin_rastro_48h papel_func=$papel_func bug_p1=$bug_p1"
echo "$linea_resumen"

echo "== entorno"
# Mismo criterio que check.sh: el venv si existe, si no el sistema.
py=python3; [ -x .venv/bin/python ] && py=.venv/bin/python
tiene_ruff=no; { [ -x .venv/bin/ruff ] || command -v ruff >/dev/null 2>&1; } && tiene_ruff=si
completo=si
if ! { [ -d frontend/node_modules ] && [ "$tiene_ruff" = si ] && "$py" -c 'import django, zstandard' 2>/dev/null; }; then
    completo=no
    echo "ENTORNO_INCOMPLETO: pip install -r requirements.txt -r requirements-dev.txt; (cd frontend && npm install)"
fi
# Sin navegador check.sh cae en [5/5]: el e2e maneja la app en Chromium.
if ! ls -d "${PLAYWRIGHT_BROWSERS_PATH:-${HOME:-}/.cache/ms-playwright}"/chromium-* >/dev/null 2>&1; then
    completo=no
    echo "ENTORNO_INCOMPLETO: cd frontend && npm run e2e:browser"
fi
if [ "$completo" = si ]; then echo "completo"; fi

if [ "$modo" = resumen ]; then
    # Con el fetch caido la linea seria vieja: mejor ninguna, y turno.sh cae al reloj.
    [ "$fetch_fallo" = no ] && echo "$linea_resumen" >&3
    exit 0
fi
[ "$modo" = tablero ] || exit 0

# ------------------------------------------------------------------ tablero
# ESTADO.md entero (M4). Lo repetitivo sale de lo calculado arriba; lo que
# escribe la gente (la tabla de ultimos turnos, los pedidos al humano y
# `## Para el equipo`) se copia de la version de origin. `## Para el equipo`
# va byte por byte: es del humano.
hoy=$(date -u -d "@$ahora" +%F); ahora_txt=$(date -u -d "@$ahora" '+%F %H:%M')
seccion() { printf '%s\n' "$estado_previo" | awk -v h="$1" '$0 == h {f=1; next} f && /^## / {exit} f'; }
sub_bloque() { seccion "## Para el humano" | awk -v h="$1" '$0 == h {f=1; next} f && /^### / {exit} f'; }
{
roles_txt=${EQUIPO_ROLES:-$EQUIPO_ROL}
echo "# Estado del equipo de desarrollo autonomo"
echo
echo "actualizado: $ahora_txt UTC por ${roles_txt:-?} (sesion ${EQUIPO_SESION:-?}; motivo: ${EQUIPO_MOTIVO:-?}; reloj: ${EQUIPO_RELOJ:-?}, franja ${EQUIPO_FRANJA:-?})"
echo "playbook: $playbook_linea${candidato:+ (candidato: $candidato)}"
echo "rutina: $rutina_linea${pulso_linea:+ | $pulso_linea}${rutina_txt:+; $rutina_txt}"
echo "pausa: $pausa"
echo "sin_merge: $sin_merge"
echo
echo "## Cola (items con codigo, esperando al humano o en trabajo)"
echo
if [ -z "$cola_filas" ]; then
    echo "Vacia."
else
    echo "| rama | ficha | estado | tipo | horas sin commits | candado | commits humanos | compare |"
    echo "|---|---|---|---|---|---|---|---|"
    printf '%s' "$cola_filas" | while IFS='|' read -r ra fi es ti ed ca hu; do
        echo "| \`$ra\` | $fi | $es | $ti | $ed | $ca | $hu | [compare](https://github.com/bfigueroa99/r6-replay-lab/compare/main...$ra?expand=1) |"
    done
fi
echo
echo "COLA=$cola/$tope_cola  TOTAL=$total/$tope_total"
echo "$linea_resumen"
echo
echo "## Orden de merge sugerido"
echo
# Primero lo mas cerca de main; dentro de cada etapa, lo mas viejo. El merge
# de prueba por pares dice que choca con que.
orden=$(printf '%s' "$cola_filas" | while IFS='|' read -r ra fi es ti ed ca hu; do
    case "$es" in aprobado*|entregado*) p=1 ;; revisado*) p=2 ;; implementado*) p=3 ;; "con hallazgos"*) p=4 ;; *) p=5 ;; esac
    echo "$p $((100000 - ed)) $ra"
done | sort -n | awk '{print $3}')
if [ -z "$orden" ]; then
    echo "Nada abierto."
else
    i=0
    for ra in $orden; do
        i=$((i + 1)); choques=""
        git merge-tree --write-tree origin/main "origin/$ra" >/dev/null 2>&1 || choques="$choques main (P3: arreglar antes que nada)"
        for rb in $orden; do
            [ "$rb" = "$ra" ] && continue
            git merge-tree --write-tree "origin/$ra" "origin/$rb" >/dev/null 2>&1 || choques="$choques \`$rb\`"
        done
        if [ -z "$choques" ]; then echo "$i. \`$ra\`: no choca con nada."; else echo "$i. \`$ra\`: choca con$choques en el merge de prueba."; fi
    done
fi
echo
echo "## Alcance"
echo
echo "- $main7_linea"
echo "- PAPEL_TIPOS=funcionalidad:$papel_func otros:$papel_otro. COLA_TIPOS=funcionalidad:$cola_func de $total."
echo "- $ciclo_linea"
echo "- $alcance_linea"
echo "- $invest_linea"
echo "- $release_linea"
echo
echo "## Papel (rama backlog)"
echo
if [ -z "$papel_filas" ]; then
    echo "Vacio: 0 propuesto, 0 disenado."
else
    echo "| ficha | estado | tipo | epica | prioridad | area | candado |"
    echo "|---|---|---|---|---|---|---|"
    printf '%s' "$papel_filas" | while IFS='|' read -r fi es ti ep pr ar ca; do echo "| $fi | $es | $ti | $ep | $pr | $ar | $ca |"; done
fi
echo
echo "## Salud del loop"
echo
if [ "${#salud[@]}" -eq 0 ]; then echo "- SALUD_OK: nada raro en disparos, atascos, papel, roles ni pedidos."; else printf -- '- %s\n' "${salud[@]}"; fi
echo
echo "## Ultimo turno de cada rol"
echo
echo "| rol | fecha-hora UTC | que hizo |"
echo "|---|---|---|"
filas_previas=$(seccion "## Ultimo turno de cada rol" | grep -E '^\| [a-z]+ \|')
for rr in release po arquitecto dev revisor qa investigador; do
    if [ -n "$turno_txt" ] && echo ",$roles_txt," | tr ' ' ',' | grep -q ",$rr,"; then
        echo "| $rr | $ahora_txt | $(printf '%s' "$turno_txt" | tr '\n|' ' /') |"
    else
        printf '%s\n' "$filas_previas" | grep -m1 -E "^\| $rr \|" || true
    fi
done
echo
echo "## Para el humano"
echo
nb=$(echo $borrables | wc -w)
[ "$nb" -gt 0 ] && echo "- Ramas borrables (mergeadas, descartadas o sin codigo), un solo comando: \`git push origin --delete$borrables\`"
if [ -n "$espera_lista" ]; then
    printf '%s' "$espera_lista" | while IFS='|' read -r ra es; do echo "- Espera tu merge: \`$ra\` ($es)"; done
fi
[ -n "$del_humano" ] && echo "- Tocan lo que mergeas vos:$(for x in $del_humano; do printf ' `%s`' "$x"; done)"
[ -n "$tocado" ] && echo "- Ramas del equipo que tocan el playbook (no se mergean solas):$(for x in $tocado; do printf ' `%s`' "$x"; done)"
if [ -n "$pulso_linea" ] && { [ "$perdidos" -ge 2 ] || [ "$murieron" -ge 1 ]; }; then
    echo "- Rutina: $perdidos disparos perdidos y $murieron sesiones que arrancaron y murieron en 48 h; revisar el historial de la Routine \`r6-replay-lab: equipo dev cada 3h\`."
elif [ -z "$pulso_linea" ] && [ "$sin_rastro_48h" -gt 0 ]; then
    echo "- Rutina: $sin_rastro_48h disparos sin rastro en 48 h; revisar el historial de la Routine \`r6-replay-lab: equipo dev cada 3h\`."
fi
[ -n "$candidato" ] && echo "- Playbook candidato: $candidato (la rama del playbook trae algo que main no tiene)."
if [ "$main_func_n" -eq 0 ]; then
    if [ "$papel_func" -eq 0 ]; then cuello="papel sin funcionalidades ($propuesto propuesto, $disenado disenado)"
    elif [ "$cola" -ge "$tope_cola" ] || [ "$total" -ge "$tope_total" ]; then cuello="cola llena (COLA=$cola, TOTAL=$total)"
    elif [ "$disenado" -eq 0 ]; then cuello="diseno trabado (0 disenado)"
    else cuello="en camino (cola: $cola, funcionalidades en cola: $cola_func)"
    fi
    echo "- Funcionalidad: ninguna llego a \`main\` en 7 dias. Cuello de botella: $cuello."
fi
echo "- CI remota: GitHub Actions no ejecuta pasos desde 2026-09-11; lo que vale es \`check.sh\` local. (Aviso fijo.)"
echo
# Pedidos abiertos: ids estables (H1, H2...), fecha de alta y texto; el
# equipo agrega con --humano y cierra con --cerrar, nunca reescribe.
abiertos=$(sub_bloque "### Pedidos abiertos" | grep -E '^- H[0-9]+ ')
resueltos=$(sub_bloque "### Resueltos (ultimos 7 dias)" | grep -E '^- ')
maq=$(sub_bloque "### Maquinaria propuesta por el equipo" | grep -E '^- Mp[0-9]+ ')
if ! printf '%s\n' "$estado_previo" | grep -q '^### Pedidos abiertos'; then
    # Migracion del formato anterior: las preguntas anidadas bajo "Preguntas
    # abiertas" y los avisos que no son automaticos pasan a pedidos con id.
    n=0; fe=$(printf '%s\n' "$estado_previo" | grep -m1 -oE '^actualizado: [0-9]{4}-[0-9]{2}-[0-9]{2}' | cut -c14-)
    fe=${fe:-$hoy}
    while IFS= read -r l; do
        [ -n "$l" ] || continue
        n=$((n + 1)); abiertos="$abiertos- H$n (desde $fe): $l"$'\n'
    done <<< "$(seccion "## Para el humano" | awk '
        /^- (Ramas borrables|Rutina|Playbook|CI remota|Funcionalidad|PRs abiertos|Espera tu merge|Tocan lo que)/ {skip=1; nested=0; next}
        /^- Preguntas abiertas/ {skip=0; nested=1; next}
        /^- / {skip=0; nested=0; sub(/^- /, ""); print; next}
        /^  +- / && nested { if ($0 ~ /~~/) next; sub(/^ +- /, ""); print; next }
        /^  +- / && skip { next }
    ')"
fi
ultimo_h=$(printf '%s\n%s\n' "$abiertos" "$resueltos" | grep -oE '(^- |~~)H[0-9]+' | grep -oE '[0-9]+' | sort -n | tail -1)
ultimo_h=${ultimo_h:-0}
for c in "${cerrar[@]}"; do
    id=${c%%|*}; motivo=${c#*|}
    l=$(printf '%s\n' "$abiertos" | grep -m1 -E "^- $id ")
    [ -n "$l" ] || continue
    abiertos=$(printf '%s\n' "$abiertos" | grep -vE "^- $id ")$'\n'
    resueltos="$resueltos- ~~$id~~ ($hoy): ${l#*: } -> $motivo"$'\n'
done
for h in "${humanos[@]}"; do
    [ -n "$h" ] || continue
    # El mismo pedido no se agrega dos veces: se reconoce por el texto.
    printf '%s\n' "$abiertos" | grep -qF -- "$h" && continue
    ultimo_h=$((ultimo_h + 1)); abiertos="$abiertos- H$ultimo_h (desde $hoy): $h"$'\n'
done
ultimo_m=$(printf '%s\n' "$maq" | grep -oE '^- Mp[0-9]+' | grep -oE '[0-9]+' | sort -n | tail -1); ultimo_m=${ultimo_m:-0}
for m in "${maquinas[@]}"; do
    [ -n "$m" ] || continue
    printf '%s\n' "$maq" | grep -qF -- "$m" && continue
    ultimo_m=$((ultimo_m + 1)); maq="$maq"$'\n'"- Mp$ultimo_m (desde $hoy, ${EQUIPO_SESION:-?}): $m"
done
echo "### Pedidos abiertos"
echo
echo "(Uno por decision, con id estable. El equipo agrega con \`pulso.sh cierre --humano\` y cierra con \`--cerrar H<n>\`; nunca los repite con otras palabras.)"
echo
if printf '%s' "$abiertos" | grep -q .; then printf '%s\n' "$abiertos" | grep . ; else echo "Ninguno."; fi
echo
echo "### Maquinaria propuesta por el equipo"
echo
echo "(Ideas para el loop que el equipo no implementa: las pasa a \`MAQUINARIA.md\` una sesion del dueno.)"
echo
if printf '%s' "$maq" | grep -q .; then printf '%s\n' "$maq" | grep . ; else echo "Ninguna."; fi
echo
echo "### Resueltos (ultimos 7 dias)"
echo
semana=$(date -u -d "@$(( ahora - 604800 ))" +%F)
rec=$(printf '%s\n' "$resueltos" | grep -E '^- ' | awk -v s="$semana" '{ if (match($0, /\(([0-9]{4}-[0-9]{2}-[0-9]{2})\)/)) { d = substr($0, RSTART + 1, 10); if (d >= s) print } else print }')
if [ -n "$rec" ]; then printf '%s\n' "$rec"; else echo "Ninguno."; fi
echo
equipo=$(printf '%s\n' "$estado_previo" | sed -n '/^## Para el equipo/,$p')
if [ -n "$equipo" ]; then
    printf '%s\n' "$equipo"
else
    echo "## Para el equipo"
    echo
    echo "(Escribe aca el humano. El equipo no borra ni edita este bloque; responde debajo con fecha.)"
fi
} >&3
exit 0
