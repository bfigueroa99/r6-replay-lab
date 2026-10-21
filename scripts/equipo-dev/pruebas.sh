#!/usr/bin/env bash
# Pruebas del playbook del equipo: que los scripts, la skill, la rutina y las
# plantillas digan lo mismo, y que la regla del rol siga fija. No escribe en el
# repo ni en el remoto. Corre antes de empujar a la rama del playbook.
# Uso:  bash scripts/equipo-dev/pruebas.sh                                   # arbol de trabajo
#       bash scripts/equipo-dev/pruebas.sh origin/claude/equipo-dev/playbook  # lo que hay en una ref
#       PRUEBAS_SIN_RED=1 bash scripts/equipo-dev/pruebas.sh                 # sin la prueba contra el remoto
#       git show <ref>:scripts/equipo-dev/pruebas.sh | bash -s -- <ref>
# Una linea `OK <nombre>` o `FALLA <nombre>: <detalle>` por comprobacion;
# termina en `PRUEBAS_OK (n)` con salida 0 o `PRUEBAS_FALLAN: k` con salida 1.
set -u
# Rutas que los textos nombran y que viven solo en la rama backlog, no en el
# arbol. Las que llevan NN, * o < son patrones, no archivos, y tambien se saltan.
EXENTAS="docs/backlog/ESTADO.md docs/backlog/PAUSA docs/backlog/SIN_MERGE"

REF="${1:-}"
repo="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
cd "$repo"
if [ -n "$REF" ]; then
    git rev-parse -q --verify "$REF^{commit}" >/dev/null 2>&1 || { echo "FALLA ref: $REF no existe"; echo "PRUEBAS_FALLAN: 1"; exit 1; }
    base=$(mktemp -d)
    trap 'rm -rf "$base"' EXIT
    for p in $(git ls-tree -r --name-only "$REF" -- .claude .opencode scripts docs/backlog 2>/dev/null); do
        mkdir -p "$base/$(dirname "$p")"
        git show "$REF:$p" > "$base/$p"
    done
else
    base="$repo"
fi
sk=$base/.claude/skills/equipo-dev/SKILL.md
ru=$base/.claude/skills/equipo-dev/rutina.md
tu=$base/scripts/equipo-dev/turno.sh
es=$base/scripts/equipo-dev/estado.sh
bl=$base/docs/backlog

n=0; fallos=0
ok() { n=$((n + 1)); echo "OK $1"; }
falla() { n=$((n + 1)); fallos=$((fallos + 1)); echo "FALLA $1:$2"; }
cierra() { if [ -z "$2" ]; then ok "$1"; else falla "$1" "$2"; fi; }

# 1. sintaxis
det=""
for s in scripts/equipo-dev/turno.sh scripts/equipo-dev/estado.sh scripts/equipo-dev/pruebas.sh scripts/equipo-dev/opencode.sh scripts/check.sh .claude/hooks/session-start.sh; do
    if [ ! -f "$base/$s" ]; then det="$det falta $s"
    elif ! bash -n "$base/$s" 2>/dev/null; then det="$det bash -n $s"
    fi
done
cierra sintaxis "$det"

# 2. cadena: la misma secuencia de refs en los cuatro lugares, probando
# rutina.md (solo el playbook nuevo lo tiene), y ninguna ref vieja en ningun
# lado. El patron de las viejas se arma partido para que este archivo no lo
# contenga.
det=""
cadena='origin/main origin/claude/equipo-dev/playbook'
for f in "$tu" "$es" "$sk" "$ru"; do
    c=$(grep -o "$cadena" "$f" 2>/dev/null | wc -l)
    [ "$c" -eq 1 ] || det="$det ${f#$base/} tiene la cadena $c veces;"
    grep -- "$cadena" "$f" 2>/dev/null | grep -qF '/equipo-dev/rutina.md"' || det="$det ${f#$base/} no prueba rutina.md en la cadena;"
done
viejas='great-'"cray"'\|ccr'"-"
h=$(grep -rln -- "$viejas" "$base/.claude" "$base/scripts/equipo-dev" "$bl/README.md" "$bl/PLANTILLA.md" "$bl/ESTADO.plantilla.md" "$bl/ALCANCE.md" "$bl/INVESTIGACION.md" "$bl/MAQUINARIA.md" 2>/dev/null | sed "s#^$base/##" | tr '\n' ' ')
[ -z "$h" ] || det="$det refs viejas en: $h"
cierra cadena "$det"

# 3. rutina: corta, con lo que la sesion necesita para arrancar y sin hechos
# que se pudren (topes, minutos, prioridades viven en el playbook).
det=""
if [ ! -f "$ru" ]; then det=" no existe"
else
    b=$(wc -c < "$ru"); [ "$b" -lt 2600 ] || det="$det $b bytes (tope 2600)"
    for t in 'turno.sh' 'estado.sh' 'rol:' 'SKILL.md' 'SIN_PLAYBOOK' '+refs/heads/claude/*'; do
        grep -qF -- "$t" "$ru" || det="$det falta '$t'"
    done
    for t in tope minutos P1; do grep -qi -- "$t" "$ru" && det="$det contiene '$t'"; done
fi
cierra rutina "$det"

# 4. rutas: todo lo que los textos nombran como archivo existe.
det=""
# Linea por linea y no `for p in $(...)`: el for expandiria `docs/backlog/*.md`
# contra el directorio actual.
while IFS= read -r p; do
    [ -n "$p" ] || continue
    case " $EXENTAS " in *" $p "*) continue ;; esac
    case "$p" in *NN*|*'*'*|*'<'*) continue ;; esac
    [ -e "$base/$p" ] || det="$det $p"
done <<< "$(cat "$sk" "$ru" "$bl/README.md" 2>/dev/null | grep -oE '`(\.claude|scripts|docs/backlog)/[^`]*`' | tr -d '`' | sort -u)"
cierra rutas "$det"

# 5. topes: los numeros de estado.sh son los que el playbook y la plantilla
# dicen en prosa (las lineas se juntan para tolerar un salto de linea).
det=""
tope() { grep -oE "$1=[0-9]+" "$es" | head -1 | cut -d= -f2; }
tc=$(tope tope_cola); tt=$(tope tope_total); tp=$(tope tope_propuesto); td=$(tope tope_disenado)
if [ -z "$tc" ] || [ -z "$tt" ] || [ -z "$tp" ] || [ -z "$td" ]; then det=" estado.sh sin los cuatro topes"
else
    texto=$(tr '\n' ' ' < "$sk" | tr -s ' ')
    for t in "COLA (tope $tc)" "TOTAL (tope $tt)" "COLA >= $tc" "TOTAL >= $tt" "$tp fichas en \`propuesto\`" "$td en \`disenado\`" "COLA=<n>/$tc TOTAL=<n>/$tt"; do
        echo "$texto" | grep -qF -- "$t" || det="$det SKILL.md sin '$t';"
    done
    pl=$(tr '\n' ' ' < "$bl/ESTADO.plantilla.md" 2>/dev/null | tr -s ' ')
    echo "$pl" | grep -qF -- "COLA=<n>/$tc TOTAL=<n>/$tt" || det="$det ESTADO.plantilla.md sin 'COLA=<n>/$tc TOTAL=<n>/$tt';"
fi
# El largo del turno tambien vive en los dos lados.
mt=$(grep -oE 'minutos_turno=[0-9]+' "$tu" 2>/dev/null | head -1 | cut -d= -f2)
if [ -z "$mt" ]; then det="$det turno.sh sin minutos_turno;"
else echo "$texto" | grep -qF -- "$mt minutos" || det="$det SKILL.md sin '$mt minutos'"
fi
cierra topes "$det"

# 6. plantilla: la cabecera que estado.sh y los roles leen con grep.
det=""
for k in estado candado rama tipo epica turnos; do grep -q "^$k:" "$bl/PLANTILLA.md" 2>/dev/null || det="$det $k:"; done
cierra plantilla "$det"

# 7. roles: siete en el case de turno.sh y siete especificaciones en el playbook.
det=""
nc=$(grep -oE '^[[:space:]]*release\|[a-z|]+\)' "$tu" 2>/dev/null | head -1 | tr -d ' )' | tr '|' '\n' | grep -c .)
nh=$(sed -n '/^## Especificacion por rol/,/^## Cierre comun/p' "$sk" 2>/dev/null | grep -c '^### ')
[ "$nc" -eq 7 ] && [ "$nh" -eq 7 ] || det=" case de turno.sh: $nc nombres; SKILL.md: $nh encabezados ### (esperados 7 y 7)"
cierra roles "$det"

# 8. podridos: hechos que ya no son ciertos y que el playbook no puede nombrar.
det=""
for t in 'ci.yml' 'hoy:' '90 minutos' '#11' 'great-'"cray"; do grep -qF -- "$t" "$sk" 2>/dev/null && det="$det '$t'"; done
cierra podridos "$det"

# 8b. opencode: el comando de OpenCode pasa la rutina de origin/main (no una copia que
# se aleje) y el autor que fija opencode.sh es uno que estado.sh cuenta como del equipo:
# con otro, cada commit del turno seria un pedido del humano.
det=""
oc=$base/.opencode/commands/equipo-dev.md
if [ ! -f "$oc" ]; then det=" falta .opencode/commands/equipo-dev.md"
else
    grep -qF 'git show origin/main:.claude/skills/equipo-dev/rutina.md' "$oc" || det="$det el comando no pasa la rutina de origin/main;"
    grep -qF '$ARGUMENTS' "$oc" || det="$det el comando no pasa el mensaje del disparo (rol:);"
fi
autor=$(grep -oE 'GIT_AUTHOR_NAME=[A-Za-z]+' "$base/scripts/equipo-dev/opencode.sh" 2>/dev/null | head -1 | cut -d= -f2)
if [ -z "$autor" ]; then det="$det opencode.sh no fija el autor;"
else
    c=$(grep -cF "grep -vE '^(Claude|$autor)'" "$es")
    [ "$c" -eq 2 ] || det="$det estado.sh cuenta a '$autor' como del equipo en $c de 2 lugares;"
fi
cierra opencode "$det"

# 9. simular: la regla del rol, caso por caso, comparando la linea entera.
# Un caso es "rol|argumentos|salida esperada"; el rol va vacio salvo que se pida.
# Los casos con dos contadores activos fijan el orden de las reglas: invertir
# dos adyacentes tiene que caer aca. GIT_DIR apunta a un directorio que no
# existe para que un turno.sh viejo (sin --simular) no escriba .git/equipo-dev.env.
casos=(
'|aprobado=1 hora=0905|rol=release motivo=por estado: 1 aprobado reloj=dev franja=3'
'|entregado=1 hora=1801|rol=release motivo=por estado: 1 entregado reloj=qa franja=6'
'|aprobado=1 sin_merge=si hora=0905|rol=release motivo=por estado: 1 aprobado reloj=dev franja=3'
'|revisado=1 hora=0301|rol=qa motivo=por estado: 1 revisado reloj=po franja=1'
'|implementado=1 hora=0301|rol=revisor motivo=por estado: 1 implementado reloj=po franja=1'
'|con_hallazgos=1 hora=1801|rol=dev motivo=por estado: 1 con_hallazgos, 0 huerfanas reloj=qa franja=6'
'|huerfanas=1 hora=0001|rol=dev motivo=por estado: 0 con_hallazgos, 1 huerfanas reloj=release franja=0'
'|hora=0301|rol=po motivo=papel vacio reloj=po franja=1'
'|propuesto=2 hora=1201|rol=arquitecto motivo=por estado: 2 propuesto, 0 disenado de 3 reloj=revisor franja=4'
'|disenado=1 cola=1 total=1 hora=1801|rol=dev motivo=por estado: 1 disenado, lugar en cola reloj=qa franja=6'
'|disenado=1 propuesto=1 cola=4 total=4 hora=1801|rol=arquitecto motivo=por estado: 1 propuesto, 1 disenado de 3 reloj=qa franja=6'
'|disenado=1 cola=4 total=4 hora=1801|rol=po motivo=papel corto: 0 propuesto de 6 reloj=qa franja=6'
'|propuesto=6 disenado=3 cola=4 total=4 ideas_libres=23 hora=2101 fecha=2026-10-12|rol=investigador motivo=reloj: investigador reloj=investigador franja=7'
'|propuesto=6 disenado=3 cola=4 total=4 ideas_libres=23 hora=2101 fecha=2026-10-13|rol=revisor motivo=nada tomable: reloj reloj=revisor franja=7'
'|propuesto=6 disenado=3 cola=4 total=4 ideas_libres=5 hora=1201|rol=investigador motivo=ideas libres: 5 de 10 reloj=revisor franja=4'
'|implementado=1 hora=2101 fecha=2026-10-12|rol=revisor motivo=por estado: 1 implementado reloj=investigador franja=7'
'|hora=0229|rol=po motivo=papel vacio reloj=po franja=1'
'qa|aprobado=1 hora=0905|rol=qa motivo=pedido reloj=dev franja=3'
'|aprobado=1 entregado=1 hora=0905|rol=release motivo=por estado: 1 aprobado reloj=dev franja=3'
'|revisado=1 implementado=1 hora=0301|rol=qa motivo=por estado: 1 revisado reloj=po franja=1'
'|entregado=1 revisado=1 hora=0301|rol=release motivo=por estado: 1 entregado reloj=po franja=1'
'|implementado=1 con_hallazgos=1 hora=0301|rol=revisor motivo=por estado: 1 implementado reloj=po franja=1'
'|con_hallazgos=1 hora=2101 fecha=2026-10-12|rol=dev motivo=por estado: 1 con_hallazgos, 0 huerfanas reloj=investigador franja=7'
'|hora=2101 fecha=2026-10-12|rol=investigador motivo=reloj: investigador reloj=investigador franja=7'
'|disenado=1 propuesto=1 cola=1 total=1 hora=1801|rol=dev motivo=por estado: 1 disenado, lugar en cola reloj=qa franja=6'
'|espera_humano=1 propuesto=2 hora=0001|rol=release motivo=reloj: release, 1 en espera reloj=release franja=0'
'|espera_humano=1 propuesto=2 hora=0301|rol=arquitecto motivo=por estado: 2 propuesto, 0 disenado de 3 reloj=po franja=1'
'|aprobado=1 espera_humano=1 hora=0001|rol=release motivo=por estado: 1 aprobado reloj=release franja=0'
'|con_hallazgos=1 espera_humano=1 hora=0001|rol=dev motivo=por estado: 1 con_hallazgos, 0 huerfanas reloj=release franja=0'
)
malos=0
for c in "${casos[@]}"; do
    r=${c%%|*}; resto=${c#*|}; a=${resto%%|*}; e=${resto#*|}
    if [ -n "$r" ]; then s=$(GIT_DIR="$base/.nogit" bash "$tu" "$r" --simular "$a" 2>&1); else s=$(GIT_DIR="$base/.nogit" bash "$tu" --simular "$a" 2>&1); fi
    [ "$s" = "$e" ] || { malos=$((malos + 1)); echo "FALLA simular: ${r:+$r }$a -> $s (esperado $e)"; }
done
GIT_DIR="$base/.nogit" bash "$tu" foo --simular "hora=0905" >/dev/null 2>&1; codigo=$?
[ "$codigo" -eq 1 ] || { malos=$((malos + 1)); echo "FALLA simular: foo --simular hora=0905 -> salida $codigo (esperado 1)"; }
det=""; [ "$malos" -eq 0 ] || det=" $malos de $(( ${#casos[@]} + 1 )) casos"
cierra simular "$det"

# 10. resumen: contra el remoto real, la linea existe y trae los 20 pares en
# orden; los valores no se afirman porque cambian con cada turno. Lo unico
# estable: la rama del playbook no aparece como rama de trabajo.
if [ "${PRUEBAS_SIN_RED:-}" = 1 ]; then
    ok "resumen (saltada: PRUEBAS_SIN_RED=1)"
else
    det=""
    salida=$(bash "$es" --resumen 2>/dev/null)
    lineas=$(printf '%s\n' "$salida" | grep -c .)
    claves=$(printf '%s\n' "$salida" | grep -m1 '^RESUMEN ' | sed 's/^RESUMEN //' | tr ' ' '\n' | grep -E '^[a-z_0-9]+=[^ ]+$' | cut -d= -f1 | tr '\n' ' ')
    esperadas='propuesto disenado en_curso huerfanas implementado revisado con_hallazgos aprobado entregado espera_humano cola total tope_cola tope_total tope_propuesto tope_disenado ideas_libres sin_merge pausa sin_rastro_48h '
    [ "$lineas" -eq 1 ] || det="$det $lineas lineas en vez de 1;"
    [ "$claves" = "$esperadas" ] || det="$det pares: '${claves:-ninguno}';"
    filas=$(bash "$es" 2>/dev/null | grep -c 'equipo-dev/playbook |')
    [ "$filas" -eq 0 ] || det="$det la rama del playbook aparece $filas veces como rama de trabajo"
    cierra resumen "$det"
fi

if [ "$fallos" -gt 0 ]; then echo "PRUEBAS_FALLAN: $fallos"; exit 1; fi
echo "PRUEBAS_OK ($n)"
