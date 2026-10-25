#!/usr/bin/env bash
# equipo-dev pre-push: guardia de ramas para los turnos del equipo (M11).
#
# Hasta aca nada tecnico impedia que un turno empujara a `main` o a la rama
# del playbook: solo lo prohibia el texto. Acotar `Bash(git push:*)` en
# .claude/settings.json no alcanza, porque un prefijo de comando no ve el
# destino real (`git push origin HEAD:refs/heads/main`, `+main`, `--all`
# pasan igual) y una regla mal escrita trabaria al equipo entero sin nadie
# para aprobar. Un hook pre-push si lo ve: git le pasa cada ref de destino ya
# resuelta (`refs/heads/...`), escriba como se escriba el comando.
#
# turno.sh lo instala en .git/hooks/pre-push al arrancar un turno. Solo actua
# si .git/equipo-dev.env existe y el turno arranco hace menos de 4 horas: en
# cualquier otra sesion (la del dueno, el PC del humano otro dia) no hace nada.
# Deja pasar: refs/heads/claude/equipo-dev/* salvo la del playbook, y el
# borrado de una rama de trabajo (claude/equipo-dev/NN-...). Rechaza todo lo
# demas (main, playbook, otras ramas, tags) con el motivo.
set -u
gitdir=$(git rev-parse --git-dir 2>/dev/null) || exit 0
env_file="$gitdir/equipo-dev.env"
[ -f "$env_file" ] || exit 0
inicio=$(sed -n 's/^export EQUIPO_INICIO=\([0-9][0-9]*\)$/\1/p' "$env_file" | head -1)
[ -n "$inicio" ] || exit 0
ahora=${EQUIPO_AHORA:-$(date -u +%s)}
[ $(( ahora - inicio )) -lt 14400 ] || exit 0

malo=""
while read -r local_ref local_sha remote_ref remote_sha; do
    [ -n "${remote_ref:-}" ] || continue
    case "$remote_ref" in
        refs/heads/claude/equipo-dev/playbook|refs/heads/claude/equipo-dev/playbook[-/]*)
            malo="$malo $remote_ref (la rama del playbook la mueve el humano)" ;;
        refs/heads/claude/equipo-dev/*)
            # borrar: el sha local son solo ceros (40 o 64, segun el repo)
            if [ -z "${local_sha//0/}" ]; then
                case "$remote_ref" in
                    refs/heads/claude/equipo-dev/[0-9]*) ;;
                    *) malo="$malo $remote_ref (el equipo solo borra la rama de trabajo que acaba de mergear)" ;;
                esac
            fi ;;
        *) malo="$malo $remote_ref (el equipo solo empuja a claude/equipo-dev/*)" ;;
    esac
done
if [ -n "$malo" ]; then
    echo "PUSH_BLOQUEADO por el guardia del equipo (scripts/equipo-dev/pre-push.sh):$malo" >&2
    echo "Si esta sesion no es un turno del equipo, borrar $env_file y reintentar." >&2
    exit 1
fi
exit 0
