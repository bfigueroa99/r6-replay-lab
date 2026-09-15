# Mercado

Revisiones periodicas de competencia, pedidos de la comunidad y cambios de
Siege. Cada entrada lleva fecha y fuente; nada entra sin URL. Lo que no pasa el
filtro de `CLAUDE.md` (no-goals y limites del `.rec`, ver tambien
`docs/formato-rec.md`) queda anotado en Descartados con el motivo en una linea,
no en `docs/roadmap.md`.

Nota sobre esta primera revision: `docs/mercado.md` no existia todavia. El
analisis de competidores vivia solo dentro de `docs/roadmap.md`
("Que hacen los competidores"), que se mantiene y sigue siendo la referencia de
fondo; esta revision es la primera corrida separada, enfocada en novedades
desde ese analisis.

## Revision 2026-09-15

### Cambio de temporada

[Y11S3 "Operation Split Fire"](https://www.hotspawn.com/rainbow-six/news/rainbow-six-siege-y11s3-release-date)
salio el 1 de septiembre de 2026: Noor (nueva defensora), rework de Dokkaebi
(el Jegeo Payload ahora exige conexion continua y las granadas EMP se
cambiaron por cargas de brecha) y cambio de mapa en Villa (el sitio
Living Room/Library se mueve al subterraneo, el garage pasa a ser interior).
`docs/formato-rec.md` ya esta verificado contra replays de esta temporada
(code 9883691, partida del 9 de septiembre), asi que no hay nada pendiente de
parser por este cambio.

### Herramientas parecidas

- [r6-dissect](https://github.com/redraskal/r6-dissect) (el proyecto del que
  `pydissect` porta la logica original): sus releases publicadas llegan solo
  hasta Y10S1 (Rauora). Sigue atras de la temporada actual, igual que ya
  registra `docs/formato-rec.md`. Nada nuevo que portar.
- [Aurelix](https://aurelix.app/) (via busqueda, el sitio esta bloqueado desde
  este entorno): app web que sube el `.rec` a un servidor para parsearlo y
  ofrece comparacion de jugadores/operadores/mapas y "scouting" de rivales.
  Es la familia de "subir a un servidor", ya descartada en
  `docs/roadmap.md` ("Todo corre en el PC, a proposito").
- [r6data.com](https://r6data.com/r6-replay-viewer) y el roadmap publico de
  [R6 Replay](https://r6-replay.com/roadmap) (via busqueda, tambien bloqueado):
  "interactive blueprints con posiciones" y "static heatmap analytics" sobre
  datos posicionales. El `.rec` no trae coordenadas, es el mismo motivo ya
  anotado en `docs/roadmap.md`.
- R6 Replay marca como completado un **"Match Event Timeline"**: kill feed,
  eventos de objetivo y **uso de utilidad** (dron, gadgets) en una sola linea
  de tiempo. Es el mismo `.rec` que parsea este proyecto, asi que si ellos lo
  sacan, el patron de bytes probablemente esta en el stream de telemetria.
  `docs/formato-rec.md` no tiene documentado ningun patron para uso de
  utilidad (solo jugador, cambio de operador, sitio, reloj, kill feed y
  scoreboard). Candidato: ver Pendientes.

### Pedidos de la comunidad

La busqueda en r/Rainbow6 y r/SiegeAcademy no devolvio hilos concretos (el
buscador no encontro resultados utilizables de Reddit desde este entorno). Lo
unico verificable fue un pedido abierto en el issue tracker de r6-dissect:
[issue #127 "Banned Operators"](https://github.com/redraskal/r6-dissect/issues/127),
pidiendo capturar que operadores se banearon en la fase de picks/bans. El
mismo autor del pedido reconoce que no sabe si el dato esta en el archivo, y
no hay ninguna discusion tecnica que confirme un offset o patron. No pasa el
filtro tal como esta: no hay evidencia de que el `.rec` traiga esta
informacion (la ronda grabada probablemente ni siquiera cubre la fase de
bans), asi que va a Descartados en vez de a Pendientes.

No se encontro ningun otro pedido de la comunidad con evidencia suficiente
para proponer algo. Si esto se repite en la proxima revision, vale la pena
probar el acceso a Reddit desde otra via en vez de asumir que no hay pedidos.

### Descartados

| Hallazgo | Motivo |
|---|---|
| Aurelix: subir replays y "scouting" de rivales | Cloud/servidor ajeno; no-goal del proyecto (todo corre en el PC). |
| r6data.com, R6 Replay: blueprints y heatmaps posicionales | El `.rec` no trae coordenadas. |
| R6 Replay: "Tournament Analytics Dashboard", "Free public match HUB" | Multi-usuario / compartido; este proyecto es local y de un jugador. |
| r6-dissect #127: operadores baneados en pick/ban | Sin evidencia de que el dato este en el `.rec`; nadie confirmo un patron. |

### Pendientes promovidos

- **#20 Investigar timeline de uso de utilidad por ronda** (drone, breach,
  trampas), a partir de que R6 Replay lo muestra sobre el mismo formato. Ver
  `docs/roadmap.md`.
