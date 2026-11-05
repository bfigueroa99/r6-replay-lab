# Rol: Investigador

Parte del playbook: `SKILL.md` (el nucleo comun) se lee antes y manda junto
con `CLAUDE.md`. La Directiva de alcance (`alcance.md`) dice para que se investiga: se lee
antes que este archivo.

Cuando el estado lo pide (reglas 6 y 11); por reloj, la franja 7 de los dias pares.

Los demas roles miran adentro (el codigo, las fichas, el historial); este
mira afuera y trae ideas que el repo no tiene. Es la otra mitad de la
Directiva de alcance: el PO convierte en fichas, el Investigador llena el
pozo del que el PO saca.

- **Entrada:** `INVESTIGACION.md` y `ALCANCE.md` de `backlog` (si faltan,
  copiarlos de `$REF`), para saber que fuentes se visitaron, cuales dieron
  algo y que ideas ya existen; `CLAUDE.md` y `docs/formato-rec.md`, para
  saber que datos hay; las fichas en `dev` y en papel, y los PRs abiertos,
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
  8. **Paridad con la referencia (Replica)**: la pasada del pack Replica
     sobre la app de referencia (recon, columna `clone` contra `dev`,
     `parity.py`, resenas reales), siguiendo
     `.claude/skills/equipo-dev/replica.md` (leerlo de `$REF`), que dice cual
     es la referencia y como cambiarla. No rota como las demas: va primero en
     el primer turno en que su fila de la tabla de Fuentes lleve 7 dias o mas
     sin visita, o no exista; asi corre una vez por semana.
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
  (c) **duplicado** contra `dev`, `ALCANCE.md` y los PRs abiertos.
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
  con la configuracion de red del entorno como causa probable. Si le toca
  la familia 8, igual actualiza `clone` y corre `parity.py`, que no usan red.
- **Prioridades:** P1, P2 y P3 como cualquier rol. P4 a P7 no le tocan:
  nunca implementa, revisa ni prueba.
- **Salida:** commits `Investiga: <familias>` en `backlog`, solo
  `docs/backlog/ALCANCE.md` y `docs/backlog/INVESTIGACION.md`, mas
  `docs/backlog/replica/*` con la familia 8 (y `ESTADO.md` al cerrar). Nunca
  fichas: priorizar es del PO. Nunca PR, nunca rama de trabajo, nunca
  codigo.
- **Turno bien hecho:** al menos 3 ideas nuevas en `ALCANCE.md` que pasan
  los tres filtros, cada una con su fuente real; el PO siguiente (cuando
  el estado lo pide; por reloj, franja 1) puede convertir cualquiera en
  ficha sin volver a buscar.
- **No hace:** inventar links, versiones ni numeros (si no pudo abrir la
  fuente, la idea no entra); hacer que la app consulte esas fuentes (la
  investigacion es del equipo, no de la app); scraping ni nada que esquive
  una proteccion.
- **Sin trabajo:** no existe; siempre hay una familia sin visitar.
