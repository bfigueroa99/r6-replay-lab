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
| 2. Herramientas de replay de Siege | r6tv.online/how-it-works (la pagina util de R6TV), aurelix.app (portada y su unico post del blog), r6-replay.com/roadmap (casi todo ya esta en ALCANCE; `/changelog` da 404; `/siegewatch` es anti-cheat, no sirve). SiegeScope (siege-scope-stats.vercel.app, local con `.rec`, en desarrollo; 2026-11-03: nada que la app no tenga). Secos: r6.arenyze.com, ReplayAnalysis, Sprabuni/R6-Replays, Breach Report (top.gg 403), r6data.eu (dominio vencido, redirige a expireddomains) | 2026-10-14 (2211Z); SiegeScope de paso 2026-11-03 | alta |
| 3. Trackers de API | stats.cc, R6 Tracker: descripcion publica, resenas, lo que se comenta. Detras de Cloudflare: si da 403, busqueda y seguir. Sin changelog abrible de ninguno desde 2026-10 (R6 Analyst: ultimo changelog 2021, soporte de Overwolf 404). Lo que rinde es el rating de Siege.GG: blog 946 (2026-08-11) y news de support value y win probability. r6data.eu vencido | 2026-11-03 | baja (trackers) / alta (Siege.GG) |
| 4. Otros juegos tacticos | Refrag blog (nuevo, alta: oportunidades de trade, intentos de apertura), Leetify blog (profiles-update), vlr.gg (pestana Performance de una partida; `/stats` falla por redirects), CS Demo Manager `/changelog`. Secos: Dotabuff (403), csstats.gg (403), Scope.gg (blog quieto desde 2025-08), tracker.gg (403), help.op.gg (403) | 2026-10-14 (2211Z) | alta |
| 5. Comunidad | Reddit bloqueado desde la nube (WebSearch rechaza reddit.com, WebFetch no abre old.reddit): no se usan mirrors. Rinden Siege.GG news (2026-10-29 analytics), shattered.io ranks-guide y stats-tracker-setup (actualizadas 2026-10-20/21: todo ya en ALCANCE). Secos: boostroom (blog ahora solo The Division 2), metafy, bsky, foros de Ubisoft; exitlag y sportskeeda 403 | 2026-11-03 | baja |
| 6. Ubisoft | ubisoft.com/.../news-updates (listado, seasons/splitfire, patch notes Y11S3.2 y Y11S3.3, Community Checkpoint Recap) y MP1st para fechas y numero de parche. Liquipedia da 403. Ninguna fuente publica da IDs ni code versions: eso sale de r6-dissect o del PC | 2026-11-03 | alta |
| 7. Analitica de esports y deporte | Siege.GG blog (rating rebalance 2026-08-11: normalizacion por operador, trade differential), FanGraphs (regresion a la media), Agresti y Coull (Wilson), nomiun.substack.com, HLTV Rating 3.0. Secos: Leetify glossary, ESPN consistency (vacio), Pythagorean para esports. No hay tabla publica XvY ni ventana de trade en segundos para Siege | 2026-10-14 (2211Z) | alta |
| 8. Paridad con la referencia (Replica) | r6-replay.com (portada, /roadmap "last updated February 2026") y aurelix.app (portada, /features, /blog con un solo post de 2026-03-20). Secos: aurelix /faq /changelog /docs /help (404), X (402), Discord (cuenta), Trustpilot de las dos (404), HN Algolia 0, Overwolf sin ficha. Matriz en `replica/features.csv`; proximo recon completo desde 2026-11-21 | 2026-11-03 (2005Z) | baja (sin cambios en la referencia) |

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

### 2026-11-03 (sesion 20261103T2005Z-cWAnVGk)

- Familias: 8 (pasada semanal liviana, sin recon completo), 3, 5 y 6.
- Paridad: 79.4 / 100, must 14 de 17, skip 21, resenas 0 de 4 fuentes (Trustpilot x2, HN Algolia x2). Sube de 76.1 por las fichas 64 (resumen de partidas), 72 (apertura en la timeline), 65 y 62 (parciales al dia).
- Dio senal: Siege.GG blog 946 (aperturas sin trade, clutches silenciosos) y win probability (lado inicial por mapa); Ubisoft splitfire (regla de 3v3 Arcade), Checkpoint Recap 2026-11-02 (3v3 vuelve en Y11S4, pool ranked fijo de ~15 mapas, Hostage y Secure Area a Quick Match), Y11S3.3 2026-11-03 (privacidad en el scoreboard); consolepcgaming (datos de un reporte) y Dexerto (compartir replays).
- Seco: la referencia sin cambios desde 2026-10-24 (ni funciones ni resenas); changelogs de stats.cc, R6 Tracker y R6 Analyst; boostroom, metafy, bsky, foros de Ubisoft. SiegeScope (competidor local nuevo) no trae nada que la app no tenga.
- Ideas agregadas a ALCANCE.md: A9 reglas de 3v3 Arcade, B17 lado inicial por mapa, H8 datos para reportar a un jugador, H9 partida en .zip, K10 aperturas sin trade, K11 clutches silenciosos, P7 jugadores anonimos desde Y11S3.3.
- Descartadas: KOST (ya es KST), rating compuesto normalizado por operador (O3 y Rating), Villa rehecho en Y11S3 (ya anotado en A4), pool fijo de Y11S4 (E11 lo cubre), heatmaps y post-plant (formato), Glicko de equipos (fuera de tus replays).
- Proxima: familias 1, 2, 4 y 7 (2026-10-14). A9 y P7 piden un `.rec` del PC: P7 es lo primero a mirar con replays posteriores al 2026-11-03.

### 2026-10-24 (sesion 20261024T2004Z)

- Familias: 8 (primera pasada de Replica: recon completo, paridad y resenas; por replica.md no se visitan otras).
- Paridad: 76.1 / 100, must 12 de 17, skip 21, resenas 0 de 8 fuentes.
- Dio senal: r6-replay.com portada (trades por equipo, apertura en el kill feed) y roadmap (casi todo es coordenadas, equipos o nube: skip); aurelix.app /features y blog (resumen del Clubhouse, win delta por mapa y sitio, tramos de 30 s, tags por ronda).
- Seco: resenas de las dos (Trustpilot y Overwolf sin ficha, HN 0, Reddit 403, X 402, Discord con cuenta); aurelix /faq, /changelog, /docs y /help (404).
- Ideas agregadas a ALCANCE.md: epica nueva `paridad-referencia` con R1 partidas en el Inicio, R2 trades de los dos equipos en la partida, R3 fases de la ronda en la partida, R4 apertura marcada en la timeline.
- Descartadas (skip en la matriz): recorridos, heatmaps, visor 2D y setups (coordenadas); plants, post-plant y retakes (formato); Drive, API key, cuentas, equipos, planes y analytics (no-goals); OCR (dependencia); overlays de torneo; leaderboards y scouting fuera de tus replays (Ubisoft). Ya tenian idea: A1, O1, O5, D2, D4, F1, F2, F13, G2, O2.
- Proxima: familias 3, 5 y 6 (las mas viejas, 2026-10-14); en la proxima pasada de Replica, reintentar resenas.

### 2026-10-14 (sesiones 20261014T2010Z, 2111Z y 2211Z, condensadas)

- Familias 1, 2, 4, 7 y 3, 5, 6. Senal: r6-dissect #130 y PR #126, forks ImAAhmad, nicktstewart, defiancer6s-hub y lumina-r6, Aurelix, r6-replay.com, r6tv.online, Refrag, CS Demo Manager, vlr.gg, nomiun, HLTV 3.0, Leetify, Siege.GG, FanGraphs, Agresti-Coull, tracker.gg, R6 Analyst, shattered.io, boostroom, temporadas de Ubisoft.
- Ideas: B10, C6, D4, F7, F8, K1-K3, O1, O2, P1-P4; A4, B11, C7, E6, E7, F9, K4; A5, B12, C8, C9, D5, E8, E9, F10, O3, O4, O5, P5, P6.
- Descartadas: posiciones x/y/z (ImAAhmad), score y asistencias por entidad, plant por "arma lista" o bonus de score, bans, consistencia entre partidas, Op Kills, muertes por spawn (PR #22), comparar dos jugadores, tiempo vivo por mapa.
