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
tu=$base/scripts/equipo-dev/turno.sh
es=$base/scripts/equipo-dev/estado.sh
bl=$base/docs/backlog

n=0; fallos=0
ok() { n=$((n + 1)); echo "OK $1"; }
falla() { n=$((n + 1)); fallos=$((fallos + 1)); echo "FALLA $1:$2"; }
cierra() { if [ -z "$2" ]; then ok "$1"; else falla "$1" "$2"; fi; }

# 1. sintaxis
det=""
for s in scripts/equipo-dev/turno.sh scripts/equipo-dev/estado.sh scripts/equipo-dev/pruebas.sh scripts/check.sh .claude/hooks/session-start.sh; do
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
for t in 'ci.yml' 'hoy:' '90 minutos' '#11' 'great-'"cray" 'titulo del PR como mensaje' 'Corre cada 3 horas'; do grep -qF -- "$t" "$sk" 2>/dev/null && det="$det '$t'"; done
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

# 11. resumen: contra el remoto real, la linea existe y trae los 20 pares en
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
    for k in CADENCIA ROTACION_EPICAS ROTACION_PAGINAS ROTACION CICLO PARA_EL_HUMANO RELEASE DEV_7D; do
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
for f in "$sk" "$ru" "$tu" "$es" $base/.claude/skills/equipo-dev/revision.md $base/.claude/skills/equipo-dev/plantilla-pr.md $base/.claude/skills/equipo-dev/arena.md $base/.claude/skills/equipo-dev/replica.md $base/.claude/skills/equipo-dev/skills.md "$bl/ESTADO.plantilla.md" "$bl/README.md"; do
    [ -f "$f" ] || continue
    m=$(grep -nE 'origin/main|compare/main\.\.\.' "$f" | grep -vF -- "$cadena" | grep -v 'RELEASE' | cut -d: -f1 | tr '\n' ',')
    [ -z "$m" ] || det="$det ${f#$base/} nombra main fuera de la cadena y de RELEASE (lineas ${m%,});"
    m=$(grep -nE 'git fetch( -q)? origin ' "$f" | grep -v 'origin dev' | cut -d: -f1 | tr '\n' ',')
    [ -z "$m" ] || det="$det ${f#$base/} hace git fetch sin dev (lineas ${m%,});"
done
grep -qE 'abierto contra `dev`' "$sk" 2>/dev/null || det="$det SKILL.md: la puerta de merge no pide el PR contra dev;"
cierra base "$det"

if [ "$fallos" -gt 0 ]; then echo "PRUEBAS_FALLAN: $fallos"; exit 1; fi
echo "PRUEBAS_OK ($n)"
