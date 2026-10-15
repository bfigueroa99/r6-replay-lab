# Alcance: lo que la app todavia no hace

El mapa de crecimiento del equipo (Directiva de alcance de
`.claude/skills/equipo-dev/SKILL.md`). Vive en la rama
`claude/equipo-dev/backlog`; esta copia del playbook es la semilla que el
primer turno copia alla si no existe. Desde ahi lo mantiene el product owner:
reconcilia estados, agrega al menos 2 ideas por turno y saca de aca las
fichas nuevas. El Investigador (cuando el estado lo pide; por reloj, la
franja 7 de los dias pares) suma lo que trae de
afuera, con `[fuente](url)` en la celda de la idea; su bitacora esta en
`INVESTIGACION.md`.

Como se lee:

- Una tabla por epica. El slug del titulo (`temporada-y-modo`, ...) es el
  `epica:` de las fichas que salen de ella.
- Columnas: `id` (para nombrar la idea en una ficha o en `## Para el
  equipo`), que gana quien usa la app, que datos usa (archivo y campo; si no
  hay dato, no hay idea), tamano (S cabe en un tramo, M en uno o dos, L es
  epica de varios) y estado.
- Estados, siempre en la ultima columna: `idea` (libre), `ficha NN`,
  `en main`, `PR #n` (cubierta por un PR abierto que no es del equipo: no se
  propone mientras siga abierto), `decision (<que>)` (espera la respuesta
  del humano en `## Para el equipo` de `ESTADO.md`; no se propone), `no` (la
  tacho el humano).
- El humano reordena las filas o pone `no` desde la web. Lo que esta mas
  arriba dentro de una tabla se propone antes.

Semilla del 2026-10-10, verificada contra `main` 0b547d7. Reconciliado por el PO
el 2026-10-13 contra `main` e5bad5b (PR #12 mergeado: G4, G5 e I2 en main).
Reconciliado otra vez el 2026-10-13 (sesion 20261013T1915Z) contra `main`
5d2aecc: B1 (#25) y D1 (#27) en main.
Reconciliado el 2026-10-14 (sesion 20261014T0911Z) contra `main` 3438ab2:
B2 tramo 1 (41), B4 (39), E3 (40) y T3 en main.
Reconciliado el 2026-10-14 (sesion 20261014T1911Z) contra `main` f74a16f:
B5 (43), B6 (42) y E4 (44) en main; B7 -> ficha 45, C4 -> ficha 46,
A2 -> ficha 47; nuevas B8, B9, E5, F6 y H3.
Investigador 2026-10-14 (sesion 20261014T2010Z): nuevas B10, C6, D4, F7, F8,
K1-K3, O1, O2 y P1-P4 (epicas nuevas `impacto` y `operadores`).
Investigador 2026-10-14 (sesion 20261014T2111Z): nuevas A4, B11, C7, E6, E7, F9 y
K4; P1 suma Noor, Solid Snake y Calypso Casino; MVP sale de descartadas como E7.
Investigador 2026-10-14 (sesion 20261014T2211Z): nuevas A5, B12, C8, C9, D5, E8, E9,
F10, O3, O4, O5, P5 y P6; F1 y F7 ampliadas.

## Epicas

### temporada-y-modo: temporada y modo de juego

| id | idea | que gana quien usa la app | datos | tam | estado |
|---|---|---|---|---|---|
| A1 | Selector de tipo de partida en la barra de filtros | Filtrar todo por ranked, unranked, rapida o la que sea, y no solo con "solo ranked" | `Match.match_type`; la API ya filtra (`views.py:48`) y `filters/` ya devuelve `match_types`; falta en `Filters.jsx`, que PR #14 tambien toca | S | idea |
| A2 | Etiquetar modos de juego desconocidos en Datos | Un modo nuevo deja de verse como `Unknown(...)` | `gamemode_name` (`header.py:233`) no llama a `record_unknown`, a diferencia de mapas y operadores; candidato de `mercado/2026-09-13`. Incluye tipos de partida (`match_type_name`, `header.py:229`) | S | en main (PR #36) |
| A3 | Temporada como dimension: etiqueta, filtro y comparacion | Saber si mejoraste de una temporada a otra | `Match.game_version` y `code_version` (`models.py:57-58`); tabla version -> temporada en `constants.py`, y las versiones sin nombre se etiquetan en Datos como los mapas | M | idea |
| A4 | Mapas rehechos como su propia fila | Fortress (rework Y10S4), Consulate, Club House y los demas `*Y10` tienen otro ID y otro slug que la version vieja pero el mismo nombre: en Mapas salen dos filas "Fortress" iguales de nombre, y el winrate por lado de las dos es el mismo numero mezclado, porque `by_map` une el lado por `map_name` y no por slug (`aggregates.py:395`); `by_site` tambien agrupa por nombre y mezcla sitios de layouts distintos. Etiquetar la version ("Fortress (2025)") y unir por slug. Incluye un bug de numeros: el PO puede abrirlo como `tipo: bug`. [fuente](https://www.ubisoft.com/en-us/game/rainbow-six/siege/news-updates/seasons/tenfoldpursuit) ("Fortress now has less hallways, bombsites have been balanced") | `MAPS` (`pydissect/constants.py:72-115`: `Fortress` 126196841359 y `FortressY10` en P1, `ConsulateY7`/`ConsulateY10`, `ClubHouse`/`ClubHouseY10`...), `Match.map_slug` y `map_name` (`models.py:53-54`), `by_map` y `by_site` (`aggregates.py:383-414`). Villa cambio de sitios en Y11S3 sin ID nuevo conocido: verificar con `.rec` reales en el PC | S | idea |
| A5 | Mapas para banear | Una señal del Coach con tus 1 o 2 peores mapas por winrate de ronda, por lado y con su muestra, leida como sugerencia de ban; no reabre la pagina de mapas retirada: es una sola señal sobre los agregados por mapa que el Coach ya arma. [fuente](https://aurelix.app/blog/how-to-analyse-r6-siege-replays) | `Match.map_slug`, `Round.my_side`, `RoundPlayer.won`; agregados por mapa de `replays/analytics/aggregates.py` | S | idea |

### lado-y-marcador: mitades, prorroga y presion

| id | idea | que gana quien usa la app | datos | tam | estado |
|---|---|---|---|---|---|
| B1 | Primera mitad, segunda mitad y prorroga | Ver si arrancar en ataque o en defensa te cambia la partida, y como rindes en prorroga | `Round.number`, `overtime_number` (`models.py:89`, guardado y sin exponer), `my_side` | S | en main |
| B2 | Rondas bajo presion | Tu rendimiento en match point, yendo abajo y yendo arriba | `score_before` / `score_after` (`models.py:98-99`). Partida en dos tramos: adelante/empatado/atras (ficha 41) y match point (B5) | M | en main (tramo 1, ficha 41); tramo 2 en main (ficha 43, PR #33) |
| B3 | Metricas por tercios de la ronda segun el reloj | Si te va peor al principio, al medio o al final de la ronda, mas alla de cuando mueres | reloj de los eventos, `death_clock`, `death_elapsed`; candidato #23 de `mercado/2026-09-16`. Nunca anclado al plant | M | idea |
| B4 | Inercia entre rondas | Tu winrate de ronda despues de ganar la anterior contra despues de perderla: si una ronda perdida te arrastra a la siguiente | `Round.my_team_won` de la ronda `number - 1` de la misma partida (`models.py:94`); fila nueva en `docs/metricas.md`, con banda de ruido como el #10 | S | en main |
| B5 | Match point y ronda decisiva (segundo tramo de B2) | Tu rendimiento cuando una ronda gana o pierde la partida | `score_before` + `Match.match_type`/`gamemode` para saber a cuanto se gana; las reglas por modo (prorroga, ventaja de 2) van en una tabla de `constants.py`, y un modo sin regla conocida no cuenta. Implementar despues de la ficha 41 | M | en main (ficha 43, PR #33) |
| B6 | Como ganas y pierdes tus rondas | Por lado y mapa, cuantas rondas se cierran por eliminacion, por tiempo o por objetivo: si en defensa pierdes por tiempo o por quedarte sin gente | `Round.win_condition` y `win_condition_certain` (`models.py:95-96`), hoy solo en el detalle de una ronda. Las inferidas (plant/defuse de temporadas nuevas) van en su propia fila "inferida" y no se desglosan, por `docs/formato-rec.md` | S | en main (ficha 42) |
| B7 | Remontadas y derrumbes | Lista de partidas que ganaste yendo abajo por 2 o mas rondas y de las que perdiste yendo arriba por 2 o mas, con tu winrate de partida segun la diferencia en el cambio de lado: si sueltas las partidas que tienes ganadas | `Round.score_before` por ronda (mismo corte `code_version >= Y9S4` que `by_score_state`, `aggregates.py:543`) + `Match.won`; maxima diferencia a favor y en contra por partida | S | en main (PR #34) |
| B8 | Primera ronda de cada mitad | Tu winrate en la ronda 1 y en la primera ronda tras el cambio de lado, contra el resto: si arrancas frio cada mitad. En Siege no hay ronda de pistola, pero la primera de cada lado marca el tono y se juega sin informacion | `Round.number` y la frontera de mitad que ya calcula `by_half` (`aggregates.py:456`, `_lado_inicial`); `Round.my_team_won`; sale en `/api/trends/` | S | idea |
| B9 | Rondas cortas y largas | Tu winrate de ronda segun cuanto duro, por lado: si en ataque ganas solo las ejecuciones rapidas o si en defensa te quiebras en las rondas largas | `Round.clock_start` y `clock_end` (`models.py:101-102`, propiedad `Round.duration`), hoy sin mostrar; tramos fijos de duracion. Las rondas con `possible_plant` van en su propia fila, porque el reloj despues del plant no mide lo mismo (`docs/formato-rec.md`) | S | idea |
| B10 | Partidas cerradas y partidas holgadas | Tu winrate y rating en partidas que se definieron por 1 ronda o fueron a prorroga, contra las que se definieron por 3 o mas: si cierras las parejas o solo ganas las que vas sobrado. B7 mira la trayectoria; esto, el margen final. [fuente](https://aurelix.app) (tarjeta "Close games") | marcador final de la ultima ronda (`Round.score_after`, `models.py:99`) y `Round.overtime_number` (`models.py:89`); `Match.won`. Mismo corte `code_version >= Y9S4` que `by_score_state` para el marcador | S | idea |
| B11 | Cuando matas | La distribucion de tus bajas en tramos de 30 s de la fase de accion, por lado, al lado de "Cuando mueres": si sacas tus bajas en la apertura o en el cierre, y en defensa cuantas bajas tempranas consigues. PR #22 cuenta solo los primeros 15 s por mapa; esto es la curva entera. [fuente](https://tracker.gg/r6siege/articles/r6-ow-v3-0) ("number of kills in the first 30 seconds", 2022-10-01) | reloj de tus eventos `KILL` (`Event`, `pydissect/events.py`) contra `clock_max` como `death_elapsed` (`models.py:150`, `docs/formato-rec.md`); los mismos tramos que "Cuando mueres" (`docs/metricas.md:205`) | S | idea |
| B12 | Cuanto tardas en ganar | Duracion media de tus rondas ganadas y perdidas, por lado y separada en por eliminacion y sin eliminacion (post-plant y retake no: el plant solo se infiere). Puede ir como tramo de B9. [fuente](https://aurelix.app/) | `Round.clock_start` y `clock_end`, `win_condition`, `my_side`, `my_team_won` (`models.py`) | S | idea |

### escuadra: el equipo con el que juegas

| id | idea | que gana quien usa la app | datos | tam | estado |
|---|---|---|---|---|---|
| C1 | Winrate por grupo exacto de compañeros | Saber que stack completo te funciona, no solo que pares | `teammate_synergy` (`aggregates.py:383`) agrupa de a uno; `team_index` y `player` por ronda | M | idea |
| C2 | Matriz de trades del equipo | Quien venga a quien, y a quien nadie venga | `Event.traded` (`models.py:195`), `trade_kills`, `was_traded` (`models.py:146-147`) | M | idea |
| C3 | Alineacion de operadores de tu equipo contra el resultado | Que combinaciones de tu lado ganan mas por mapa y lado | `RoundPlayer.operator` de tus compañeros por ronda, `operators/catalog/` | M | idea |
| C4 | Primero de tu equipo en caer | Cuantas rondas eres el primero de tu equipo en morir (no solo la primera muerte de la ronda) y el winrate de esas rondas contra cuando cae otro: si tu forma de abrir le cuesta rondas al equipo | `RoundPlayer.death_elapsed` de las filas de tu equipo por ronda (`team_index`, `models.py:127,150`); hoy `opening_death` solo mira la primera muerte de toda la ronda | S | en main (PR #35) |
| C5 | Solo, en duo o en stack | Tu winrate y rating segun cuantos compañeros habituales (los que aparecen contigo en 5 o mas partidas) juegan esa partida: 0, 1, 2 o mas. Responde si te conviene entrar solo o esperar a tu grupo | filas `RoundPlayer` de tu equipo por partida (`team_index`, `player`, `is_me=False`); habitual = `player` con N partidas compartidas, como `teammate_synergy` (`aggregates.py:542`). N fijo en el diseno, sin ajuste en la UI | S | idea |
| C6 | Tiempo de refrag | Histograma de cuantos segundos tarda tu equipo en matar a quien te mato (0-1, 1-2, 2-3, 3-5, 5-10, mas de 10 s), por lado: muestra los "casi trades" que la ventana de trade deja afuera y si el equipo llega tarde, sin depender de la ventana (`docs/metricas.md`, seccion trades). [fuente](https://r6-replay.com) ("refrag timing") | reloj de los eventos `KILL` (`pydissect/events.py`) y el `team_index` de autor y victima; la misma recorrida que `annotate_trades` (`replays/analytics/metrics.py:201`) sin cortar en la ventana | S | idea |
| C7 | Teamkills | Cuantos compañeros mataste y cuantas veces te mato uno, con quien, y el winrate de las rondas con un teamkill: hoy Duelos los descarta y ninguna pantalla los muestra. El rating de Siege.GG los cuenta aparte. [fuente](https://siege.gg/news/support-value-in-siege-explained-with-the-new-rating-model) (2025-10-31, "Teamkills per Round") | feed de bajas con el `team_index` de autor y victima en esa ronda: el mismo descarte de `aggregates.py:953` invertido; `Round.my_team_won`. No toca el Rating | S | idea |
| C8 | Diferencial de trade | Que proporcion de tus muertes se vengo menos que proporcion de tus bajas te devolvieron (te mataron dentro de la ventana): si cambias vidas a favor o en contra. La primera mitad ya existe; la segunda no. [fuente](https://siege.gg/blog/946-player-rating-rebalance) | Kill feed (`Event`) y `TRADE_WINDOW_SECONDS` (`config/settings.py:185`); columna nueva en `RoundPlayer` calculada al importar en `replays/analytics/metrics.py`, junto a `traded` y `trade_kills` | S | idea |
| C9 | Oportunidades de trade convertidas | Hoy `trade_kills` no tiene denominador. Oportunidad = un rival mato a un compañero mientras seguias vivo; conversion = mataste a ese rival dentro de la ventana. Porcentaje por lado y operador; la oportunidad es temporal, no espacial, y `metricas.md` lo dice. [fuente](https://refrag.gg/blog/refrag-rating-explained/) | Kill feed con tiempos, equipos de la ronda (`Round.teams`), `TRADE_WINDOW_SECONDS`; distinto de C2 (matriz del equipo) | S | idea |

### rivales: los rivales de tus replays

| id | idea | que gana quien usa la app | datos | tam | estado |
|---|---|---|---|---|---|
| D1 | Rivales repetidos | Lista de los que te tocaron en 2 o mas partidas, con tu record contra cada uno; el detalle ya esta en la pagina de jugador | filas `RoundPlayer` del equipo rival por `profileID`. Solo gente de tus replays: no es scouting | S | en main |
| D2 | Meta rival por mapa y sitio | Que operadores te ponen enfrente en cada mapa y como te va contra cada uno | extiende `rounds_vs_operator` (`aggregates.py:771`) con mapa y sitio; muestra chica, va con banda de ruido como el #10 | M | idea |
| D3 | Abandonos | Partidas con alguien que se fue, y tu winrate en 5v4 y 4v5 | eventos `PLAYER_LEAVE` (`constants.py:294`), que hoy solo cuentan como muerte (`stats.py:126`). Verificar que el evento sigue saliendo en temporadas nuevas | S | idea |
| D4 | Stacks rivales repetidos | Grupos de 2 o mas rivales que te tocaron juntos en 2 o mas partidas, con tu record contra cada grupo: reconocer al stack que ya te gano, no solo a la persona (D1 va de a uno). Solo gente de tus replays: no es scouting. [fuente](https://aurelix.app) ("Opponent Tracking") | filas `RoundPlayer` del equipo rival por partida (`team_index`, `player`), agrupadas por el conjunto de `profileID`; reusa la consulta de rivales repetidos de D1 | S | idea |
| D5 | Cara a cara en el detalle de partida | En `MatchDetail`, junto a cada rival y compañero, cuantas veces lo cruzaste antes de esa partida y tu record contra el o con el. Lleva D1 (en main) a la pantalla de la partida, solo con tus replays. [fuente](https://r6tv.online/how-it-works) | `RoundPlayer.player`, `Match.played_at`, `Match.won`; la consulta de rivales repetidos de D1 acotada a fechas anteriores | S | idea |

### progreso: progreso y metas

| id | idea | que gana quien usa la app | datos | tam | estado |
|---|---|---|---|---|---|
| E1 | Curva de aprendizaje por operador | Tu rating en las primeras N rondas con un operador contra las siguientes: si practicarlo rinde | `RoundPlayer` por operador ordenado por fecha, como `trend_by_match`; fila nueva en `docs/metricas.md` | M | idea |
| E2 | Metas personales | Fijar una meta (KST 70 %, menos de 30 % de muertes sin trade) y ver si la cumpliste en cada sesion | modelo nuevo de metadatos + POST de accion explicita que `CLAUDE.md` hoy no admite; sesiones de `sessions/` | M | decision (POST nuevo: ver Para el humano) |
| E3 | Rendimiento por hora del dia y dia de la semana | Saber si juegas peor de madrugada o los domingos, con muestra suficiente para creerlo | `Match.played_at` (`models.py:50`), ya en hora local (`USE_TZ = False`, `TIME_ZONE` en `config/settings.py:143`); agrupar por franja de 3 h y por dia con `ExtractHour`/`ExtractWeekDay` | S | en main |
| E4 | Records personales | Tu mejor partida (rating, bajas), tu ronda con mas bajas, tu 1vX mas grande y tu mejor dia, cada uno con enlace a la partida: lo que da gusto volver a mirar y marca el techo a superar | `RoundPlayer.kills`, `one_vx` y rating por partida (`trend_by_match`), `trend_by_day`; un agregado nuevo que devuelve el maximo con su `match_id`. La racha actual es de PR #14: no se duplica | S | en main (ficha 44) |
| E5 | Mapas que mejoran y mapas que empeoran | En Tendencias, junto a la comparacion de periodos que ya muestra `Trends.jsx`, por cada mapa con muestra en los dos periodos, tu rating y winrate de las ultimas N partidas contra las N anteriores, ordenado por la diferencia: en que mapa estas mejorando y cual se te esta cayendo, con la banda de ruido que ya usa la comparacion general | `compare_periods` (`aggregates.py:1316`, `_periodo_por_partidas` y `_ruido`) hoy compara el total; agruparlo por `round__match__map_slug` como `by_map`. Mapas sin muestra minima en un periodo no se listan | S | idea |
| E6 | Partida despues de perder seguido | Tu winrate en la partida siguiente segun cuantas derrotas seguidas llevabas en la sesion (0, 1, 2, 3 o mas) y cuantos minutos pasaron desde la anterior: si conviene cortar despues de dos derrotas. B4 mira rondas; la curva de sesion mira la posicion; la racha de PR #14 es solo un indicador. [fuente](https://shattered.io/rainbow-six-siege-ranks-2026/) (2026-06-13, "after two or three frustrating losses") | `Match.won` y `Match.played_at` (`models.py:50`) ordenados dentro de cada sesion (`_sessions_raw`, `aggregates.py:790`); banda de ruido por fila | S | idea |
| E7 | Puesto en el lobby | En cada partida, tu lugar entre los 10 jugadores por Rating, y en Tendencias cuantas veces fuiste el mejor de la partida, el mejor de tu equipo o el ultimo: el Rating suelto no dice si arrastraste o te arrastraron. [fuente](https://tracker.gg/r6siege/articles/r6-ow-v3-0) ("MVPs" en el historial, 2022-10-01) | `rating_points_expr` (`aggregates.py:99`) sobre las filas `RoundPlayer` de los 10 jugadores de la partida (ya se guardan todas); `team_index` para el puesto dentro del equipo | S | idea |
| E8 | Banda de ruido en winrates y tasas | Junto a cada % (mapa, operador, compañero, aperturas) el intervalo de Wilson o su limite inferior, y el Coach compara ese limite y no la tasa cruda: 10 de 15 da 67 % pero todavia no se distingue de 50 %. Variante: ordenar por winrate regresado a tu media, `(exitos + p*k) / (n + k)`, con `k` fijado y documentado (no hay `k` publicado para Siege). [fuente](https://math.unm.edu/~james/Agresti1998.pdf), [fuente](https://blogs.fangraphs.com/randomness-stabilization-regression) | Los conteos que ya devuelve `replays/analytics/aggregates.py`; `metricas.md:187` ya dice que "vs. promedio" no trae banda de ruido | M | idea |
| E9 | Tus numeros contra el promedio de tus lobbies | KPR, HS%, aperturas ganadas, sobrevives, KST y muertes sin trade comparados con el promedio de los otros 9 jugadores de tus replays; resalta tu metrica mas por encima y la mas por debajo. Sesgo de seleccion (solo tus lobbies) anotado en `metricas.md`. Distinto de E7 (puesto por partida). [fuente](https://leetify.com/blog/profiles-update/) | `RoundPlayer` de los 10 jugadores de cada ronda (`kills`, `opening_kill`, `survived`, `kst`); `aggregates.py` | M | idea |

### revision-de-rondas: revisar rondas

| id | idea | que gana quien usa la app | datos | tam | estado |
|---|---|---|---|---|---|
| F1 | Buscador de rondas entre partidas | Encontrar todas tus rondas de un tipo (clutch, apertura perdida sin trade, ronda perdida tras abrir ganando) y saltar al detalle de cada una Ampliacion (2026-10-14): filtro por composicion (1 a 5 operadores de tu equipo + mapa, sitio, resultado) con su winrate. [fuente](https://r6tv.online/how-it-works) | banderas de `RoundPlayer` (`one_vx`, `entry_kill`, `untraded_death`, `models.py:140-148`). PR #14 enlaza señales del coach a rondas: revisarlo antes de disenar para no duplicar | M | idea |
| F2 | Notas y marcadores por ronda | Anotar que paso en una ronda y volver a las marcadas | modelo nuevo + POST de accion explicita; candidato #22 de `mercado/2026-09-16` | M | decision (POST nuevo: ver Para el humano) |
| F4 | Tira de rondas en el listado de partidas | En Partidas, cada fila muestra la secuencia de rondas ganadas y perdidas (y el lado) y no solo el marcador final: se ven las remontadas y los derrumbes sin abrir la partida | `Round.my_team_won`, `my_side`, `number` por partida; `match_list` (`views.py`) agrega una lista corta por partida en la misma consulta paginada. PR #14 toca `Matches.jsx` (filtros): disenar sin pisarlo o esperar | S | idea |
| F3 | Cambios de operador y spawn en la linea de tiempo | Ver en el detalle de la ronda quien cambio de operador y desde que spawn salio cada uno | eventos `OPERATOR_SWAP` (`constants.py:292`), hoy una linea generica en `MatchDetail.jsx`; `spawn` ya viene en `matches/<id>/` y ninguna pagina lo pinta | S | idea |
| F5 | Ventaja numerica tirada | Rondas que tu equipo perdio despues de quedar con un jugador mas (o dos), contadas por lado y mapa, con enlace a cada una: el error que mas duele y que el marcador no muestra | orden de las bajas por ronda (`Event` de tipo kill con su reloj y el `team_index` de victima y autor), conteo de vivos por equipo; `Round.my_team_won`. Los abandonos (`PLAYER_LEAVE`) cuentan como baja, igual que en `stats.py` | M | idea |
| F6 | Saltar a la ronda desde los records y las listas | Desde Records, Remontadas y Clutches del Coach, el enlace abre el detalle de la partida ya posicionado en la ronda que importa (`#ronda-N`) y no en la primera | `RoundPlayer.round.number` ya esta en los agregados (`_record_de_ronda`, `aggregates.py:314`); ancla en `MatchDetail.jsx`. PR #14 agrega flechas de ronda en `MatchDetail.jsx`: disenar sin pisarlo o esperar | S | idea |
| F7 | Matriz de duelos de la partida | En el detalle de una partida, una tabla 5x5 de quien mato a quien (con headshots): ver de un vistazo que rival te paso por encima esa partida. Duelos agrega entre partidas; esto es una sola. [fuente](https://cs-demo-manager.com/changelog) (v3.5.0, "players duels matrix") Ampliacion (2026-10-14): selector Todas / Solo aperturas, como la matriz "First Kills" de vlr.gg. [fuente](https://www.vlr.gg/188013/velaris-vs-clg-red-complexity-paradox-invitational-playoffs-lr3/?game=all&tab=performance) | eventos `KILL` de la partida con autor, victima y `headshot` (`Event`, `models.py`); `matches/<id>/` ya trae el feed por ronda | S | idea |
| F8 | Duracion del multikill | Para cada ronda con 2 o mas bajas tuyas, los segundos entre la primera y la ultima: separa el multikill de un solo pico del que se arma a lo largo de la ronda. Columna en Records y filtro del buscador F1. [fuente](https://cs-demo-manager.com/changelog) (v3.11.0, "how long a multi kill event took") | reloj de tus eventos `KILL` por ronda; `RoundPlayer.kills`. Metrica nueva al importar en `metrics.py` + fila en `docs/metricas.md` | S | idea |
| F9 | La ronda para revisar de la sesion | En cada sesion, la app elige una ronda perdida para mirar en el juego (primero una ventaja numerica tirada, despues una apertura tuya sin trade) y dice partida, numero de ronda y archivo: el consejo de coaching de revisar una derrota por sesion, sin tener que buscarla. Implementar despues de F5 o con la regla de apertura sola. [fuente](https://shattered.io/rainbow-six-siege-ranks-2026/) ("Review one loss per session in the replay system") | banderas de `RoundPlayer` (`opening_death`, `untraded_death`, `models.py:140-148`), `Round.my_team_won`, sesiones (`aggregates.py:876`), `Match.source_path` (`models.py:49`) para el nombre del archivo | S | idea |
| F10 | Multikills por tamaño: 2K, 3K, 4K y ace | Hoy solo existe `multikill_pct` (rondas con 2 o mas). Conteo por tamaño en el scoreboard de la partida y en Jugador, con el ace aparte. Distinto de E4 y F8. [fuente](https://cs-demo-manager.com/changelog), [fuente](https://www.vlr.gg/188013/velaris-vs-clg-red-complexity-paradox-invitational-playoffs-lr3/?game=all&tab=performance) | `RoundPlayer.kills` por ronda; `aggregates.py:143` ya cuenta `multikill_rounds` | S | idea |

### impacto: cuanto mueve cada baja la probabilidad de ganar la ronda

La tecnica de HLTV Rating 3.0 ("Round Swing") y Leetify Rating, con la tabla
armada sobre las rondas importadas (no hay tabla publica para Siege: los dos
equipos de cada ronda aportan muestra). Nada de dano, utilidad ni economia:
solo el conteo de vivos.

| id | idea | que gana quien usa la app | datos | tam | estado |
|---|---|---|---|---|---|
| K1 | Tabla de conversion por estado de vivos | Cuanto ganas cuando llegas a 5v4, 4v3, 2v1... y cuanto pierdes en 4v5, por lado, contra la misma tabla de todas las rondas importadas: si sueltas ventajas o das vuelta desventajas mas que lo normal. Es la base de K2 y K3; F5 lista rondas, esto da las tasas. [fuente](https://nomiun.substack.com/p/flaws-of-win-probability) | feed de bajas por ronda con el `team_index` de la victima (`Event`), `PLAYER_LEAVE` como baja (igual que `stats.py:126`), `Round.my_team_won`, `my_side`; la misma recorrida que "segundos en inferioridad" del resumen de ronda. Banda de ruido por estado con poca muestra | M | idea |
| K2 | Impacto por baja (probabilidad agregada) | Un numero por ronda y por partida que pesa distinto la baja que abre un 5v5 de la que remata un 5v2: cuanto movio tus bajas y tus muertes la chance de ganar. Las bajas que vengan una muerte (trade) se reparten entre quien mata y el vengado. Implementar despues de K1 | delta de la tabla K1 por cada baja y muerte tuya, calculado al importar en `metrics.py` (columna nueva en `RoundPlayer`, migracion + `recompute`); `Event.traded` para el reparto. Fila nueva en `docs/metricas.md`; no reemplaza al Rating. [fuente](https://www.hltv.org/news/42485/introducing-rating-30), [fuente](https://leetify.com/blog/introducing-leetify-rating/) | M | idea |
| K3 | Clutch: intentos, conversion y lo esperado | Hoy `one_vx` solo cuenta los clutches ganados. Contar tambien los perdidos (cada ronda en que quedaste ultimo frente a X), con el % por X y por lado y, con K1, cuantos ganaste contra cuantos se esperaban. [fuente](https://siege.gg/blog/946-player-rating-rebalance), [fuente](https://www.vlr.gg/713548/vlr-cl-knowers-come) | el mismo calculo de `one_vx` (`metrics.py`, logica de r6-dissect) sin filtrar por ronda ganada: columna nueva `clutch_vs` al importar; la parte "esperado" despues de K1 | S | idea |
| K4 | El ultimo minuto del ataque | Con cuantos vivos de cada lado llegas a falta de 60 s en tus rondas de ataque y cuanto conviertes desde cada estado: si llegas al ultimo minuto sin gente o con gente y sin cerrar. K1 da la conversion por baja; esto corta por reloj. [fuente](https://boostroom.com/blog/rainbow-six-siege-common-mistakes-beginners-should-avoid) (2026-05-26, "Reaching the final minute with no finish plan") | conteo de vivos por equipo recorriendo el feed (la misma recorrida que "segundos en inferioridad") cortado en `clock == 60`; `Round.my_team_won`, `win_condition`. Las rondas con `possible_plant` antes de ese minuto van aparte: despues del plant el reloj mide otra cosa (`docs/formato-rec.md`) | S | idea |

### operadores: tus operadores segun el contexto

| id | idea | que gana quien usa la app | datos | tam | estado |
|---|---|---|---|---|---|
| O1 | Operador por sitio contra la base del sitio | Por mapa y sitio, tu winrate de ronda con cada operador menos tu winrate en ese sitio: que operador te rinde en Cocina de Oregon y cual te hunde, desde 10 rondas y con banda de ruido. Hoy `by_operator` y `by_site` van por separado. [fuente](https://aurelix.app/blog/how-to-analyse-r6-siege-replays) | `RoundPlayer.operator`, `Round.site`, `round__match__map_slug`, `Round.my_team_won`; `_ruido` de `aggregates.py` | S | idea |
| O2 | Rol inferido de la ronda | Cada ronda tuya clasificada por una regla a la vista (entrada: `entry_kill` o muerte de apertura; ancla: defensa con muerte tardia o vivo al final; el resto, soporte) y tu winrate y rating por rol y lado. Sin coordenadas no distingue roamer de ancla por posicion: la regla lo dice. [fuente](https://r6-replay.com/roadmap) ("Role Detection") | `entry_kill`, `opening_death`, `death_elapsed` (`models.py:140-150`), `my_side`, lado del operador en `operators/catalog/`. Umbral de "muerte tardia": calibrar con la base real | M | idea |
| O3 | Tu operador contra la media de ese operador | Tu KPR, KST, supervivencia y aperturas con un operador comparados con la media y el desvio de todos los que lo jugaron en tus replays, rivales incluidos: un ancla no queda castigada por matar poco. Solo la normalizacion; Siege.GG no publica pesos, asi que no se copia un rating. [fuente](https://siege.gg/blog/946-player-rating-rebalance), [fuente](https://siege.gg/news/support-value-in-siege-explained-with-the-new-rating-model) | `RoundPlayer.operator`, `kills`, `kst`, `survived`, `opening_kill` de los 10 jugadores | M | idea |
| O4 | Participacion en aperturas | Porcentaje de tus rondas en que estuviste en el primer duelo, por lado y operador: separa al que entra del que ancla. Hoy se muestra cuantas aperturas ganas, no cuantas veces te metes. Complementa O2 sin depender de el. [fuente](https://refrag.gg/blog/refrag-rating-explained/) | `RoundPlayer.opening_kill` y `opening_death` sobre las rondas jugadas | S | idea |
| O5 | Presencia y delta de winrate por operador | En Operadores, por operador y lado: % de tus rondas de ese lado jugadas con el y su winrate menos tu winrate base del lado. Version global de O1; puede ser su primer tramo. [fuente](https://r6tv.online/how-it-works), [fuente](https://aurelix.app/blog/how-to-analyse-r6-siege-replays) | `RoundPlayer.operator`, `side`, `won`; tabla de `frontend/src/pages/Operators.jsx` | S | idea |

### datos: datos y configuracion

| id | idea | que gana quien usa la app | datos | tam | estado |
|---|---|---|---|---|---|
| G1 | Calidad de datos | Ver las partidas con avisos del parser o leidas con una version vieja, y recalcularlas sin abrir una consola | `Match.warnings` (`models.py:69`, hoy solo por partida), `Match.parser_version` (`models.py:68`, sin exponer), `recompute.py` | M | idea |
| G2 | Excluir una partida de los agregados | Sacar una custom o una partida rara de tus numeros sin borrarla, y volver a meterla | campo nuevo + migracion + POST; reversible por diseno (nunca borra) | M | decision (POST nuevo: ver Para el humano) |
| G3 | Unir jugadores y alias desde Datos | Juntar dos perfiles que son la misma persona | alias de `Player`, `retag.py`. Reescribe datos: disenar reversible (tabla de equivalencias) o va a P10 | M | idea |
| G4 | Boton de backup en Datos | Respaldar la base desde la app (deuda del #16) | `replays/backup.py` + POST | S | en main |
| G5 | Carpeta de replays desde la UI | Fijar `REPLAY_DIR` sin editar un `.env` (deuda del #19 y #20) | `config/replay_dir.py` + POST | S | en main |

### exportar: exportar y compartir en local

| id | idea | que gana quien usa la app | datos | tam | estado |
|---|---|---|---|---|---|
| H1 | Informe imprimible de una partida | Una pagina limpia para imprimir o guardar como PDF desde el navegador y mandarsela a quien te entrena | detalle de partida; solo CSS de impresion, sin dependencias | S | idea |
| H2 | CSV por ronda y jugador | Cada fila de `RoundPlayer` exportable para analizar por fuera | tabla nueva en `export.py`; sin `assists` ni `score` | S | idea |
| H3 | CSV de las tablas nuevas de Tendencias | Exportar mitades, inercia, marcador, match point, cierres de ronda y hora/dia como las demas tablas, para analizarlas en una planilla | `TABLES` de `export.py:22` hoy no incluye `by_half`, `by_previous_round`, `by_score_state`, `by_match_point`, `round_endings`, `by_hour` ni `by_weekday` (fichas 36-43); el selector de Exportar las toma de `export.tables()` | S | idea |

### escritorio: app de escritorio

| id | idea | que gana quien usa la app | datos | tam | estado |
|---|---|---|---|---|---|
| I1 | Abrir la carpeta de una partida | Un boton en el detalle que abre la carpeta del replay | `Match.source_path` (`models.py:49`, sin exponer) + `shell.openPath` (`frontend/electron/main.cjs:179`). Toca Electron: lo mergea el humano, "verificado solo en nube" | S | idea |
| I2 | Importacion automatica al aparecer una partida | No tener que apretar Importar | vigia de carpeta | M | en main |

### datos-nuevos-del-parser: campos que el `.rec` tiene y `pydissect/` todavia no lee

Las llena el Investigador cuando un parser abierto (primero r6-dissect, del
que `pydissect/` es un port) decodifica algo nuevo. Cada idea dice que campo,
donde lo encontro (archivo y commit) y que pantalla lo usaria. Se verifican
con `.rec` reales en el PC antes de prometer un numero: la nube no tiene
replays.

| id | idea | que gana quien usa la app | datos | tam | estado |
|---|---|---|---|---|---|
| P1 | Catalogo Y10S4 a Y11S3 | Las partidas nuevas muestran el operador y el mapa con nombre y no `Unknown(...)`, y la temporada se lee bien (base de A3): operador 444310693746 (atacante; `SolidSnake` en el fork), code versions Y10S4 = 9394857 e Y11S1 = 9578674, mapa FortressY10 = 398899676157. [fuente](https://github.com/redraskal/r6-dissect/issues/130) (2026-09-30), [fuente](https://github.com/ImAAhmad/r6-dissect/tree/main/dissect) (`version.go`, `header.go:125,214`) | `pydissect/constants.py`: `OPERATORS`, `OPERATOR_SIDES`, `CODE_VERSIONS`, `MAPS_EXTRA`. Hoy no rompe (`header.py:185` cae en `Unknown` y `record_unknown`), pero el lado de ese operador sale `None`. Ubisoft (2026-10-14): el atacante nuevo de Y11S1 es Solid Snake ([Silent Hunt](https://www.ubisoft.com/en-us/game/rainbow-six/siege/news-updates/seasons/silenthunt)), el candidato mas probable; Dokkaebi se rehizo en Y11S2 y podria traer ID nuevo; Noor, de Y11S3, es defensor ([nota](https://news.ubisoft.com/en-us/article/4qqpGJZSWrrS3Ko2hYvviK/rainbow-six-siege-operation-split-fire-new-operator-noor-3v3-arcade-mode-wasteland-circuit-event-and-more)), asi que 444310693746 no es Noor. Mapa nuevo Calypso Casino en Y11S2 ([System Override](https://www.ubisoft.com/en-us/game/rainbow-six/siege/news-updates/seasons/systemoverride)), sin ID publicado: sale de `record_unknown` en el PC. Verificar con `.rec` reales en el PC | S | idea |
| P2 | Ronda con los dos equipos marcados como ganadores | En replays Y11S3 r6-dissect ve `won: true` en los dos equipos en 3 de 5 rondas. `metrics.py:205` se queda con el ultimo sin avisar, asi que `my_team_won` puede salir al reves y mover todos los winrates. Desempatar con el marcador (`score` contra `startingScore`) o dejar la ronda sin ganador y anotar un aviso en `Match.warnings`. [fuente](https://github.com/redraskal/r6-dissect/issues/130) | `teams[i].won`, `score`, `startingScore` (`pydissect/match.py:95`, `header.py:133`); `analyse_round` (`replays/analytics/metrics.py:204-208`). Posible bug: verificar con `.rec` Y11S3 reales en el PC antes de escribir la ficha | S | idea |
| P3 | Derribado (DBNO) y quien remata | Separar la baja de quien derriba de la de quien remata, y contar los derribos: arregla bajas atribuidas al jugador equivocado (issue #115 de r6-dissect). Lo lee un PR sin mergear: flag 20 bytes despues del headshot, o el marcador `22 96 E2 29 7F`. [fuente](https://github.com/redraskal/r6-dissect/pull/126) (`feedback.go`) | `pydissect/events.py`, `read_match_feedback`; columnas nuevas en `Event`. Heuristica sin mergear upstream: portar solo despues de verificar con `.rec` reales en el PC | M | idea |
| P4 | Scoreboard con el formato Y10S4+ | Leer las bajas del scoreboard con los offsets nuevos desde Y10S4 y conciliarlas con el feed: menos rondas con bajas de mas o de menos en temporadas nuevas. [fuente](https://github.com/redraskal/r6-dissect/pull/126) (`scoreboard.go`, rama `CodeVersion >= Y10S4`) | `pydissect/events.py` `read_scoreboard_*`, que hoy usa los offsets viejos sin rama de version. `assists` y `score` siguen sin exponerse. Verificar con `.rec` reales en el PC | M | idea |
| P5 | Jugadores y kill feed de Y11S2 | Desde code version 9734089 dos forks independientes buscan el DissectID con `8C 61 1A 75 23` y no `33 D8 3D 4F 23`, y el kill feed deja el salto fijo de 38 bytes por un payload tras `22 D9 13 3C BA` (headshot sin decodificar). Sintoma: jugadores duplicados o faltantes. `formato-rec.md` dice que Y11S3 anda: puede ser solo Y11S2. Verificar con `.rec` reales en el PC. [fuente](https://github.com/defiancer6s-hub/r6-dissect/commit/26213be8519e0b1601b011b469627d1f6b7a992c), [fuente](https://github.com/nicktstewart/r6-dissect/commit/dd6fbc12206fc06f25afb3a46c78e12a7e641ea4), [fuente](https://github.com/nicktstewart/r6-dissect/blob/main/codex-docs/Y11S2_format_overhaul.md) | `pydissect/events.py:42` (`ID_INDICATOR`), `:46` (`UI_ID_INDICATOR`), `:245` (`r.skip(38)`); `constants.py` (`CODE_VERSIONS`) | M | idea |
| P6 | Picks de operador en la preparacion (replays antes de Y9S3) | lumina-r6 distingue el swap a mitad de ronda (`1A 5E F7 D9 9D`) del pick en preparacion (`22 B6 B7 1D D2` + 10 bytes) y descarta `op == 0`; los swaps por ronda pasan de 0-5 a 10-14 en sus 9 replays. Alimenta F3 y C3 en replays viejos. Verificar con `.rec` reales en el PC. [fuente](https://github.com/lumina-r6/siege-dissect/commit/bf3e6c5152cd1e6f4f2ead45b43bbc5f9c3eedc7) | `pydissect/events.py:149-166` (`read_atk_op_swap` hace `skip(5)` a ciegas) | S | idea |

### deuda-y-tests: no son funcionalidad

Entran por la regla de mezcla de la Directiva (solo con 3 funcionalidades
esperando en el papel) o como bug si lo son. Su estado es `idea (tests)` o
`idea (deuda)`: libres, pero `estado.sh` no las cuenta como ideas libres.

| id | idea | que gana quien usa la app | datos | tam | estado |
|---|---|---|---|---|---|
| T1 | Barrido de parametros borde sobre toda la API como test de Django | Ningun filtro raro vuelve a dar 500 (las fichas 32 y 33 salieron de barridos a mano; el PO del 2026-10-10 repitio 19 endpoints x ~50 parametros sin dejar script) | `backend/tests/test_barrido_api.py`: recorre las 18 rutas GET de `replays/urls.py` (pk 1 y 999999) con 14 variantes fijas de query (`since=foo`, `until=2026-01-01T00:00Z`, `since=0001-01-01T00:00Z`, `days=99999999999`, `days=-1`, `page=-1`, `page=abc`, `side=`, `map=%00`, `operator=;`, `session=x`, `ranked_only=2`, `table=`, `table=maps&sep=;`) con el test client sobre base vacia y sobre `seed_demo`; afirma status < 500; una ruta nueva entra sola; menos de 20 s | S | idea (tests) |
| T3 | `seed_demo` sin `score_before` | Las metricas por marcador (fichas 41 y B5) no se ven en el e2e porque la semilla deja `score_before` vacio | `seed_demo.py`: llenar `score_before`/`score_after` coherentes con `my_team_won`; cambia numeros que afirma el e2e. Entra con la 41 si su diseno lo pide | S | en main (lo hizo la ficha 41) |
| T2 | README sin cifras de tests que se pudren | El README no miente: `README.md:248` dice 306 tests y `:392` dice 366 cuando `grep -c 'def test_' backend/tests/*.py` suma 403 en main 0949f87 | `README.md`: no afirmar cifras que cambian con cada ficha; decir "la suite completa" y remitir a `check.sh` | S | idea (deuda) |

## Cubierto por PRs abiertos que no son del equipo

No se proponen mientras el PR siga abierto. Si el humano lo cierra sin
mergear, sus ideas pasan a `idea`; si lo mergea, a `en main`.

- **PR #1** (`claude/loop-lwjbgs`): pagina Posicionamiento, con veredicto por
  sitio y spawn.
- **PR #22** (`ccr-ec8265ab-4qn7k2`): spawn peeks de peekabooR6 por mapa,
  cruzados con la salida del spawn. Toca lo mismo que cualquier idea de
  agregados por spawn. Cubre tambien las muertes tempranas por spawn de R6 Analyst y los spawn peeks y runouts que pide la comunidad (Siege.GG, 2026-02-22): no se proponen aparte.
- **PR #14** (`claude/dazzling-einstein-w3qcyq`): filtros en la URL, "Ver esas
  rondas" desde las señales, vigia de importacion, filtros en Partidas,
  partida anterior y siguiente, flechas para cambiar de ronda, racha actual,
  pick rate por operador.

## Ideas descartadas

| idea | por que |
|---|---|
| Pagina de mapas y sitios | Se retiro a proposito en 096fd52 (2026-10-07). Los agregados por mapa, sitio y spawn siguen en el Coach y en el CSV. No se reabre sin pedido del humano |
| Heatmap o posiciones sobre el minimapa | El `.rec` no trae coordenadas |
| Armas, dano, disparos, precision | No estan en el formato |
| Asistencias y score por jugador | Los paquetes existen pero no se pueden atribuir; `assists` y `score` se guardan y no se exponen |
| Metricas sobre plant o defuse en temporadas nuevas | Solo se infieren del reloj; `possible_plant` se muestra como inferencia y no entra en ninguna metrica (`docs/formato-rec.md`) |
| Timeline de utilidad (drones, gadgets) | `mercado/2026-09-15`: nadie encontro el patron de bytes. Solo como investigacion del parser en el PC, con `.rec` reales |
| Operadores baneados | `mercado/2026-09-15`: sin evidencia de que el `.rec` lo traiga |
| MMR, rango o historial de temporada en una metrica | Viven en la API de Ubisoft; ninguna metrica de replay puede depender de ella |
| Scouting de rivales fuera de tus partidas | El perfil existe para quien aparece en tus replays |
| Scraping de stats.cc o R6 Tracker | Cloudflare; ver `CLAUDE.md` |
| Overlay, ventana flotante, captura o lectura de memoria | No-goal del proyecto |
| Posiciones x/y/z del fork ImAAhmad de r6-dissect (`reader.go`, listener `60 73 85 FE`) | Sin validar ni mergear upstream, y `CLAUDE.md` dice que no hay coordenadas. Solo como investigacion del parser en el PC, con `.rec` reales; no se propone feature encima (2026-10-14) |
| Quien planto o desactivo por el bonus de +100 de score (PR #126 de r6-dissect) | Heuristica; plants y defuses de temporadas nuevas solo se infieren y no entran en metricas (`docs/formato-rec.md`) |
| Operadores baneados (issue #127 de r6-dissect, 2026-03-12) | El autor dice haber visto los datos en replays viejos, pero no publico bytes; vuelve si aparece el decodificado |
| ACE de la partida (OP.GG) | Sin link verificado (help.op.gg da 403). El MVP volvio como E7 (puesto en el lobby) con fuente de tracker.gg el 2026-10-14 |
| Comparar dos jugadores lado a lado (Scope.gg) | Duplica las paginas Compañero y Jugador |
| Tiempo vivo promedio por mapa (R6 Tracker) | Duplica "Mueres a los" y "Sobrevives" por mapa (2026-10-14) |
| Mejor y peor mapa con cada compañero o rival (R6 Tracker Rivals) | Ya existen Compañero y rivales repetidos; cortado por mapa la muestra es ruido (2026-10-14) |
| Score y asistencias por entidad en Y11S1 (lumina-r6 8b205b1, 2026-04-18) | Asigna por cercania de IDs (distancia <= 64) sin tests ni muestra publicada; no levanta el descarte de "asistencias y score". Solo investigacion del parser en el PC (2026-10-14) |
| Quien planta o desactiva por el campo "arma lista" (PR #129 de r6-dissect, fork julio208920) | Heuristica que en Y11S3 depende de strings del timer que ya no existen; plants y defuses no entran en metricas (2026-10-14) |
| Consistencia entre partidas (coeficiente de variacion del rating) | Sin fuente abrible: las paginas de ESPN vinieron vacias y el post de vlr.gg no explica el calculo (2026-10-14) |
| "Op Kills" de vlr.gg | Es por arma (el Operator); el `.rec` no trae armas (2026-10-14) |
| Cuentas, nube, telemetria, subir replays | Todo corre en el PC, a proposito |
