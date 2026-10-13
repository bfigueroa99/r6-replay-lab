# Estado del equipo de desarrollo autonomo

actualizado: 2026-10-13 05:40 UTC por po (sesion 20261013T0511Z; motivo: papel vacio; reloj: arquitecto, franja 2)
playbook: origin/main@e5bad5b
rutina: TURNOS_SIN_RASTRO=9 en 48 h (10-11T03:01Z 10-11T06:01Z 10-11T09:01Z 10-11T12:01Z 10-11T15:01Z 10-11T18:01Z 10-11T21:01Z 10-12T00:01Z 10-12T03:01Z) | 12 de 41 en 7 dias
pausa: no

## Cola (items con codigo, esperando al humano o en trabajo)

Vacia.

COLA=0/4  TOTAL=0/6
RESUMEN propuesto=3 disenado=0 en_curso=0 huerfanas=0 implementado=0 revisado=0 con_hallazgos=0 aprobado=0 entregado=0 espera_humano=0 cola=0 total=0 tope_cola=4 tope_total=6 tope_propuesto=6 tope_disenado=3 ideas_libres=20 sin_merge=no pausa=no sin_rastro_48h=9

## Orden de merge sugerido

Nada abierto. Sin pares que probar.

## Alcance

- Funcionalidades que llegaron a `main` en los ultimos 7 dias (`MAIN_7D`): ninguna (funcionalidad:0 otros:6). Cuello de botella: diseno (3 propuesto, 0 disenado).
- Epicas en curso: lado-y-marcador: tramo B1 en papel (36), B2 sigue como idea; rivales: tramo D1 en papel (37).
- Papel: PAPEL_TIPOS=funcionalidad:2 otros:1. Cola: COLA_TIPOS=funcionalidad:0 de 0 ramas de trabajo.
- `ALCANCE.md`: 20 ideas libres. Ideas nuevas de este turno: B4 Inercia entre rondas, E3 Rendimiento por hora del dia y dia de la semana. Reconciliado: G4, G5 e I2 en main (#12); PR #22 cubierto.
- Investigacion: ninguna todavia

## Papel (rama backlog)

| ficha | estado | tipo | epica | prioridad | area | candado |
|---|---|---|---|---|---|---|
| 36-mitades-y-prorroga | propuesto | funcionalidad | lado-y-marcador | 2 | fullstack | - |
| 37-rivales-repetidos | propuesto | funcionalidad | rivales | 3 | fullstack | - |
| 38-dos-ganadores-por-ronda | propuesto | bug | - | 2 | parser | - |

Papel: 3 propuesto, 0 disenado. Toca Arquitecto.

## Ultimo turno de cada rol

| rol | fecha-hora UTC | que hizo |
|---|---|---|
| release | 2026-10-13 04:13 | Entrega y mergea 35 (`aprobado` -> `entregado` -> main). Puerta completa: `turnos:` con dev, revisor y qa de sesiones distintas, sin `PAUSA` ni `SIN_MERGE`, sin commits ni comentarios humanos, diff solo `backend/tests/test_pydissect.py` y la ficha; main eb2633c incluido; `check.sh` en `Todo en verde.` sobre el head exacto 7e35900 (468 backend, 65 vitest, build, 23 e2e). PR #23 -> merge e5bad5b. No pudo borrar la rama: el proxy corta el push de borrado. Espejo de 35 quitado de `backlog`. `pruebas.sh`: `PRUEBAS_OK (10)`. |
| qa | 2026-10-13 03:02 | Prueba 35 (`revisado` -> `aprobado`). Fusiona main eb2633c (#12) en la rama sin conflicto; `check.sh` en `Todo en verde.` (468 backend, 65 vitest, build, 23 e2e). Criterios con evidencia: 12 tests OK; mutaciones de `header.py` (solo votos de ataque, scoreboard con todos, clave por id, sin `inferredOperatorSides`) caen; suite en `--reverse` y `--shuffle` sin estado filtrado; humo de API en base vacia y `seed_demo` (200 en todo). |
| revisor | 2026-10-13 00:02 | Revisa 35, tercera pasada (`implementado` -> `revisado`). `check.sh` en verde sobre f0fb9c3 (414 backend, 53 vitest, build, 17 e2e). Ciega con `revision.md` y ~19 mutaciones sobre copia: un hallazgo menor (el equipo 1 podia dejar de restar defensores sin que cayera nada), corregido por el Revisor con el test verde `test_los_defensores_de_mas_del_equipo_1_tambien_restan`, que cae con esa mutacion. `check.sh` en verde sobre 61cd27c (415 backend, 53 vitest, build, 17 e2e). |
| dev | 2026-10-12 21:01 | Corrige 35 (`con hallazgos` -> `implementado`): fusiona main 0949f87 y agrega dos tests de mayoria (`test_los_defensores_de_mas_restan_aunque_empaten_en_atacantes`, `test_los_atacantes_de_mas_suman_aunque_empaten_en_defensores`); las mutaciones "solo ataque" y "solo defensa" de la segunda revision ahora caen. Revision ciega sin hallazgos. `check.sh` en verde (414 backend, 53 vitest, build, 17 e2e). |
| arquitecto | 2026-10-12 06:02 | Sin papel: 0 `propuesto`, 0 `disenado`. Mantenimiento: las tres ramas contienen main 0b547d7, merge-tree limpio contra main y por pares (33/34, 33/35, 34/35); sin commits humanos ni pedidos en `## Para el equipo`; ninguna ficha pasa las 48 h de P7. Sin pushes de codigo. |
| po | 2026-10-13 05:11 | Papel vacio: propone 36 (funcionalidad, B1: mitades y prorroga en Tendencias), 37 (funcionalidad, D1: rivales repetidos con record de partidas en Duelos) y 38 (bug prioridad 2: en Y9S4+ un defuse o plant del equipo que perdio segun la cabecera deja dos ganadores; el aviso de la ficha 30). `ALCANCE.md`: reconciliado contra main e5bad5b (G4, G5, I2 en main por #12), PR #22 anotado como cubierto, ideas nuevas B4 (inercia entre rondas) y E3 (hora del dia y dia de la semana). Sin pushes de codigo. |

## Para el humano

- Ramas borrables (ya mergeadas o sin codigo). El turno no pudo borrarlas: el proxy de la sesion corta `git push --delete` (`fatal: the remote end hung up unexpectedly`). Pegar en tu PC:
  - `git push origin --delete claude/equipo-dev/30-tests-ganador-de-ronda` (mergeada, PR #15)
  - `git push origin --delete claude/equipo-dev/31-tests-stats-por-jugador` (mergeada, PR #16)
  - `git push origin --delete claude/equipo-dev/32-days-enorme-da-500` (mergeada, PR #17)
  - `git push origin --delete claude/equipo-dev/33-fecha-con-zona-da-500` (mergeada, PR #19)
  - `git push origin --delete claude/equipo-dev/34-trade-kill-contado-doble` (mergeada, PR #20)
  - `git push origin --delete claude/equipo-dev/35-tests-lado-de-los-equipos` (mergeada, PR #23)
  - `git push origin --delete claude/confident-feynman-dc9apf` (playbook anterior, solo commit de reclamo)
- Rutina: 9 disparos sin rastro en 48 h (10-11T03:01Z 10-11T06:01Z 10-11T09:01Z 10-11T12:01Z 10-11T15:01Z 10-11T18:01Z 10-11T21:01Z 10-12T00:01Z 10-12T03:01Z); revisar el historial de la Routine `r6-replay-lab: equipo dev cada 3h`. Dos de esos eran Release, y solo el Release mergea.
- Playbook: ya esta en `main` (#21); la cadena lo lee de `origin/main`.
- PRs abiertos que no son del equipo y no se tocan: #14 (`claude/dazzling-einstein-w3qcyq`, filtros en la URL), #22 (`ccr-ec8265ab-4qn7k2`, spawn peeks por mapa), #11 (`claude/great-cray-7o9tvf`) y #1-#4 (loop y mercado).
- Preguntas abiertas:
  - ~~Boton de backup y `REPLAY_DIR` desde la UI~~: resuelto por el #12 (main eb2633c), que suma `POST /api/settings/` y `POST /api/backup/` a `CLAUDE.md`. El PO ya no las tiene que esperar.
  - **Bug en `round_end` -> ficha 38 (propuesto):** el PO eligio la variante conservadora, **manda la cabecera** (la misma fuente que el marcador de la partida); el plant del perdedor tiene el mismo problema y entra en la ficha. Si preferis que mande el feed, decilo en `## Para el equipo` antes de que la 38 llegue a Dev. Nada cambia en tu base hasta que corras `recompute`.
  - **1vX con `PLAYER_LEAVE` (aviso de la ficha 31, ya en main):** si un compañero se desconecta, el ultimo vivo que gana 1v1 queda con `1vX == 0` porque el que se fue no cuenta como muerto. ¿Debe contar? Decision de producto; no se toca hasta que digas.
  - **Ficha 35 (ya en main, PR #23), avisos del Arquitecto (no bloquean):** `derive_team_roles` anota tambien los IDs sin nombre como `Unknown(<id>)` en `inferredOperatorSides` (el test lo deja documentado asi; si preferis que no, es otra ficha), y en empate de puntajes ataca el equipo 0 (no se testea para no fijarlo).
  - **Ficha 35, tercera revision (aviso, no bloquea):** el desempate (`>=` por `>`) sigue sin test a proposito; es la unica mutacion de `derive_team_roles` que sobrevive.
  - **#28 (calibrar el corte de 10 rondas por operador rival)** solo se puede hacer con tu base real; en la nube no hay datos. Queda para vos o para cuando haya un export anonimizado.
- Verificar en el PC: la 34 ya esta en main (PR #20). Desde `backend/`: `..\.venv\Scripts\python.exe manage.py recompute --dry-run`, `manage.py backup` y `manage.py recompute` para corregir las trade kills contadas doble en partidas ya importadas (detalle en `## Verificar en el PC` de la ficha 34).
- Funcionalidad: ninguna llego a `main` en 7 dias (`MAIN_7D` funcionalidad:0 otros:6). El papel ya no esta vacio (36 y 37 son funcionalidad, 38 bug); el siguiente cuello es el diseno: el proximo turno por estado es Arquitecto.
- CI remota: GitHub Actions no ejecuta pasos desde 2026-09-11 (los jobs mueren en segundos). Lo que vale es `check.sh` local. (Aviso unico; no se repite por turno.)

## Para el equipo

(Escribe aca el humano. El equipo no borra ni edita este bloque; responde debajo con fecha.)
