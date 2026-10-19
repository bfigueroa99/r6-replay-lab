# Estado del equipo de desarrollo autonomo

(Esta es la forma de `ESTADO.md`, que vive en la rama `backlog`. Nadie lo
escribe a mano: lo genera `scripts/equipo-dev/estado.sh --tablero` y lo
empuja `scripts/equipo-dev/pulso.sh cierre` al final de cada turno. Lo que
escribe la gente se conserva de una version a la siguiente: la tabla de
ultimos turnos, los pedidos al humano y `## Para el equipo`, que va byte por
byte.)

actualizado: <fecha-hora UTC> por <roles encadenados> (sesion <EQUIPO_SESION>; motivo: <EQUIPO_MOTIVO>; reloj: <EQUIPO_RELOJ>, franja <n>)
playbook: <ref>@<sha corto>[ (candidato: <PLAYBOOK_CANDIDATO>)]
rutina: <TURNOS_SIN_RASTRO de estado.sh> | <PULSO de estado.sh>[; <estado del prompt que agrega el Release>]
pausa: no | si
sin_merge: no | si

## Cola (items con codigo, esperando al humano o en trabajo)

| rama | ficha | estado | tipo | horas sin commits | candado | commits humanos | compare |
|---|---|---|---|---|---|---|---|
| `claude/equipo-dev/NN-slug` | NN-slug | implementado | funcionalidad | 5 | - | ninguno | [compare](https://github.com/bfigueroa99/r6-replay-lab/compare/main...claude/equipo-dev/NN-slug?expand=1) |

COLA=<n>/4  TOTAL=<n>/6
RESUMEN <linea tal cual de estado.sh>

## Orden de merge sugerido

1. `<rama>`: no choca con nada.
2. `<rama>`: choca con `<otra>` en el merge de prueba.

## Alcance

- MAIN_7D=... (funcionalidades y otros que llegaron a `main` en 7 dias)
- PAPEL_TIPOS=... COLA_TIPOS=...
- ALCANCE=... (ideas libres)
- INVESTIGACION=... (ultima entrada)
- RELEASE_PENDIENTE=... (fichas en main desde el ultimo tag v*)

## Papel (rama backlog)

| ficha | estado | tipo | epica | prioridad | area | candado |
|---|---|---|---|---|---|---|

## Salud del loop

- SALUD_OK, o una linea por `SALUD_*` de `estado.sh` (ver Salud del loop en
  `.claude/skills/equipo-dev/SKILL.md`).

## Ultimo turno de cada rol

| rol | fecha-hora UTC | que hizo |
|---|---|---|
| release | AAAA-MM-DD HH:MM | <lo que paso `pulso.sh cierre --turno`> |

## Para el humano

- Ramas borrables, un solo comando: `git push origin --delete <rama> <rama> ...`
- Espera tu merge: `<rama>` (<estado con el motivo>)
- Rutina: <n> disparos perdidos y <m> sesiones que murieron en 48 h (solo si hay)
- Funcionalidad: ninguna llego a `main` en 7 dias. Cuello de botella: <...> (solo si es asi)
- CI remota: aviso fijo de una linea.

### Pedidos abiertos

- H<n> (desde AAAA-MM-DD): <una decision o una accion en el PC, en una frase, con la ficha>

### Maquinaria propuesta por el equipo

- Mp<n> (desde AAAA-MM-DD, <sesion>): <idea para el loop, por que, con el numero que lo muestra>

### Resueltos (ultimos 7 dias)

- ~~H<n>~~ (AAAA-MM-DD): <pedido> -> <como se resolvio>

## Para el equipo

(Escribe aca el humano. El equipo no borra ni edita este bloque; responde debajo con fecha.)
