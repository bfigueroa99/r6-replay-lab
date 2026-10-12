#!/usr/bin/env bash
# Decide que rol del equipo lidera esta iteracion. Sale del reloj UTC y de
# nada mas: cero estado compartido que una sesion muerta pueda dejar a medias.
# Uso:  scripts/equipo-dev/turno.sh            # el rol lo da el reloj
#       scripts/equipo-dev/turno.sh revisor    # fuerza un rol (disparo manual)
#       git show <ref>:scripts/equipo-dev/turno.sh | bash -s -- [rol]
#
# Las variables de shell no sobreviven entre comandos de Claude Code ni llegan
# a los subagentes, asi que el resultado se guarda en .git/equipo-dev.env (no
# se commitea nunca) y cada comando que lo necesite empieza con
#   source "$(git rev-parse --git-dir)/equipo-dev.env"
# Ademas se imprime entero, para que quede a la vista en la salida.
#
# La franja es la de 3 horas mas cercana, no la que contiene al minuto actual:
# asi un arranque demorado hasta 88 minutos cae en la franja que le tocaba.
set -u
roles=(release po arquitecto dev revisor dev qa revisor)
min=$(( 10#$(date -u +%H) * 60 + 10#$(date -u +%M) ))
franja=$(( (min + 90) / 180 % 8 ))
rol="${1:-${roles[$franja]}}"
case "$rol" in
    release|po|arquitecto|dev|revisor|qa) ;;
    *) echo "rol desconocido: '$rol' (release|po|arquitecto|dev|revisor|qa, en minuscula)" >&2; exit 1 ;;
esac
gitdir="$(git rev-parse --git-dir 2>/dev/null)" || { echo "no es un repo git" >&2; exit 1; }
inicio=$(date -u +%s)
# El playbook se lee de main si ya esta ahi; si no, de la rama donde vive.
ref=origin/main
git cat-file -e "$ref:.claude/skills/equipo-dev/SKILL.md" 2>/dev/null || ref=origin/claude/great-cray-7o9tvf
env_file="$gitdir/equipo-dev.env"
{
    echo "export EQUIPO_ROL=$rol"
    echo "export EQUIPO_FRANJA=$franja"
    echo "export EQUIPO_INICIO=$inicio"
    echo "export EQUIPO_SESION=$(date -u -d "@$inicio" +%Y%m%dT%H%MZ)"
    echo "export EQUIPO_CIERRE=$(date -u -d "@$((inicio + 75 * 60))" +%H:%M)"
    echo "export EQUIPO_REF=$ref"
} > "$env_file"
cat "$env_file"
echo "# turno: $rol | franja $franja | sesion $(date -u -d "@$inicio" +%Y%m%dT%H%MZ) | inicio $(date -u -d "@$inicio" +%H:%M) UTC | cerrar a las $(date -u -d "@$((inicio + 75 * 60))" +%H:%M) UTC | playbook $ref | variables en $env_file"
