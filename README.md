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
operador / lado / numero de ronda, y con que companeros de escuadra ganas mas
rondas.

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
`setup.ps1`, `init-git.ps1`, `import.ps1`, `start.ps1`, `watch.ps1`, `dev.ps1`,
`test.ps1`.

## Uso

```powershell
# importar todo lo que haya en la carpeta de replays
cd backend
python manage.py import_replays

# levantar la app (sirve el build de React en la misma URL)
python manage.py runserver
```

Abre <http://127.0.0.1:8000>.

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
| `manage.py test tests` | Corre la suite (98 tests). |

## Configuracion

Todo vive en `.env` (ver `.env.example`):

| Variable | Default | Que hace |
|---|---|---|
| `REPLAY_DIR` | ruta de Steam por defecto | Carpeta `MatchReplay` de Siege. |
| `IMPORT_QUIET_SECONDS` | `60` | Segundos sin cambios en los `.rec` para considerar terminada una partida. |
| `WATCH_INTERVAL_SECONDS` | `20` | Cada cuanto revisa el watcher. |
| `MIN_ROUNDS_DEFAULT` | `5` | Muestra minima para que un agregado aparezca en las tablas. |
| `SQLITE_PATH` | `data/db.sqlite3` | Base de datos. |
| `OVERRIDES_PATH` | `data/overrides.json` | Nombres para IDs de temporadas nuevas. |

## Cada temporada rompe algo

Ubisoft cambia los IDs de mapas revampeados y agrega operadores, asi que el
parser esta hecho para degradar bien en vez de reventar:

- **Operador nuevo**: el nombre sale de la cabecera del propio replay
  (campo `rolename`), y su lado se deduce por mayoria de los operadores
  conocidos de su equipo. No hay que tocar codigo.
- **Mapa revampeado (ID nuevo)**: aparece como `Unknown(<id>)`. Corre
  `manage.py unknown_ids`: te muestra los sitios de bomba que vio en ese mapa
  (con eso lo identificas al tiro) y con `--write` te deja la entrada lista en
  `data/overrides.json` para rellenar.
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
    analytics/
      metrics.py        metricas derivadas por ronda
      aggregates.py     agregaciones para la API
      coach.py          motor de insights
    views.py, urls.py   API JSON
  tests/                98 tests (parser, metricas, agregados, coach, API)
frontend/               React + Vite + recharts
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

## Credito

El trabajo de reverse engineering del formato Dissect es de
[r6-dissect](https://github.com/redraskal/r6-dissect) (redraskal, licencia MIT).
`pydissect` es un port a Python de esa logica, con los ajustes necesarios para
las temporadas nuevas. Si el parser te sirve, el credito es de alla.

Este proyecto no esta afiliado a Ubisoft.

## Licencia

MIT. Ver `LICENSE`.
