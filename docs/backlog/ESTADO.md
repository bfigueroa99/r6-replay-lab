# Estado del equipo de desarrollo autonomo

actualizado: 2026-10-17 04:55 UTC por qa (sesion 20261017T0404Z; motivo: por estado: 1 revisado; reloj: po, franja 1)
playbook: origin/main@06e3351
rutina: TURNOS_SIN_RASTRO=3 en 48 h (10-15T21:01Z 10-16T09:01Z 10-16T21:01Z) | 14 de 56 en 7 dias
pausa: no

## Cola (items con codigo, esperando al humano o en trabajo)

| rama | ficha | estado | horas sin commits | PR / compare |
|---|---|---|---|---|
| claude/equipo-dev/51-matriz-de-duelos-de-la-partida | docs/backlog/51-matriz-de-duelos-de-la-partida.md | aprobado | 0 | [compare](https://github.com/bfigueroa99/r6-replay-lab/compare/main...claude/equipo-dev/51-matriz-de-duelos-de-la-partida?expand=1) |

COLA=1/4  TOTAL=1/6
RESUMEN propuesto=0 disenado=0 en_curso=0 huerfanas=0 implementado=0 revisado=0 con_hallazgos=0 aprobado=1 entregado=0 espera_humano=0 cola=1 total=1 tope_cola=4 tope_total=6 tope_propuesto=6 tope_disenado=3 ideas_libres=59 sin_merge=no pausa=no sin_rastro_48h=3

## Orden de merge sugerido

1. `claude/equipo-dev/51-matriz-de-duelos-de-la-partida` (`aprobado`, unica rama en cola): `git merge-tree` contra main 06e3351 limpio. Le faltan los 16 commits de main que trajo PR #38: el Release hace `git merge origin/main` y `check.sh` antes del PR (puerta f). Libera `MatchDetail.jsx` y `styles.css` (la unica zona que comparte con PR #14 es el import de `MatchDetail.jsx`).

## Alcance

- Funcionalidades que llegaron a `main` en los ultimos 7 dias (`MAIN_7D`): funcionalidad:11 (36-mitades-y-prorroga 37-rivales-repetidos 39-inercia-entre-rondas 40-hora-y-dia-de-la-semana 41-ronda-segun-el-marcador 42-como-se-cierran-tus-rondas 43-match-point 44-records-personales 45-remontadas-y-derrumbes 46-primero-de-tu-equipo-en-caer 47-modos-desconocidos-en-datos) otros:8 (incluye 48, bug, PR #37 en main 2a6c86b).
- Epicas en curso: lado-y-marcador: B1-B7 en main, B10 en main (50, PR #38, main 06e3351); B8, B9, B11 y B12 como idea. temporada-y-modo: A2 (47) en main, A4 descartada como bug (49) y en espera de decision del humano; A1 lo toca PR #14, A3 libre. revision-de-rondas: F7 `aprobado` (51, QA 2026-10-17, espera al Release). escuadra: C4 (46) en main; C1-C3, C5 y C10 libres. progreso: E3 (40) y E4 (44) en main; E5 y E10 como idea. rivales: D1 (37) en main.
- Papel: PAPEL_TIPOS=funcionalidad:0 otros:0. Cola: COLA_TIPOS=funcionalidad:1 de 1 ramas de trabajo.
- `ALCANCE.md`: 59 ideas libres (58 al empezar el turno; A4, B10 y F7 pasaron a fichas). Ideas nuevas de este turno: C10 compañeros por lado, E10 operadores que mejoran y empeoran, G6 partidas incompletas en Datos, H4 copiar el resumen de una partida como texto.
- Investigacion: ultima entrada 2026-10-14 22:11Z (familias 1, 2, 4 y 7; antes 3, 5 y 6). Proxima: 3, 5 y 6.

## Papel (rama backlog)

| ficha | estado | tipo | epica | prioridad | area | candado |
|---|---|---|---|---|---|---|
| 51-matriz-de-duelos-de-la-partida | en curso (aprobado en su rama) | funcionalidad | revision-de-rondas | 3 | frontend | - |
| 49-mapas-rehechos-mezclan-lados | descartado (premisa falsa: las versiones de un mapa ya comparten slug y nombre) | bug | temporada-y-modo | 2 | backend | - |

Proximo turno por estado: release para la 51 `aprobado` (regla 1): merge de main 06e3351, `check.sh`, `## PR`, PR y puerta. Con el papel vacio (0 `propuesto`, 0 `disenado`), despues le toca al PO.

## Ultimo turno de cada rol

| rol | fecha-hora UTC | que hizo |
|---|---|---|
| release | 2026-10-16 16:40 | Entrega 50 (funcionalidad, `aprobado` -> `entregado`): `turnos:` con dev, revisor y qa de sesiones distintas, main 2a6c86b ya fusionado, `check.sh` en `Todo en verde.` dos veces (644 backend, 90 vitest, build, 38 e2e; la segunda sobre 0f735c1, el commit de la ficha recortada). `## PR` escrito, ficha recortada, PR #38 abierto. El merge (`merge_pull_request`) fallo una vez por un sha corto y el reintento lo nego el clasificador de permisos de la sesion: queda `entregado (PR pendiente de merge)`. 2026-10-17: el humano pidio el merge en la sesion; PR #38 mergeado (main 06e3351), espejo quitado de backlog; el borrado de la rama lo corto el proxy. Merge de prueba 50x51 limpio. pruebas.sh: PRUEBAS_OK (10). Rutina: sin herramientas para comparar el prompt. |
| dev | 2026-10-16 20:18 | Corrige el hallazgo de la segunda revision de 51 (`con hallazgos` -> `implementado`): "Solo aperturas" toma el primer `Kill` o `Death` de la ronda por `order` (la regla de `opening_death` y de la columna Aperturas del scoreboard) y, si no es baja entre rivales, la ronda no suma. Tests: teamkill de apertura y `Death` suelto de apertura no suman (los dos caen con la mutacion); fila de `docs/metricas.md` alineada con Duelos de apertura. Revision ciega previa: aprobar (un nombre de test, corregido). `check.sh` en `Todo en verde.` (632 backend, 95 vitest, build, 38 e2e) con main 2a6c86b ya en la rama. |
| revisor | 2026-10-17 00:40 | Tercera pasada sobre 51, rama al dia con main 2a6c86b, `check.sh` en `Todo en verde.` (632 backend, 95 vitest, build, 38 e2e) antes y despues del push. Hallazgo de la segunda revision (apertura = primer `Kill`/`Death`) verificado. Revision ciega: aprobar con dos menores de tests: fixture del `Death` suelto con la victima en `target` en vez de `actor` (corregido en esta revision, test que pasa) y e2e de "Solo aperturas" que no distingue el filtro (a `## Para el humano`). `implementado` -> `revisado`. |
| qa | 2026-10-17 04:55 | Prueba 51 (funcionalidad, `revisado` -> `aprobado`) sobre f0d410b con main 2a6c86b. `check.sh` en `Todo en verde.` (632 backend, 95 vitest, build, 38 e2e). Base sembrada con 4 partidas sinteticas (sin bajas; solo teamkill y `Death` suelto; 3 rondas con apertura `Death`, nick que cambia de lado, ronda sin tu fila y nick sin equipo; sin rondas) en Chromium: celdas, HS y "Solo aperturas" cuadran a mano, texto vacio correcto, 375 px sin scroll horizontal, consola limpia. 3 mutaciones, todas caen. Chunk inicial 186,78 -> 186,82 kB. Fuera de la ficha: una partida sin rondas rompe el detalle (`MatchDetail.jsx:93`, codigo de main). Sin pushes de codigo. |
| arquitecto | 2026-10-15 18:35 | Disena 50 (`by_margin` en `/api/trends/` desde `Match.my_score/opponent_score`, corte Y9S4, prorroga primero, `side` ignorado, rating sobre la partida entera; `margen.js` + panel en Tendencias + e2e: seed_demo da 29 partidas en "1 ronda") y 51 (matriz de duelos en el navegador: `matrizDuelos.js` + componente `MatrizDuelos.jsx`, insertado entre Rondas y Scoreboard para no chocar con PR #14). Descarta 49: `map_slug` colapsa las versiones de un mapa a proposito (`header.py:227`, `test_pydissect.py:178`), no hay dos filas ni mezcla; separar versiones es decision de producto. `ALCANCE.md` A4 anotada. Sin pushes de codigo. |
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
  - `git push origin --delete claude/equipo-dev/50-partidas-cerradas-y-holgadas` (mergeada, PR #38)
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
- Ficha 49 **descartada** (Arquitecto 2026-10-15): el bug no existe. `map_slug()` sale del nombre legible y colapsa las versiones de un mapa a proposito (`pydissect/header.py:227-232`, `tests/test_pydissect.py:178`): `Consulate`, `ConsulateY7` y `ConsulateY10` son todos `Consulate`/`consulate`, asi que Mapas da una sola fila y el winrate por lado no se mezcla entre filas. `FortressY10` todavia no esta en `MAPS` (idea P1). **Decision tuya (P10, cambia como se agrupa un numero que ya se muestra):** ¿queres ver cada version de un mapa en su propia fila ("Consulate (Y10)")? Si si, es una funcionalidad barata: agrupar por `Match.map_id` (ya guardado) con el sufijo del identificador interno de `MAPS`, sin migracion ni reimportar. Decilo en `## Para el equipo` y el PO abre la ficha.
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
- Rutina: 3 disparos sin rastro en 48 h (10-15T21:01Z 10-16T09:01Z 10-16T21:01Z); revisar el historial de la Routine `r6-replay-lab: equipo dev cada 3h`.
- Ficha 50 (aviso del Revisor, no bloquea, preexistente): `ingest.py:146-169` saca el marcador final y `won` del ultimo `.rec` importado; si falta el de la ronda final (ranked 4-2 importada hasta 3-2), la partida queda ganada "por 1 ronda" en el panel nuevo y como victoria 3-2 en toda la app. Candidato a ficha `tipo: bug` del PO: `won=None` cuando el marcador final no cierra la partida segun `reglas_partida`.
- Ficha 51 (aviso del Revisor, no bloquea): el e2e de la matriz de duelos no distingue "Todas" de "Solo aperturas" (solo afirma que queda una celda con dato); un test mas fuerte cabe en una ficha `tests`.
- Ficha 51 (aviso de QA, no bloquea, preexistente en main): el detalle de una partida **sin rondas** tira `TypeError ... reading 'label'` en `MatchDetail.jsx:93` (`rounds[sel]` indefinido). Con `.rec` reales una partida siempre trae rondas; solo pasa con datos armados a mano. Candidato a ficha `bug` chica si el PO la quiere.
- CI remota: GitHub Actions no ejecuta pasos desde 2026-09-11 (los jobs mueren en segundos). Lo que vale es `check.sh` local. (Aviso unico; no se repite por turno.)

## Para el equipo

(Escribe aca el humano. El equipo no borra ni edita este bloque; responde debajo con fecha.)
