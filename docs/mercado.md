# Mercado

Revision periodica de la fase `mercado` del loop: que hacen herramientas
parecidas, que piden los jugadores, y que cambio en Siege. Cada hallazgo se
filtra contra los no-goals de `CLAUDE.md` y contra lo que el `.rec` no trae
(`docs/formato-rec.md`). Lo que no pasa el filtro queda en Descartados con el
motivo en una linea. Si no hay nada nuevo, la revision se deja corta en vez de
inventar una tendencia.

## Revision 2026-09-13

### Que cambio en Siege

Y11S3 "Operation Split Fire" salio el 1 de septiembre de 2026 (parche
3.46/1.000.151): nuevo Defensor **Noor** (lanzador que atraviesa escudos y
destructibles), rework "focalizado" de Villa (el sitio Dining/Kitchen se mueve
al subsuelo), nueva **Legend Division** en ranked y un modo arcade **3v3**
nuevo. Fuentes:
[mp1st.com](https://mp1st.com/news/rainbow-six-siege-y11s3-update-is-called-split-fire-and-shoots-out-sept-1),
[hotspawn.com](https://www.hotspawn.com/rainbow-six/news/rainbow-six-siege-y11s3-release-date),
[pixeltwelve.com](https://pixeltwelve.com/articles/rainbow-six-siege-operation-split-fire-noor-patch-notes).

Revisado contra el codigo antes de proponer nada:

- **Noor no necesita cambios.** `operator_label()` en `backend/pydissect/header.py`
  ya cae al `rolename` de la cabecera para un operador sin ID en `OPERATORS`
  (el mismo mecanismo que ya cubrio `"NOOR"` como ejemplo documentado en
  `docs/formato-rec.md`).
- **El rework de Villa, si trae un `worldid` nuevo**, lo cubre el flujo que ya
  existe (`manage.py unknown_ids` + overrides). No es una feature nueva, es el
  camino de siempre.
- **El modo arcade 3v3 si es una brecha real.** `GAME_MODES` en
  `backend/pydissect/constants.py` solo tiene 4 ids (Bomb, SecureArea, Hostage,
  QuickMatchBomb), y `gamemode_name()` no llama a `record_unknown()` como si
  hacen `map_name()` y `operator_name()`. Un `gamemodeid` nuevo queda mostrando
  `Unknown(id)` para siempre, sin forma de etiquetarlo desde la pagina
  **Datos**. Ademas no hay ningun filtro por modo en la barra de filtros, asi
  que un modo estructuralmente distinto (rondas mas cortas, probablemente sin
  bomba) se mezclaria sin poder sacarlo de los agregados. Los dos puntos se
  promueven abajo.

Ranked 3.0 (Champion en cinco divisiones, la Legend Division nueva) es
matchmaking y MMR: vive en la API de Ubisoft, fuera de alcance por el no-goal
de `CLAUDE.md`.

### Que hacen los competidores

`r6-dissect` (el proyecto del que `pydissect` porto la logica original) tiene
issues abiertos que sirven mas para confirmar que este proyecto no se quedo
atras que para encontrar algo nuevo:

- [#102](https://github.com/redraskal/r6-dissect/issues/102) "Defuser Plant
  Time is fixed at 0:44" (abierto desde 2024): el mismo callejon sin salida que
  ya documenta `docs/formato-rec.md` sobre plant/defuse desde que el juego dejo
  de emitir el timer como texto. No hay solucion conocida rio arriba tampoco;
  la inferencia por reloj que ya usa este proyecto sigue siendo lo mejor
  disponible.
- [#115](https://github.com/redraskal/r6-dissect/issues/115) "Downed finish
  gives kill to wrong player": el kill feed y el scoreboard discrepan en quien
  se queda con la baja cuando alguien remata a un jugador derribado por otro.
  Revisado contra `backend/pydissect/events.py`: `read_scoreboard_kills()` ya
  corrige justamente este caso (`usernameFromScoreboard` sobreescribe el
  nombre del feed), asi que el bug que reporta r6-dissect no aplica aca.
- [#127](https://github.com/redraskal/r6-dissect/issues/127) pide baneos de
  operador en el JSON. Interesante para leer meta de ranked, pero el baneo
  ocurre en el lobby antes de que arranque la ronda que graba el `.rec`; no
  hay evidencia de que ese dato exista en el archivo. Va a Descartados.

`ReplayAnalysis` (Zander-9909, GitHub) exporta a Excel con la formula KOST y
una ventana de trade fija de 10s: mismo terreno que el rating compuesto (#5) y
la ventana de trade configurable (#11) de este proyecto, los dos ya hechos y
con mejor version (la ventana se puede cambiar, KOST es fijo). La tabla de
brechas de `docs/roadmap.md` (seccion "Que hacen los competidores") esta
completa: las 4 filas con item asignado ya tienen `[x]`.

No encontre pedidos concretos y recientes en r/Rainbow6 o r/SiegeAcademy que
pasaran el filtro: la busqueda devolvio sobre todo contenido generico de
coaching y paginas de trackers de API (MMR, leaderboards), no pedidos puntuales
sobre analisis de replays. Si aparece algo especifico en la proxima revision
se agrega aca con su fuente en vez de forzar uno ahora.

### Descartados

| Hallazgo | Fuente | Por que no |
|---|---|---|
| Baneos de operador en el JSON | [r6-dissect #127](https://github.com/redraskal/r6-dissect/issues/127) | No hay evidencia de que el `.rec` incluya la fase de baneo del lobby; ocurre antes de la ronda grabada. |
| Legend Division / Ranked 3.0 | [hotspawn.com](https://www.hotspawn.com/rainbow-six/news/rainbow-six-siege-y11s3-release-date) | MMR y ranked viven en la API de Ubisoft, no en el `.rec`. |
| Marketplace pricing, ban lists via reputation.gg | stats.cc | API de Ubisoft y servicio externo de terceros, no datos de replay. |

## Candidatos promovidos a docs/roadmap.md

- **#20 Etiquetar modos de juego desconocidos**: extiende el patron de
  `unknown_ids` de mapas y operadores a `gamemodeid`.
- **#21 Filtro por modo de partida en la barra de filtros**: para poder sacar
  el 3v3 arcade nuevo (o cualquier modo futuro) de los agregados que se
  calculan sobre "todo el historial".
