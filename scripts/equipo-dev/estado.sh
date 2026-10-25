#!/usr/bin/env bash
# Lista el estado del equipo leyendo solo git: fichas en papel (rama backlog),
# ramas de trabajo con su ficha y estado, cola, techo, rutina y entorno. Es lo
# primero que corre cada rol y lo unico que necesita para decidir.
# Uso:  scripts/equipo-dev/estado.sh             (hace fetch de origin)
#       scripts/equipo-dev/estado.sh --resumen   (solo la linea RESUMEN; la lee turno.sh)
#       git show <ref>:scripts/equipo-dev/estado.sh | bash [-s -- --resumen]
#       EQUIPO_AHORA=<epoch> scripts/equipo-dev/estado.sh   (fija "ahora"; gancho de pruebas)
#       EQUIPO_AHORA=<epoch> scripts/equipo-dev/estado.sh --rastros "<epochs>"
#           (solo CADENCIA y TURNOS_SIN_RASTRO sobre esos commits; sin git; lo usa pruebas.sh)
set -u

# Disparos de la rutina sin rastro, medidos contra la cadencia real. La
# cadencia la fija la Routine, que vive fuera del repo y paso de 3 h a 1 h y a
# 4 h sin que el playbook se enterara: contar contra un cron fijo de 3 h daba
# por perdidos 2 disparos por dia que nunca existieron (15 de 56 en 7 dias, con
# 2 reales). Por eso sale de los rastros: commits de ESTADO.md a menos de 30
# min son una misma sesion; la cadencia de cada intervalo es la mediana de los
# 9 que lo rodean (la de hoy, la de los ultimos 9; 3 h si hay menos de 3), y un
# intervalo de k cadencias (redondeado) esconde k - 1 disparos. El tramo
# abierto (ultimo rastro hasta ahora) redondea con +1/4 y no con +1/2: el turno
# en curso commitea al cerrar, hasta 135 min despues de su disparo, y no puede
# contarse como perdido.
# Entrada: epochs (uno por linea, cualquier orden) y el "ahora". Salida, una
# linea: cadencia_s disparos_48h sin_48h disparos_7d sin_7d [epochs de los sin rastro en 48 h].
rastros_calc() {
    sort -n | awk -v ahora="$1" '
        $1 > ahora { next }
        { if (m == 0 || $1 - prev >= 1800) s[++m] = $1; prev = $1 }
        # Mediana de los intervalos d[a..b].
        function mediana(a, b,    k, i, j, x, t) {
            k = 0
            for (i = a; i <= b; i++) t[++k] = d[i]
            for (i = 1; i <= k; i++) for (j = i + 1; j <= k; j++) if (t[j] < t[i]) { x = t[i]; t[i] = t[j]; t[j] = x }
            x = (k % 2) ? t[(k + 1) / 2] : int((t[k / 2] + t[k / 2 + 1]) / 2)
            return (x < 600) ? 600 : x
        }
        END {
            for (i = 1; i < m; i++) d[i] = s[i + 1] - s[i]
            g = m - 1
            # Cadencia de hoy: los ultimos 9 intervalos. La de cada intervalo
            # viejo, los 9 centrados en el: un cambio de cadencia de la Routine
            # no convierte en perdidos los intervalos de la cadencia anterior.
            P = (g >= 3) ? mediana((g - 8 > 1) ? g - 8 : 1, g) : 10800
            t48 = 0; f48 = 0; t7 = 0; f7 = 0; lista = ""
            for (i = 1; i <= m; i++) {
                if (i < m) {
                    Pi = (g >= 3) ? mediana((i - 4 > 1) ? i - 4 : 1, (i + 4 < g) ? i + 4 : g) : P
                    n = int(d[i] / Pi + 0.5)
                } else {
                    Pi = P
                    n = int((ahora - s[i]) / Pi + 0.25)
                }
                for (q = 1; q <= n; q++) {
                    f = s[i] + q * Pi
                    # El ultimo disparo de cada tramo no se perdio: es el que dejo
                    # el rastro siguiente o, en el tramo abierto, el turno en curso.
                    perdido = (q == n) ? 0 : 1
                    if (f > ahora) continue
                    if (f >= ahora - 604800) { t7++; if (perdido) f7++ }
                    if (f >= ahora - 172800) { t48++; if (perdido) { f48++; lista = lista " " f } }
                }
            }
            printf "%d %d %d %d %d%s\n", P, t48, f48, t7, f7, lista
        }'
}
# Imprime CADENCIA y TURNOS_SIN_RASTRO a partir de la salida de rastros_calc.
rastros_lineas() {
    local p t48 f48 t7 f7 lista="" e
    read -r p t48 f48 t7 f7 resto <<< "$1"
    for e in ${resto:-}; do lista="$lista ~$(date -u -d "@$e" +%m-%dT%H:%MZ)"; done
    echo "CADENCIA=$((p / 3600))h$(printf '%02d' $(( (p % 3600) / 60 ))) (mediana de los ultimos intervalos entre turnos con rastro)"
    if [ "$f48" -gt 0 ]; then
        echo "TURNOS_SIN_RASTRO=$f48 en 48 h (${lista# }) | $f7 de $t7 en 7 dias"
    else
        echo "TURNOS_SIN_RASTRO=0 en 48 h | $f7 de $t7 en 7 dias"
    fi
}
if [ "${1:-}" = --rastros ]; then
    rastros_lineas "$(printf '%s\n' ${2:-} | rastros_calc "${EQUIPO_AHORA:-$(date -u +%s)}")"
    exit 0
fi
# Con --resumen todo lo demas va a /dev/null y la linea final sale por el
# descriptor 3, que conserva la salida original.
resumen=no
if [ "${1:-}" = --resumen ]; then resumen=si; exec 3>&1; exec >/dev/null; fi
repo="$(git rev-parse --show-toplevel 2>/dev/null)" || { echo "no es un repo git" >&2; exit 1; }
cd "$repo"
# El + fuerza la actualizacion aunque el humano haya reescrito una rama
# (por ejemplo "Update with rebase" en un PR).
fetch_fallo=no
if ! git fetch -q origin main '+refs/heads/claude/*:refs/remotes/origin/claude/*' 2>/dev/null; then
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

echo "== playbook"
# Se prueba rutina.md y no SKILL.md: solo el playbook nuevo lo tiene, asi que
# un main con un playbook viejo mergeado no gana la cadena.
for ref in origin/main origin/claude/equipo-dev/playbook; do git cat-file -e "$ref:.claude/skills/equipo-dev/rutina.md" 2>/dev/null && break; done
if git cat-file -e "$ref:.claude/skills/equipo-dev/rutina.md" 2>/dev/null; then
    echo "$ref@$(git rev-parse --short "$ref")"
    # Si main gano la cadena con un playbook viejo (por ejemplo, mergeado un PR
    # anterior) y la rama del playbook trae otro, hay que decirlo. Solo si la
    # rama trae commits que main no tiene: una rama del playbook ya mergeada y
    # quieta tiene un SKILL.md distinto porque main siguio, no porque sea nueva
    # (asi se anunciaba como candidato desde 2026-10-21 un e8d6798 ya en main).
    pb=origin/claude/equipo-dev/playbook
    if [ "$ref" = origin/main ] && git cat-file -e "$pb:.claude/skills/equipo-dev/rutina.md" 2>/dev/null \
        && ! git merge-base --is-ancestor "$pb" origin/main 2>/dev/null \
        && [ "$(git rev-parse "origin/main:.claude/skills/equipo-dev/SKILL.md")" != "$(git rev-parse "$pb:.claude/skills/equipo-dev/SKILL.md")" ]; then
        echo "PLAYBOOK_CANDIDATO=$pb@$(git rev-parse --short "$pb")"
    fi
else
    echo "SIN_PLAYBOOK"
fi

echo "== pausa"
pausa=no
if git cat-file -e "$B:docs/backlog/PAUSA" 2>/dev/null; then pausa=si; echo "PAUSA"; else echo "no"; fi
echo "== sin_merge (veto del humano al merge automatico)"
sin_merge=no
if git cat-file -e "$B:docs/backlog/SIN_MERGE" 2>/dev/null; then sin_merge=si; echo "SIN_MERGE"; else echo "no"; fi

# Sin tipo: no cuenta como funcionalidad (Directiva de alcance del playbook).
tipo_de() { local t; t=$(campo "$1" "$2" tipo); echo "${t:-sin tipo}"; }
echo "== papel (rama backlog)"
papel_func=0; papel_otro=0; propuesto=0; disenado=0
if git rev-parse -q --verify "$B" >/dev/null 2>&1; then
    for f in $(git -c core.quotePath=false ls-tree -r --name-only "$B" docs/backlog/ | grep -E '/[0-9]+-'); do
        estado=$(campo "$B" "$f" estado); tipo=$(tipo_de "$B" "$f"); epica=$(campo "$B" "$f" epica)
        printf '%s | estado: %s | tipo: %s | epica: %s | candado: %s | rama: %s\n' "$f" "$estado" \
            "$tipo" "${epica:--}" "$(campo "$B" "$f" candado)" "$(campo "$B" "$f" rama)"
        case "$estado" in
            propuesto*|disenado*)
                if [ "$tipo" = funcionalidad ]; then papel_func=$((papel_func + 1)); else papel_otro=$((papel_otro + 1)); fi ;;
        esac
        # Solo el papel cuenta aca; el espejo "en curso" de una ficha reclamada
        # no manda: la rama de trabajo si.
        case "$estado" in
            propuesto*) propuesto=$((propuesto + 1)) ;;
            disenado*) disenado=$((disenado + 1)) ;;
        esac
    done
else
    echo "sin rama backlog (la crea el primer PO o Release)"
fi

echo "== ramas de trabajo (origin/claude/* no mergeadas con ficha)"
borrables=()
cola=0; total=0; cola_func=0
en_curso=0; huerfanas=0; implementado=0; revisado=0; con_hallazgos=0; aprobado=0; entregado=0; espera_humano=0
for r in $(git branch -r --list 'origin/claude/*' --no-merged origin/main --format='%(refname:short)'); do
    es_playbook "$r" && continue
    [ "$r" = "$B" ] && continue
    f=$(ficha_de "$r"); [ -z "$f" ] && continue
    if mergeada "$r"; then echo "$r | mergeada efectivamente: borrable"; borrables+=("${r#origin/}"); continue; fi
    estado=$(campo "$r" "$f" estado)
    edad=$(edad_h "$r")
    if [[ "$estado" == descartado* ]]; then echo "$r | $f | $estado | no cuenta: borrable"; borrables+=("${r#origin/}"); continue; fi
    total=$((total + 1))
    reciente=no
    if [ "$edad" -lt 336 ] || [[ "$estado" == entregado* ]]; then reciente=si; cola=$((cola + 1)); fi
    tipo=$(tipo_de "$r" "$f")
    [ "$tipo" = funcionalidad ] && cola_func=$((cola_func + 1))
    candado=$(campo "$r" "$f" candado)
    # P8: un candado con mas de 3 h sin commits sobre la ficha (los de
    # ESTADO.md no cuentan) es una sesion muerta.
    ult=$(git log -1 --format=%ct "$r" -- "$f"); ult=${ult:-0}
    muerto=no
    [ "$candado" != "-" ] && [ $(( ahora - ult )) -ge 10800 ] && muerto=si
    case "$estado" in
        aprobado*) aprobado=$((aprobado + 1)) ;;
        entregado) entregado=$((entregado + 1)) ;;
        "entregado ("*) espera_humano=$((espera_humano + 1)) ;;
        revisado*) revisado=$((revisado + 1)) ;;
        implementado*) implementado=$((implementado + 1)) ;;
        "con hallazgos"*) con_hallazgos=$((con_hallazgos + 1)) ;;
        "en curso"*)
            en_curso=$((en_curso + 1))
            # Huerfana: nadie la tiene (candado suelto) o quien la tenia murio.
            if [ "$candado" = "-" ] || [ $(( ahora - ult )) -ge 10800 ]; then huerfanas=$((huerfanas + 1)); fi ;;
    esac
    # Sin merges: un "Update branch" del humano desde GitHub no es un pedido.
    humano=$(git log --no-merges "origin/main..$r" --format=%an | grep -v '^Claude' | sort -u | tr '\n' ' ')
    printf '%s | %s | estado: %s | tipo: %s | candado: %s | %sh | cuenta en cola: %s | commits humanos: %s | candado muerto: %s\n' \
        "$r" "$f" "$estado" "$tipo" "$candado" "$edad" "$reciente" "${humano:-ninguno}" "$muerto"
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
    mergeada "$r" && { echo "$r | mergeada efectivamente: borrable"; borrables+=("${r#origin/}"); continue; }
    n=$(git rev-list --count "origin/main..$r")
    edad=$(edad_h "$r")
    if [ "$n" -le 1 ]; then
        echo "$r | ${edad}h | solo el commit de reclamo, sin codigo: borrable, no cuenta, no se le crea ficha"
        borrables+=("${r#origin/}")
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

echo "== ramas borrables (las borra el humano: el proxy de la nube corta git push --delete)"
# Las del equipo ya mergeadas con merge commit no salen arriba (--no-merged) y
# se acumulaban en ESTADO.md copiadas a mano, una vineta por rama, turno tras
# turno (31 al 2026-10-25). Aca salen de git, en un solo comando para pegar.
for r in $(git branch -r --list 'origin/claude/equipo-dev/*' --merged origin/main --format='%(refname:short)'); do
    es_playbook "$r" && continue
    [ "$r" = "$B" ] && continue
    borrables+=("${r#origin/}")
done
echo "BORRABLES=${#borrables[@]}"
if [ "${#borrables[@]}" -gt 0 ]; then
    echo "BORRAR: git push origin --delete $(printf '%s\n' "${borrables[@]}" | sort -u -V | tr '\n' ' ' | sed 's/ $//')"
fi

echo "== pedidos del humano en backlog (commits suyos y seccion Para el equipo)"
if git rev-parse -q --verify "$B" >/dev/null 2>&1; then
    git log --no-merges -5 "$B" --format='%an %ci | %s' -- docs/backlog | grep -v '^Claude' || echo "sin commits humanos recientes"
    git show "$B:docs/backlog/ESTADO.md" 2>/dev/null | sed -n '/^## Para el equipo/,$p' | head -30
    # El humano no lee un tablero que solo crece: `## Para el humano` paso de
    # 14 a 98 vinetas en 15 dias (5,8 a 29,9 KB de ESTADO.md, reescrito entero
    # por cada turno) y nunca respondio en `## Para el equipo`. El cierre comun
    # lo poda cuando pasa el tope.
    tope_para_el_humano=20
    n=$(git show "$B:docs/backlog/ESTADO.md" 2>/dev/null | sed -n '/^## Para el humano/,/^## Para el equipo/p' | grep -cE '^[[:space:]]*- ')
    echo "PARA_EL_HUMANO=$n vinetas (tope $tope_para_el_humano)$([ "$n" -gt "$tope_para_el_humano" ] && echo ': podar en el cierre')"
else
    echo "sin rama backlog"
fi

echo "== rutina (disparos sin commit de ESTADO.md en backlog, a la cadencia medida)"
# Cada turno que termina deja un commit de ESTADO.md; un disparo sin ninguno
# es una sesion que no corrio o murio antes de cerrar. Es lo unico que mide la
# capa de la rutina desde el repo. El calculo esta en rastros_calc, arriba.
sin_rastro_48h=0
rastros=$(git log --format='%ct %s' "$B" -- docs/backlog/ESTADO.md 2>/dev/null)
if [ -z "$rastros" ]; then
    echo "TURNOS_SIN_RASTRO=? (sin ESTADO.md en backlog)"
else
    ultimo=$(echo "$rastros" | awk -v a="$ahora" '$1 <= a { print; exit }')
    if [ -n "$ultimo" ]; then
        echo "ULTIMO_RASTRO=$(date -u -d "@${ultimo%% *}" +%FT%H:%MZ) (${ultimo#* })"
    else
        echo "ULTIMO_RASTRO=ninguno"
    fi
    calculo=$(echo "$rastros" | cut -d' ' -f1 | rastros_calc "$ahora")
    read -r _ _ sin_rastro_48h _ <<< "$calculo"
    rastros_lineas "$calculo"
fi

echo "== cola"
echo "COLA=$cola (tope $tope_cola)  TOTAL=$total (tope $tope_total)"

echo "== alcance"
echo "PAPEL_TIPOS=funcionalidad:$papel_func otros:$papel_otro (propuesto y disenado; la directiva pide 3 funcionalidades antes de tests sueltos)"
echo "COLA_TIPOS=funcionalidad:$cola_func de $total ramas de trabajo"
# --first-parent -m fecha cada ficha por el merge que la trajo a main, no por
# el commit "Reclama:" de su rama, que puede tener mas de una semana.
main_func=""; main_otro=0
for f in $(git log --since=7.days --first-parent -m origin/main --diff-filter=A --name-only --format= -- docs/backlog | grep -E '/[0-9]+-' | sort -u); do
    if [ "$(tipo_de origin/main "$f")" = funcionalidad ]; then main_func="$main_func $(basename "$f" .md)"; else main_otro=$((main_otro + 1)); fi
done
echo "MAIN_7D=funcionalidad:$(echo $main_func | wc -w)${main_func:+ (${main_func# })} otros:$main_otro (fichas que llegaron a main en 7 dias)"
libres=0
if git cat-file -e "$B:docs/backlog/ALCANCE.md" 2>/dev/null; then
    # Una idea libre es una fila de tabla cuya ultima columna dice "idea".
    libres=$(git show "$B:docs/backlog/ALCANCE.md" | grep -cE '\|[[:space:]]*idea[[:space:]]*\|[[:space:]]*$')
    echo "ALCANCE=backlog, ideas libres: $libres"
else
    echo "ALCANCE=falta en backlog: copiar docs/backlog/ALCANCE.md desde el playbook"
fi
if git cat-file -e "$B:docs/backlog/INVESTIGACION.md" 2>/dev/null; then
    ultima=$(git show "$B:docs/backlog/INVESTIGACION.md" | grep -m1 -oE '^### [0-9]{4}-[0-9]{2}-[0-9]{2}' | cut -c5-)
    echo "INVESTIGACION=backlog, ultima entrada: ${ultima:-ninguna}"
else
    echo "INVESTIGACION=falta en backlog: copiar docs/backlog/INVESTIGACION.md desde el playbook"
fi
# Rotacion. El PO tomaba siempre la idea mas barata de la epica "en curso", y
# las ideas sueltas de un tema la dejaban en curso para siempre: de las fichas
# 36 a 63, 13 son de lado-y-marcador, y 10 de las 20 entregas de la 40 a la 60
# sumaron una tarjeta a Tendencias (17 tarjetas), mientras exportar,
# datos-nuevos-del-parser y paridad-referencia no entregaron nada. Se mide sobre
# las ultimas funcionalidades que llegaron a main; el PO lo lee en ROTACION.
ventana_rotacion=10 tope_rotacion=4
declare -A por_epica=() por_pagina=()
vistas=0; commit=""
while read -r linea; do
    case "$linea" in
        "C "*) commit=${linea#C }; continue ;;
        docs/backlog/[0-9]*-*.md) ;;
        *) continue ;;
    esac
    [ "$(tipo_de origin/main "$linea")" = funcionalidad ] || continue
    vistas=$((vistas + 1))
    e=$(campo origin/main "$linea" epica); e=${e:--}
    por_epica[$e]=$(( ${por_epica[$e]:-0} + 1 ))
    for pg in $(git diff --name-only "$commit^1" "$commit" -- frontend/src/pages 2>/dev/null | xargs -r -n1 basename); do
        por_pagina[$pg]=$(( ${por_pagina[$pg]:-0} + 1 ))
    done
    [ "$vistas" -ge "$ventana_rotacion" ] && break
done < <(git log --first-parent -m origin/main --diff-filter=A --name-only --format='C %H' -- docs/backlog 2>/dev/null)
conteo() { local -n m=$1; local k; for k in "${!m[@]}"; do echo "$k:${m[$k]}"; done | sort -t: -k2,2nr -k1,1 | tr '\n' ' ' | sed 's/ $//'; }
echo "ROTACION_EPICAS=$(conteo por_epica) (epica de las ultimas $vistas funcionalidades en main)"
echo "ROTACION_PAGINAS=$(conteo por_pagina) (paginas de frontend/src/pages que tocaron)"
saturadas=""
for k in "${!por_epica[@]}"; do [ "$k" != - ] && [ "${por_epica[$k]}" -ge "$tope_rotacion" ] && saturadas="$saturadas epica $k,"; done
for k in "${!por_pagina[@]}"; do [ "${por_pagina[$k]}" -ge "$tope_rotacion" ] && saturadas="$saturadas pagina $k,"; done
saturadas=${saturadas%,}
# Epicas con ideas libres y nada en main (deuda-y-tests no es funcionalidad).
sin_entrega=$(git show "$B:docs/backlog/ALCANCE.md" 2>/dev/null | awk -F'|' '
    /^### / { ep = $0; sub(/^### /, "", ep); sub(/:.*/, "", ep); orden[++n] = ep; next }
    ep != "" && /^\|/ { st = $(NF - 1); gsub(/^[ \t]+|[ \t]+$/, "", st); if (st == "idea") libre[ep] = 1; if (st ~ /^en main/) hecha[ep] = 1 }
    END { for (i = 1; i <= n; i++) { e = orden[i]; if (libre[e] && !hecha[e] && e != "deuda-y-tests") printf "%s%s", (c++ ? " " : ""), e } }')
echo "ROTACION=saturadas (${tope_rotacion} o mas de las ultimas ${ventana_rotacion}):${saturadas:- ninguna} | sin entrega: ${sin_entrega:-ninguna}"

echo "== resumen"
# Una linea con todo lo que turno.sh necesita para elegir el rol. Mismo orden
# siempre: pruebas.sh cuenta los 20 pares.
linea_resumen="RESUMEN propuesto=$propuesto disenado=$disenado en_curso=$en_curso huerfanas=$huerfanas implementado=$implementado revisado=$revisado con_hallazgos=$con_hallazgos aprobado=$aprobado entregado=$entregado espera_humano=$espera_humano cola=$cola total=$total tope_cola=$tope_cola tope_total=$tope_total tope_propuesto=$tope_propuesto tope_disenado=$tope_disenado ideas_libres=$libres sin_merge=$sin_merge pausa=$pausa sin_rastro_48h=$sin_rastro_48h"
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

# Con el fetch caido la linea seria vieja: mejor ninguna, y turno.sh cae al reloj.
if [ "$resumen" = si ] && [ "$fetch_fallo" = no ]; then echo "$linea_resumen" >&3; fi
exit 0
