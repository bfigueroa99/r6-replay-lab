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
| 1. Parsers abiertos del `.rec` | r6-dissect (https://github.com/redraskal/r6-dissect): upstream quieto desde e6c2ca8 (2025-09-16); #131 y #129 cerradas sin merge, #126 y #124 abiertas, #132 (2026-11-08) sin contenido. Fork con mas senal: **prestonwillis10/r6-dissect** (488 commits, activo 2026-10-19 a 10-28: arma por baja, loadout, dano, DBNO, salas, Y11S2). nicktstewart, defiancer6s-hub y lumina-r6 quietos desde antes de 2026-10-14. Secos: aa-sasha, cliffside-git, ItaloRossySantiago, Animuxs/r6-stats-app, PR #105. `api.github.com` y el MCP de GitHub dan 403 fuera del repo: usar las paginas HTML | 2026-11-09 | alta |
| 2. Herramientas de replay de Siege | r6tv.online/how-it-works, aurelix.app (blog con un solo post, 2026-03-20), r6-replay.com/roadmap (sin cambios desde 2026-02), SiegeScope (sin cambios). Nuevas 2026-11-09: r6insights.org/overview (equipos y coach, KPI Tracking) y matchanalytics.eu (sube `.rec` a la nube; sitios, "Cheat Analytics"), sin fechas por funcion. Secos: r6.arenyze.com, ReplayAnalysis, Sprabuni/R6-Replays, Breach Report, r6data.eu (vencido), GitHub R6ReadRecFile y r6-dissect-application | 2026-11-09 | baja |
| 3. Trackers de API | stats.cc, R6 Tracker: descripcion publica, resenas, lo que se comenta. Detras de Cloudflare: si da 403, busqueda y seguir. Sin changelog abrible de ninguno desde 2026-10 (R6 Analyst: ultimo changelog 2021, soporte de Overwolf 404). Lo que rinde es el rating de Siege.GG: blog 946 (2026-08-11) y news de support value y win probability. r6data.eu vencido | 2026-11-03 | baja (trackers) / alta (Siege.GG) |
| 4. Otros juegos tacticos | Refrag blog (2026-10-30: Coach por partida y por ventana), Leetify blog (2026-11-07 veto de Premier), Siege.GG news (fantasy 2026-11-04, MVP 2026-11-08), CS Demo Manager `/changelog` (sin fechas, solo CS), vlr.gg. Secos o 403: Dotabuff, csstats.gg, Scope.gg, tracker.gg, help.op.gg, noesis.gg, mobalytics.gg, blitz.gg (403), roundiq.gg (404), csskill.com (502), runitback.gg (503) | 2026-11-09 | baja |
| 5. Comunidad | Reddit bloqueado desde la nube (WebSearch rechaza reddit.com, WebFetch no abre old.reddit): no se usan mirrors. Rinden Siege.GG news (2026-10-29 analytics), shattered.io ranks-guide y stats-tracker-setup (actualizadas 2026-10-20/21: todo ya en ALCANCE). Secos: boostroom (blog ahora solo The Division 2), metafy, bsky, foros de Ubisoft; exitlag y sportskeeda 403 | 2026-11-03 | baja |
| 6. Ubisoft | ubisoft.com/.../news-updates (listado, seasons/splitfire, patch notes Y11S3.2 y Y11S3.3, Community Checkpoint Recap) y MP1st para fechas y numero de parche. Liquipedia da 403. Ninguna fuente publica da IDs ni code versions: eso sale de r6-dissect o del PC | 2026-11-03 | alta |
| 7. Analitica de esports y deporte | FanGraphs library (LI y Clutch), metricgate.com (Bradley-Terry, shrinkage), Counterwatch (shrinkage), arXiv 1701.02359 (supervivencia), Miller y Sanjurjo 2018 (hot hand, sin metodo en la pagina), Siege.GG (win probability 2026-04-27, sin tabla XvY), HLTV Rating 3.0, nomiun. Secos: Leetify glossary, ESPN consistency, Pythagorean, varianceexplained.org (503) | 2026-11-09 | alta |
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

### 2026-11-09 (sesion 20261109T2004Z-cQbf8yt)

- Familias: 1, 2, 4 y 7 (las mas viejas, 2026-10-14). La 8 no tocaba (ultima pasada 2026-11-03).
- Dio senal: fork prestonwillis10/r6-dissect (arma por baja 63149de, loadout 807d93f, dano d8a0d4d, DBNO a3b438e, salas en el README, tags de Y11S2 044bc7c); FanGraphs LI y Clutch; metricgate Bradley-Terry; arXiv 1701.02359; Refrag (Coach por partida); matchanalytics.eu (sitio de la partida, rivales atipicos).
- Seco: upstream r6-dissect (sin commits; #132 sin contenido), forks viejos, herramientas de replay ya visitadas (ninguna fecha posterior a 2026-10-14), CS Demo Manager, blogs con 403 (noesis, mobalytics, blitz).
- Ideas agregadas a ALCANCE.md: B21 peso de cada ronda, K13 supervivencia sin sesgo, D15 duelos ajustados por rival, D16 rivales fuera de lo comun, F20 sitios de la partida, F21 Coach de una partida, P8 sala inicial del defensor; fuentes nuevas en P3 y P5.
- Descartadas: arma, loadout y dano del fork (choca con `CLAUDE.md`; pregunta al humano), winrates encogidos (E8), comparar jugadores, operador sugerido (O1), puntos fantasy, mapa repetido, hot hand, puesto por stat (E4), antes y despues (Tendencias).
- Proxima: familias 3, 5 y 6 (2026-11-03) y la 8 desde 2026-11-10; mirar si el humano respondio sobre armas y dano.

### 2026-11-03 (sesion 20261103T2005Z-cWAnVGk)

- Familias: 8 (pasada semanal liviana, sin recon completo), 3, 5 y 6.
- Paridad: 79.4 / 100, must 14 de 17, skip 21, resenas 0 de 4 fuentes (Trustpilot x2, HN Algolia x2). Sube de 76.1 por las fichas 64 (resumen de partidas), 72 (apertura en la timeline), 65 y 62 (parciales al dia).
- Dio senal: Siege.GG blog 946 (aperturas sin trade, clutches silenciosos) y win probability (lado inicial por mapa); Ubisoft splitfire (regla de 3v3 Arcade), Checkpoint Recap 2026-11-02 (3v3 vuelve en Y11S4, pool ranked fijo de ~15 mapas, Hostage y Secure Area a Quick Match), Y11S3.3 2026-11-03 (privacidad en el scoreboard); consolepcgaming (datos de un reporte) y Dexerto (compartir replays).
- Seco: la referencia sin cambios desde 2026-10-24 (ni funciones ni resenas); changelogs de stats.cc, R6 Tracker y R6 Analyst; boostroom, metafy, bsky, foros de Ubisoft. SiegeScope (competidor local nuevo) no trae nada que la app no tenga.
- Ideas agregadas a ALCANCE.md: A9 reglas de 3v3 Arcade, B17 lado inicial por mapa, H8 datos para reportar a un jugador, H9 partida en .zip, K10 aperturas sin trade, K11 clutches silenciosos, P7 jugadores anonimos desde Y11S3.3.
- Descartadas: KOST (ya es KST), rating compuesto normalizado por operador (O3 y Rating), Villa rehecho en Y11S3 (ya anotado en A4), pool fijo de Y11S4 (E11 lo cubre), heatmaps y post-plant (formato), Glicko de equipos (fuera de tus replays).
- Proxima: familias 1, 2, 4 y 7 (2026-10-14). A9 y P7 piden un `.rec` del PC: P7 es lo primero a mirar con replays posteriores al 2026-11-03.

### 2026-10-24 (sesion 20261024T2004Z, condensada)

- Familia 8, primera pasada de Replica: paridad 76.1, epica `paridad-referencia` con R1 a R4; resenas 0 de 8 fuentes. Descartadas por formato, no-goals o Ubisoft: recorridos, heatmaps, plants, cuentas, OCR, overlays, scouting.

### 2026-10-14 (sesiones 20261014T2010Z, 2111Z y 2211Z, condensadas)

- Familias 1, 2, 4, 7 y 3, 5, 6. Senal: r6-dissect #130 y PR #126, forks ImAAhmad, nicktstewart, defiancer6s-hub y lumina-r6, Aurelix, r6-replay.com, r6tv.online, Refrag, CS Demo Manager, vlr.gg, nomiun, HLTV 3.0, Leetify, Siege.GG, FanGraphs, Agresti-Coull, tracker.gg, R6 Analyst, shattered.io, boostroom, temporadas de Ubisoft.
- Ideas: B10, C6, D4, F7, F8, K1-K3, O1, O2, P1-P4; A4, B11, C7, E6, E7, F9, K4; A5, B12, C8, C9, D5, E8, E9, F10, O3, O4, O5, P5, P6.
- Descartadas: posiciones x/y/z (ImAAhmad), score y asistencias por entidad, plant por "arma lista" o bonus de score, bans, consistencia entre partidas, Op Kills, muertes por spawn (PR #22), comparar dos jugadores, tiempo vivo por mapa.
