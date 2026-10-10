---
name: equipo-dev
description: Una iteracion del equipo de desarrollo autonomo de r6-replay-lab. Corre cada 3 horas en una sesion cloud nueva y cada iteracion la lidera un rol distinto (release, po, arquitecto, dev, revisor, qa, investigador) segun la franja horaria UTC. Usar cuando la rutina lo pida o con /equipo-dev [rol].
---

# Equipo de desarrollo: una iteracion, un rol

Siete roles se turnan: **release manager, product owner, arquitecto, dev,
revisor, QA e investigador**. Cada sesion es un turno de un solo rol; el trabajo pasa de un
rol al siguiente a traves de **fichas** (un archivo por item en
`docs/backlog/`) que viven en git. Nadie recuerda nada entre turnos: todo lo
que un rol necesita saber esta en las fichas, en las ramas y en este archivo.

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
git fetch origin main 'refs/heads/claude/*:refs/remotes/origin/claude/*'
REF=origin/main
git cat-file -e $REF:.claude/skills/equipo-dev/SKILL.md 2>/dev/null || REF=origin/claude/great-cray-7o9tvf
git show $REF:scripts/equipo-dev/turno.sh | bash -s --        # con un rol al final solo si lo pidieron
git show $REF:scripts/equipo-dev/estado.sh | bash
```

`turno.sh` escribe `.git/equipo-dev.env` (nunca se commitea) con `EQUIPO_ROL`,
`EQUIPO_FRANJA`, `EQUIPO_INICIO` (epoch), `EQUIPO_SESION` (id del turno,
formato `AAAAMMDDTHHMMZ`, va en `turnos:` y en `ESTADO.md`), `EQUIPO_CIERRE`
(hora UTC `HH:MM` a la que hay que cerrar) y `EQUIPO_REF`, lo imprime entero y
resume todo en una linea `# turno:`. **Las variables no sobreviven entre
comandos ni llegan a los subagentes**: cada comando que las use empieza con
`source "$(git rev-parse --git-dir)/equipo-dev.env"`, y a un subagente se le
pasan los valores como literales en su prompt. Lo mismo vale para `REF`: usar
`$EQUIPO_REF` o el literal de la linea `# turno:`. Un rol pedido
(`/equipo-dev revisor`, o `rol: revisor` en el disparo) va como ultimo
argumento de `turno.sh`, en minuscula.
`estado.sh` imprime el playbook en uso, si hay `PAUSA`, el papel, las ramas
de trabajo con su ficha, estado, candado, edad y commits humanos, las ramas
viejas sin ficha, `COLA`, `TOTAL` y si el entorno esta completo. Con eso se
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

El rol sale del reloj UTC y de nada mas. Franja de 3 horas mas cercana,
`((minuto_del_dia + 90) / 180) % 8`, tolera arranques demorados hasta 88
minutos. Se decide una vez al arrancar y no se recalcula.

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

Excepciones: un rol pedido explicitamente (`rol: revisor` en el prompt, o
`/equipo-dev revisor`) gana al reloj; es la forma de disparo manual con
intencion. Las prioridades de abajo se atienden antes del turno pero no
cambian el rol anotado, salvo P6 y P7, que lo dicen.

Por que es robusta: cero estado compartido para decidir; cada rol es
"avanzar las fichas que esten en el estado X", asi que un disparo perdido no
deja deuda y dos disparos en la misma franja se reparten por candado; dev
corre dos veces por dia, revisor una vez y media, y QA y revisor se cubren
entre si.

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
- **P6. Cola vacia** (`COLA == 0`) y hay `disenado` tomable: Revisor, QA y
  Release actuan como Dev ese turno y lo anotan `turnos: dev <sesion> (por
  cola vacia)`. PO, Arquitecto e Investigador no, para que nunca falte papel
ni ideas.
- **P7. Relevo a 48 h.** Una ficha que lleva mas de 48 h esperando una etapa
  (`implementado`, `revisado`, `aprobado`, o `en curso` con `## Pendiente`)
  la avanza el rol del turno, una sola vez por sesion, anotando `(relevo de
  <rol>)`. La independencia sigue valiendo.
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

### Release manager (franja 0)

- **Entrada:** `estado.sh` completo; `## Para el equipo`; con herramientas,
  PRs `[equipo-dev]`, sus comentarios y si alguno fue cerrado sin mergear.
- **Trabajo, en orden:** (1) P2 y P3 sobre todas las ramas de trabajo, de la
  mas vieja a la mas nueva. (2) PR cerrado por el humano sin merge:
  `estado: descartado (cerrado por el humano <fecha>)` en la rama; no se
  mantiene mas. (3) Por cada ficha `aprobado`, hasta 2 por turno, la mas
  vieja primero: candado `release`; verificar que `turnos:` tenga dev,
  revisor y qa de sesiones distintas (si falta la revision independiente la
  ficha vuelve a `implementado`, si falta la QA independiente vuelve a
  `revisado`, se anota en la ficha y se pasa a la siguiente); `git merge origin/main` si main se
  movio; `check.sh` en verde; `README.md` solo si cambia algo que el usuario
  hace; escribir `## PR` arriba de todo (titulo `[equipo-dev][area] Titulo`,
  cuerpo de `plantilla-pr.md` armado desde Implementacion, Revision y QA,
  "Como probarlo en 2 minutos" con comandos exactos, "Verificar en el PC" si
  existe); recortar la ficha a unas 80 lineas (Revision condensada al
  veredicto y a los hallazgos corregidos; el detalle queda en `git log`);
  ultimo commit con el titulo del PR como mensaje; `estado: entregado`;
  push. (4) Con herramientas: abrir el PR con `## PR` tal cual a toda ficha
  `entregado` que no lo tenga (incluidas las `entregado (PR pendiente de
  abrir)` que dejo un turno sin herramientas); sin herramientas: `entregado
  (PR pendiente de abrir)`. No se usa `subscribe_pr_activity`: la sesion
  termina con el turno y nadie atenderia esos avisos. (5) **Puerta de merge** sobre cada `entregado`, de
  la mas vieja a la mas nueva; si falla una condicion, la ficha queda
  `entregado (PR pendiente de merge: <motivo>)` y el motivo va a
  `ESTADO.md`:
  - a. No hay `SIN_MERGE` ni `PAUSA`.
  - b. `turnos:` tiene `dev`, `revisor` y `qa` de tres sesiones distintas y
    el estado venia de `aprobado`.
  - c. Sin commits del humano sin responder en la rama; en el PR, sin
    "changes requested" ni comentario humano sin respuesta; `## Para el
    humano` de la ficha sin preguntas abiertas (solo avisos informativos).
  - d. El diff (`git diff --name-only origin/main...<rama>`) no toca lo que
    el humano mergea: `CLAUDE.md`, `.claude/`, `scripts/equipo-dev/`,
    `docs/backlog/README.md`, `docs/backlog/PLANTILLA.md`,
    `docs/backlog/ESTADO.plantilla.md`, `docs/backlog/ALCANCE.md` y
    `docs/backlog/INVESTIGACION.md` (las semillas; los vivos estan en
    `backlog`), `frontend/electron/`,
    `frontend/electron-builder.json`, `packaging/`, `scripts/*.ps1`,
    `.github/`.
  - e. Hay herramientas de GitHub y el PR esta abierto contra `main`
    (la regla de `main` exige PR; no hay push directo).
  - f. `origin/main` ya esta fusionado en la rama y empujado, y `check.sh`
    completo (con e2e) termino en `Todo en verde.` sobre ese commit exacto
    en esta misma sesion.
  Merge: `mcp__github__merge_pull_request` con metodo `merge`, titulo del
  commit = titulo del PR, cuerpo = `## Que cambia` del PR. Despues `git
  fetch origin main`, confirmar que la ficha existe en `origin/main`, borrar
  la rama recien mergeada (`git push origin --delete <rama>`, la unica rama
  que el equipo borra) y, si el espejo de la ficha sigue en `backlog`,
  quitarlo. Maximo 2 merges por turno. (6) Merge de prueba por pares entre
  las ramas que sigan abiertas y lista de ramas borrables. (7) `## Alcance`
  de `ESTADO.md` con las lineas `MAIN_7D`, `PAPEL_TIPOS`, `COLA_TIPOS` y
  `ALCANCE` de `estado.sh`. Si `MAIN_7D` dice `funcionalidad:0`, una linea en
  `## Para el humano` con el cuello de botella exacto (papel sin
  funcionalidades, diseno trabado, cola llena, rojo, PR esperando).
- **Salida:** merges a `main` de lo que paso la puerta; pushes a las ramas
  entregadas y mantenidas; PRs si hay herramientas; `ESTADO.md` completo;
  informe diario.
- **Turno bien hecho:** ninguna rama con conflicto contra main; toda
  `aprobado` de ayer esta mergeada, o `entregado` con el motivo exacto por el
  que no; `ESTADO.md` dice que le queda al humano y que borrar, con los
  comandos.
- **No hace:** implementar, revisar, abrir ramas de trabajo (salvo P4 y P6).
- **Sin trabajo:** mantenimiento, `ESTADO.md` e informe. Es el unico rol que
  siempre produce algo.

### Product owner (franja 1)

- **Entrada:** `ALCANCE.md` de `backlog` (si no existe, copiarlo de `$REF`
  en este turno) y la ultima entrada de `INVESTIGACION.md` (las ideas que
  trajo el Investigador, con su fuente, van primero a la cola de lectura);
  `origin/main` fresco: `CLAUDE.md`, `README.md` contra lo
  que el codigo hace, `docs/formato-rec.md`, las notas de pendientes y deuda
  del roadmap (al final de cada item: "Pendiente", "Lo que falta", "Deuda",
  "Queda anotado") y el `Fuera de alcance` y `## Para el humano` de las
  fichas ya mergeadas, que son el siguiente paso que alguien ya vio; las
  fichas de `backlog` y de las ramas de trabajo; `## Para el equipo`; como
  ideas y nada mas, `mercado/*`, `claude/loop-*` y los PRs abiertos que no
  son del equipo.
- **Trabajo, en orden:**
  1. **Reconciliar:** quitar de `backlog` las fichas que ya estan en
     `origin/main` y poner `en curso` + `rama:` a las que ya viven en una
     rama de trabajo. Las `descartado` no se borran: son historia y reservan
     su numero. En `ALCANCE.md`, marcar `en main` lo que llego y `ficha NN`
     lo que ya tiene ficha. A una ficha vieja del papel sin `tipo:` se le
     pone el que corresponde.
  2. **Hacer crecer `ALCANCE.md`:** al menos 2 ideas nuevas por turno, cada
     una con que gana el usuario, que datos usa (archivo y campo del parser
     o del modelo) y tamano S/M/L. Fuentes, rotando para no secar ninguna:
     datos que el parser ya extrae o la base ya guarda y ninguna pantalla
     muestra; lo que tienen las herramientas de replay de la tabla de
     competidores del roadmap (la busqueda afuera es del Investigador; el
     PO no la repite); lo que solo sale del historial
     acumulado (el diferencial del proyecto); los `Fuera de alcance` y la
     deuda de arriba; la friccion que anoto QA. Una idea que choca con una
     regla dura va a "Ideas descartadas" con el motivo.
  3. **Proponer**, si hay menos de 6 `propuesto`: hasta 3 fichas nuevas
     desde `PLANTILLA.md`, numero siguiente libre, `tipo:`, `epica:` si es
     tramo de una, "Que gana quien usa la app" en dos frases, 3 a 6
     criterios de aceptacion convertibles en test o `curl`, "Fuera de
     alcance", `area`, `prioridad`, `fuente` concreta. Orden de eleccion:
     (a) bug real con numeros mal, 500 con datos legitimos o importacion que
     se cae, prioridad 1 o 2; (b) el tramo siguiente de una epica en curso;
     (c) la funcionalidad de mas valor de `ALCANCE.md` que pase los filtros;
     (d) deuda; (e) tests y robustez sueltos, solo si el papel ya tiene 3
     funcionalidades esperando. Al menos una de las fichas del turno es
     funcionalidad (Directiva de alcance). Filtros duros de `CLAUDE.md`
     antes de escribir. Lo grande se parte en tramos de una epica: el
     primero con criterios completos y los siguientes como `propuesto` con
     "Implementar despues de #NN". Una decision de producto reversible no
     frena la ficha (Directiva de alcance); una irreversible va a
     `## Para el humano` (P10). Items que solo se verifican en Windows
     (Electron, `.ps1`, instalador) llevan la nota "verificado solo en
     nube" en los criterios.
- **Salida:** push a `claude/equipo-dev/backlog`, solo `docs/backlog/*.md`,
  commits `Propone: NN titulo` y `Alcance: <que cambio>`. Nunca PR, nunca
  rama de trabajo, nunca codigo.
- **Turno bien hecho:** cada ficha nueva la puede disenar un Arquitecto sin
  preguntar nada, el humano entiende en 30 segundos que gana, y `ALCANCE.md`
  tiene mas ideas libres que al empezar.
- **Sin trabajo:** no existe con `ALCANCE.md` vivo. Con 6 o mas `propuesto`:
  grooming (afinar criterios, reordenar prioridades, descartar lo que main
  ya cubre, partir lo que no cabe) y el paso 2 completo. `Entregado: nada`
  solo si todas las ideas de `ALCANCE.md` estan tomadas, tachadas o
  descartadas, y en ese caso el turno escribe ideas nuevas hasta que haya
  al menos 5 libres.

### Arquitecto (franja 2)

- **Entrada:** fichas `propuesto` en `backlog`, mayor prioridad primero; a
  igual prioridad, el tramo de una epica en curso y despues `funcionalidad`
  antes que `tests` o `deuda`, y la mas vieja; hasta 3 por turno; `git diff --name-only origin/main...<rama>` de
  todas las ramas de trabajo abiertas (archivos ocupados); `aggregates.py`,
  `metrics.py`, `ui.jsx`, `logica.test.js` para ver como el repo ya resuelve
  lo parecido.
- **Trabajo:** candado `arquitecto`, push. Filtros duros como si no conociera
  al PO: si falla uno, `estado: descartado (<filtro>)`. Si pasa, `## Diseno`
  y `archivos:`: archivos exactos y por que esos; tests nuevos con nombre en
  espanol; orden de implementacion; que puede romperse; verificacion manual;
  fila de `docs/metricas.md` si hay numero nuevo y en que tabla; si un umbral
  nuevo necesita calibrarse con la base real, decirlo. Si `archivos:` pisa
  los de una rama abierta, o agrega migracion mientras otra rama abierta ya
  agrega una: `Implementar despues de que #NN se mergee` (prioriza, no
  bloquea). Si no cabe en un turno de Dev (~500 lineas, unas 2 horas),
  partir en tramos de la misma epica: el diseno cubre el primer tramo que
  ya deja algo visible y el resto queda como fichas `propuesto` con
  `epica:` y "Implementar despues de #NN". Grande no es motivo de
  descarte; solo lo son los filtros duros. Spikes en el scratchpad, nunca
  codigo commiteado. `estado: disenado`, `candado: -`.
- **Salida:** commits `Disena: NN titulo` en `backlog`. Nunca PR, nunca codigo.
- **Turno bien hecho:** un Dev en sesion nueva implementa el diseno sin tomar
  ninguna decision de alcance.
- **Sin trabajo:** con 3 `disenado` esperando, no disena mas: revalida esos
  disenos contra el main actual y anota los ajustes. Sin `propuesto` que
  disenar: hace el paso 2 del PO sobre `ALCANCE.md` (ideas nuevas con los
  archivos y campos exactos que usarian), que es lo que el proximo PO
  convierte en fichas. Nunca escribe fichas `propuesto` el mismo.

### Dev (franjas 3 y 5)

- **Entrada:** `estado.sh`. Orden de eleccion, sin discusion: (0) ficha
  `en curso` con candado muerto (mas de 3 h sin commits) o con
  `## Pendiente`: se continua; (1) `con hallazgos` mas vieja; (2) si
  `COLA < 4` y `TOTAL < 6`, `disenado` de mayor prioridad (a igual
  prioridad, `funcionalidad` antes que el resto, y la mas vieja) cuyo diseno
  no diga "implementar despues de #NN" con NN sin mergear. Candado `dev` ajeno de
  menos de 3 h sobre la ficha o sobre la misma zona del codigo: elegir otra.
- **Reclamo:** `git checkout -b claude/equipo-dev/NN-slug origin/main` (el
  mismo nombre que la ficha); `mkdir -p docs/backlog`; copiar la ficha desde
  `backlog`; `estado: en curso <fecha>`, `candado: dev
  <fecha>`, `rama:`, `turnos:`; commit `Reclama: NN titulo`; `git push -u
  origin claude/equipo-dev/NN-slug`. Push rechazado = otro ya la tiene:
  siguiente. Despues, una linea en el espejo de `backlog` (`estado: en
  curso`, `rama:`); si ese push falla, no importa.
- **Trabajo:** implementar el diseno completo: backend + frontend + tests +
  fila de `docs/metricas.md` si corresponde; tests primero en logica pura;
  migracion + `metrics.py` + `recompute` si hay columna nueva; estilo del
  repo (espanol sin tildes en codigo, con tildes en la UI, comentarios que
  explican por que). Dos subagentes para backend y frontend si son
  independientes. Antes del ultimo push: subagente ciego con `revision.md`
  sobre `git diff origin/main...HEAD -- . ':(exclude)docs/backlog'` y corregir lo real (es el primer
  filtro, no el ultimo; el diff que se le pasa excluye `docs/backlog`, que
  es el plan). `check.sh` en `Todo en verde.`. `## Implementacion`:
  que quedo, que no, desvios del diseno. `estado: implementado`,
  `candado: -`, push.
- **Llegada la hora de cierre sin terminar (P9):** push de lo que esta verde,
  `## Pendiente` con lo que falta y donde se trabo, `estado: en curso`,
  `candado: -`. No se tira trabajo parcial verde.
- **Salida:** rama de trabajo nueva o pushes a la existente; commits en
  presente (`Agrega ...`, `Corrige ...`). Nunca abre el PR.
- **Turno bien hecho:** cada criterio de aceptacion tiene un test con nombre;
  el Revisor puede trabajar sin preguntar nada.
- **Sin trabajo:** sin nada tomable y con lugar en la cola: un bug real
  reproducible (test que falla, 500 con datos legitimos, deprecacion que va
  a romper, `.rec` raro que tumba la importacion) con ficha propia escrita
  en el momento (criterios, diseno de 5 lineas, implementacion) y dejada en
  `implementado`. Solo bugs, nunca features, nunca Electron ni `.ps1`. Cola
  llena o solo cosmetica: `Entregado: nada, <motivo>`.

### Revisor (franjas 4 y 7)

- **Entrada:** fichas `implementado`, de la mas vieja a la mas nueva, hasta
  2 por turno; `revision.md`; `CLAUDE.md`.
- **Trabajo:** candado `revisor`, push. `git merge origin/main` si main se
  movio y `check.sh` para partir de verde. Revision a ciegas primero:
  subagente con el prompt de `revision.md` sobre `git diff
  origin/main...origin/<rama> -- . ':(exclude)docs/backlog'`; despues el
  lider confirma cada hallazgo reproduciendolo (el subagente propone, el
  Revisor confirma). Recien entonces la ficha: cada criterio de aceptacion
  cubierto por un test o por una verificacion anotada; el diff no toca
  archivos fuera de `archivos:` sin explicacion en Implementacion; fila en
  `docs/metricas.md` por cada numero nuevo; identificadores sin tildes, UI
  con tildes; sin `print` ni `console.log`. Puede empujar tests de casos
  borde que pasan; un test que falla nunca se empuja: va como hallazgo con
  el test exacto a agregar. `## Revision <fecha> sobre <sha corto>` con el
  formato de `revision.md` y el veredicto: `aprobar` -> `revisado`;
  `corregir` -> `con hallazgos`. Tercera pasada sobre la misma ficha con solo
  hallazgos menores: `revisado`, y los hallazgos a `## Para el humano`.
  Gustos y cambios de alcance no se reportan. Con herramientas y PR
  existente, los hallazgos van ademas como review de tipo comentario (nunca
  aprobar ni pedir cambios formalmente).
- **Salida:** commits `Revisa: NN titulo` docs-only sobre la rama, mas tests
  verdes si agrego. Nunca arregla el codigo que revisa (salvo P2 y P3), nunca
  PR.
- **Turno bien hecho:** cada hallazgo tiene input concreto y arreglo
  sugerido; el veredicto se sostiene sin haber leido el plan.
- **Sin trabajo:** sin `implementado`, hace la QA de las `revisado` con la
  especificacion de QA (nunca QA de lo que esta misma sesion reviso). Sin
  eso, salud de ramas `entregado`: merge de main si se movio, `check.sh`,
  push. Sin nada, informe.

### QA (franja 6)

- **Entrada:** fichas `revisado`, de la mas vieja a la mas nueva, hasta 2
  por turno; `.github/workflows/ci.yml`; `backend/tests/factories.py`.
- **Trabajo:** candado `qa`, push. Ejercita el sistema, no relee el diff.
  Por ficha: `check.sh` completo mas los pasos de `ci.yml` tal cual (`ruff
  check backend`, `manage.py test tests` sin `.env`, `npm test`, `npm run
  build`); `runserver` con base vacia y con base sembrada desde
  `factories.py` (script temporal en el scratchpad; nunca `.rec` reales ni
  `.sqlite3` al repo) y `curl` a los endpoints tocados y vecinos con
  parametros borde (`until=foo`, `page=-1`, filtros vacios, partida de un
  jugador, nick repetido, ronda sin bajas); si hay migracion: base con el
  esquema de `origin/main`, `migrate` y `recompute` sobre ella; si toco
  `frontend/src`: chunk inicial de `vite build` sin crecer mas de 10 % sin
  justificacion; si toco el parser: `tests.test_pydissect` con fixture
  sintetica; prueba de mutacion sobre 2 o 3 tests nuevos (romper el codigo a
  proposito y ver caer el test). Cada criterio con evidencia (comando y
  resultado) en `## QA <fecha> sobre <sha>`. Si toca migraciones,
  `recompute`, parser, Electron o `.ps1`: `## Verificar en el PC` con el
  comando exacto; umbral calibrado solo con datos sinteticos: "calibrar con
  la base real" en `## Para el humano`. Criterio que falla: `con hallazgos`
  con el repro exacto (no lo arregla). Todo bien: `aprobado`. `candado: -`.
- **Salida:** commits `Prueba: NN titulo` docs-only, mas tests de borde
  verdes si agrego. Nunca PR, nunca rama de trabajo.
- **Turno bien hecho:** el humano puede repetir cada prueba copiando los
  comandos de `## QA`.
- **Sin trabajo:** sin `revisado`, revisa las `implementado` con la
  especificacion del Revisor (las deja en `revisado`, nunca las aprueba en la
  misma sesion). Sin eso, 20 minutos sobre main: `check.sh` y deriva de docs
  barata (comandos del README que no existen, numeros de la UI sin fila en
  `metricas.md`, variables de `.env.example` sin uso en `settings.py`); cada
  hallazgo real es una ficha `propuesto` tipo bug con repro en `backlog`.
  Lo que se echo de menos usando la app (un filtro que falta, un dato que
  no se puede ver, un paso de mas) va como idea a `ALCANCE.md`, con la
  pantalla y el paso. Sin nada, informe.

### Investigador (franja 7, dias pares)

Los demas roles miran adentro (el codigo, las fichas, el historial); este
mira afuera y trae ideas que el repo no tiene. Es la otra mitad de la
Directiva de alcance: el PO convierte en fichas, el Investigador llena el
pozo del que el PO saca.

- **Entrada:** `INVESTIGACION.md` y `ALCANCE.md` de `backlog` (si faltan,
  copiarlos de `$REF`), para saber que fuentes se visitaron, cuales dieron
  algo y que ideas ya existen; `CLAUDE.md` y `docs/formato-rec.md`, para
  saber que datos hay; las fichas en `main` y en papel, y los PRs abiertos,
  para no traer lo que ya existe.
- **Fuentes**, por familias. Cada turno toma 3 o 4, primero las que llevan
  mas tiempo sin visitarse y las que dieron senal la ultima vez; ninguna se
  repite dos turnos seguidos:
  1. **Parsers abiertos del `.rec`**: primero r6-dissect, del que
     `pydissect/` es un port (README, "Creditos"), con sus commits, releases
     e issues desde la ultima visita; despues sus forks y otros parsers.
     Campos que alguien decodifico y `pydissect/` todavia no lee. Es la
     fuente que mas agranda el alcance, porque trae datos nuevos.
  2. **Herramientas de replay de Siege** (las de la tabla de competidores
     del roadmap y las que aparezcan): que muestran, que piden sus usuarios.
  3. **Trackers de API** (stats.cc, R6 Tracker): solo su descripcion
     publica, resenas y lo que se dice de ellos. Si una pagina responde 403,
     se usa la busqueda y se sigue; nunca se intenta pasar la proteccion.
  4. **Herramientas de otros juegos tacticos** (CS2: Leetify, Scope.gg,
     CS Demo Manager; Valorant: Blitz, tracker.gg; MOBAs: OP.GG, Dotabuff):
     metricas y pantallas que se traducen a Siege.
  5. **Comunidad** (r/Rainbow6, r/R6ProLeague, Siege.GG, contenido de
     coaching): lo que los jugadores dicen que quieren ver de sus partidas.
  6. **Ubisoft**: notas de parche y temporada (operadores, mapas, modos y
     cambios del sistema de replays que van a llegar al parser).
  7. **Analitica de esports y deporte**: ratings compuestos, probabilidad de
     ganar la ronda segun la ventaja numerica, redes de trade, rating de
     clutch.
- **Trabajo:** un subagente por familia, en paralelo, cada uno con la lista de ideas que ya
  existen y la de lo que el `.rec` no trae, que devuelve hasta 5 candidatos
  con link verificado, fecha y una linea de que hace. Despues el lider
  filtra cada candidato, en este orden:
  (a) **dato**: que campo de `pydissect/` o de `models.py` lo alimenta,
  con archivo; si no existe pero un parser abierto lo decodifica, entra
  como idea de la epica `datos-nuevos-del-parser` con el link al hallazgo y
  la nota "verificar con `.rec` reales en el PC"; si nadie lo tiene, va a
  "Ideas descartadas" con el motivo.
  (b) **reglas duras** de `CLAUDE.md`.
  (c) **duplicado** contra `main`, `ALCANCE.md` y los PRs abiertos.
  Lo que pasa entra a `ALCANCE.md`: en la epica que corresponda, o en una
  nueva si no encaja, con `[fuente](url)` en la celda de la idea. De otros
  proyectos se traen ideas, no codigo. La excepcion es r6-dissect (MIT): su
  logica se porta igual que el resto de `pydissect/`, con el commit de
  origen anotado en la idea y el credito del README al dia. Por ultimo, la
  entrada del turno en `INVESTIGACION.md`, la mas nueva arriba: fecha,
  familias visitadas, que dio senal, que salio seco, ideas agregadas (con su
  `id`), descartadas y por que. Se actualiza la tabla de fuentes. El archivo
  se mantiene bajo unos 10.000 caracteres condensando las entradas viejas.
  Sin candado: no hay ficha que candar, y un push rechazado sigue la receta
  unica de `backlog` (en `ALCANCE.md` e `INVESTIGACION.md` se conservan las
  filas y entradas de los dos lados).
- **Sin red** (la sesion no tiene busqueda web o el proxy la corta): el
  turno no se pierde. Hace la investigacion interna: datos que el parser
  extrae y ninguna pantalla muestra, ramas `mercado/*` y PRs cerrados sin
  mergear, y las ideas van igual a `ALCANCE.md`. Se anota "sin red" en
  `INVESTIGACION.md`, y una sola vez en `## Para el humano` de `ESTADO.md`,
  con la configuracion de red del entorno como causa probable.
- **Prioridades:** P1, P2 y P3 como cualquier rol. P4 a P7 no le tocan:
  nunca implementa, revisa ni prueba.
- **Salida:** commits `Investiga: <familias>` en `backlog`, solo
  `docs/backlog/ALCANCE.md` y `docs/backlog/INVESTIGACION.md` (mas
  `ESTADO.md` al cerrar). Nunca fichas: priorizar es del PO. Nunca PR,
  nunca rama de trabajo, nunca codigo.
- **Turno bien hecho:** al menos 3 ideas nuevas en `ALCANCE.md` que pasan
  los tres filtros, cada una con su fuente real; el PO siguiente (03:01
  UTC) puede convertir cualquiera en ficha sin volver a buscar.
- **No hace:** inventar links, versiones ni numeros (si no pudo abrir la
  fuente, la idea no entra); hacer que la app consulte esas fuentes (la
  investigacion es del equipo, no de la app); scraping ni nada que esquive
  una proteccion.
- **Sin trabajo:** no existe; siempre hay una familia sin visitar.

## Cierre comun (todos los roles, 5 minutos)

1. `candado: -` en toda ficha que el turno haya candado, con su estado final,
   y push.
2. Regenerar `docs/backlog/ESTADO.md` entero en la rama `backlog` a partir
   de `estado.sh`. Push rechazado: `git fetch`, `git reset --hard
   origin/claude/equipo-dev/backlog`, regenerar, push, hasta 3 veces.
   `## Para el equipo` se copia tal cual de origin.
3. Informe final, que tiene que entenderse solo:

```
## Iteracion equipo-dev <fecha UTC>

**Turno:** <rol> (franja N | pedido | por cola vacia | relevo de <rol>)
**Playbook:** <ref>@<sha corto>
**Entregado:** <ficha NN: estado anterior -> nuevo, rama> | mergeado a main: <PR #n, ficha NN> | nada, porque <motivo>
**Mantenimiento:** <P2/P3/P4 atendidos> | nada pendiente
**Cola:** COLA=<n>/4 TOTAL=<n>/6 | papel: <n> propuesto, <n> disenado (<n> funcionalidad)
**Alcance:** <funcionalidades a main en 7 dias, epica en curso> | nada nuevo, porque <cuello de botella>
**GitHub:** con herramientas (<PRs tocados>) | sin herramientas
**Descartado esta vez:** <ficha o idea> porque <filtro> | nada
**Para el humano:** <decision, pregunta o rama para mergear/borrar> | nada
**Verificacion:** check.sh en verde (<n> tests backend, <n> frontend, build ok) | sin pushes de codigo
```

## Transicion

- Mientras este playbook no este en `main`, `$REF` apunta a la rama donde
  vive y `ESTADO.md` e informe lo dicen en `playbook:`. El PR del playbook
  (#11) lo mergea el humano: toca las reglas del equipo.
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
  mergear.
- Saltar, desactivar o borrar un test. Empujar codigo con `check.sh` en rojo.
- Agregar dependencias, servicios externos, cuentas, telemetria, red.
  Cualquier forma de overlay in-game.
- Subir `.rec`, `.sqlite3` o `.env`. Tocar `docs/roadmap.md`, `mercado/*`,
  `claude/loop-*` ni las ramas del humano.
- Hacer mas de una de estas etapas sobre la misma ficha en la misma sesion:
  implementar, revisar, probar.
