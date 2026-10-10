# Investigacion: ideas de afuera

Bitacora del Investigador del equipo (franja 7, dias pares; ver
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
| 1. Parsers abiertos del `.rec` | r6-dissect (https://github.com/redraskal/r6-dissect): commits, releases e issues desde la ultima visita; sus forks; otros parsers que aparezcan | - | - |
| 2. Herramientas de replay de Siege | r6-replay.com, R6 Replay Viewer (r6.arenyze.com), Aurelix (aurelix.app), ReplayAnalysis (github.com/Zander-9909/ReplayAnalysis) y las nuevas que aparezcan | - | - |
| 3. Trackers de API | stats.cc, R6 Tracker: descripcion publica, resenas, lo que se comenta. Detras de Cloudflare: si da 403, busqueda y seguir | - | - |
| 4. Otros juegos tacticos | CS2: Leetify, Scope.gg, CS Demo Manager. Valorant: Blitz, tracker.gg. MOBAs: OP.GG, Dotabuff | - | - |
| 5. Comunidad | r/Rainbow6, r/R6ProLeague, Siege.GG, contenido de coaching | - | - |
| 6. Ubisoft | Notas de parche y de temporada: operadores, mapas, modos, cambios del sistema de replays | - | - |
| 7. Analitica de esports y deporte | Ratings compuestos, probabilidad de ganar la ronda por ventaja numerica, redes de trade, rating de clutch | - | - |

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

(Todavia sin entradas.)
