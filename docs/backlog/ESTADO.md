# Estado del equipo de desarrollo autonomo

actualizado: 2026-10-15 17:15 UTC por po (sesion 20261015T1711Z; motivo: papel vacio; reloj: qa, franja 6)
playbook: origin/main@2a6c86b
rutina: TURNOS_SIN_RASTRO=0 en 48 h | 12 de 56 en 7 dias
pausa: no

## Cola (items con codigo, esperando al humano o en trabajo)

| rama | ficha | estado | horas sin commits | PR / compare |
|---|---|---|---|---|

Ninguna rama de trabajo abierta: la 48 se mergeo en el turno anterior (PR #37, main 2a6c86b).

COLA=0/4  TOTAL=0/6
RESUMEN propuesto=3 disenado=0 en_curso=0 huerfanas=0 implementado=0 revisado=0 con_hallazgos=0 aprobado=0 entregado=0 espera_humano=0 cola=0 total=0 tope_cola=4 tope_total=6 tope_propuesto=6 tope_disenado=3 ideas_libres=59 sin_merge=no pausa=no sin_rastro_48h=0

## Orden de merge sugerido

Nada que mergear: no hay ramas de trabajo abiertas.

## Alcance

- Funcionalidades que llegaron a `main` en los ultimos 7 dias (`MAIN_7D`): funcionalidad:11 (36-mitades-y-prorroga 37-rivales-repetidos 39-inercia-entre-rondas 40-hora-y-dia-de-la-semana 41-ronda-segun-el-marcador 42-como-se-cierran-tus-rondas 43-match-point 44-records-personales 45-remontadas-y-derrumbes 46-primero-de-tu-equipo-en-caer 47-modos-desconocidos-en-datos) otros:8 (incluye 48, bug, PR #37 en main 2a6c86b).
- Epicas en curso: lado-y-marcador: B1-B7 en main, B10 en papel (50); B8, B9, B11 y B12 como idea. temporada-y-modo: A2 (47) en main, A4 en papel (49, bug); A1 lo toca PR #14, A3 libre. revision-de-rondas: F7 en papel (51). escuadra: C4 (46) en main; C1-C3, C5 y C10 libres. progreso: E3 (40) y E4 (44) en main; E5 y E10 como idea. rivales: D1 (37) en main.
- Papel: PAPEL_TIPOS=funcionalidad:2 otros:1. Cola: COLA_TIPOS=funcionalidad:0 de 0 ramas de trabajo.
- `ALCANCE.md`: 59 ideas libres (58 al empezar el turno; A4, B10 y F7 pasaron a fichas). Ideas nuevas de este turno: C10 compañeros por lado, E10 operadores que mejoran y empeoran, G6 partidas incompletas en Datos, H4 copiar el resumen de una partida como texto.
- Investigacion: ultima entrada 2026-10-14 22:11Z (familias 1, 2, 4 y 7; antes 3, 5 y 6). Proxima: 3, 5 y 6.

## Papel (rama backlog)

| ficha | estado | tipo | epica | prioridad | area | candado |
|---|---|---|---|---|---|---|
| 49-mapas-rehechos-mezclan-lados | propuesto | bug | temporada-y-modo | 2 | backend | - |
| 50-partidas-cerradas-y-holgadas | propuesto | funcionalidad | lado-y-marcador | 3 | fullstack | - |
| 51-matriz-de-duelos-de-la-partida | propuesto | funcionalidad | revision-de-rondas | 3 | frontend | - |

Proximo turno por estado: arquitecto (regla 9), primero la 49 (prioridad 2).

## Ultimo turno de cada rol

| rol | fecha-hora UTC | que hizo |
|---|---|---|
| release | 2026-10-15 16:45 | Entrega y mergea 48 (bug, `aprobado` -> `entregado` -> main, PR #37, main 2a6c86b). Puerta completa: dev 1311Z, revisor 1411Z y qa 1511Z en sesiones distintas, sin pedidos del humano ni preguntas abiertas, diff fuera de lo que mergea el humano, PR abierto, `check.sh` en `Todo en verde.` sobre 70f8958 con main 591a300 fusionado (632 backend con 4 saltados, 86 vitest, build, 37 e2e). Ficha recortada con `## PR`; espejo quitado de backlog. Borrado de la rama cortado por el proxy. pruebas.sh: PRUEBAS_OK (10). Rutina: sin herramientas para comparar el prompt. |
| dev | 2026-10-15 13:40 | Implementa 48 (bug, `disenado` -> `implementado`, rama `claude/equipo-dev/48-posts-sin-json-desde-otra-pagina`): `player_ubisoft` (antes del 404), `save_overrides` y `run_import` devuelven 415 sin `application/json`; `api.js` manda `{}` JSON por defecto en todo `post`. 3 tests de 415 (text/plain y urlencoded; `abrir` prohibido, `start_import` no llamado, `overrides.json` sin escribir) y e2e `los POST de la UI mandan JSON` (cae con el `api.js` de main). Fuera de `archivos:`: `test_ajustes.py` tambien postea a `/api/import/`. Revision ciega: aprobar. `check.sh` en `Todo en verde.` (632 backend, 86 vitest, build, 37 e2e). |
| revisor | 2026-10-15 14:14 | Revisa 48 (bug, `implementado` -> `revisado`). Rama al dia con main 591a300, `check.sh` en `Todo en verde.` (632 backend, 86 vitest, build, 37 e2e). Revision ciega: aprobar, sin hallazgos; confirmado a mano el orden de los 415, que todo POST de la UI pasa por `post()` y que los tests nuevos caen con el bug. Nota preexistente (tambien en main): `test_ajustes.VigilanteTests` da 4 fallos si se corre junto con `test_import_job` (dependen del orden). Sin pushes de codigo. |
| qa | 2026-10-15 15:17 | Prueba 48 (bug, `revisado` -> `aprobado`). `check.sh` en `Todo en verde.` (632 backend, 86 vitest, build, 37 e2e). Base vacia y sembrada: overrides, import (`?force=1`) y Ubisoft (id real e inexistente) dan 415 con text/plain, urlencoded, multipart y sin cuerpo, y no escriben `overrides.json`; con JSON (tambien `; charset=utf-8`) siguen igual. UI en Chromium: Importar, respaldo, interruptor de Ajustes, Datos (reetiqueta un `Unknown(424242)`) y Consultar Ubisoft (interceptado, sin red) mandan `application/json`. Mutacion: cada chequeo quitado hace caer su test. Chunk 186.78 kB (main 186.80). Sin pushes de codigo. |
| arquitecto | 2026-10-15 12:13 | Disena 48 (bug, `propuesto` -> `disenado`): `_es_json` + 415 al principio de `player_ubisoft` (antes del 404 y de `configurado()`), `save_overrides` y tambien `run_import` (con `?force=1` una pagina ajena forzaba la reimportacion entera; cuesta una linea); `api.js` manda `{}` JSON por defecto en todo `post`, asi `App.jsx` y `PerfilUbisoft.jsx` no cambian; helpers de tests a JSON, 3 tests nuevos de 415 y un e2e que intercepta `/api/import/` y afirma `application/json`. Sin pushes de codigo. |
| investigador | 2026-10-14 22:18 | Familias 1 (forks nicktstewart, defiancer6s-hub y lumina-r6 de r6-dissect; api.github.com 403), 2 (r6tv.online, Aurelix, r6-replay.com/roadmap), 4 (Refrag nuevo, Leetify, vlr.gg, CS Demo Manager; Dotabuff 403) y 7 (Siege.GG rebalance, FanGraphs, Wilson). 13 ideas nuevas con fuente (45 -> 58 libres), F1 y F7 ampliadas, 4 descartadas con motivo. Sin pushes de codigo. |
| po | 2026-10-15 17:15 | Papel vacio: propone 49 (bug A4: `by_map` une el winrate por lado por `map_name` y mezcla Fortress con FortressY10; `by_site`/`by_spawn` mezclan layouts; verificado en `aggregates.py:383-430`), 50 (B10: partidas cerradas y holgadas en Tendencias) y 51 (F7: matriz de duelos 5x5 en el detalle de partida, solo frontend). Reconcilia `ALCANCE.md` con main 2a6c86b. Ideas nuevas C10, E10, G6 y H4: 59 libres (58 al empezar). PRs #1, #14 y #22 siguen abiertos. Sin pushes de codigo. |

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
  - `git push origin --delete claude/equipo-dev/45-remontadas-y-derrumbes` (mergeada, PR #34)
  - `git push origin --delete claude/equipo-dev/46-primero-de-tu-equipo-en-caer` (mergeada, PR #35)
  - `git push origin --delete claude/equipo-dev/47-modos-desconocidos-en-datos` (mergeada, PR #36)
  - `git push origin --delete claude/equipo-dev/48-posts-sin-json-desde-otra-pagina` (mergeada, PR #37)
  - `git push origin --delete claude/confident-feynman-dc9apf` (playbook anterior, solo el commit de reclamo)
- Playbook: ya esta en `main` (#21); la cadena lo lee de `origin/main`.
- PRs abiertos que no son del equipo y no se tocan: #14 (`claude/dazzling-einstein-w3qcyq`, filtros en la URL), #22 (`ccr-ec8265ab-4qn7k2`, spawn peeks por mapa), #24 (`ccr-0e92052b-murujj`, cambios al playbook), #11 (`claude/great-cray-7o9tvf`) y #1-#4 (loop y mercado). La rama `claude/bold-cori-6gcxh9` (armas y temporadas de stats.cc, sin PR) toca `aggregates.py` y `seed_demo.py`: si la mergeas, el choque con las fichas siguientes lo resuelve el equipo (P3).
- Ficha 40 (aviso, no bloquea): una partida cuyo `.rec` no trae `datetime` en el header cae en la franja y el dia en que se importo (fallback preexistente de `_parse_ts`). Con `.rec` reales el campo viene siempre; si ves una franja rara, avisa y va a ficha propia.
- Ficha 40 (aviso de QA, no bloquea): con datos reales casi siempre habra una franja con menos de 30 rondas, asi que el hint del panel mostrara el aviso de muestra chica y casi nunca la explicacion de la hora. Si molesta, ficha chica.
- Ficha 41 (aviso, no bloquea): con replays anteriores a Y9S4 la fila "Sin marcador" de Tendencias puede ser grande; es correcto, el `.rec` viejo no trae el marcador.
- Ficha 43 (ya en main, PR #33; match point, aviso, no bloquea): solo Ranked tiene regla citable (gana a 4; con 3-3 prorroga y gana el primero a 5; fuente: guia de Dexerto actualizada en 2024, no hay pagina oficial de Ubisoft con el dato). Unranked, rapida y custom van a "Sin marcador o sin regla" hasta que alguien cite la suya; si la sabes, es una linea en `reglas_partida.py`. Conviene mirarlo en el PC con una ranked real cuando llegue. Revisor: el tipo `Standard` tambien cae en "sin regla" y la fila de `metricas.md` no lo nombra (menor).
- Ficha 44 (ya en main, PR #32; aviso de QA, no bloquea): `/api/overview/` tarda ~0,29 s con 2.000 partidas sinteticas (los records suman ~0,16 s). Si con tu base se siente lento, los records pueden ir a su propia request.
- Ficha 44 (ya en main, PR #32; aviso, no bloquea): los minimos de los records (6 rondas para la mejor partida, 20 para el mejor dia) son a ojo; calibrar con la base real.
- Verificar en el PC (Investigador, 2026-10-14): r6-dissect issue #130 reporta replays Y11S3 con `won: true` en los dos equipos en 3 de 5 rondas. `replays/analytics/metrics.py:205` se queda con el ultimo equipo sin avisar, asi que `my_team_won` podria salir al reves en esas rondas. Si tienes un `.rec` Y11S3, mirar si alguna ronda tiene a los dos equipos ganadores (idea P2 de `ALCANCE.md`); si se confirma, es un bug para el PO con prioridad 1. Tambien falta el operador 444310693746 (sale `Unknown(...)`, se puede nombrar en Datos; idea P1).
- Verificar en el PC (Investigador, 2026-10-14 22:11Z, idea P5): dos forks de r6-dissect (nicktstewart y defiancer6s-hub) cambian en Y11S2 (code version 9734089) el patron del DissectID a `8C 61 1A 75 23` y el layout del kill feed; sintoma: jugadores duplicados o faltantes y bajas de gente que no esta en la lista. `docs/formato-rec.md` dice que Y11S3 anda sin cambios, asi que puede afectar solo a Y11S2. Si tienes un `.rec` de Y11S2 (Calypso Casino, 2026-06 a 2026-09), importalo y mira si faltan jugadores o bajas.
- Ficha 49 propuesta (PO 2026-10-15) a partir de este aviso. Posible bug para el PO (Investigador, 2026-10-14, idea A4): `by_map` (`aggregates.py:383-402`) agrupa por nombre y slug, pero une el winrate por lado solo por `map_name`. Los mapas con version vieja y rehecha (`Fortress`/`FortressY10`, `ConsulateY7`/`ConsulateY10`, `ClubHouse`/`ClubHouseY10`...) salen como dos filas con el mismo nombre y el mismo winrate de ataque y defensa, mezclado. `by_site` tambien mezcla los sitios de los dos layouts. Leido en el codigo, no reproducido con datos: el PO puede abrirlo como `tipo: bug`.
- Ficha 45 (ya en main, PR #34; aviso del Dev, no bloquea): una partida con un `.rec` de ronda faltante, en el medio o al principio, no entra a remontadas, derrumbes ni a la tabla del cambio de lado (evita numeros falsos). Si faltan las ultimas no se detecta: el resultado de la partida ya sale truncado del ultimo `.rec` para toda la app. Con la base real, abrir una remontada y confirmar en el detalle que el marcador estuvo 2 abajo.
- Ficha 45 (ya en main, PR #34; aviso del Revisor, no bloquea): con `matches_known == 0` el panel dice "hace falta Y9S4 o posterior", pero tambien saca partidas Y9S4 con rondas faltantes o sin resultado; cambio de texto de una linea (Trends.jsx:546); el Release no implementa, queda para una ficha chica.
- Ficha 46 (ya en main, PR #35; aviso del Dev, no bloquea): `seed_demo` gana todas las rondas de ataque y pierde todas las de defensa, asi que en la demo el panel "Primero en caer" muestra 100 % y 0 % por lado; con la base real, abrir una ronda contada como "caíste primero" y confirmar en el feed que fuiste la primera baja de tu equipo.
- Ficha 46 (ya en main, PR #35; aviso del Revisor, no bloquea): la clasificacion "primero en caer" se calcula al consultar (lee `Event` si hay empates), como los Duelos. Si pesa con tu base, la alternativa es una columna `first_team_death` en `RoundPlayer` marcada al importar (migracion + `recompute`), ficha aparte.
- Ficha 48 (ya en main, PR #37, main 2a6c86b): los cinco POST de la API (`/api/import/`, `/api/overrides/`, `/api/players/<id>/ubisoft/`, `/api/settings/`, `/api/backup/`) exigen `application/json`; la UI manda `{}` JSON en todo POST. Reversible; si preferis dejar `/api/import/` abierto, decilo en `## Para el equipo`. (1) `CLAUDE.md` ("La API es de lectura") dice que exigen JSON "los que cambian configuracion": ahora lo exigen todos; la frase la cambias vos si queres. (2) **Despues de bajar main, `npm run build` antes de `runserver`**: con un `frontend/dist` viejo, los botones de Importar y de Ubisoft dan 415.
- Tests dependientes del orden (Revisor 2026-10-15, preexistente en main 591a300, no bloquea): desde `backend/`, `python manage.py test tests.test_import_job tests.test_ajustes` da 4 fallos en `test_ajustes.VigilanteTests`; la suite completa y cada modulo solo pasan. Candidato a ficha `tests` del PO.
- Verificar en el PC (ficha 47, ya en main, PR #36, toca el parser): desde `backend/`, `..\.venv\Scripts\python.exe manage.py unknown_ids` y `... manage.py retag --dry-run` sobre tu base: sin error, y si hay modos o tipos `Unknown(...)` aparecen en Datos > Sin identificar.
- Ficha 47 (ya en main, PR #36; aviso del Arquitecto, no bloquea): `Match` no guarda el id del modo ni del tipo de partida, asi que el retag lo lee del texto `Unknown(<id>)`; una etiqueta puesta mal no se corrige sobre lo ya importado. Corregirla pediria columnas `gamemode_id`/`match_type_id` con migracion y `recompute` (ficha aparte si la queres).
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
