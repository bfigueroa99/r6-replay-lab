# Estado del equipo de desarrollo autonomo

actualizado: 2026-10-21 00:35 UTC por release (sesion 20261021T0004Z; motivo: por estado: 1 aprobado; reloj: release, franja 0)
playbook: origin/main@6c3e640
rutina: TURNOS_SIN_RASTRO=5 en 48 h (10-19T09:01Z 10-19T12:01Z 10-19T21:01Z 10-20T09:01Z 10-20T21:01Z) | 11 de 56 en 7 dias; sin herramientas para comparar
pausa: no

## Cola (items con codigo, esperando al humano o en trabajo)

| rama | ficha | estado | horas sin commits | PR / compare |
|---|---|---|---|---|
| (vacia) | - | - | - | - |

COLA=0/4  TOTAL=0/6
RESUMEN propuesto=3 disenado=1 en_curso=0 huerfanas=0 implementado=0 revisado=0 con_hallazgos=0 aprobado=0 entregado=0 espera_humano=0 cola=0 total=0 tope_cola=4 tope_total=6 tope_propuesto=6 tope_disenado=3 ideas_libres=62 sin_merge=no pausa=no sin_rastro_48h=5

## Orden de merge sugerido

Nada abierto: la 58 entro a main (PR #46, 44c525b). La 60 (disenado) ya puede tomar `aggregates.py`, `views.py`, `Trends.jsx`, `humo.spec.js` y `metricas.md`.

## Alcance

- Funcionalidades que llegaron a `main` en los ultimos 7 dias (`MAIN_7D`): funcionalidad:16 (39-inercia-entre-rondas 40-hora-y-dia-de-la-semana 41-ronda-segun-el-marcador 42-como-se-cierran-tus-rondas 43-match-point 44-records-personales 45-remontadas-y-derrumbes 46-primero-de-tu-equipo-en-caer 47-modos-desconocidos-en-datos 50-partidas-cerradas-y-holgadas 51-matriz-de-duelos-de-la-partida 52-rondas-cortas-y-largas 53-multikills-por-tamano 54-solo-duo-o-stack 55-clutch-intentos-y-conversion 58-primera-ronda-de-cada-mitad) otros:1.
- Epicas en curso: lado-y-marcador: B1-B7, B9, B10 y B12 en main; B8 (58, PR #46) en main y B13 -> ficha 60 (disenado); B11 y B14 como idea. revision-de-rondas: F7 (51) y F10 (53) en main. escuadra: C4 (46) y C5 (54) en main; C7 -> ficha 57 (propuesto). impacto: K3 (55) en main, PR #43; K5 -> ficha 59 (propuesto, ya desbloqueada); O6 y K7 como idea. progreso: E3 (40) y E4 (44) en main; E5+E10 -> ficha 56 (propuesto). temporada-y-modo: A2 (47) en main, A4 descartada (49); A1 lo toca PR #14. rivales: D1 (37) en main.
- Papel: PAPEL_TIPOS=funcionalidad:4 otros:0. Cola: COLA_TIPOS=funcionalidad:0 de 0 ramas de trabajo.
- `ALCANCE.md`: 62 ideas libres (sin cambios en este turno).
- Investigacion: ultima entrada 2026-10-14 22:11Z (familias 1, 2, 4 y 7; antes 3, 5 y 6). Proxima: 3, 5 y 6.

## Papel (rama backlog)

| ficha | estado | tipo | epica | prioridad | area | candado |
|---|---|---|---|---|---|---|
| 56-mapas-y-operadores-que-mejoran | propuesto | funcionalidad | progreso | 3 | fullstack | - |
| 57-teamkills | propuesto | funcionalidad | escuadra | 3 | fullstack | - |
| 59-clutch-por-mapa-y-sitio | propuesto (#55 ya en main) | funcionalidad | impacto | 3 | fullstack | - |
| 60-racha-de-rondas | disenado | funcionalidad | lado-y-marcador | 3 | fullstack | - |
| 49-mapas-rehechos-mezclan-lados | descartado (premisa falsa: las versiones de un mapa ya comparten slug y nombre) | bug | temporada-y-modo | 2 | backend | - |

Un `disenado` (60) y tres `propuesto` (56, 57, 59). La 58 ya esta en main (PR #46). Proximo turno por estado: dev (regla 8) sobre la 60.

## Ultimo turno de cada rol

| rol | fecha-hora UTC | que hizo |
|---|---|---|
| release | 2026-10-21 00:35 | Entrega y mergea la 58 (`aprobado` -> `entregado` -> main): main 6c3e640 fusionado en la rama, puerta a-f cumplida (dev, revisor y qa de sesiones distintas; diff fuera de archivos del humano; sin preguntas abiertas), `check.sh` en `Todo en verde.` sobre el head 637425b (721 backend, 115 vitest, build, 44 e2e); PR #46 abierto y mergeado por MCP (main 44c525b). Ficha con `## PR`; espejo quitado de `backlog`. Borrar la rama: el proxy lo corta (va a borrables). pruebas.sh: PRUEBAS_OK (10). Rutina: sin herramientas para comparar el prompt. |
| dev | 2026-10-20 12:40 | Implementa 58 (`disenado` -> `implementado`, rama `claude/equipo-dev/58-primera-ronda-de-cada-mitad`): `by_half_opener` en `/api/trends/` (Ronda 1, Primera tras el cambio, Resto; prorroga fuera; el `Q` con nulo para partidas sin cambio), tabla "Primera ronda de cada lado" en el panel de mitades de Tendencias con CSV y aviso de muestra chica, 9 tests de Django, e2e, fila en `metricas.md`. Revision ciega: aprobar, 2 hallazgos menores corregidos. Dos mutaciones caen. `check.sh` en `Todo en verde.` (720 backend, 115 vitest, build, 44 e2e). |
| revisor | 2026-10-20 16:20 | Revisa 58 (funcionalidad, `implementado` -> `revisado`), rama al dia con main afd72ae. `check.sh` en `Todo en verde.` (720 backend, 115 vitest, build, 44 e2e). Revision ciega: aprobar; un hallazgo menor confirmado (el e2e solo afirma las etiquetas de las tres filas, no que tengan rondas; el backend si lo cubre). Los 5 criterios con test o verificacion anotada. Sin pushes de codigo. |
| qa | 2026-10-20 20:30 | Prueba 58 (funcionalidad, `revisado` -> `aprobado`), rama al dia con main afd72ae. `check.sh` en `Todo en verde.` (721 backend, 115 vitest, build, 44 e2e). Base sembrada desde `factories.py` (cambio en la 4 con prorroga, sin cambio numerada desde 0, sin lado, ronda sin lado antes del cambio, nick repetido): `/api/trends/` da 3/2/9 como se esperaba a mano, con `?side=` 2/1/6 y 1/1/3, bordes (`until=foo`, `days=abc`, `page=-1`, filtros vacios) sin 500; base vacia tres filas en 0. seed_demo: 29/29/145 = 203 rondas. Chunk inicial sin cambio. Mutaciones: 4; una no equivalente sobrevivia (tomar la ultima ronda del otro lado): test de borde agregado que la mata. |
| arquitecto | 2026-10-19 04:30 | Disena 55 (`clutch_vs` en `RoundPlayer`: funcion pura en `metrics.py` usada por import, `recompute` y migracion `0003` con `RunPython` que llena lo ya importado; cuenta `Kill`, `Death` y `PlayerLeave`; `clutch_conversion` en `/api/teammates/` por X y lado; tabla en Compañeros > Clutches; seed: intentos 1v1 ganados y 1v2 perdidos), 58 (`by_half_opener` en `/api/trends/` con subqueries de primera ronda y primera tras el cambio, ojo con `exclude(F)` sobre nulo; tabla en el panel de mitades) y 60 (`rachas_de_rondas` pura; `round_streaks` en el detalle de partida, record `longest_round_streak` sobre la partida entera; `rachas.js` para el texto). Papel: 3 disenado, 3 propuesto. Sin pushes de codigo. |
| investigador | 2026-10-14 22:18 | Familias 1 (forks nicktstewart, defiancer6s-hub y lumina-r6 de r6-dissect; api.github.com 403), 2 (r6tv.online, Aurelix, r6-replay.com/roadmap), 4 (Refrag nuevo, Leetify, vlr.gg, CS Demo Manager; Dotabuff 403) y 7 (Siege.GG rebalance, FanGraphs, Wilson). 13 ideas nuevas con fuente (45 -> 58 libres), F1 y F7 ampliadas, 4 descartadas con motivo. Sin pushes de codigo. |
| po | 2026-10-19 03:31 | Pedido (modo caos): propone 58 (B8: primera ronda de cada lado contra el resto, en el panel de mitades de Tendencias), 59 (K5: clutch por mapa y sitio, despues de #55) y 60 (B13: racha de rondas ganadas y perdidas en el detalle de partida y en Records). Papel en 6 `propuesto`. `ALCANCE.md`: nuevas B14, C13, C14, F12 y K7; H3 descartada (ya cubierta por los botones CSV): 62 libres (61 al empezar). Sin pushes de codigo. |

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
  - `git push origin --delete claude/equipo-dev/51-matriz-de-duelos-de-la-partida` (mergeada, PR #39)
  - `git push origin --delete claude/equipo-dev/52-rondas-cortas-y-largas` (mergeada, PR #40)
  - `git push origin --delete claude/equipo-dev/54-solo-duo-o-stack` (mergeada, PR #41)
  - `git push origin --delete claude/equipo-dev/53-multikills-por-tamano` (mergeada, PR #42)
  - `git push origin --delete claude/equipo-dev/55-clutch-intentos-y-conversion` (mergeada, PR #43)
  - `git push origin --delete claude/equipo-dev/58-primera-ronda-de-cada-mitad` (mergeada, PR #46)
  - `git push origin --delete claude/confident-feynman-dc9apf` (playbook anterior, solo el commit de reclamo)
- Playbook: ya esta en `main` (#21); la cadena lo lee de `origin/main`.
- Playbook candidato: origin/claude/equipo-dev/playbook@e8d6798
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
- Rutina: 5 disparos sin rastro en 48 h (10-19T09:01Z 10-19T12:01Z 10-19T21:01Z 10-20T09:01Z 10-20T21:01Z); revisar el historial de la Routine `r6-replay-lab: equipo dev cada 3h`.
- Ficha 50 (aviso del Revisor, no bloquea, preexistente): `ingest.py:146-169` saca el marcador final y `won` del ultimo `.rec` importado; si falta el de la ronda final (ranked 4-2 importada hasta 3-2), la partida queda ganada "por 1 ronda" en el panel nuevo y como victoria 3-2 en toda la app. Candidato a ficha `tipo: bug` del PO: `won=None` cuando el marcador final no cierra la partida segun `reglas_partida`. PO 2026-10-17: queda como idea G7 de `ALCANCE.md` (marcar en Datos, sin cambiar `won`); cambiar `won` mueve todos los winrates y es P10, decision tuya.
- Ficha 51 (ya en main, PR #39; aviso del Revisor, no bloquea): el e2e de la matriz de duelos no distingue "Todas" de "Solo aperturas" (solo afirma que queda una celda con dato); un test mas fuerte cabe en una ficha `tests`.
- Ficha 51 (ya en main, PR #39; aviso de QA, no bloquea, preexistente en main): el detalle de una partida **sin rondas** tira `TypeError ... reading 'label'` en `MatchDetail.jsx:93` (`rounds[sel]` indefinido). Con `.rec` reales una partida siempre trae rondas; solo pasa con datos armados a mano. Candidato a ficha `bug` chica si el PO la quiere. PO 2026-10-17: no entra; con `.rec` reales no pasa, solo con datos armados a mano.
- Ficha 53 (Arquitecto 2026-10-17, P10, no bloquea): `RoundPlayer.kills` incluye teamkills (`pydissect/stats.py:81-85`), asi que K/D, KPR, rating y los multikills nuevos los cuentan. El diseno lo deja asi y lo documenta. Si preferis excluirlos de `kills`, cambia numeros que ya se muestran: decilo en `## Para el equipo` y va a ficha propia.
- Ficha 54 (Arquitecto 2026-10-17, aviso, no bloquea): bug latente en main: un empate queda con `won=None` (`ingest.py:169`) y `match_result` mira `won is None` antes que el empate (`models.py:13-20`), asi que un empate se muestra como "incompleta" en toda la app. Candidato a ficha `bug` del PO.
- Ficha 52 (Arquitecto 2026-10-17, aviso, no bloquea): un plant seguido de barrida no se marca `possible_plant` (`metrics.py:236`) y entra a un tramo de duracion medido hasta el plant; no se puede separar con lo que trae el `.rec`. Los tramos de 45 s no se calibraron con la base real (en seed_demo todo cae en "135 s o más").
- Fichas 52-54 (Dev 2026-10-17, aviso, no bloquea): 53 deja `ACE` = 5 o mas bajas con teamkills incluidos (como Bajas); con un teamkill entre las 5 la ronda sale ACE sin haber matado a los 5 rivales. Queda documentado en `metricas.md`; cambia si decidis excluir teamkills de `kills` (aviso de la 53 arriba). 54: el umbral de 5 partidas para "habitual" sigue sin calibrar con la base real.
- Ficha 52 (Revisor 2026-10-18, aviso, no bloquea): la fila `Posible plant` de `/api/trends/` trae `rounds_won: 0` y no `null` aunque esas rondas se hayan ganado (lo pidio el diseno; la UI no muestra `rounds_won`). Si preferis `null`, es un cambio de una linea en `_celda`.
- Fichas 52 y 54 (QA 2026-10-18, aviso, no bloquea): los tramos de 45 s (52) y el umbral de 5 partidas para habitual (54) se probaron solo con datos sinteticos; calibrar con la base real.
- PR #43 (ficha 55) ya en main (afd72ae): lo mergeo el release 20261020T0804Z por MCP. Nada pendiente de merge. **Verificar en el PC (trae migracion 0003):** bajar main, `cd frontend; npm run build`, y desde `backend/` `..\.venv\Scripts\python.exe manage.py backup`, `... manage.py migrate`, `... manage.py recompute --dry-run` (esperado: sin cambios de `clutch_vs`).
- Turno release 20261020T0804Z (aviso): el clasificador de permisos nego volver a correr `estado.sh` despues del merge; la linea RESUMEN de arriba se conto a mano.
- Rutina: el disparo de las 21:01 corrio dos veces en paralelo con la misma sesion 20261018T2227Z (dos commits de `ESTADO.md` del mismo turno). Si se repite, revisar en la Routine `r6-replay-lab: equipo dev cada 3h` si hay dos disparos configurados.
- Ficha 55 (ya en main, PR #43; PO 2026-10-19, aviso, no bloquea): `clutch_vs` cuenta las rondas en que quedaste ultimo gane o pierda; `one_vx`, el Rating y el record de clutch no cambian. Si el X de las dos columnas difiere en una ronda ganada, la tabla agrupa por `clutch_vs`. Reversible.
- Turno po 20261019T0325Z (aviso): el clasificador de permisos de la sesion nego ejecutar `turno.sh` y `estado.sh` (`git show ... | bash` y tambien `bash <archivo>` ya leido: "Code from External"). El turno siguio a mano con `git` de solo lectura (mismo conteo que `estado.sh`) y no corrio ningun script del repo. Si se repite, la rutina necesita permiso para `bash` sobre `scripts/equipo-dev/*.sh` en la configuracion de la sesion.
- Ficha 54 (aviso del Arquitecto, revisado por el PO 2026-10-19): el empate que se muestra "incompleta" (`models.py:16` mira `won is None` antes que el empate) es solo la etiqueta: los winrates ya dejan fuera empates e incompletas. No entra como ficha `bug` porque con un `.rec` final faltante un 3-3 truncado tambien seria "empate": se resuelve junto con G7 (resultado dudoso en Datos).
- Ficha 55 (Arquitecto 2026-10-19, aviso, no bloquea): `clutch_vs` cuenta `PlayerLeave` como muerte (alguien que se fue no esta vivo), igual que `pydissect/stats.py` para el `1vX`. No toca `died`, `one_vx` ni la pregunta abierta del 1vX con `PLAYER_LEAVE`. La migracion `0003` llena la columna en tu base al primer `migrate`; si `recompute --dry-run` reporta cambios de `clutch_vs` despues, avisar.
- Ficha 55 (Dev 2026-10-19, Verificar en el PC cuando llegue a main, trae migracion): desde `backend/`, `..\.venv\Scripts\python.exe manage.py backup`, `... manage.py migrate` y despues `... manage.py recompute --dry-run`: no deberia reportar cambios de `clutch_vs`. La conversion deja fuera las rondas sin ganador conocido (`.rec` cortado al final).
- Ficha 55 (Revisor 2026-10-19, Verificar en el PC, no bloquea): antes de Y9S1 `PlayerLeave` sale de mensajes de texto; si en `.rec` reales aparecen abandonos despues del final de la ronda, `clutch_vs` (y el `1vX` de `pydissect/stats.py`) contarian un intento falso. Si tenes un `.rec` viejo con alguien que se fue al final, mirar el feed.
- Ficha 55 (Revisor 2026-10-20, aviso, no bloquea): `manage.py recompute` sobre la base de `seed_demo` vacia la tabla de conversion de clutch, porque el seed asigna `clutch_vs` a mano sin un feed coherente (en main ya pasa igual con los trades). Con datos reales no aplica.
- Ficha 55 (QA 2026-10-20, aviso, no bloquea, preexistente): el filtro `side` de la API distingue mayusculas (`?side=defense` da vacio); la UI manda `Attack`/`Defense`, asi que no se ve desde la app.
- Ficha 58 (ya en main, PR #46; Revisor 2026-10-20, aviso, no bloquea): el e2e de "Primera ronda de cada lado" pasa aunque las tres filas tengan 0 rondas (solo mira las etiquetas); un assert sobre la celda Rondas cabe en una ficha `tests` o en la proxima correccion de la 58.
- Ficha 58 (ya en main, PR #46; QA 2026-10-20, aviso, no bloquea): con `seed_demo` las tres filas tienen rondas (29/29/145), asi que el e2e no se apoya en 0; el hallazgo menor del Revisor queda como esta. QA agrego `test_la_fila_del_cambio_es_la_primera_ronda_del_otro_lado_y_no_otra` (los tests solo contaban rondas y no distinguian la R4 de la R6). Sin migracion ni parser: nada que verificar en el PC.
- CI remota: GitHub Actions no ejecuta pasos desde 2026-09-11 (los jobs mueren en segundos). Lo que vale es `check.sh` local. (Aviso unico; no se repite por turno.)

## Para el equipo

(Escribe aca el humano. El equipo no borra ni edita este bloque; responde debajo con fecha.)
