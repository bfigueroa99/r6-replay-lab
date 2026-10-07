#!/usr/bin/env bash
# Decide que rol del equipo lidera esta iteracion. Sale del reloj UTC y de
# nada mas: cero estado compartido que una sesion muerta pueda dejar a medias.
# Uso:  source <(scripts/equipo-dev/turno.sh)      # exporta las variables
#       scripts/equipo-dev/turno.sh revisor         # fuerza un rol (disparo manual)
#       git show <ref>:scripts/equipo-dev/turno.sh | bash -s -- [rol]
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
    *) echo "rol desconocido: $rol (release|po|arquitecto|dev|revisor|qa)" >&2; exit 1 ;;
esac
echo "export EQUIPO_INICIO=$(date -u +%s)"
echo "export EQUIPO_SESION=$(date -u +%Y%m%dT%H%MZ)"
echo "export EQUIPO_FRANJA=$franja"
echo "export EQUIPO_ROL=$rol"
echo "# turno: $rol (franja $franja, $(date -u +%H:%M) UTC)" >&2
