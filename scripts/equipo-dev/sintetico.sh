#!/usr/bin/env bash
# Arma un remoto bare con ramas sinteticas del equipo y un clon con origin
# apuntando a el, para probar estado.sh, puerta.sh, pulso.sh y fichas.sh de
# punta a punta sin tocar el remoto real (M5 de MAQUINARIA.md). Lo usa
# pruebas.sh; no escribe nada fuera de <dir>.
#
# Uso:  sintetico.sh <dir> <base>
#   <base> es el arbol con los scripts y el playbook que se prueban: main del
#   remoto sintetico los trae, asi la cadena de turno.sh lo encuentra.
# Imprime `AHORA=<epoch> CLON=<ruta> REMOTO=<ruta>`; el clon queda en main.
#
# El escenario fija lo que pruebas.sh afirma (si cambias algo aca, cambian los
# numeros esperados de alla):
#   backlog: 40 propuesto funcionalidad, 41 disenado tests, 42 propuesto bug
#            prioridad 1, ALCANCE.md con 2 ideas libres, ESTADO.md con texto
#            del humano en `## Para el equipo`.
#   ramas:   43 implementado funcionalidad; 44 aprobado limpio (turnos dev S1,
#            revisor S2, qa S3); 45 y 46 entregado (PR pendiente de merge: ...);
#            47 implementado que toca scripts/equipo-dev/; 48 en curso con
#            candado muerto; 49 aprobado con dev y revisor en la misma sesion;
#            50 aprobado con un commit humano sin respuesta y una pregunta
#            abierta; 51 mergeada por squash (borrable, no cuenta).
set -eu
dir=$1; base=$2
mkdir -p "$dir"
dir=$(cd "$dir" && pwd)
remoto=$dir/remoto.git
clon=$dir/clon
AHORA=$(date -u -d 2026-10-13T12:00:00Z +%s)
git init -q --bare -b main "$remoto"
git init -q -b main "$clon"
cd "$clon"
git config user.name Claude
git config user.email noreply@anthropic.com
git config commit.gpgsign false
# Un push.negotiate global ensucia la salida contra un remoto local.
git config push.negotiate false
git remote add origin "$remoto"

# hace un commit con fecha `hace` segundos antes de AHORA y autor opcional
commit() { # mensaje hace [autor]
    local cuando=$(( AHORA - $2 )) autor=${3:-Claude}
    GIT_AUTHOR_DATE="@$cuando +0000" GIT_COMMITTER_DATE="@$cuando +0000" \
        git -c user.name="$autor" commit -q --allow-empty -m "$1"
}
ficha() { # ruta numero estado tipo prioridad turnos [candado]
    mkdir -p "$(dirname "$1")"
    cat > "$1" <<EOF
# $2. Ficha sintetica $2

estado: $3
candado: ${7:--}
rama: claude/equipo-dev/$(basename "$1" .md)
tipo: $4
epica: -
area: backend
prioridad: $5
fuente: escenario de sintetico.sh
archivos: backend/x.py
turnos: $6

## Que gana quien usa la app

Algo que se ve.

## Criterios de aceptacion

- [ ] uno
- [ ] dos
- [ ] tres

## Fuera de alcance

Nada.
EOF
    # Las secciones que cada etapa deja, para que fichas.sh las vea completas.
    case "$3" in entregado*) printf '\n## PR\n\nTitulo: `[equipo-dev][backend] Ficha %s`\n' "$2" >> "$1" ;; esac
    case "$3" in disenado*|"en curso"*|implementado*|revisado*|"con hallazgos"*|aprobado*|entregado*) printf '\n## Diseno\n\nArchivos: backend/x.py.\n' >> "$1" ;; esac
    case "$3" in implementado*|revisado*|aprobado*|entregado*) printf '\n## Implementacion\n\nTal cual el diseno.\n' >> "$1" ;; esac
    case "$3" in revisado*|aprobado*|entregado*) printf '\n## Revision 2026-10-12 sobre abc1234\n\nVeredicto: aprobar.\n' >> "$1" ;; esac
    case "$3" in aprobado*|entregado*) printf '\n## QA 2026-10-12 sobre abc1234\n\nVeredicto: aprobado.\n' >> "$1" ;; esac
}

# main: el playbook bajo prueba
(cd "$base" && tar cf - .claude scripts docs/backlog 2>/dev/null) | tar xf -
rm -f docs/backlog/[0-9]*-*.md
echo "repo sintetico" > README.md
git add -A
commit "Base sintetica" 720000
git push -q origin main

# backlog
git checkout -q -b claude/equipo-dev/backlog
ficha docs/backlog/40-propuesta-func.md 40 propuesto funcionalidad 3 "po 20261012T0301Z"
ficha docs/backlog/41-disenada-tests.md 41 disenado tests 3 "po 20261012T0301Z, arquitecto 20261012T0602Z"
ficha docs/backlog/42-bug-grave.md 42 propuesto bug 1 "po 20261013T0301Z"
cat > docs/backlog/ALCANCE.md <<'EOF'
# Alcance

### demo: demo

| id | idea | que gana quien usa la app | datos | tam | estado |
|---|---|---|---|---|---|
| Z1 | Una | algo | `x.py` | S | idea |
| Z2 | Otra | algo | `y.py` | S | idea |
| Z3 | Tomada | algo | `z.py` | S | ficha 40 |
EOF
cat > docs/backlog/ESTADO.md <<'EOF'
# Estado del equipo de desarrollo autonomo

actualizado: 2026-10-12 21:05 UTC por dev (sesion 20261012T2101Z)

## Ultimo turno de cada rol

| rol | fecha-hora UTC | que hizo |
|---|---|---|
| dev | 2026-10-12 21:01 | Implementa algo. |
| qa | 2026-10-12 18:02 | Prueba algo. |

## Para el humano

- Ramas borrables (ya mergeadas o sin codigo): `git push origin --delete x`
- Preguntas abiertas:
  - **Bug en round_end:** decidir cual manda.
  - ~~Resuelta~~: ya no.
- Verificar en el PC: correr recompute.
- CI remota: aviso unico.

## Para el equipo

(Escribe aca el humano. El equipo no borra ni edita este bloque; responde debajo con fecha.)

Pedido de prueba del humano: no borrar esta linea.
EOF
git add -A
commit "Crea la rama backlog" 100000
# Rastros de turnos: commits de ESTADO.md a las 21:05 del 12 y a las 09:04 del 13
echo >> docs/backlog/ESTADO.md; git add -A; commit "Estado: turno dev 20261012T2101Z" $(( AHORA - $(date -u -d 2026-10-12T21:05:00Z +%s) ))
echo >> docs/backlog/ESTADO.md; git add -A; commit "Estado: turno dev 20261013T0902Z" $(( AHORA - $(date -u -d 2026-10-13T09:04:00Z +%s) ))
git push -q origin claude/equipo-dev/backlog

rama() { # numero slug estado tipo turnos hace [candado]
    git checkout -q -b "claude/equipo-dev/$1-$2" main
    ficha "docs/backlog/$1-$2.md" "$1" "$3" "$4" 3 "$5" "${7:--}"
    mkdir -p backend; echo "x = $1" > "backend/m$1.py"
    git add -A
    commit "Implementa: $1" "$6"
}
H=3600
# 51 va primero: el squash mueve main, y las demas ramas nacen despues de el
# (asi la condicion f de la puerta ve main fusionado).
# 51: mergeada por squash en main, la rama sigue viva
rama 51 squash implementado tests "dev 20261011T0902Z" $((30*H))
git push -q origin claude/equipo-dev/51-squash
git checkout -q main
git merge -q --squash claude/equipo-dev/51-squash >/dev/null
commit "Squash de 51" $((20*H))
git push -q origin main

rama 43 implementada implementado funcionalidad "po 20261012T0301Z, arquitecto 20261012T0602Z, dev 20261012T0902Z" $((2*H))
git push -q origin claude/equipo-dev/43-implementada

rama 44 aprobada revisado funcionalidad "po 20261011T0301Z, dev 20261011T0902Z, revisor 20261011T1202Z" $((6*H))
sed -i 's/^estado: .*/estado: aprobado/; s/^turnos: .*/turnos: po 20261011T0301Z, dev 20261011T0902Z, revisor 20261011T1202Z (relevo de qa, sin apuro), qa 20261011T1802Z/' docs/backlog/44-aprobada.md
printf '\n## QA 2026-10-13 sobre abc1234\n\nVeredicto: aprobado.\n' >> docs/backlog/44-aprobada.md
git add -A; commit "Prueba: 44" $((4*H))
git push -q origin claude/equipo-dev/44-aprobada

rama 45 espera-uno "entregado (PR pendiente de merge: toca .claude)" funcionalidad "dev 20261010T0902Z, revisor 20261010T1202Z, qa 20261010T1802Z" $((60*H))
git push -q origin claude/equipo-dev/45-espera-uno
rama 46 espera-dos "entregado (PR pendiente de merge: sin herramientas)" bug "dev 20261010T0902Z, revisor 20261010T1202Z, qa 20261010T1802Z" $((50*H))
git push -q origin claude/equipo-dev/46-espera-dos

rama 47 toca-playbook implementado deuda "dev 20261013T0902Z" $((1*H))
echo "# cambio" >> scripts/equipo-dev/turno.sh; git add -A; commit "Toca el playbook" $((1*H))
git push -q origin claude/equipo-dev/47-toca-playbook

rama 48 huerfana "en curso 2026-10-12" funcionalidad "dev 20261012T0902Z" $((10*H)) "dev 2026-10-12 09:02"
git push -q origin claude/equipo-dev/48-huerfana

rama 49 misma-sesion aprobado funcionalidad "dev 20261012T0902Z, revisor 20261012T0902Z, qa 20261012T1802Z" $((5*H))
git push -q origin claude/equipo-dev/49-misma-sesion

rama 50 humano aprobado funcionalidad "dev 20261011T0902Z, revisor 20261011T1202Z, qa 20261011T1802Z" $((8*H))
printf '\n## Para el humano\n\n¿Mostramos el numero con un decimal o con dos?\n' >> docs/backlog/50-humano.md
git add -A; commit "Prueba: 50" $((7*H))
echo "y = 1" > backend/humano.py; git add -A; commit "Un cambio del humano" $((6*H)) Benjamin
git push -q origin claude/equipo-dev/50-humano

git checkout -q main
git fetch -q origin main '+refs/heads/claude/*:refs/remotes/origin/claude/*'
echo "AHORA=$AHORA CLON=$clon REMOTO=$remoto"
