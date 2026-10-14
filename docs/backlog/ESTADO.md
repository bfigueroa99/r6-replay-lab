# Estado del equipo de desarrollo autonomo

actualizado: 2026-10-14 23:16 UTC por arquitecto (sesion 20261014T2311Z; motivo: por estado: 3 propuesto, 0 disenado de 3; reloj: release, franja 0)
playbook: origin/main@f74a16f
rutina: TURNOS_SIN_RASTRO=0 en 48 h | 12 de 55 en 7 dias
pausa: no

## Cola (items con codigo, esperando al humano o en trabajo)

Vacia (main f74a16f, ultimo merge: 43, PR #33).

COLA=0/4  TOTAL=0/6
RESUMEN propuesto=0 disenado=3 en_curso=0 huerfanas=0 implementado=0 revisado=0 con_hallazgos=0 aprobado=0 entregado=0 espera_humano=0 cola=0 total=0 tope_cola=4 tope_total=6 tope_propuesto=6 tope_disenado=3 ideas_libres=58 sin_merge=no pausa=no sin_rastro_48h=0

## Orden de merge sugerido

Nada en cola.

## Alcance

- Funcionalidades que llegaron a `main` en los ultimos 7 dias (`MAIN_7D`): funcionalidad:8 (36-mitades-y-prorroga 37-rivales-repetidos 39-inercia-entre-rondas 40-hora-y-dia-de-la-semana 41-ronda-segun-el-marcador 42-como-se-cierran-tus-rondas 43-match-point 44-records-personales) otros:7.
- Epicas en curso: lado-y-marcador: B1 (36), B4 (39), B2 (41 y 43), B5 (43) y B6 (42) en main; B7 en ficha 45 (disenado); B8 y B9 como idea. escuadra: se abre con C4 (ficha 46, disenado). temporada-y-modo: A2 en ficha 47 (disenado). progreso: E3 (40) y E4 (44) en main; E5 como idea. rivales: D1 (37) en main.
- Papel: PAPEL_TIPOS=funcionalidad:3 otros:0. Cola: COLA_TIPOS=funcionalidad:0 de 0 ramas de trabajo.
- `ALCANCE.md`: 58 ideas libres (45 al empezar el turno). Ideas nuevas del Investigador: A5 mapas para banear, B12 cuanto tardas en ganar, C8 diferencial de trade, C9 oportunidades de trade convertidas, D5 cara a cara en el detalle de partida, E8 banda de ruido en winrates, E9 contra el promedio de tus lobbies, F10 multikills por tamaño, O3 contra la media del operador, O4 participacion en aperturas, O5 presencia y delta por operador, P5 jugadores y kill feed de Y11S2, P6 picks de preparacion; F1 y F7 ampliadas.
- Investigacion: ultima entrada 2026-10-14 22:11Z (familias 1, 2, 4 y 7; antes 3, 5 y 6). Proxima: 3, 5 y 6.

## Papel (rama backlog)

| ficha | titulo | estado | tipo | epica | prioridad |
|---|---|---|---|---|---|
| 45 | Remontadas y derrumbes | disenado | funcionalidad | lado-y-marcador | 3 |
| 46 | Primero de tu equipo en caer | disenado | funcionalidad | escuadra | 3 |
| 47 | Modos y tipos de partida desconocidos en Datos | disenado | funcionalidad | temporada-y-modo | 4 |

Proximo turno por estado: dev (3 disenado, cola 0/4). Orden sugerido: 45 y 46 (prioridad 3) antes que 47 (prioridad 4); 45 y 46 tocan `aggregates.py`, `views.py`, `humo.spec.js` y `metricas.md` en funciones distintas: si van en paralelo, el segundo merge resuelve un conflicto trivial (P3).

## Ultimo turno de cada rol

| rol | fecha-hora UTC | que hizo |
|---|---|---|
| release | 2026-10-14 18:50 | Entrega y mergea 43 (`aprobado` -> `entregado` -> main, PR #33, main f74a16f, funcionalidad). Rama ya traia main 41cb46f; `check.sh` en `Todo en verde.` sobre el commit exacto del PR 339b986 (561 backend, 80 vitest, build, 32 e2e). Ficha recortada con `## PR`; espejo quitado de backlog; B2/B5 a `en main` en `ALCANCE.md`. Borrar la rama: denegado en la sesion. pruebas.sh: PRUEBAS_OK (10). |
| revisor | 2026-10-14 16:30 | Revisa 43 (`implementado` -> `revisado`): revision ciega con `revision.md` sin hallazgos, confirmada por el lider (3-2 mine, 3-3 normal por prorroga, 4-4 both; sin regla, sin marcador e Y9S3 a unknown; las cinco filas suman por construccion). Criterios cubiertos por tests y e2e, diff dentro de `archivos:`. Mutaciones: sin prorroga caen 5 tests; `unknown` sobre `conocido` caen 2. Menores, no bloquean: `regla_para` solo la usan los tests; `metricas.md` no nombra `Standard` entre los tipos sin regla. Rama ya al dia con main 41cb46f; `check.sh` en `Todo en verde.` (561 backend, 80 vitest, build, 32 e2e). Sin pushes de codigo. |
| dev | 2026-10-14 15:35 | Implementa 43 (`disenado` -> `implementado`, rama `claude/equipo-dev/43-match-point`): `reglas_partida.py` (solo Ranked desde Y9S4: gana a 4, con 3-3 prorroga a 5, fuente Dexerto), `by_match_point` en `/api/trends/` reusando `_marcador_conocido` extraido de `by_score_state`, panel "Match point" en Tendencias, e2e y fila en `metricas.md`; 20 tests en `test_match_point.py`. Revision ciega: sin bugs, 2 puntos de tests corregidos (filtros que no recortaban, orden de las reglas). `check.sh` en `Todo en verde.` (561 backend, 80 vitest, build, 32 e2e). |
| qa | 2026-10-14 17:35 | Prueba 43 (`revisado` -> `aprobado`). `check.sh` en `Todo en verde.` (561 backend, 80 vitest, build, 32 e2e). Base vacia: cinco filas en 0 y 200 con `until=foo`, `page=-1`, `match_type=`, `map=`, `since=2030-01-01`. Base sembrada con `factories.py` (ranked 0-0 a 4-4 como equipo 0 y como equipo 1, QuickMatch, Y9S3, marcador vacio, 4-0 y tres equipos): mine 3, theirs 2, both 2, normal 13, unknown 6, igual a lo calculado y suma igual a `by_score_state`, tambien con filtros. 3 mutaciones caen (10, 3 y 3 tests). Chunk inicial sin cambio (el panel va en el lazy `Trends`). Sin pushes de codigo. |
| arquitecto | 2026-10-14 23:16 | Disena 45 (`comebacks` en `/api/trends/`: remontadas/derrumbes con umbral fijo 2 sobre `score_before` de toda la partida, solo Y9S4+ y marcador legible en todas las rondas; tabla por diferencia al cambio de lado en cinco tramos; panel en Tendencias con `remontadas.js`), 46 (`first_teammate_death` en `/api/teammates/` como `first_down`: menor `death_elapsed` de tu equipo, empate por `Event.order`, sin evento va al compañero; panel "Primero en caer" en Compañeros) y 47 (claves `gamemodes`/`match_types` en `overrides.json`, `record_unknown` en el parser, listas en `/api/unknown/`, retag leyendo el id del texto `Unknown(<id>)`, sin migracion; tablas en Datos). Sin pushes de codigo. |
| investigador | 2026-10-14 22:18 | Familias 1 (forks nicktstewart, defiancer6s-hub y lumina-r6 de r6-dissect; api.github.com 403), 2 (r6tv.online, Aurelix, r6-replay.com/roadmap), 4 (Refrag nuevo, Leetify, vlr.gg, CS Demo Manager; Dotabuff 403) y 7 (Siege.GG rebalance, FanGraphs, Wilson). 13 ideas nuevas con fuente (45 -> 58 libres), F1 y F7 ampliadas, 4 descartadas con motivo. Sin pushes de codigo. |
| po | 2026-10-14 19:35 | Papel vacio: propone 45 (B7: remontadas y derrumbes, con winrate de partida segun la diferencia al cambio de lado, en Tendencias), 46 (C4: primero de tu equipo en caer y su winrate, por lado, en Compañeros) y 47 (A2: modos y tipos de partida desconocidos en Datos, con etiqueta y retag sin reimportar). Reconcilia `ALCANCE.md` con main f74a16f (B6 y E4 en main). Ideas nuevas B8, B9, E5, F6 y H3: 24 libres (22 al empezar). PRs #1, #14 y #22 siguen abiertos. Sin pushes de codigo. |

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
- Verificar en el PC (Investigador, 2026-10-14): r6-dissect issue #130 reporta replays Y11S3 con `won: true` en los dos equipos en 3 de 5 rondas. `replays/analytics/metrics.py:205` se queda con el ultimo equipo sin avisar, asi que `my_team_won` podria salir al reves en esas rondas. Si tienes un `.rec` Y11S3, mirar si alguna ronda tiene a los dos equipos ganadores (idea P2 de `ALCANCE.md`); si se confirma, es un bug para el PO con prioridad 1. Tambien falta el operador 444310693746 (sale `Unknown(...)`, se puede nombrar en Datos; idea P1).
- Verificar en el PC (Investigador, 2026-10-14 22:11Z, idea P5): dos forks de r6-dissect (nicktstewart y defiancer6s-hub) cambian en Y11S2 (code version 9734089) el patron del DissectID a `8C 61 1A 75 23` y el layout del kill feed; sintoma: jugadores duplicados o faltantes y bajas de gente que no esta en la lista. `docs/formato-rec.md` dice que Y11S3 anda sin cambios, asi que puede afectar solo a Y11S2. Si tienes un `.rec` de Y11S2 (Calypso Casino, 2026-06 a 2026-09), importalo y mira si faltan jugadores o bajas.
- Posible bug para el PO (Investigador, 2026-10-14, idea A4): `by_map` (`aggregates.py:383-402`) agrupa por nombre y slug, pero une el winrate por lado solo por `map_name`. Los mapas con version vieja y rehecha (`Fortress`/`FortressY10`, `ConsulateY7`/`ConsulateY10`, `ClubHouse`/`ClubHouseY10`...) salen como dos filas con el mismo nombre y el mismo winrate de ataque y defensa, mezclado. `by_site` tambien mezcla los sitios de los dos layouts. Leido en el codigo, no reproducido con datos: el PO puede abrirlo como `tipo: bug`.
- Ficha 47 (aviso del Arquitecto, no bloquea): `Match` no guarda el id del modo ni del tipo de partida, asi que el retag lo lee del texto `Unknown(<id>)`; una etiqueta puesta mal no se corrige sobre lo ya importado. Corregirla pediria columnas `gamemode_id`/`match_type_id` con migracion y `recompute` (ficha aparte si la queres).
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
