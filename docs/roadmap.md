# Roadmap

Backlog de desarrollo. Lo consume el loop de Claude Code: cada iteracion toma
**el primer item sin marcar**, lo implementa completo (backend + frontend +
tests + docs), deja la suite en verde y hace un commit.

Reglas del loop:

- Un item por iteracion. Si un item resulta ser mas grande de lo que parece, se
  parte en dos y se deja el resto anotado aca.
- `cd backend; python manage.py test tests` en verde antes de cada commit.
  `cd frontend; npm run build` si se toco `frontend/src`.
- Metrica nueva -> fila nueva en `docs/metricas.md`.
- Marcar el item como hecho (`### 3. ~~Nemesis~~ [x]`) con una linea de que
  quedo implementado, y commitear el roadmap junto con el codigo.
- Cuando no queden items sin marcar, el loop se detiene.

## No-goals

- **Overlay in-game, en ninguna forma.** Ni ventana flotante, ni hook, ni
  captura de pantalla, ni lectura de memoria del juego. Es una decision del
  proyecto, no una tarea pendiente.
- API de Ubisoft, cuentas, nube, telemetria.
- Cualquier cosa que necesite datos que el `.rec` no trae (ver `CLAUDE.md`).

## Que hacen los competidores

Dos familias distintas, y solo una es comparable:

**Trackers de API** ([stats.cc](https://stats.cc/siege),
[R6 Tracker](https://r6.tracker.network/)): leen la API de Ubisoft. MMR,
historial de temporadas, leaderboards, rango de los rivales del lobby. Nada de
eso se puede replicar leyendo replays, y no es el objetivo. Lo unico que si
aplica de ellos: **comparacion con companeros de escuadra** ("con quien deberias
jugar mas"), ya implementado, y el breakdown por operador / mapa / modo, que ya
existe.

**Herramientas de replay** ([r6-replay.com](https://r6-replay.com/),
[R6 Replay Viewer](https://r6.arenyze.com/r6-replay-viewer),
[Aurelix](https://aurelix.app/),
[ReplayAnalysis](https://github.com/Zander-9909/ReplayAnalysis)): parsean el
mismo `.rec` que este proyecto. Son la competencia real. Lo que tienen y aca
falta:

| Ellos tienen | Aca | Item |
|---|---|---|
| Export CSV / Excel / XML de las tablas | Solo JSON crudo por comando | #6 |
| Resumen y "takeaways" por ronda | Timeline de eventos sin narrativa | #8 |
| Planilla estilo Pro League de Siege.GG (rating compuesto) | KST propio, sin rating | #5 |
| Ventana de trade configurable (usan 10s, aca son 3s) | Constante fija en el codigo | #11 |
| Blueprints interactivos con posiciones | Imposible: el `.rec` no trae coordenadas | - |
| Workspaces de equipo y scrims compartidos | Fuera de alcance: local y de un jugador | - |

Y lo que **ninguno** tiene, porque solo sale de tu propio historial acumulado:
nemesis por rival (#3), sesiones de juego con curva de fatiga (#4), perfil de un
jugador cruzado con tus partidas (#7) y comparacion entre dos periodos (#10).
Ahi esta la diferencia del proyecto, no en igualar la planilla de nadie.

## Backlog

> **Nota de orden**: los items #1 y #2 se dieron vuelta. El #1 (UI) necesita el
> re-etiquetado del #2 para poder decir que quedo listo, asi que el #2 se hizo
> primero. El #18 (Electron) entro fuera de orden porque lo pidio el usuario.
> El numero de cada item se mantiene para no romper las referencias.

### 2. `manage.py retag` [x]

Hecho: `replays/retag.py` vuelve a resolver `Match.map_name` / `map_slug` desde
`map_id` y `RoundPlayer.operator` desde `operator_id`, sin tocar los `.rec`.
Nunca degrada una etiqueta buena a `Unknown(...)`. Comando `manage.py retag`
con `--dry-run`, y `unknown_ids --write` ahora escribe en `OVERRIDES_PATH` (antes
ignoraba la variable) y apunta a `retag` en vez de a `import_replays --force`.
12 tests nuevos.

### 18. App de escritorio con Electron [x]

Pedido directo del usuario, hecho fuera de orden. `frontend/electron/` envuelve
la misma UI en una ventana: el proceso principal levanta Django, espera a que
`/api/health/` responda y recien ahi muestra la ventana (mientras tanto se ve
`loading.html`, no un error de conexion). Si ya hay un `runserver` corriendo lo
reutiliza y no lo mata al cerrar; si lo levanto el, lo baja con el arbol
completo. Menu con acceso a la carpeta de replays, links externos al navegador,
`contextIsolation` + `sandbox` y preload que no expone nada mas que un flag.
`npm run desktop`, `npm run desktop:dev` (contra Vite) y `scripts/desktop.ps1`.

**No es un overlay**: ventana con marco, sin always-on-top ni transparencia.
Sigue valiendo el no-goal de mas arriba.

### 1. Etiquetar mapas y operadores desconocidos desde la UI [x]

Hecho: pagina **Datos** con los IDs sin nombre, cada uno con sus sitios de bomba
(la pista que delata el mapa), cuantas partidas y rondas arrastra y desde cuando
aparece. Los operadores muestran ademas el lado, que parte el universo en dos.
Se escriben todos juntos con un boton, `POST /api/overrides/` valida y guarda, y
`retag()` reetiqueta lo ya importado en la misma request.

Verificado end to end sobre una copia de la base real: `Unknown(398899676157)`
-> nombre -> el historial se agrupa solo (11 rondas bajo el slug nuevo) y el ID
desaparece de la lista.

De paso: `unknowns.py` centraliza el descubrimiento (lo comparten el comando y
la API) y arregla un bug del `unknown_ids` viejo, que repetia el mismo sitio
varias veces porque el `ordering` del Meta de `Round` rompe el `.distinct()`.
La pagina tambien muestra el estado de importacion (`/api/import/status/`, otro
endpoint que existia y no consumia nadie): carpetas en disco, importadas y
pendientes. 20 tests nuevos.

> La pagina se llevo el estado de importacion ademas del etiquetado, porque una
> vez etiquetado todo queda vacia para siempre. Con las dos cosas es una pagina
> que sigue sirviendo.

### 3. Nemesis: duelos por rival

Del kill feed sale quien te mata y a quien matas, con identidad estable
(`profileID`). Ningun tracker de API puede hacer esto, porque no ve tus rondas.

- Tabla: rival, veces que te mato, veces que lo mataste, balance, en que mapas.
- Solo rivales con muestra suficiente (5 duelos o mas).
- Distinguir el duelo de apertura del resto: no es lo mismo perder siempre el
  primer contacto contra la misma persona.
- **Listo cuando**: hay una vista de nemesis y una regla del coach del estilo
  "pierdes 8 de 10 duelos de apertura contra X".

### 4. Sesiones de juego y curva de fatiga

Agrupar partidas por sesion (corte con mas de 2 horas sin jugar) y medir como se
mueve el rendimiento *dentro* de la sesion.

- Winrate, KPR y muertes sin trade por posicion en la sesion (1a partida, 2a...).
- Filtro "esta sesion" en la barra de filtros.
- Regla del coach: si a partir de la partida N el winrate cae mas de X puntos con
  muestra suficiente, decirlo con el numero.
- **Listo cuando**: se puede responder "juego peor despues de la tercera?" con
  datos y no con sensacion.

### 5. Rating compuesto por ronda y partida

Un solo numero que resuma el aporte, al estilo del rating de Siege.GG, calculado
sobre las metricas que ya existen (KPR, KST, aperturas, trades, supervivencia) y
normalizado contra el **propio promedio del jugador**, no contra un promedio
global que aca no existe.

- Formula explicita y documentada en `docs/metricas.md`, con los pesos a la
  vista y justificados.
- Rating por ronda -> promedio por partida -> serie temporal en Tendencias.
- **Listo cuando**: la formula esta escrita, tiene tests con casos limite y se ve
  en la UI sin presentarse como un numero oficial de nadie.

### 6. Export CSV de cualquier tabla

Es lo que ofrecen las herramientas de replay web y aca no hay nada equivalente.

- `?format=csv` en los endpoints de agregados (`/maps/`, `/operators/`,
  `/trends/`, `/teammates/`).
- Boton de descarga en `DataTable`, que exporte exactamente lo que se ve, con
  los filtros y el orden aplicados.
- **Listo cuando**: cualquier tabla de la app se abre en Excel en dos clicks.

### 7. Pagina de jugador

Perfil de un companero o rival dentro de tus partidas: rondas juntos y en contra,
winrate compartido, sus operadores, tu rendimiento con y sin esa persona.

- Ruta `/jugadores/:id`, enlazada desde Companeros, el scoreboard y el nemesis.
- **Listo cuando**: se puede hacer click en cualquier nombre de la app y ver todo
  lo que sabemos de esa persona.

### 8. Resumen narrativo por ronda

En `MatchDetail`, dos o tres frases generadas de los eventos: quien abrio, si
hubo trade, cuanto duro el 4v5, como se cerro. Las herramientas web lo venden
como "takeaways"; aca sale casi gratis porque los eventos ya estan anotados.

- Texto derivado, nunca inventado: si un dato no esta, no se menciona.
- **Listo cuando**: cada ronda del detalle tiene su parrafo y se entiende sin
  leer el timeline evento por evento.

### 9. Distribucion del momento de la muerte

Hoy solo esta el promedio ("mueres a los 98s"). Un promedio esconde la forma:
morir siempre a los 100s no es lo mismo que morir mitad a los 20 y mitad a los
170.

- Histograma por tramos del reloj, separado por lado.
- Cruce con "muerte sin trade": en que tramos ademas nadie te venga.
- **Listo cuando**: el histograma esta en Tendencias y el coach lo usa para
  distinguir "sales muy temprano" de "te quedas sin tiempo".

### 10. Comparar dos periodos

"Ultimos 30 dias vs los 30 anteriores": diff de cada metrica con su delta y la
muestra de cada lado. Es la unica forma honesta de decir "mejoraste".

- **Listo cuando**: hay una vista de comparacion que no afirma nada cuando la
  muestra de cualquiera de los dos lados es chica.

### 11. Ventana de trade configurable

`TRADE_WINDOW = 3.0` esta fija en `metrics.py`. Otras herramientas usan 10s, y el
numero cambia bastante los porcentajes de trade. Que sea configurable obliga
ademas a poder recalcular sin reimportar.

- `TRADE_WINDOW_SECONDS` en `.env`.
- `manage.py recompute` que recalcula las metricas derivadas de las rondas ya
  importadas.
- La UI dice con que ventana estan calculados los numeros que muestra.
- **Listo cuando**: cambiar la ventana y correr `recompute` actualiza toda la app.

### 12. Rango de fechas explicito en los filtros

Hoy solo hay "ultimos N dias". Falta desde / hasta, que la API ya soporta
(`since` y `until`).

- **Listo cuando**: se puede aislar una noche puntual o un mes cerrado.

### 13. Importacion con progreso

`POST /api/import/` es bloqueante y sin feedback: con 30 carpetas el boton queda
colgado sin decir nada.

- Reportar avance por carpeta, con polling sobre `ImportLog`, que ya existe.
- **Listo cuando**: el boton muestra "importando 3 de 12" y que carpeta va.

### 14. Lint y verificacion local

- `ruff` con configuracion minima y el repo limpio.
- `scripts/check.ps1`: tests + build + lint en un comando.
- Workflow de GitHub Actions listo para cuando el repo tenga remoto.
- **Listo cuando**: `.\scripts\check.ps1` es lo unico que hay que correr antes de
  commitear.

### 15. Tests de frontend

No hay ninguno. Los candidatos obvios son la logica pura: `qs()` en `api.js`, el
orden de `DataTable`, `fmt` / `pct` y `winrateColor`.

- Vitest, evitando jsdom si se puede.
- **Listo cuando**: `npm test` corre y cubre esa logica.

### 16. Backup de la base

`manage.py backup` que copie el SQLite con timestamp a `data/backups/`.
Reimportar todo el historial cuesta minutos, y los replays viejos los borra el
propio juego.

- **Listo cuando**: hay un backup con un comando y esta documentado en el README.

### 17. Bundle mas liviano

585 kB minificados, casi todo `recharts` cargado en la primera pantalla.

- Lazy load de las paginas con graficos, o chunk aparte para recharts.
- **Listo cuando**: la carga inicial baja de 250 kB sin perder funcionalidad.

### 19. Empaquetar la app de escritorio

Hoy `npm run desktop` necesita el repo, el venv y `npm install`. Un `.exe`
distribuible es otra cosa: hay que meter CPython y las dependencias adentro
(electron-builder + PyInstaller o similar), decidir donde vive la base de datos
fuera del repo y firmar el binario. Vale la pena solo si la app va a salir de
este PC.

- **Listo cuando**: existe un instalador que corre en una maquina sin Python.

## Ideas descartadas

| Idea | Por que no |
|---|---|
| Overlay in-game | No-goal del proyecto. |
| Heatmap de posiciones sobre el minimapa | El `.rec` no trae coordenadas. |
| Stats de armas, precision, dano | No estan en el formato. |
| MMR, rango, historial de temporada | Solo via API de Ubisoft. |
| Scouting de rivales fuera de tus partidas | Idem. |
| Workspaces de equipo, scrims compartidos | Es una app local y de un jugador. |
| Subir replays a un servidor para parsear | Todo corre en el PC, a proposito. |
