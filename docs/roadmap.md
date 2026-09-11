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

### 3. Nemesis: duelos por rival [x]

Hecho: pagina **Duelos**, con el total de duelos y dos tablas. Los teamkills se
descartan comparando el equipo de los dos en esa ronda, y se agrupa por
`profileID` y no por el nick de la ronda. Reglas nuevas del coach:
`operador-rival` y `nemesis`, las dos comparadas contra tu winrate global de
duelos.

**Ajuste sobre lo planeado**: se calibro contra los datos reales antes de
escribir la tabla, y en ranked solo el maximo era **5 duelos** contra un mismo
rival en 28 partidas. Con el umbral de 5 que decia este item la vista quedaba
con una fila. Asi que la tabla por persona baja a 3 duelos y se rotula como
anecdota, y se agrego una tabla **por operador rival** que junta muestra mucho
mas rapido: el operador sale del `RoundPlayer` del rival en esa ronda, porque el
evento del kill feed no lo trae. Esa es la que muestra algo util: en los datos
del usuario, Thorn le gana 8 de 9 duelos contra un promedio de 35%.

La regla `nemesis` mantiene el umbral honesto (8 duelos contra la misma persona)
y por lo tanto **no dispara** con estos datos. Es el comportamiento correcto, y
esta cubierta con tests sinteticos. 14 tests nuevos.

Pendiente anotado: la tasa por operador esta sobre duelos, no sobre rondas en
que enfrentaste a ese operador. Lo segundo seria mejor senal ("cuando enfrentas
a Thorn mueres el X% de las rondas") y necesita cruzar con las rondas donde ese
operador estuvo en el equipo rival.

### 4. Sesiones de juego y curva de fatiga [x]

Hecho: corte por `SESSION_GAP_MINUTES` (120 por defecto, configurable), panel
**Curva de la sesion** y tabla de sesiones en Tendencias, selector de sesion en
la barra de filtros y regla `fatiga-sesion` en el coach.

El corte de sesion se calcula sobre **todo** el historial y no sobre lo
filtrado: si filtras por mapa, esa partida sigue siendo la tercera de su noche.
Tiene test.

El corte de la 3a partida en el coach esta fijo a proposito: probar varios
cortes y quedarse con el que mas conviene es la forma barata de encontrar
patrones que no existen. Umbral de 10 puntos y 30 rondas de cada lado.

En los datos del usuario la curva existe y es clara: 52% en la 1a partida de la
sesion, 43% en la 2a, 46% en la 3a, 30% en la 4a y 29% de la 5a en adelante, con
el KPR cayendo de 0.48 a 0.05 en la 4a. 14 tests nuevos.

Detalle de implementacion: los agregados se piden una sola vez por partida y se
pliegan en Python por posicion (`_fold`). Todo es suma menos
`avg_death_elapsed`, que es promedio y se pondera por muertes en vez de
promediar promedios; eso tambien tiene test.

### 5. Rating compuesto por ronda y partida [x]

Hecho: `RATING_WEIGHTS` + `rating_points_expr()` en `aggregates.py`, formula y
pesos documentados en `docs/metricas.md` con el por que de cada uno. El rating
entro en `AGGREGATES`, asi que aparece gratis en todos los agregados: mapas,
operadores, sitios, spawns, numero de ronda, sesiones, posicion en la sesion,
serie por partida y lista de partidas.

Decisiones que quedaron escritas:

- El 1.00 es el promedio del jugador sobre **todo** su historial, y no se
  recalcula con los filtros: si cambiara, el rating de un mapa y el de un
  operador no serian comparables. Tiene test.
- No entra si la ronda se gano: es aporte individual. Mirar rating y winrate
  juntos es lo interesante, y en los datos del usuario ya aparece el caso: Bank
  tiene rating 1.16 con winrate 31.6% (rinde y pierde igual).
- No se puso como KPI del Resumen: el rating global es 1.00 por definicion, asi
  que como numero suelto no dice nada. Va en las tablas, que es donde compara.

Dos trampas que costaron y quedaron comentadas en el codigo: la expresion se
arma con una funcion y no como constante de modulo (Django deja estado al
resolverla y compartir la instancia termina en "is an aggregate"), y en
`match_list` hubo que renombrar el alias `kills` porque el `F("kills")` del
rating lo resolvia contra la anotacion en vez del campo. 14 tests nuevos,
incluidos los casos limite de la formula.

### 6. Export CSV de cualquier tabla [x]

Hecho por los dos lados, y a proposito con formatos distintos:

- **Boton en `DataTable`**: basta pasarle `csvName` y aparece. Exporta las
  columnas visibles con sus etiquetas, en el orden en que esta ordenada la
  tabla y con los filtros aplicados. Punto y coma, coma decimal y BOM, que es lo
  que Excel en espanol abre sin preguntar. Una columna puede traer
  `csv: (row) => valor` o `csv: false` para ajustar que se exporta.
- **`GET /api/export/?table=...`**: CSV estandar (coma, punto decimal, sin BOM),
  el que espera pandas. `sep=;` lo cambia. Sin `table` lista las 13 disponibles.

Cambio sobre lo planeado: en vez de `?format=csv` en cada endpoint hay un
endpoint unico con `?table=`. `/trends/` devuelve tres tablas distintas, asi que
`?format=csv` ahi no tenia una respuesta unica; con nombres explicitos ademas se
exportan tablas que no tienen endpoint propio (sesiones, rivales, clutches).

Dos detalles que se vieron probando: las columnas del CSV se reordenan para que
el identificador quede primero (si no, el nombre del mapa salia en la columna
16), y el nombre del archivo usa la fecha local y no `toISOString()`, que en
UTC-4 bautizaba con el dia siguiente cualquier descarga despues de las 20:00.
14 tests nuevos.

### 7. Pagina de jugador [x]

Hecho: `/jugadores/:id` con tu rendimiento con esa persona, sin ella y contra
ella; sus propios numeros y operadores en las rondas compartidas; los duelos
directos si los hubo; y la lista de partidas marcando de que lado estuvo en cada
una (companero, rival o ambos, que pasa cuando entra por un abandono). Los
nombres enlazan desde Companeros, Duelos, el scoreboard de la partida y la lista
de jugadores de cada ronda.

Dos decisiones:

- **Las stats de la otra persona van sin rating.** El 1.00 es el promedio del
  jugador principal; aplicado a otro no significa nada, y mostrarlo mal es peor
  que no mostrarlo. Tiene test.
- **El lado "sin esa persona" casi siempre tiene poca muestra.** Con el
  companero habitual del usuario son 133 rondas contra 18, asi que la pagina
  avisa cuando alguno de los dos lados baja de 20 rondas en vez de dejar que la
  diferencia se lea como un hecho.

14 tests nuevos.

### 8. Resumen narrativo por ronda [x]

Hecho: `analytics/narrative.py`, una funcion pura sobre el mismo dict que la API
ya arma para el detalle. Cada frase se escribe solo si su dato existe; una ronda
sin eventos devuelve lista vacia en vez de texto de relleno.

La frase que mas aporta no estaba en el item: **cuantos segundos se jugaron en
inferioridad**, recorriendo el feed con la cuenta de vivos por equipo. En los
datos del usuario aparecen rondas con 122 de 178 segundos en 4v5, que explica la
derrota mejor que cualquier metrica individual.

Detalle de redaccion que hubo que corregir mirando la salida real: el trade de
la apertura se enmarca segun quien perdio el duelo. "Nadie la vengo" cuando la
muerte es propia, "El rival no la vengo" cuando la apertura la gano tu equipo:
la misma frase para los dos casos leia como un reproche cuando era una ventaja.

18 tests nuevos, todos sobre que no afirme lo que no sabe.

### 9. Distribucion del momento de la muerte [x]

Hecho: panel "Cuando mueres" en Tendencias, con histograma apilado por lado en
tramos de 30s, el cruce con muertes sin trade por tramo, y cuatro tarjetas con
los dos extremos de cada lado. Reglas nuevas del coach:
`muertes-tempranas-{lado}` y `sin-tiempo-ataque`.

**Los dos extremos miden ejes distintos, y eso fue el hallazgo del item.**
"Sales muy temprano" son los primeros 30 **segundos jugados**; "te quedas sin
tiempo" son las muertes con menos de 30 **segundos de reloj**. No es lo mismo y
el promedio tapa los dos.

Calibracion contra los datos reales, otra vez antes de escribir la regla: la
distribucion del usuario esta cargada al final (43% de las muertes despues de
los 120s, apenas 10% en los primeros 30). La primera version de la regla iba a
marcar "mueres muy tarde" con un umbral de 40% sobre los ultimos tramos, pero la
distribucion de muertes en Siege **es** naturalmente tardia (mientras mas
sobrevives, mas chance de morir tarde) y este proyecto no tiene un promedio
poblacional con que comparar. Habria sido marcar como problema una forma normal.

La regla que quedo usa el reloj restante, que si es interpretable sin baseline:
morir en ataque con menos de 30s de reloj significa que la ronda ya no daba para
plantar. Con los datos del usuario dispara: 15 de 52 muertes en ataque (29%).
16 tests nuevos.

### 10. Comparar dos periodos [x]

Hecho: panel "Progreso" arriba de Tendencias, `GET /api/compare/`, y diez
metricas con su delta.

**Dos cambios sobre lo planeado, los dos por el mismo motivo: 30 dias contra 30
no dice nada con este historial.** El usuario tiene 8 dias de replays, asi que
el modo por dias deja el periodo anterior vacio. Se agrego el modo por
**partidas** (las ultimas N contra las N anteriores), que siempre tiene muestra
de los dos lados si jugaste 2N, y quedo de default. El modo por dias sigue
disponible en el selector.

El segundo cambio es el que mas aporta: **banda de ruido**. La comparacion de 10
contra 10 partidas daba un winrate 9.3 puntos mas bajo, que leido solo parece un
bajon. El error estandar de la diferencia de proporciones con ~50 rondas por
lado es 9.6 puntos: ese cambio no existe. Ahora cada porcentaje trae su banda y
el veredicto es `ruido` cuando el cambio no la pasa. En la misma comparacion,
KST bajo 15.2 con banda 9.6 y ese si se marca como real: el problema no era el
winrate, era que esta aportando en menos rondas.

La banda solo se puede calcular para proporciones; en K/D, KPR y rating la
flecha muestra direccion pero no afirma que el cambio sea real, y "mueres a los"
va sin juicio (ver item #9). 16 tests nuevos, la mitad sobre la banda.

### 11. Ventana de trade configurable [x]

Hecho: `TRADE_WINDOW_SECONDS` en el `.env`, `manage.py recompute` (con
`--window` y `--dry-run`), y la ventana a la vista en el panel de salud de datos
del Resumen y en `/api/health/`.

La regla de trade se saco a `metrics.annotate_trades()` y la llaman los dos
caminos, el import y el recalculo. Duplicarla habria significado que cambiar la
ventana diera numeros distintos segun por donde pasaste.

`annotate_trades` resetea antes de contar, y eso tiene test propio: achicar la
ventana tiene que poder **sacar** trades que antes valian, no solo sumar. Sin el
reset, ir de 10s a 3s dejaba los trades viejos pegados.

Verificado end to end sobre una copia de la base real: con 3s las muertes sin
trade son 97.3% y el KST 45.5%; con 10s pasan a 91.2% y 49.1%; volviendo a 3s
quedan exactamente los numeros originales. 145 filas de jugador y 77 eventos se
mueven en cada pasada.

Dato que salio de ahi: aun con la ventana de 10 segundos, el 91% de las muertes
del usuario sigue sin vengarse. El problema que marca el coach no era un
artefacto de una ventana estricta. 16 tests nuevos.

### 12. Rango de fechas explicito en los filtros [x]

Hecho: la barra de filtros tiene "Entre dos fechas..." en el selector de
periodo, y al elegirlo aparecen desde y hasta. Elegir cualquier otro periodo
limpia el rango, y viceversa, para que no queden dos filtros de tiempo peleando.

El bug que habia que arreglar no estaba en la UI sino en la API: `until` se
parseaba con `fromisoformat`, asi que `until=2026-09-08` era la medianoche del 8
y **dejaba fuera todo ese dia**, justo lo contrario de lo que espera quien lo
escribe. Ahora una fecha sin hora se estira al final del dia; si viene con hora,
se respeta tal cual. Los dos casos tienen test.

El modo rango vive en un estado local del componente y no en los filtros: entre
elegir "entre dos fechas" y escribir la primera hay un momento en que no hay nada
que mandar a la API, y sin ese estado el selector se volvia solo a "todo el
historial". 11 tests nuevos.

### 13. Importacion con progreso [x]

Hecho: `POST /api/import/` lanza la importacion en un hilo y vuelve enseguida,
`GET /api/import/progress/` dice como va, y el boton muestra "Importando 3 de
12" con la carpeta que esta leyendo debajo.

Cambio sobre lo planeado: no se hace polling sobre `ImportLog` sino sobre un
estado propio (`ImportJob`). `ImportLog` tiene una fila por carpeta ya
intentada, pero no sabe cuantas faltan, y sin el total no hay "3 de 12".

Dos detalles que salieron de probarlo contra los replays reales:

- La lista de carpetas se arma en el request y no en el hilo. En la primera
  version el POST volvia con `total: 0` porque el hilo todavia no habia
  alcanzado a calcularla, y el boton mostraba "importando..." sin numero.
- Cada partida tarda varios segundos en parsear (5-9 MB por ronda), asi que una
  importacion de 30 carpetas dejaba el boton congelado por minutos. Ahora se ve
  avanzar carpeta por carpeta.

`run_import_job` es sincrono y separado de `start_import` justamente para poder
probarlo: en los tests de Django un hilo abre otra conexion y no ve los datos de
la transaccion. 14 tests nuevos.

### 14. Lint y verificacion local [x]

Hecho: `ruff.toml` con un set corto de reglas, `requirements-dev.txt` (ruff y
nada mas, para que el runtime siga en dos dependencias), `scripts/check.ps1` con
lint + tests + build, y `.github/workflows/ci.yml` listo para cuando haya remoto.

De los 36 hallazgos iniciales, 11 eran RUF012 sobre `class Meta: ordering = [...]`
de Django: son listas por definicion del framework, no estado compartido
peligroso, asi que la regla se ignora con el motivo escrito. Los otros 25 se
arreglaron: 12 lineas largas, 4 `zip()` sin `strict=` (que ahora revienta si las
longitudes dejan de coincidir, que es lo que uno quiere), una variable `l` que se
confunde con un 1, un `int(round(...))` redundante y los imports desordenados.

Dos decisiones:

- **`ruff format` no entra.** Reformatearia 23 archivos para pelear con un
  estilo que ya es consistente. El linter busca errores; el formateador impone
  gustos.
- **El autofix borro los `# noqa: BLE001 - se registra y se sigue`** junto con su
  explicacion. El `except Exception` amplio sigue siendo deliberado, asi que la
  razon volvio como comentario normal arriba de cada uno.

`check.ps1` usa `$ErrorActionPreference = 'Continue'` y mira `$LASTEXITCODE`:
Django y npm escriben su salida normal en stderr, y con 'Stop' PowerShell la
toma como error y corta en la primera linea.

### 15. Tests de frontend [x]

Hecho: 26 tests con vitest corriendo en **node, sin jsdom**. Cubren `qs()`, el
formateo de numeros que pueden venir null (`fmt` / `pct` / `ratio`), la rampa de
color del winrate, el orden de las tablas y la generacion del CSV.

Para poder probar sin DOM hubo que sacar dos cosas de adentro de los
componentes, y las dos ganaron con la mudanza:

- `ordenarFilas(rows, sort)`, que estaba dentro de un `useMemo`. Es donde vive
  la regla de que los nulos van al final **en las dos direcciones**: un "sin
  datos" no es ni el mejor ni el peor, y verlos arriba al invertir el orden es
  lo que hace desconfiar de una tabla. Ahora esa regla tiene test.
- `csvText(columns, rows)`, separado de `descargarCsv`, que se queda con el
  Blob y el enlace. El contenido del archivo (punto y coma, coma decimal,
  escapado de comillas) es logica; bajarlo es DOM.

Nota de versiones: vitest 5 pide vite >= 6 y el proyecto esta en vite 5.4, asi
que se fijo `vitest@2.1.9`. No se sube la herramienta de build para poder
agregar tests.

`npm test` entro tambien a `scripts/check.ps1` (ahora 4 pasos) y al workflow.

### 16. Backup de la base [x]

Hecho: `manage.py backup` con `--keep`, `--out` y `--list`, documentado en el
README.

**No es `shutil.copy`.** Copiar un SQLite como archivo mientras alguien escribe
deja una base rota a la mitad; se usa la API de backup online de SQLite, que da
una copia consistente aunque el server este corriendo. El test no mira el
tamano del archivo: lo abre, corre `PRAGMA integrity_check` y cuenta las filas,
que es lo unico que importa de un backup.

Tres cosas que salieron de escribir los tests:

- `--out` llega como string y `existing_backups` asumia `Path`: reventaba al
  listar. Lo cazo el test del comando.
- Dos copias en el mismo segundo caian en el mismo nombre y la segunda pisaba a
  la primera en silencio. Ahora la segunda lleva sufijo.
- La rotacion ordenaba por nombre, y con ese sufijo el orden alfabetico pone la
  copia nueva antes que la vieja: habria borrado la equivocada. Ahora ordena por
  fecha del archivo.

Queda anotado como posible siguiente paso un boton en la pagina Datos: quien
vive en la app de escritorio no abre una consola, y un backup que no se corre no
sirve de nada.

### 17. Bundle mas liviano [x]

Hecho: **610 kB -> 184 kB** en la carga inicial (60 kB con gzip). Cada pagina es
su propio chunk de 2 a 11 kB, y `recharts` quedo en uno aparte de 383 kB que
solo se baja cuando hay un grafico en pantalla.

Hicieron falta las dos cosas, no una:

- `React.lazy` por ruta. Solo el Resumen entra en el bundle inicial, que es la
  pantalla de partida.
- Sacar el grafico del Resumen a `components/EvolucionChart.jsx`, tambien lazy.
  Sin esto la pantalla de entrada seguia arrastrando recharts y el numero no
  bajaba: el lazy por ruta no sirve si la ruta inicial es la que importa la
  libreria pesada.

Verificado en el navegador, y ahi aparecio lo unico que se rompio: al sacar el
grafico del Dashboard se fue tambien el import de `fmt`, que el panel de salud
de datos seguia usando. **El build no dijo nada y los tests tampoco** (es un
error de runtime en una pagina que no se renderiza en los tests); lo mostro la
consola del navegador.

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
