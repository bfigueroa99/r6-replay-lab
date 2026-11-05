# Rol: Dev

Parte del playbook: `SKILL.md` (el nucleo comun) se lee antes y manda junto
con `CLAUDE.md`. La eleccion por `tipo:` y por epica sale de la Directiva de alcance
(`alcance.md`), resumida en el nucleo.

Cuando el estado lo pide (reglas 4 y 8); por reloj, franjas 3 y 5.

- **Entrada:** `estado.sh`. Orden de eleccion, sin discusion: (0) ficha
  `en curso` con candado muerto (mas de 3 h sin commits) o con
  `## Pendiente`: se continua; (1) `con hallazgos` mas vieja; (2) si
  `COLA < 4` y `TOTAL < 6`, `disenado` de mayor prioridad (a igual
  prioridad, `funcionalidad` antes que el resto, y la mas vieja) cuyo diseno
  no diga "implementar despues de #NN" con NN sin mergear. Candado `dev` ajeno de
  menos de 3 h sobre la ficha o sobre la misma zona del codigo: elegir otra.
- **Reclamo:** `git checkout -b claude/equipo-dev/NN-slug origin/dev` (el
  mismo nombre que la ficha); `mkdir -p docs/backlog`; copiar la ficha desde
  `backlog`; `estado: en curso <fecha>`, `candado: dev
  <fecha>`, `rama:`, `turnos:`; commit `Reclama: NN titulo`; `git push -u
  origin claude/equipo-dev/NN-slug`. Push rechazado = otro ya la tiene:
  siguiente. Despues, una linea en el espejo de `backlog` (`estado: en
  curso`, `rama:`); si ese push falla, no importa.
- **Trabajo:** implementar el diseno completo: backend + frontend + tests +
  fila de `docs/metricas.md` si corresponde; tests primero en logica pura;
  con `tipo: bug`, el test que falla primero (receta 4 de OMC):
  `omc-test-engineer` lo propone antes de tocar el codigo, el Dev lo escribe
  y lo ve fallar (comando y falla en `## Implementacion`) y recien entonces
  arregla; migracion + `metrics.py` + `recompute` si hay columna nueva;
  estilo del repo (espanol sin tildes en codigo, con tildes en la UI,
  comentarios que explican por que). Dos subagentes para backend y frontend
  si son independientes. Si un punto cae en un dominio que ni el diseno ni el repo
  resuelven y el Arquitecto no busco para esa ficha (su linea `Skills:`),
  una busqueda de skills de afuera (`.claude/skills/equipo-dev/skills.md`):
  una por turno, se consulta sin instalarla; `## Implementacion` lleva la
  linea `Skills:` siempre. Si el diseno deja abierto un punto con enfoques
  genuinamente distintos (un algoritmo, la decodificacion de un campo) y no
  lo decidio una arena del Arquitecto, ese punto se juega en una arena
  (`.claude/skills/equipo-dev/arena.md`): una por turno, `--agents 4`, el
  diff del ganador pasa por los mismos tests, `check.sh` y revision que
  cualquier cambio. Antes del ultimo push: subagente ciego
  `omc-code-reviewer` con `revision.md` (receta 2 de OMC, eje de estandares)
  sobre `git diff origin/dev...HEAD -- . ':(exclude)docs/backlog'` y corregir lo real (es el primer
  filtro, no el ultimo; el diff que se le pasa excluye `docs/backlog`, que
  es el plan); un CRITICAL o HIGH confirmado que no alcanza a corregirse
  deja la ficha `en curso` con `## Pendiente`, nunca `implementado`.
  `check.sh` en `Todo en verde.`. `## Implementacion`:
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
