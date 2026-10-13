# Estado del equipo de desarrollo autonomo

actualizado: 2026-10-13 16:14 UTC por revisor (sesion 20261013T1612Z; motivo: por estado: 1 implementado; reloj: dev, franja 5)
playbook: origin/main@ac18a6e
rutina: TURNOS_SIN_RASTRO=5 en 48 h (10-11T15:01Z 10-11T18:01Z 10-11T21:01Z 10-12T00:01Z 10-12T03:01Z) | 12 de 45 en 7 dias
pausa: no

## Cola (items con codigo, esperando al humano o en trabajo)

| rama | ficha | estado | horas sin commits | PR / compare |
|---|---|---|---|---|
| claude/equipo-dev/37-rivales-repetidos | docs/backlog/37-rivales-repetidos.md | revisado | 0 | [compare](https://github.com/bfigueroa99/r6-replay-lab/compare/main...claude/equipo-dev/37-rivales-repetidos?expand=1) |

COLA=1/4  TOTAL=1/6
RESUMEN propuesto=0 disenado=0 en_curso=0 huerfanas=0 implementado=0 revisado=1 con_hallazgos=0 aprobado=0 entregado=0 espera_humano=0 cola=1 total=1 tope_cola=4 tope_total=6 tope_propuesto=6 tope_disenado=3 ideas_libres=20 sin_merge=no pausa=no sin_rastro_48h=5

## Orden de merge sugerido

1. `claude/equipo-dev/37-rivales-repetidos`: unica rama abierta; main ac18a6e ya fusionado en la rama (ec8df02). Libera `aggregates.py`, `views.py`, `Duelos.jsx`, `humo.spec.js`, `metricas.md`.

## Alcance

- Funcionalidades que llegaron a `main` en los ultimos 7 dias (`MAIN_7D`): funcionalidad:1 (36-mitades-y-prorroga) otros:7 (la 38, bug, llego hoy por PR #26).
- Epicas en curso: lado-y-marcador: tramo B1 en main (36, PR #25), B2 sigue como idea; rivales: tramo D1 revisado (37, segunda pasada aprobada; espera QA).
- Papel: PAPEL_TIPOS=funcionalidad:0 otros:0 (vacio). Cola: COLA_TIPOS=funcionalidad:1 de 1 ramas de trabajo.
- `ALCANCE.md`: 20 ideas libres. Ideas nuevas de este turno: ninguna (turno de Dev).
- Investigacion: ninguna todavia

## Papel (rama backlog)

| ficha | estado | tipo | epica | prioridad | area | candado |
|---|---|---|---|---|---|---|
| 37-rivales-repetidos | en curso (espejo; rama: revisado) | funcionalidad | rivales | 3 | fullstack | - |

Papel: 0 propuesto, 0 disenado. Proximo turno por estado: QA (37 revisado); el PO tiene que reponer papel (vacio).

## Ultimo turno de cada rol

| rol | fecha-hora UTC | que hizo |
|---|---|---|
| release | 2026-10-13 14:40 | Entrega y mergea 38 (`aprobado` -> `entregado` -> main, bug del parser). Puerta completa: `turnos:` con dev, revisor y qa de sesiones distintas, sin `PAUSA` ni `SIN_MERGE`, sin commits ni comentarios humanos, diff fuera de las rutas del humano; main 3e42126 ya fusionado; `check.sh` en `Todo en verde.` sobre el head exacto 0f6c40e (484 backend, 65 vitest, build, 24 e2e). PR #26 -> merge ac18a6e. No pudo borrar la rama (403 en el push de borrado). Espejo de 38 quitado de `backlog`. 37 sin conflicto contra main. `pruebas.sh`: `PRUEBAS_OK (10)`. Rutina: sin herramientas para comparar el prompt. |
| revisor | 2026-10-13 16:14 | Revisa 37 por segunda vez (`implementado` -> `revisado`): hallazgo del CSV corregido en c71b7c6 y cubierto por e2e; revision ciega con `revision.md` sin hallazgos; nota sin efecto (el `.distinct()` de `repeated_rivals` no deduplica por el `Meta.ordering`, pero se junta en sets). Fusiona main ac18a6e en la rama (ec8df02); `check.sh` en `Todo en verde.` (493 backend, 65 vitest, build, 26 e2e). Sin pushes de codigo. |
| dev | 2026-10-13 15:25 | Corrige 37 (`con hallazgos` -> `implementado`): `csv:` en la columna "Récord" de "Rivales repetidos" (`Duelos.jsx`) y e2e nuevo que baja el CSV y afirma `Récord == Ganadas-Perdidas` (visto rojo antes: `""` en vez de `"29-0"`). `check.sh` en `Todo en verde.` (26 e2e), main ac18a6e ya en la rama. |
| qa | 2026-10-13 13:40 | Prueba 38 (`revisado` -> `aprobado`). `check.sh` en `Todo en verde.` (484 backend, 65 vitest, build, 24 e2e), main 3e42126 ya fusionado. Propiedad sobre 3456 combinaciones de `round_end`: en Y9S4 siempre un solo ganador, el de la cabecera (con `events.py` de main falla). Partida sintetica importada por `ingest`: rondas ganadas 1 = marcador 1-2 (main daba 2). Endpoints con base vacia y parametros borde en 200. 3 mutaciones caen. Sin pushes de codigo. |
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
  - `git push origin --delete claude/equipo-dev/38-dos-ganadores-por-ronda` (mergeada, PR #26)
  - `git push origin --delete claude/confident-feynman-dc9apf` (playbook anterior, solo commit de reclamo)
- Rutina: 6 disparos sin rastro en 48 h (10-11T12:01Z 10-11T15:01Z 10-11T18:01Z 10-11T21:01Z 10-12T00:01Z 10-12T03:01Z); revisar el historial de la Routine `r6-replay-lab: equipo dev cada 3h`. Dos de esos eran Release, y solo el Release mergea.
- Playbook: ya esta en `main` (#21); la cadena lo lee de `origin/main`.
- PRs abiertos que no son del equipo y no se tocan: #14 (`claude/dazzling-einstein-w3qcyq`, filtros en la URL), #22 (`ccr-ec8265ab-4qn7k2`, spawn peeks por mapa), #11 (`claude/great-cray-7o9tvf`) y #1-#4 (loop y mercado).
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
