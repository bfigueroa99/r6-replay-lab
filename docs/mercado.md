# Mercado

Revisiones periodicas de competencia, pedidos de la comunidad y cambios de
Siege. Cada entrada lleva fecha y fuente; nada entra sin URL. Lo que no pasa
el filtro de `CLAUDE.md` (no-goals y limites del `.rec`, ver tambien
`docs/formato-rec.md`) queda anotado en Descartados con el motivo en una
linea, no en `docs/roadmap.md`.

**Nota sobre el estado de este archivo.** A la fecha de esta revision,
`docs/mercado.md` y `docs/loop.md` (los archivos que esta fase deberia leer
primero) no existen todavia en `main`. Hay dos revisiones anteriores escritas
para este mismo archivo que tampoco llegaron a `main`: `mercado/2026-09-13`
(PR #2) y `mercado/2026-09-15` (PR #3), las dos abiertas y con el chequeo de
CI en rojo. Como ninguna esta mergeada, esta revision se vuelve a escribir
sobre un `main` sin ese historial, y las tres proponen candidatos con
numeros que se pisan: **el #20 quedo pedido dos veces** (PR #2: "Etiquetar
modos de juego desconocidos"; PR #3: "Investigar timeline de uso de utilidad
por ronda"). Alguien tiene que revisar y mergear esas dos PRs (en el orden
que corresponda) antes de que se acumule una tercera colision. Mientras
tanto, esta revision numera sus candidatos desde el #22 -- el numero mas
alto ya pedido en una PR abierta, mas uno -- y deja en `docs/roadmap.md` un
"proximo numero libre" declarado para que esto no se repita.

## Revision 2026-09-16

### Cambio de temporada

Sigue [Y11S3 "Operation Split Fire"](https://www.hotspawn.com/rainbow-six/news/rainbow-six-siege-y11s3-release-date),
sin cambio de temporada desde la revision del 2026-09-15. Lo unico nuevo es
el evento por tiempo limitado **M.U.T.E. Protocol** (17 de septiembre al 1 de
octubre): otro modo temporal con su propio `gamemodeid`, que refuerza (no
reemplaza) los dos candidatos que ya esperan revision en la PR #2 (`#20`
etiquetar modos desconocidos, `#21` filtro por modo de partida). No se
propone nada nuevo por este evento puntual.

### Herramientas parecidas

- [r6-dissect](https://github.com/redraskal/r6-dissect): sin release nueva
  desde la revision anterior (sigue en v0.24.0, "Y10S1 Rauora"). El issue
  [#114 "winCondition missing"](https://github.com/redraskal/r6-dissect/issues/114)
  (reportado contra Y9S4) confirma el mismo limite que ya documenta
  `docs/formato-rec.md` sobre la condicion de victoria cuando la ronda no
  termina en barrida: sin respuesta del mantenedor y sin ningun patron de
  bytes propuesto. No aporta nada nuevo que intentar; va a Descartados.
- [R6 Replay](https://r6-replay.com/roadmap) (via busqueda -- el sitio sigue
  bloqueado desde este entorno, igual que en la revision anterior) publico su
  roadmap con varias features para Q3/Q4 2026:
  - **"Bookmarks & Notes System"** (Q4 2026): marcar momentos de una ronda y
    agregar notas tacticas. La parte de compartir highlights no aplica (es
    multi-usuario, fuera de alcance), pero **anotar una ronda propia es
    metadata local que escribe el usuario**, no un dato que haya que sacar
    del `.rec`. Candidato: ver Pendientes.
  - **"3-Stage Round Analysis"** (Q3 2026): parte la ronda en fases
    Early/Mid/Execute con metricas por fase. Tal como lo describen depende de
    saber cuando se plant la bomba, y eso es justo lo que
    `docs/formato-rec.md` documenta como ya no disponible como dato duro
    desde Y11S3 (solo `possible_plant`, una inferencia que "no entra en
    ninguna metrica"). Una version fiel al espiritu de la idea pero sin esa
    dependencia -- partir la ronda en tercios por **reloj**, que si es un
    dato confiable -- es factible con lo que ya parsea el proyecto.
    Candidato: ver Pendientes.
  - **"Dynamic Heatmap Analytics"** y **"Team Statistics Hub"** (site take
    rate, post-plant success, retake efficiency, synergy scores): la primera
    ya esta descartada en `docs/roadmap.md` (el `.rec` no trae coordenadas);
    la segunda depende de plant/defuse ciertos para "post-plant success" y
    "retake efficiency" -- mismo problema que el punto anterior, pero sin una
    version reducida que lo evite ("site take rate" ya existe como winrate
    por sitio en este proyecto). Van a Descartados completas.
  - **"Voice Comm Integration"**: captura de audio del juego. No-goal (hook
    al juego). Va a Descartados.
  - **"Opponent Scouting Reports"**: ya esta en Ideas descartadas de
    `docs/roadmap.md` ("Scouting de rivales fuera de tus partidas").
- [Aurelix](https://aurelix.app/): sin cambios visibles desde la revision
  anterior (sitio bloqueado desde este entorno; su cuenta en X no muestra
  anuncios nuevos desde la ultima revision).

### Pedidos de la comunidad

Reddit sigue sin devolver resultados usables desde este entorno: tercera
revision seguida en la que `r/Rainbow6` y `r/SiegeAcademy` solo devuelven
contenido generico de trackers de API (MMR, leaderboards), no hilos
puntuales sobre analisis de replays. No se fuerza ningun hallazgo. Si se
repite en la proxima revision, vale la pena que alguien con acceso normal a
Reddit revise a mano en vez de seguir intentando por busqueda desde este
entorno.

### Descartados

| Hallazgo | Fuente | Por que no |
|---|---|---|
| r6-dissect #114: `winCondition` faltante en rondas sin barrida | [issue #114](https://github.com/redraskal/r6-dissect/issues/114) | Mismo limite ya documentado en `docs/formato-rec.md` (plant/defuse solo inferido); sin patron nuevo que probar. |
| R6 Replay: Dynamic Heatmap Analytics | [roadmap](https://r6-replay.com/roadmap) | El `.rec` no trae coordenadas. |
| R6 Replay: Team Statistics Hub (post-plant success, retake efficiency, synergy scores) | [roadmap](https://r6-replay.com/roadmap) | Depende de plant/defuse ciertos, que el `.rec` no entrega con certeza desde Y11S3. |
| R6 Replay: Voice Comm Integration | [roadmap](https://r6-replay.com/roadmap) | Captura de audio del juego; no-goal (hook al juego). |
| R6 Replay: Opponent Scouting Reports | [roadmap](https://r6-replay.com/roadmap) | Ya en Ideas descartadas de `docs/roadmap.md` (scouting de rivales fuera de tus partidas). |

### Pendientes promovidos

- **#22 Notas y marcadores por ronda** -- adaptado de "Bookmarks & Notes
  System" de R6 Replay, sin la parte de compartir.
- **#23 Metricas por tercio de ronda segun el reloj** -- adaptado de
  "3-Stage Round Analysis" de R6 Replay, usando el reloj en vez del plant
  para no heredar una inferencia en una metrica agregada.

Ver `docs/roadmap.md` para el detalle de cada item.
