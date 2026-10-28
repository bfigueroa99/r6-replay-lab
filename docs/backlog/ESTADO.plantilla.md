# Estado del equipo de desarrollo autonomo

actualizado: <fecha-hora UTC> por <rol> (sesion <EQUIPO_SESION>; motivo: <EQUIPO_MOTIVO>)
playbook: <ref>@<sha corto>
rutina: <linea TURNOS_SIN_RASTRO de estado.sh tal cual>[; prompt al dia | prompt sincronizado con rutina.md@<sha corto> | sin herramientas para comparar | apagada]
pausa: no

## Cola (items con codigo, esperando al humano o en trabajo)

| rama | ficha | estado | horas sin commits | PR / compare |
|---|---|---|---|---|
| claude/equipo-dev/NN-slug | docs/backlog/NN-slug.md | entregado | 5 | [PR #n](url) o [compare](https://github.com/bfigueroa99/r6-replay-lab/compare/dev...claude/equipo-dev/NN-slug?expand=1) |

COLA=<n>/4  TOTAL=<n>/6
RESUMEN <linea tal cual de estado.sh>

## Orden de merge sugerido

1. `<rama>`: no choca con nada. Libera `<archivos>`.
2. `<rama>`: choca con la anterior en `<archivo>`; mergear despues.

## Alcance

- Funcionalidades que llegaron a `dev` en los ultimos 7 dias (`DEV_7D`): <n> (<fichas NN>) | ninguna: <cuello de botella>
- Epicas en curso: <slug>: tramos <NN en dev>, <NN en cola>, <NN en papel> | ninguna
- Papel: <PAPEL_TIPOS de estado.sh>. Cola: <COLA_TIPOS de estado.sh>.
- `ALCANCE.md`: <n> ideas libres. Ideas nuevas de este turno: <titulos> | ninguna
- Investigacion: ultima entrada <fecha> (<familias visitadas>) | ninguna todavia
- Rotacion: <linea ROTACION de estado.sh tal cual>
- Ciclo: <linea CICLO de estado.sh tal cual>

## Papel (rama backlog)

| ficha | estado | tipo | epica | prioridad | area | candado |
|---|---|---|---|---|---|---|

## Ultimo turno de cada rol

| rol | fecha-hora UTC | que hizo |
|---|---|---|

## Para el humano

(Solo lo que el humano tiene que decidir o hacer, bajo el tope de `PARA_EL_HUMANO`. Un aviso que no bloquea de una ficha ya en `dev` queda en la ficha, no aca.)

- Ramas borrables: <linea BORRAR de estado.sh tal cual>
- Release: <linea RELEASE de estado.sh tal cual> (solo si dev lleva commits que main no tiene)
- Preguntas abiertas: ...
- PRs que esperan tu merge: ...
- Verificar en el PC: <NN> (<que correr, en pocas palabras>), una linea por ficha
- Rutina: <n> disparos sin rastro en 48 h (<lista>); revisar el historial de la Routine `r6-replay-lab: equipo dev cada 3h` (solo si n > 0)
- Playbook candidato: <linea PLAYBOOK_CANDIDATO de estado.sh> (solo si aparece)
- CI remota: GitHub Actions no ejecuta pasos desde 2026-09-11 (los jobs mueren en segundos). Lo que vale es `check.sh` local. (Aviso unico; no se repite por turno.)

## Para el equipo

(Escribe aca el humano. El equipo no borra ni edita este bloque; responde debajo con fecha.)
