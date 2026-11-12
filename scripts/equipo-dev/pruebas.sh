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
ve=$base/scripts/equipo-dev/verificar.sh
in=$base/scripts/equipo-dev/independencia.sh
al=$base/.claude/skills/equipo-dev/alcance.md
ro=$base/.claude/skills/equipo-dev/roles
bl=$base/docs/backlog
# El playbook entero: nucleo, Directiva de alcance y un archivo por rol.
playbook=("$sk" "$al")
for f in "$ro"/*.md; do [ -f "$f" ] && playbook+=("$f"); done

n=0; fallos=0
ok() { n=$((n + 1)); echo "OK $1"; }
falla() { n=$((n + 1)); fallos=$((fallos + 1)); echo "FALLA $1:$2"; }
cierra() { if [ -z "$2" ]; then ok "$1"; else falla "$1" "$2"; fi; }

# 1. sintaxis
det=""
for s in scripts/equipo-dev/turno.sh scripts/equipo-dev/estado.sh scripts/equipo-dev/pruebas.sh scripts/equipo-dev/opencode.sh scripts/equipo-dev/verificar.sh scripts/equipo-dev/independencia.sh scripts/check.sh .claude/hooks/session-start.sh; do
    if [ ! -f "$base/$s" ]; then det="$det falta $s"
    elif ! bash -n "$base/$s" 2>/dev/null; then det="$det bash -n $s"
    fi
done
cierra sintaxis "$det"

# 2. cadena: la misma secuencia de refs en los cuatro lugares, dev primero,
# probando rutina.md (solo el playbook nuevo lo tiene), y ninguna ref vieja en
# ningun lado. El patron de las viejas se arma partido para que este archivo no lo
# contenga.
det=""
cadena='origin/dev origin/main origin/claude/equipo-dev/playbook'
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
    for t in 'turno.sh' 'estado.sh' 'rol:' 'SKILL.md' 'SIN_PLAYBOOK' '+refs/heads/claude/*' '# leer:' 'verificar.sh' 'timeout: 600000'; do
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
done <<< "$(cat "${playbook[@]}" "$ru" "$bl/README.md" 2>/dev/null | grep -oE '`(\.claude|scripts|docs/backlog)/[^`]*`' | tr -d '`' | sort -u)"
# Las rutas relativas a la skill (`roles/qa.md`, `alcance.md`) tambien.
while IFS= read -r p; do
    [ -n "$p" ] || continue
    case "$p" in *'<'*) continue ;; esac
    [ -e "$base/.claude/skills/equipo-dev/$p" ] || det="$det .claude/skills/equipo-dev/$p"
done <<< "$(cat "${playbook[@]}" "$ru" 2>/dev/null | grep -oE '`(roles/[a-z<>]+\.md|alcance\.md|skills-del-repo\.md)`' | tr -d '`' | sort -u)"
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
# Y los roles que una sesion puede encadenar (--seguir): turno.sh, el playbook
# y el README del humano, que es donde se le dice como bajarlo.
rs=$(grep -oE '^tope_roles=[0-9]+' "$tu" 2>/dev/null | head -1 | cut -d= -f2)
if [ -z "$rs" ]; then det="$det turno.sh sin tope_roles;"
else
    tr '\n' ' ' < "$sk" | tr -s ' ' | grep -qF -- "hasta $rs roles por sesion" || det="$det SKILL.md sin 'hasta $rs roles por sesion';"
    tr '\n' ' ' < "$bl/README.md" | tr -s ' ' | grep -qF -- "hasta $rs roles" || det="$det README.md sin 'hasta $rs roles';"
fi
cierra topes "$det"

# 6. plantilla: la cabecera que estado.sh y los roles leen con grep.
det=""
for k in estado candado rama tipo epica turnos; do grep -q "^$k:" "$bl/PLANTILLA.md" 2>/dev/null || det="$det $k:"; done
cierra plantilla "$det"

# 7. roles: los siete nombres del case de turno.sh son exactamente los siete
# archivos de roles/ (turno.sh imprime `roles/<rol>.md` y un nombre sin
# archivo dejaria al turno sin especificacion) y la tabla de Roles los nombra.
det=""
nombres=$(grep -oE '^[[:space:]]*release\|[a-z|]+\)' "$tu" 2>/dev/null | head -1 | tr -d ' )' | tr '|' '\n' | sort)
archivos=$(ls "$ro" 2>/dev/null | grep '\.md$' | sed 's/\.md$//' | sort)
[ "$(printf '%s\n' "$nombres" | grep -c .)" -eq 7 ] || det="$det case de turno.sh con $(printf '%s\n' "$nombres" | grep -c .) nombres;"
[ "$nombres" = "$archivos" ] || det="$det case de turno.sh ($(echo $nombres)) distinto de roles/ ($(echo $archivos));"
for r in $nombres; do grep -qF "\`roles/$r.md\`" "$sk" || det="$det SKILL.md no nombra roles/$r.md;"; done
cierra roles "$det"

# 8. podridos: hechos que ya no son ciertos y que el playbook no puede nombrar.
det=""
for t in 'ci.yml' 'hoy:' '90 minutos' '#11' 'great-'"cray" 'titulo del PR como mensaje' 'Corre cada 3 horas' 'trig_'; do
    for f in "${playbook[@]}"; do grep -qF -- "$t" "$f" 2>/dev/null && det="$det '$t' en ${f#$base/}"; done
done
cierra podridos "$det"

# 8b. opencode: el comando de OpenCode pasa la rutina de origin/dev (no una copia que
# se aleje) y el autor que fija opencode.sh es uno que estado.sh cuenta como del equipo:
# con otro, cada commit del turno seria un pedido del humano.
det=""
oc=$base/.opencode/commands/equipo-dev.md
if [ ! -f "$oc" ]; then det=" falta .opencode/commands/equipo-dev.md"
else
    grep -qF 'git show origin/dev:.claude/skills/equipo-dev/rutina.md' "$oc" || det="$det el comando no pasa la rutina de origin/dev;"
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
'|disenado=2 propuesto=1 cola=1 total=1 bloqueadas=1 hora=0331|rol=dev motivo=por estado: 2 disenado, lugar en cola; 1 bloqueadas por independencia reloj=po franja=1'
'revisor|bloqueadas=1 hora=0331|rol=revisor motivo=pedido reloj=po franja=1'
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

# 9b. seguir: la sesion encadena roles con `turno.sh --seguir`. La misma regla
# de arriba, sin el reloj y sin lo que la sesion no debe tomar; un caso es
# "pares|salida esperada" (`hechos=` son los roles ya liderados, `restante=`
# los minutos que quedan; sin `restante`, el turno entero). Cada veto tiene su
# caso: quitarlo de seguir_rol tiene que caer aca.
casos_s=(
'hechos=release aprobado=1 entregado=1 revisado=1|sigue=qa motivo=sigue: por estado: 1 revisado'
'hechos=qa revisado=1 con_hallazgos=1 huerfanas=1 implementado=1|sigue=revisor motivo=sigue: por estado: 1 implementado'
'hechos=qa aprobado=1|sigue=release motivo=sigue: por estado: 1 aprobado'
'hechos=revisor implementado=1 con_hallazgos=1 disenado=1 cola=1 total=1|sigue=dev motivo=sigue: por estado: 1 disenado, lugar en cola'
'hechos=revisor con_hallazgos=1 huerfanas=1 propuesto=2|sigue=arquitecto motivo=sigue: por estado: 2 propuesto, 0 disenado de 3'
'hechos=qa con_hallazgos=1 propuesto=6 disenado=3 cola=4 total=4 ideas_libres=50|fin=nada mas que tomar por estado'
'hechos=dev con_hallazgos=1 huerfanas=1 disenado=2 propuesto=1 cola=1 total=1|sigue=arquitecto motivo=sigue: por estado: 1 propuesto, 2 disenado de 3'
'hechos=dev implementado=1 bloqueadas=1|sigue=revisor motivo=sigue: por estado: 1 implementado; 1 bloqueadas por independencia'
'hechos=dev,arquitecto disenado=2 propuesto=1 cola=1 total=1|sigue=po motivo=sigue: papel corto: 1 propuesto de 6'
'hechos=arquitecto disenado=1 cola=1 total=1 ideas_libres=50|sigue=po motivo=sigue: papel corto: 0 propuesto de 6'
'hechos=arquitecto disenado=1 con_hallazgos=1 cola=1 total=1|sigue=dev motivo=sigue: por estado: 1 con_hallazgos, 0 huerfanas'
'hechos=po propuesto=3 ideas_libres=50|fin=nada mas que tomar por estado'
'hechos=po propuesto=3 disenado=1 cola=1 total=1|sigue=dev motivo=sigue: por estado: 1 disenado, lugar en cola'
'hechos=dev,arquitecto,po disenado=2 propuesto=1 cola=1 total=1 ideas_libres=50|fin=nada mas que tomar por estado'
'hechos=po ideas_libres=50|fin=lo que sigue es po, que esta sesion ya lidero'
'hechos=arquitecto ideas_libres=50|sigue=po motivo=sigue: papel vacio'
'hechos=qa,revisor,dev,arquitecto propuesto=1 ideas_libres=50|fin=tope de 4 roles por sesion'
'hechos=dev propuesto=6 disenado=3 cola=4 total=4 ideas_libres=50 espera_humano=1 hora=0001|fin=nada mas que tomar por estado'
'hechos=dev propuesto=6 disenado=3 cola=4 total=4 ideas_libres=50 hora=2101 fecha=2026-10-12|fin=nada mas que tomar por estado'
'hechos=dev propuesto=6 disenado=3 cola=4 total=4 ideas_libres=5|sigue=investigador motivo=sigue: ideas libres: 5 de 10'
'hechos=dev,investigador propuesto=6 disenado=3 cola=4 total=4 ideas_libres=5|fin=nada mas que tomar por estado'
'hechos=revisor disenado=1 cola=1 total=1 restante=45|sigue=dev motivo=sigue: por estado: 1 disenado, lugar en cola'
'hechos=revisor disenado=1 cola=1 total=1 restante=44|fin=quedan 44 min y dev pide 45'
'hechos=dev aprobado=1 restante=19|fin=quedan 19 min y release pide 20'
'hechos=qa aprobado=1 pausa=si|fin=PAUSA'
'hechos=dev implementado=1 pedido_antes=si|fin=el rol vino pedido a mano: no encadena'
)
malos=0
for c in "${casos_s[@]}"; do
    a=${c%%|*}; e=${c#*|}
    s=$(GIT_DIR="$base/.nogit" bash "$tu" --seguir --simular "$a" 2>&1)
    [ "$s" = "$e" ] || { malos=$((malos + 1)); echo "FALLA seguir: $a -> $s (esperado $e)"; }
done
GIT_DIR="$base/.nogit" bash "$tu" --seguir dev --simular "hechos=qa" >/dev/null 2>&1; codigo=$?
[ "$codigo" -eq 1 ] || { malos=$((malos + 1)); echo "FALLA seguir: --seguir dev -> salida $codigo (esperado 1: --seguir no lleva rol)"; }
det=""; [ "$malos" -eq 0 ] || det=" $malos de $(( ${#casos_s[@]} + 1 )) casos;"
# El playbook, la rutina y la plantilla dicen como se encadena y como se cierra.
for t in 'bash -s -- --seguir' '# turno: sigue como' '# fin:' 'DESTRABA' 'FRENADAS'; do
    grep -qF -- "$t" "$sk" || det="$det SKILL.md sin '$t';"
done
grep -qF -- '--seguir' "$ru" 2>/dev/null || det="$det rutina.md no nombra --seguir;"
grep -qF -- 'bash -s -- --seguir' "$tu" || det="$det turno.sh no anuncia --seguir al terminar;"
tr '\n' ' ' < "$ro/dev.md" | tr -s ' ' | grep -qF -- '--puedo dev' || det="$det roles/dev.md no pide --puedo dev (quien reviso no arregla);"
for t in DESTRABA FRENADAS; do grep -qF "$t" "$bl/ESTADO.plantilla.md" 2>/dev/null || det="$det ESTADO.plantilla.md sin $t;"; done
cierra seguir "$det"

# 9c. dependencia: la frase con que el playbook manda escribir "esta ficha va
# despues de aquella" es una que estado.sh sabe leer. Si alguien la redacta de
# otro modo en un rol o en la plantilla, las FRENADAS vuelven a contarse como
# tomables sin que nada falle.
det=""
frases=$(cat "$bl/PLANTILLA.md" "$al" "$ro"/*.md 2>/dev/null | tr '\n' ' ' | tr -s ' ' | grep -oiE 'implementar despues de[^"`.;:)]*#NN')
nf=$(printf '%s\n' "$frases" | grep -c .)
[ "$nf" -ge 4 ] || det="$det solo $nf frases 'Implementar despues de ... #NN' en la plantilla y los roles (se esperaban 4 o mas);"
while IFS= read -r fr; do
    [ -n "$fr" ] || continue
    r=$(bash "$es" --espera "${fr//NN/79}" 2>&1)
    [ "$r" = 79 ] || det="$det estado.sh --espera no lee '$fr' (dio '$r');"
done <<< "$frases"
# Con tilde tambien (la e acentuada va por printf: este archivo es ASCII).
for c in "$(printf 'Implementar despu\303\251s de que la 78 y la #79 se mergeen: usa la columna 0006|78 79')" 'implementar despues de la ficha 101, la 102 o #103. Despues, 5 tests|101 102 103' 'La 79 ya esta en dev; despues de implementar la 80, nada|'; do
    r=$(bash "$es" --espera "${c%%|*}" 2>&1)
    [ "$r" = "${c#*|}" ] || det="$det --espera '${c%%|*}' -> '$r' (esperado '${c#*|}');"
done
cierra dependencia "$det"

# 9d. vacio: los turnos que no dejaron otro commit que ESTADO.md. Primero la
# cuenta sola (rastros R y actividad A sinteticos, como en rastros), despues
# estado.sh entero contra un remoto con commits fechados: lo que firma el
# humano no es entrega del equipo, lo de una rama de trabajo si, y con un
# tercio o mas de los turnos de 48 h en vacio sale como DESTRABA.
det=""
v0=1790812800; vh=3600
vcasos=(
"uno en vacio entre dos con entrega|$((v0 + 9 * vh))|A:$((v0 - 600)) R:$v0 R:$((v0 + 4 * vh)) A:$((v0 + 8 * vh - 120)) R:$((v0 + 8 * vh))|1 3 1 3"
"dos rastros a 10 min son una sesion|$((v0 + vh))|R:$v0 A:$((v0 + 300)) R:$((v0 + 600))|0 1 0 1"
"a un disparo por hora, lo que sigue al cierre es de esa sesion y no de la siguiente|$((v0 + 2 * vh))|A:$((v0 - 60)) R:$v0 A:$((v0 + 200)) R:$((v0 + vh))|1 2 1 2"
"una sesion larga: entrega 130 min antes de su rastro|$((v0 + 5 * vh))|A:$((v0 - 60)) R:$v0 A:$((v0 + 4 * vh - 7800)) R:$((v0 + 4 * vh))|0 2 0 2"
"actividad de hace 3 horas no es de este turno|$((v0 + 5 * vh))|A:$((v0 + vh - 10800)) R:$((v0 + vh))|1 1 1 1"
"un turno de hace 3 dias cuenta en 7 dias y no en 48 h|$((v0 + vh))|R:$((v0 - 72 * vh)) A:$((v0 - 60)) R:$v0|0 1 1 2"
"sin rastros|$v0||0 0 0 0"
)
for c in "${vcasos[@]}"; do
    nombre=${c%%|*}; resto=${c#*|}; ahora=${resto%%|*}; resto=${resto#*|}; eps=${resto%%|*}; e=${resto#*|}
    r=$(EQUIPO_AHORA=$ahora bash "$es" --vacio "$eps" 2>&1)
    [ "$r" = "$e" ] || det="$det --vacio '$nombre' -> '$r' (esperado '$e');"
done
tz=$(mktemp -d)
(
    export GIT_CONFIG_GLOBAL=/dev/null GIT_CONFIG_NOSYSTEM=1
    export GIT_AUTHOR_NAME=Claude GIT_COMMITTER_NAME=Claude GIT_AUTHOR_EMAIL=c@c GIT_COMMITTER_EMAIL=c@c
    unset EQUIPO_CONTEXTO EQUIPO_REF EQUIPO_AHORA EQUIPO_INDEPENDENCIA
    cd "$tz" && git init -q --bare origen.git && git clone -q origen.git w 2>/dev/null && cd w || exit 9
    ya=$(date -u +%s)
    # Commit fechado hace N horas (y M segundos mas).
    hace() { local t=$(( ya - $1 * 3600 - ${3:-0} )); git add -A && GIT_AUTHOR_DATE="$t +0000" GIT_COMMITTER_DATE="$t +0000" git commit -qm "$2"; }
    mkdir -p .claude/skills/equipo-dev docs/backlog && echo x > .claude/skills/equipo-dev/rutina.md
    hace 40 base && git push -q origin HEAD:dev HEAD:main || exit 9
    git fetch -q origin && git checkout -q -B papel origin/dev && mkdir -p docs/backlog
    echo 'estado: propuesto' > docs/backlog/90-a.md && hace 20 'Propone: 90' 300
    for n in 20 16 12 8; do echo "turno de hace $n h" > docs/backlog/ESTADO.md && hace $n "Estado: hace $n h"; done
    git push -q origin HEAD:refs/heads/claude/equipo-dev/backlog || exit 9
    v() { bash "$es" 2>/dev/null | grep -E '^TURNOS_EN_VACIO=|^DESTRABA: el equipo gira en vacio' | sed 's/ (turnos que.*//; s/ no dejaron.*//' | tr '\n' ';'; }
    s=$(v); e='TURNOS_EN_VACIO=3 de 4 en 48 h | 3 de 4 en 7 dias;DESTRABA: el equipo gira en vacio: 3 de los 4 turnos de las ultimas 48 h;'
    [ "$s" = "$e" ] || echo "tres turnos con solo ESTADO.md: '$s' (esperado '$e')"
    # El humano commitea en la ventana del turno de hace 12 h: no es entrega.
    git checkout -q -B t91 origin/dev && mkdir -p docs/backlog && echo x > docs/backlog/91-b.md
    GIT_AUTHOR_NAME=Humano hace 12 'pedido del humano' 600 && git push -q origin HEAD:refs/heads/claude/equipo-dev/91-b || exit 9
    s=$(v); [ "$s" = "$e" ] || echo "un commit del humano conto como entrega: '$s'"
    # El equipo commitea en esa rama en los turnos de hace 12 y 8 h: queda 1 de 4.
    echo y >> docs/backlog/91-b.md && hace 12 'Agrega algo' 300
    echo z >> docs/backlog/91-b.md && hace 8 'Agrega mas' 300
    git push -q origin HEAD:refs/heads/claude/equipo-dev/91-b || exit 9
    s=$(v); [ "$s" = 'TURNOS_EN_VACIO=1 de 4 en 48 h | 1 de 4 en 7 dias;' ] || echo "con entregas en la rama de trabajo: '$s' (esperado 1 de 4, sin DESTRABA)"
) > "$tz/fallos" 2>&1
[ -s "$tz/fallos" ] && det="$det $(tr '\n' ';' < "$tz/fallos")"
rm -rf "$tz"
grep -qF 'TURNOS_EN_VACIO' "$bl/ESTADO.plantilla.md" 2>/dev/null || det="$det ESTADO.plantilla.md sin TURNOS_EN_VACIO;"
cierra vacio "$det"

# 9e. encadenar: turno.sh y estado.sh enteros sobre un remoto sintetico, con
# el papel como estaba el 2026-11-10: una `disenado` (83) que espera a la 79,
# la 79 `entregado (...)` esperando al humano y una `propuesto` con candado.
# Antes el rol era dev ("1 disenado, lugar en cola") y no habia nada que
# implementar. Despues, --seguir de verdad: el env de la sesion, los roles ya
# liderados, el reloj, PAUSA y quien reviso no arregla.
det=""
te=$(mktemp -d)
(
    export GIT_CONFIG_GLOBAL=/dev/null GIT_CONFIG_NOSYSTEM=1
    export GIT_AUTHOR_NAME=Claude GIT_COMMITTER_NAME=Claude GIT_AUTHOR_EMAIL=c@c GIT_COMMITTER_EMAIL=c@c
    unset EQUIPO_CONTEXTO EQUIPO_REF EQUIPO_AHORA EQUIPO_INDEPENDENCIA
    cd "$te" && git init -q --bare origen.git && git clone -q origen.git w 2>/dev/null && cd w || exit 9
    mkdir -p .claude/skills/equipo-dev scripts/equipo-dev docs/backlog && echo x > .claude/skills/equipo-dev/rutina.md
    cp "$tu" "$es" "$in" scripts/equipo-dev/ || exit 9
    git add -A && git commit -qm base && git push -q origin HEAD:dev HEAD:main || exit 9
    git fetch -q origin
    sube() { git add -A && git commit -qm "$1" && git push -q origin "HEAD:refs/heads/$2" && git checkout -q --detach origin/dev; }
    # Un directorio vacio no se commitea: dev no trae docs/backlog.
    rama() { git checkout -q -B "$1" "$2" && mkdir -p docs/backlog; }
    rama papel origin/dev
    printf 'estado: disenado\ncandado: -\ntipo: funcionalidad\nturnos: arquitecto 20261101T0000Z-cARQ001\n\n**Implementar despues de que #79 se mergee**: usa su columna.\n' > docs/backlog/83-tramo-dos.md
    printf 'estado: propuesto\ncandado: arquitecto 2026-11-06T06:49Z\ntipo: funcionalidad\nturnos: po 20261101T0000Z-cPO0001\n' > docs/backlog/102-pool.md
    # Con ideas libres de sobra: sin ellas el estado pediria un investigador.
    for i in 1 2 3 4 5 6 7 8 9 10 11 12; do echo "| I$i | una idea | idea |"; done > docs/backlog/ALCANCE.md
    sube papel claude/equipo-dev/backlog || exit 9
    rama t79 origin/dev
    printf 'estado: entregado (PR pendiente de merge: toca CLAUDE.md, lo mergea el humano)\ncandado: -\ntipo: funcionalidad\nturnos: dev 20261101T0100Z-cDEV001, revisor 20261101T0200Z-cREV001, qa 20261101T0300Z-cQA0001\n' > docs/backlog/79-tramo-uno.md
    sube 'Reclama: 79' claude/equipo-dev/79-tramo-uno || exit 9

    e() { bash "$es" "$@" 2>/dev/null; }
    pares() { tr ' ' '\n' | grep -E "^($1)=" | tr '\n' ' '; }
    s=$(e --resumen | pares 'propuesto|disenado|espera_humano')
    [ "$s" = 'propuesto=1 disenado=0 espera_humano=1 ' ] || echo "RESUMEN con una frenada: '$s' (esperado 'propuesto=1 disenado=0 espera_humano=1 ')"
    completa=$(e)
    grep -qF 'FRENADAS=1 (la 83 espera a la 79)' <<< "$completa" || echo "sin 'FRENADAS=1 (la 83 espera a la 79)': $(grep -m1 '^FRENADAS' <<< "$completa")"
    grep -F '83-tramo-dos.md' <<< "$completa" | grep -qF 'frenada: espera a la 79' || echo "la linea de la 83 en el papel no dice que esta frenada"
    grep -E '^DESTRABA: ficha 79, entregado \(PR pendiente de merge: toca CLAUDE.md' <<< "$completa" | grep -qF '| frena a: 83 |' || echo "sin la linea DESTRABA de la 79 con 'frena a: 83': $(grep -m1 '^DESTRABA' <<< "$completa")"
    grep -F '102-pool.md' <<< "$completa" | grep -qF 'candado muerto' && echo "un candado recien puesto en el papel sale como muerto"
    EQUIPO_AHORA=$(( $(date -u +%s) + 14400 )) bash "$es" 2>/dev/null | grep -F '102-pool.md' | grep -qF 'candado muerto: si' || echo "un candado de 4 h en el papel no sale como muerto"

    # El reloj fijo a las 09:05 UTC de hoy (franja 3): a las 23 el reloj
    # elegiria release (la 79 espera al humano) y a las 21 de un dia par,
    # investigador, antes de mirar el papel, y la prueba dependeria de la hora.
    fijo=$(date -u -d "$(date -u +%F) 09:05" +%s)
    t() { EQUIPO_AHORA=$fijo bash "$tu" "$@" 2>&1; }
    env_f="$(git rev-parse --absolute-git-dir)/equipo-dev.env"
    campo_env() { sed -n "s/^export $1=//p" "$env_f"; }
    t --seguir >/dev/null; c=$?; [ "$c" = 1 ] || echo "--seguir sin turno en curso: salida $c (esperada 1)"
    s=$(t --contexto cSES001)
    grep -q '^# turno: arquitecto | motivo: por estado: 1 propuesto, 0 disenado de 3 ' <<< "$s" || echo "primer rol con la 83 frenada: $(grep -m1 '^# turno' <<< "$s") (esperado arquitecto)"
    grep -qF 'bash -s -- --seguir' <<< "$s" || echo "el arranque no anuncia --seguir"
    [ "$(campo_env EQUIPO_ROLES)" = '"arquitecto"' ] || echo "EQUIPO_ROLES tras el arranque: $(campo_env EQUIPO_ROLES)"
    sesion=$(campo_env EQUIPO_SESION); inicio=$(campo_env EQUIPO_INICIO)
    s=$(t --seguir)
    grep -q '^# turno: sigue como po | motivo: sigue: papel corto: 1 propuesto de 6 | roles de esta sesion: arquitecto po ' <<< "$s" || echo "primer --seguir: $(grep -m1 '^# ' <<< "$s") (esperado sigue como po)"
    [ "$(campo_env EQUIPO_ROL)" = po ] && [ "$(campo_env EQUIPO_ROLES)" = '"arquitecto po"' ] || echo "env tras seguir: rol $(campo_env EQUIPO_ROL), roles $(campo_env EQUIPO_ROLES)"
    [ "$(campo_env EQUIPO_SESION)" = "$sesion" ] && [ "$(campo_env EQUIPO_INICIO)" = "$inicio" ] || echo "--seguir cambio la sesion o el inicio del turno"
    grep -qF 'roles/po.md' <<< "$s" || echo "--seguir no manda a leer roles/po.md"
    grep -qE 'SKILL\.md|alcance\.md' <<< "$s" && echo "--seguir manda a releer SKILL.md o alcance.md"
    # Al seguir se lee el estado recortado: el comando impreso, tal cual, trae
    # lo que el rol necesita y deja afuera lo que ya se leyo al arrancar. Si
    # estado.sh renombra una seccion, el recorte cae aca y no en un turno.
    leer=$(grep -m1 '^# leer: .*estado\.sh' <<< "$s" | sed 's/^# leer: //')
    r=$(bash -c "$leer" 2>/dev/null)
    for k in '^docs/backlog/83-tramo-dos.md ' '^FRENADAS=' '^origin/claude/equipo-dev/79-tramo-uno ' '^DESTRABA: ' '^COLA=' '^RESUMEN '; do
        grep -q -- "$k" <<< "$r" || echo "el estado recortado de --seguir no trae $k"
    done
    grep -qE '^(BORRABLES|RELEASE|CADENCIA|PAPEL_TIPOS)=|^ENTORNO|^completo' <<< "$r" && echo "el estado recortado de --seguir trae secciones de mas: $(grep -oE '^(BORRABLES|RELEASE|CADENCIA|PAPEL_TIPOS)=|^ENTORNO|^completo' <<< "$r" | tr '\n' ' ')"
    s=$(t --seguir)
    grep -q '^# fin: nada mas que tomar por estado | roles de esta sesion: arquitecto po ' <<< "$s" || echo "segundo --seguir: $(head -1 <<< "$s") (esperado fin)"
    [ "$(printf '%s\n' "$s" | grep -c .)" -eq 1 ] || echo "el fin imprime mas de una linea"
    [ "$(campo_env EQUIPO_ROLES)" = '"arquitecto po"' ] || echo "un fin cambio el env"

    # Una implementado de otro contexto: sigue como revisor. Y una con hallazgos:
    # esta sesion ya reviso, no la arregla (sin el veto saldria dev).
    rama t106 origin/dev
    printf 'estado: implementado\ncandado: -\ntipo: bug\nturnos: dev 20261101T0100Z-cOTRO01\n' > docs/backlog/106-bug.md
    sube 'Reclama: 106' claude/equipo-dev/106-bug || exit 9
    s=$(t --seguir)
    grep -q '^# turno: sigue como revisor | motivo: sigue: por estado: 1 implementado | roles de esta sesion: arquitecto po revisor ' <<< "$s" || echo "con una implementado ajena: $(grep -m1 '^# ' <<< "$s") (esperado sigue como revisor)"
    rama t107 origin/dev
    printf 'estado: con hallazgos\ncandado: -\ntipo: bug\nturnos: dev 20261101T0100Z-cOTRO02, revisor 20261101T0500Z-cSES001\n' > docs/backlog/107-otro.md
    sube 'Reclama: 107' claude/equipo-dev/107-otro || exit 9
    git push -q origin --delete claude/equipo-dev/106-bug
    s=$(t --seguir)
    grep -q '^# fin: nada mas que tomar por estado ' <<< "$s" || echo "tras revisar, con una con hallazgos: $(head -1 <<< "$s") (esperado fin: quien reviso no arregla)"

    # El reloj: con 15 minutos no arranca un Dev. Y con PAUSA no sigue nadie.
    sed -i "s/^export EQUIPO_ROLES=.*/export EQUIPO_ROLES=\"po\"/; s/^export EQUIPO_INICIO=.*/export EQUIPO_INICIO=$(( fijo - 120 * 60 ))/; s/^export EQUIPO_MINUTOS=.*/export EQUIPO_MINUTOS=135/" "$env_f"
    s=$(t --seguir)
    grep -q '^# fin: quedan 15 min y dev pide 45 ' <<< "$s" || echo "con 15 minutos: $(head -1 <<< "$s") (esperado fin: quedan 15 min y dev pide 45)"
    sed -i "s/^export EQUIPO_INICIO=.*/export EQUIPO_INICIO=$fijo/" "$env_f"
    s=$(t --seguir)
    grep -q '^# turno: sigue como dev | motivo: sigue: por estado: 1 con_hallazgos, 0 huerfanas ' <<< "$s" || echo "con el reloj entero: $(grep -m1 '^# ' <<< "$s") (esperado sigue como dev)"
    rama papel origin/claude/equipo-dev/backlog && : > docs/backlog/PAUSA
    sube pausa claude/equipo-dev/backlog || exit 9
    sed -i 's/^export EQUIPO_ROLES=.*/export EQUIPO_ROLES="po"/' "$env_f"
    s=$(t --seguir)
    grep -q '^# fin: PAUSA ' <<< "$s" || echo "con PAUSA: $(head -1 <<< "$s") (esperado fin: PAUSA)"

    # La 79 llega a dev: la 83 deja de estar frenada y nada espera al humano.
    rama d origin/dev
    printf 'estado: entregado\ncandado: -\ntipo: funcionalidad\nturnos: dev 20261101T0100Z-cDEV001\n' > docs/backlog/79-tramo-uno.md
    git add -A && git commit -qm 'entra la 79' && git push -q origin HEAD:dev && git checkout -q --detach origin/dev || exit 9
    s=$(e --resumen | pares 'disenado|espera_humano')
    [ "$s" = 'disenado=1 espera_humano=0 ' ] || echo "con la 79 en dev: '$s' (esperado 'disenado=1 espera_humano=0 ')"
    completa=$(e)
    grep -q '^FRENADAS=0 ' <<< "$completa" || echo "con la 79 en dev sigue habiendo frenadas: $(grep -m1 '^FRENADAS' <<< "$completa")"
    grep -q '^DESTRABA' <<< "$completa" && echo "con la 79 en dev sigue saliendo DESTRABA"
    grep -qF 'nada espera al humano' <<< "$completa" || echo "sin 'nada espera al humano'"
) > "$te/fallos" 2>&1
[ -s "$te/fallos" ] && det="$det $(tr '\n' ';' < "$te/fallos")"
rm -rf "$te"
cierra encadenar "$det"

# 10. rastros: los disparos sin rastro se cuentan a la cadencia que la Routine
# tiene de verdad, no a un cron fijo. Series sinteticas (un commit de ESTADO.md
# entre 5 y 17 min despues de cada disparo) y la linea entera de estado.sh
# --rastros. Con el cron fijo de 3 h el caso de 4 h daba 2 perdidos por dia.
serie() {
    local desde=$1 paso=$2 n=$3 i; shift 3
    for ((i = 0; i < n; i++)); do
        case " $* " in *" $i "*) continue ;; esac
        echo $(( desde + i * paso + 300 + (i * 7 % 4) * 240 ))
    done
}
b0=1790812800; h=3600   # 2026-10-01T00:00Z
rcasos=(
"4 h, 8 dias|$((b0 + 240 + 48 * 4 * h + 60))|$(serie $((b0 + 240)) $((4 * h)) 48)|CADENCIA=3h56 TURNOS_SIN_RASTRO=0 en 48 h | 0 de 42 en 7 dias"
"4 h con un hueco hace 32 h|$((b0 + 240 + 48 * 4 * h + 60))|$(serie $((b0 + 240)) $((4 * h)) 48 40)|CADENCIA=3h56 TURNOS_SIN_RASTRO=1 en 48 h (~10-07T16:09Z) | 1 de 42 en 7 dias"
"3 h|$((b0 + 60 + 64 * 3 * h + 60))|$(serie $((b0 + 60)) $((3 * h)) 64)|CADENCIA=2h56 TURNOS_SIN_RASTRO=0 en 48 h | 0 de 56 en 7 dias"
"1 h|$((b0 + 660 + 96 * h + 60))|$(serie $((b0 + 660)) $h 96)|CADENCIA=0h56 TURNOS_SIN_RASTRO=0 en 48 h | 0 de 95 en 7 dias"
"3 h y despues 4 h|$((b0 + 60 + 32 * 3 * h + 24 * 4 * h + 60))|$(serie $((b0 + 60)) $((3 * h)) 32) $(serie $((b0 + 60 + 32 * 3 * h)) $((4 * h)) 24)|CADENCIA=3h56 TURNOS_SIN_RASTRO=0 en 48 h | 0 de 48 en 7 dias"
"tramo abierto con un perdido|$((b0 + 240 + 47 * 4 * h + 60))|$(serie $((b0 + 240)) $((4 * h)) 46)|CADENCIA=3h56 TURNOS_SIN_RASTRO=1 en 48 h (~10-08T16:17Z) | 1 de 42 en 7 dias"
"turno en curso a los 130 min|$((b0 + 240 + 48 * 4 * h + 130 * 60))|$(serie $((b0 + 240)) $((4 * h)) 48)|CADENCIA=3h56 TURNOS_SIN_RASTRO=0 en 48 h | 0 de 42 en 7 dias"
"4 h y hace 30 h pasa a 1 h|$((b0 + 240 + 24 * 4 * h + 30 * h + 60))|$(serie $((b0 + 240)) $((4 * h)) 24) $(serie $((b0 + 240 + 24 * 4 * h)) $h 30)|CADENCIA=0h56 TURNOS_SIN_RASTRO=0 en 48 h | 0 de 53 en 7 dias"
"cada sesion commitea dos veces|$((b0 + 240 + 48 * 4 * h + 60))|$(serie $((b0 + 240)) $((4 * h)) 48) $(for x in $(serie $((b0 + 240)) $((4 * h)) 48); do echo $((x + 600)); done)|CADENCIA=3h56 TURNOS_SIN_RASTRO=0 en 48 h | 0 de 42 en 7 dias"
)
malos=0
for c in "${rcasos[@]}"; do
    nombre=${c%%|*}; resto=${c#*|}; ahora=${resto%%|*}; resto=${resto#*|}; eps=${resto%%|*}; e=${resto#*|}
    r=$(EQUIPO_AHORA=$ahora bash "$es" --rastros "$eps" 2>&1 | sed 's/ (mediana[^)]*)//' | tr '\n' ' ' | sed 's/ $//')
    [ "$r" = "$e" ] || { malos=$((malos + 1)); echo "FALLA rastros: $nombre -> $r (esperado $e)"; }
done
det=""; [ "$malos" -eq 0 ] || det=" $malos de ${#rcasos[@]} casos"
cierra rastros "$det"

# 10b. tamano: cada parte del playbook entra en una salida de la herramienta
# Bash, que guarda en un archivo lo que pasa de 30 KB y muestra solo 2 KB (con
# el SKILL.md de 59 KB, el arranque no veia ni el estado ni las reglas). Y
# turno.sh dice que leer, una parte por llamada.
det=""
tope_parte=28000
for f in "${playbook[@]}"; do
    b=$(wc -c < "$f"); [ "$b" -lt "$tope_parte" ] || det="$det ${f#$base/} $b bytes (tope $tope_parte);"
done
[ "${#playbook[@]}" -ge 9 ] || det="$det playbook con ${#playbook[@]} partes (esperadas SKILL.md, alcance.md y 7 roles);"
for t in '# leer: git show $ref:scripts/equipo-dev/estado.sh' '# leer: git show $ref:.claude/skills/equipo-dev/SKILL.md' '# leer: git show $ref:.claude/skills/equipo-dev/roles/$rol.md'; do
    grep -qF -- "$t" "$tu" || det="$det turno.sh no imprime '$t';"
done
cierra tamano "$det"

# 10c. espera: en una Routine el turno terminado es la corrida terminada, y la
# herramienta manda a segundo plano lo que pasa de 120 s. El playbook corre
# check.sh solo por verificar.sh, con timeout, y no deja nada esperando.
det=""
for t in 'verificar.sh' 'timeout: 600000' 'Monitor' 'el turno terminado es la corrida terminada'; do
    grep -qF -- "$t" "$sk" || det="$det SKILL.md sin '$t';"
done
m=$(grep -nE '\./scripts/check\.sh|bash scripts/check\.sh' "${playbook[@]}" "$ru" 2>/dev/null | grep -vE 'verificar|Nunca' | sed "s#^$base/##" | cut -d: -f1,2 | tr '\n' ' ')
[ -z "$m" ] || det="$det check.sh corrido sin verificar.sh en: $m;"
grep -qF 'verificar.sh' "$base/.opencode/commands/equipo-dev.md" 2>/dev/null || det="$det el comando de OpenCode no usa verificar.sh;"
cierra espera "$det"

# 10d. verificar: la espera en tramos contra un check.sh falso, en un repo
# temporal. Una llamada con --max corto sale 124 y la siguiente retoma la
# misma corrida (no la relanza); un resultado guardado se informa sin volver a
# correr; --estado solo cree en un verde completo sobre HEAD con el arbol
# limpio; una corrida que murio se relanza; el rojo sale 1 con su Fallo.
det=""
tv=$(mktemp -d)
falso="$tv/falso.sh"
cat > "$falso" <<'FALSO'
#!/usr/bin/env bash
echo x >> "$FALSO_DIR/corridas"
sleep "$(cat "$FALSO_DIR/dormir")"
echo "Ran 7 tests in 0.1s"; echo "      Tests  3 passed (3)"; echo "  2 passed (1.0s)"
[ "$(cat "$FALSO_DIR/codigo")" = 0 ] && { echo "Todo en verde."; exit 0; }
echo "Fallo: tests"; exit 1
FALSO
(
    set -u
    export FALSO_DIR="$tv/f" EQUIPO_CHECK_CMD="bash $falso"
    # Sin la configuracion global: la de la nube firma commits y negocia pushes.
    export GIT_CONFIG_GLOBAL=/dev/null GIT_CONFIG_NOSYSTEM=1 GIT_AUTHOR_NAME=t GIT_COMMITTER_NAME=t GIT_AUTHOR_EMAIL=t@t GIT_COMMITTER_EMAIL=t@t
    mkdir -p "$FALSO_DIR" "$tv/r"; echo 2 > "$FALSO_DIR/dormir"; echo 0 > "$FALSO_DIR/codigo"
    cd "$tv/r" && git init -q && echo a > a && git add a && git commit -qm uno || exit 9
    v() { bash "$ve" "$@" > "$tv/salida" 2>&1; echo $?; }
    c=$(v --max 0); [ "$c" = 124 ] || echo "primera llamada con --max 0: salida $c (esperada 124)"
    c=$(v --estado); [ "$c" = 1 ] || echo "--estado con la corrida en curso: salida $c (esperada 1)"
    c=$(v --max 30); [ "$c" = 0 ] && grep -q '^VERDE .*7 tests backend, 3 vitest, 2 e2e' "$tv/salida" || echo "segunda llamada: salida $c, $(head -1 "$tv/salida")"
    c=$(v --max 30); [ "$c" = 0 ] || echo "resultado guardado: salida $c"
    [ "$(wc -l < "$FALSO_DIR/corridas")" -eq 1 ] || echo "check.sh corrio $(wc -l < "$FALSO_DIR/corridas") veces para un mismo commit (esperada 1)"
    c=$(v --estado); [ "$c" = 0 ] || echo "--estado tras el verde: salida $c (esperada 0)"
    echo b > a
    c=$(v --estado); [ "$c" = 1 ] || echo "--estado con el arbol sucio: salida $c (esperada 1)"
    git checkout -q -- a
    echo 30 > "$FALSO_DIR/dormir"; git commit -qm dos --allow-empty
    c=$(v --max 1); [ "$c" = 124 ] || echo "corrida larga: salida $c (esperada 124)"
    # Muere con el contenedor: se mata su grupo entero (setsid) sin dejar .fin.
    pid=$(cat "$(git rev-parse --absolute-git-dir)/equipo-dev-verificar/$(git rev-parse HEAD).pid")
    kill -9 -- "-$pid" 2>/dev/null || { pkill -9 -P "$pid"; kill -9 "$pid"; } 2>/dev/null
    for _ in 1 2 3 4 5; do kill -0 "$pid" 2>/dev/null || break; sleep 1; done
    echo 0 > "$FALSO_DIR/dormir"; echo 1 > "$FALSO_DIR/codigo"
    c=$(v --max 30); [ "$c" = 1 ] && grep -q 'murio' "$tv/salida" && grep -q '^ROJO .*Fallo: tests' "$tv/salida" || echo "corrida muerta y relanzada en rojo: salida $c, $(tr '\n' ' ' < "$tv/salida" | cut -c1-200)"
    c=$(v --max 0 --de-nuevo); [ "$c" = 124 ] || [ "$c" = 1 ] || echo "--de-nuevo: salida $c"
    c=$(v --max 1 --foo); [ "$c" = 2 ] || echo "opcion invalida: salida $c (esperada 2)"
) > "$tv/fallos" 2>&1
[ -s "$tv/fallos" ] && det=" $(tr '\n' ';' < "$tv/fallos")"
rm -rf "$tv"
cierra verificar "$det"

# 10e. independencia: la condicion b y lo que estado.sh no cuenta. Los pares
# de `turnos:` (notas entre parentesis, entradas viejas sin contexto) y quien
# puede firmar que; despues, estado.sh entero sobre un remoto sintetico.
det=""
casos_i=(
'turnos: po 20261030T1653Z, dev 20261031T2135Z-cr3J9k (relevo de qa, P7), foo|po 20261030T1653Z 20261030T1653Z;dev 20261031T2135Z-cr3J9k cr3J9k;ILEGIBLE foo;'
'turnos: dev 20261009T0905Z, revisor 20261009T1205Z, qa 20261009T1805Z|dev 20261009T0905Z 20261009T0905Z;revisor 20261009T1205Z 20261009T1205Z;qa 20261009T1805Z 20261009T1805Z;'
)
for c in "${casos_i[@]}"; do
    r=$(bash "$in" --turnos "${c%%|*}" | tr '\n' ';')
    [ "$r" = "${c#*|}" ] || det="$det --turnos '${c%%|*}' -> '$r';"
done
firmas=(
'dev 20261031T2135Z-cr3J9k|revisor|cr3J9k|1'
'dev 20261031T2135Z-cr3J9k|revisor|cZZ999|0'
'dev 20261031T2135Z-cr3J9k, revisor 20261101T0331Z-ab12cd|qa|ab12cd|1'
'dev 20261031T2135Z-cr3J9k, revisor 20261101T0331Z-ab12cd|qa|cr3J9k|1'
'dev 20261031T2135Z-cr3J9k, revisor 20261101T0331Z-ab12cd|release|cr3J9k|0'
'dev 20261031T2135Z-cr3J9k, qa 20261101T0331Z-ab12cd|revisor|ab12cd|1'
'dev 20261030T1653Z|revisor|20261030T1653Z|1'
)
for c in "${firmas[@]}"; do
    IFS='|' read -r t rol ctx esperado <<< "$c"
    bash "$in" --firmable "turnos: $t" "$rol" "$ctx" >/dev/null 2>&1; r=$?
    [ "$r" = "$esperado" ] || det="$det --firmable '$t' $rol $ctx -> $r (esperado $esperado);"
done
# estado.sh sobre un remoto sintetico: una implementado y una revisado.
ts=$(mktemp -d)
(
    export GIT_CONFIG_GLOBAL=/dev/null GIT_CONFIG_NOSYSTEM=1
    export GIT_AUTHOR_NAME=Claude GIT_COMMITTER_NAME=Claude GIT_AUTHOR_EMAIL=c@c GIT_COMMITTER_EMAIL=c@c
    cd "$ts" && git init -q --bare origen.git && git clone -q origen.git w 2>/dev/null && cd w || exit 9
    mkdir -p .claude/skills/equipo-dev docs/backlog && echo x > .claude/skills/equipo-dev/rutina.md
    git add -A && git commit -qm base && git push -q origin HEAD:dev HEAD:main || exit 9
    ficha() { # rama ficha estado turnos
        git checkout -q -B "$1" origin/dev && mkdir -p docs/backlog
        printf 'estado: %s\ncandado: -\ntipo: funcionalidad\nturnos: %s\n' "$3" "$4" > "docs/backlog/$2.md"
        git add -A && git commit -qm "Reclama: $2" && git push -q origin "HEAD:refs/heads/claude/equipo-dev/$2"
    }
    git fetch -q origin
    ficha a 80-implementada implementado 'po 20261101T0000Z, dev 20261101T0100Z-cAAAAA'
    ficha b 81-revisada revisado 'dev 20261101T0100Z-cBBBBB, revisor 20261101T0400Z-cCCCCC'
    r() { EQUIPO_AHORA=$(date -u +%s) EQUIPO_INDEPENDENCIA="$in" EQUIPO_CONTEXTO="$1" bash "$es" --resumen 2>/dev/null | grep -oE 'implementado=[0-9]+|revisado=[0-9]+|bloqueadas=[0-9]+' | tr '\n' ' '; }
    for c in 'cAAAAA|implementado=0 revisado=1 bloqueadas=1 ' 'cCCCCC|implementado=1 revisado=0 bloqueadas=1 ' 'cBBBBB|implementado=1 revisado=0 bloqueadas=1 ' 'cOTRO1|implementado=1 revisado=1 bloqueadas=0 ' '|implementado=1 revisado=1 bloqueadas=0 '; do
        s=$(r "${c%%|*}"); [ "$s" = "${c#*|}" ] || echo "estado.sh con contexto '${c%%|*}': '$s' (esperado '${c#*|}')"
    done
) > "$ts/fallos" 2>&1
[ -s "$ts/fallos" ] && det="$det $(tr '\n' ';' < "$ts/fallos")"
rm -rf "$ts"
cierra independencia "$det"

# 11. resumen: contra el remoto real, la linea existe y trae los 21 pares en
# orden; los valores no se afirman porque cambian con cada turno. Lo unico
# estable: la rama del playbook no aparece como rama de trabajo.
if [ "${PRUEBAS_SIN_RED:-}" = 1 ]; then
    ok "resumen (saltada: PRUEBAS_SIN_RED=1)"
else
    det=""
    salida=$(bash "$es" --resumen 2>/dev/null)
    lineas=$(printf '%s\n' "$salida" | grep -c .)
    claves=$(printf '%s\n' "$salida" | grep -m1 '^RESUMEN ' | sed 's/^RESUMEN //' | tr ' ' '\n' | grep -E '^[a-z_0-9]+=[^ ]+$' | cut -d= -f1 | tr '\n' ' ')
    esperadas='propuesto disenado en_curso huerfanas implementado revisado con_hallazgos aprobado entregado espera_humano cola total tope_cola tope_total tope_propuesto tope_disenado ideas_libres sin_merge pausa sin_rastro_48h bloqueadas '
    [ "$lineas" -eq 1 ] || det="$det $lineas lineas en vez de 1;"
    [ "$claves" = "$esperadas" ] || det="$det pares: '${claves:-ninguno}';"
    filas=$(bash "$es" 2>/dev/null | grep -c 'equipo-dev/playbook |')
    [ "$filas" -eq 0 ] || det="$det la rama del playbook aparece $filas veces como rama de trabajo"
    cierra resumen "$det"

    # 12. tablero: lo que estado.sh le da al cierre para el humano y al PO,
    # contra el remoto real. Una rama del playbook ya contenida en dev no es
    # candidata; toda rama del equipo ya mergeada esta en el comando BORRAR;
    # salen la rotacion y el tamano de `## Para el humano`.
    det=""
    completa=$(bash "$es" 2>/dev/null)
    pb=origin/claude/equipo-dev/playbook
    if git rev-parse -q --verify "$pb" >/dev/null && git merge-base --is-ancestor "$pb" origin/dev; then
        printf '%s\n' "$completa" | grep -q '^PLAYBOOK_CANDIDATO=' && det="$det PLAYBOOK_CANDIDATO con $pb ya en dev;"
    fi
    borrar=$(printf '%s\n' "$completa" | grep -m1 '^BORRAR: git push origin --delete ')
    for r in $(git branch -r --list 'origin/claude/equipo-dev/[0-9]*' --merged origin/dev --format='%(refname:short)'); do
        case " ${borrar#BORRAR: } " in *" ${r#origin/} "*) ;; *) det="$det ${r#origin/} falta en BORRAR;" ;; esac
    done
    nb=$(printf '%s\n' "$completa" | grep -m1 '^BORRABLES=' | cut -d= -f2)
    [ -n "$nb" ] && [ "$nb" -eq "$(printf '%s\n' "${borrar#BORRAR: git push origin --delete }" | tr ' ' '\n' | grep -c .)" ] || det="$det BORRABLES='${nb:-}' no cuadra con BORRAR;"
    for k in CADENCIA ROTACION_EPICAS ROTACION_PAGINAS ROTACION CICLO PARA_EL_HUMANO RELEASE DEV_7D FRENADAS TURNOS_EN_VACIO; do
        printf '%s\n' "$completa" | grep -q "^$k=" || det="$det falta $k=;"
    done
    printf '%s\n' "$completa" | grep -qE '^ROTACION=saturadas \(' || det="$det ROTACION sin saturadas;"
    cierra tablero "$det"
fi

# 13. base: el equipo integra en dev y main es release (lo promueve el humano).
# origin/main solo puede aparecer en la cadena (respaldo) y en la linea RELEASE;
# un compare/main... solo en RELEASE; todo git fetch trae dev. Una rama de
# trabajo creada desde main, un merge de main o un PR contra main caen aca.
det=""
for f in "${playbook[@]}" "$ru" "$tu" "$es" $base/.claude/skills/equipo-dev/revision.md $base/.claude/skills/equipo-dev/plantilla-pr.md $base/.claude/skills/equipo-dev/arena.md $base/.claude/skills/equipo-dev/replica.md $base/.claude/skills/equipo-dev/skills.md $base/.claude/skills/equipo-dev/skills-del-repo.md "$bl/ESTADO.plantilla.md" "$bl/README.md"; do
    [ -f "$f" ] || continue
    m=$(grep -nE 'origin/main|compare/main\.\.\.' "$f" | grep -vF -- "$cadena" | grep -v 'RELEASE' | cut -d: -f1 | tr '\n' ',')
    [ -z "$m" ] || det="$det ${f#$base/} nombra main fuera de la cadena y de RELEASE (lineas ${m%,});"
    m=$(grep -nE 'git fetch( -q)? origin ' "$f" | grep -v 'origin dev' | cut -d: -f1 | tr '\n' ',')
    [ -z "$m" ] || det="$det ${f#$base/} hace git fetch sin dev (lineas ${m%,});"
done
grep -qE 'abierto contra `dev`' "$ro/release.md" 2>/dev/null || det="$det roles/release.md: la puerta de merge no pide el PR contra dev;"
cierra base "$det"

# 14. skills: toda skill que el playbook nombra existe, y toda vendorizada
# tiene un paso que la cita o su motivo para quedar a mano. El mapa es la
# tabla de `skills-del-repo.md`. Un paso cita una skill como "skill `<nombre>`";
# tambien cuentan `<plugin>:<nombre>`, `/<nombre> ...` y las rutas
# .claude/skills/<nombre>/. Lo que no esta en .claude/skills/ solo vale si
# viene con Claude Code o es un conector (las dos listas). Cada cita tiene su
# fila con ese archivo en `donde`, y cada archivo de `donde` la cita: asi el
# mapa no se aleja de los roles. MAQUINARIA.md no se mira: ahi se proponen
# skills que todavia no estan.
INCORPORADAS="dataviz code-review security-review simplify claude-api"
CONECTORES="github"
det=""
ed=$base/.claude/skills/equipo-dev
sr=$ed/skills-del-repo.md
vm=$base/.claude/skills/VENDORIZADAS.md
hay_skill() {
    [ -f "$base/.claude/skills/$1/SKILL.md" ] && return 0
    case " $INCORPORADAS $CONECTORES " in *" $1 "*) return 0 ;; esac
    return 1
}
# Un parrafo partido entre "skill" y su nombre sigue siendo una cita: se mira
# cada archivo con los saltos de linea hechos espacios.
plano() { tr '\n' ' ' < "$1" | tr -s ' '; }
citas() { plano "$1" | grep -oE 'skill `[a-z0-9:-]+`' | sed -E 's/^skill `(.*)`$/\1/; s/^.*://' | sort -u; }
textos=()
for f in "$ed"/*.md "$ro"/*.md "$bl/README.md" "$bl/PLANTILLA.md" "$bl/ESTADO.plantilla.md" "$base/.opencode/commands/equipo-dev.md"; do
    [ -f "$f" ] && textos+=("$f")
done
nombradas=$( {
    for f in "${textos[@]}"; do citas "$f"; done
    grep -ohE '`[a-z][a-z0-9-]*:[a-z][a-z0-9-]*`' "${textos[@]}" | tr -d '`' | sed 's/^.*://'
    grep -ohE '`/[a-z][a-z0-9-]*( [^`]*)?`' "${textos[@]}" | sed -E 's#^`/([a-z0-9-]+).*#\1#'
    grep -ohE '\.claude/skills/[a-z0-9][a-z0-9-]*/' "${textos[@]}" | sed -E 's#^\.claude/skills/##; s#/$##'
} 2>/dev/null | sort -u)
for s in $nombradas; do
    hay_skill "$s" || det="$det el playbook nombra '$s', que no esta en .claude/skills/ ni en INCORPORADAS ni en CONECTORES;"
done
filas=$(grep -E '^\| `[a-z0-9-]+` \|' "$sr" 2>/dev/null)
[ -n "$filas" ] || det="$det skills-del-repo.md sin la tabla del mapa;"
mapa=" "
while IFS='|' read -r _ nom o d _; do
    [ -n "$nom" ] || continue
    nom=$(printf '%s' "$nom" | tr -d ' `'); o=$(printf '%s' "$o" | tr -d ' '); d=$(printf '%s' "$d" | sed 's/^ *//; s/ *$//')
    mapa="$mapa$nom "
    case "$o" in
        propia|vendorizada) [ -f "$base/.claude/skills/$nom/SKILL.md" ] || det="$det mapa: $nom ($o) no esta en .claude/skills/;" ;;
        incorporada) case " $INCORPORADAS " in *" $nom "*) ;; *) det="$det mapa: $nom no esta en INCORPORADAS;" ;; esac ;;
        conector) case " $CONECTORES " in *" $nom "*) ;; *) det="$det mapa: $nom no esta en CONECTORES;" ;; esac ;;
        *) det="$det mapa: $nom con origen '$o';" ;;
    esac
    if grep -qE "^\| \`$nom\` \|" "$vm" 2>/dev/null; then
        [ "$o" = vendorizada ] || det="$det mapa: $nom esta en VENDORIZADAS.md y dice $o;"
    else
        [ "$o" != vendorizada ] || det="$det mapa: $nom dice vendorizada y no esta en VENDORIZADAS.md;"
    fi
    case "$d" in
        'a mano:'*)
            m=${d#a mano:}; m=$(printf '%s' "$m" | tr -d ' ')
            [ "${#m}" -ge 20 ] || det="$det mapa: $nom a mano sin motivo;" ;;
        *)
            arch=$(printf '%s\n' "$d" | grep -oE '`[A-Za-z/-]+\.md`' | tr -d '`')
            [ -n "$arch" ] || det="$det mapa: $nom sin donde (archivos del playbook o 'a mano: <motivo>');"
            for a in $arch; do
                if [ ! -f "$ed/$a" ]; then det="$det mapa: $nom en $a, que no existe;"; continue; fi
                case "$o" in
                    conector) grep -qF "mcp__${nom}__" "$ed/$a" ;;
                    propia) grep -qiw -- "$nom" "$ed/$a" ;;
                    *) plano "$ed/$a" | grep -qF -- "skill \`$nom\`" ;;
                esac || det="$det mapa: $a no cita $nom;"
            done ;;
    esac
done <<< "$filas"
for f in "$ed"/*.md "$ro"/*.md; do
    [ -f "$f" ] || continue
    rel=${f#$ed/}
    for nom in $(citas "$f"); do
        fila=$(printf '%s\n' "$filas" | grep -E "^\| \`$nom\` \|")
        if [ -z "$fila" ]; then det="$det $rel cita la skill $nom y el mapa no la tiene;"
        else printf '%s\n' "$fila" | cut -d'|' -f4 | grep -qF "\`$rel\`" || det="$det $rel cita la skill $nom y su fila del mapa no lo dice;"
        fi
    done
done
vend=$(grep -oE '^\| `[a-z0-9-]+` \|' "$vm" 2>/dev/null | tr -d '|` ')
[ -n "$vend" ] || det="$det VENDORIZADAS.md sin su tabla;"
for nom in $vend; do
    case "$mapa" in *" $nom "*) ;; *) det="$det $nom esta vendorizada y el mapa no dice en que paso se usa ni por que queda a mano;" ;; esac
done
cierra skills "$det"

if [ "$fallos" -gt 0 ]; then echo "PRUEBAS_FALLAN: $fallos"; exit 1; fi
echo "PRUEBAS_OK ($n)"
