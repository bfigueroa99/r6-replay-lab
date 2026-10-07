---
name: equipo-dev
description: Una iteracion del equipo de desarrollo autonomo de r6-replay-lab. Corre cada 3 horas en una sesion cloud nueva y cada iteracion la lidera un rol distinto (release, po, arquitecto, dev, revisor, qa) segun la franja horaria UTC. Usar cuando la rutina lo pida o con /equipo-dev [rol].
---

# Equipo de desarrollo: una iteracion, un rol

Seis roles se turnan: **release manager, product owner, arquitecto, dev,
revisor y QA**. Cada sesion es un turno de un solo rol; el trabajo pasa de un
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
6. **No inventar trabajo.** Si no hay nada con valor para quien usa la app,
   el turno termina y lo dice.

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
| 7 | 21:01 | 18:01 | Revisor |

Nemotecnica: el dia UTC arranca entregando, despues propone, disena,
implementa, revisa, implementa, prueba, revisa. Un item disenado a las 06:01
puede ser un PR listo a las 00:01 del dia siguiente, cuando el humano esta
sentado en Santiago.

Excepciones: un rol pedido explicitamente (`rol: revisor` en el prompt, o
`/equipo-dev revisor`) gana al reloj; es la forma de disparo manual con
intencion. Las prioridades de abajo se atienden antes del turno pero no
cambian el rol anotado, salvo P6 y P7, que lo dicen.

Por que es robusta: cero estado compartido para decidir; cada rol es
"avanzar las fichas que esten en el estado X", asi que un disparo perdido no
deja deuda y dos disparos en la misma franja se reparten por candado; dev y
revisor corren dos veces por dia y QA y revisor se cubren entre si.

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
- **P5. Cola llena** (`COLA >= 3` o `TOTAL >= 5`): nadie abre ramas de
  trabajo. Dev solo atiende `con hallazgos` y huerfanas (fichas `en curso`
  con candado muerto o con `## Pendiente`). Los demas siguen
  con su turno: ninguno convierte papel en codigo.
- **P6. Cola vacia** (`COLA == 0`) y hay `disenado` tomable: Revisor, QA y
  Release actuan como Dev ese turno y lo anotan `turnos: dev <sesion> (por
  cola vacia)`. PO y Arquitecto no, para que nunca falte papel.
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
- **P9. Reloj.** 90 minutos de turno. Antes de cada `check.sh`, cada
  subagente y cada fase nueva: `source "$(git rev-parse --git-dir)/equipo-dev.env"
  && echo "minuto $(( ($(date -u +%s) - EQUIPO_INICIO) / 60 )) de 90, cierre a las
  $EQUIPO_CIERRE UTC"`. Pasado el minuto 75 (o la hora de cierre, si el archivo
  se perdio: compararla con `date -u +%H:%M`), se cierra con lo que esta verde: push,
  `## Pendiente` con lo que falta, `candado: -`, `ESTADO.md`. Nunca se
  empuja con `check.sh` en rojo, tampoco docs sobre una rama cuyo codigo
  quedo roto.
- **P10. Decision de producto del humano**: no se adivina. Va a `## Para el
  humano` de la ficha y a `ESTADO.md`; la ficha se queda donde estaba.

## Fichas

Formato fijo en `docs/backlog/PLANTILLA.md` (leerla siempre de `$REF`).
Cabecera legible con `grep`: `estado:`, `candado:`, `rama:`, `area:`,
`prioridad:`, `fuente:`, `archivos:`, `turnos:`. `turnos:` es una sola linea
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
   `PLANTILLA.md` y `ESTADO.plantilla.md` desde `$REF` si no estan, escribir
   `ESTADO.md`, commit `Crea la rama backlog`, push). Sin ella no hay donde
   anotar hallazgos ni tablero, asi que no se posterga. Solo admite
   archivos dentro de `docs/backlog/`. Ahi viven `propuesto`, `disenado`, `descartado`,
   `ESTADO.md`, `PAUSA` y `SIN_MERGE`, mas el espejo `en curso` de las fichas
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
merge); papel (`propuesto`, `disenado`, `descartado` de los ultimos 30 dias);
ultimo turno de cada rol; `## Para el humano` (preguntas acumuladas, ramas
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

- **COLA (tope 3)**: ramas de trabajo (y ramas del playbook anterior con
  codigo) con algun commit en los ultimos 14 dias o con ficha `entregado`
  aunque esten quietas (un PR que espera al humano
  ocupa su tiempo de revision). Con herramientas se suman los PRs abiertos
  `[equipo-dev]` en otras ramas.
- **TOTAL (tope 5)**: todas las ramas de trabajo no mergeadas, con o sin
  actividad, mas las ramas viejas sin ficha.
- **No cuentan**: `backlog` y todo lo que haya en ella; ramas mergeadas
  efectivamente aunque sigan existiendo (merge commit, squash o rebase:
  `estado.sh` las marca borrables); fichas `descartado`; la rama del
  playbook; `mercado/*`, `loop/*`, `claude/loop-*` y las ramas del humano.
- **Papel, tope propio**: 4 fichas en `propuesto` (lo mira el PO) y 2 en
  `disenado` (lo mira el Arquitecto).
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
    `docs/backlog/ESTADO.plantilla.md`, `frontend/electron/`,
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
  las ramas que sigan abiertas y lista de ramas borrables.
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

- **Entrada:** `origin/main` fresco: `CLAUDE.md`, las notas de pendientes y deuda que dejan los items hechos del roadmap (al
  final de cada item, con nombres como "Pendiente", "Lo que falta" o "Deuda";
  hoy:
  nemesis por rondas enfrentadas del #3, boton de backup en Datos del #16,
  `REPLAY_DIR` desde la UI del #19), `README.md` contra lo que el codigo
  hace, `docs/formato-rec.md`; las fichas de `backlog` y de las ramas de
  trabajo; `## Para el equipo`; como ideas y nada mas, `mercado/*` y
  `claude/loop-*`.
- **Trabajo:** reconciliar primero: quitar de `backlog` las fichas que ya
  estan en `origin/main` y poner `en curso` + `rama:` a las que ya viven en
  una rama de trabajo. Las `descartado` no se borran: son historia y
  reservan su numero. Despues, si
  hay menos de 4 `propuesto`: hasta 2 fichas nuevas desde `PLANTILLA.md`,
  numero siguiente libre, "Que gana quien usa la app" en dos frases, 3 a 6
  criterios de aceptacion convertibles en test o `curl`, "Fuera de alcance",
  `area`, `prioridad`, `fuente` concreta. Fuentes, en orden: deuda anotada
  en el roadmap; bugs reales; huecos de tests en `analytics/`, `pydissect/`
  y `logica.test.js`; robustez del parser ante temporadas nuevas; UX chica y
  verificable. Filtros duros de `CLAUDE.md` antes de escribir. Lo grande se
  parte antes de proponerlo. Una decision de producto del humano va a
  `## Para el humano`, no se propone como item. Items que solo se verifican
  en Windows (Electron, `.ps1`, instalador) llevan la nota "verificado solo
  en nube" en los criterios.
- **Salida:** push a `claude/equipo-dev/backlog`, solo `docs/backlog/*.md`,
  commit `Propone: NN titulo`. Nunca PR, nunca rama de trabajo, nunca codigo.
- **Turno bien hecho:** cada ficha nueva la puede disenar un Arquitecto sin
  preguntar nada, y el humano entiende en 30 segundos que gana.
- **Sin trabajo:** con 4 o mas `propuesto`, solo grooming (afinar criterios,
  reordenar prioridades, descartar lo que main ya cubre). Sin nada real que
  proponer: `Entregado: nada, sin trabajo con valor para el usuario`.

### Arquitecto (franja 2)

- **Entrada:** fichas `propuesto` en `backlog`, mayor prioridad y mas vieja
  primero, hasta 2 por turno; `git diff --name-only origin/main...<rama>` de
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
  bloquea). Si no cabe en un turno de Dev (~300 lineas, 90 min), partir: el
  diseno cubre la primera mitad util y la segunda queda como ficha
  `propuesto`. Spikes en el scratchpad, nunca codigo commiteado.
  `estado: disenado`, `candado: -`.
- **Salida:** commits `Disena: NN titulo` en `backlog`. Nunca PR, nunca codigo.
- **Turno bien hecho:** un Dev en sesion nueva implementa el diseno sin tomar
  ninguna decision de alcance.
- **Sin trabajo:** con 2 `disenado` esperando, no disena mas: revalida esos
  disenos contra el main actual y anota los ajustes. Sin nada, informe.

### Dev (franjas 3 y 5)

- **Entrada:** `estado.sh`. Orden de eleccion, sin discusion: (0) ficha
  `en curso` con candado muerto (mas de 3 h sin commits) o con
  `## Pendiente`: se continua; (1) `con hallazgos` mas vieja; (2) si
  `COLA < 3` y `TOTAL < 5`, `disenado` mas vieja cuyo diseno no diga
  "implementar despues de #NN" con NN sin mergear. Candado `dev` ajeno de
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
- **A los 75 minutos sin terminar:** push de lo que esta verde,
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
  Sin nada, informe.

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
**Cola:** COLA=<n>/3 TOTAL=<n>/5 | papel: <n> propuesto, <n> disenado
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
