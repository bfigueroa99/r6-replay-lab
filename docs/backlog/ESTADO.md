# Estado del equipo de desarrollo autonomo

actualizado: 2026-10-14 05:40 UTC por dev (sesion 20261014T0511Z; motivo: por estado: 1 disenado, lugar en cola; reloj: arquitecto, franja 2)
playbook: origin/main@a233a03
rutina: TURNOS_SIN_RASTRO=1 en 48 h (10-12T03:01Z) | 12 de 49 en 7 dias
pausa: no

## Cola (items con codigo, esperando al humano o en trabajo)

| rama | ficha | estado | horas desde el ultimo commit | compare | PR |
|---|---|---|---|---|---|
| claude/equipo-dev/40-hora-y-dia-de-la-semana | 40-hora-y-dia-de-la-semana | implementado | 0 | https://github.com/bfigueroa99/r6-replay-lab/compare/main...claude/equipo-dev/40-hora-y-dia-de-la-semana?expand=1 | no |

COLA=1/4  TOTAL=1/6
RESUMEN propuesto=0 disenado=0 en_curso=0 huerfanas=0 implementado=1 revisado=0 con_hallazgos=0 aprobado=0 entregado=0 espera_humano=0 cola=1 total=1 tope_cola=4 tope_total=6 tope_propuesto=6 tope_disenado=3 ideas_libres=21 sin_merge=no pausa=no sin_rastro_48h=1

## Orden de merge sugerido

Una sola rama abierta (40), sin conflicto con main a233a03 (nace de el).

## Alcance

- Funcionalidades que llegaron a `main` en los ultimos 7 dias (`MAIN_7D`): funcionalidad:4 (36-mitades-y-prorroga 37-rivales-repetidos 39-inercia-entre-rondas 41-ronda-segun-el-marcador) otros:7.
- Epicas en curso: lado-y-marcador: B1 (36), B4 (39) y B2 tramo 1 (41) en main, B5 (match point) como idea; rivales: D1 en main (37), siguientes tramos como idea; progreso: 40 (E3, hora y dia) implementada en su rama.
- Papel: funcionalidad:0 otros:0 (la 40 paso a la rama de trabajo). Cola: COLA_TIPOS=funcionalidad:1 de 1 ramas de trabajo.
- `ALCANCE.md`: 21 ideas libres (B2 tramo 1 y B4 pasan a `en main` en el proximo turno del PO).
- Investigacion: ninguna todavia

## Papel (rama backlog)

| ficha | estado | tipo | epica | prioridad | area | candado |
|---|---|---|---|---|---|---|
| 40-hora-y-dia-de-la-semana | en curso (espejo; la rama manda: implementado) | funcionalidad | progreso | 3 | fullstack | - |

Papel sin `propuesto` ni `disenado`: proximo turno por estado, Revisor (40 implementado); despues el PO llena el papel.

## Ultimo turno de cada rol

| rol | fecha-hora UTC | que hizo |
|---|---|---|
| release | 2026-10-14 00:40 | Entrega y mergea 39 (`aprobado` -> `entregado` -> main, funcionalidad, epica lado-y-marcador). Puerta completa: `turnos:` con dev, revisor y qa de sesiones distintas, sin `PAUSA` ni `SIN_MERGE`, sin commits ni comentarios humanos, diff fuera de las rutas del humano; main 5d2aecc ya fusionado; `check.sh` en `Todo en verde.` sobre el head exacto eaea5ca (503 backend, 69 vitest, build, 27 e2e). PR #28 -> merge 2a95f98. No pudo borrar la rama (403 del proxy en `git push --delete`). Espejo de 39 quitado de `backlog`. `pruebas.sh`: `PRUEBAS_OK (10)`. Rutina: sin herramientas para comparar el prompt. |
| revisor | 2026-10-14 02:14 | Revisa 41 (`implementado` -> `revisado`): revision ciega con `revision.md` sin hallazgos, confirmada por el lider (los 6 criterios con test o e2e; el desvio de Y9S4 se sostiene: `header.py:146` fuerza `startingScore` 0 y `code_version` fuera del parser solo lo lee `by_score_state`). Main 2a95f98 ya fusionado; `check.sh` en `Todo en verde.` (512 backend, 69 vitest, build, 28 e2e). Sin pushes de codigo. |
| dev | 2026-10-14 05:40 | Implementa 40 (`disenado` -> `implementado`, rama `claude/equipo-dev/40-hora-y-dia-de-la-semana`): `by_hour` (8 franjas de 3 h) y `by_weekday` (lunes a domingo con `iso_week_day`) en `/api/trends/`, paneles "Por hora del día" y "Por día de la semana" en Tendencias con CSV y aviso de muestra chica, seccion `## Cuando juegas` en `metricas.md`, 8 tests backend y e2e. Revision ciega: 2 hallazgos corregidos (test sin trackear, filtro de lado que no recortaba). `check.sh` en `Todo en verde.` (520 backend, 69 vitest, build, 29 e2e). Quita el espejo de 41 (ya en main, a233a03). |
| qa | 2026-10-14 03:14 | Prueba 41 (`revisado` -> `aprobado`). `check.sh` en `Todo en verde.` (512 backend, 69 vitest, build, 28 e2e), sin conflicto con main 2a95f98. Base vacia y filtros raros 200 con cuatro filas en 0; semilla 87/116/0/0; bordes con `factories.py` (replay pre-Y9S4, tu equipo 1, marcador `[]`/`[1]`/`[1,2,3]`) dan 88/116/2/4 y suman igual que `overview` con filtros. UI en Chromium con "Sin marcador" visible cuando tiene rondas, consola limpia. Chunk inicial sin cambio (185503 bytes). 4 mutaciones caen. Sin pushes de codigo. |
| arquitecto | 2026-10-13 20:16 | Disena 39 (`by_previous_round` con subconsulta a la ronda `number - 1` de la partida entera; ayudantes `_filas_por_tramo`, `TablaDeCorte`, `muestra.js` con aviso bajo 30 rondas), 41 (`by_score_state` con `KeyTransform`+`Cast` sobre `score_before` y tu `team_index`; `seed_demo` pasa a llenar `score_before`, solo cambia el panel nuevo) y 40 (`by_hour` en 8 franjas y `by_weekday` con `iso_week_day`). Spike en scratchpad con `seed_demo`: las sumas cuadran con el total (203). Orden 39 -> 41 -> 40. Sin pushes de codigo. |
| po | 2026-10-13 19:18 | Papel vacio: propone 39 (funcionalidad, B4: winrate y rating despues de ganar o perder la ronda anterior, en Tendencias), 40 (funcionalidad, E3: por franja de 3 h y por dia de la semana, en Tendencias) y 41 (funcionalidad, B2 tramo 1: adelante, empatado o atras segun `score_before`). `ALCANCE.md`: reconciliado contra main 5d2aecc (B1 y D1 en main), ideas nuevas B5, B6, E4, F4 y T3; 21 ideas libres. PRs abiertos revisados con herramientas: #14, #22, #1 siguen abiertos. Sin pushes de codigo. |

## Para el humano

- Ramas borrables (ya mergeadas o sin codigo). El turno no pudo borrarlas: el proxy de la sesion corta `git push --delete` (`HTTP 403`, `fatal: the remote end hung up unexpectedly`). Pegar en tu PC:
  - `git push origin --delete claude/equipo-dev/30-tests-ganador-de-ronda` (mergeada, PR #15)
  - `git push origin --delete claude/equipo-dev/31-tests-stats-por-jugador` (mergeada, PR #16)
  - `git push origin --delete claude/equipo-dev/32-days-enorme-da-500` (mergeada, PR #17)
  - `git push origin --delete claude/equipo-dev/33-fecha-con-zona-da-500` (mergeada, PR #19)
  - `git push origin --delete claude/equipo-dev/34-trade-kill-contado-doble` (mergeada, PR #20)
  - `git push origin --delete claude/equipo-dev/35-tests-lado-de-los-equipos` (mergeada, PR #23)
  - `git push origin --delete claude/equipo-dev/36-mitades-y-prorroga` (mergeada, PR #25)
  - `git push origin --delete claude/equipo-dev/38-dos-ganadores-por-ronda` (mergeada, PR #26)
  - `git push origin --delete claude/equipo-dev/37-rivales-repetidos` (mergeada, PR #27)
  - `git push origin --delete claude/equipo-dev/39-inercia-entre-rondas` (mergeada, PR #28)
  - `git push origin --delete claude/equipo-dev/41-ronda-segun-el-marcador` (mergeada, main a233a03)
  - `git push origin --delete claude/confident-feynman-dc9apf` (playbook anterior, solo commit de reclamo)
- Rutina: 1 disparo sin rastro en 48 h (10-12T03:01Z); revisar el historial de la Routine `r6-replay-lab: equipo dev cada 3h`.
- Playbook: ya esta en `main` (#21); la cadena lo lee de `origin/main`.
- PRs abiertos que no son del equipo y no se tocan: #14 (`claude/dazzling-einstein-w3qcyq`, filtros en la URL), #22 (`ccr-ec8265ab-4qn7k2`, spawn peeks por mapa), #24 (`ccr-0e92052b-murujj`, cambios al playbook), #11 (`claude/great-cray-7o9tvf`) y #1-#4 (loop y mercado). La rama `claude/bold-cori-6gcxh9` (armas y temporadas de stats.cc, sin PR) toca `aggregates.py` y `seed_demo.py`: si la mergeas antes que la ficha 40, el choque en `aggregates.py` lo resuelve el equipo (P3).
- Ficha 41 (aviso, no bloquea): con replays anteriores a Y9S4 la fila "Sin marcador" de Tendencias puede ser grande; es correcto, el `.rec` viejo no trae el marcador.
- Preguntas abiertas:
  - **Ficha 39 (ya en main, PR #28; aviso, no bloquea):** el aviso de muestra chica de Tendencias (30 rondas por fila) se probo solo con datos sinteticos; calibrar con la base real.
  - ~~Boton de backup y `REPLAY_DIR` desde la UI~~: resuelto por el #12 (main eb2633c), que suma `POST /api/settings/` y `POST /api/backup/` a `CLAUDE.md`. El PO ya no las tiene que esperar.
  - **Ficha 38 ya en main (PR #26):** manda la cabecera sobre el kill feed para el ganador de la ronda desde Y9S4. Si preferis que mande el feed y se corrija el marcador, pedilo en `## Para el equipo`.
  - **1vX con `PLAYER_LEAVE` (aviso de la ficha 31, ya en main):** si un compañero se desconecta, el ultimo vivo que gana 1v1 queda con `1vX == 0` porque el que se fue no cuenta como muerto. ¿Debe contar? Decision de producto; no se toca hasta que digas.
  - **Ficha 35 (ya en main, PR #23), avisos del Arquitecto (no bloquean):** `derive_team_roles` anota tambien los IDs sin nombre como `Unknown(<id>)` en `inferredOperatorSides` (el test lo deja documentado asi; si preferis que no, es otra ficha), y en empate de puntajes ataca el equipo 0 (no se testea para no fijarlo).
  - **Ficha 35, tercera revision (aviso, no bloquea):** el desempate (`>=` por `>`) sigue sin test a proposito; es la unica mutacion de `derive_team_roles` que sobrevive.
  - **#28 (calibrar el corte de 10 rondas por operador rival)** solo se puede hacer con tu base real; en la nube no hay datos. Queda para vos o para cuando haya un export anonimizado.
- Verificar en el PC (38, PR #26, parser): `manage.py backup` y despues `manage.py import_replays --force <carpeta>` (`recompute` no reparsea) para corregir rondas Y9S4+ ya importadas; confirmar con `.rec` reales que el ganador de cada ronda coincide con el marcador, y `$env:R6_TEST_REPLAY="<ruta a un .rec Y9S4+>"; python manage.py test tests.test_pydissect`.
- Verificar en el PC: la 34 ya esta en main (PR #20). Desde `backend/`: `..\.venv\Scripts\python.exe manage.py recompute --dry-run`, `manage.py backup` y `manage.py recompute` para corregir las trade kills contadas doble en partidas ya importadas (detalle en `## Verificar en el PC` de la ficha 34).
- Ficha 36 (aviso, no bloquea): si faltan los `.rec` del inicio de una partida, la segunda mitad se lee como primera (documentado). Se podria evitar tomando el lado inicial solo de una ronda con `score_before == [0, 0]`; queda como posible mejora.
- CI remota: GitHub Actions no ejecuta pasos desde 2026-09-11 (los jobs mueren en segundos). Lo que vale es `check.sh` local. (Aviso unico; no se repite por turno.)

## Para el equipo

(Escribe aca el humano. El equipo no borra ni edita este bloque; responde debajo con fecha.)
