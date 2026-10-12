# Estado del equipo de desarrollo autonomo

actualizado: <fecha-hora UTC> por <rol> (sesion <EQUIPO_SESION>)
playbook: <ref>@<sha corto>
pausa: no

## Cola (items con codigo, esperando al humano o en trabajo)

| rama | ficha | estado | horas sin commits | PR / compare |
|---|---|---|---|---|
| claude/equipo-dev/NN-slug | docs/backlog/NN-slug.md | entregado | 5 | [PR #n](url) o [compare](https://github.com/bfigueroa99/r6-replay-lab/compare/main...claude/equipo-dev/NN-slug?expand=1) |

COLA=<n>/3  TOTAL=<n>/5

## Orden de merge sugerido

1. `<rama>`: no choca con nada. Libera `<archivos>`.
2. `<rama>`: choca con la anterior en `<archivo>`; mergear despues.

## Papel (rama backlog)

| ficha | estado | prioridad | area | candado |
|---|---|---|---|---|

## Ultimo turno de cada rol

| rol | fecha-hora UTC | que hizo |
|---|---|---|

## Para el humano

- Ramas borrables (ya mergeadas o sin codigo): `git push origin --delete <rama>`
- Preguntas abiertas: ...
- Verificar en el PC: ...
- CI remota: GitHub Actions no ejecuta pasos desde 2026-09-11 (los jobs mueren en segundos). Lo que vale es `check.sh` local. (Aviso unico; no se repite por turno.)

## Para el equipo

(Escribe aca el humano. El equipo no borra ni edita este bloque; responde debajo con fecha.)
