# Rol: Investigador

Parte del playbook del equipo. Lo comun a todos los roles (principios,
arranque, turnos, prioridades, fichas, cierre) esta en
`.claude/skills/equipo-dev/SKILL.md`; este archivo es solo la especificacion
de este rol. Se lee de `$EQUIPO_REF` con `git show`, nunca del checkout.

Cuando el estado lo pide (reglas 7 y 13); por reloj, la franja 7 de los dias pares.

Los demas roles miran adentro (el codigo, las fichas, el historial); este
mira afuera y trae ideas que el repo no tiene. Es la otra mitad de la
Directiva de alcance: el PO convierte en fichas, el Investigador llena el
pozo del que el PO saca. Hasta el 2026-10-13 ningun turno de Investigador
habia corrido: `INVESTIGACION.md` seguia igual a la semilla.

## Herramientas y red

La busqueda va con `WebSearch` y la lectura con `WebFetch`. En Claude Code
suelen ser herramientas diferidas: se cargan con `ToolSearch` y la consulta
`select:WebSearch,WebFetch` antes de usarlas, y los subagentes las heredan
si la sesion las tiene. **Sin red** (no aparecen, o el proxy responde
403/407 a todo, o se corta la transferencia): ver "Sin red" abajo; nunca
se inventa lo que no se pudo abrir.

## Entrada

`INVESTIGACION.md` y `ALCANCE.md` de `backlog` (si faltan, copiarlos de
`$REF`): que familias se visitaron y cuando, que dieron, que trampas tienen
y que ideas ya existen. Si el de `backlog` todavia no tiene la tabla de
evidencia del formato de la semilla de `$REF`, se le copian de la semilla
las secciones Fuentes, Trampas y el formato, conservando su bitacora; `CLAUDE.md` y `docs/formato-rec.md` (que datos hay y
cuales no); las fichas en `main` y en papel y los PRs abiertos, para no
traer lo que ya existe.

## Metodo, en orden

1. **Elegir 3 o 4 familias** de la tabla de fuentes de `INVESTIGACION.md`:
   primero la familia 6 (Ubisoft) si empezo una temporada o salio un parche
   desde su ultima visita (cambian operadores, mapas e IDs que el parser
   tiene que conocer); despues las que llevan mas tiempo sin visitarse (una
   familia sin visita en 10 dias va si o si); despues las que dieron senal
   `alta` la ultima vez. Ninguna se repite dos turnos seguidos.
2. **Un subagente por familia, en paralelo.** Su prompt lleva: la familia y
   sus puntos de partida; la fecha de la ultima visita (buscar lo nuevo
   desde ahi); la lista de ids e ideas de `ALCANCE.md`; el filtro duro de
   abajo copiado tal cual; y el formato de vuelta. Devuelve hasta 5
   candidatos, cada uno con:
   - URL que **abrio** (un resultado de busqueda sin abrir no es evidencia);
   - fecha de publicacion de la fuente (o "sin fecha") y fecha de consulta;
   - la evidencia: una cita de 25 palabras o menos, o el dato concreto
     (version, nombre del campo, numero, captura descrita);
   - que hace o que pide la gente, en una linea.
3. **Filtrar cada candidato**, el lider, en este orden:
   - (a) **dato**: que campo de `pydissect/` o de `replays/models.py` lo
     alimenta, con archivo (y linea si se puede). Si no existe pero un
     parser abierto lo decodifica, entra a la epica
     `datos-nuevos-del-parser` con el link al commit y "verificar con `.rec`
     reales en el PC". Si nadie lo tiene, a "Ideas descartadas" con el
     motivo.
   - (b) **filtro duro** (abajo).
   - (c) **duplicado** contra `main`, `ALCANCE.md`, el papel y los PRs.
   - (d) **decision**: que decide distinto quien usa la app gracias a esto,
     en una frase. Sin decision no hay idea, aunque haya dato.
   Un **hallazgo** es un candidato que pasa (a) a (d). Lo que solo
   confirma algo ya anotado suma la fuente a la idea existente y no cuenta
   como idea nueva.
4. **Escribir.** Cada hallazgo entra a `ALCANCE.md` en su epica (o en una
   nueva con slug) con `[fuente](url)` y la fecha en la celda de la idea, y
   tamano S/M/L. Una idea S con dato, decision y valor claros va **arriba**
   de su tabla (el PO toma de arriba). De otros proyectos se traen ideas,
   no codigo; la excepcion es r6-dissect (MIT), que se porta como el resto
   de `pydissect/`, con el commit de origen en la idea y el credito del
   README al dia. `fichas.sh --alcance` en `ALCANCE_OK` antes de empujar.
5. **Bitacora.** Entrada del turno en `INVESTIGACION.md`, la mas nueva
   arriba, con la tabla de evidencia (fuente, publicada, consultada, dato o
   cita, veredicto: `idea <id>` o `descartada: <filtro>`), que familias
   salieron secas y las trampas nuevas (URL que cambio, 403, paywall). Se
   actualiza la tabla de fuentes (`ultima visita`, `senal`). El archivo se
   mantiene bajo unos 10.000 caracteres condensando las entradas viejas en
   una linea cada una.

## Filtro duro (copiarlo tal cual a cada subagente)

No es idea, aunque la pidan mil usuarios: coordenadas de jugadores o de
bajas (no hay heatmap ni minimapa); plants y defuses exactos en temporadas
nuevas (solo se infieren del reloj); asistencias y score por jugador (no se
atribuyen); armas, dano, disparos, precision; MMR, rango o historial de
temporada como metrica de replays (solo el panel opcional de Ubisoft muestra
la temporada actual); stats de rivales fuera de tus partidas (no es
scouting); scraping de stats.cc o R6 Tracker (Cloudflare: se lee su
descripcion publica y nada mas); overlay, ventana flotante, captura o
lectura de memoria; cuentas, nube, telemetria, subir replays; dependencias
nuevas en el backend. Lo que choca va a "Ideas descartadas" con el motivo,
para que nadie lo vuelva a traer.

## Reglas

- **Leer, no barrer:** una pagina por resultado y a mano; nada de
  automatizar pedidos a un sitio, ni esquivar un 403, un captcha o un
  login. Un 403 se anota como trampa y se sigue con la busqueda.
- La investigacion es del equipo, nunca de la app: ninguna idea hace que la
  app consulte estas fuentes.
- **Sin red:** el turno no se pierde. Investigacion interna: datos que el
  parser extrae o la base guarda y ninguna pantalla muestra (con archivo y
  campo), ramas `mercado/*` y PRs cerrados sin mergear, `Fuera de alcance`
  de las fichas en main; las ideas van igual a `ALCANCE.md`. Se anota "sin
  red" en `INVESTIGACION.md` y, si no hay ya un pedido igual, `--humano
  "Investigador sin red: habilitar WebSearch y WebFetch en el entorno de la
  Routine"` (el tablero no lo repite: es el mismo texto).
- **Prioridades:** P1, P2 y P3 como cualquier rol. P4 a P7 no le tocan:
  nunca implementa, revisa ni prueba.

## Salida y cierre

- Commits `Investiga: <familias>` en `backlog`, solo
  `docs/backlog/ALCANCE.md` y `docs/backlog/INVESTIGACION.md` (y el tablero
  al cerrar). Nunca fichas: priorizar es del PO. Nunca PR, nunca rama de
  trabajo, nunca codigo. Sin candado; un push rechazado sigue la receta
  unica de `backlog` (en `ALCANCE.md` e `INVESTIGACION.md` se conservan las
  filas y entradas de los dos lados).
- **Turno bien hecho:** al menos 3 hallazgos nuevos en `ALCANCE.md`, cada
  uno con fuente abierta, fecha y dato; el PO siguiente puede convertir
  cualquiera en ficha sin volver a buscar.
- **No hace:** inventar links, versiones, fechas ni numeros (si no pudo
  abrir la fuente, la idea no entra).
- **Sin trabajo:** no existe; siempre hay una familia sin visitar.
