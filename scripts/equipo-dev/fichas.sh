#!/usr/bin/env bash
# Lint de las fichas del equipo y de ALCANCE.md (M5 de MAQUINARIA.md). Un
# estado mal escrito (`implementada`, `en revision`), un candado sin fecha o un
# `turnos:` ilegible no los veia nadie hasta que un rol se confundia: estado.sh
# cuenta por prefijo y una ficha con un estado fuera del vocabulario
# desaparece del pipeline sin aviso.
#
# Uso:  fichas.sh                      fichas de la rama backlog y la de cada rama de trabajo
#       fichas.sh <archivo>...         fichas locales (antes de commitear)
#       fichas.sh --resumen            solo la linea final (la lee estado.sh)
#       fichas.sh --alcance [archivo]  filas de ALCANCE.md (de backlog o el archivo dado)
#       git show <ref>:scripts/equipo-dev/fichas.sh | bash -s -- [...]
# Una linea `FICHA_MAL <ficha>: <motivos>` por ficha con problemas y al final
# `FICHAS_OK (n)` (salida 0) o `FICHAS_MAL=k de n` (salida 1). Con --alcance:
# `ALCANCE_MAL <id>: <motivo>` y `ALCANCE_OK (n)` o `ALCANCE_MAL=k de n`.
set -u
B=origin/claude/equipo-dev/backlog
ROLES='release|po|arquitecto|dev|revisor|qa|investigador'
ESTADOS='^(propuesto|disenado|en curso( .*)?|implementado|revisado|con hallazgos|aprobado|entregado|entregado \(.+\)|descartado \(.+\))$'
resumen=no; alcance=no; archivos=()
while [ $# -gt 0 ]; do
    case "$1" in
        --resumen) resumen=si ;;
        --alcance) alcance=si ;;
        *) archivos+=("$1") ;;
    esac
    shift
done
repo="$(git rev-parse --show-toplevel 2>/dev/null)" || { echo "no es un repo git" >&2; exit 2; }
cd "$repo"

if [ "$alcance" = si ]; then
    if [ "${#archivos[@]}" -gt 0 ]; then texto=$(cat "${archivos[0]}"); else texto=$(git show "$B:docs/backlog/ALCANCE.md" 2>/dev/null); fi
    [ -n "$texto" ] || { echo "ALCANCE_MAL=sin ALCANCE.md"; exit 1; }
    n=0; malos=0
    # Solo las tablas de epicas (las de 6 columnas con id), no la de descartadas.
    while IFS= read -r l; do
        n=$((n + 1))
        id=$(printf '%s' "$l" | awk -F'|' '{gsub(/ /, "", $2); print $2}')
        cols=$(printf '%s' "$l" | awk -F'|' '{print NF - 2}')
        est=$(printf '%s' "$l" | awk -F'|' '{gsub(/^ +| +$/, "", $(NF-1)); print $(NF-1)}')
        mot=""
        [ "$cols" -eq 6 ] || mot="$mot $cols columnas (van 6);"
        printf '%s' "$est" | grep -qE '^(idea|idea \((tests|deuda)\)|ficha [0-9]+|en main|PR #[0-9]+|decision \(.+\)|no|~~.*~~)$' \
            || mot="$mot estado '$est' fuera del vocabulario;"
        datos=$(printf '%s' "$l" | awk -F'|' '{gsub(/^ +| +$/, "", $5); print $5}')
        [ -n "$datos" ] && [ "$datos" != "-" ] || mot="$mot sin datos (si no hay dato, no hay idea);"
        if [ -n "$mot" ]; then malos=$((malos + 1)); echo "ALCANCE_MAL $id:$mot"; fi
    done <<< "$(printf '%s\n' "$texto" | grep -E '^\| *[A-Z]+[0-9]+ *\|')"
    if [ "$malos" -gt 0 ]; then echo "ALCANCE_MAL=$malos de $n"; exit 1; fi
    echo "ALCANCE_OK ($n)"; exit 0
fi

# fuentes: "ref:ruta" o un archivo local
fuentes=()
if [ "${#archivos[@]}" -gt 0 ]; then
    fuentes=("${archivos[@]}")
else
    for f in $(git -c core.quotePath=false ls-tree -r --name-only "$B" docs/backlog/ 2>/dev/null | grep -E '/[0-9]+-[^/]*\.md$'); do
        fuentes+=("$B:$f")
    done
    for r in $(git branch -r --list 'origin/claude/equipo-dev/[0-9]*' --no-merged origin/main --format='%(refname:short)'); do
        f=$(git -c core.quotePath=false diff --name-only --diff-filter=A "origin/main...$r" -- docs/backlog 2>/dev/null | grep -E 'docs/backlog/[0-9]+-' | head -1)
        [ -n "$f" ] && fuentes+=("$r:$f")
    done
fi

leer() { case "$1" in *:*) git show "$1" 2>/dev/null ;; *) cat "$1" 2>/dev/null ;; esac; }
campo() { printf '%s\n' "$2" | grep -m1 "^$1:" | sed "s/^$1:[[:space:]]*//"; }
seccion() { printf '%s\n' "$2" | awk -v h="$1" 'index($0, h) == 1 {f=1; next} f && /^## / {exit} f'; }
# Una seccion tiene contenido si le queda algo despues de sacar el texto guia
# de la plantilla, que empieza con "(Rol)".
con_contenido() { printf '%s\n' "$1" | grep -vE '^[[:space:]]*$|^\((Arquitecto|Dev|Revisor|QA|Cualquiera|La escribe)' | grep -q .; }

n=0; malos=0
for src in "${fuentes[@]}"; do
    n=$((n + 1))
    t=$(leer "$src")
    ruta=${src#*:}; [ "$ruta" = "$src" ] || true
    base=$(basename "$ruta" .md)
    num=${base%%-*}
    mot=""
    if [ -z "$t" ]; then echo "FICHA_MAL $src: no se puede leer"; malos=$((malos + 1)); continue; fi
    [[ "$num" =~ ^[0-9]+$ ]] && [ "$num" -ge 30 ] || mot="$mot numero '$num' (desde 30);"
    printf '%s\n' "$t" | head -1 | grep -qE "^# $num\. " || mot="$mot el titulo no es '# $num. ...';"
    for k in estado candado rama tipo epica area prioridad fuente archivos turnos; do
        printf '%s\n' "$t" | grep -q "^$k:" || mot="$mot falta '$k:';"
    done
    estado=$(campo estado "$t"); candado=$(campo candado "$t"); rama=$(campo rama "$t")
    tipo=$(campo tipo "$t"); prio=$(campo prioridad "$t"); epica=$(campo epica "$t"); turnos=$(campo turnos "$t")
    printf '%s' "$estado" | grep -qE "$ESTADOS" || mot="$mot estado '$estado' fuera del vocabulario;"
    [ "$candado" = "-" ] || printf '%s' "$candado" | grep -qE "^($ROLES) [0-9]{4}-[0-9]{2}-[0-9]{2}" || mot="$mot candado '$candado' (va '-' o '<rol> <fecha-hora UTC>');"
    case "$tipo" in funcionalidad|bug|tests|deuda) ;; *) mot="$mot tipo '$tipo' (funcionalidad, bug, tests o deuda);" ;; esac
    [[ "$prio" =~ ^[1-5]$ ]] || mot="$mot prioridad '$prio' (1 a 5);"
    [ "$epica" = "-" ] || [[ "$epica" =~ ^[a-z0-9-]+$ ]] || mot="$mot epica '$epica' (slug de ALCANCE.md o '-');"
    case "$estado" in
        propuesto*|disenado*|descartado*) ;;
        *) [ "$rama" = "claude/equipo-dev/$base" ] || mot="$mot rama '$rama' (va claude/equipo-dev/$base);" ;;
    esac
    # turnos: pares rol sesion; las notas entre parentesis se toleran.
    ileg=$(printf '%s' "$turnos" | sed -E 's/\([^)]*\)//g' | tr ',' '\n' | sed -E 's/^ +| +$//g' | grep . \
        | grep -vE "^($ROLES) [0-9]{8}T[0-9]{4}Z( .*)?$" | head -2 | tr '\n' ';')
    [ -z "$ileg" ] || mot="$mot turnos ilegibles: $ileg"
    [ -n "$turnos" ] && [ "$turnos" != "-" ] || mot="$mot turnos vacio;"
    crit=$(seccion "## Criterios de aceptacion" "$t" | grep -cE '^- \[( |x)\] ')
    case "$estado" in
        propuesto*|disenado*) [ "$crit" -ge 3 ] && [ "$crit" -le 6 ] || mot="$mot $crit criterios de aceptacion (van 3 a 6);" ;;
        descartado*) ;;
        *) [ "$crit" -ge 1 ] || mot="$mot sin criterios de aceptacion;" ;;
    esac
    con_contenido "$(seccion "## Que gana quien usa la app" "$t")" || [[ "$estado" == descartado* ]] || mot="$mot sin 'Que gana quien usa la app';"
    # Cada etapa deja su seccion: si no, el rol siguiente no tiene de donde
    # leer. Una `entregado` ya la recorto el Release (Diseno, Revision y QA
    # condensadas en un titulo como `## Implementacion, Revision y QA`).
    titulo() { printf '%s\n' "$t" | grep -qiE "^## .*$1"; }
    case "$estado" in
        disenado*|"en curso"*|implementado*|revisado*|"con hallazgos"*|aprobado*)
            if printf '%s\n' "$t" | grep -q '^## Diseno$'; then con_contenido "$(seccion "## Diseno" "$t")" || mot="$mot $estado con '## Diseno' vacio;"
            else titulo Diseno || mot="$mot $estado sin '## Diseno';"
            fi ;;
    esac
    case "$estado" in
        implementado*|revisado*|aprobado*) titulo Implementacion || mot="$mot $estado sin '## Implementacion';" ;;
    esac
    case "$estado" in
        revisado*|aprobado*) titulo Revision || mot="$mot $estado sin '## Revision';" ;;
    esac
    case "$estado" in
        aprobado*) titulo QA || mot="$mot $estado sin '## QA';" ;;
        entregado*)
            printf '%s\n' "$t" | grep -q '^## PR' || mot="$mot $estado sin '## PR';"
            titulo Revision || mot="$mot $estado sin '## Revision' (ni condensada);"
            titulo QA || mot="$mot $estado sin '## QA' (ni condensada);" ;;
    esac
    if [ "$tipo" = bug ]; then
        f=$(campo fuente "$t")
        [ -n "$f" ] && [ "$f" != "-" ] || mot="$mot bug sin 'fuente:' con el repro;"
    fi
    if [ -n "$mot" ]; then malos=$((malos + 1)); [ "$resumen" = si ] || echo "FICHA_MAL $src:$mot"; fi
done
if [ "$malos" -gt 0 ]; then echo "FICHAS_MAL=$malos de $n"; exit 1; fi
echo "FICHAS_OK ($n)"
exit 0
