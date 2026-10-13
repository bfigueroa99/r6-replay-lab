# Estado del equipo de desarrollo autonomo

actualizado: 2026-10-13 22:30 UTC por revisor (sesion 20261013T2211Z; motivo: por estado: 1 implementado; reloj: revisor, franja 7)
playbook: origin/main@5d2aecc
rutina: TURNOS_SIN_RASTRO=3 en 48 h (10-11T21:01Z 10-12T00:01Z 10-12T03:01Z) | 12 de 47 en 7 dias
pausa: no

## Cola (items con codigo, esperando al humano o en trabajo)

| rama | ficha | estado | horas | link | PR |
|---|---|---|---|---|---|
| claude/equipo-dev/39-inercia-entre-rondas | 39-inercia-entre-rondas | revisado | 0 | https://github.com/bfigueroa99/r6-replay-lab/compare/main...claude/equipo-dev/39-inercia-entre-rondas?expand=1 | no |

COLA=1/4  TOTAL=1/6
RESUMEN propuesto=0 disenado=2 en_curso=0 huerfanas=0 implementado=0 revisado=1 con_hallazgos=0 aprobado=0 entregado=0 espera_humano=0 cola=1 total=1 tope_cola=4 tope_total=6 tope_propuesto=6 tope_disenado=3 ideas_libres=21 sin_merge=no pausa=no sin_rastro_48h=3

## Orden de merge sugerido

Una sola rama abierta (39), sin conflicto con main 5d2aecc. Despues de que la 39 se mergee se pueden implementar 41 y luego 40 (usan sus ayudantes).

## Alcance

- Funcionalidades que llegaron a `main` en los ultimos 7 dias (`MAIN_7D`): funcionalidad:2 (36-mitades-y-prorroga 37-rivales-repetidos) otros:7.
- Epicas en curso: lado-y-marcador: B1 en main (36, PR #25), 39 (B4, inercia) revisada en su rama, 41 (B2 tramo 1, marcador) disenada, B5 (match point) como idea; rivales: D1 en main (37, PR #27), siguientes tramos como idea; progreso: 40 (E3, hora y dia) disenada.
- Papel: PAPEL_TIPOS=funcionalidad:2 otros:0. Cola: COLA_TIPOS=funcionalidad:1 de 1 ramas de trabajo.
- `ALCANCE.md`: 21 ideas libres.
- Investigacion: ninguna todavia

## Papel (rama backlog)

| ficha | estado | tipo | epica | prioridad | area | candado |
|---|---|---|---|---|---|---|
| 39-inercia-entre-rondas | en curso (espejo; en su rama: revisado) | funcionalidad | lado-y-marcador | 2 | fullstack | - |
| 40-hora-y-dia-de-la-semana | disenado | funcionalidad | progreso | 3 | fullstack | - |
| 41-ronda-segun-el-marcador | disenado | funcionalidad | lado-y-marcador | 3 | fullstack | - |

40 y 41 dicen "implementar despues de que #39 (y #41) se mergee": esperan a la 39. Proximo turno por estado: QA (39).

## Ultimo turno de cada rol

| rol | fecha-hora UTC | que hizo |
|---|---|---|
| release | 2026-10-13 18:35 | Entrega y mergea 37 (`aprobado` -> `entregado` -> main, funcionalidad, epica rivales). Puerta completa: `turnos:` con dev, revisor y qa de sesiones distintas, sin `PAUSA` ni `SIN_MERGE`, sin commits ni comentarios humanos, diff fuera de las rutas del humano; main ac18a6e ya fusionado; `check.sh` en `Todo en verde.` sobre el head exacto 9bab1ab (493 backend, 65 vitest, build, 26 e2e). PR #27 -> merge 5d2aecc. No pudo borrar la rama (el proxy corta `git push --delete`). Espejo de 37 quitado de `backlog`. `pruebas.sh`: `PRUEBAS_OK (10)`. Rutina: sin herramientas para comparar el prompt. |
| revisor | 2026-10-13 22:30 | Revisa 39 (`implementado` -> `revisado`): revision ciega con `revision.md` sin hallazgos, confirmada por el lider (los 6 criterios con test; con `seed_demo` las tres filas suman el total en todo, `side=Attack`, `side=Defense` y `map=oregon`). Agrega `test_el_filtro_de_operador_no_cambia_la_ronda_anterior` (verde). Main 5d2aecc ya fusionado; `check.sh` en `Todo en verde.` (503 backend, 69 vitest, build, 27 e2e). |
| dev | 2026-10-13 21:20 | Implementa 39 (`disenado` -> `implementado`, rama `claude/equipo-dev/39-inercia-entre-rondas`): `by_previous_round` en `/api/trends/` (ronda `number - 1` leida de la partida entera), ayudantes `_filas_por_tramo`, `TablaDeCorte` y `muestra.js`, panel "Después de ganar o perder la ronda anterior" en Tendencias con CSV y aviso bajo 30 rondas, seccion `## Contexto de la ronda` en `metricas.md`, 9 tests backend, 4 vitest, e2e que afirma 0 %/100 % con `seed_demo`. Revision ciega: 4 menores, corregidos. `check.sh` en `Todo en verde.` (502 backend, 69 vitest, build, 27 e2e). |
| qa | 2026-10-13 17:14 | Prueba 37 (`revisado` -> `aprobado`). `check.sh` en `Todo en verde.` (493 backend, 65 vitest, build, 26 e2e), main ac18a6e ya fusionado. Base sembrada con `factories.py`: record por profileID con nick cambiado, compañero/rival, partida sin resultado, `min_matches` 0/-5/abc/99999/vacio/1.5, `map=oregon`, `side`, `until=foo`, `page=-1` y base vacia, todo 200 con los numeros esperados. Chunk inicial sin cambio (185503 B). 4 mutaciones de `repeated_rivals` caen. Sin pushes de codigo. |
| arquitecto | 2026-10-13 20:16 | Disena 39 (`by_previous_round` con subconsulta a la ronda `number - 1` de la partida entera; ayudantes `_filas_por_tramo`, `TablaDeCorte`, `muestra.js` con aviso bajo 30 rondas), 41 (`by_score_state` con `KeyTransform`+`Cast` sobre `score_before` y tu `team_index`; `seed_demo` pasa a llenar `score_before`, solo cambia el panel nuevo) y 40 (`by_hour` en 8 franjas y `by_weekday` con `iso_week_day`). Spike en scratchpad con `seed_demo`: las sumas cuadran con el total (203). Orden 39 -> 41 -> 40. Sin pushes de codigo. |
| po | 2026-10-13 19:18 | Papel vacio: propone 39 (funcionalidad, B4: winrate y rating despues de ganar o perder la ronda anterior, en Tendencias), 40 (funcionalidad, E3: por franja de 3 h y por dia de la semana, en Tendencias) y 41 (funcionalidad, B2 tramo 1: adelante, empatado o atras segun `score_before`). `ALCANCE.md`: reconciliado contra main 5d2aecc (B1 y D1 en main), ideas nuevas B5, B6, E4, F4 y T3; 21 ideas libres. PRs abiertos revisados con herramientas: #14, #22, #1 siguen abiertos. Sin pushes de codigo. |

## Para el humano

- Ramas borrables (ya mergeadas o sin codigo). El turno no pudo borrarlas: el proxy de la sesion corta `git push --delete` (`fatal: the remote end hung up unexpectedly`). Pegar en tu PC:
  - `git push origin --delete claude/equipo-dev/30-tests-ganador-de-ronda` (mergeada, PR #15)
  - `git push origin --delete claude/equipo-dev/31-tests-stats-por-jugador` (mergeada, PR #16)
  - `git push origin --delete claude/equipo-dev/32-days-enorme-da-500` (mergeada, PR #17)
  - `git push origin --delete claude/equipo-dev/33-fecha-con-zona-da-500` (mergeada, PR #19)
  - `git push origin --delete claude/equipo-dev/34-trade-kill-contado-doble` (mergeada, PR #20)
  - `git push origin --delete claude/equipo-dev/35-tests-lado-de-los-equipos` (mergeada, PR #23)
  - `git push origin --delete claude/equipo-dev/36-mitades-y-prorroga` (mergeada, PR #25)
  - `git push origin --delete claude/equipo-dev/38-dos-ganadores-por-ronda` (mergeada, PR #26)
  - `git push origin --delete claude/equipo-dev/37-rivales-repetidos` (mergeada, PR #27)
  - `git push origin --delete claude/confident-feynman-dc9apf` (playbook anterior, solo commit de reclamo)
- Rutina: 3 disparos sin rastro en 48 h (10-11T21:01Z 10-12T00:01Z 10-12T03:01Z); revisar el historial de la Routine `r6-replay-lab: equipo dev cada 3h`.
- Playbook: ya esta en `main` (#21); la cadena lo lee de `origin/main`.
- PRs abiertos que no son del equipo y no se tocan: #14 (`claude/dazzling-einstein-w3qcyq`, filtros en la URL), #22 (`ccr-ec8265ab-4qn7k2`, spawn peeks por mapa), #24 (`ccr-0e92052b-murujj`, cambios al playbook), #11 (`claude/great-cray-7o9tvf`) y #1-#4 (loop y mercado). La rama `claude/bold-cori-6gcxh9` (armas y temporadas de stats.cc, sin PR) toca `aggregates.py` y `seed_demo.py`: si la mergeas antes que las fichas 39-41, el Dev resuelve el choque en `aggregates.py` y la 41 en `seed_demo.py` (P3).
- Preguntas abiertas:
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
