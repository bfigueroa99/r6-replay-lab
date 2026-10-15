# Estado del equipo de desarrollo autonomo

actualizado: 2026-10-15 09:16 UTC por revisor (sesion 20261015T0912Z; motivo: por estado: 2 implementado; reloj: dev, franja 3)
playbook: origin/main@17f0ae1
rutina: TURNOS_SIN_RASTRO=0 en 48 h | 12 de 56 en 7 dias
pausa: no

## Cola (items con codigo, esperando al humano o en trabajo)

| rama | ficha | estado | horas | compare | PR |
|---|---|---|---|---|---|
| claude/equipo-dev/46-primero-de-tu-equipo-en-caer | docs/backlog/46-primero-de-tu-equipo-en-caer.md | revisado | 0 | [compare](https://github.com/bfigueroa99/r6-replay-lab/compare/main...claude/equipo-dev/46-primero-de-tu-equipo-en-caer?expand=1) | sin PR |
| claude/equipo-dev/47-modos-desconocidos-en-datos | docs/backlog/47-modos-desconocidos-en-datos.md | revisado | 0 | [compare](https://github.com/bfigueroa99/r6-replay-lab/compare/main...claude/equipo-dev/47-modos-desconocidos-en-datos?expand=1) | sin PR |

COLA=2/4  TOTAL=2/6
RESUMEN propuesto=0 disenado=0 en_curso=0 huerfanas=0 implementado=0 revisado=2 con_hallazgos=0 aprobado=0 entregado=0 espera_humano=0 cola=2 total=2 tope_cola=4 tope_total=6 tope_propuesto=6 tope_disenado=3 ideas_libres=58 sin_merge=no pausa=no sin_rastro_48h=0

## Orden de merge sugerido

1. `claude/equipo-dev/46-primero-de-tu-equipo-en-caer`: la mas vieja, sin choque con main 17f0ae1.
2. `claude/equipo-dev/47-modos-desconocidos-en-datos`: sin choque con main ni con la 46 (merge de prueba 46+47 limpio, aunque las dos tocan `views.py` y `humo.spec.js`).

## Alcance

- Funcionalidades que llegaron a `main` en los ultimos 7 dias (`MAIN_7D`): funcionalidad:9 (36-mitades-y-prorroga 37-rivales-repetidos 39-inercia-entre-rondas 40-hora-y-dia-de-la-semana 41-ronda-segun-el-marcador 42-como-se-cierran-tus-rondas 43-match-point 44-records-personales 45-remontadas-y-derrumbes) otros:7.
- Epicas en curso: lado-y-marcador: B1 (36), B4 (39), B2 (41 y 43), B5 (43) y B6 (42) en main; B7 (45, PR #34) en main; B8 y B9 como idea. escuadra: C4 (ficha 46) revisado. temporada-y-modo: A2 (ficha 47) revisado. progreso: E3 (40) y E4 (44) en main; E5 como idea. rivales: D1 (37) en main.
- Papel: PAPEL_TIPOS=funcionalidad:0 otros:0 (la 47 paso a su rama). Cola: COLA_TIPOS=funcionalidad:2 de 2 ramas de trabajo.
- `ALCANCE.md`: 58 ideas libres. Ideas nuevas de este turno: ninguna. Ultimas del Investigador (2026-10-14): A5 mapas para banear, B12 cuanto tardas en ganar, C8 diferencial de trade, C9 oportunidades de trade convertidas, D5 cara a cara en el detalle de partida, E8 banda de ruido en winrates, E9 contra el promedio de tus lobbies, F10 multikills por tamaño, O3 contra la media del operador, O4 participacion en aperturas, O5 presencia y delta por operador, P5 jugadores y kill feed de Y11S2, P6 picks de preparacion; F1 y F7 ampliadas.
- Investigacion: ultima entrada 2026-10-14 22:11Z (familias 1, 2, 4 y 7; antes 3, 5 y 6). Proxima: 3, 5 y 6.

## Papel (rama backlog)

| ficha | titulo | estado | tipo | epica | prioridad |
|---|---|---|---|---|---|
| 46 | Primero de tu equipo en caer | revisado (rama de trabajo) | funcionalidad | escuadra | 3 |
| 47 | Modos y tipos de partida desconocidos en Datos | revisado (rama de trabajo) | funcionalidad | temporada-y-modo | 4 |

Papel vacio (0 propuesto, 0 disenado). Proximo turno por estado: qa para 46 y 47 (otra sesion: esta las reviso); despues release y po.

## Ultimo turno de cada rol

| rol | fecha-hora UTC | que hizo |
|---|---|---|
| release | 2026-10-15 05:50 | Entrega y mergea 45 (`aprobado` -> `entregado` -> main, PR #34, main 17f0ae1, funcionalidad; cierra B7 de lado-y-marcador). Puerta completa: dev/revisor/qa en sesiones distintas, rama con main f74a16f, `check.sh` en `Todo en verde.` sobre el commit exacto del PR 780ee84 (585 backend, 86 vitest, build, 33 e2e). Ficha recortada con `## PR`; espejo quitado de backlog; B7 a `en main` en `ALCANCE.md`. Borrar la rama: el push de borrado no tuvo efecto. pruebas.sh: PRUEBAS_OK (10). |
| dev | 2026-10-15 08:45 | Corrige 46 (`con hallazgos` -> `implementado`): fila de `metricas.md` define el % de "Caíste primero"/"Cayó un compañero"; `_primer_orden_de_muerte` con `Exists` correlacionado y test con el tope de SQLite bajado a 50 (falla sin el arreglo). Implementa 47 (`disenado` -> `implementado`, rama `claude/equipo-dev/47-modos-desconocidos-en-datos`, funcionalidad, A2 de temporada-y-modo): modos y tipos `Unknown(<id>)` anotados por el parser, listados en `/api/unknown/` y Datos, etiquetados por `POST /api/overrides/` y reetiquetados por `retag` sin reimportar; `unknown_ids` y README. Revision ciega: contador de partidas reetiquetadas contado una vez por campo, corregido. `check.sh` en `Todo en verde.` en las dos ramas (46: 603 backend, 86 vitest, build, 34 e2e; 47: 610, 86, build, 35). |
| revisor | 2026-10-15 09:16 | Revisa 46 (segunda pasada) y 47 (`implementado` -> `revisado` las dos). `check.sh` en `Todo en verde.` en las dos ramas (46: 603 backend, 86 vitest, build, 34 e2e; 47: 610, 86, build, 35). 46: los dos hallazgos de la primera pasada corregidos y verificados; revision ciega nueva sin bugs, su unico punto (clasificacion calculada al consultar) lo fijo el diseno y va como aviso. 47: revision ciega sin hallazgos; cada criterio con tests nombrados; largos de campo confirmados (32). Sin pushes de codigo. |
| qa | 2026-10-15 04:50 | Prueba 45 (`revisado` -> `aprobado`). `check.sh` en `Todo en verde.` (585 backend, 86 vitest, build, 33 e2e). Base vacia: listas vacias, cinco tramos en 0, 200 con `until=foo`, `page=-1`, `map=`. Base sembrada con `factories.py` (31 partidas: remontada 0-3, derrumbe 3-0 con `team_index=1` numerado desde 1, pre-Y9S4, ronda faltante, `won` nulo, tres equipos, 25 remontadas para el tope): `matches_known 27`, 26 remontadas con 20 listadas, 1 derrumbe, tramos esperados; filtros coherentes con `by_half`. UI en Chromium: listas, "Se muestran 20 de 26.", enlaces al detalle, consola limpia. Chunk inicial sin cambio. 5 mutaciones caen (4 backend, 1 vitest). Sin pushes de codigo. |
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
  - `git push origin --delete claude/equipo-dev/45-remontadas-y-derrumbes` (mergeada, PR #34)
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
- Ficha 45 (ya en main, PR #34; aviso del Dev, no bloquea): una partida con un `.rec` de ronda faltante, en el medio o al principio, no entra a remontadas, derrumbes ni a la tabla del cambio de lado (evita numeros falsos). Si faltan las ultimas no se detecta: el resultado de la partida ya sale truncado del ultimo `.rec` para toda la app. Con la base real, abrir una remontada y confirmar en el detalle que el marcador estuvo 2 abajo.
- Ficha 45 (ya en main, PR #34; aviso del Revisor, no bloquea): con `matches_known == 0` el panel dice "hace falta Y9S4 o posterior", pero tambien saca partidas Y9S4 con rondas faltantes o sin resultado; cambio de texto de una linea (Trends.jsx:546); el Release no implementa, queda para una ficha chica.
- Ficha 46 (aviso del Dev, no bloquea): `seed_demo` gana todas las rondas de ataque y pierde todas las de defensa, asi que en la demo el panel "Primero en caer" muestra 100 % y 0 % por lado; con la base real, abrir una ronda contada como "caíste primero" y confirmar en el feed que fuiste la primera baja de tu equipo.
- Ficha 46 (aviso del Revisor, no bloquea): la clasificacion "primero en caer" se calcula al consultar (lee `Event` si hay empates), como los Duelos. Si pesa con tu base, la alternativa es una columna `first_team_death` en `RoundPlayer` marcada al importar (migracion + `recompute`), ficha aparte.
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
