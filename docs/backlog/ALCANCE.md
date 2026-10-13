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

## Epicas

### temporada-y-modo: temporada y modo de juego

| id | idea | que gana quien usa la app | datos | tam | estado |
|---|---|---|---|---|---|
| A1 | Selector de tipo de partida en la barra de filtros | Filtrar todo por ranked, unranked, rapida o la que sea, y no solo con "solo ranked" | `Match.match_type`; la API ya filtra (`views.py:48`) y `filters/` ya devuelve `match_types`; falta en `Filters.jsx`, que PR #14 tambien toca | S | idea |
| A2 | Etiquetar modos de juego desconocidos en Datos | Un modo nuevo deja de verse como `Unknown(...)` | `gamemode_name` (`header.py:233`) no llama a `record_unknown`, a diferencia de mapas y operadores; candidato de `mercado/2026-09-13` | S | idea |
| A3 | Temporada como dimension: etiqueta, filtro y comparacion | Saber si mejoraste de una temporada a otra | `Match.game_version` y `code_version` (`models.py:57-58`); tabla version -> temporada en `constants.py`, y las versiones sin nombre se etiquetan en Datos como los mapas | M | idea |

### lado-y-marcador: mitades, prorroga y presion

| id | idea | que gana quien usa la app | datos | tam | estado |
|---|---|---|---|---|---|
| B1 | Primera mitad, segunda mitad y prorroga | Ver si arrancar en ataque o en defensa te cambia la partida, y como rindes en prorroga | `Round.number`, `overtime_number` (`models.py:89`, guardado y sin exponer), `my_side` | S | en main |
| B2 | Rondas bajo presion | Tu rendimiento en match point, yendo abajo y yendo arriba | `score_before` / `score_after` (`models.py:98-99`). Partida en dos tramos: adelante/empatado/atras (ficha 41) y match point (B5) | M | ficha 41 (tramo 1) |
| B3 | Metricas por tercios de la ronda segun el reloj | Si te va peor al principio, al medio o al final de la ronda, mas alla de cuando mueres | reloj de los eventos, `death_clock`, `death_elapsed`; candidato #23 de `mercado/2026-09-16`. Nunca anclado al plant | M | idea |
| B4 | Inercia entre rondas | Tu winrate de ronda despues de ganar la anterior contra despues de perderla: si una ronda perdida te arrastra a la siguiente | `Round.my_team_won` de la ronda `number - 1` de la misma partida (`models.py:94`); fila nueva en `docs/metricas.md`, con banda de ruido como el #10 | S | ficha 39 |
| B5 | Match point y ronda decisiva (segundo tramo de B2) | Tu rendimiento cuando una ronda gana o pierde la partida | `score_before` + `Match.match_type`/`gamemode` para saber a cuanto se gana; las reglas por modo (prorroga, ventaja de 2) van en una tabla de `constants.py`, y un modo sin regla conocida no cuenta. Implementar despues de la ficha 41 | M | idea |
| B6 | Como ganas y pierdes tus rondas | Por lado y mapa, cuantas rondas se cierran por eliminacion, por tiempo o por objetivo: si en defensa pierdes por tiempo o por quedarte sin gente | `Round.win_condition` y `win_condition_certain` (`models.py:95-96`), hoy solo en el detalle de una ronda. Las inferidas (plant/defuse de temporadas nuevas) van en su propia fila "inferida" y no se desglosan, por `docs/formato-rec.md` | S | idea |

### escuadra: el equipo con el que juegas

| id | idea | que gana quien usa la app | datos | tam | estado |
|---|---|---|---|---|---|
| C1 | Winrate por grupo exacto de compañeros | Saber que stack completo te funciona, no solo que pares | `teammate_synergy` (`aggregates.py:383`) agrupa de a uno; `team_index` y `player` por ronda | M | idea |
| C2 | Matriz de trades del equipo | Quien venga a quien, y a quien nadie venga | `Event.traded` (`models.py:195`), `trade_kills`, `was_traded` (`models.py:146-147`) | M | idea |
| C3 | Alineacion de operadores de tu equipo contra el resultado | Que combinaciones de tu lado ganan mas por mapa y lado | `RoundPlayer.operator` de tus compañeros por ronda, `operators/catalog/` | M | idea |

### rivales: los rivales de tus replays

| id | idea | que gana quien usa la app | datos | tam | estado |
|---|---|---|---|---|---|
| D1 | Rivales repetidos | Lista de los que te tocaron en 2 o mas partidas, con tu record contra cada uno; el detalle ya esta en la pagina de jugador | filas `RoundPlayer` del equipo rival por `profileID`. Solo gente de tus replays: no es scouting | S | en main |
| D2 | Meta rival por mapa y sitio | Que operadores te ponen enfrente en cada mapa y como te va contra cada uno | extiende `rounds_vs_operator` (`aggregates.py:771`) con mapa y sitio; muestra chica, va con banda de ruido como el #10 | M | idea |
| D3 | Abandonos | Partidas con alguien que se fue, y tu winrate en 5v4 y 4v5 | eventos `PLAYER_LEAVE` (`constants.py:294`), que hoy solo cuentan como muerte (`stats.py:126`). Verificar que el evento sigue saliendo en temporadas nuevas | S | idea |

### progreso: progreso y metas

| id | idea | que gana quien usa la app | datos | tam | estado |
|---|---|---|---|---|---|
| E1 | Curva de aprendizaje por operador | Tu rating en las primeras N rondas con un operador contra las siguientes: si practicarlo rinde | `RoundPlayer` por operador ordenado por fecha, como `trend_by_match`; fila nueva en `docs/metricas.md` | M | idea |
| E2 | Metas personales | Fijar una meta (KST 70 %, menos de 30 % de muertes sin trade) y ver si la cumpliste en cada sesion | modelo nuevo de metadatos + POST de accion explicita que `CLAUDE.md` hoy no admite; sesiones de `sessions/` | M | decision (POST nuevo: ver Para el humano) |
| E3 | Rendimiento por hora del dia y dia de la semana | Saber si juegas peor de madrugada o los domingos, con muestra suficiente para creerlo | `Match.played_at` (`models.py:50`), ya en hora local (`USE_TZ = False`, `TIME_ZONE` en `config/settings.py:143`); agrupar por franja de 3 h y por dia con `ExtractHour`/`ExtractWeekDay` | S | ficha 40 |
| E4 | Records personales | Tu mejor partida (rating, bajas), tu ronda con mas bajas, tu 1vX mas grande y tu mejor dia, cada uno con enlace a la partida: lo que da gusto volver a mirar y marca el techo a superar | `RoundPlayer.kills`, `one_vx` y rating por partida (`trend_by_match`), `trend_by_day`; un agregado nuevo que devuelve el maximo con su `match_id`. La racha actual es de PR #14: no se duplica | S | idea |

### revision-de-rondas: revisar rondas

| id | idea | que gana quien usa la app | datos | tam | estado |
|---|---|---|---|---|---|
| F1 | Buscador de rondas entre partidas | Encontrar todas tus rondas de un tipo (clutch, apertura perdida sin trade, ronda perdida tras abrir ganando) y saltar al detalle de cada una | banderas de `RoundPlayer` (`one_vx`, `entry_kill`, `untraded_death`, `models.py:140-148`). PR #14 enlaza señales del coach a rondas: revisarlo antes de disenar para no duplicar | M | idea |
| F2 | Notas y marcadores por ronda | Anotar que paso en una ronda y volver a las marcadas | modelo nuevo + POST de accion explicita; candidato #22 de `mercado/2026-09-16` | M | decision (POST nuevo: ver Para el humano) |
| F4 | Tira de rondas en el listado de partidas | En Partidas, cada fila muestra la secuencia de rondas ganadas y perdidas (y el lado) y no solo el marcador final: se ven las remontadas y los derrumbes sin abrir la partida | `Round.my_team_won`, `my_side`, `number` por partida; `match_list` (`views.py`) agrega una lista corta por partida en la misma consulta paginada. PR #14 toca `Matches.jsx` (filtros): disenar sin pisarlo o esperar | S | idea |
| F3 | Cambios de operador y spawn en la linea de tiempo | Ver en el detalle de la ronda quien cambio de operador y desde que spawn salio cada uno | eventos `OPERATOR_SWAP` (`constants.py:292`), hoy una linea generica en `MatchDetail.jsx`; `spawn` ya viene en `matches/<id>/` y ninguna pagina lo pinta | S | idea |

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

### deuda-y-tests: no son funcionalidad

Entran por la regla de mezcla de la Directiva (solo con 3 funcionalidades
esperando en el papel) o como bug si lo son. Su estado es `idea (tests)` o
`idea (deuda)`: libres, pero `estado.sh` no las cuenta como ideas libres.

| id | idea | que gana quien usa la app | datos | tam | estado |
|---|---|---|---|---|---|
| T1 | Barrido de parametros borde sobre toda la API como test de Django | Ningun filtro raro vuelve a dar 500 (las fichas 32 y 33 salieron de barridos a mano; el PO del 2026-10-10 repitio 19 endpoints x ~50 parametros sin dejar script) | `backend/tests/test_barrido_api.py`: recorre las 18 rutas GET de `replays/urls.py` (pk 1 y 999999) con 14 variantes fijas de query (`since=foo`, `until=2026-01-01T00:00Z`, `since=0001-01-01T00:00Z`, `days=99999999999`, `days=-1`, `page=-1`, `page=abc`, `side=`, `map=%00`, `operator=;`, `session=x`, `ranked_only=2`, `table=`, `table=maps&sep=;`) con el test client sobre base vacia y sobre `seed_demo`; afirma status < 500; una ruta nueva entra sola; menos de 20 s | S | idea (tests) |
| T3 | `seed_demo` sin `score_before` | Las metricas por marcador (fichas 41 y B5) no se ven en el e2e porque la semilla deja `score_before` vacio | `seed_demo.py`: llenar `score_before`/`score_after` coherentes con `my_team_won`; cambia numeros que afirma el e2e. Entra con la 41 si su diseno lo pide | S | idea (tests) |
| T2 | README sin cifras de tests que se pudren | El README no miente: `README.md:248` dice 306 tests y `:392` dice 366 cuando `grep -c 'def test_' backend/tests/*.py` suma 403 en main 0949f87 | `README.md`: no afirmar cifras que cambian con cada ficha; decir "la suite completa" y remitir a `check.sh` | S | idea (deuda) |

## Cubierto por PRs abiertos que no son del equipo

No se proponen mientras el PR siga abierto. Si el humano lo cierra sin
mergear, sus ideas pasan a `idea`; si lo mergea, a `en main`.

- **PR #1** (`claude/loop-lwjbgs`): pagina Posicionamiento, con veredicto por
  sitio y spawn.
- **PR #22** (`ccr-ec8265ab-4qn7k2`): spawn peeks de peekabooR6 por mapa,
  cruzados con la salida del spawn. Toca lo mismo que cualquier idea de
  agregados por spawn.
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
| Cuentas, nube, telemetria, subir replays | Todo corre en el PC, a proposito |
