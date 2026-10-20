# Arena en el equipo: elegir entre enfoques que compiten

Como corre la skill arena (`.claude/skills/arena/`, MIT, de
https://github.com/Jakeschincariol/arena-skill, commit df07b8e) dentro del
loop. Es un torneo de eliminacion simple: N subagentes resuelven la misma
tarea con una carta de estrategia distinta, se atacan, se defienden y un juez
puntua cada match con `rubric.md` hasta que queda una solucion. Los
competidores nunca editan el proyecto: escriben solo en `.arena/` (ignorado
por git) y el ganador vuelve como diff o archivos completos dentro de su
solucion.

Es la skill del repo, no otra con el mismo nombre que la sesion pueda
ofrecer. Lleva `disable-model-invocation: true`, asi que no se activa con la
herramienta Skill: el rol lee `.claude/skills/arena/SKILL.md` por su ruta y
la sigue con las reglas de este archivo, que mandan sobre lo que diga ella.
`${CLAUDE_SKILL_DIR}` y `$ARGUMENTS` solo se expanden al invocarla como
skill: donde la skill dice `ARENA`, el loop escribe siempre, desde la raiz
del checkout donde corre la arena,

```bash
python3 .claude/skills/arena/bracket.py <comando>
```

## Quien la usa y cuando

Como maximo **una arena por turno**, y solo con 60 minutos o mas antes de
`EQUIPO_CIERRE` (P9): son 7 tandas de subagentes con `--agents 4`. Si el
cierre llega a mitad de camino, se abandona (`.arena/` no se commitea) y el
rol decide solo, como siempre.

- **Arquitecto**: cuando la ficha que disena admite dos o mas disenos
  genuinamente distintos y la eleccion importa. Por ejemplo: calcular al
  importar (`metrics.py`, columna y migracion) o al consultar
  (`aggregates.py`); en que pagina o endpoint vive; un algoritmo o umbral con
  alternativas reales. El ganador es la base del `## Diseno`.
- **Dev**: cuando el diseno deja abierto un punto de la implementacion con
  enfoques genuinamente distintos (un algoritmo, la decodificacion de un
  campo del parser) y no lo decidio ya una arena del Arquitecto. La arena es
  sobre ese punto, no sobre la ficha entera.
- **No aplica** cuando hay una sola forma obvia, que es lo comun: una
  columna o un agregado que sigue un patron que el repo ya tiene, un arreglo
  con causa clara, tests. Tampoco en PO, Investigador, Revisor, QA ni
  Release: priorizan, buscan afuera o juzgan, y una arena no reemplaza un
  juicio independiente.

## Tamano

Nunca el default de 100 ni `--quick` (16 competidores, 91 llamadas).
`--agents 4` por defecto (2 rondas, 19 llamadas de subagente) y
`--agents 8` como tope (3 rondas, 43 llamadas), solo para una decision
grande: ficha de tamano L, primer tramo de una epica o cambio de modelo con
migracion, y con 90 minutos o mas por delante. Siempre `plan` antes de
`init`. Sin `--seed`: `init` elige uno, lo imprime y queda en `arena.json`
y en el nombre de la carpeta del run.

## Donde corre

- **Dev**: en su propio checkout, la rama de trabajo, que sale de
  `origin/main` y trae la skill y el `.gitignore` con `.arena/`. Si la rama es
  anterior a la skill (no existe `.claude/skills/arena/`), no hay arena.
- **Arquitecto**: en un worktree de `$EQUIPO_REF`, el codigo contra el que
  disena, nunca en el checkout de `backlog`, que no trae la skill ni ignora
  `.arena/`:

```bash
source "$(git rev-parse --git-dir)/equipo-dev.env"
A="$(dirname "$(git rev-parse --path-format=absolute --git-common-dir)")-arena"
git worktree remove --force "$A" 2>/dev/null; git worktree add --detach "$A" "$EQUIPO_REF"
cd "$A" && python3 .claude/skills/arena/bracket.py plan --agents 4
```

`$A` es el mismo desde el checkout principal y desde el worktree. Cada
comando empieza con `cd "$A"` (las variables no sobreviven entre comandos).
Al terminar: `git worktree remove --force "$A"`.

## La arena, paso a paso

Se sigue `.claude/skills/arena/SKILL.md` con estos cambios:

1. **Paso 1 (tamano y pedir un si)**: no se pregunta. Las reglas del loop son
   la autorizacion. `python3 .claude/skills/arena/bracket.py plan --agents 4`
   (u 8 segun Tamano) y se sigue.
2. **Paso 2 (la tarea)**: el rol escribe `.arena/task.md` solo, desde la
   ficha, sin pistas de solucion y sin su propia opinion de cual es el mejor
   enfoque (eso empuja a todos para el mismo lado). Lleva:
   - El pedido: que gana quien usa la app, los criterios de aceptacion y el
     fuera de alcance de la ficha, tal cual. Para el Dev, ademas, el
     `## Diseno` y el punto abierto que se juega.
   - Que entregar. Arquitecto: un `## Diseno` con el formato del playbook
     (archivos exactos y por que, tests con nombre en espanol, orden de
     implementacion, que puede romperse, verificacion manual, fila de
     `docs/metricas.md` si hay numero nuevo). Dev: un diff unificado contra
     el commit actual (`git rev-parse HEAD`) o los archivos completos, con
     sus tests.
   - Contexto con rutas absolutas: `CLAUDE.md`, `docs/formato-rec.md`, los
     archivos que la ficha nombra y los vecinos que muestran como el repo ya
     resuelve lo parecido.
   - Las reglas duras de `CLAUDE.md`, copiadas: `pydissect/` y `externo/` no
     importan Django; sin dependencias nuevas (el backend tiene `django` y
     `zstandard`; nada de DRF, pandas ni requests); nada sale a la red sin un
     clic y ningun test sale a internet; sin scraping de stats.cc ni R6
     Tracker; la API es de lectura, vistas planas con `JsonResponse`, sin
     serializers ni viewsets; la configuracion vive en el `.env`; las
     metricas se calculan al importar (`metrics.py`) y `aggregates.py` solo
     agrega; todo numero de la UI tiene fila en `docs/metricas.md`; nada que
     dependa de lo que el `.rec` no entrega; overlay in-game, cuentas,
     telemetria y nube estan fuera; codigo y comentarios en espanol sin
     tildes, la UI con tildes; cada funcionalidad llega con tests y una
     pagina nueva entra al e2e (`frontend/e2e/`).
   Sin `baseline.md`: no hay respuesta rechazada que vencer, asi que tampoco
   hay chequeo final.
3. **Pasos 3 y 4**: tal cual (`init --agents N --task-file .arena/task.md`,
   despues `next`, tandas de subagentes, `collect`, `advance`). Sin lineas
   de avance para nadie: no hay quien las lea. No se leen soluciones,
   ataques ni veredictos durante la arena.
4. **Paso 5 (el resultado)**: no se pregunta si aplicar. `winner`, y se lee
   solo la solucion del campeon. El Arquitecto la vuelve el `## Diseno` (la
   revisa contra los filtros duros; si rompe uno, se descarta y disena
   solo). El Dev aplica el diff y lo pasa por lo mismo que cualquier cambio:
   tests, `check.sh` en `Todo en verde.` (suite, build y e2e) y la revision
   ciega con `revision.md`. Un ganador que no aplica o no queda en verde no
   se empuja: el Dev sigue solo.
5. **Registro**, en `## Diseno` o `## Implementacion` de la ficha y en
   `**Entregado:**` del informe, una linea:
   `Arena: N=<n>, seed <s>, <r> rondas (<n> -> ... -> 1), ganador <id>, carta <razonamiento + flujo + estrategia>, final <puntaje>-<puntaje>`.
   La carta y los puntajes salen de `winner`.
