# Rol: Product owner

Parte del playbook del equipo. Lo comun a todos los roles (principios,
arranque, turnos, prioridades, fichas, cierre) esta en
`.claude/skills/equipo-dev/SKILL.md`; este archivo es solo la especificacion
de este rol. Se lee de `$EQUIPO_REF` con `git show`, nunca del checkout.

Cuando el estado lo pide (reglas 7 y 10); por reloj, franja 1.

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

