# Rol: Dev

Parte del playbook del equipo. Lo comun a todos los roles (principios,
arranque, turnos, prioridades, fichas, cierre) esta en
`.claude/skills/equipo-dev/SKILL.md`; este archivo es solo la especificacion
de este rol. Se lee de `$EQUIPO_REF` con `git show`, nunca del checkout.

Cuando el estado lo pide (reglas 4, 5 y 10); por reloj, franjas 3 y 5.

- **Entrada:** `estado.sh`. Orden de eleccion, sin discusion: (0) ficha
  `en curso` con candado muerto (mas de 3 h sin commits) o con
  `## Pendiente`: se continua; (1) `con hallazgos` mas vieja; (1b) un bug
  de prioridad 1 del papel (`bug_p1` en `RESUMEN`; regla 5 de Turnos),
  aunque la cola este llena por uno: si esta `propuesto`, el Dev le escribe
  un diseno de 5 lineas en la misma ficha antes de reclamarla; (2) si
  `COLA < 4` y `TOTAL < 6`, `disenado` de mayor prioridad (a igual
  prioridad, `funcionalidad` antes que el resto, y la mas vieja) cuyo diseno
  no diga "implementar despues de #NN" con NN sin mergear. Candado `dev` ajeno de
  menos de 3 h sobre la ficha o sobre la misma zona del codigo: elegir otra.
  Encadenado, la sesion no implementa una ficha que reviso o probo
  (`puerta.sh <rama> --solo b` si la ficha ya tiene rama); implementar lo
  que la misma sesion diseno si se puede.
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
  independientes. Si el diseno deja abierto un punto con enfoques
  genuinamente distintos (un algoritmo, la decodificacion de un campo) y no
  lo decidio una arena del Arquitecto, ese punto se juega en una arena
  (`.claude/skills/equipo-dev/arena.md`): una por turno, `--agents 4`, el
  diff del ganador pasa por los mismos tests, `check.sh` y revision que
  cualquier cambio. Antes del ultimo push: subagente ciego con `revision.md`
  sobre `git diff origin/main...HEAD -- . ':(exclude)docs/backlog'` y corregir lo real (es el primer
  filtro, no el ultimo; el diff que se le pasa excluye `docs/backlog`, que
  es el plan). `mutar.py` sobre cada archivo de codigo que cambio, con el
  test mas chico que lo cubre: un `MUTANTE vivo` que no sea equivalente se
  mata con un test antes de entregar (el Revisor y QA lo van a correr
  igual). `check.sh` en `Todo en verde.`. `## Implementacion`: que quedo,
  que no, desvios del diseno, y la linea `MUTACION_...` de cada archivo.
  `estado: implementado`, `candado: -`, push.
- **Un bug, siempre en este orden** (ficha `tipo: bug`, propia o de QA):
  1. **Reproducir en main** con el repro de la ficha (comando exacto).
  2. **Test que falla primero:** el test con nombre que describe el caso
     (`test_un_playerid_que_no_es_numero_no_tumba_la_partida`), corrido sobre
     main sin el arreglo; su salida en rojo va a `## Implementacion`.
  3. **Arreglo minimo** en el lugar del error, no un `try` alrededor de todo.
  4. **Prueba de que el test sirve:** `mutar.py --lineas` sobre las lineas
     del arreglo (o revertirlo a mano): el test nuevo tiene que caer.
  5. Si el bug cambio numeros guardados, `recompute` en el diseno y
     `## Verificar en el PC` con el comando, como la ficha 34.
- **Llegada la hora de cierre sin terminar (P9):** push de lo que esta verde,
  `## Pendiente` con lo que falta y donde se trabo, `estado: en curso`,
  `candado: -`. No se tira trabajo parcial verde.
- **Salida:** rama de trabajo nueva o pushes a la existente; commits en
  presente (`Agrega ...`, `Corrige ...`). Nunca abre el PR.
- **Turno bien hecho:** cada criterio de aceptacion tiene un test con nombre;
  el Revisor puede trabajar sin preguntar nada.
- **Sin trabajo:** sin nada tomable y con lugar en la cola, **caza de
  bugs**, en este orden de fuentes: (a) los `HALLAZGO` de la ultima pasada
  de QA que todavia no son ficha; (b) `fuzz_parser.py --casos 3000` y
  `barrido_api.py` sobre main; (c) leer los casos borde del parser
  (`header.py`, `events.py`, `stats.py`: cada `int(...)` sin `try`, cada
  indice sin guarda, cada `split` que asume un formato) y de `aggregates.py`
  (divisiones por cero con 0 rondas, filtros que se cruzan); (d) con
  herramientas de GitHub, issues abiertos del repo. Lo que reproduce va con
  ficha propia escrita en el momento (severidad, repro, criterios, diseno
  de 5 lineas) y sigue "Un bug, siempre en este orden" hasta
  `implementado`. Solo bugs, nunca features, nunca Electron ni `.ps1`. Cola
  llena o solo cosmetica: `Entregado: nada, <motivo>`.

