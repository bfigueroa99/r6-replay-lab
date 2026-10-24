# Investigacion: ideas de afuera

Bitacora del Investigador del equipo (cuando el estado lo pide; por reloj,
la franja 7 de los dias pares; ver
`.claude/skills/equipo-dev/SKILL.md`). Vive en la rama
`claude/equipo-dev/backlog`; esta copia del playbook es la semilla que el
primer turno copia alla si no existe.

Para que sirve: que cada turno sepa que fuentes ya se miraron, cuales dieron
algo y que trampas tienen, para no repetir busquedas secas y para seguir las
que rinden. Las ideas no viven aca: van a `ALCANCE.md` con su fuente, y aca
queda solo el registro de donde salieron.

Reglas que no cambian: ninguna idea entra sin un link que el turno haya
abierto; la investigacion es del equipo y nunca hace que la app consulte
estas fuentes; nada esquiva una proteccion (un 403 se anota y se sigue).

## Fuentes

Puntos de partida, no una lista cerrada. El primer turno verifica que siguen
vivos y corrige lo que no. `ultima visita` y `senal` las actualiza cada turno
(`senal`: `alta`, `baja`, `seca` o `-` si nunca se visito).

| familia | donde mirar | ultima visita | senal |
|---|---|---|---|
| 1. Parsers abiertos del `.rec` | r6-dissect (https://github.com/redraskal/r6-dissect): upstream quieto desde e6c2ca8 (2025-09-16); ultimo issue/PR #131 y #130 (2026-09-30). Forks con senal: nicktstewart y defiancer6s-hub (Y11S2), lumina-r6/siege-dissect (picks de preparacion, score). Secos: aa-sasha, cliffside-git, ItaloRossySantiago, PR #105. `api.github.com` da 403 desde la nube: usar las paginas HTML | 2026-10-14 (2211Z) | alta |
| 2. Herramientas de replay de Siege | r6tv.online/how-it-works (la pagina util de R6TV), aurelix.app (portada y su unico post del blog), r6-replay.com/roadmap (casi todo ya esta en ALCANCE; `/changelog` da 404; `/siegewatch` es anti-cheat, no sirve). Secos: r6.arenyze.com, ReplayAnalysis, Sprabuni/R6-Replays, Breach Report (top.gg 403) | 2026-10-14 (2211Z) | alta |
| 3. Trackers de API | stats.cc, R6 Tracker: descripcion publica, resenas, lo que se comenta. Detras de Cloudflare: si da 403, busqueda y seguir. Rindio el articulo de tracker.gg sobre R6 Tracker 3.0 y la pagina de R6 Analyst (r6analyst.overwolf.com). stats.cc sin fuente abrible; r6data.eu sin DNS | 2026-10-14 | baja |
| 4. Otros juegos tacticos | Refrag blog (nuevo, alta: oportunidades de trade, intentos de apertura), Leetify blog (profiles-update), vlr.gg (pestana Performance de una partida; `/stats` falla por redirects), CS Demo Manager `/changelog`. Secos: Dotabuff (403), csstats.gg (403), Scope.gg (blog quieto desde 2025-08), tracker.gg (403), help.op.gg (403) | 2026-10-14 (2211Z) | alta |
| 5. Comunidad | Reddit bloqueado desde la nube (WebSearch rechaza reddit.com, WebFetch no abre old.reddit): no se usan mirrors. Rindieron Siege.GG (news), shattered.io y boostroom.com (guias). Aimlabs, Metafy y 1v9: genericos o venta de coaching | 2026-10-14 | alta |
| 6. Ubisoft | Paginas de temporada en ubisoft.com/.../news-updates/seasons/<nombre> (tenfoldpursuit, silenthunt, systemoverride) y news.ubisoft.com; Liquipedia para fechas de parche. Ninguna fuente publica da IDs ni code versions: eso sale de r6-dissect o del PC | 2026-10-14 | alta |
| 7. Analitica de esports y deporte | Siege.GG blog (rating rebalance 2026-08-11: normalizacion por operador, trade differential), FanGraphs (regresion a la media), Agresti y Coull (Wilson), nomiun.substack.com, HLTV Rating 3.0. Secos: Leetify glossary, ESPN consistency (vacio), Pythagorean para esports. No hay tabla publica XvY ni ventana de trade en segundos para Siege | 2026-10-14 (2211Z) | alta |
| 8. Paridad con la referencia (Replica) | r6-replay.com (portada, /pricing sin precios, /roadmap, legales) y aurelix.app (portada, /features con FAQ, /pricing, blog, legales, /waitlist). Secos: aurelix /faq /changelog /docs /help (404), X de las dos (402), Discord (cuenta), Trustpilot y Overwolf sin ficha. Matriz en `replica/features.csv`; proximo recon completo desde 2026-11-21 | 2026-10-24 (2004Z) | alta |

## Trampas conocidas

- stats.cc y R6 Tracker responden 403 a lo que no es un navegador (ver
  `CLAUDE.md`). No se insiste ni se esquiva.
- `docs/roadmap.md` ya tiene una tabla de competidores (2026-09). Partir de
  ahi y buscar solo lo nuevo.
- Lo que el `.rec` no trae (coordenadas, armas, dano, asistencias
  atribuibles, plants en temporadas nuevas) no se vuelve a investigar salvo
  que un parser abierto lo haya decodificado: en ese caso la idea entra a la
  epica `datos-nuevos-del-parser` con "verificar con `.rec` reales en el PC".

## Bitacora

La entrada mas nueva arriba. Formato:

```
### AAAA-MM-DD (sesion AAAAMMDDTHHMMZ)

- Familias: 1, 4, 5
- Dio senal: <fuente>: <que>
- Seco: <fuente>
- Ideas agregadas a ALCANCE.md: <id> <titulo>, ...
- Descartadas: <idea> porque <motivo>
```

### 2026-10-24 (sesion 20261024T2004Z)

- Familias: 8 (primera pasada de Replica: recon completo, paridad y resenas; por replica.md no se visitan otras).
- Paridad: 76.1 / 100, must 12 de 17, skip 21, resenas 0 de 8 fuentes.
- Dio senal: r6-replay.com portada (trades por equipo, apertura en el kill feed) y roadmap (casi todo es coordenadas, equipos o nube: skip); aurelix.app /features y blog (resumen del Clubhouse, win delta por mapa y sitio, tramos de 30 s, tags por ronda).
- Seco: resenas de las dos (Trustpilot y Overwolf sin ficha, HN 0, Reddit 403, X 402, Discord con cuenta); aurelix /faq, /changelog, /docs y /help (404).
- Ideas agregadas a ALCANCE.md: epica nueva `paridad-referencia` con R1 partidas en el Inicio, R2 trades de los dos equipos en la partida, R3 fases de la ronda en la partida, R4 apertura marcada en la timeline.
- Descartadas (skip en la matriz): recorridos, heatmaps, visor 2D y setups (coordenadas); plants, post-plant y retakes (formato); Drive, API key, cuentas, equipos, planes y analytics (no-goals); OCR (dependencia); overlays de torneo; leaderboards y scouting fuera de tus replays (Ubisoft). Ya tenian idea: A1, O1, O5, D2, D4, F1, F2, F13, G2, O2.
- Proxima: familias 3, 5 y 6 (las mas viejas, 2026-10-14); en la proxima pasada de Replica, reintentar resenas.

### 2026-10-14 (sesion 20261014T2211Z)

- Familias: 1, 2, 4, 7
- Dio senal: nicktstewart y defiancer6s-hub (DissectID y kill feed de Y11S2); lumina-r6 (picks de preparacion antes de Y9S3); r6tv.online (presencia y delta por operador, cara a cara, busqueda por composicion); Aurelix (tiempo de victoria por lado, mapas para banear); Refrag (oportunidades de trade, intentos de apertura); Leetify profiles-update (contra el promedio); vlr.gg y CS Demo Manager (2K-5K, matriz de aperturas); Siege.GG rebalance (normalizacion por operador, trade differential); FanGraphs y Agresti-Coull (banda de ruido).
- Seco: PR #105, aa-sasha, cliffside-git, ItaloRossySantiago, api.github.com (403), r6-replay.com/changelog (404) y /siegewatch, Dotabuff y csstats.gg (403), Scope.gg, Leetify glossary, ESPN (vacio).
- Ideas agregadas a ALCANCE.md: A5 mapas para banear, B12 cuanto tardas en ganar, C8 diferencial de trade, C9 oportunidades de trade, D5 cara a cara en la partida, E8 banda de ruido en winrates, E9 contra el promedio de tus lobbies, F10 multikills por tamano, O3 contra la media del operador, O4 participacion en aperturas, O5 presencia y delta por operador, P5 Y11S2, P6 picks de preparacion; F1 (composicion) y F7 (solo aperturas) ampliadas.
- Descartadas: score y asistencias por entidad (lumina, sin validacion), plant por "arma lista" (heuristica, plants fuera de metricas), consistencia entre partidas (sin fuente abrible), Op Kills (armas). Duplicados no anotados: Round Swing (K2), KOST (KST), 3-Stage/Playlists/Notes/Role/Synergy del roadmap de r6-replay.com (B3, F1, F2, O2, C1).
- Proxima: familias 3, 5 y 6. P5 contradice `formato-rec.md` para Y11S2: es lo primero que conviene verificar en el PC.

### 2026-10-14 (sesiones 20261014T2010Z y 20261014T2111Z, condensadas)

- Familias 1, 2, 4, 7 y luego 3, 5, 6. Senal: r6-dissect #130 y PR #126, fork ImAAhmad, Aurelix, r6-replay.com, CS Demo Manager, nomiun, HLTV 3.0, Leetify, Siege.GG, tracker.gg (R6 Tracker 3.0), R6 Analyst, shattered.io, boostroom, paginas de temporada de Ubisoft.
- Ideas: B10, C6, D4, F7, F8, K1-K3, O1, O2, P1-P4; A4, B11, C7, E6, E7, F9, K4; P1 con Noor, Snake y Calypso Casino.
- Descartadas: posiciones x/y/z de ImAAhmad, plant por bonus de score, bans, ACE, comparar dos jugadores, muertes por spawn y spawn peeks (PR #22), tiempo vivo por mapa, mejor mapa por compañero, 12 -> 30 replays, Dual Front.
