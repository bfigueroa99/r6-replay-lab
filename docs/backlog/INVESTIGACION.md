# Investigacion: ideas de afuera

Bitacora del Investigador del equipo (cuando el estado lo pide; por reloj,
la franja 7 de los dias pares; el metodo esta en
`.claude/skills/equipo-dev/roles/investigador.md`). Vive en la rama
`claude/equipo-dev/backlog`; esta copia del playbook es la semilla que el
primer turno copia alla si no existe.

Para que sirve: que cada turno sepa que fuentes ya se miraron, cuales dieron
algo y que trampas tienen, para no repetir busquedas secas y para seguir las
que rinden. Las ideas no viven aca: van a `ALCANCE.md` con su fuente, y aca
queda el registro de donde salieron y la evidencia que las sostiene.

Reglas que no cambian: ninguna idea entra sin un link que el turno haya
abierto; la investigacion es del equipo y nunca hace que la app consulte
estas fuentes; nada esquiva una proteccion (un 403 se anota y se sigue).

## Fuentes

Puntos de partida, no una lista cerrada. El primer turno verifica que siguen
vivos y corrige lo que no. `ultima visita` y `senal` las actualiza cada turno
(`senal`: `alta`, `baja`, `seca` o `-` si nunca se visito). Una familia sin
visita en 10 dias va en el turno siguiente; la 8 va cada 7.

| familia | donde mirar | ultima visita | senal |
|---|---|---|---|
| 1. Parsers abiertos del `.rec` | r6-dissect (https://github.com/redraskal/r6-dissect): releases, commits e issues desde la ultima visita; sus forks; otros parsers que aparezcan (busqueda "rainbow six siege replay parser", "dissect .rec") | - | - |
| 2. Herramientas de replay de Siege | r6-replay.com, R6 Replay Viewer (r6.arenyze.com), Aurelix (aurelix.app), ReplayAnalysis (github.com/Zander-9909/ReplayAnalysis), herramientas tipo r6analyst y las nuevas que aparezcan: que muestran, que cobran, que piden sus usuarios | - | - |
| 3. Trackers de API | stats.cc, R6 Tracker (r6.tracker.network), siege.gg: descripcion publica, novedades, resenas y lo que se comenta. Detras de Cloudflare: si da 403, busqueda y seguir | - | - |
| 4. Otros juegos tacticos | CS2: Leetify, Scope.gg, CS Demo Manager. Valorant: Blitz, tracker.gg. MOBAs: OP.GG, Dotabuff. Metricas y pantallas que se traducen a Siege | - | - |
| 5. Comunidad | r/Rainbow6, r/R6ProLeague, r/SiegeAcademy, Siege.GG (noticias), contenido de coaching: que quieren ver los jugadores de sus partidas, que se quejan de las herramientas que usan | - | - |
| 6. Ubisoft | Notas de parche y de temporada (ubisoft.com, seccion Rainbow Six Siege news-updates), designer's notes: operadores y mapas nuevos (IDs que el parser no conoce), modos, cambios del sistema de replays | - | - |
| 7. Analitica de esports y deporte | Ratings compuestos (HLTV rating y sus explicaciones), probabilidad de ganar la ronda por ventaja numerica, redes de trade, rating de clutch, banda de ruido para muestras chicas | - | - |
| 8. Paridad con la referencia (Replica) | La pasada semanal del pack Replica sobre r6-replay.com y Aurelix (`.claude/skills/equipo-dev/replica.md`): recon, matriz contra `main`, `parity.py` y resenas. No rota: va primero cuando esta fila lleva 7 dias sin visita | - | - |

## Trampas conocidas

- stats.cc y R6 Tracker responden 403 a lo que no es un navegador (ver
  `CLAUDE.md`). No se insiste ni se esquiva: se usa la busqueda.
- `docs/roadmap.md` ya tiene una tabla de competidores (2026-09). Partir de
  ahi y buscar solo lo nuevo.
- Lo que el `.rec` no trae (coordenadas, armas, dano, asistencias
  atribuibles, plants en temporadas nuevas) no se vuelve a investigar salvo
  que un parser abierto lo haya decodificado: en ese caso la idea entra a la
  epica `datos-nuevos-del-parser` con "verificar con `.rec` reales en el PC".
- Un snippet del buscador no es evidencia: se abre la pagina. Reddit y los
  foros: se cita el hilo con su fecha, no "la comunidad dice".

## Bitacora

La entrada mas nueva arriba. Formato:

```
### AAAA-MM-DD (sesion AAAAMMDDTHHMMZ)

- Familias: 1, 4, 6 | sin red
- Evidencia:

  | fuente | publicada | consultada | dato o cita (25 palabras o menos) | veredicto |
  |---|---|---|---|---|
  | [r6-dissect v0.x](url) | 2026-10-01 | 2026-10-13 | "..." | idea J1 |
  | [hilo de r/Rainbow6](url) | 2026-09-20 | 2026-10-13 | piden X | descartada: coordenadas |

- Seco: <fuente> (que se busco)
- Trampas nuevas: <URL que cambio, 403, paywall>
- Ideas agregadas a ALCANCE.md: <id> <titulo>, ...
```

(Todavia sin entradas.)
