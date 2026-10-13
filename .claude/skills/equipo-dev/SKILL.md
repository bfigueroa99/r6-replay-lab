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
`EQUIPO_ROLES` (los roles de esta sesion, si encadeno), `EQUIPO_FRANJA`,
`EQUIPO_MOTIVO` (por que ese rol), `EQUIPO_RELOJ` (el rol que decia el
reloj), `EQUIPO_INICIO` (epoch), `EQUIPO_SESION` (id del turno, formato
`AAAAMMDDTHHMMZ`, va en `turnos:` y en `ESTADO.md`), `EQUIPO_CIERRE` (hora UTC
`HH:MM` a la que hay que cerrar) y `EQUIPO_CIERRE_EPOCH`, `EQUIPO_MINUTOS` y
`EQUIPO_REF`, lo imprime entero y resume todo en una linea `# turno:`, mas
`# leer:` con el archivo de rol. Tambien escribe la linea de arranque en
`PULSO.md` de la rama `backlog` (`# pulso: PULSO_OK <sha>`); si falla, el
motivo queda en esa linea y el turno sigue igual. **Las variables no sobreviven entre
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
5. `dev` si hay un bug de prioridad 1 en el papel (`bug_p1`, ver Severidad)
   y `COLA <= 4`: un numero mal o una importacion que se cae salta al papel
   nuevo y puede pasar la cola por uno, como el hotfix de P4.
6. `release` si hay `entregado (...)` (espera al humano) y el reloj dice
   release, motivo `reloj: release, N en espera`: lo que quedo `pendiente
   de merge` por un motivo transitorio (sin herramientas, veto levantado,
   pregunta respondida, entorno incompleto) se reintenta una vez por dia.
7. `investigador` si el reloj dice investigador (franja 7, dia par).
8. `po` si el papel esta vacio (0 `propuesto` y 0 `disenado`).
9. `po` si el papel no tiene ninguna funcionalidad (`papel_func=0`) y
   `ALCANCE.md` tiene ideas libres: un papel solo de tests y deuda se
   rellena antes de que el Dev lo convierta en codigo (Directiva de alcance).
10. `dev` si hay `disenado` y lugar en la cola (`COLA < 4` y `TOTAL < 6`).
11. `arquitecto` si hay `propuesto` y menos de 3 `disenado`.
12. `po` si hay menos de 6 `propuesto`.
13. `investigador` si `ALCANCE.md` tiene menos de 10 ideas libres.
14. El rol del reloj (tabla de abajo), motivo `nada tomable: reloj`.

Un rol pedido (`rol: revisor` en el disparo, o `/equipo-dev revisor`) gana a
todo, motivo `pedido`. Sin linea `RESUMEN` (fetch caido), rol del reloj,
motivo `sin resumen: reloj`. `EQUIPO_MOTIVO` y `EQUIPO_RELOJ` quedan en el
env y en `ESTADO.md`.

### Encadenar: usar el turno entero

Medido del 2026-10-08 al 2026-10-13: 33 turnos con rastro cerraron en
promedio a los 5 minutos de arrancar (el mas largo, 14) sobre un presupuesto
de 135, y ninguna funcionalidad llego a `main`. Por eso, **cuando el trabajo
del rol termino y quedan 40 minutos o mas**, el turno no se cierra: pide el
siguiente rol con

```bash
git show "$EQUIPO_REF:scripts/equipo-dev/turno.sh" | bash -s -- --encadenar
```

que vuelve a aplicar la lista de arriba con el `RESUMEN` del momento, pero
contado **sin las fichas en las que esta sesion ya firmo una etapa que le
impide la siguiente** (no revisa lo que implemento, no prueba lo que reviso
o implemento, no implementa lo que reviso o probo, no mergea nada en lo que
firmo, no disena lo que propuso). Asi la independencia (principio 4) sigue
intacta: lo que encadena es otro trabajo, no otra etapa del mismo. Mantiene
sesion, inicio y hora de cierre; escribe el rol nuevo y `EQUIPO_ROLES` en el
env; imprime `ENCADENAR=si rol=<rol>` y la linea `# leer:` con el archivo de
rol a leer (`roles/<rol>.md`), o `ENCADENAR=no motivo=<...>` y el turno va al
cierre. No encadena: un rol pedido, un rol que la sesion ya hizo, mas de 3
roles por sesion (`max_roles_por_turno` en `turno.sh`, la perilla de costo:
en 1 apaga el encadenado) ni el rol del reloj por "nada tomable". Cada rol
encadenado anota su par en `turnos:` de la ficha que toca, con la misma
sesion, y el cierre comun se hace una sola vez al final con todos los roles.

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
estado; y `PULSO.md` deja en git si un disparo se perdio o la sesion murio.

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
- **P6. Cola vacia.** Cubierto por el orden de `turno.sh` (regla 10). Vale
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
  quedo roto. Un rol encadenado hereda la misma hora de cierre.
- **P10. Decision de producto del humano que no se puede deshacer** (borra o
  reescribe datos del usuario, cambia la definicion de una metrica que ya se
  muestra, toca una regla dura de `CLAUDE.md`): no se adivina. Va a `## Para
  el humano` de la ficha y, una sola vez, a los pedidos de `ESTADO.md`
  (`pulso.sh cierre --humano`, ver Fichas); la ficha se queda donde estaba. El
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

**`ESTADO.md`**, el tablero, en la rama `backlog`, **lo genera
`estado.sh --tablero`** y lo escribe `pulso.sh cierre` (Cierre comun); nadie
lo arma a mano. Trae la cabecera (`actualizado:` con roles y sesion,
`playbook:`, `rutina:` con `TURNOS_SIN_RASTRO` y `PULSO`, `pausa:`,
`sin_merge:`), la cola con links de compare y commits humanos, `COLA`,
`RESUMEN`, el orden de merge por merge de prueba de a pares, `## Alcance`,
el papel, `## Salud del loop`, el ultimo turno de cada rol y `## Para el
humano`: primero los avisos automaticos (ramas borrables en **un** comando,
lo que espera su merge, la Routine, el cuello de botella si no llego ninguna
funcionalidad), despues `### Pedidos abiertos`, uno por decision con id
estable (`H<n>`, desde que fecha), `### Maquinaria propuesta por el equipo` y
`### Resueltos (ultimos 7 dias)`. `## Para el equipo` es del humano: se copia
byte por byte y `pulso.sh` no escribe un tablero que no lo conserve. La
plantilla comentada esta en `docs/backlog/ESTADO.plantilla.md`.

**Pedidos al humano.** Una decision que solo el humano puede tomar (P10,
calibrar con su base, verificar en el PC) se anota **una vez** con `pulso.sh
cierre --humano "<pedido en una frase, con la ficha>"` y queda como `H<n>`
hasta que alguien la cierra con `--cerrar H<n> "<como se resolvio>"` (el
humano contesta en `## Para el equipo` citando el id). No se repite en cada
turno con otras palabras ni se copia a la ficha mas que como `ver H<n>`: el
historial mostro las mismas cinco preguntas reescritas en cada `ESTADO.md`
durante dias. `estado.sh` marca `SALUD_PEDIDO_VIEJO` las que pasan 3 dias.

**Antes de empujar una ficha** (PO, Arquitecto, cualquier rol que la
avanza): `git show $EQUIPO_REF:scripts/equipo-dev/fichas.sh | bash -s --
docs/backlog/NN-slug.md` en `FICHAS_OK`. Un estado fuera del vocabulario
desaparece del pipeline sin aviso: `estado.sh` cuenta por prefijo.

## Limite de trabajo en curso

Rama de trabajo del equipo = rama `origin/claude/*` no mergeada
efectivamente que agrega una ficha `docs/backlog/NN-*.md`, salvo `backlog`.
La identidad es la ficha, no el nombre de la rama. El limite existe para que
el pipeline no se llene de codigo a medio verificar y para que lo que espera
al humano siga siendo poco.

- **COLA (tope 4)**: ramas de trabajo (y ramas del playbook anterior con
  codigo) con algun commit en los ultimos 14 dias o con ficha `entregado`
  aunque esten quietas. Las `entregado (PR pendiente de merge: ...)`, que
  esperan al humano, ocupan **entre todas un solo lugar**: si no, unos PRs
  esperando su merge frenan al Dev aunque el equipo no tenga nada a medio
  verificar (`estado.sh` lo dice en `ESPERA_HUMANO`). Con herramientas se
  suman los PRs abiertos `[equipo-dev]` en otras ramas.
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

## Herramientas del equipo

Todas viven en `scripts/equipo-dev/` y se corren desde `$EQUIPO_REF`, nunca
del checkout (una rama vieja trae una version vieja): los `.sh` con
`git show "$EQUIPO_REF:scripts/equipo-dev/X.sh" | bash -s -- <args>`, los
`.py` con `git show "$EQUIPO_REF:scripts/equipo-dev/X.py" | python3 - <args>`
y los `.mjs` guardandolos en el scratchpad y corriendolos con `node` desde
la raiz del repo. Lo que miden es el checkout (la rama bajo prueba).

| herramienta | para que | quien |
|---|---|---|
| `turno.sh` | elegir el rol; `--encadenar` para el siguiente | todos, al arrancar |
| `estado.sh` | papel, ramas, cola, rutina, salud; `--tablero` arma `ESTADO.md` | todos |
| `pulso.sh` | `arranque` (lo llama `turno.sh`) y `cierre` con el tablero | todos, al cerrar |
| `puerta.sh` | la puerta de merge a-f; `--solo b` antes de revisar o probar | Release, Revisor, QA |
| `fichas.sh` | lint de fichas y de `ALCANCE.md` (`--alcance`) | quien escribe o avanza una ficha |
| `pruebas.sh` | las pruebas del propio playbook | Release (paso 8) y sesiones del dueno |
| `qa.sh` | la bateria de QA en un comando: deriva, fichas, barrido, fuzz y paginas | QA en cada ficha y sin trabajo; Dev cazando bugs |
| `barrido_api.py` | todas las rutas de la API con parametros y cuerpos borde, base vacia y sembrada | QA, Dev |
| `fuzz_parser.py` | `.rec` sinteticos rotos y truncados contra el parser | QA si toca el parser, Dev cazando bugs |
| `qa-paginas.mjs` | todas las paginas en Chromium, escritorio y celular: consola, red, desborde, foco | QA |
| `mutar.py` | mutacion de las lineas que cambio la rama | Dev antes de entregar, Revisor, QA |
| `deriva-docs.sh` | lo que los docs citan contra el codigo (M9) | QA |
| `notas.sh` | notas de version desde las fichas que llegaron a main desde el ultimo tag (M7) | Release |
| `pre-push.sh` | guardia de ramas que `turno.sh` instala: solo `claude/equipo-dev/*` durante un turno (M11) | nadie lo corre a mano |

Cada herramienta de QA trae `--autoprueba`, que rompe a proposito lo que
dice detectar; `pruebas.sh` las corre todas.

## Severidad de bugs

Un bug encontrado por cualquier rol se clasifica antes de escribir la ficha,
y la severidad decide la prioridad:

| severidad | que es | prioridad | efecto |
|---|---|---|---|
| S1 | numero equivocado en una metrica que la UI muestra; importacion que se cae o pierde partidas; datos del usuario borrados o reescritos | 1 | regla 5 de Turnos: el proximo turno es Dev, aunque la cola este llena por uno |
| S2 | 500 o pagina rota con datos legitimos; `recompute` que no corrige; parser que tumba una partida entera por una ronda rara | 2 | antes que cualquier funcionalidad de igual tamano |
| S3 | 500 solo con parametros absurdos; texto o numero mal redondeado sin cambiar decisiones | 3 | compite con el resto del papel |
| S4 | cosmetico, friccion de uso | - | idea en `ALCANCE.md`, no ficha |

Una ficha `tipo: bug` lleva en `fuente:` el repro minimo exacto (comando,
input y salida, sobre que sha de main) y la severidad (`S1`..`S3`) en la
primera frase de "Que gana quien usa la app". Un bug no paga la cuota de la
Directiva de alcance.

## Salud del loop

El equipo se mira a si mismo con `estado.sh` (seccion `== salud`, y
`## Salud del loop` en el tablero), y cada turno la lee al arrancar:

- `SALUD_RUTINA`: disparos perdidos (sin arranque en `PULSO.md`) o sesiones
  que arrancaron y murieron sin cierre en 48 h. Lo que se puede hacer desde
  el repo es nada: va solo al tablero (la linea se actualiza sola, no se
  repite) y es del humano.
- `SALUD_ATASCADA`: una ficha mas de 48 h quieta en una etapa del equipo. El
  rol de esa etapa la toma primero en su proximo turno; si nadie puede
  (independencia), el Release lo dice en un pedido `H<n>`.
- `SALUD_PAPEL_VIEJO`: papel sin tocar en 7 dias. El PO lo afina, lo parte o
  lo descarta en su turno.
- `SALUD_ROL_OCIOSO`: un rol que cerro sin entregar 3 de sus ultimos 4
  turnos. La regla que lo elige esta mal calibrada: va como `--maquinaria`.
- `SALUD_PEDIDO_VIEJO`: un `H<n>` abierto hace 3 dias o mas. No se reescribe:
  se deja como esta (el humano ya lo ve) salvo que haya un dato nuevo.
- `SALUD_FICHAS_MAL`: `fichas.sh` encontro fichas mal escritas; la corrige
  el rol que la toque, o el PO en su reconciliacion.
- `SALUD_PLAYBOOK_TOCADO`: una rama del equipo cambia `.claude/` o
  `scripts/equipo-dev/`. El Revisor la devuelve a `con hallazgos`: el equipo
  no edita su maquinaria.
- `SALUD_BORRABLES`: cinco o mas ramas esperando que el humano las borre.

El equipo **propone** maquinaria y **nunca la implementa**: lo que haria el
loop mas autonomo o mas barato va con `pulso.sh cierre --maquinaria "<idea,
por que, con el numero que lo muestra>"` a `### Maquinaria propuesta por el
equipo`, y una sesion del dueno la pasa a `docs/backlog/MAQUINARIA.md`.

## Especificacion por rol

Cada rol tiene su archivo en `roles/`, y cada turno lee **solo el suyo**
(mas el de otro rol si cae en su fallback, por ejemplo QA que revisa):

```bash
source "$(git rev-parse --git-dir)/equipo-dev.env"
git show "$EQUIPO_REF:.claude/skills/equipo-dev/roles/$EQUIPO_ROL.md"
```

| rol | archivo | cuando |
|---|---|---|
| Release manager | `roles/release.md` | reglas 1 y 6; por reloj, franja 0 |
| Product owner | `roles/po.md` | reglas 8, 9 y 12; por reloj, franja 1 |
| Arquitecto | `roles/arquitecto.md` | regla 11; por reloj, franja 2 |
| Dev | `roles/dev.md` | reglas 4, 5 y 10; por reloj, franjas 3 y 5 |
| Revisor | `roles/revisor.md` | regla 3; por reloj, franja 4 y la 7 de los dias impares |
| QA | `roles/qa.md` | regla 2; por reloj, franja 6 |
| Investigador | `roles/investigador.md` | reglas 7 y 13; por reloj, la franja 7 de los dias pares |

## Cierre comun (todos los roles, 5 minutos)

1. `candado: -` en toda ficha que el turno haya candado, con su estado final,
   y push.
2. Si sobra tiempo, encadenar (ver Turnos) antes de cerrar; el cierre se
   hace una vez, al final de todos los roles.
3. Tablero y pulso, en un comando (no toca el checkout; reintenta solo):

   ```bash
   source "$(git rev-parse --git-dir)/equipo-dev.env"
   git show "$EQUIPO_REF:scripts/equipo-dev/pulso.sh" | bash -s -- cierre \
       --resultado entrego|nada|parcial --turno "<que hizo, una o dos frases con fichas y estados>" \
       [--humano "<pedido nuevo>"] [--cerrar H<n> "<como se resolvio>"] \
       [--maquinaria "<idea para el loop>"] [--rutina "<estado del prompt, solo Release>"]
   ```

   `CIERRE_OK <sha>` o `PULSO_FALLA: <motivo>`; con un fallo, el motivo va
   al informe y nada mas (no se arma `ESTADO.md` a mano). `--resultado
   nada` es honesto y sirve: tres de cuatro cierres `nada` de un rol son
   `SALUD_ROL_OCIOSO`, la senal para cambiar la regla que lo elige.
4. Informe final, que tiene que entenderse solo:

```
## Iteracion equipo-dev <fecha UTC>

**Turno:** <roles encadenados> (motivo: <EQUIPO_MOTIVO> | reloj: <EQUIPO_RELOJ>, franja N)
**Playbook:** <ref>@<sha corto>[ (pruebas: ok | FALLAN k)]
**Rutina:** <TURNOS_SIN_RASTRO y PULSO de estado.sh>[; prompt al dia | prompt sincronizado con rutina.md@<sha corto> | sin herramientas para comparar | apagada]
**Entregado:** <ficha NN: estado anterior -> nuevo, rama> | mergeado a main: <PR #n, ficha NN> | nada, porque <motivo>
**Mantenimiento:** <P2/P3/P4 atendidos> | nada pendiente
**Cola:** COLA=<n>/4 TOTAL=<n>/6 | papel: <n> propuesto, <n> disenado (<n> funcionalidad)
**Alcance:** <funcionalidades a main en 7 dias, epica en curso> | nada nuevo, porque <cuello de botella>
**Salud:** <lineas SALUD_ de estado.sh> | SALUD_OK
**GitHub:** con herramientas (<PRs tocados>) | sin herramientas
**Descartado esta vez:** <ficha o idea> porque <filtro> | nada
**Para el humano:** <H<n> nuevos o cerrados> | nada
**Verificacion:** check.sh en verde (<n> tests backend, <n> frontend, build ok) | sin pushes de codigo
**Cierre:** CIERRE_OK <sha> | PULSO_FALLA: <motivo>
```

Lo que va entre corchetes en `**Playbook:**` y `**Rutina:**` lo escribe solo
el Release (pasos 8 y 9 de `roles/release.md`).

## Transicion

- El playbook vive en `main` (#21). La cadena de `turno.sh` sigue probando
  `claude/equipo-dev/playbook` despues de `main` por si `main` lo pierde.
  Cambia solo por PR que mergea el humano, con `pruebas.sh` en `PRUEBAS_OK`;
  lo diferido de la maquinaria vive en `docs/backlog/MAQUINARIA.md`.
- Ramas del playbook anterior (reclamaban en `docs/roadmap.md` con un commit
  `Reclama:`; `estado.sh` las lista): con codigo, el primer Revisor (o QA en
  su fallback) les crea la ficha en `implementado` desde su entrada en el
  roadmap y su ultimo commit; con solo el reclamo, borrables. Los numeros 20
  a 29 del roadmap estan tomados: las fichas arrancan en 30.

## Lo que el equipo nunca hace

- Mergear fuera del turno de Release o sin pasar la puerta de merge. Aprobar
  PRs formalmente. Cerrar PRs. Empujar a `main` directo. Force-push. Rebase
  de ramas publicadas. Borrar ramas, salvo la que el Release acaba de
  mergear. Empujar a `claude/equipo-dev/playbook`. Saltar la guardia de
  ramas (`git push --no-verify`, borrar o editar `.git/hooks/pre-push`): un
  `PUSH_BLOQUEADO` se informa, no se esquiva.
- Saltar, desactivar o borrar un test. Empujar codigo con `check.sh` en rojo.
- Agregar dependencias, servicios externos, cuentas, telemetria, red.
  Cualquier forma de overlay in-game.
- Subir `.rec`, `.sqlite3` o `.env`. Tocar `docs/roadmap.md`, `mercado/*`,
  `claude/loop-*` ni las ramas del humano.
- Hacer mas de una de estas etapas sobre la misma ficha en la misma sesion:
  implementar, revisar, probar.
