#!/usr/bin/env bash
# Lista el estado del equipo leyendo solo git: fichas en papel (rama backlog),
# ramas de trabajo con su ficha y estado, cola, techo, rutina y entorno. Es lo
# primero que corre cada rol y lo unico que necesita para decidir.
# Uso:  scripts/equipo-dev/estado.sh             (hace fetch de origin)
#       scripts/equipo-dev/estado.sh --resumen   (solo la linea RESUMEN; la lee turno.sh)
#       git show <ref>:scripts/equipo-dev/estado.sh | bash [-s -- --resumen]
#       EQUIPO_AHORA=<epoch> scripts/equipo-dev/estado.sh   (fija "ahora"; gancho de pruebas)
set -u
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
    # anterior) y la rama del playbook trae otro, hay que decirlo.
    pb=origin/claude/equipo-dev/playbook
    if [ "$ref" = origin/main ] && git cat-file -e "$pb:.claude/skills/equipo-dev/rutina.md" 2>/dev/null \
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
cola=0; total=0; cola_func=0
en_curso=0; huerfanas=0; implementado=0; revisado=0; con_hallazgos=0; aprobado=0; entregado=0; espera_humano=0
for r in $(git branch -r --list 'origin/claude/*' --no-merged origin/main --format='%(refname:short)'); do
    es_playbook "$r" && continue
    [ "$r" = "$B" ] && continue
    f=$(ficha_de "$r"); [ -z "$f" ] && continue
    if mergeada "$r"; then echo "$r | mergeada efectivamente: borrable"; continue; fi
    estado=$(campo "$r" "$f" estado)
    edad=$(edad_h "$r")
    if [[ "$estado" == descartado* ]]; then echo "$r | $f | $estado | no cuenta: borrable"; continue; fi
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
    # Sin merges: un "Update branch" del humano desde GitHub no es un pedido. El equipo
    # firma `Claude` (la nube) u `OpenCode` (opencode.sh); cualquier otro autor es el humano.
    humano=$(git log --no-merges "origin/main..$r" --format=%an | grep -vE '^(Claude|OpenCode)' | sort -u | tr '\n' ' ')
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
    mergeada "$r" && { echo "$r | mergeada efectivamente: borrable"; continue; }
    n=$(git rev-list --count "origin/main..$r")
    edad=$(edad_h "$r")
    if [ "$n" -le 1 ]; then
        echo "$r | ${edad}h | solo el commit de reclamo, sin codigo: borrable, no cuenta, no se le crea ficha"
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
if git rev-parse -q --verify "$B" >/dev/null 2>&1; then
    git log --no-merges -5 "$B" --format='%an %ci | %s' -- docs/backlog | grep -vE '^(Claude|OpenCode)' || echo "sin commits humanos recientes"
    git show "$B:docs/backlog/ESTADO.md" 2>/dev/null | sed -n '/^## Para el equipo/,$p' | head -30
else
    echo "sin rama backlog"
fi

echo "== rutina (disparos \`1 */3 * * *\` sin commit de ESTADO.md en backlog en las 3 h siguientes)"
# Cada turno que termina deja un commit de ESTADO.md; un disparo sin ninguno
# en sus 3 horas es una sesion que no corrio o murio antes de cerrar. Es lo
# unico que mide la capa de la rutina desde el repo.
sin_rastro_48h=0
rastros=$(git log --format='%ct %s' "$B" -- docs/backlog/ESTADO.md 2>/dev/null)
if [ -z "$rastros" ]; then
    echo "TURNOS_SIN_RASTRO=? (sin ESTADO.md en backlog)"
else
    cts=$(echo "$rastros" | cut -d' ' -f1)
    primero=$(echo "$cts" | tail -1)
    ultimo=$(echo "$rastros" | awk -v a="$ahora" '$1 <= a { print; exit }')
    if [ -n "$ultimo" ]; then
        echo "ULTIMO_RASTRO=$(date -u -d "@${ultimo%% *}" +%FT%H:%MZ) (${ultimo#* })"
    else
        echo "ULTIMO_RASTRO=ninguno"
    fi
    # Un disparo tiene rastro si algun commit de ESTADO.md cae en [d, d + 3 h).
    con_rastro() { local t; for t in $cts; do [ "$t" -ge "$1" ] && [ "$t" -lt $(( $1 + 10800 )) ] && return 0; done; return 1; }
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
            con_rastro "$d" || { sin=$((sin + 1)); lista="$lista $(date -u -d "@$d" +%m-%dT%H:%MZ)"; }
            d=$(( d + 10800 ))
        done
        echo "$sin $tot$lista"
    }
    read -r sin_rastro_48h _ lista48 <<< "$(contar 172800)"
    read -r sin7 tot7 _ <<< "$(contar 604800)"
    if [ "$sin_rastro_48h" -gt 0 ]; then
        echo "TURNOS_SIN_RASTRO=$sin_rastro_48h en 48 h ($lista48) | $sin7 de $tot7 en 7 dias"
    else
        echo "TURNOS_SIN_RASTRO=0 en 48 h | $sin7 de $tot7 en 7 dias"
    fi
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
