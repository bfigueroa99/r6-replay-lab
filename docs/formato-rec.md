# El formato .rec, por dentro

Notas de implementacion de `backend/pydissect/`. Sirven para dos cosas: entender
de donde sale cada dato de la app, y arreglar el parser cuando una temporada de
Siege cambie algo.

El reverse engineering original es de
[r6-dissect](https://github.com/redraskal/r6-dissect) (redraskal, MIT).
`pydissect` porta esa logica a Python y agrega el manejo de temporadas nuevas.

## Donde estan los replays

```
D:\...\steamapps\common\Tom Clancy's Rainbow Six Siege\MatchReplay\
  Match-2026-09-09_17-20-05-21072\
    Match-2026-09-09_17-20-05-21072-R01.rec    ~5-9 MB por ronda
    Match-2026-09-09_17-20-05-21072-R02.rec
    ...
```

Una carpeta = una partida. Un `.rec` = una ronda. **No** quedan en Documentos.
Siege los va rotando, asi que si quieres historial hay que importarlos antes de
que el juego los borre.

## Estructura del archivo

Desde Y8S4 el archivo es "chunked":

```
┌───────────────────────────────────────────────┐
│ "dissect" + versionado + cabecera texto plano │  ~120 KB
├───────────────────────────────────────────────┤
│ frame zstd 1                                  │
│ frame zstd 2                                  │  ~40-60 MB al descomprimir
│ ...                                           │  (96 frames en un ejemplo real)
├───────────────────────────────────────────────┤
│ cola sin comprimir                            │
└───────────────────────────────────────────────┘
```

Antes de Y8S4 el archivo completo era un solo frame zstd con la cabecera dentro.
`Reader._load` detecta cual es cual mirando los primeros 4 bytes: `28 B5 2F FD`
es zstd (formato viejo), `dissect` es el nuevo.

`_decompress_chunks` recorre el archivo buscando el magic de zstd, descomprime
cada frame y concatena la salida. El error de magic mismatch al llegar a la cola
sin comprimir es esperado y corta el loop.

### La cabecera

Empieza con `"dissect"` (7 bytes) y despues viene un esquema de versionado que
nadie descifro. `read_header_magic` lo salta avanzando hasta el final de la
**segunda** secuencia de 7 bytes `0x00`; ahi arrancan los pares clave/valor.

Cada string se codifica como un uint64 little-endian de largo (que en la
practica es 1 byte significativo + 7 ceros) seguido de los bytes:

```
08 00 00 00 00 00 00 00  "playerid"
13 00 00 00 00 00 00 00  "7547976154654522721"
```

El loop lee pares hasta encontrar `teamscore1`, que es el ultimo. Las claves de
jugador (`playerid`, `playername`, `team`, `rolename`, ...) se agrupan: un
`playerid` abre un bloque y un `id` o `playlistcategory` lo cierra.

Claves utiles: `version`, `code`, `datetime`, `matchtype`, `worldid` (mapa),
`gamemodeid`, `recordingplayerid`, `recordingprofileid`, `roundnumber`,
`teamname0/1`, `teamscore0/1`, `startingteamscore0/1` (desde Y9S4), `id`
(match id, igual en todas las rondas de la partida).

`teamname1` suele venir como `"YOUR TEAM"`: es el equipo del que grabo.

### La telemetria

No tiene schema. Es un stream de paquetes y la unica forma de leerlo es buscar
patrones de bytes conocidos y a partir de ahi leer los campos que siguen.

| Patron | Que trae |
|---|---|
| `22 07 94 9B DC` | paquete de jugador: nombre, operador, spawn, profileID |
| `22 A9 26 0B E4` | cambio de operador de ataque |
| `AF 98 99 CA` | ubicacion / sitio de bomba |
| `1F 07 EF C9` | reloj de la ronda (uint32, segundos restantes) |
| `59 34 E5 8B 04` | match feedback (contiene el kill feed) |
| `22 D9 13 3C BA` | indicador de kill dentro del feedback |
| `EC DA 4F 80` | score del scoreboard |
| `4D 73 7F 9E` | asistencias del scoreboard |
| `1C D2 B1 9D` | kills del scoreboard |
| `22 A9 C8 58 D9` | timer del defuser (ya no funciona, ver abajo) |

El escaneo original de r6-dissect es un matcher incremental byte a byte.
`pydissect` usa `bytes.find`, que esta implementado en C: para estos patrones el
resultado es identico (ninguno tiene un prefijo que sea tambien sufijo de un
prefijo propio) y es unas 100 veces mas rapido en Python. Las coincidencias se
ordenan por offset antes de disparar los listeners, para que el orden de los
eventos sea el cronologico.

### El reloj

La secuencia de valores de un `.rec` real se ve asi:

```
0, 44, 43, ... 1, 0,   179, 178, ... 78, 77,   0
└── preparacion (45s) ──┘ └── fase de accion ──┘ └ fin
```

`clock_max` es el maximo (inicio de la fase de accion) y `clock_last` el ultimo
valor distinto de cero. Con eso se calcula cuanto duro la ronda y a que segundo
murio cada jugador (`death_elapsed = clock_max - reloj_de_la_muerte`).

## Lo que se rompio en las temporadas nuevas

Verificado contra replays de **Y11S3 (code 9883691)**, mas nuevo que la ultima
version que soporta r6-dissect upstream. La cabecera, los jugadores, el sitio,
el reloj y el kill feed funcionan sin cambios. Lo que no:

### Plant / defuse

El paquete `22 A9 C8 58 D9` ya no es el timer del defuser: ahora cae en paquetes
de creacion de entidades (se ven IDs de entidad con el prefijo `0x23`, y a veces
un `AF 98 99 CA` con un spawn adentro). Ademas **no hay ningun string tipo
`"44.97"` en todo el archivo**, asi que el contador ya no se transmite como
texto. Busque tambien un uint32 o float contando 45→0 en la region posterior al
plant y no aparece con un prefijo estable.

Consecuencia: no hay eventos de plant ni de defuse, y por lo tanto tampoco
condicion de victoria exacta cuando la ronda no termino en barrida.

Lo que hace la app: `analyse_round` marca `KilledOpponents` cuando el equipo
perdedor murio completo (eso si es certero) y `ObjectiveOrTime` con
`win_condition_certain = False` en el resto. Aparte marca `possible_plant`
cuando el modo es Bomb, el perdedor no fue barrido y el reloj se corto sobre los
5 segundos: la razon es que al plantar, el juego reemplaza el reloj principal por
el del defuser y deja de emitir el paquete de tiempo, asi que un corte muy
arriba con datos despues es señal de plant. Es una inferencia y se muestra como
tal; no entra en ninguna metrica.

**Por donde seguir**: comparar dos rondas del mismo mapa, una con plant y otra
sin, y diffear los patrones de 5-6 bytes que aparecen solo en la primera. Lo
intente con un diff de n-gramas sobre 6 rondas y no dio una señal limpia, pero
con ground truth (grabar una partida sabiendo que rondas tuvieron plant) deberia
salir.

### Asistencias y score

Los tres patrones del scoreboard siguen apareciendo (100+ veces por ronda) y los
valores se leen bien (210, 360, 190...), pero el `dissectID` del jugador ya no
esta a 13 o 30 bytes del valor. Busque los 10 IDs conocidos en una ventana de
120 bytes despues de cada paquete y no aparecen en ninguna posicion.

Consecuencia: se pueden leer los numeros pero no atribuirlos. La app guarda 0 y
`data_health.assists_available` sale en `false` para que la UI lo diga.

### IDs de mapas y operadores

Cada revamp cambia el `worldid` y cada temporada agrega operadores. Dos
mecanismos:

- **Operadores**: `operator_label()` usa el campo `rolename` de la cabecera como
  respaldo, que trae el nombre en texto (`"NOOR"` → `Noor`). El lado se deduce
  en `derive_team_roles()` por mayoria de los operadores conocidos del equipo, y
  el desconocido hereda el del equipo. No hay que tocar nada.
- **Mapas**: no hay nombre en la cabecera, asi que quedan como `Unknown(<id>)`.
  `manage.py unknown_ids` lista los IDs junto con los sitios de bomba que vio en
  ese mapa, que alcanzan para identificarlo (por ejemplo `2F Hookah Lounge, 2F
  Billiards Room` + `1F Kitchen, 1F Service Entrance` es Coastline). Se etiqueta
  en `data/overrides.json` y se reimporta con `--force`.

`MAPS_EXTRA` en `constants.py` ya trae los IDs identificados por este metodo.

## Como diagnosticar

Cuando algo deje de andar, esto es lo que sirve:

```python
from pydissect import Reader

r = Reader.from_path("...-R01.rec")
print(r.header["gameVersion"], r.header["codeVersion"])   # que temporada es
print(len(r.b))                                            # bytes descomprimidos

# cuantas veces aparece cada patron
for name, pat in [("player", b"\x22\x07\x94\x9b\xdc"),
                  ("time", b"\x1f\x07\xef\xc9"),
                  ("feedback", b"\x59\x34\xe5\x8b\x04")]:
    print(name, r.b.count(pat))

r.read()
print(r.header["site"], len(r.players), len(r.match_feedback))
```

Si un patron aparece 0 veces, cambio el patron. Si aparece pero el listener no
produce nada, cambiaron los offsets: hay que volcar los bytes que siguen al
patron y buscar donde quedo el campo.

```python
pos = r.b.find(b"\x59\x34\xe5\x8b\x04")
print(r.b[pos + 5 : pos + 80].hex(" "))
```

Un truco que funciona bien: los `dissectID` de los jugadores son 4 bytes con un
sufijo comun (`ed 99 1a f0`, `f2 99 1a f0`, ...). Buscarlos en la ventana
posterior a un paquete dice al tiro a que offset quedo el ID.

`manage.py export_round <archivo.rec>` escupe el JSON completo de una ronda, que
es la forma mas rapida de ver si el parseo quedo coherente.

## Rendimiento

En una maquina normal: unos 0.5 s por ronda (0.3 s de descompresion + 0.2 s de
escaneo), o sea ~3-4 s por partida de 6 rondas. La memoria pico es de unos
60 MB por ronda, porque la telemetria descomprimida se carga completa; `read()`
libera el buffer al terminar.

Importar 30 partidas (~170 rondas) toma alrededor de dos minutos.
