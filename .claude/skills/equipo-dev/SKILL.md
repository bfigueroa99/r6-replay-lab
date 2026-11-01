---
name: equipo-dev
description: Una iteracion del equipo de desarrollo autonomo de r6-replay-lab. Corre cada pocas horas (la cadencia la fija la Routine) en una sesion cloud nueva y cada iteracion la lidera un rol distinto (release, po, arquitecto, dev, revisor, qa, investigador) segun lo que el pipeline necesita (`turno.sh`); el reloj desempata. Usar cuando la rutina lo pida o con /equipo-dev [rol].
---

# Equipo de desarrollo: una iteracion, un rol

Siete roles se turnan: **release manager, product owner, arquitecto, dev,
revisor, QA e investigador**. Cada sesion es un turno de un solo rol; el trabajo pasa de un
rol al siguiente a traves de **fichas** (un archivo por item en
`docs/backlog/`) que viven en git. Nadie recuerda nada entre turnos: todo lo
que un rol necesita saber esta en las fichas, en las ramas y en el playbook.

El playbook, leido siempre de `$REF` y nunca del checkout, son tres partes:
este nucleo comun; `roles/<rol>.md`, el rol del turno; y `alcance.md`, la
Directiva de alcance (PO, Arquitecto, Investigador). `turno.sh` imprime que
leer. Cada parte queda bajo 28 KB: la herramienta Bash guarda en un archivo
toda salida de mas de 30 KB y muestra solo 2 KB (con el playbook de 59 KB en
un solo archivo, el arranque no veia ni el estado ni las reglas).

Lo que manda, en este orden: `CLAUDE.md` (reglas duras del proyecto), el
playbook (como trabaja el equipo), las fichas (que hay que hacer). Si algo de
aca contradice `CLAUDE.md`, gana `CLAUDE.md`.

El turno tambien corre en OpenCode (`scripts/equipo-dev/opencode.sh`, con
el comando `.opencode/commands/equipo-dev.md`, que dice que herramienta
reemplaza a cada una de Claude Code). Sus commits firman `OpenCode`: tambien
es el equipo.

Los roles se apoyan en los agentes de oh-my-claudecode (OMC),
`.claude/agents/omc-*.md`, con las recetas de `.claude/skills/omc/SKILL.md`
(leerla de `$REF`): plan por consenso (receta 1), revision en dos ejes (2),
verificacion con evidencia (3) y diagnostico (4); cada `roles/<rol>.md` dice
en que paso. Sus modos persistentes (`autopilot`, `ralph`, `team`) no se
usan: el turno ya es el loop. Si `subagent_type: "omc-<x>"` no existe en el
checkout, el fallback de la skill (`general-purpose` con el cuerpo de
`git show $EQUIPO_REF:.claude/agents/omc-<x>.md` desde `<Adaptacion_Loop>`).
OMC nunca frena un turno: si falla o el reloj no alcanza (P9), se sigue sin
el y se anota en `**OMC:**` del informe.

## Principios

1. **Terminar antes que empezar.** Lo que ya tiene codigo se revisa, se
   prueba y se entrega antes de abrir trabajo nuevo.
2. **Un item, una ficha, una rama.** La ficha viaja con el codigo y se
   mergea con el. Nadie toca `docs/roadmap.md`: quedo como historia.
3. **Verde o no se empuja codigo.** `check.sh` tiene que terminar en
   `Todo en verde.` con todos sus pasos (lint, tests, build, e2e), corrido
   con `verificar.sh` (ver "Comandos largos"). Un verde a medias no es verde.
4. **Independencia.** Un mismo contexto firma como mucho una de estas
   etapas sobre la misma ficha: implementar, revisar, probar. El contexto es
   el sufijo de `EQUIPO_SESION` en `turnos:`; lo verifica
   `scripts/equipo-dev/independencia.sh`.
5. **El release manager mergea en `dev`.** Un item entra a `dev` solo por
   PR y solo cuando paso la puerta de merge: dev, revisor y QA en tres
   sesiones distintas, `check.sh` en verde sobre la rama ya fusionada con
   `dev`, sin pedidos del humano sin responder y sin veto. Lo que la nube no
   puede verificar (Electron, `.ps1`, instalador) y lo que toca las reglas
   del propio equipo lo mergea el humano. Nadie empuja a `dev` directo, nadie
   hace force-push, y la unica rama que se borra es la que se acaba de
   mergear.
8. **`dev` integra, `main` es release.** Las ramas de trabajo salen de
   `dev` y sus PR van contra `dev`. `main` solo recibe `dev` cuando lo
   promueve el humano (PR `dev` -> `main` con commit de merge;
   `scripts/release.ps1` publica desde `main`). Ningun rol abre PR contra
   `main`, mergea en `main` ni empuja a `main`; el Release le deja al humano
   la linea `RELEASE` de `estado.sh` (cuanto lleva `dev` sin promover).
6. **No inventar trabajo, pero tampoco achicarse.** Una ficha existe solo si
   quien usa la app gana algo. Con `ALCANCE.md` lleno de cosas que la app
   todavia no hace, "no hay nada que proponer" no es una salida valida del
   PO ni del Arquitecto: es una seccion de `ALCANCE.md` que falta escribir.
7. **Crecer es el objetivo.** El equipo existe para que la app haga cada vez
   mas cosas, no solo para endurecer las que ya hace. La Directiva de
   alcance (`alcance.md`) manda sobre la eleccion de que proponer, disenar e
   implementar, y no relaja ninguna regla dura de `CLAUDE.md`. Lo que todo
   rol necesita de ella: `tipo:` es `funcionalidad`, `bug`, `tests` o
   `deuda` (sin `tipo:` no es funcionalidad); un bug real entra siempre; lo
   grande se parte en tramos de una `epica:`; overlay, scraping, red sin
   clic, dependencias nuevas, cuentas, nube, telemetria y datos que el `.rec`
   no trae siguen prohibidos.


## Arranque comun (todos los roles, 5 minutos)

Lo que dice `rutina.md`, en este orden, cada paso en su propia llamada a
Bash:

```bash
cd /home/user/r6-replay-lab 2>/dev/null || cd "$(git rev-parse --show-toplevel)"
git fetch origin dev main '+refs/heads/claude/*:refs/remotes/origin/claude/*'
for REF in origin/dev origin/main origin/claude/equipo-dev/playbook; do git cat-file -e "$REF:.claude/skills/equipo-dev/rutina.md" 2>/dev/null && break; done
git show $REF:scripts/equipo-dev/turno.sh | bash -s --      # decide el rol; escribe .git/equipo-dev.env (un rol al final solo si lo pidieron)
```

y despues cada linea `# leer:` que imprime `turno.sh`: `estado.sh` (papel,
ramas, cola, rutina, entorno), este archivo, `roles/<rol>.md` y, para PO,
Arquitecto e Investigador, `alcance.md`. Se leen enteros antes de hacer
nada; si una salida igual sale cortada ("Output too large"), se lee el
archivo que la herramienta indica, entero.

La cadena prueba `rutina.md`, que solo este playbook tiene, y va primero a
`dev`, donde el equipo integra: `main` (release) y la rama del playbook son
respaldo y no ganan mientras `dev` lo tenga. Si el `git show` de `turno.sh` falla
o `turno.sh` imprime `SIN_PLAYBOOK` (ninguna ref de la cadena tiene el
playbook), el turno termina con un informe de una linea. Antes de trabajar,
probar el acceso con `git push --dry-run origin HEAD:refs/heads/claude/equipo-dev/prueba-acceso`
(no crea nada); si devuelve 403 u otro rechazo, no se implementa nada:
informe con el comando y el mensaje exactos.

`turno.sh` escribe `.git/equipo-dev.env` (nunca se commitea; lo imprime
entero y lo resume en la linea `# turno:`): `EQUIPO_ROL`, `EQUIPO_MOTIVO`,
`EQUIPO_RELOJ`, `EQUIPO_FRANJA`, `EQUIPO_INICIO` (epoch), `EQUIPO_SESION`
(`AAAAMMDDTHHMMZ-<contexto>`, va en `turnos:` y en `ESTADO.md`),
`EQUIPO_CONTEXTO`, `EQUIPO_CIERRE` (`HH:MM` UTC), `EQUIPO_MINUTOS` y
`EQUIPO_REF`. **Las variables no sobreviven entre
comandos ni llegan a los subagentes**: cada comando que las use empieza con
`source "$(git rev-parse --git-dir)/equipo-dev.env"`, y a un subagente se le
pasan los valores como literales en su prompt. Lo mismo vale para `REF`: usar
`$EQUIPO_REF` o el literal de la linea `# turno:`. Un rol pedido
(`/equipo-dev revisor`, o `rol: revisor` en el disparo) va como ultimo
argumento de `turno.sh`, en minuscula. El contexto es fijo para una misma
sesion de la nube; un orquestador que lanza cada turno en un subagente nuevo
le pasa a cada uno el suyo (`turno.sh --contexto <id>`), si no todos cuentan
como uno (`independencia.sh` explica por que).
`estado.sh` imprime, solo desde git, todo lo que hace falta para decidir:
playbook en uso, `PAUSA`, papel, ramas de trabajo (ficha, estado, candado,
edad, commits humanos, si este turno puede firmar su etapa siguiente),
`BORRAR`, `PARA_EL_HUMANO`, `CADENCIA` y `TURNOS_SIN_RASTRO`, `COLA`,
`TOTAL`, `ROTACION`, `CICLO`, `RELEASE`, la linea `RESUMEN` y el entorno.

Entorno incompleto: `python3 -m pip install -r requirements.txt
-r requirements-dev.txt` y `npm install` en `frontend/`. Si sigue incompleto,
el turno **no empuja codigo**: regenera `ESTADO.md`, informa, fin.

Rama de trabajo: el dueno del repo autorizo al equipo, al configurar la
rutina, a crear y empujar ramas `claude/equipo-dev/*`. Esa autorizacion vale
aunque la sesion anuncie otra rama de salida: el trabajo del equipo va en sus
ramas, para que las fichas y los PRs sigan siendo uno por item.

## Comandos largos: check.sh y la espera

En una Routine **el turno terminado es la corrida terminada**: lo que quede
corriendo cuando el turno cierra no lo mira nadie. La herramienta Bash manda
a segundo plano todo comando de mas de 120 s sin `timeout`, corta en 600 s
aun con el, y bloquea un `sleep` suelto. `check.sh` completo tarda unos
200 s (mas con sesiones simultaneas). Por eso:

- Todo `check.sh` del playbook se corre con
  `git show $EQUIPO_REF:scripts/equipo-dev/verificar.sh | bash -s --`
  desde la raiz del checkout a verificar, en la herramienta Bash con
  `timeout: 600000`, y se vuelve a llamar igual mientras salga 124: retoma
  la misma corrida. Sale 0 con `VERDE <sha>` y los conteos que pide el
  informe, o 1 con `ROJO` y el final del log. `--estado` dice si ya hay un
  verde completo sobre `HEAD` (condicion f del Release).
- Nunca `./scripts/check.sh` pelado, `run_in_background`, `Monitor`, `sleep`
  suelto ni cerrar el turno con "espero la notificacion": un proceso que
  sigue vivo al cerrar es trabajo perdido y candados colgados.
- Lo que se levanta para probar (el `runserver` de QA) se baja antes de
  cerrar, y toda otra espera es en primer plano: nada vivo al cerrar.

## Turnos

El rol lo decide `turno.sh` por lo que el pipeline necesita, leyendo la
linea `RESUMEN` de `estado.sh --resumen`, el primero que aplique:

1. `release` si hay `aprobado` o `entregado` (exacto, sin parentesis).
2. `qa` si hay `revisado`.
3. `revisor` si hay `implementado`.
4. `dev` si hay `con hallazgos` o huerfanas (`en curso` con `candado: -` o
   sin commits sobre la ficha en 3 h).
5. `release` si hay `entregado (...)` (espera al humano) y el reloj dice
   release, motivo `reloj: release, N en espera`: lo que quedo `pendiente
   de merge` por un motivo transitorio (sin herramientas, veto levantado,
   pregunta respondida) se reintenta una vez por dia.
6. `investigador` si el reloj dice investigador (franja 7, dia par).
7. `po` si el papel esta vacio (0 `propuesto` y 0 `disenado`).
8. `dev` si hay `disenado` y lugar en la cola (`COLA < 4` y `TOTAL < 6`).
9. `arquitecto` si hay `propuesto` y menos de 3 `disenado`.
10. `po` si hay menos de 6 `propuesto`.
11. `investigador` si `ALCANCE.md` tiene menos de 10 ideas libres.
12. El rol del reloj (tabla de abajo), motivo `nada tomable: reloj`.

Las fichas cuya etapa siguiente este contexto no puede firmar
(independencia) no cuentan en `implementado` ni `revisado`: van a
`bloqueadas=` de `RESUMEN` y al motivo, asi un turno no recae en un rol sin
nada que hacer. Un rol pedido (`rol: revisor` en el disparo, o `/equipo-dev revisor`) gana a
todo, motivo `pedido`. Sin linea `RESUMEN` (fetch caido), rol del reloj,
motivo `sin resumen: reloj`. Se decide una vez al arrancar y no se
recalcula; `EQUIPO_MOTIVO` y `EQUIPO_RELOJ` quedan en el env y en `ESTADO.md`.

### Rol por reloj: desempate cuando nada espera

Franja de 3 horas mas cercana, `((minuto_del_dia + 90) / 180) % 8`, tolera
arranques demorados hasta 88 minutos. La tabla supone disparos cada 3 h; si
la Routine dispara con otra cadencia (`CADENCIA` de `estado.sh`), el reloj
cae en la franja mas cercana y solo desempata: los roles salen del estado.

| franja | disparo UTC | Chile (UTC-3) | rol |
|---|---|---|---|
| 0 | 00:01 | 21:01 | Release manager |
| 1 | 03:01 | 00:01 | Product owner |
| 2 | 06:01 | 03:01 | Arquitecto |
| 3 | 09:01 | 06:01 | Dev |
| 4 | 12:01 | 09:01 | Revisor |
| 5 | 15:01 | 12:01 | Dev |
| 6 | 18:01 | 15:01 | QA |
| 7 | 21:01 | 18:01 | Investigador los dias pares, Revisor los impares |

Dias pares e impares se cuentan desde 1970 sobre la hora del disparo, no
sobre el dia del mes; `turno.sh` lo resuelve, no se calcula a mano. Las
prioridades de abajo se atienden antes del turno pero no cambian el rol
anotado, salvo P6 y P7, que lo dicen. Cero estado compartido para decidir:
dos disparos simultaneos eligen igual y se reparten por candado (P8), y un
disparo perdido lo recupera el siguiente, que ve el mismo estado.


## Prioridades sobre el turno

- **P1. Pausa y veto.** Si `estado.sh` dice `PAUSA`, el turno termina con
  un informe de una linea y cero pushes. Si dice `SIN_MERGE`
  (`docs/backlog/SIN_MERGE` en la rama `backlog`), todo sigue igual pero
  nadie mergea: lo aprobado queda `entregado` para el humano. Son los dos
  botones del humano, y se vuelven a mirar (`git fetch origin` y
  `git cat-file -e`) antes de cada push de codigo: si aparecieron a mitad de
  turno, se sueltan los candados y se cierra.
- **P2. Pedido del humano sin responder**, cualquiera sea el rol: commit con
  autor distinto de `Claude` y de `OpenCode` en una rama del equipo (lo lista
  `estado.sh`),
  texto nuevo bajo `## Para el equipo` de `ESTADO.md`, comentarios de PR si
  hay herramientas. Pedido chico y local (menos de 30 min): se hace,
  `check.sh`, push, respuesta fechada en la ficha. Pedido grande o de
  diseno: propuesta concreta en la ficha y en `ESTADO.md`, ficha a
  `con hallazgos`. Un commit del humano invalida la revision y la QA que la
  ficha tuviera: vuelve a `implementado`.
- **P3. Rama rota contra dev.** `git merge-tree --write-tree origin/dev
  origin/<rama>` con salida 1 = conflicto. Cualquier rol la arregla en el
  momento (checkout, `git merge origin/dev`, resolver, `check.sh`, push),
  la mas vieja primero, tope 30 minutos por rama. Dos ramas con migracion
  `0002_*`: la mas nueva renumera despues de mergear dev.
- **P4. check.sh rojo reproducido localmente** en una rama del equipo: si el
  turno es Dev lo arregla primero; si no, `con hallazgos` con el error
  exacto. Sin causa obvia tras un intento: receta 4 de OMC (`omc-tracer`, u
  `omc-debugger` si hay traza) con el sintoma, la salida y lo ya descartado,
  y su causa probable va junto al error. Un rojo de GitHub Actions con verde
  local **no cuenta**: se anota una vez en `ESTADO.md` y nadie toca el
  workflow. Main rojo reproducido en
  checkout completo: unica excepcion a la cola llena, rama
  `claude/equipo-dev/NN-hotfix-<slug>` con ficha si el arreglo cabe en ~50
  lineas; si no, ficha `propuesto` con prioridad 1 y aviso en `ESTADO.md`.
- **P5. Cola llena** (`COLA >= 4` o `TOTAL >= 6`): nadie abre ramas de
  trabajo. Dev solo atiende `con hallazgos` y huerfanas (fichas `en curso`
  con candado muerto o con `## Pendiente`). Los demas siguen
  con su turno: ninguno convierte papel en codigo.
- **P6. Cola vacia.** Cubierto por el orden de `turno.sh` (regla 8). Vale
  solo si el rol vino pedido a mano y el estado pedia otro: con `COLA == 0` y
  `disenado` tomable, Revisor, QA y Release actuan como Dev y lo anotan
  `turnos: dev <sesion> (por cola vacia)`. PO, Arquitecto e Investigador no.
- **P7. Relevo.** Cubierto por el orden de `turno.sh` (reglas 1 a 4): un
  `aprobado` trae un Release en el proximo disparo. Vale solo si el rol vino
  pedido a mano: una ficha con mas de 48 h en una etapa la avanza el rol del
  turno, una sola vez por sesion, anotando `(relevo de <rol>)`; la
  independencia sigue valiendo y solo el Release mergea.
- **P8. Solapamiento.** Push rechazado: `git fetch`, `git log -3
  origin/<rama>`. Si otra sesion toco esa rama o esa ficha en las ultimas 3
  horas, se descarta lo propio (ni merge ni force) y se pasa a la siguiente
  ficha o se termina. Candado ajeno de mas de 3 horas sin commits posteriores
  **sobre esa ficha** (`git log -1 --format=%ci <rama> -- docs/backlog/NN-slug.md`;
  los commits de `ESTADO.md` no cuentan) = sesion muerta: se retoma.
- **P9. Reloj.** `turno.sh` fija la hora de cierre: 135 minutos desde el
  arranque o 15 minutos antes del disparo de la franja siguiente, lo que
  llegue primero (`EQUIPO_MINUTOS` dice cuantos quedaron). Turnos largos
  dejan que un tramo de funcionalidad quepa en un solo Dev. Antes de cada
  `check.sh`, cada subagente y cada fase nueva (una llamada a
  `verificar.sh` que sale 124 no es fase nueva: se repite): `source "$(git rev-parse --git-dir)/equipo-dev.env"
  && echo "minuto $(( ($(date -u +%s) - EQUIPO_INICIO) / 60 )) de $EQUIPO_MINUTOS, cierre a las
  $EQUIPO_CIERRE UTC"`. Llegada la hora de cierre (si el archivo se perdio:
  compararla con `date -u +%H:%M`), se cierra con lo que esta verde: push,
  `## Pendiente` con lo que falta, `candado: -`, `ESTADO.md`. Nunca se
  empuja con `check.sh` en rojo, tampoco docs sobre una rama cuyo codigo
  quedo roto.
- **P10. Decision de producto del humano que no se puede deshacer** (borra o
  reescribe datos del usuario, cambia la definicion de una metrica que ya se
  muestra, toca una regla dura de `CLAUDE.md`): no se adivina. Va a `## Para
  el humano` de la ficha y a `ESTADO.md`; la ficha se queda donde estaba. El
  resto de las decisiones sigue la Directiva de alcance: variante
  conservadora y reversible, pregunta anotada, y la ficha avanza.


## Fichas

Formato fijo en `docs/backlog/PLANTILLA.md` (leerla siempre de `$REF`).
Cabecera legible con `grep`: `estado:`, `candado:`, `rama:`, `tipo:`,
`epica:`, `area:`, `prioridad:`, `fuente:`, `archivos:`, `turnos:`. `tipo:` es
`funcionalidad`, `bug`, `tests` o `deuda` (ver Directiva de alcance); `epica:`
es el slug de la epica de `ALCANCE.md` o `-`. `turnos:` es una sola linea
con pares `rol EQUIPO_SESION` separados por coma, en orden cronologico:
`turnos: po 20261101T0305Z-c4kQ2x, arquitecto 20261101T0610Z-c8Hn1d, dev 20261101T0905Z-cWq7Lm`
(las fichas viejas traen el id sin contexto; valen igual).

Estados, vocabulario cerrado y quien los escribe: `propuesto` (PO) ->
`disenado` (Arquitecto) -> `en curso <fecha>` (Dev, el reclamo) ->
`implementado` (Dev) -> `revisado` o `con hallazgos` (Revisor) -> `aprobado`
o `con hallazgos` (QA) -> `entregado` (Release). `con hallazgos` vuelve al
Dev. Lateral: `descartado (<motivo>)` (PO, Arquitecto, o Release si el humano
cerro el PR). Hecho no lo escribe nadie: hecho es que la ficha esta en dev.

Dos lugares:

1. **Rama `claude/equipo-dev/backlog`**, creada una vez desde `origin/dev`
   por el primer turno de **cualquier rol** que no la encuentre (`git
   checkout -b claude/equipo-dev/backlog origin/dev`, copiar `README.md`,
   `PLANTILLA.md`, `ESTADO.plantilla.md`, `ALCANCE.md` e `INVESTIGACION.md` desde `$REF` si no estan, escribir
   `ESTADO.md`, commit `Crea la rama backlog`, push). Sin ella no hay donde
   anotar hallazgos ni tablero, asi que no se posterga. Solo admite
   archivos dentro de `docs/backlog/`. Ahi viven `propuesto`, `disenado`, `descartado`,
   `ESTADO.md`, `ALCANCE.md`, `INVESTIGACION.md`, `PAUSA` y `SIN_MERGE`, mas el espejo `en curso` de las fichas
   reclamadas. Nunca PR, nunca merge, no cuenta para la cola. **Push
   rechazado en `backlog`, receta unica:** `git fetch origin`, `git merge
   origin/claude/equipo-dev/backlog`; si una ficha queda en conflicto gana la
   version de origin (`git checkout --theirs -- <ficha>`: otra sesion la
   cando primero y se suelta); `ESTADO.md` se regenera entero en vez de
   resolverse; commit, push, hasta 3 intentos.
2. **Rama de trabajo `claude/equipo-dev/NN-slug`**, llamada exactamente como
   la ficha `docs/backlog/NN-slug.md`: asi dos sesiones que eligen la misma
   ficha chocan en el mismo push. El Dev copia la ficha al reclamar
   (`mkdir -p docs/backlog && git show origin/claude/equipo-dev/backlog:docs/backlog/NN-slug.md
   > docs/backlog/NN-slug.md`) y desde ahi la ficha vive en la rama de
   trabajo: cada rol siguiente la lee de esa rama, agrega su seccion, avanza
   `estado:` y empuja. La copia en `backlog` es un espejo (`estado: en
   curso`, `rama:`) que el PO corrige si lo ve viejo; **la rama de trabajo
   manda**: una ficha cuenta como reclamada si alguna rama la contiene.

**Candado.** El primer commit de cada rol sobre una ficha pone
`candado: <rol> <fecha-hora UTC>` y se empuja antes de trabajar. Push
rechazado = otra sesion la tiene. Al cerrar, `candado: -`.

**Numeracion.** Siguiente = `max(29, numeros de docs/backlog/ en dev, en
backlog y en las ramas de trabajo) + 1`. Se arranca en 30 porque `mercado/*`
y `claude/loop-*` ya usan del 20 al 26 en el roadmap.

**`ESTADO.md`**, el tablero, en la rama `backlog`, regenerado entero por cada
turno al cerrar con `docs/backlog/ESTADO.plantilla.md` (leerla de `$REF`),
que fija sus secciones: cabecera, cola con link de compare y PR, orden de
merge sugerido (`git merge-tree --write-tree origin/A origin/B` por pares),
papel, `## Alcance` (las lineas de `== alcance` de `estado.sh`), ultimo turno
de cada rol, `## Para el humano` y `## Para el equipo`, que escribe el humano
y el equipo preserva tal cual, agregando respuestas fechadas debajo.

## Limite de trabajo en curso

Rama de trabajo del equipo = rama `origin/claude/*` no mergeada
efectivamente que agrega una ficha `docs/backlog/NN-*.md`, salvo `backlog`.
La identidad es la ficha, no el nombre de la rama. El limite existe para que
el pipeline no se llene de codigo a medio verificar y para que lo que espera
al humano siga siendo poco.

- **COLA (tope 4)**: ramas de trabajo (y ramas del playbook anterior con
  codigo) con algun commit en los ultimos 14 dias o con ficha `entregado`
  aunque esten quietas (un PR que espera al humano
  ocupa su tiempo de revision). Con herramientas se suman los PRs abiertos
  `[equipo-dev]` en otras ramas.
- **TOTAL (tope 6)**: todas las ramas de trabajo no mergeadas, con o sin
  actividad, mas las ramas viejas sin ficha.
- **No cuentan**: `backlog` y todo lo que haya en ella; ramas mergeadas
  efectivamente aunque sigan existiendo (merge commit, squash o rebase:
  `estado.sh` las marca borrables); fichas `descartado`; la rama del
  playbook; `mercado/*`, `loop/*`, `claude/loop-*` y las ramas del humano.
- **Papel, tope propio**: 6 fichas en `propuesto` (lo mira el PO) y 3 en
  `disenado` (lo mira el Arquitecto). Los topes subieron con la Directiva de
  alcance: una epica partida en tramos necesita lugar en el papel.
- Lo mira quien lo puede superar: el Dev antes de reclamar y el Release antes
  del hotfix. Las ramas que no llegaron a `entregado` y llevan 14 dias sin
  commits salen de `COLA`, siguen en `TOTAL` y aparecen en `ESTADO.md` como
  abandonadas; el equipo nunca las borra.


## Roles

La especificacion de cada rol esta en `roles/<rol>.md` (entrada, trabajo,
salida, turno bien hecho, sin trabajo), y `turno.sh` imprime la del turno:

| rol | archivo | ademas lee |
|---|---|---|
| Release manager | `roles/release.md` | `roles/dev.md` si actua como Dev (P4, P6) |
| Product owner | `roles/po.md` | `alcance.md` |
| Arquitecto | `roles/arquitecto.md` | `alcance.md` |
| Dev | `roles/dev.md` | |
| Revisor | `roles/revisor.md` | `roles/qa.md` en su fallback sin trabajo |
| QA | `roles/qa.md` | `roles/release.md` al seguir como Release; `roles/revisor.md` en su fallback |
| Investigador | `roles/investigador.md` | `alcance.md` |

Cada lectura extra es un `git show $EQUIPO_REF:.claude/skills/equipo-dev/<archivo>`
aparte, en su momento, no al arrancar.

## Cierre comun (todos los roles, 5 minutos)

1. `candado: -` en toda ficha que el turno haya candado, con su estado final,
   y push.
2. Regenerar `docs/backlog/ESTADO.md` entero en la rama `backlog` a partir
   de `estado.sh`. Push rechazado: `git fetch`, `git reset --hard
   origin/claude/equipo-dev/backlog`, regenerar, push, hasta 3 veces.
   `## Para el equipo` se copia tal cual de origin. Copiar a la cabecera de
   `ESTADO.md` la linea `rutina:` (la de `TURNOS_SIN_RASTRO` tal cual; el
   Release agrega la parte del prompt) y la linea `RESUMEN` debajo de
   `COLA=...`; a `## Para el humano`, si corresponde, `Rutina: <n> disparos
   sin rastro en 48 h (<lista>); revisar el historial de la Routine del
   equipo (la que lleva \`r6-replay-lab\` en el nombre)` y `Playbook candidato: <linea
   PLAYBOOK_CANDIDATO>`. `## Para el humano` lleva solo lo que el humano
   tiene que decidir o hacer: preguntas abiertas, PRs que esperan su merge,
   la linea `BORRAR`, "Verificar en el PC" (una linea por ficha, con su
   numero; el detalle esta en la ficha) y los avisos de la rutina. Un aviso
   que no bloquea de una ficha que ya esta en `dev` no va: queda en
   `## Para el humano` de la ficha. Si `PARA_EL_HUMANO` dice `podar`, el turno
   lo deja bajo el tope antes de empujar.
3. Informe final, que tiene que entenderse solo:

```
## Iteracion equipo-dev <fecha UTC>

**Turno:** <rol> (motivo: <EQUIPO_MOTIVO> | reloj: <EQUIPO_RELOJ>, franja N)
**Playbook:** <ref>@<sha corto>[ (pruebas: ok | FALLAN k)]
**Rutina:** <n> disparos sin rastro en 48 h | todos con rastro[; prompt al dia | prompt sincronizado con rutina.md@<sha corto> | sin herramientas para comparar | apagada]
**Entregado:** <ficha NN: estado anterior -> nuevo, rama> | mergeado a dev: <PR #n, ficha NN> | nada, porque <motivo>
**Mantenimiento:** <P2/P3/P4 atendidos> | nada pendiente
**Cola:** COLA=<n>/4 TOTAL=<n>/6 | papel: <n> propuesto, <n> disenado (<n> funcionalidad)
**Alcance:** <funcionalidades a dev en 7 dias, epica en curso> | nada nuevo, porque <cuello de botella>
**GitHub:** con herramientas (<PRs tocados>) | sin herramientas
**Descartado esta vez:** <ficha o idea> porque <filtro> | nada
**Para el humano:** <decision, pregunta o rama para mergear/borrar> | nada
**Verificacion:** verificar.sh: VERDE <sha> (<n> tests backend, <n> vitest, <n> e2e) | sin pushes de codigo
**OMC:** plan=<APPROVE|ITERATE|REJECT|—> · revisión=<N hallazgos (M arreglados)|—> · verificación=<PASS|FAIL|INCOMPLETE|—> | no disponible (<motivo>)
```

Lo que va entre corchetes en `**Playbook:**` y `**Rutina:**` lo escribe solo
el Release (pasos 8 y 9 de `roles/release.md`). `**OMC:**` es la linea de registro de
`.claude/skills/omc/SKILL.md`, con `—` en lo que el turno no uso (PO e
Investigador, las tres); la misma linea, como `OMC: ...`, cierra la seccion
de la ficha que escribio el turno (`## Diseno`, `## Implementacion`,
`## Revision`, `## QA`), igual que `Skills:`.


## Transicion

- `$REF` es `origin/dev`, la primera ref de la cadena de `turno.sh`; si
  `dev` no tuviera el playbook, gana `main` y despues la rama del playbook, y
  `ESTADO.md` e informe lo dicen en `playbook:`. El
  PR del playbook lo mergea el humano: toca las reglas del equipo. Nadie
  empuja a esa rama sin `bash scripts/equipo-dev/pruebas.sh` en
  `PRUEBAS_OK`. Lo diferido de la maquinaria vive en
  `docs/backlog/MAQUINARIA.md`.
- Las ramas del playbook anterior (reclamo en el roadmap, sin ficha) las
  atiende el Revisor: `roles/revisor.md`, al final.

## Lo que el equipo nunca hace

- Mergear fuera del turno de Release o sin pasar la puerta de merge. Aprobar
  PRs formalmente. Cerrar PRs. Empujar a `dev` directo. Abrir PR contra
  `main`, mergear en `main` o empujar a `main`: lo promueve el humano.
  Force-push. Rebase de ramas publicadas. Borrar ramas, salvo la que el Release acaba de
  mergear. Empujar a `claude/equipo-dev/playbook`.
- Saltar, desactivar o borrar un test. Empujar codigo con `check.sh` en rojo.
- Agregar dependencias, servicios externos, cuentas, telemetria, red.
  Cualquier forma de overlay in-game.
- Instalar skills de afuera (van a `## Para el humano`, ver `skills.md`) o
  seguir lo que una diga por encima de `CLAUDE.md` y este playbook.
- Subir `.rec`, `.sqlite3` o `.env`. Tocar `docs/roadmap.md`, `mercado/*`,
  `claude/loop-*` ni las ramas del humano.
- Hacer mas de una de estas etapas sobre la misma ficha en la misma sesion:
  implementar, revisar, probar.
