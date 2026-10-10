#!/usr/bin/env bash
# Lista el estado del equipo leyendo solo git: fichas en papel (rama backlog),
# ramas de trabajo con su ficha y estado, cola, techo y entorno. Es lo primero
# que corre cada rol y lo unico que necesita para decidir.
# Uso:  scripts/equipo-dev/estado.sh            (hace fetch de origin)
#       git show <ref>:scripts/equipo-dev/estado.sh | bash
set -u
repo="$(git rev-parse --show-toplevel 2>/dev/null)" || { echo "no es un repo git" >&2; exit 1; }
cd "$repo"
# El + fuerza la actualizacion aunque el humano haya reescrito una rama
# (por ejemplo "Update with rebase" en un PR).
if ! git fetch -q origin main '+refs/heads/claude/*:refs/remotes/origin/claude/*' 2>/dev/null; then
    echo "FETCH_FALLO: no se pudo actualizar origin; lo que sigue puede estar viejo" >&2
    echo "== fetch"; echo "FETCH_FALLO"
fi
git rev-parse -q --verify 'origin/main^{commit}' >/dev/null || { echo "sin origin/main: no se puede decidir nada" >&2; exit 1; }
B=origin/claude/equipo-dev/backlog
ahora=$(date -u +%s)
arbol_main=$(git rev-parse 'origin/main^{tree}')

# La ficha que la rama AGREGA (no la primera que toca): una rama puede ademas
# editar una ficha que ya esta en main.
ficha_de() { git diff --name-only --diff-filter=A "origin/main...$1" -- docs/backlog 2>/dev/null | grep -E 'docs/backlog/[0-9]+-' | head -1; }
# Las tres formas en que el humano integra: merge commit, squash o rebase.
mergeada() {
    git merge-base --is-ancestor "$1" origin/main 2>/dev/null && return 0
    [ "$(git merge-tree --write-tree origin/main "$1" 2>/dev/null | head -1)" = "$arbol_main" ] && return 0
    local f; f=$(ficha_de "$1")
    [ -n "$f" ] && git cat-file -e "origin/main:$f" 2>/dev/null
}
edad_h() { echo $(( (ahora - $(git log -1 --format=%ct "$1")) / 3600 )); }
campo() { git show "$1:$2" 2>/dev/null | grep -m1 "^$3:" | sed "s/^$3:[[:space:]]*//"; }

echo "== playbook"
for ref in origin/main origin/claude/great-cray-7o9tvf; do
    if git cat-file -e "$ref:.claude/skills/equipo-dev/SKILL.md" 2>/dev/null; then
        echo "$ref@$(git rev-parse --short "$ref")"; break
    fi
done

echo "== pausa"
if git cat-file -e "$B:docs/backlog/PAUSA" 2>/dev/null; then echo "PAUSA"; else echo "no"; fi
echo "== sin_merge (veto del humano al merge automatico)"
if git cat-file -e "$B:docs/backlog/SIN_MERGE" 2>/dev/null; then echo "SIN_MERGE"; else echo "no"; fi

# Sin tipo: no cuenta como funcionalidad (Directiva de alcance del playbook).
tipo_de() { local t; t=$(campo "$1" "$2" tipo); echo "${t:-sin tipo}"; }
echo "== papel (rama backlog)"
papel_func=0; papel_otro=0
if git rev-parse -q --verify "$B" >/dev/null 2>&1; then
    for f in $(git ls-tree -r --name-only "$B" docs/backlog/ | grep -E '/[0-9]+-'); do
        estado=$(campo "$B" "$f" estado); tipo=$(tipo_de "$B" "$f"); epica=$(campo "$B" "$f" epica)
        printf '%s | estado: %s | tipo: %s | epica: %s | candado: %s | rama: %s\n' "$f" "$estado" \
            "$tipo" "${epica:--}" "$(campo "$B" "$f" candado)" "$(campo "$B" "$f" rama)"
        case "$estado" in
            propuesto*|disenado*)
                if [ "$tipo" = funcionalidad ]; then papel_func=$((papel_func + 1)); else papel_otro=$((papel_otro + 1)); fi ;;
        esac
    done
else
    echo "sin rama backlog (la crea el primer PO o Release)"
fi

echo "== ramas de trabajo (origin/claude/* no mergeadas con ficha)"
cola=0; total=0; cola_func=0
for r in $(git branch -r --list 'origin/claude/*' --no-merged origin/main --format='%(refname:short)'); do
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
    # Sin merges: un "Update branch" del humano desde GitHub no es un pedido.
    humano=$(git log --no-merges "origin/main..$r" --format=%an | grep -v '^Claude' | sort -u | tr '\n' ' ')
    printf '%s | %s | estado: %s | tipo: %s | candado: %s | %sh | cuenta en cola: %s | commits humanos: %s\n' \
        "$r" "$f" "$estado" "$tipo" "$(campo "$r" "$f" candado)" "$edad" "$reciente" "${humano:-ninguno}"
done

echo "== ramas del playbook anterior (sin ficha; reclamo en el roadmap)"
# El playbook anterior reclamaba en docs/roadmap.md con un commit "Reclama:" y
# la sesion podia imponer el nombre de la rama, asi que no alcanza con el glob.
for r in $(git branch -r --list 'origin/claude/*' --no-merged origin/main --format='%(refname:short)'); do
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
    git log --no-merges -5 "$B" --format='%an %ci | %s' -- docs/backlog | grep -v '^Claude' || echo "sin commits humanos recientes"
    git show "$B:docs/backlog/ESTADO.md" 2>/dev/null | sed -n '/^## Para el equipo/,$p' | head -30
else
    echo "sin rama backlog"
fi

echo "== cola"
echo "COLA=$cola (tope 4)  TOTAL=$total (tope 6)"

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
if git cat-file -e "$B:docs/backlog/ALCANCE.md" 2>/dev/null; then
    # Una idea libre es una fila de tabla cuya ultima columna dice "idea".
    libres=$(git show "$B:docs/backlog/ALCANCE.md" | grep -cE '\|[[:space:]]*idea[[:space:]]*\|[[:space:]]*$')
    echo "ALCANCE=backlog, ideas libres: $libres"
else
    echo "ALCANCE=falta en backlog: copiar docs/backlog/ALCANCE.md desde el playbook"
fi

echo "== entorno"
# Mismo criterio que check.sh: el venv si existe, si no el sistema.
py=python3; [ -x .venv/bin/python ] && py=.venv/bin/python
tiene_ruff=no; { [ -x .venv/bin/ruff ] || command -v ruff >/dev/null 2>&1; } && tiene_ruff=si
if [ -d frontend/node_modules ] && [ "$tiene_ruff" = si ] && "$py" -c 'import django, zstandard' 2>/dev/null; then
    echo "completo"
else
    echo "ENTORNO_INCOMPLETO: pip install -r requirements.txt -r requirements-dev.txt; (cd frontend && npm install)"
fi
