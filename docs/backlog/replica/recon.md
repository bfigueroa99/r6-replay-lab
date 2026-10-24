# Recon map: r6-replay.com y Aurelix (web)

Referencia: r6-replay.com (https://r6-replay.com/), Aurelix (https://aurelix.app/)
Ultimo recon: 2026-10-24
Tajada: lo que un jugador de Siege mira de sus propias partidas: perfil, historial, detalle de una partida, desglose por operador, mapa y modo, comparacion con otros jugadores y progreso en el tiempo.
Para: quien usa r6-replay-lab, un jugador que analiza sus replays en su PC.
Sesion: Investigador 20261024T2004Z, `main` 5647aa1.

Solo paginas publicas, leidas una vez cada una. Sin cuenta, sin capturas, sin
bundles JS ni llamadas de red de las apps. Las pantallas internas de las dos
apps no se ven sin cuenta: salen de su marketing, FAQ, terminos y privacidad,
y llevan confianza media.

## Sources

| # | source | URL | notes |
| --- | --- | --- | --- |
| 1 | portada r6-replay | https://r6-replay.com/ | features, flujo de subida, FAQ embebida |
| 2 | pricing r6-replay | https://r6-replay.com/pricing | sin precios ni tabla: Free, mas almacenamiento, "Basic" |
| 3 | roadmap r6-replay | https://r6-replay.com/roadmap | Foundation / Team Dominance / Individual Excellence, con estado |
| 4 | SiegeWatch | https://r6-replay.com/siegewatch | anti-cheat comunitario: fuera de la tajada |
| 5 | terminos y privacidad r6-replay | https://r6-replay.com/terms, https://r6-replay.com/privacy | datos parseados, visibilidad de partidas, PostHog |
| 6 | login r6-replay | https://r6-replay.com/login?mode=signup | usertag, email, password |
| 7 | portada Aurelix | https://aurelix.app/ | Clubhouse, KPIs, Upload/Analyse/Improve |
| 8 | features Aurelix | https://aurelix.app/features | War Room, Map & Site, Recon, Round Tagging, Movement, OCR, FAQ |
| 9 | pricing Aurelix | https://aurelix.app/pricing | Pro y Team "Coming Soon", sin precio |
| 10 | blog Aurelix | https://aurelix.app/blog/how-to-analyse-r6-siege-replays | win delta, bins de 30 s, minimo de rondas |
| 11 | legales Aurelix | https://aurelix.app/privacy-policy, https://aurelix.app/terms-of-service, https://aurelix.app/cookie-policy | Drive, OCR, Clerk, Supabase |
| 12 | waitlist Aurelix | https://aurelix.app/waitlist | open beta desde 2026-06-07 |
| - | no abren | x.com/PicklePioneer y x.com/AurelixApp (402), aurelix.app/faq, /changelog, /docs, /help (404), Discord (cuenta), Reddit (403) | anotado, sin reintentos |

## Core loop

Subir los `.rec` de una partida y revisarla ronda por ronda (timeline, kill
feed, trades, aperturas), y despues agregar entre partidas por operador, mapa
y sitio. En r6-replay-lab el mismo loop corre local: la importacion es
automatica y no hay subida.

## Screens

| ID | screen | route / how to reach | purpose | key components | states seen |
| --- | --- | --- | --- | --- | --- |
| S01 | Portada r6-replay | / | vender, subir | hero, zona de arrastre, FAQ | filled |
| S02 | Pricing r6-replay | /pricing | planes | Free, almacenamiento, Basic | filled (sin precios) |
| S03 | Roadmap r6-replay | /roadmap | backlog publico | grupos con estado y trimestre | filled |
| S04 | Login y signup r6-replay | /login | cuenta | email, password, usertag | filled |
| S05 | Analisis de partida r6-replay (inferida) | despues de subir | revisar ronda por ronda | timeline, kill feed, aperturas, trades, plants | no visto |
| S06 | Archivo de replays r6-replay (inferida) | app | lista de subidas | lista con limite por plan | no visto |
| S07 | Portada y features Aurelix | /, /features | vender | previews de partida y paneles | filled |
| S08 | Clubhouse Aurelix (inferida) | home logueado | resumen | partidas recientes, KPIs (partidas, win rate, rondas medias, partidas cerradas, mejor mapa) | no visto |
| S09 | Detalle de partida Aurelix (inferida) | clic en partida | marcador y rondas | KDA, HS%, historial de rondas con condicion y sitio | preview de marketing |
| S10 | War Room Aurelix | modulo | analitica filtrada | win rate por operador y sitio, win delta, bins de 30 s, CSV | preview de marketing |
| S11 | Map & Site Aurelix | modulo | por mapa | sitio por sitio, ataque y defensa, ranking de operadores | preview |
| S12 | Opponent Recon Aurelix | modulo | rivales | historial contra un equipo, operadores y sitios preferidos | preview |
| S13 | Round Tagging Aurelix | modulo | anotar | tags por ronda, filtro | preview |
| S14 | Movement Tracking Aurelix | modulo | posiciones | recorridos sobre plano | preview (choca con el formato: ver Out of scope) |
| S15 | Team Hub y Settings Aurelix | modulo | equipo y cuenta | roster, API key, borrar cuenta | preview |

## Flows

```
F01 Analizar una partida (las dos)
    portada -> crear cuenta -> arrastrar .rec o carpeta -> partida -> ronda N
    happy path clicks: 4 o mas, con alta de cuenta
    r6-replay-lab: 0 (importacion automatica) + 2 (Partidas -> partida)
F02 Analitica entre partidas (Aurelix)
    War Room -> filtros (mapa, sitio, jugador, operador, fechas) -> tablas -> CSV
F03 Revisar y etiquetar rondas (Aurelix)
    Clubhouse -> partida -> tag por ronda -> filtrar historial por tag
F04 Scouting de rival (Aurelix)
    Recon -> equipo rival -> historial, operadores y sitios -> reporte
```

## Components

| component | variants | states | used on |
| --- | --- | --- | --- |
| Zona de arrastre | archivos, carpeta | idle, subiendo, error de parseo | S01, S05 |
| Tira de rondas | ganada/perdida, condicion, sitio | - | S09 |
| Tabla con filtros y CSV | por operador, sitio, mapa | vacia, llena | S10, S11 |
| Timeline de ronda | apertura, trade, plant | - | S05 |

## Inferred data model

```
Match       mapa, modo, tipo (ranked/unranked/custom), fecha, equipos, score, origen, clave de dedup
            evidence: features (FAQ), privacy de las dos
            confidence: medium
Round       numero, lado, sitio, ganador, condicion, duracion, plant
            evidence: preview de partida de /features, portada r6-replay
            confidence: high
RoundPlayer operador, K, D, HS, DBNO, apertura (asistencias: el .rec ya no las atribuye)
            confidence: high
Event       tipo, actor, victima, tiempo, trade (posicion x/y en Aurelix: no verificable)
            confidence: medium
RoundTag    ronda, etiqueta, autor
            confidence: high
```

Relationships: Match 1-n Round, Round 1-n RoundPlayer, Round 1-n Event, Round 1-n RoundTag.
En r6-replay-lab ya existen Match, Round, RoundPlayer y Event
(`backend/replays/models.py`); RoundTag es la idea F2, en decision del humano.

## Feature matrix

See `features.csv`. 61 filas: must 18 (1 skip: plants), should 18, could 25; skip 21.
Paridad 76.1 / 100, must 12 de 17 (`parity.md`).

## Out of scope (cannot or should not be cloned)

- Coordenadas: recorridos, heatmaps, visor 2D, setups (CLAUDE.md: el `.rec` no las entrega).
- Plants y defuses en temporadas nuevas, post-plant y retakes (formato-rec.md).
- Asistencias, DBNO sin validar (idea P3), valor de utilidad.
- Cuentas, equipos en la nube, planes, Drive, API key, telemetria (no-goals).
- Overlays de broadcast y SiegeWatch (no-goal y fuera de la tajada).
- Scouting y leaderboards fuera de tus replays (API de Ubisoft).
- OCR (dependencia nueva).

## Size

No aplica en el loop (replica.md, paso 9).
