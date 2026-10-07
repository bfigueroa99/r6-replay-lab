#!/usr/bin/env bash
# Lista el estado del equipo leyendo solo git: fichas en papel (rama backlog),
# ramas de trabajo con su ficha y estado, cola, techo y entorno. Es lo primero
# que corre cada rol y lo unico que necesita para decidir.
# Uso:  scripts/equipo-dev/estado.sh            (hace fetch de origin)
#       git show <ref>:scripts/equipo-dev/estado.sh | bash
set -u
repo="$(git rev-parse --show-toplevel 2>/dev/null)" || { echo "no es un repo git" >&2; exit 1; }
cd "$repo"
git fetch -q origin main 'refs/heads/claude/*:refs/remotes/origin/claude/*' 2>/dev/null
B=origin/claude/equipo-dev/backlog
ahora=$(date -u +%s)
arbol_main=$(git rev-parse 'origin/main^{tree}')

ficha_de() { git diff --name-only "origin/main...$1" -- docs/backlog 2>/dev/null | grep -E 'docs/backlog/[0-9]+-' | head -1; }
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

echo "== papel (rama backlog)"
if git rev-parse -q --verify "$B" >/dev/null 2>&1; then
    for f in $(git ls-tree -r --name-only "$B" docs/backlog/ | grep -E '/[0-9]+-'); do
        printf '%s | estado: %s | candado: %s | rama: %s\n' "$f" "$(campo "$B" "$f" estado)" \
            "$(campo "$B" "$f" candado)" "$(campo "$B" "$f" rama)"
    done
else
    echo "sin rama backlog (la crea el primer PO o Release)"
fi

echo "== ramas de trabajo (origin/claude/* no mergeadas con ficha)"
cola=0; total=0
for r in $(git branch -r --list 'origin/claude/*' --no-merged origin/main --format='%(refname:short)'); do
    [ "$r" = "$B" ] && continue
    f=$(ficha_de "$r"); [ -z "$f" ] && continue
    if mergeada "$r"; then echo "$r | mergeada efectivamente: borrable"; continue; fi
    total=$((total + 1))
    estado=$(campo "$r" "$f" estado)
    edad=$(edad_h "$r")
    reciente=no
    if [ "$edad" -lt 336 ] || [[ "$estado" == entregado* ]]; then reciente=si; cola=$((cola + 1)); fi
    humano=$(git log "origin/main..$r" --format=%an | grep -v '^Claude' | sort -u | tr '\n' ' ')
    printf '%s | %s | estado: %s | candado: %s | %sh | cuenta en cola: %s | commits humanos: %s\n' \
        "$r" "$f" "$estado" "$(campo "$r" "$f" candado)" "$edad" "$reciente" "${humano:-ninguno}"
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
    total=$((total + 1))
    n=$(git rev-list --count "origin/main..$r")
    edad=$(edad_h "$r")
    if [ "$n" -le 1 ]; then
        echo "$r | ${edad}h | solo el commit de reclamo, sin codigo: borrable, no se le crea ficha"
    else
        # Con codigo es trabajo que espera al humano, igual que una rama con ficha.
        [ "$edad" -lt 336 ] && cola=$((cola + 1))
        echo "$r | ${edad}h | $n commits sin ficha: el primer Revisor le crea una en implementado | cuenta en cola: $([ "$edad" -lt 336 ] && echo si || echo no) | $(git log -1 --format=%s "$r")"
    fi
done

echo "== cola"
echo "COLA=$cola (tope 3)  TOTAL=$total (tope 5)"

echo "== entorno"
if [ -d frontend/node_modules ] && command -v ruff >/dev/null 2>&1 && python3 -c 'import django, zstandard' 2>/dev/null; then
    echo "completo"
else
    echo "ENTORNO_INCOMPLETO: pip install -r requirements.txt -r requirements-dev.txt; (cd frontend && npm install)"
fi
