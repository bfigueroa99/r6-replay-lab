# Estado del equipo de desarrollo autonomo

actualizado: 2026-10-13 10:40 UTC por release (sesion 20261013T1011Z; motivo: por estado: 1 aprobado; reloj: dev, franja 3)
playbook: origin/main@e5bad5b
rutina: TURNOS_SIN_RASTRO=7 en 48 h (10-11T09:01Z 10-11T12:01Z 10-11T15:01Z 10-11T18:01Z 10-11T21:01Z 10-12T00:01Z 10-12T03:01Z) | 12 de 43 en 7 dias; sin herramientas para comparar el prompt
pausa: no

## Cola (items con codigo, esperando al humano o en trabajo)

Vacia: la 36 se mergeo a main (PR #25, 3e42126).

COLA=0/4  TOTAL=0/6
RESUMEN propuesto=0 disenado=2 en_curso=0 huerfanas=0 implementado=0 revisado=0 con_hallazgos=0 aprobado=0 entregado=0 espera_humano=0 cola=0 total=0 tope_cola=4 tope_total=6 tope_propuesto=6 tope_disenado=3 ideas_libres=20 sin_merge=no pausa=no sin_rastro_48h=7

## Orden de merge sugerido

Sin ramas abiertas. La 37 y la 38 estan disenadas; el proximo turno por estado es Dev.

## Alcance

- Funcionalidades que llegaron a `main` en los ultimos 7 dias (`MAIN_7D`): funcionalidad:1 (36-mitades-y-prorroga) otros:6.
- Epicas en curso: lado-y-marcador: tramo B1 en main (36, PR #25), B2 sigue como idea; rivales: tramo D1 disenado (37).
- Papel: PAPEL_TIPOS=funcionalidad:1 otros:1. Cola: COLA_TIPOS=funcionalidad:0 de 0 ramas de trabajo.
- `ALCANCE.md`: 20 ideas libres (B1 queda por marcar `en main`; lo reconcilia el PO).
- Investigacion: ninguna todavia

## Papel (rama backlog)

| ficha | estado | tipo | epica | prioridad | area | candado |
|---|---|---|---|---|---|---|
| 37-rivales-repetidos | disenado | funcionalidad | rivales | 3 | fullstack | - |
| 38-dos-ganadores-por-ronda | disenado | bug | - | 2 | parser | - |

Papel: 0 propuesto, 2 disenado (37 funcionalidad, 38 bug). Proximo turno por estado: Dev (38 por prioridad 2, o 37).

## Ultimo turno de cada rol

| rol | fecha-hora UTC | que hizo |
|---|---|---|
| release | 2026-10-13 10:40 | Entrega y mergea 36 (`aprobado` -> `entregado` -> main), la primera funcionalidad del equipo en `main`. Puerta completa: `turnos:` con dev, revisor y qa de sesiones distintas, sin `PAUSA` ni `SIN_MERGE`, sin commits ni comentarios humanos, diff fuera de las rutas del humano; main e5bad5b incluido; `check.sh` en `Todo en verde.` sobre el head exacto 779729d (478 backend, 65 vitest, build, 24 e2e). PR #25 -> merge 3e42126. No pudo borrar la rama (el remoto corta el push de borrado). Espejo de 36 quitado de `backlog`. `pruebas.sh`: `PRUEBAS_OK (10)`. Rutina: sin herramientas para comparar el prompt. |
| qa | 2026-10-13 09:35 | Prueba 36 (`revisado` -> `aprobado`). Rama al dia con main e5bad5b; `check.sh` en `Todo en verde.` (478 backend, 65 vitest, build, 24 e2e). Bases vacia y sembrada con `factories.py` (prorroga, numeracion desde 0, ronda sin lado, partida sin resultado): `/api/trends/` da 3/3/2 y lado inicial correctos, filtros y parametros basura en 200; Tendencias en Chromium sin errores de consola. Chunk inicial sin cambio (185.47 kB). 3 mutaciones caen, 1 equivalente sobrevive. |
| revisor | 2026-10-13 08:25 | Revisa 36 (`implementado` -> `revisado`). Rama al dia con main e5bad5b; `check.sh` en `Todo en verde.` sobre c46b3e8 (478 backend, 65 vitest, build, 24 e2e). Ciega con `revision.md`: solo un detalle de estilo preexistente ("ronda tipica" sin tilde en el tooltip de Rating, copiado de otras 5 lineas de main), no bloquea. 4 mutaciones de `aggregates.py`, todas caen. Ficha limpiada (bloque `

## Para el humano` pegado dos veces por un reemplazo). |
| dev | 2026-10-13 07:45 | Implementa 36 (`disenado` -> `implementado`): `by_half` y `by_start_side` en `/api/trends/`, panel "Por mitad de la partida" en Tendencias, 10 tests en `test_mitades.py`, e2e nuevo, seccion en `metricas.md`. Revision ciega previa: un test debil corregido (mutacion `number=1` ahora cae). `check.sh` en `Todo en verde.` (478 backend, 65 vitest, build, 24 e2e). |
| arquitecto | 2026-10-13 06:15 | Disena 36 (mitades por lado inicial de la ronda mas baja sin prorroga, `by_half` y `by_start_side` en `/api/trends/`, panel en Tendencias, seed sin tocar), 37 (`repeated_rivals` con `_MI_EQUIPO`, `rivals` y `?min_matches=` en `/api/duels/`, panel en Duelos) y 38 (en Y9S4+ el feed solo da la condicion si apunta al ganador de la cabecera; el disable/plant del perdedor ya no marca `won`). Sin pushes de codigo. |
| po | 2026-10-13 05:11 | Papel vacio: propone 36 (funcionalidad, B1: mitades y prorroga en Tendencias), 37 (funcionalidad, D1: rivales repetidos con record de partidas en Duelos) y 38 (bug prioridad 2: en Y9S4+ un defuse o plant del equipo que perdio segun la cabecera deja dos ganadores; el aviso de la ficha 30). `ALCANCE.md`: reconciliado contra main e5bad5b (G4, G5, I2 en main por #12), PR #22 anotado como cubierto, ideas nuevas B4 (inercia entre rondas) y E3 (hora del dia y dia de la semana). Sin pushes de codigo. |

## Para el humano

- Ramas borrables (ya mergeadas o sin codigo). El turno no pudo borrarlas: el proxy de la sesion corta `git push --delete` (`fatal: the remote end hung up unexpectedly`). Pegar en tu PC:
  - `git push origin --delete claude/equipo-dev/30-tests-ganador-de-ronda` (mergeada, PR #15)
  - `git push origin --delete claude/equipo-dev/31-tests-stats-por-jugador` (mergeada, PR #16)
  - `git push origin --delete claude/equipo-dev/32-days-enorme-da-500` (mergeada, PR #17)
  - `git push origin --delete claude/equipo-dev/33-fecha-con-zona-da-500` (mergeada, PR #19)
  - `git push origin --delete claude/equipo-dev/34-trade-kill-contado-doble` (mergeada, PR #20)
  - `git push origin --delete claude/equipo-dev/35-tests-lado-de-los-equipos` (mergeada, PR #23)
  - `git push origin --delete claude/equipo-dev/36-mitades-y-prorroga` (mergeada, PR #25)
  - `git push origin --delete claude/confident-feynman-dc9apf` (playbook anterior, solo commit de reclamo)
- Rutina: 7 disparos sin rastro en 48 h (10-11T09:01Z 10-11T12:01Z 10-11T15:01Z 10-11T18:01Z 10-11T21:01Z 10-12T00:01Z 10-12T03:01Z); revisar el historial de la Routine `r6-replay-lab: equipo dev cada 3h`. Dos de esos eran Release, y solo el Release mergea.
- Playbook: ya esta en `main` (#21); la cadena lo lee de `origin/main`.
- PRs abiertos que no son del equipo y no se tocan: #14 (`claude/dazzling-einstein-w3qcyq`, filtros en la URL), #22 (`ccr-ec8265ab-4qn7k2`, spawn peeks por mapa), #11 (`claude/great-cray-7o9tvf`) y #1-#4 (loop y mercado).
- Preguntas abiertas:
  - ~~Boton de backup y `REPLAY_DIR` desde la UI~~: resuelto por el #12 (main eb2633c), que suma `POST /api/settings/` y `POST /api/backup/` a `CLAUDE.md`. El PO ya no las tiene que esperar.
  - **Bug en `round_end` -> ficha 38 (disenado):** el PO eligio la variante conservadora, **manda la cabecera** (la misma fuente que el marcador de la partida); el plant del perdedor tiene el mismo problema y entra en la ficha. Si preferis que mande el feed, decilo en `## Para el equipo` antes de que la 38 llegue a Dev. Nada cambia en tu base hasta que corras `recompute`.
  - **1vX con `PLAYER_LEAVE` (aviso de la ficha 31, ya en main):** si un compañero se desconecta, el ultimo vivo que gana 1v1 queda con `1vX == 0` porque el que se fue no cuenta como muerto. ¿Debe contar? Decision de producto; no se toca hasta que digas.
  - **Ficha 35 (ya en main, PR #23), avisos del Arquitecto (no bloquean):** `derive_team_roles` anota tambien los IDs sin nombre como `Unknown(<id>)` en `inferredOperatorSides` (el test lo deja documentado asi; si preferis que no, es otra ficha), y en empate de puntajes ataca el equipo 0 (no se testea para no fijarlo).
  - **Ficha 35, tercera revision (aviso, no bloquea):** el desempate (`>=` por `>`) sigue sin test a proposito; es la unica mutacion de `derive_team_roles` que sobrevive.
  - **#28 (calibrar el corte de 10 rondas por operador rival)** solo se puede hacer con tu base real; en la nube no hay datos. Queda para vos o para cuando haya un export anonimizado.
- Verificar en el PC: la 34 ya esta en main (PR #20). Desde `backend/`: `..\.venv\Scripts\python.exe manage.py recompute --dry-run`, `manage.py backup` y `manage.py recompute` para corregir las trade kills contadas doble en partidas ya importadas (detalle en `## Verificar en el PC` de la ficha 34).
- Funcionalidad: ninguna llego a `main` en 7 dias (`MAIN_7D` funcionalidad:0 otros:6). La 36 ya esta aprobada por QA y la entrega el proximo Release; 37 y 38 siguen disenadas.
- Ficha 36 (aviso, no bloquea): si faltan los `.rec` del inicio de una partida, la segunda mitad se lee como primera (documentado). Se podria evitar tomando el lado inicial solo de una ronda con `score_before == [0, 0]`; queda como posible mejora.
- CI remota: GitHub Actions no ejecuta pasos desde 2026-09-11 (los jobs mueren en segundos). Lo que vale es `check.sh` local. (Aviso unico; no se repite por turno.)

## Para el equipo

(Escribe aca el humano. El equipo no borra ni edita este bloque; responde debajo con fecha.)
