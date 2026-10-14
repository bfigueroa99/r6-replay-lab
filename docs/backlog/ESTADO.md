# Estado del equipo de desarrollo autonomo

actualizado: 2026-10-14 18:50 UTC por release (sesion 20261014T1811Z; motivo: por estado: 1 aprobado; reloj: qa, franja 6)
playbook: origin/main@f74a16f
rutina: TURNOS_SIN_RASTRO=0 en 48 h | 12 de 54 en 7 dias; sin herramientas para comparar el prompt
pausa: no

## Cola (items con codigo, esperando al humano o en trabajo)

Vacia: 43 se mergeo (PR #33, main f74a16f).

COLA=0/4  TOTAL=0/6
RESUMEN propuesto=0 disenado=0 en_curso=0 huerfanas=0 implementado=0 revisado=0 con_hallazgos=0 aprobado=0 entregado=0 espera_humano=0 cola=0 total=0 tope_cola=4 tope_total=6 tope_propuesto=6 tope_disenado=3 ideas_libres=22 sin_merge=no pausa=no sin_rastro_48h=0

## Orden de merge sugerido

Nada en cola.

## Alcance

- Funcionalidades que llegaron a `main` en los ultimos 7 dias (`MAIN_7D`): funcionalidad:8 (36-mitades-y-prorroga 37-rivales-repetidos 39-inercia-entre-rondas 40-hora-y-dia-de-la-semana 41-ronda-segun-el-marcador 42-como-se-cierran-tus-rondas 43-match-point 44-records-personales) otros:7.
- Epicas en curso: lado-y-marcador: B1 (36), B4 (39), B2 (41 y 43), B5 (43) y B6 (42) en main; B7 como idea. progreso: E3 (40) y E4 (44) en main. rivales: D1 (37) en main, siguientes como idea.
- Papel: PAPEL_TIPOS=funcionalidad:0 otros:0 (papel vacio: el proximo turno por estado es PO). Cola: COLA_TIPOS=funcionalidad:0 de 0 ramas de trabajo.
- `ALCANCE.md`: 22 ideas libres (B2 y B5 marcados `en main` por el Release).
- Investigacion: ninguna todavia

## Papel (rama backlog)

Vacio. Espejo de 43 quitado (ya en main).

Proximo turno por estado: PO (papel vacio).

## Ultimo turno de cada rol

| rol | fecha-hora UTC | que hizo |
|---|---|---|
| release | 2026-10-14 18:50 | Entrega y mergea 43 (`aprobado` -> `entregado` -> main, PR #33, main f74a16f, funcionalidad). Rama ya traia main 41cb46f; `check.sh` en `Todo en verde.` sobre el commit exacto del PR 339b986 (561 backend, 80 vitest, build, 32 e2e). Ficha recortada con `## PR`; espejo quitado de backlog; B2/B5 a `en main` en `ALCANCE.md`. Borrar la rama: denegado en la sesion. pruebas.sh: PRUEBAS_OK (10). |
| revisor | 2026-10-14 16:30 | Revisa 43 (`implementado` -> `revisado`): revision ciega con `revision.md` sin hallazgos, confirmada por el lider (3-2 mine, 3-3 normal por prorroga, 4-4 both; sin regla, sin marcador e Y9S3 a unknown; las cinco filas suman por construccion). Criterios cubiertos por tests y e2e, diff dentro de `archivos:`. Mutaciones: sin prorroga caen 5 tests; `unknown` sobre `conocido` caen 2. Menores, no bloquean: `regla_para` solo la usan los tests; `metricas.md` no nombra `Standard` entre los tipos sin regla. Rama ya al dia con main 41cb46f; `check.sh` en `Todo en verde.` (561 backend, 80 vitest, build, 32 e2e). Sin pushes de codigo. |
| dev | 2026-10-14 15:35 | Implementa 43 (`disenado` -> `implementado`, rama `claude/equipo-dev/43-match-point`): `reglas_partida.py` (solo Ranked desde Y9S4: gana a 4, con 3-3 prorroga a 5, fuente Dexerto), `by_match_point` en `/api/trends/` reusando `_marcador_conocido` extraido de `by_score_state`, panel "Match point" en Tendencias, e2e y fila en `metricas.md`; 20 tests en `test_match_point.py`. Revision ciega: sin bugs, 2 puntos de tests corregidos (filtros que no recortaban, orden de las reglas). `check.sh` en `Todo en verde.` (561 backend, 80 vitest, build, 32 e2e). |
| qa | 2026-10-14 17:35 | Prueba 43 (`revisado` -> `aprobado`). `check.sh` en `Todo en verde.` (561 backend, 80 vitest, build, 32 e2e). Base vacia: cinco filas en 0 y 200 con `until=foo`, `page=-1`, `match_type=`, `map=`, `since=2030-01-01`. Base sembrada con `factories.py` (ranked 0-0 a 4-4 como equipo 0 y como equipo 1, QuickMatch, Y9S3, marcador vacio, 4-0 y tres equipos): mine 3, theirs 2, both 2, normal 13, unknown 6, igual a lo calculado y suma igual a `by_score_state`, tambien con filtros. 3 mutaciones caen (10, 3 y 3 tests). Chunk inicial sin cambio (el panel va en el lazy `Trends`). Sin pushes de codigo. |
| arquitecto | 2026-10-14 10:17 | Disena 42 (`round_endings` por lado en `/api/trends/` desde `round__my_team_won` + `win_condition`; panel "Cómo se cierran tus rondas" con `cierres.js`), 43 (tabla `reglas_partida.py` solo con Ranked: gana a 4, con 3-3 prorroga a 5, fuente Dexerto 2024; los demas tipos a `unknown`; `by_match_point` reusa la lectura del marcador de `by_score_state`; va despues de 42) y 44 (`personal_records` en `/api/overview/` agregado en la vista, cinco records con desempate al mas reciente, panel "Tus récords" en el Resumen con `records.js`). Sin pushes de codigo. |
| po | 2026-10-14 09:40 | Papel vacio: propone 42 (B6: rondas ganadas y perdidas por eliminacion o sin ella, por lado, en Tendencias), 43 (B5: match point y ronda decisiva con tabla de reglas por tipo de partida) y 44 (E4: records personales en el Resumen con enlace a cada partida). Reconcilia `ALCANCE.md` con main 3438ab2 (B2 tramo 1, B4, E3 y T3 en main) y quita el espejo de 40. Ideas nuevas B7, C4, C5 y F5: 22 libres (20 al empezar). PRs #1, #14 y #22 siguen abiertos. Sin pushes de codigo. |

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
  - `git push origin --delete claude/equipo-dev/40-hora-y-dia-de-la-semana` (mergeada, main 3438ab2)
  - `git push origin --delete claude/equipo-dev/42-como-se-cierran-tus-rondas` (mergeada, PR #31)
  - `git push origin --delete claude/equipo-dev/44-records-personales` (mergeada, PR #32)
  - `git push origin --delete claude/equipo-dev/43-match-point` (mergeada, PR #33)
  - `git push origin --delete claude/confident-feynman-dc9apf` (playbook anterior, solo el commit de reclamo)
- Playbook: ya esta en `main` (#21); la cadena lo lee de `origin/main`.
- PRs abiertos que no son del equipo y no se tocan: #14 (`claude/dazzling-einstein-w3qcyq`, filtros en la URL), #22 (`ccr-ec8265ab-4qn7k2`, spawn peeks por mapa), #24 (`ccr-0e92052b-murujj`, cambios al playbook), #11 (`claude/great-cray-7o9tvf`) y #1-#4 (loop y mercado). La rama `claude/bold-cori-6gcxh9` (armas y temporadas de stats.cc, sin PR) toca `aggregates.py` y `seed_demo.py`: si la mergeas, el choque con las fichas siguientes lo resuelve el equipo (P3).
- Ficha 40 (aviso, no bloquea): una partida cuyo `.rec` no trae `datetime` en el header cae en la franja y el dia en que se importo (fallback preexistente de `_parse_ts`). Con `.rec` reales el campo viene siempre; si ves una franja rara, avisa y va a ficha propia.
- Ficha 40 (aviso de QA, no bloquea): con datos reales casi siempre habra una franja con menos de 30 rondas, asi que el hint del panel mostrara el aviso de muestra chica y casi nunca la explicacion de la hora. Si molesta, ficha chica.
- Ficha 41 (aviso, no bloquea): con replays anteriores a Y9S4 la fila "Sin marcador" de Tendencias puede ser grande; es correcto, el `.rec` viejo no trae el marcador.
- Ficha 43 (ya en main, PR #33; match point, aviso, no bloquea): solo Ranked tiene regla citable (gana a 4; con 3-3 prorroga y gana el primero a 5; fuente: guia de Dexerto actualizada en 2024, no hay pagina oficial de Ubisoft con el dato). Unranked, rapida y custom van a "Sin marcador o sin regla" hasta que alguien cite la suya; si la sabes, es una linea en `reglas_partida.py`. Conviene mirarlo en el PC con una ranked real cuando llegue. Revisor: el tipo `Standard` tambien cae en "sin regla" y la fila de `metricas.md` no lo nombra (menor).
- Ficha 44 (ya en main, PR #32; aviso de QA, no bloquea): `/api/overview/` tarda ~0,29 s con 2.000 partidas sinteticas (los records suman ~0,16 s). Si con tu base se siente lento, los records pueden ir a su propia request.
- Ficha 44 (ya en main, PR #32; aviso, no bloquea): los minimos de los records (6 rondas para la mejor partida, 20 para el mejor dia) son a ojo; calibrar con la base real.
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
