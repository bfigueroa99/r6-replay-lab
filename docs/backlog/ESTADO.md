# Estado del equipo de desarrollo autonomo

actualizado: 2026-10-12 21:20 UTC por dev (sesion 20261012T2101Z; motivo: por estado: 1 con_hallazgos, 0 huerfanas)
playbook: origin/claude/equipo-dev/playbook@e8d6798
rutina: TURNOS_SIN_RASTRO=11 en 48 h (10-10T21:01Z 10-11T00:01Z 10-11T03:01Z 10-11T06:01Z 10-11T09:01Z 10-11T12:01Z 10-11T15:01Z 10-11T18:01Z 10-11T21:01Z 10-12T00:01Z 10-12T03:01Z) | 12 de 39 en 7 dias
pausa: no

## Cola (items con codigo, esperando al humano o en trabajo)

| rama | ficha | estado | horas sin commits | PR / compare |
|---|---|---|---|---|
| claude/equipo-dev/35-tests-lado-de-los-equipos | docs/backlog/35-tests-lado-de-los-equipos.md | implementado | 0 | sin PR, [compare](https://github.com/bfigueroa99/r6-replay-lab/compare/main...claude/equipo-dev/35-tests-lado-de-los-equipos?expand=1) |

COLA=1/4  TOTAL=1/6
RESUMEN propuesto=0 disenado=0 en_curso=0 huerfanas=0 implementado=1 revisado=0 con_hallazgos=0 aprobado=0 entregado=0 espera_humano=0 cola=1 total=1 tope_cola=4 tope_total=6 tope_propuesto=6 tope_disenado=3 ideas_libres=20 sin_merge=no pausa=no sin_rastro_48h=11

## Orden de merge sugerido

1. `claude/equipo-dev/35-tests-lado-de-los-equipos`: `implementado` (tercera vuelta del Dev, main 0949f87 ya fusionado). Necesita revision y QA de sesiones distintas a dev 20261010T1501Z, 20261012T1503Z y 20261012T2101Z. Solo tests: no choca con nada. Libera `backend/tests/test_pydissect.py`.

## Alcance

- Funcionalidades que llegaron a `main` en los ultimos 7 dias (`MAIN_7D`): ninguna (funcionalidad:0 otros:5): papel vacio.
- Epicas en curso: ninguna
- Papel: PAPEL_TIPOS=funcionalidad:0 otros:0. Cola: COLA_TIPOS=funcionalidad:0 de 1 ramas de trabajo.
- `ALCANCE.md`: 20 ideas libres. Ideas nuevas de este turno: ninguna
- Investigacion: ninguna todavia

## Papel (rama backlog)

| ficha | estado | tipo | epica | prioridad | area | candado |
|---|---|---|---|---|---|---|
| [35. Tests de como el parser decide que equipo ataca](35-tests-lado-de-los-equipos.md) | en curso (rama 35, implementado) | tests | - | 3 | tests | - |

Papel: 0 propuesto, 0 disenado.

## Ultimo turno de cada rol

| rol | fecha-hora UTC | que hizo |
|---|---|---|
| dev | 2026-10-12 21:01 | Corrige 35 (`con hallazgos` -> `implementado`): fusiona main 0949f87 y agrega dos tests de mayoria (`test_los_defensores_de_mas_restan_aunque_empaten_en_atacantes`, `test_los_atacantes_de_mas_suman_aunque_empaten_en_defensores`); las mutaciones "solo ataque" y "solo defensa" de la segunda revision ahora caen. Revision ciega sin hallazgos. `check.sh` en verde (414 backend, 53 vitest, build, 17 e2e). |
| qa | 2026-10-12 18:02 | Sin `revisado` ni `implementado` (35 esta `con hallazgos`, es del Dev). Fallback sobre main 0949f87: `check.sh` en `Todo en verde.` (403 backend, 53 vitest, build, 17 e2e). Deriva de docs: los comandos `manage.py` y `npm run` del README existen; las 11 variables de `.env.example` se leen en el backend; las etiquetas numericas de la UI sin match literal en `metricas.md` son secciones o columnas de metricas ya definidas ("Del total" es la tabla de "Mueres a los"). Sin fichas nuevas. 35: merge-tree limpio contra main; sin pedidos del humano. |
| release | 2026-10-12 16:40 | Turno pedido por el humano. Entrega 33 y 34 (`## PR`, ficha recortada, `entregado`), abre los PRs #19 y #20 y los mergea con la puerta completa: `turnos:` con dev, revisor y qa de sesiones distintas, sin `PAUSA` ni `SIN_MERGE`, sin pedidos del humano, diff fuera de lo reservado. 33: `check.sh` en verde sobre el head exacto 3468b29 con main 0b547d7 incluido (399 backend, 53 vitest, build, 17 e2e) -> merge 6d9b07e. 34: main 6d9b07e fusionado (2fa93ca, sin conflicto), `check.sh` en verde sobre ese commit (403 backend, 53 vitest, build, 17 e2e) -> merge 0949f87. No pudo borrar las ramas mergeadas: el proxy corta el push de borrado. |
| revisor | 2026-10-12 12:02 | Revisa 35: rama al dia con main 0b547d7, `check.sh` en verde (403 backend, 53 vitest, build, 17 e2e). Ciega con `revision.md`: 3 hallazgos, los 3 confirmados con mutacion. Bloqueantes: el test de "hereda el lado de su equipo" pasa aunque el codigo ponga ATTACK a todos, y los tests de lado pasan aunque solo vote el equipo 0. Menor: nombre del test de limpieza. Tests de arreglo verificados sobre main. 35 -> `con hallazgos`. Sin QA ni `entregado` para atender. |
| arquitecto | 2026-10-12 06:02 | Sin papel: 0 `propuesto`, 0 `disenado`. Mantenimiento: las tres ramas contienen main 0b547d7, merge-tree limpio contra main y por pares (33/34, 33/35, 34/35); sin commits humanos ni pedidos en `## Para el equipo`; ninguna ficha pasa las 48 h de P7. Sin pushes de codigo. |
| po | 2026-10-10 03:01 | Propone 34 (bug: `annotate_trades` suma una trade kill por cada victima vengada, asi que una baja que venga un doble cuenta 2 y +0.6 de rating; reproducido en main 0b547d7) y 35 (tests de `derive_team_roles`, que hoy solo cubre un test que se salta sin `.rec`). Fuzz de 19 endpoints con ~50 parametros borde sobre `seed_demo`: ningun 500. Reconciliacion: nada de `backlog` esta en main; el espejo de 33 esta al dia. |

## Para el equipo`; ninguna ficha pasa las 48 h de P7. Sin pushes de codigo. |
| po | 2026-10-10 03:01 | Propone 34 (bug: `annotate_trades` suma una trade kill por cada victima vengada, asi que una baja que venga un doble cuenta 2 y +0.6 de rating; reproducido en main 0b547d7) y 35 (tests de `derive_team_roles`, que hoy solo cubre un test que se salta sin `.rec`). Fuzz de 19 endpoints con ~50 parametros borde sobre `seed_demo`: ningun 500. Reconciliacion: nada de `backlog` esta en main; el espejo de 33 esta al dia. |

## Para el humano

- Ramas borrables (ya mergeadas o sin codigo). El turno no pudo borrarlas: el proxy de la sesion corta `git push --delete` (`fatal: the remote end hung up unexpectedly`). Pegar en tu PC:
  - `git push origin --delete claude/equipo-dev/30-tests-ganador-de-ronda` (mergeada, PR #15)
  - `git push origin --delete claude/equipo-dev/31-tests-stats-por-jugador` (mergeada, PR #16)
  - `git push origin --delete claude/equipo-dev/32-days-enorme-da-500` (mergeada, PR #17)
  - `git push origin --delete claude/equipo-dev/33-fecha-con-zona-da-500` (mergeada, PR #19)
  - `git push origin --delete claude/equipo-dev/34-trade-kill-contado-doble` (mergeada, PR #20)
  - `git push origin --delete claude/confident-feynman-dc9apf` (playbook anterior, solo commit de reclamo)
- Rutina: dos Release seguidos (00:01 UTC del 11 y del 12) no corrieron o no dejaron rastro, y como solo el Release mergea, un disparo perdido atrasa todo 24 h. Conviene mirar el historial de la rutina `r6-replay-lab: equipo dev cada 3h` en esos horarios.
- Playbook: sigue viviendo en `claude/great-cray-7o9tvf` (PR #11, abierto). Lo mergeas vos: toca las reglas del equipo.
- PRs abiertos que no son del equipo y no se tocan: #12 (`claude/focused-newton-w26nu4`, instalador), #14 (`claude/dazzling-einstein-w3qcyq`, filtros en la URL) y #18 (`ccr-6620de3c-r23lk0`, directiva de alcance del equipo).
- Preguntas abiertas:
  - **Boton de backup en Datos (deuda del #16) y `REPLAY_DIR` desde la UI (deuda del #19/#20).** Los dos necesitan un POST nuevo, y `CLAUDE.md` fija la API en tres POST (`/api/import/`, `/api/overrides/`, `/api/players/<id>/ubisoft/`). El PO no los propone hasta que digas si se puede sumar un cuarto (`POST /api/backup/`) y/o un quinto (`POST /api/config/replay-dir/`, que escribiria el `.env` de `%APPDATA%`). Contesta abajo, en la seccion Para el equipo.
  - **Bug en `round_end` (aviso de la ficha 30, ya en main):** en Y9S4+ un `DEFUSER_DISABLE_COMPLETE` del equipo que perdio segun la cabecera deja a los **dos** equipos con `won=True`. Hay que decidir cual manda (cabecera o feed) antes de arreglarlo; el PO lo puede proponer como ficha.
  - **1vX con `PLAYER_LEAVE` (aviso de la ficha 31, ya en main):** si un compañero se desconecta, el ultimo vivo que gana 1v1 queda con `1vX == 0` porque el que se fue no cuenta como muerto. ¿Debe contar? Decision de producto; no se toca hasta que digas.
  - **Ficha 35, avisos del Arquitecto (no bloquean):** `derive_team_roles` anota tambien los IDs sin nombre como `Unknown(<id>)` en `inferredOperatorSides` (el test lo deja documentado asi; si preferis que no, es otra ficha), y en empate de puntajes ataca el equipo 0 (no se testea para no fijarlo).
  - **#28 (calibrar el corte de 10 rondas por operador rival)** solo se puede hacer con tu base real; en la nube no hay datos. Queda para vos o para cuando haya un export anonimizado.
- Verificar en el PC: la 34 ya esta en main (PR #20). Desde `backend/`: `..\.venv\Scripts\python.exe manage.py recompute --dry-run`, `manage.py backup` y `manage.py recompute` para corregir las trade kills contadas doble en partidas ya importadas (detalle en `## Verificar en el PC` de la ficha 34).
- CI remota: GitHub Actions no ejecuta pasos desde 2026-09-11 (los jobs mueren en segundos). Lo que vale es `check.sh` local. (Aviso unico; no se repite por turno.)

## Para el equipo

(Escribe aca el humano. El equipo no borra ni edita este bloque; responde debajo con fecha.)
