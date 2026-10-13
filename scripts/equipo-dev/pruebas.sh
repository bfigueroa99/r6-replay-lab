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
    for p in $(git ls-tree -r --name-only "$REF" -- .claude scripts docs/backlog 2>/dev/null); do
        mkdir -p "$base/$(dirname "$p")"
        git show "$REF:$p" > "$base/$p"
    done
else
    base="$repo"
fi
sk=$base/.claude/skills/equipo-dev/SKILL.md
ru=$base/.claude/skills/equipo-dev/rutina.md
rl=$base/.claude/skills/equipo-dev/roles
ROLES="release po arquitecto dev revisor qa investigador"
tu=$base/scripts/equipo-dev/turno.sh
es=$base/scripts/equipo-dev/estado.sh
bl=$base/docs/backlog

n=0; fallos=0
ok() { n=$((n + 1)); echo "OK $1"; }
falla() { n=$((n + 1)); fallos=$((fallos + 1)); echo "FALLA $1:$2"; }
cierra() { if [ -z "$2" ]; then ok "$1"; else falla "$1" "$2"; fi; }

# 1. sintaxis
det=""
for s in scripts/equipo-dev/turno.sh scripts/equipo-dev/estado.sh scripts/equipo-dev/pruebas.sh scripts/check.sh .claude/hooks/session-start.sh \
    scripts/equipo-dev/puerta.sh scripts/equipo-dev/pulso.sh scripts/equipo-dev/fichas.sh scripts/equipo-dev/sintetico.sh \
    scripts/equipo-dev/deriva-docs.sh scripts/equipo-dev/qa.sh scripts/equipo-dev/notas.sh scripts/equipo-dev/pre-push.sh; do
    if [ ! -f "$base/$s" ]; then det="$det falta $s"
    elif ! bash -n "$base/$s" 2>/dev/null; then det="$det bash -n $s"
    fi
done
for s in scripts/equipo-dev/barrido_api.py scripts/equipo-dev/fuzz_parser.py scripts/equipo-dev/mutar.py; do
    if [ ! -f "$base/$s" ]; then det="$det falta $s"
    elif ! python3 -c "import ast, sys; ast.parse(open(sys.argv[1]).read())" "$base/$s" 2>/dev/null; then det="$det python $s"
    fi
done
if [ ! -f "$base/scripts/equipo-dev/qa-paginas.mjs" ]; then det="$det falta scripts/equipo-dev/qa-paginas.mjs"
elif command -v node >/dev/null 2>&1 && ! node --check "$base/scripts/equipo-dev/qa-paginas.mjs" 2>/dev/null; then det="$det node --check qa-paginas.mjs"
fi
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
    for t in 'turno.sh' 'estado.sh' 'rol:' 'SKILL.md' 'roles/$EQUIPO_ROL.md' 'equipo-dev.env' 'SIN_PLAYBOOK' '+refs/heads/claude/*'; do
        grep -qF -- "$t" "$ru" || det="$det falta '$t'"
    done
    for t in tope minutos P1; do grep -qi -- "$t" "$ru" && det="$det contiene '$t'"; done
fi
cierra rutina "$det"

# 4. rutas: todo lo que los textos nombran como archivo existe. Los
# `roles/<rol>.md` que se citan entre si son relativos a la skill.
det=""
# Linea por linea y no `for p in $(...)`: el for expandiria `docs/backlog/*.md`
# contra el directorio actual.
textos=$(cat "$sk" "$ru" "$bl/README.md" "$rl"/*.md 2>/dev/null)
while IFS= read -r p; do
    [ -n "$p" ] || continue
    case " $EXENTAS " in *" $p "*) continue ;; esac
    case "$p" in *NN*|*'*'*|*'<'*|*'$'*) continue ;; esac
    case "$p" in roles/*) p=.claude/skills/equipo-dev/$p ;; esac
    [ -e "$base/$p" ] || det="$det $p"
done <<< "$(printf '%s\n' "$textos" | grep -oE '`(\.claude|scripts|docs/backlog|roles)/[^` ]*`' | tr -d '`' | sort -u)"
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

# 7. roles: los siete del case de turno.sh tienen su archivo `roles/<rol>.md`
# con un `# Rol:`, el indice de SKILL.md los nombra a los siete y no sobra
# ninguno: un rol sin archivo deja al turno sin especificacion.
det=""
caso=$(grep -oE '^[[:space:]]*release\|[a-z|]+\)' "$tu" 2>/dev/null | head -1 | tr -d ' )' | tr '|' ' ')
[ "$caso" = "$ROLES" ] || det="$det case de turno.sh: '$caso' (esperado '$ROLES');"
for r in $ROLES; do
    if [ ! -f "$rl/$r.md" ]; then det="$det falta roles/$r.md;"
    else grep -q '^# Rol: ' "$rl/$r.md" || det="$det roles/$r.md sin '# Rol:';"
    fi
    sed -n '/^## Especificacion por rol/,/^## Cierre comun/p' "$sk" 2>/dev/null | grep -qF "\`roles/$r.md\`" || det="$det el indice de SKILL.md no nombra roles/$r.md;"
done
for f in "$rl"/*.md; do
    [ -e "$f" ] || continue
    r=$(basename "$f" .md)
    case " $ROLES " in *" $r "*) ;; *) det="$det roles/$r.md no es un rol de turno.sh;" ;; esac
done
nh=$(sed -n '/^## Especificacion por rol/,/^## Cierre comun/p' "$sk" 2>/dev/null | grep -c '^### ')
[ "$nh" -eq 0 ] || det="$det SKILL.md volvio a tener $nh especificaciones ### de rol"
cierra roles "$det"

# 8. podridos: hechos que ya no son ciertos y que el playbook no puede nombrar.
det=""
for f in "$sk" "$rl"/*.md; do
    for t in 'ci.yml' 'hoy:' '90 minutos' '#11' 'great-'"cray"; do grep -qF -- "$t" "$f" 2>/dev/null && det="$det ${f#$base/}:'$t'"; done
done
cierra podridos "$det"

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
'|propuesto=6 disenado=3 cola=4 total=4 ideas_libres=23 papel_func=2 hora=2101 fecha=2026-10-12|rol=investigador motivo=reloj: investigador reloj=investigador franja=7'
'|propuesto=6 disenado=3 cola=4 total=4 ideas_libres=23 papel_func=2 hora=2101 fecha=2026-10-13|rol=revisor motivo=nada tomable: reloj reloj=revisor franja=7'
'|propuesto=6 disenado=3 cola=4 total=4 ideas_libres=5 papel_func=2 hora=1201|rol=investigador motivo=ideas libres: 5 de 10 reloj=revisor franja=4'
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
'|propuesto=2 ideas_libres=5 hora=1201|rol=po motivo=papel sin funcionalidades: 5 ideas libres reloj=revisor franja=4'
'|propuesto=2 papel_func=1 ideas_libres=5 hora=1201|rol=arquitecto motivo=por estado: 2 propuesto, 0 disenado de 3 reloj=revisor franja=4'
'|disenado=1 ideas_libres=5 cola=1 total=1 hora=1801|rol=po motivo=papel sin funcionalidades: 5 ideas libres reloj=qa franja=6'
'|bug_p1=1 propuesto=1 cola=4 total=4 hora=0301|rol=dev motivo=por estado: 1 bug prioridad 1 reloj=po franja=1'
'|bug_p1=1 propuesto=1 cola=5 total=5 hora=0301|rol=arquitecto motivo=por estado: 1 propuesto, 0 disenado de 3 reloj=po franja=1'
'|bug_p1=1 implementado=1 propuesto=1 hora=0301|rol=revisor motivo=por estado: 1 implementado reloj=po franja=1'
'|con_hallazgos=1 bug_p1=1 propuesto=1 hora=0301|rol=dev motivo=por estado: 1 con_hallazgos, 0 huerfanas reloj=po franja=1'
'|bug_p1=1 propuesto=1 espera_humano=1 hora=0001|rol=dev motivo=por estado: 1 bug prioridad 1 reloj=release franja=0'
)
malos=0
for c in "${casos[@]}"; do
    r=${c%%|*}; resto=${c#*|}; a=${resto%%|*}; e=${resto#*|}
    if [ -n "$r" ]; then s=$(GIT_DIR="$base/.nogit" bash "$tu" "$r" --simular "$a" 2>&1); else s=$(GIT_DIR="$base/.nogit" bash "$tu" --simular "$a" 2>&1); fi
    [ "$s" = "$e" ] || { malos=$((malos + 1)); echo "FALLA simular: ${r:+$r }$a -> $s (esperado $e)"; }
done
GIT_DIR="$base/.nogit" bash "$tu" foo --simular "hora=0905" >/dev/null 2>&1; codigo=$?
[ "$codigo" -eq 1 ] || { malos=$((malos + 1)); echo "FALLA simular: foo --simular hora=0905 -> salida $codigo (esperado 1)"; }
# Encadenar: misma sesion, siguiente rol. Los contadores ya vienen sin las
# fichas que la sesion firmo (estado.sh --excluir-sesion, que se prueba en el
# repo sintetico); aca se fija cuando se encadena y cuando no.
casos_enc=(
'|roles=po queda=90 disenado=1 cola=1 total=1 papel_func=1 hora=0305|encadenar=si rol=dev motivo=por estado: 1 disenado, lugar en cola'
'|roles=dev queda=90 revisado=1 hora=1505|encadenar=si rol=qa motivo=por estado: 1 revisado'
'|roles=po queda=30 disenado=1 cola=1 total=1 papel_func=1 hora=0305|encadenar=no motivo=quedan 30 minutos (minimo 40)'
'|roles=po,dev,qa queda=90 aprobado=1 hora=0305|encadenar=no motivo=ya hizo 3 roles (tope 3)'
'|roles=revisor queda=90 implementado=1 hora=1205|encadenar=no motivo=el rol que sigue (revisor) ya lo hizo esta sesion'
'|roles=dev queda=90 propuesto=6 disenado=3 cola=4 total=4 ideas_libres=23 papel_func=2 hora=1205|encadenar=no motivo=nada tomable'
'qa|roles=dev queda=90 revisado=1 hora=1505|encadenar=no motivo=un rol pedido no encadena'
)
for c in "${casos_enc[@]}"; do
    r=${c%%|*}; resto=${c#*|}; a=${resto%%|*}; e=${resto#*|}
    if [ -n "$r" ]; then s=$(GIT_DIR="$base/.nogit" bash "$tu" "$r" --encadenar --simular "$a" 2>&1); else s=$(GIT_DIR="$base/.nogit" bash "$tu" --encadenar --simular "$a" 2>&1); fi
    [ "$s" = "$e" ] || { malos=$((malos + 1)); echo "FALLA simular: --encadenar ${r:+$r }$a -> $s (esperado $e)"; }
done
det=""; [ "$malos" -eq 0 ] || det=" $malos de $(( ${#casos[@]} + ${#casos_enc[@]} + 1 )) casos"
cierra simular "$det"

# 10. resumen: contra el remoto real, la linea existe y trae los 22 pares en
# orden; los valores no se afirman porque cambian con cada turno. Lo unico
# estable: la rama del playbook no aparece como rama de trabajo.
if [ "${PRUEBAS_SIN_RED:-}" = 1 ]; then
    ok "resumen (saltada: PRUEBAS_SIN_RED=1)"
else
    det=""
    salida=$(bash "$es" --resumen 2>/dev/null)
    lineas=$(printf '%s\n' "$salida" | grep -c .)
    claves=$(printf '%s\n' "$salida" | grep -m1 '^RESUMEN ' | sed 's/^RESUMEN //' | tr ' ' '\n' | grep -E '^[a-z_0-9]+=[^ ]+$' | cut -d= -f1 | tr '\n' ' ')
    esperadas='propuesto disenado en_curso huerfanas implementado revisado con_hallazgos aprobado entregado espera_humano cola total tope_cola tope_total tope_propuesto tope_disenado ideas_libres sin_merge pausa sin_rastro_48h papel_func bug_p1 '
    [ "$lineas" -eq 1 ] || det="$det $lineas lineas en vez de 1;"
    [ "$claves" = "$esperadas" ] || det="$det pares: '${claves:-ninguno}';"
    filas=$(bash "$es" 2>/dev/null | grep -c 'equipo-dev/playbook |')
    [ "$filas" -eq 0 ] || det="$det la rama del playbook aparece $filas veces como rama de trabajo"
    cierra resumen "$det"
fi

# 11-13: de punta a punta contra un remoto sintetico (sintetico.sh, M5): el
# escenario fija los numeros que se afirman aca. Nada toca el remoto real.
es_s=$base/scripts/equipo-dev
sint=$(mktemp -d)
salida_s=$(bash "$es_s/sintetico.sh" "$sint" "$base" 2>&1)
AHORA_S=$(printf '%s\n' "$salida_s" | grep -oE 'AHORA=[0-9]+' | cut -d= -f2)
clon=$sint/clon
if [ -z "$AHORA_S" ] || [ ! -d "$clon/.git" ]; then
    falla sintetico " no se pudo armar el repo sintetico: $(printf '%s' "$salida_s" | tail -2 | tr '\n' ' ')"
else
    # 11. estado.sh: los contadores, M6 (lo que espera al humano ocupa un
    # lugar), M10, borrables por squash y la exclusion por sesion.
    det=""
    sal=$(cd "$clon" && EQUIPO_AHORA=$AHORA_S bash "$es_s/estado.sh" 2>&1)
    esperado='RESUMEN propuesto=2 disenado=1 en_curso=1 huerfanas=1 implementado=2 revisado=0 con_hallazgos=0 aprobado=3 entregado=0 espera_humano=2 cola=7 total=8 tope_cola=4 tope_total=6 tope_propuesto=6 tope_disenado=3 ideas_libres=2 sin_merge=no pausa=no sin_rastro_48h=7 papel_func=1 bug_p1=1'
    r=$(printf '%s\n' "$sal" | grep -m1 '^RESUMEN ')
    [ "$r" = "$esperado" ] || det="$det RESUMEN: '$r';"
    printf '%s\n' "$sal" | grep -qx 'PLAYBOOK_TOCADO_POR_EL_EQUIPO=claude/equipo-dev/47-toca-playbook: scripts/equipo-dev/turno.sh' || det="$det sin PLAYBOOK_TOCADO de 47;"
    printf '%s\n' "$sal" | grep -q '51-squash | mergeada efectivamente: borrable' || det="$det 51 no sale borrable;"
    printf '%s\n' "$sal" | grep -q 'ESPERA_HUMANO=2 (ocupan 1 lugar de COLA)' || det="$det sin ESPERA_HUMANO;"
    r=$(cd "$clon" && EQUIPO_AHORA=$AHORA_S bash "$es_s/estado.sh" --resumen --sin-fetch --excluir-sesion 20261011T1202Z 2>/dev/null)
    case "$r" in *" aprobado=1 "*) ;; *) det="$det --excluir-sesion del revisor de 44 y 50 no deja aprobado=1: '$r';" ;; esac
    r=$(cd "$clon" && EQUIPO_AHORA=$AHORA_S bash "$es_s/estado.sh" --resumen --sin-fetch --excluir-sesion 20261012T0301Z 2>/dev/null)
    case "$r" in "RESUMEN propuesto=1 "*) ;; *) det="$det --excluir-sesion del po de 40 no deja propuesto=1: '$r';" ;; esac
    # M7: las notas de version salen de las fichas que llegaron a main.
    r=$(cd "$clon" && bash "$es_s/notas.sh" 2>&1)
    printf '%s\n' "$r" | grep -q '^### Por dentro (tests y deuda)' && printf '%s\n' "$r" | grep -q '(ficha 51)' || det="$det notas.sh no lista la 51: '$(printf '%s' "$r" | head -3 | tr '\n' ' ')';"
    r=$(cd "$clon" && bash "$es_s/notas.sh" --desde origin/main 2>&1)
    case "$r" in NOTAS_VACIAS*) ;; *) det="$det notas.sh desde main no da NOTAS_VACIAS: '$r';" ;; esac
    cierra sintetico "$det"

    # 12. puerta.sh: cada condicion cae con su violacion y pasa sin ella.
    det=""
    pu() { (cd "$clon" && EQUIPO_INICIO=0 bash "$es_s/puerta.sh" "$@" 2>&1); }
    sha44=$(git -C "$clon" rev-parse origin/claude/equipo-dev/44-aprobada)
    echo "$sha44 $(date -u +%s) e2e" > "$clon/.git/check-verde"
    r=$(pu claude/equipo-dev/44-aprobada | tail -1)
    [ "$r" = "PUERTA_OK (a confirmar a mano: c2 e)" ] || det="$det 44 limpia: '$r';"
    echo "$sha44 $(date -u +%s) sin-e2e" > "$clon/.git/check-verde"
    pu claude/equipo-dev/44-aprobada | grep -q '^PUERTA f FALLA: sin check.sh completo' || det="$det un verde sin e2e pasa f;"
    rm -f "$clon/.git/check-verde"
    pu claude/equipo-dev/49-misma-sesion | grep -q '^PUERTA b FALLA: dev y revisor en la misma sesion: 20261012T0902Z' || det="$det 49 pasa b con dev y revisor en una sesion;"
    r=$(pu claude/equipo-dev/50-humano --solo c)
    printf '%s\n' "$r" | grep -q 'commit de Benjamin sin respuesta' || det="$det 50 pasa c con un commit humano sin respuesta;"
    printf '%s\n' "$r" | grep -q 'pregunta abierta en Para el humano' || det="$det 50 pasa c con una pregunta abierta;"
    pu claude/equipo-dev/47-toca-playbook --solo d | grep -q '^PUERTA d FALLA: toca lo que mergea el humano: .*scripts/equipo-dev/turno.sh' || det="$det 47 pasa d tocando scripts/equipo-dev/;"
    pu claude/equipo-dev/44-aprobada --solo b --como qa 20261011T0902Z | grep -q 'ya firmo otra etapa' || det="$det el dev de 44 puede firmar su QA;"
    pu claude/equipo-dev/44-aprobada --solo b --como revisor 20261013T0902Z | grep -q '^PUERTA b OK' || det="$det una sesion nueva no puede revisar 44;"
    pu claude/equipo-dev/44-aprobada --solo b --como release 20261011T1802Z | grep -q 'ya firmo otra etapa' || det="$det el QA de 44 puede mergearla;"
    r=$(bash "$es_s/puerta.sh" --turnos "turnos: po 20261010T0301Z, dev 20261010T1501Z (relevo de qa, 48 h), revisor 2026101, Qa 20261013T0302Z nota")
    [ "$r" = "$(printf 'po 20261010T0301Z\ndev 20261010T1501Z\nILEGIBLE revisor 2026101\nqa 20261013T0302Z')" ] || det="$det parseo de turnos: '$(echo "$r" | tr '\n' ';')';"
    (cd "$clon" && git checkout -q claude/equipo-dev/backlog 2>/dev/null || git checkout -q -b claude/equipo-dev/backlog origin/claude/equipo-dev/backlog) \
        && (cd "$clon" && touch docs/backlog/SIN_MERGE && git add -A && git commit -qm veto && git push -q origin HEAD:claude/equipo-dev/backlog && git fetch -q origin) >/dev/null 2>&1
    pu claude/equipo-dev/44-aprobada --solo a | grep -q '^PUERTA a FALLA: SIN_MERGE' || det="$det SIN_MERGE no frena a;"
    (cd "$clon" && git rm -q docs/backlog/SIN_MERGE && git commit -qm "levanta veto" && git push -q origin HEAD:claude/equipo-dev/backlog && git checkout -q main && git fetch -q origin) >/dev/null 2>&1
    l1=$(bash "$es_s/puerta.sh" --rutas-del-humano | tr '\n' ' ')
    l2=$(grep -m1 '^RUTAS_DEL_HUMANO=' "$es_s/estado.sh" | cut -d'"' -f2)
    [ "$l1" = "$l2 " ] || det="$det RUTAS_DEL_HUMANO distinta en puerta.sh y estado.sh;"
    cierra puerta "$det"

    # 13. pulso.sh: arranque y cierre en backlog sin tocar el checkout, el
    # tablero que conserva `## Para el equipo`, PAUSA, reintento tras un push
    # rechazado y la diferencia entre disparo perdido y sesion muerta.
    det=""
    t0=$(date -u -d 2026-10-13T03:02:00Z +%s)
    envs() { printf 'export EQUIPO_ROL=%s\nexport EQUIPO_ROLES=%s\nexport EQUIPO_SESION=%s\nexport EQUIPO_MOTIVO="por estado: prueba"\nexport EQUIPO_RELOJ=po\nexport EQUIPO_FRANJA=1\nexport EQUIPO_REF=origin/main\n' "$1" "$2" "$3" > "$clon/.git/equipo-dev.env"; }
    pl() { (cd "$clon" && GIT_AUTHOR_DATE="@$1 +0000" GIT_COMMITTER_DATE="@$1 +0000" EQUIPO_AHORA=$1 bash "$es_s/pulso.sh" "${@:2}" 2>&1 | tail -1); }
    envs dev dev 20261013T0302Z
    antes=$(git -C "$clon" rev-parse HEAD)
    r=$(pl "$t0" arranque); case "$r" in "PULSO_OK "*) ;; *) det="$det arranque: '$r';" ;; esac
    [ "$(git -C "$clon" rev-parse HEAD)" = "$antes" ] && [ -z "$(git -C "$clon" status --porcelain --untracked-files=no)" ] || det="$det el arranque toco el checkout;"
    git -C "$sint/remoto.git" show claude/equipo-dev/backlog:docs/backlog/PULSO.md 2>/dev/null | grep -q '^2026-10-13T03:02Z 20261013T0302Z arranque dev | por estado: prueba' || det="$det sin linea de arranque en PULSO.md;"
    git -C "$sint/remoto.git" show claude/equipo-dev/backlog:docs/backlog/.gitattributes 2>/dev/null | grep -qx 'PULSO.md merge=union' || det="$det sin merge=union;"
    r=$(cd "$clon" && EQUIPO_AHORA=$AHORA_S bash "$es_s/estado.sh" 2>/dev/null | grep '^PULSO=')
    [ "$r" = "PULSO=48 h: 0 con cierre, 1 murieron (10-13T03:01Z), 1 perdidos (10-13T06:01Z)" ] || det="$det clasificacion de disparos: '$r';"
    # Un push rechazado una vez (hook del remoto) se reintenta desde origin.
    printf '#!/bin/sh\n[ -f "%s/rechazado" ] && exit 0\ntouch "%s/rechazado"; echo rechazado; exit 1\n' "$sint" "$sint" > "$sint/remoto.git/hooks/pre-receive"
    chmod +x "$sint/remoto.git/hooks/pre-receive"
    r=$(pl $((t0 + 2280)) cierre --resultado nada --turno "Prueba el cierre" --humano "Pedido nuevo de prueba")
    case "$r" in "CIERRE_OK "*) ;; *) det="$det cierre con un rechazo: '$r';" ;; esac
    [ -f "$sint/rechazado" ] || det="$det el hook de rechazo no corrio;"
    rm -f "$sint/remoto.git/hooks/pre-receive"
    e=$(git -C "$sint/remoto.git" show claude/equipo-dev/backlog:docs/backlog/ESTADO.md 2>/dev/null)
    printf '%s\n' "$e" | sed -n '/^## Para el equipo/,$p' | grep -qx 'Pedido de prueba del humano: no borrar esta linea.' || det="$det el tablero perdio Para el equipo;"
    printf '%s\n' "$e" | grep -qE '^- H[0-9]+ \(desde 2026-10-13\): Pedido nuevo de prueba$' || det="$det el tablero no agrega el pedido;"
    printf '%s\n' "$e" | grep -qE '^\| dev \| 2026-10-13 03:40 \| Prueba el cierre \|$' || det="$det el tablero no anota el turno;"
    printf '%s\n' "$e" | grep -q '^RESUMEN propuesto=2 ' || det="$det el tablero no trae RESUMEN;"
    r=$(cd "$clon" && EQUIPO_AHORA=$AHORA_S bash "$es_s/estado.sh" 2>/dev/null | grep '^PULSO=')
    [ "$r" = "PULSO=48 h: 1 con cierre, 0 murieron, 1 perdidos (10-13T06:01Z)" ] || det="$det clasificacion tras el cierre: '$r';"
    # Un tablero que pierde `## Para el equipo` no se escribe.
    mal=$(mktemp -d); cp "$es_s"/*.sh "$mal/"
    printf '#!/bin/sh\necho "# Estado del equipo de desarrollo autonomo"\necho "## Para el equipo"\necho otra cosa\n' > "$mal/estado.sh"
    previo=$(git -C "$sint/remoto.git" rev-parse claude/equipo-dev/backlog)
    r=$(cd "$clon" && EQUIPO_AHORA=$AHORA_S bash "$mal/pulso.sh" cierre --resultado nada --turno x 2>&1 | tail -1)
    case "$r" in "PULSO_FALLA: el tablero no conserva"*) ;; *) det="$det un tablero sin Para el equipo se escribio: '$r';" ;; esac
    [ "$(git -C "$sint/remoto.git" rev-parse claude/equipo-dev/backlog)" = "$previo" ] || det="$det hubo push con el tablero roto;"
    rm -rf "$mal"
    # Con PAUSA no se escribe nada (P1).
    (cd "$clon" && git checkout -q claude/equipo-dev/backlog && git pull -q --ff-only origin claude/equipo-dev/backlog && touch docs/backlog/PAUSA && git add -A && git commit -qm pausa && git push -q origin HEAD:claude/equipo-dev/backlog && git checkout -q main) >/dev/null 2>&1
    previo=$(git -C "$sint/remoto.git" rev-parse claude/equipo-dev/backlog)
    r=$(pl $((t0 + 3000)) arranque)
    [ "$r" = PULSO_PAUSA ] && [ "$(git -C "$sint/remoto.git" rev-parse claude/equipo-dev/backlog)" = "$previo" ] || det="$det con PAUSA escribio: '$r';"
    cierra pulso "$det"

    # 14. fichas.sh: el escenario esta limpio; cada defecto inyectado en una
    # copia local cae con su motivo, y estado.sh lo lleva a la salud del loop.
    det=""
    r=$(cd "$clon" && bash "$es_s/fichas.sh" 2>&1 | tail -1)
    [ "$r" = "FICHAS_OK (12)" ] || det="$det escenario: '$r';"
    fx=$(mktemp -d)
    git -C "$clon" show origin/claude/equipo-dev/44-aprobada:docs/backlog/44-aprobada.md > "$fx/44-aprobada.md"
    r=$(cd "$clon" && bash "$es_s/fichas.sh" "$fx/44-aprobada.md" | tail -1)
    [ "$r" = "FICHAS_OK (1)" ] || det="$det la ficha buena falla: '$r';"
    defecto() { # nombre sed motivo-esperado
        cp "$fx/44-aprobada.md" "$fx/44-$1.md"
        sed -i "$2" "$fx/44-$1.md"
        (cd "$clon" && bash "$es_s/fichas.sh" "$fx/44-$1.md") | grep -qF -- "$3" || det="$det no ve $1;"
    }
    defecto estado 's/^estado: .*/estado: aprobada/' "estado 'aprobada' fuera del vocabulario"
    defecto candado 's/^candado: .*/candado: qa/' "candado 'qa'"
    defecto turnos 's/^turnos: .*/turnos: dev 20261011T0902Z, revisor ayer/' "turnos ilegibles: revisor ayer"
    defecto tipo 's/^tipo: .*/tipo: mejora/' "tipo 'mejora'"
    defecto qa '/^## QA/,$d' "aprobado sin '## QA'"
    defecto criterios 's/^estado: .*/estado: propuesto/; /^- \[ \] tres/d' "2 criterios de aceptacion (van 3 a 6)"
    defecto rama 's/^rama: .*/rama: claude\/otra/' "rama 'claude/otra'"
    defecto titulo '1s/.*/# 45. Otro numero/' "el titulo no es '# 44. ...'"
    r=$(cd "$clon" && bash "$es_s/fichas.sh" --alcance | tail -1)
    [ "$r" = "ALCANCE_OK (3)" ] || det="$det ALCANCE del escenario: '$r';"
    git -C "$clon" show origin/claude/equipo-dev/backlog:docs/backlog/ALCANCE.md | sed 's/| S | idea |$/| S | lista |/' > "$fx/ALCANCE.md"
    (cd "$clon" && bash "$es_s/fichas.sh" --alcance "$fx/ALCANCE.md") | grep -q "^ALCANCE_MAL Z1: estado 'lista' fuera del vocabulario" || det="$det ALCANCE con estado raro pasa;"
    (cd "$clon" && git checkout -q claude/equipo-dev/backlog && git pull -q --ff-only origin claude/equipo-dev/backlog \
        && git rm -q docs/backlog/PAUSA && cp "$fx/44-estado.md" docs/backlog/52-mal-escrita.md && sed -i '1s/.*/# 52. Mal escrita/' docs/backlog/52-mal-escrita.md \
        && git add -A && git commit -qm "ficha mal" && git push -q origin HEAD:claude/equipo-dev/backlog && git checkout -q main) >/dev/null 2>&1
    (cd "$clon" && EQUIPO_AHORA=$AHORA_S bash "$es_s/estado.sh" 2>/dev/null) | grep -q '^SALUD_FICHAS_MAL=1 de 13' || det="$det estado.sh no lleva la ficha mal a la salud;"
    rm -rf "$fx"
    cierra fichas "$det"

    # 16. turno.sh de verdad (no simulado) en el clon: instala la guardia
    # pre-push y escribe el arranque a traves de ella; la guardia deja pasar
    # lo del equipo y frena main, el playbook, otras ramas y borrados ajenos,
    # escriba como se escriba el destino; fuera de un turno no hace nada.
    det=""
    rm -f "$clon/.git/equipo-dev.env"
    sal=$(cd "$clon" && bash "$es_s/turno.sh" 2>&1)
    printf '%s\n' "$sal" | grep -q '^# guardia: pre-push del equipo instalado' || det="$det turno.sh no instalo la guardia;"
    printf '%s\n' "$sal" | grep -q '^# pulso: PULSO_OK ' || det="$det el arranque no paso por la guardia: '$(printf '%s\n' "$sal" | grep '^# pulso' | head -1)';"
    printf '%s\n' "$sal" | grep -qE '^# leer: git show origin/main:.claude/skills/equipo-dev/roles/[a-z]+\.md$' || det="$det sin linea # leer;"
    empuja() { (cd "$clon" && git push -q "$@" >/dev/null 2>&1); }
    # un commit nuevo: empujar algo que el remoto ya tiene no llama al hook
    (cd "$clon" && git checkout -q --detach && git commit -q --allow-empty -m "prueba de guardia") >/dev/null 2>&1
    empuja origin HEAD:refs/heads/claude/equipo-dev/60-nueva || det="$det frena una rama de trabajo;"
    empuja --dry-run origin HEAD:refs/heads/claude/equipo-dev/prueba-acceso || det="$det frena la prueba de acceso;"
    empuja origin --delete claude/equipo-dev/60-nueva || det="$det frena el borrado de una rama de trabajo;"
    empuja origin HEAD:main && det="$det deja empujar a main;"
    empuja origin HEAD:refs/heads/main && det="$det deja empujar a refs/heads/main;"
    empuja origin +HEAD:refs/heads/claude/equipo-dev/playbook && det="$det deja empujar al playbook;"
    empuja origin HEAD:refs/heads/otra && det="$det deja empujar a otra rama;"
    empuja origin --delete claude/equipo-dev/backlog && det="$det deja borrar backlog;"
    empuja origin HEAD:refs/tags/v9.9.9 && det="$det deja empujar un tag;"
    sed -i 's/^export EQUIPO_INICIO=.*/export EQUIPO_INICIO=1/' "$clon/.git/equipo-dev.env"
    empuja origin HEAD:refs/heads/otra-fuera-de-turno || det="$det frena fuera de turno (env de hace mas de 4 h);"
    rm -f "$clon/.git/equipo-dev.env"
    empuja origin HEAD:refs/heads/otra-sin-env || det="$det frena sin equipo-dev.env;"
    printf '#!/bin/sh\nexit 0\n' > "$clon/.git/hooks/pre-push"
    (cd "$clon" && EQUIPO_SIN_PULSO=1 bash "$es_s/turno.sh" 2>&1) | grep -q '^# guardia: ya hay otro pre-push' || det="$det pisa un pre-push ajeno;"
    grep -q 'equipo-dev pre-push' "$clon/.git/hooks/pre-push" && det="$det el pre-push ajeno quedo reemplazado;"
    cierra guardia "$det"
fi
rm -rf "$sint"

# 15. herramientas de QA: cada una trae una --autoprueba que inyecta la
# violacion que dice detectar (una vista que revienta, un listener roto, un
# mutante vivo, una cita a un comando que no existe, un 500 en la pagina).
# Corren sobre el checkout; si falta lo que necesitan (django, zstandard,
# Chromium o el build) se dice cual y se salta, nunca se da por buena.
det=""; saltadas=""
auto() { # nombre comando...
    local n=$1 r; shift
    r=$("$@" 2>&1 | grep -E '^AUTOPRUEBA_' | tail -1)
    case "$r" in AUTOPRUEBA_OK*) ;; *) det="$det $n: '${r:-sin AUTOPRUEBA_}';" ;; esac
}
auto deriva-docs bash "$es_s/deriva-docs.sh" --autoprueba
auto mutar python3 "$es_s/mutar.py" --autoprueba
if python3 -c 'import zstandard' 2>/dev/null; then auto fuzz_parser python3 "$es_s/fuzz_parser.py" --autoprueba; else saltadas="$saltadas fuzz_parser(sin zstandard)"; fi
if python3 -c 'import django, zstandard' 2>/dev/null; then auto barrido_api python3 "$es_s/barrido_api.py" --autoprueba; else saltadas="$saltadas barrido_api(sin django)"; fi
if [ -d frontend/node_modules ] && [ -f frontend/dist/index.html ] \
    && ls -d "${PLAYWRIGHT_BROWSERS_PATH:-${HOME:-}/.cache/ms-playwright}"/chromium-* >/dev/null 2>&1 \
    && python3 -c 'import django' 2>/dev/null; then
    auto qa-paginas node "$es_s/qa-paginas.mjs" --autoprueba
else
    saltadas="$saltadas qa-paginas(sin build, node_modules o Chromium)"
fi
if [ -n "$det" ]; then falla herramientas "$det"
elif [ -n "$saltadas" ]; then ok "herramientas (saltadas:$saltadas)"
else ok herramientas
fi

if [ "$fallos" -gt 0 ]; then echo "PRUEBAS_FALLAN: $fallos"; exit 1; fi
echo "PRUEBAS_OK ($n)"
