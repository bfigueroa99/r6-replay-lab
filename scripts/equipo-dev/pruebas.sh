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
done <<< "$(cat "${playbook[@]}" "$ru" 2>/dev/null | grep -oE '`(roles/[a-z<>]+\.md|alcance\.md)`' | tr -d '`' | sort -u)"
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
for f in "${playbook[@]}" "$ru" "$tu" "$es" $base/.claude/skills/equipo-dev/revision.md $base/.claude/skills/equipo-dev/plantilla-pr.md $base/.claude/skills/equipo-dev/arena.md $base/.claude/skills/equipo-dev/replica.md $base/.claude/skills/equipo-dev/skills.md "$bl/ESTADO.plantilla.md" "$bl/README.md"; do
    [ -f "$f" ] || continue
    m=$(grep -nE 'origin/main|compare/main\.\.\.' "$f" | grep -vF -- "$cadena" | grep -v 'RELEASE' | cut -d: -f1 | tr '\n' ',')
    [ -z "$m" ] || det="$det ${f#$base/} nombra main fuera de la cadena y de RELEASE (lineas ${m%,});"
    m=$(grep -nE 'git fetch( -q)? origin ' "$f" | grep -v 'origin dev' | cut -d: -f1 | tr '\n' ',')
    [ -z "$m" ] || det="$det ${f#$base/} hace git fetch sin dev (lineas ${m%,});"
done
grep -qE 'abierto contra `dev`' "$ro/release.md" 2>/dev/null || det="$det roles/release.md: la puerta de merge no pide el PR contra dev;"
cierra base "$det"

if [ "$fallos" -gt 0 ]; then echo "PRUEBAS_FALLAN: $fallos"; exit 1; fi
echo "PRUEBAS_OK ($n)"
