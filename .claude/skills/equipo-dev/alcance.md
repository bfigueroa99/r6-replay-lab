# Directiva de alcance (del humano, 2026-10-10)

Parte del playbook del equipo (`SKILL.md` es el nucleo comun). La leen el PO,
el Arquitecto y el Investigador; manda sobre que proponer, disenar e
implementar.

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
  usa y su estado (`idea`, `ficha NN`, `en dev`, `PR #n`; las marcas viejas
  `en main` cuentan igual). Lo mantiene el PO y lo alimentan dos lados: el
  PO y el Arquitecto con lo que ven adentro del repo, y el **Investigador** con lo que trae de afuera (otras
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
  las funcionalidades que llegaron a `dev` en los ultimos 7 dias. Si en 7
  dias no llego ninguna, el Release lo dice en `## Para el humano` con el
  cuello de botella (papel vacio, diseno trabado, cola llena, rojo).
