---
name: equipo-dev
description: Una iteracion del equipo de desarrollo autonomo de r6-replay-lab. Corre cada 3 horas en una sesion cloud nueva y cada iteracion la lidera un rol distinto (release, po, arquitecto, dev, revisor, qa, investigador) segun lo que el pipeline necesita (`turno.sh`); el reloj desempata. Usar cuando la rutina lo pida o con /equipo-dev [rol].
---

# Equipo de desarrollo: una iteracion, un rol

Siete roles se turnan: **release manager, product owner, arquitecto, dev,
revisor, QA e investigador**. Cada sesion es un turno de un solo rol; el trabajo pasa de un
rol al siguiente a traves de **fichas** (un archivo por item en
`docs/backlog/`) que viven en git. Nadie recuerda nada entre turnos: todo lo
que un rol necesita saber esta en las fichas, en las ramas, en este archivo
(lo comun a todos) y en `roles/<rol>.md` (lo de su rol, y solo eso).

Lo que manda, en este orden: `CLAUDE.md` (reglas duras del proyecto), este
documento (como trabaja el equipo), las fichas (que hay que hacer). Si algo de
aca contradice `CLAUDE.md`, gana `CLAUDE.md`.

## Principios

1. **Terminar antes que empezar.** Lo que ya tiene codigo se revisa, se
   prueba y se entrega antes de abrir trabajo nuevo.
2. **Un item, una ficha, una rama.** La ficha viaja con el codigo y se
   mergea con el. Nadie toca `docs/roadmap.md`: quedo como historia.
3. **Verde o no se empuja codigo.** `./scripts/check.sh` tiene que terminar
   en `Todo en verde.` con todos sus pasos (lint, tests, build, e2e). Un verde a medias no
   es verde.
4. **Independencia.** Una misma sesion firma como mucho una de estas etapas
   sobre la misma ficha: implementar, revisar, probar.
5. **El release manager mergea.** Un item entra a `main` solo por PR y solo
   cuando paso la puerta de merge: dev, revisor y QA en tres sesiones
   distintas, `check.sh` en verde sobre la rama ya fusionada con `main`, sin
   pedidos del humano sin responder y sin veto. Lo que la nube no puede
   verificar (Electron, `.ps1`, instalador) y lo que toca las reglas del
   propio equipo lo mergea el humano. Nadie empuja a `main` directo, nadie
   hace force-push, y la unica rama que se borra es la que se acaba de
   mergear.
6. **No inventar trabajo, pero tampoco achicarse.** Una ficha existe solo si
   quien usa la app gana algo. Con `ALCANCE.md` lleno de cosas que la app
   todavia no hace, "no hay nada que proponer" no es una salida valida del
   PO ni del Arquitecto: es una seccion de `ALCANCE.md` que falta escribir.
7. **Crecer es el objetivo.** El equipo existe para que la app haga cada vez
   mas cosas, no solo para endurecer las que ya hace. Ver "Directiva de
   alcance": manda sobre la eleccion de que proponer, disenar e implementar,
   y no relaja ninguna regla dura de `CLAUDE.md`.

## Directiva de alcance (del humano, 2026-10-10)

Pedido literal: "que el loop aumente el alcance lo mas posible del
proyecto". Hasta la ficha 35 el papel fue casi todo tests y arreglos de 500;
desde aca la prioridad es **funcionalidad nueva** que quien usa la app vea o
pueda usar. Lo que sigue manda sobre las fuentes y el orden de eleccion de
cada rol; la independencia, la puerta de merge y `check.sh` siguen
exactamente igual.

- **Que cuenta como funcionalidad** (`tipo: funcionalidad` en la ficha):
  una pagina, panel, tabla, grafico, metrica, regla del coach, filtro,
  exportacion, flujo (importar, configurar, respaldar, etiquetar) o
  integracion de la app de escritorio que hoy no existe, o una ampliacion
  visible de una que existe. No cuenta: tests, refactors, robustez, docs ni
  arreglos (`tipo: tests | bug | deuda`). Ficha sin `tipo:` = no es
  funcionalidad.
- **Mezcla.** Cada turno del PO propone al menos una funcionalidad. Una ficha
  `tests` o `deuda` suelta solo entra si el papel ya tiene 3 funcionalidades
  esperando (`propuesto` o `disenado`). Un **bug real** (numeros mal, 500 con
  datos legitimos, importacion que se cae) no paga cuota: entra siempre, con
  prioridad 1 o 2, porque un numero equivocado le quita valor a todo lo demas.
  Los tests que una funcionalidad necesita van dentro de su ficha.
- **`ALCANCE.md`**, en la rama `backlog`, es el mapa de lo que la app todavia
  no hace: epicas por tema, cada una con sus tramos, los datos del `.rec` que
  usa y su estado (`idea`, `ficha NN`, `en main`, `PR #n`). Lo mantiene el
  PO y lo alimentan dos lados: el PO y el Arquitecto con lo que ven adentro
  del repo, y el **Investigador** con lo que trae de afuera (otras
  herramientas, otros juegos, la comunidad, parsers abiertos), con su
  bitacora en `INVESTIGACION.md`. Las semillas estan en `docs/backlog/` de
  `$REF` y se copian a `backlog` si no existen. El humano lo edita desde la web para reordenar o
  tachar ideas: una idea tachada o marcada `no` no se propone.
- **Epicas y tramos.** Lo grande no se descarta por grande: se parte en
  tramos de una epica (`epica: <slug>` en la cabecera). Cada tramo cabe en un
  turno de Dev, se mergea solo y deja algo que el usuario ve o puede hacer;
  un tramo "solo backend" vale si el siguiente ya esta `propuesto` con
  "Implementar despues de #NN". Una epica empezada se termina antes de abrir
  otra del mismo tema.
- **Ideas con PR abierto fuera del equipo** (hoy #1, #12 y #14) no se
  proponen mientras ese PR siga abierto: duplicarlo es pelear con trabajo del
  humano. Quedan en `ALCANCE.md` con `PR #n`; si el humano lo cierra sin
  mergear, la idea vuelve a estar libre.
- **Decisiones de producto.** Si una funcionalidad necesita una decision del
  humano, el PO propone la variante mas conservadora y reversible, deja la
  alternativa en `## Para el humano` y la ficha avanza igual. Solo se frena
  (P10) lo que no se puede deshacer.
- **Lo que crecer no toca.** Overlay in-game, scraping, red sin clic,
  dependencias nuevas, cuentas, nube, telemetria, datos que el `.rec` no
  trae, metricas de replay que dependan de Ubisoft: siguen prohibidos. Una
  idea que choca con eso va a "Ideas descartadas" de `ALCANCE.md` con el
  motivo, para que nadie la vuelva a proponer.
- **Medida.** `estado.sh` cuenta las funcionalidades en papel y en las ramas
  de trabajo, y `ESTADO.md` muestra en `## Alcance` las epicas en curso y
  las funcionalidades que llegaron a `main` en los ultimos 7 dias. Si en 7
  dias no llego ninguna, el Release lo dice en `## Para el humano` con el
  cuello de botella (papel vacio, diseno trabado, cola llena, rojo).

## Arranque comun (todos los roles, 5 minutos)

```bash
cd /home/user/r6-replay-lab 2>/dev/null || cd "$(git rev-parse --show-toplevel)"
git fetch origin main '+refs/heads/claude/*:refs/remotes/origin/claude/*'
for REF in origin/main origin/claude/equipo-dev/playbook; do git cat-file -e "$REF:.claude/skills/equipo-dev/rutina.md" 2>/dev/null && break; done
git show $REF:scripts/equipo-dev/turno.sh | bash -s --      # decide el rol; escribe .git/equipo-dev.env (un rol al final solo si lo pidieron)
git show $REF:scripts/equipo-dev/estado.sh | bash           # papel, ramas, cola, salud, entorno
. "$(git rev-parse --git-dir)/equipo-dev.env"
git show $REF:.claude/skills/equipo-dev/SKILL.md            # este archivo: lo comun
git show $REF:.claude/skills/equipo-dev/roles/$EQUIPO_ROL.md   # solo la especificacion de tu rol
```

Cada turno lee este archivo y el de su rol, nunca los siete: la
especificacion de los demas roles es contexto que no usa.

La cadena prueba `rutina.md`, que solo este playbook tiene: un `main` con
un playbook viejo mergeado no la gana. Si el `git show` de `turno.sh` falla
o `turno.sh` imprime `SIN_PLAYBOOK` (ninguna ref de la cadena tiene el
playbook), el turno termina con un informe de una linea. Antes de trabajar,
probar el acceso con `git push --dry-run origin HEAD:refs/heads/claude/equipo-dev/prueba-acceso`
(no crea nada); si devuelve 403 u otro rechazo, no se implementa nada:
informe con el comando y el mensaje exactos.

`turno.sh` escribe `.git/equipo-dev.env` (nunca se commitea) con `EQUIPO_ROL`,
`EQUIPO_FRANJA`, `EQUIPO_MOTIVO` (por que ese rol), `EQUIPO_RELOJ` (el rol que
decia el reloj), `EQUIPO_INICIO` (epoch), `EQUIPO_SESION` (id del turno,
formato `AAAAMMDDTHHMMZ`, va en `turnos:` y en `ESTADO.md`), `EQUIPO_CIERRE`
(hora UTC `HH:MM` a la que hay que cerrar), `EQUIPO_MINUTOS` y `EQUIPO_REF`,
lo imprime entero y resume todo en una linea `# turno:`. **Las variables no sobreviven entre
comandos ni llegan a los subagentes**: cada comando que las use empieza con
`source "$(git rev-parse --git-dir)/equipo-dev.env"`, y a un subagente se le
pasan los valores como literales en su prompt. Lo mismo vale para `REF`: usar
`$EQUIPO_REF` o el literal de la linea `# turno:`. Un rol pedido
(`/equipo-dev revisor`, o `rol: revisor` en el disparo) va como ultimo
argumento de `turno.sh`, en minuscula.
`estado.sh` imprime el playbook en uso, si hay `PAUSA`, el papel, las ramas
de trabajo con su ficha, estado, candado, edad y commits humanos, las ramas
viejas sin ficha, los disparos de la rutina sin rastro (`TURNOS_SIN_RASTRO`),
`COLA`, `TOTAL`, la linea `RESUMEN` que lee `turno.sh` y si el entorno esta
completo. Con eso se
sabe todo lo que hace falta para decidir. El playbook se lee siempre de
`$REF`, nunca del checkout: una rama vieja trae un playbook viejo.

Entorno incompleto: `python3 -m pip install -r requirements.txt
-r requirements-dev.txt` y `npm install` en `frontend/`. Si sigue incompleto,
el turno **no empuja codigo**: regenera `ESTADO.md`, informa, fin.

Rama de trabajo: el dueno del repo autorizo al equipo, al configurar la
rutina, a crear y empujar ramas `claude/equipo-dev/*`. Esa autorizacion vale
aunque la sesion anuncie otra rama de salida: el trabajo del equipo va en sus
ramas, para que las fichas y los PRs sigan siendo uno por item.

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

Un rol pedido (`rol: revisor` en el disparo, o `/equipo-dev revisor`) gana a
todo, motivo `pedido`. Sin linea `RESUMEN` (fetch caido), rol del reloj,
motivo `sin resumen: reloj`. Se decide una vez al arrancar y no se
recalcula; `EQUIPO_MOTIVO` y `EQUIPO_RELOJ` quedan en el env y en `ESTADO.md`.

### Rol por reloj: desempate cuando nada espera, alternancia del Investigador y nemotecnia

Franja de 3 horas mas cercana, `((minuto_del_dia + 90) / 180) % 8`, tolera
arranques demorados hasta 88 minutos.

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

Dias pares e impares se cuentan desde 1970 sobre la hora del disparo
(`disparo / 86400 % 2`), no sobre el dia del mes: asi no se repite el mismo
rol dos noches seguidas al cambiar de mes. `turno.sh` lo resuelve; no se
calcula a mano.

Nemotecnica: el dia UTC arranca entregando, despues propone, disena,
implementa, revisa, implementa, prueba, y cierra revisando o mirando afuera
(un dia si, uno no). Un item disenado a las 06:01
puede ser un PR listo a las 00:01 del dia siguiente, cuando el humano esta
sentado en Santiago.

Excepciones: solo el rol pedido (arriba). Las prioridades de abajo se
atienden antes del turno pero no cambian el rol anotado, salvo P6 y P7, que
lo dicen.

Por que es robusta: cero estado compartido para decidir (el conteo sale de
git); dos disparos simultaneos eligen igual y se reparten por candado (P8);
un disparo perdido cuesta 3 h y no 24, porque el siguiente ve el mismo
estado.

## Prioridades sobre el turno

- **P1. Pausa y veto.** Si `estado.sh` dice `PAUSA`, el turno termina con
  un informe de una linea y cero pushes. Si dice `SIN_MERGE`
  (`docs/backlog/SIN_MERGE` en la rama `backlog`), todo sigue igual pero
  nadie mergea: lo aprobado queda `entregado` para el humano. Son los dos
  botones del humano, y se vuelven a mirar (`git fetch origin` y
  `git cat-file -e`) antes de cada push de codigo: si aparecieron a mitad de
  turno, se sueltan los candados y se cierra.
- **P2. Pedido del humano sin responder**, cualquiera sea el rol: commit con
  autor distinto de `Claude` en una rama del equipo (lo lista `estado.sh`),
  texto nuevo bajo `## Para el equipo` de `ESTADO.md`, comentarios de PR si
  hay herramientas. Pedido chico y local (menos de 30 min): se hace,
  `check.sh`, push, respuesta fechada en la ficha. Pedido grande o de
  diseno: propuesta concreta en la ficha y en `ESTADO.md`, ficha a
  `con hallazgos`. Un commit del humano invalida la revision y la QA que la
  ficha tuviera: vuelve a `implementado`.
- **P3. Rama rota contra main.** `git merge-tree --write-tree origin/main
  origin/<rama>` con salida 1 = conflicto. Cualquier rol la arregla en el
  momento (checkout, `git merge origin/main`, resolver, `check.sh`, push),
  la mas vieja primero, tope 30 minutos por rama. Dos ramas con migracion
  `0002_*`: la mas nueva renumera despues de mergear main.
- **P4. check.sh rojo reproducido localmente** en una rama del equipo: si el
  turno es Dev lo arregla primero; si no, `con hallazgos` con el error
  exacto. Un rojo de GitHub Actions con verde local **no cuenta**: se anota
  una vez en `ESTADO.md` y nadie toca el workflow. Main rojo reproducido en
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
  `check.sh`, cada subagente y cada fase nueva: `source "$(git rev-parse --git-dir)/equipo-dev.env"
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
con pares `rol sesion` separados por coma, en orden cronologico:
`turnos: po 20261008T0305Z, arquitecto 20261008T0610Z, dev 20261008T0905Z`.

Estados, vocabulario cerrado y quien los escribe: `propuesto` (PO) ->
`disenado` (Arquitecto) -> `en curso <fecha>` (Dev, el reclamo) ->
`implementado` (Dev) -> `revisado` o `con hallazgos` (Revisor) -> `aprobado`
o `con hallazgos` (QA) -> `entregado` (Release). `con hallazgos` vuelve al
Dev. Lateral: `descartado (<motivo>)` (PO, Arquitecto, o Release si el humano
cerro el PR). Hecho no lo escribe nadie: hecho es que la ficha esta en main.

Dos lugares:

1. **Rama `claude/equipo-dev/backlog`**, creada una vez desde `origin/main`
   por el primer turno de **cualquier rol** que no la encuentre (`git
   checkout -b claude/equipo-dev/backlog origin/main`, copiar `README.md`,
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

**Numeracion.** Siguiente = `max(29, numeros de docs/backlog/ en main, en
backlog y en las ramas de trabajo) + 1`. Se arranca en 30 porque `mercado/*`
y `claude/loop-*` ya usan del 20 al 26 en el roadmap.

**`ESTADO.md`**, el tablero, en la rama `backlog`, regenerado entero por cada
turno al cerrar siguiendo `docs/backlog/ESTADO.plantilla.md` (leerla de `$REF`): `actualizado:` (rol, sesion), `playbook:` (`$REF@sha`),
`pausa:`; cola con rama, ficha, estado, horas desde el ultimo commit, link
`https://github.com/bfigueroa99/r6-replay-lab/compare/main...<rama>?expand=1`
y si tiene PR; orden de merge sugerido (merge de prueba por pares con
`git merge-tree --write-tree origin/A origin/B` y que archivos libera cada
merge); papel (`propuesto`, `disenado`, `descartado` de los ultimos 30 dias,
con `tipo`); `## Alcance` (epicas en curso con sus tramos, funcionalidades
que llegaron a `main` en los ultimos 7 dias, ideas libres en `ALCANCE.md`:
las lineas de `== alcance` de `estado.sh`); ultimo turno de
cada rol; `## Para el humano` (preguntas acumuladas, ramas
borrables con `git push origin --delete <rama>` listo para pegar, aviso unico
de CI remota, cambios que piden "Verificar en el PC"); `## Para el equipo`,
que escribe el humano y el equipo preserva tal cual, agregando respuestas
fechadas debajo.

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

## Especificacion por rol

Cada rol tiene su archivo en `roles/`, y cada turno lee **solo el suyo**
(mas el de otro rol si cae en su fallback, por ejemplo QA que revisa):

```bash
source "$(git rev-parse --git-dir)/equipo-dev.env"
git show "$EQUIPO_REF:.claude/skills/equipo-dev/roles/$EQUIPO_ROL.md"
```

| rol | archivo | cuando |
|---|---|---|
| Release manager | `roles/release.md` | reglas 1 y 5; por reloj, franja 0 |
| Product owner | `roles/po.md` | reglas 7 y 10; por reloj, franja 1 |
| Arquitecto | `roles/arquitecto.md` | regla 9; por reloj, franja 2 |
| Dev | `roles/dev.md` | reglas 4 y 8; por reloj, franjas 3 y 5 |
| Revisor | `roles/revisor.md` | regla 3; por reloj, franja 4 y la 7 de los dias impares |
| QA | `roles/qa.md` | regla 2; por reloj, franja 6 |
| Investigador | `roles/investigador.md` | reglas 6 y 11; por reloj, la franja 7 de los dias pares |

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
   sin rastro en 48 h (<lista>); revisar el historial de la Routine
   \`r6-replay-lab: equipo dev cada 3h\`` y `Playbook candidato: <linea
   PLAYBOOK_CANDIDATO>`.
3. Informe final, que tiene que entenderse solo:

```
## Iteracion equipo-dev <fecha UTC>

**Turno:** <rol> (motivo: <EQUIPO_MOTIVO> | reloj: <EQUIPO_RELOJ>, franja N)
**Playbook:** <ref>@<sha corto>[ (pruebas: ok | FALLAN k)]
**Rutina:** <n> disparos sin rastro en 48 h | todos con rastro[; prompt al dia | prompt sincronizado con rutina.md@<sha corto> | sin herramientas para comparar | apagada]
**Entregado:** <ficha NN: estado anterior -> nuevo, rama> | mergeado a main: <PR #n, ficha NN> | nada, porque <motivo>
**Mantenimiento:** <P2/P3/P4 atendidos> | nada pendiente
**Cola:** COLA=<n>/4 TOTAL=<n>/6 | papel: <n> propuesto, <n> disenado (<n> funcionalidad)
**Alcance:** <funcionalidades a main en 7 dias, epica en curso> | nada nuevo, porque <cuello de botella>
**GitHub:** con herramientas (<PRs tocados>) | sin herramientas
**Descartado esta vez:** <ficha o idea> porque <filtro> | nada
**Para el humano:** <decision, pregunta o rama para mergear/borrar> | nada
**Verificacion:** check.sh en verde (<n> tests backend, <n> frontend, build ok) | sin pushes de codigo
```

Lo que va entre corchetes en `**Playbook:**` y `**Rutina:**` lo escribe solo
el Release (pasos 8 y 9 de `roles/release.md`).

## Transicion

- Mientras este playbook no este en `main`, `$REF` es la segunda ref de la
  cadena de `turno.sh` y `ESTADO.md` e informe lo dicen en `playbook:`. El
  PR del playbook lo mergea el humano: toca las reglas del equipo. Nadie
  empuja a esa rama sin `bash scripts/equipo-dev/pruebas.sh` en
  `PRUEBAS_OK`. Lo diferido de la maquinaria vive en
  `docs/backlog/MAQUINARIA.md`.
- Ramas del playbook anterior (`estado.sh` las lista: reclamaban en
  `docs/roadmap.md` con un commit `Reclama:` y la sesion les imponia el
  nombre, como `claude/confident-feynman-*`). Con codigo: el primer Revisor
  (o QA en su fallback) les crea la ficha a partir de su entrada en el
  roadmap y del mensaje de su ultimo commit, en `implementado`, y sigue como
  siempre; si ya tienen PR abierto, el PR se conserva y la sesion que las
  hizo ya termino, asi que no aplica la espera de 3 horas de P8 (sin
  herramientas para ver el PR, vale la regla general: commits de menos de 3
  horas = posible sesion viva). Con solo el commit de reclamo: borrables, se
  listan en `ESTADO.md` y no se les crea ficha.
- Los numeros 20 a 29 del roadmap estan tomados o reservados por
  `mercado/*`, `claude/loop-*` y los PRs del playbook anterior; no se tocan.
  El PO puede importar esos candidatos como fichas nuevas con numero nuevo.

## Lo que el equipo nunca hace

- Mergear fuera del turno de Release o sin pasar la puerta de merge. Aprobar
  PRs formalmente. Cerrar PRs. Empujar a `main` directo. Force-push. Rebase
  de ramas publicadas. Borrar ramas, salvo la que el Release acaba de
  mergear. Empujar a `claude/equipo-dev/playbook`.
- Saltar, desactivar o borrar un test. Empujar codigo con `check.sh` en rojo.
- Agregar dependencias, servicios externos, cuentas, telemetria, red.
  Cualquier forma de overlay in-game.
- Subir `.rec`, `.sqlite3` o `.env`. Tocar `docs/roadmap.md`, `mercado/*`,
  `claude/loop-*` ni las ramas del humano.
- Hacer mas de una de estas etapas sobre la misma ficha en la misma sesion:
  implementar, revisar, probar.
