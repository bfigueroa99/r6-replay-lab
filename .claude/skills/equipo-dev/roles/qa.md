# Rol: QA

Parte del playbook del equipo. Lo comun a todos los roles (principios,
arranque, turnos, prioridades, fichas, cierre) esta en
`.claude/skills/equipo-dev/SKILL.md`; este archivo es solo la especificacion
de este rol. Se lee de `$EQUIPO_REF` con `git show`, nunca del checkout.

Cuando el estado lo pide (regla 2); por reloj, franja 6.

QA ejercita el sistema, no relee el diff: lo que el Revisor ya leyo, QA lo
maneja como un usuario y como un atacante torpe. Cada prueba deja un comando
y un resultado que el humano puede repetir copiando y pegando. Las
herramientas viven en `scripts/equipo-dev/` y se traen de `$EQUIPO_REF`
(Herramientas del equipo en `SKILL.md`); miden el checkout, o sea la rama.

- **Entrada:** fichas `revisado`, de la mas vieja a la mas nueva, hasta 2
  por turno; `backend/tests/factories.py`; `docs/metricas.md`.
- **Antes de candar:** `puerta.sh <rama> --solo b` en `PUERTA b OK`: esta
  sesion no implemento ni reviso esa ficha.
- **Protocolo por ficha** (candado `qa`, push; los resultados van a
  `## QA <fecha> sobre <sha corto>`, un comando y su resultado por linea):
  1. **Base verde.** `git merge origin/main` si main se movio; `check.sh`
     completo; anotar los conteos (tests backend, vitest, e2e).
  2. **Criterios.** Cada criterio de aceptacion con su evidencia: el test
     que lo cubre (nombre y `OK`), el `curl` con la respuesta, o el paso del
     e2e. Un criterio sin evidencia es un criterio que falla.
  3. **Mutacion de lo nuevo.** Por cada archivo de codigo que cambia la rama
     (`git diff --name-only origin/main...HEAD -- backend frontend/src`):

     ```bash
     git show "$EQUIPO_REF:scripts/equipo-dev/mutar.py" | python3 - \
         --archivo <archivo> --comando "<el test mas chico que lo cubre>" --base origin/main
     ```

     Cada `MUTANTE vivo` se mira: o es equivalente (no cambia ningun
     comportamiento: se anota por que en una linea) o es un hallazgo con el
     test exacto que lo mataria.
  4. **Bateria sobre la rama.**
     `git show "$EQUIPO_REF:scripts/equipo-dev/qa.sh" | bash -s -- --salida "$TMPDIR/qa-NN"`
     (deriva de docs, lint de fichas, barrido de toda la API sobre base
     vacia y sembrada, fuzz del parser, pasada por todas las paginas en
     escritorio y celular). Un `HALLAZGO` que tambien da en `main` es
     preexistente: no bloquea la ficha y va al papel (paso de abajo); uno
     nuevo de la rama es hallazgo de la ficha. `AVISO` de una pagina que la
     rama toca se mira en la captura de `capturas/`.
  5. **Segun lo que toca la rama:**
     - API o agregados: `curl` a los endpoints tocados y vecinos con la base
       sembrada y con una base armada en el scratchpad desde `factories.py`
       con el caso borde de la ficha (partida de un jugador, nick repetido,
       ronda sin bajas, prorroga, alguien que se fue).
     - Frontend: chunk inicial de `vite build` contra el de main (no crece
       mas de 10 % sin justificacion en la ficha); la pagina en celular (375
       px) sin scroll horizontal; numeros nuevos con fila en
       `docs/metricas.md`; textos de UI con tildes y ñ.
     - Migracion o `recompute`: base con el esquema de `origin/main`,
       `migrate` y `recompute --dry-run` y `recompute` sobre ella; un segundo
       `recompute` no cambia nada.
     - Parser: `fuzz_parser.py --casos 3000` y `tests.test_pydissect` con
       fixture sintetica.
     - Electron, `.ps1`, instalador: `## Verificar en el PC` con el comando
       exacto (la nube no los corre).
  6. **Regresion fija** (siempre, aunque la ficha no lo pida): el humo del
     e2e en verde (va en `check.sh`); `seed_demo --force` y la cabecera dice
     `29 partidas · 203 rondas` salvo que la ficha cambie el seed (y entonces
     el e2e cambio con el); ningun pedido fuera de localhost (barrido y
     paginas sin `HALLAZGO red`); `--reverse` del modulo de tests nuevo sin
     estado filtrado entre tests.
  7. **Veredicto.** Todo con evidencia: `aprobado`. Criterio que falla o
     hallazgo nuevo de la rama: `con hallazgos` con el repro exacto (QA no
     arregla). Umbral calibrado solo con datos sinteticos: pedido
     `--humano "calibrar <que> con la base real (ficha NN)"`. `candado: -`.
  8. **Seguir como Release.** Con la ficha en `aprobado`, la QA encadena
     (`turno.sh --encadenar`): con 20 minutos o mas da `rol=release` sobre
     esa ficha y el turno sigue con `roles/release.md` (pasos 3 a 5, puerta
     de merge incluida), anotando `release <sesion>` en `turnos:`. Probar y
     mergear no chocan con la independencia, y el `check.sh` que acaba de
     correr vale para la puerta si encima solo hay commits de
     `docs/backlog`: el Release aparte costaba un disparo entero por entrega
     para repetirlo. Con menos de 20 minutos, el disparo siguiente es
     Release, como siempre.
- **Hallazgo a ficha.** Lo que la bateria encuentra y no es de la ficha en
  prueba (preexistente en main) se vuelve ficha en el mismo turno, hasta 3
  por turno, despues de buscarla en el papel, en las ramas y en `ALCANCE.md`
  para no duplicar:
  - `tipo: bug`, severidad S1-S3 de `SKILL.md` y la prioridad que le toca;
    `fuente:` con la linea `HALLAZGO` tal cual, el comando que la produjo y
    el sha de main.
  - **Repro minimo** en "Que gana quien usa la app" o en un `## Repro`: para
    la API, el `curl` o tres lineas con el test client; para el parser, los
    bytes armados en linea (por ejemplo la cabecera con `playerid` = `abc`),
    nunca un `.rec` ni un binario al repo; para una pagina, ruta, ancho de
    pantalla y que se ve.
  - Criterios de aceptacion que empiezan por "el repro deja de fallar" y
    un test con nombre que lo fija.
  - Un `AVISO` (S4: desborde, foco, texto raro, accesibilidad) va a
    `ALCANCE.md` como idea de friccion con la pantalla y el paso, no como
    ficha.
- **Salida:** commits `Prueba: NN titulo` docs-only, mas tests de borde
  verdes si agrego; fichas `Propone:` en `backlog` por los hallazgos
  preexistentes. Nunca rama de trabajo; PR y merge solo como Release
  encadenado en el mismo turno (paso 8).
- **Turno bien hecho:** el humano puede repetir cada prueba copiando los
  comandos de `## QA`; ningun hallazgo queda solo en el informe.
- **Sin trabajo:** sin `revisado`, revisa las `implementado` con la
  especificacion del Revisor (`roles/revisor.md`; las deja en `revisado`,
  nunca las aprueba en la misma sesion). Sin eso, **pasada sobre main**:
  `qa.sh` completo en un checkout de `origin/main`, y cada `HALLAZGO`
  sigue "Hallazgo a ficha"; lo que se echo de menos usando la app (un
  filtro que falta, un dato que no se puede ver, un paso de mas) va como
  idea a `ALCANCE.md`, con la pantalla y el paso. Si `qa.sh` da `QA_OK` y
  no hay avisos nuevos, el resultado del cierre es `nada` y se dice que se
  corrio.
