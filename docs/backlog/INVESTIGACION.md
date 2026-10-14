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
| 1. Parsers abiertos del `.rec` | r6-dissect (https://github.com/redraskal/r6-dissect): commits, releases e issues desde la ultima visita; sus forks; otros parsers que aparezcan. Upstream quieto desde e6c2ca8 (2025-09-16); lo nuevo esta en issues (#127, #130), PR #126 y el fork ImAAhmad | 2026-10-14 | alta |
| 2. Herramientas de replay de Siege | r6-replay.com (y `/roadmap`), Aurelix (aurelix.app y su blog), R6TV (nuevo, 2026-06). r6.arenyze.com es SPA de stats, no visor: sacarlo. ReplayAnalysis: Excel sobre JSON de r6-dissect, nada nuevo | 2026-10-14 | alta |
| 3. Trackers de API | stats.cc, R6 Tracker: descripcion publica, resenas, lo que se comenta. Detras de Cloudflare: si da 403, busqueda y seguir | - | - |
| 4. Otros juegos tacticos | CS2: Leetify (blog), Scope.gg, CS Demo Manager (`/changelog` es lo unico util). Valorant: Blitz, tracker.gg (403), vlr.gg. MOBAs: OP.GG (help 403), Dotabuff (sin visitar) | 2026-10-14 | alta |
| 5. Comunidad | r/Rainbow6, r/R6ProLeague, Siege.GG, contenido de coaching | - | - |
| 6. Ubisoft | Notas de parche y de temporada: operadores, mapas, modos, cambios del sistema de replays | - | - |
| 7. Analitica de esports y deporte | Ratings compuestos, probabilidad de ganar la ronda por ventaja numerica, redes de trade, rating de clutch. Rindieron: nomiun.substack.com, HLTV Rating 3.0, Leetify Rating, Siege.GG blog. No hay tabla publica XvY para Siege | 2026-10-14 | alta |

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

### 2026-10-14 (sesion 20261014T2010Z)

- Familias: 1, 2, 4, 7
- Dio senal: r6-dissect issue #130 (operador 444310693746 de Y11S3 y rondas con los dos equipos `won`); PR #126 y fork ImAAhmad (code versions Y10S4/Y11S1, FortressY10, DBNO, scoreboard Y10S4+); Aurelix (cerradas, stacks rivales, operador por sitio); r6-replay.com (refrag, rol); CS Demo Manager changelog (matriz de duelos, duracion de multikill); nomiun, HLTV 3.0, Leetify y Siege.GG (probabilidad por estado de vivos, impacto por baja, intentos de clutch).
- Seco: commits y releases de r6-dissect upstream (pydissect esta a la par hasta Y10S3_1); r6.arenyze.com (SPA de stats); ReplayAnalysis; tracker.gg (403); help.op.gg (403); perfiles de Leetify (JS vacio); Siege.GG sobre probabilidad de ganar (generico).
- Ideas agregadas a ALCANCE.md: B10 partidas cerradas, C6 tiempo de refrag, D4 stacks rivales, F7 matriz de duelos, F8 duracion del multikill, K1 conversion por estado de vivos, K2 impacto por baja, K3 intentos de clutch, O1 operador por sitio, O2 rol inferido, P1 catalogo Y10S4-Y11S3, P2 ronda con dos ganadores (posible bug), P3 DBNO, P4 scoreboard Y10S4+.
- Descartadas: posiciones x/y/z del fork (sin validar, choca con `CLAUDE.md`); plant por bonus de score (plants inferidos no entran en metricas); bans de operadores (sin bytes publicados); MVP/ACE (sin link); comparar dos jugadores (duplica Compañero); "parte de la victoria" de nomiun y el reparto por dano de Leetify (quedan dentro de K2 sin dano).
- Proxima: familias 3, 5 y 6 sin visitar; en la 1, los forks lumina-r6/siege-dissect, aa-sasha, cliffside-git y defiancer6s-hub, y el PR #105 (movement data).
