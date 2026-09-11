# R6 Replay Lab

Analizador de replays de Rainbow Six Siege que corre entero en tu PC: lee los
`.rec` que el juego deja en `MatchReplay`, los parsea sin binarios externos y
te dice, con numeros, que estas haciendo mal.

No es otro sitio de stats agregadas. Trabaja sobre **tus replays**, ronda por
ronda: quien tomo el primer duelo, cuanto duraste vivo, si tu muerte se tradeo,
en que sitio se te cae el winrate y con que operadores rindes bajo tu promedio.

```
┌──────────────┐   parser Python    ┌──────────┐   metricas    ┌──────────────┐
│  *.rec       │ ─────────────────► │  SQLite  │ ────────────► │ React + API  │
│ MatchReplay  │   (pydissect)      │  Django  │  + coach      │  dashboards  │
└──────────────┘                    └──────────┘               └──────────────┘
```

## Que hace

**Parser propio en Python puro** (`backend/pydissect/`). No necesita la CLI de
Go de r6-dissect ni ningun `.exe`: descomprime los bloques zstd del `.rec` y
escanea los patrones de bytes de la telemetria. De cada ronda saca mapa, sitio,
equipos y su lado, los 10 jugadores con operador y spawn, el kill feed completo
con reloj y headshot, y el resultado de la ronda.

**Metricas que el juego no te muestra.** Duelos de apertura y que pasa con la
ronda cuando los ganas o los pierdes, trades y muertes sin trade, momento exacto
en que mueres, KST, clutches, multikills, winrate por mapa / sitio / spawn /
operador / lado / numero de ronda, con que companeros de escuadra ganas mas
rondas, contra que operadores rivales pierdes los duelos y como se cae tu
rendimiento segun cuantas partidas llevas en la sesion. Cualquier nombre de la
app lleva al perfil de esa persona: cuanto rindes con ella y sin ella.

**Coach.** Un motor de reglas explicitas que compara cada metrica con tu propio
promedio y exige muestra minima antes de opinar (20 rondas en general, 8-15 por
mapa/sitio/operador). Cada punto trae el numero, con que se compara, cuantas
rondas lo respaldan y que hacer al respecto. Si no hay datos, lo dice en vez de
inventar.

**Importacion automatica.** `manage.py watch_replays` vigila la carpeta y en
cuanto terminas una partida la importa sola. Nada de arrastrar archivos.

## Instalacion

Necesitas Python 3.11+ y Node 18+.

```powershell
cd r6-replay-lab

# 0. inicializar el repositorio git (solo la primera vez)
.\scripts\init-git.ps1

# 1. backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt

# 2. configuracion
copy .env.example .env
#    edita REPLAY_DIR si tu Siege no esta en la ruta por defecto

# 3. base de datos
cd backend
python manage.py migrate

# 4. frontend
cd ..\frontend
npm install
npm run build
```

O corre `.\scripts\setup.ps1`, que hace todo lo de arriba (menos el `init-git`).

Los scripts de `scripts/` son todos PowerShell y asumen el venv en `.venv`:
`setup.ps1`, `init-git.ps1`, `import.ps1`, `start.ps1`, `desktop.ps1`,
`watch.ps1`, `dev.ps1`, `test.ps1`, `check.ps1`.

Para trabajar en el codigo, ademas:

```powershell
pip install -r requirements-dev.txt   # ruff, nada mas
.\scripts\check.ps1                  # lint + tests + build, en un comando
cd frontend; npm test                 # solo los tests del frontend
```

`check.ps1` es lo unico que hay que pasar antes de commitear. Corre `ruff check`
pero no `ruff format`: el linter busca errores, el formateador impone gustos y
reescribiria medio repo. El mismo chequeo esta en
`.github/workflows/ci.yml`, listo para el dia que el repo tenga un remoto.

## Uso

```powershell
# importar todo lo que haya en la carpeta de replays
cd backend
python manage.py import_replays

# levantar la app (sirve el build de React en la misma URL)
python manage.py runserver
```

Abre <http://127.0.0.1:8000>.

### App de escritorio

Si prefieres una ventana propia en vez de una pestana del navegador, hay una app
de Electron que envuelve la misma UI:

```powershell
cd frontend
npm run desktop        # o .\scripts\desktop.ps1
```

El proceso principal levanta Django solo, espera a que la API responda y recien
ahi muestra la ventana. Si ya tenias un `runserver` corriendo en otra consola, lo
reutiliza y **no** te lo mata al cerrar. El menu tiene un acceso directo a tu
carpeta `MatchReplay`.

Que quede claro, porque es la duda obvia: **no es un overlay**. Es una ventana
normal, sin always-on-top, sin transparencia y sin ningun tipo de hook al juego.
Siege no se entera de que existe. Es un no-goal del proyecto, no algo pendiente.

Para desarrollar la UI dentro de la ventana, con hot reload:

```powershell
cd frontend
npm run desktop:dev    # apunta a Vite en :5173; Django tiene que estar corriendo
```

Para que importe solo cada vez que termines una partida, deja esto corriendo en
otra consola:

```powershell
python manage.py watch_replays
```

Durante desarrollo conviene el server de Vite con hot reload (proxea `/api` a
Django, no hay que tocar CORS):

```powershell
cd frontend
npm run dev     # http://localhost:5173
```

### Comandos

| Comando | Para que |
|---|---|
| `manage.py import_replays [ruta]` | Importa una carpeta de replays o una partida puntual. `--force` reimporta, `--limit N` corta. |
| `manage.py watch_replays` | Vigila `REPLAY_DIR` e importa cada partida al terminar. `--once` hace una pasada. |
| `manage.py export_round <ruta>` | Escupe el JSON crudo del parser para un `.rec` o una carpeta. Para depurar. |
| `manage.py unknown_ids` | Lista IDs de mapa/operador que el parser no supo nombrar. `--write` los deja listos en `data/overrides.json`. |
| `manage.py retag` | Re-aplica `overrides.json` sobre lo ya importado, sin reparsear los `.rec`. `--dry-run` muestra que cambiaria. |
| `manage.py recompute` | Recalcula trades, muertes sin trade y KST con la ventana configurada. `--window N` la fuerza, `--dry-run` muestra que cambiaria. |
| `manage.py test tests` | Corre la suite (291 tests). |

### Sacar los datos

Cada tabla de la app tiene un boton **Descargar CSV** que baja exactamente lo que
estas viendo: las mismas columnas, con los filtros y el orden aplicados. Ese
archivo va con punto y coma y coma decimal, que es lo que Excel en espanol abre
sin preguntar nada.

Para scripts hay un endpoint aparte, con CSV estandar (coma, punto decimal):

```powershell
curl "http://127.0.0.1:8000/api/export/?table=maps&ranked_only=1" -o mapas.csv
curl "http://127.0.0.1:8000/api/export/"      # lista las tablas disponibles
```

Acepta los mismos filtros que el resto de la API (`side`, `map`, `operator`,
`site`, `match_type`, `since`, `until`, `days`, `session`, `ranked_only`) y
`sep=;` si lo quieres con punto y coma.

`since` y `until` aceptan fecha sola (`2026-09-08`) o fecha y hora. Una fecha
sola en `until` significa **el dia completo**: `since=2026-09-08&until=2026-09-08`
es esa noche y nada mas.

## Configuracion

Todo vive en `.env` (ver `.env.example`):

| Variable | Default | Que hace |
|---|---|---|
| `REPLAY_DIR` | ruta de Steam por defecto | Carpeta `MatchReplay` de Siege. |
| `IMPORT_QUIET_SECONDS` | `60` | Segundos sin cambios en los `.rec` para considerar terminada una partida. |
| `WATCH_INTERVAL_SECONDS` | `20` | Cada cuanto revisa el watcher. |
| `MIN_ROUNDS_DEFAULT` | `5` | Muestra minima para que un agregado aparezca en las tablas. |
| `SESSION_GAP_MINUTES` | `120` | Minutos sin jugar para cortar una sesion. |
| `TRADE_WINDOW_SECONDS` | `3` | Segundos para considerar vengada una muerte. Cambiarlo pide `manage.py recompute`. |
| `SQLITE_PATH` | `data/db.sqlite3` | Base de datos. |
| `OVERRIDES_PATH` | `data/overrides.json` | Nombres para IDs de temporadas nuevas. |

## Cada temporada rompe algo

Ubisoft cambia los IDs de mapas revampeados y agrega operadores, asi que el
parser esta hecho para degradar bien en vez de reventar:

- **Operador nuevo**: el nombre sale de la cabecera del propio replay
  (campo `rolename`), y su lado se deduce por mayoria de los operadores
  conocidos de su equipo. No hay que tocar codigo.
- **Mapa revampeado (ID nuevo)**: aparece como `Unknown(<id>)`. La pagina
  **Datos** de la app los lista con los sitios de bomba que vio en cada uno (con
  eso lo identificas al tiro): le pones el nombre, lo guardas y el historial ya
  importado se reetiqueta solo. Por consola es lo mismo en dos pasos:
  `manage.py unknown_ids --write` deja las entradas en `data/overrides.json` y
  `manage.py retag` las aplica. En los dos casos no se vuelve a leer un solo
  `.rec`: los IDs ya estan en la base.
- **Cambio de formato binario**: ahi si hay que trabajar. `docs/formato-rec.md`
  documenta la estructura del `.rec`, los patrones de bytes y como diagnosticar
  cual dejo de funcionar.

## Que NO puede hacer (y por que)

Vale la pena ser explicito, porque son limitaciones del formato, no del codigo:

- **No hay coordenadas de las bajas.** El `.rec` no expone posiciones, asi que
  no existe heatmap sobre el minimapa. El mapa de calor de la app es por zona
  del juego: sitio de bomba y spawn de ataque, que es la granularidad real que
  entrega el replay.
- **Plants y defuses no se detectan en las temporadas nuevas.** El paquete del
  timer del defuser cambio y ya no trae el string del contador. Se infiere: si
  el reloj de la ronda se corta muy arriba y el equipo perdedor no fue barrido,
  se marca como *plant probable*. Nunca se cuenta como dato duro.
- **Asistencias y score por jugador.** Los paquetes del scoreboard siguen ahi
  pero el ID del jugador ya no aparece donde estaba, asi que no se pueden
  atribuir. La app lo reporta como no disponible en vez de mostrar ceros.
- **Solo ves lo que grabaste tu.** Los replays son desde tu cliente; las stats
  de los rivales salen del kill feed, no de su scoreboard.

`docs/formato-rec.md` explica el detalle tecnico de cada punto y por donde
seguir si alguien quiere resolverlos. Lo que si esta en carpeta, con lo que
hacen las herramientas parecidas y lo que se descarto a proposito, esta en
`docs/roadmap.md`.

## Estructura

```
backend/
  pydissect/            parser del formato .rec (independiente de Django)
    reader.py           lector binario, zstd chunked, escaneo de patrones
    header.py           cabecera en texto plano, nombres, roles de equipo
    events.py           listeners: jugadores, reloj, kill feed, scoreboard
    stats.py            stats por ronda compatibles con r6-dissect
    match.py            lectura de una partida completa
    constants.py        IDs de mapas, operadores, modos y versiones
    overrides.py        etiquetas para IDs de temporadas nuevas
  replays/
    models.py           Match / Round / RoundPlayer / Event / Player
    ingest.py           parseo -> base de datos, idempotente
    export.py           agregados a CSV
    recompute.py        rehace los trades con otra ventana, sin reparsear
    retag.py            re-etiqueta IDs ya importados sin reparsear
    unknowns.py         IDs sin nombre y el archivo de etiquetas
    analytics/
      metrics.py        metricas derivadas por ronda
      aggregates.py     agregaciones para la API
      coach.py          motor de insights
      narrative.py      resumen en palabras de cada ronda
    views.py, urls.py   API JSON
  tests/                291 tests (parser, metricas, agregados, coach, API)
frontend/               React + Vite + recharts (26 tests con vitest)
  electron/             app de escritorio (proceso principal y preload)
docs/                   formato del .rec, metricas y roadmap
data/                   SQLite y overrides (no se versiona)
```

## Metricas

Las definiciones completas estan en `docs/metricas.md`. Las que mas se usan:

- **Duelo de apertura**: la primera baja de la ronda. Se cuenta como ganado para
  quien mata y perdido para quien muere.
- **Trade**: mataron a tu asesino dentro de 3 segundos. Si no pasa, tu muerte es
  una *muerte sin trade*, la mas cara del juego.
- **KST**: rondas donde mataste, sobreviviste o tu muerte se tradeo. Es KOST sin
  la O, porque los eventos de objetivo no estan disponibles.
- **KPR**: bajas por ronda.
- **Rating**: un solo numero de aporte por ronda, normalizado contra tu propio
  promedio (1.00 es tu ronda tipica). Los pesos estan a la vista en
  `docs/metricas.md`: son un juicio, no una medicion, y no es el rating de
  ningun sitio.

## Credito

El trabajo de reverse engineering del formato Dissect es de
[r6-dissect](https://github.com/redraskal/r6-dissect) (redraskal, licencia MIT).
`pydissect` es un port a Python de esa logica, con los ajustes necesarios para
las temporadas nuevas. Si el parser te sirve, el credito es de alla.

Este proyecto no esta afiliado a Ubisoft.

## Licencia

MIT. Ver `LICENSE`.
