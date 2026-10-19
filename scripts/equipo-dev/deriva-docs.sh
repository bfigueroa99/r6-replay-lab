#!/usr/bin/env bash
# Deriva de docs (M9 de MAQUINARIA.md): lo que los documentos citan contra lo
# que el codigo tiene. QA lo hacia a mano en sus turnos sin trabajo, cada vez
# distinto. Mira:
#   - `manage.py <comando>`: existe en replays/management/commands o es de Django;
#   - `scripts/<archivo>` (tambien `.\scripts\<archivo>`): existe;
#   - `/api/<ruta>/`: alguna ruta de replays/urls.py la acepta;
#   - `npm run <script>`: esta en frontend/package.json;
#   - variables de .env.example: el backend las lee;
#   - cifras de tests escritas a mano (`306 tests`): se pudren con cada ficha.
# Uso:  deriva-docs.sh [archivo.md ...]   (por defecto README.md, CLAUDE.md y docs/*.md menos roadmap)
#       deriva-docs.sh --autoprueba       (inyecta una de cada y verifica que las vea)
#       git show <ref>:scripts/equipo-dev/deriva-docs.sh | bash -s -- [...]
# Una linea `DERIVA <archivo>:<linea>: <que>` por hallazgo y al final
# `DERIVA_OK (<n> referencias)` (salida 0) o `DERIVA_FALLA: <k>` (salida 1).
set -u
repo="$(git rev-parse --show-toplevel 2>/dev/null)" || { echo "no es un repo git" >&2; exit 2; }
cd "$repo"

if [ "${1:-}" = --autoprueba ]; then
    tmp=$(mktemp -d); trap 'rm -rf "$tmp"' EXIT
    cat > "$tmp/falso.md" <<'EOF'
Corre `python manage.py importar_todo` y despues `.\scripts\no-existe.ps1`.
La API tiene `/api/inventada/` y `npm run despegar`.
Son 999 tests en verde.
Esto si existe: `manage.py seed_demo`, `/api/players/<id>/ubisoft/`, `npm run e2e`.
EOF
    # Corrido por `git show | bash` no hay archivo propio: se trae de la misma ref.
    yo="${BASH_SOURCE[0]:-}"
    if [ ! -f "$yo" ]; then yo="$tmp/deriva.sh"; git show "${EQUIPO_REF:-origin/main}:scripts/equipo-dev/deriva-docs.sh" > "$yo"; fi
    salida=$(bash "$yo" "$tmp/falso.md" 2>&1)
    n=$(printf '%s\n' "$salida" | grep -c '^DERIVA ')
    if [ "$n" -eq 5 ] && printf '%s\n' "$salida" | grep -q '^DERIVA_FALLA: 5'; then
        echo "AUTOPRUEBA_OK: ve las 5 derivas inyectadas y no marca las 3 citas buenas"; exit 0
    fi
    echo "AUTOPRUEBA_FALLA: vio $n de 5"; printf '%s\n' "$salida"; exit 1
fi

if [ $# -gt 0 ]; then docs=("$@"); else
    docs=(README.md CLAUDE.md)
    for f in docs/*.md; do [ "$f" = docs/roadmap.md ] || docs+=("$f"); done
fi
DJANGO="runserver migrate makemigrations test shell createsuperuser check dbshell collectstatic showmigrations sqlmigrate flush dumpdata loaddata changepassword"
comandos=$(ls backend/replays/management/commands/*.py 2>/dev/null | xargs -n1 basename | sed 's/\.py$//' | grep -v '^__')
npm_scripts=$(python3 -c "import json; print(' '.join(json.load(open('frontend/package.json'))['scripts']))" 2>/dev/null)
# rutas de urls.py como regex: <int:pk> y compania son un segmento cualquiera
rutas=$(grep -oE 'path\("[^"]*"' backend/replays/urls.py | sed -E 's/^path\("//; s/"$//; s/<[^>]+>/[^\/]+/g')

n=0; malas=0
deriva() { malas=$((malas + 1)); echo "DERIVA $1: $2"; }
for doc in "${docs[@]}"; do
    [ -f "$doc" ] || continue
    nl=0
    while IFS= read -r linea; do
        nl=$((nl + 1))
        donde="$doc:$nl"
        for c in $(printf '%s' "$linea" | grep -oE 'manage\.py [a-z_]+' | awk '{print $2}'); do
            n=$((n + 1))
            case " $DJANGO " in *" $c "*) continue ;; esac
            printf '%s\n' "$comandos" | grep -qx "$c" || deriva "$donde" "manage.py $c no existe"
        done
        for s in $(printf '%s' "$linea" | grep -oE '(\.\\|\./)?scripts[\\/][A-Za-z0-9_./\\-]+\.(ps1|sh|py|mjs)' | tr '\\' '/' | sed 's#^\./##'); do
            n=$((n + 1))
            [ -e "$s" ] || deriva "$donde" "$s no existe"
        done
        for a in $(printf '%s' "$linea" | grep -oE '/api/[A-Za-z0-9_<>:./-]*' | sed 's#^/api/##'); do
            n=$((n + 1))
            a=${a%%\?*}; [ -n "$a" ] || continue
            case "$a" in */) ;; *) a="$a/" ;; esac
            norm=$(printf '%s' "$a" | sed -E 's/<[^>]+>/X/g; s#/[0-9]+/#/X/#g')
            ok=no
            while IFS= read -r r; do
                [ -n "$r" ] || continue
                printf '%s' "$norm" | grep -qE "^${r}\$" && { ok=si; break; }
            done <<< "$rutas"
            [ "$ok" = si ] || deriva "$donde" "/api/$a no esta en replays/urls.py"
        done
        for s in $(printf '%s' "$linea" | grep -oE 'npm run [a-z0-9:_-]+' | awk '{print $3}'); do
            n=$((n + 1))
            case " $npm_scripts " in *" $s "*) ;; *) deriva "$donde" "npm run $s no esta en frontend/package.json" ;; esac
        done
        # Una cifra de tests escrita a mano cambia con cada ficha y nadie la vigila.
        if printf '%s' "$linea" | grep -qE '\b[0-9]{3,} tests\b'; then
            n=$((n + 1)); deriva "$donde" "cifra de tests escrita a mano ($(printf '%s' "$linea" | grep -oE '\b[0-9]{3,} tests\b' | head -1)): se pudre con cada ficha"
        fi
    done < "$doc"
done
# Variables de .env.example que nadie lee: la doc promete un ajuste que no existe.
if [ $# -eq 0 ] && [ -f .env.example ]; then
    nl=0
    while IFS= read -r linea; do
        nl=$((nl + 1))
        v=$(printf '%s' "$linea" | sed -nE 's/^#? ?([A-Z][A-Z0-9_]+)=.*/\1/p')
        [ -n "$v" ] || continue
        n=$((n + 1))
        grep -rqF -- "$v" backend --include=*.py || deriva ".env.example:$nl" "$v no lo lee ningun .py del backend"
    done < .env.example
fi
if [ "$malas" -gt 0 ]; then echo "DERIVA_FALLA: $malas"; exit 1; fi
echo "DERIVA_OK ($n referencias)"
exit 0
