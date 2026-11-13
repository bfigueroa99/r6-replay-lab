"""Lector binario del formato Dissect (.rec) de Rainbow Six Siege.

Port a Python puro de la logica de https://github.com/redraskal/r6-dissect (MIT).
Sin binarios externos: solo `zstandard` para descomprimir los bloques.

Estructura del archivo
----------------------
Desde Y8S4 el archivo es "chunked": la cabecera va en texto plano (pares
clave/valor con prefijo de largo) y despues vienen N frames zstd concatenados
con la telemetria de la ronda. Antes de Y8S4 el archivo completo es un frame
zstd y la cabecera queda adentro.

La telemetria no es un stream con schema: se escanean patrones de bytes
conocidos y en cada coincidencia se leen los campos que siguen.
"""

from __future__ import annotations

import logging
from collections.abc import Callable, Iterator

import zstandard

from .errors import EndOfFile, InvalidFile, InvalidStringSep

log = logging.getLogger(__name__)

ZSTD_MAGIC = b"\x28\xb5\x2f\xfd"
DISSECT_MAGIC = b"dissect"
STR_SEP = b"\x00" * 7

Listener = Callable[["Reader"], None]


#: Tope de lo que puede descomprimir un .rec. Uno real ocupa 40-60 MB (ver
#: docs/formato-rec.md): con diez veces eso de margen, lo que lo pasa no es un
#: replay. zstd comprime 32.000 a 1 (3 KB de ceros son 100 MB), asi que sin
#: tope un archivo de pocos MB se lleva toda la memoria del equipo.
MAX_DESCOMPRIMIDO = 512 * 1024 * 1024

#: Bytes comprimidos que se le pasan a zstd por llamada. El tope se revisa
#: entre llamadas, y un tramo no puede expandirse a mas de 32.000 veces su
#: tamano: con 4 KB el tope se pasa, como mucho, por 128 MB.
_TRAMO = 4 * 1024


def _decompress_chunks(raw: bytes, start: int, limite: int | None = None) -> bytes:
    """Descomprime todos los frames zstd desde `start` y los concatena.

    Los .rec traen datos no comprimidos al final, asi que un error de magic
    mismatch es esperado y se trata como fin de datos. Un frame cortado (el
    juego se cerro a mitad de ronda) entrega lo que alcanzo a leer.

    Lee de a tramos sobre un `memoryview`: pasarle a zstd `raw[pos:]` copiaba
    lo que quedaba del archivo en cada frame (y `unused_data` otra vez), y no
    dejaba cortar una bomba antes de tenerla entera en memoria. Si la salida
    pasa de `limite` (por defecto `MAX_DESCOMPRIMIDO`) lanza `InvalidFile`.
    """
    if limite is None:
        limite = MAX_DESCOMPRIMIDO
    partes: list[bytes] = []
    total = 0
    vista = memoryview(raw)
    fin = len(raw)
    pos = raw.find(ZSTD_MAGIC, start)
    sections = 0
    while pos != -1:
        dobj = zstandard.ZstdDecompressor().decompressobj()
        del_frame: list[bytes] = []
        i = pos
        try:
            while i < fin and not dobj.eof:
                parte = dobj.decompress(vista[i : i + _TRAMO])
                i = min(i + _TRAMO, fin)
                if parte:
                    del_frame.append(parte)
                    total += len(parte)
                    if total > limite:
                        raise InvalidFile(
                            # lo lee el usuario en Datos (el detalle del import)
                            f"el archivo se descomprime a más de {limite // (1024 * 1024)} MB: "
                            "no es un replay"
                        )
        except zstandard.ZstdError as exc:  # frame corrupto o basura final
            # lo que el frame roto alcanzo a entregar no se usa, como antes
            total -= sum(len(parte) for parte in del_frame)
            log.debug("zstd corto la descompresion en %d: %s", pos, exc)
            break
        partes.extend(del_frame)
        sections += 1
        # lo que sobro del ultimo tramo despues del fin del frame
        usado = i - len(dobj.unused_data)
        pos = raw.find(ZSTD_MAGIC, max(usado, pos + len(ZSTD_MAGIC)))
    log.debug("zstd_sections=%d bytes=%d", sections, total)
    return b"".join(partes)


class Reader:
    """Lee una sola ronda (.rec).

    Uso::

        r = Reader.from_path("...-R01.rec")
        r.read()          # recorre toda la telemetria
        r.header          # dict con metadata + jugadores
        r.match_feedback  # lista de eventos (kills, plants, swaps...)
    """

    # ---------------------------------------------------------------- ciclo de vida
    def __init__(self, raw: bytes) -> None:
        self.b: bytes = b""
        self.offset: int = 0
        self._queries: list[bytes] = []
        self._listeners: list[list[Listener]] = []

        self.time: float = 0.0
        self.time_raw: str = ""
        self.clock_max: float = 0.0   # reloj mas alto visto (inicio de la fase de accion)
        self.clock_last: float = 0.0  # ultimo reloj distinto de cero (fin de la ronda)
        self.planted: bool = False
        self.players_read: int = 0
        self.last_defuser_player_index: int = -1
        self.last_killer_from_scoreboard: str = ""
        self.read_partial: bool = False

        self.header: dict = {}
        self.match_feedback: list[dict] = []
        self.scoreboard: list[dict] = []

        self._load(raw)
        self._register_listeners()

    @classmethod
    def from_path(cls, path) -> Reader:
        with open(path, "rb") as fh:
            return cls(fh.read())

    def _load(self, raw: bytes) -> None:
        from .header import read_header, read_header_magic

        if raw[:4] == ZSTD_MAGIC:
            # formato antiguo: todo el archivo es un frame zstd
            self.b = _decompress_chunks(raw, 0)
            self.offset = 0
            read_header_magic(self)
            self.header = read_header(self)
            return
        if raw[:7] != DISSECT_MAGIC:
            raise InvalidFile("el archivo no empieza con 'dissect' ni con un frame zstd")

        self.b = raw
        self.offset = 0
        read_header_magic(self)
        self.header = read_header(self)
        header_end = self.offset
        self.b = _decompress_chunks(raw, header_end)
        self.offset = 0

    def _register_listeners(self) -> None:
        from . import events
        from .constants import Y8S1

        self.listen(b"\x22\x07\x94\x9b\xdc", events.read_player)
        self.listen(b"\x22\xa9\x26\x0b\xe4", events.read_atk_op_swap)
        self.listen(b"\xaf\x98\x99\xca", events.read_spawn)
        if self.code_version >= Y8S1:
            self.listen(b"\x1f\x07\xef\xc9", events.read_time)
        else:
            self.listen(b"\x1e\xf1\x11\xab", events.read_y7_time)
        self.listen(b"\x59\x34\xe5\x8b\x04", events.read_match_feedback)
        self.listen(b"\x22\xa9\xc8\x58\xd9", events.read_defuser_timer)
        self.listen(b"\xec\xda\x4f\x80", events.read_scoreboard_score)
        self.listen(b"\x4d\x73\x7f\x9e", events.read_scoreboard_assists)
        self.listen(b"\x1c\xd2\xb1\x9d", events.read_scoreboard_kills)

    # ---------------------------------------------------------------- accesos utiles
    @property
    def code_version(self) -> int:
        return int(self.header.get("codeVersion", 0))

    @property
    def players(self) -> list[dict]:
        return self.header.setdefault("players", [])

    @property
    def teams(self) -> list[dict]:
        return self.header.setdefault("teams", [{}, {}])

    def player_index_by_id(self, dissect_id: bytes) -> int:
        for i, p in enumerate(self.players):
            if p.get("dissectID") == dissect_id:
                return i
        return -1

    def player_index_by_username(self, username: str) -> int:
        for i, p in enumerate(self.players):
            if p.get("username") == username:
                return i
        return -1

    def recording_player(self) -> dict:
        target = self.header.get("recordingPlayerID")
        for p in self.players:
            if p.get("id") and p["id"] == target:
                return p
        # fallback: el profileID de la cabecera es mas estable entre temporadas
        target_profile = self.header.get("recordingProfileID")
        if target_profile:
            for p in self.players:
                if p.get("profileID") == target_profile:
                    return p
        return {}

    # ---------------------------------------------------------------- primitivas
    def skip(self, n: int) -> None:
        self.offset += n
        if self.offset >= len(self.b):
            raise EndOfFile

    def bytes(self, n: int) -> bytes:
        self.skip(n)
        return self.b[self.offset - n : self.offset]

    def int(self) -> int:
        return self.bytes(1)[0]

    def string(self) -> str:
        size = self.int()
        return self.bytes(size).decode("utf-8", errors="replace")

    def uint32(self) -> int:
        self.skip(1)  # byte de tamano, ya conocido
        return int.from_bytes(self.bytes(4), "little")

    def uint64(self) -> int:
        self.skip(1)
        return int.from_bytes(self.bytes(8), "little")

    def header_string(self) -> str:
        size = self.bytes(1)[0]
        if self.bytes(7) != STR_SEP:
            raise InvalidStringSep
        return self.bytes(size).decode("utf-8", errors="replace")

    def seek(self, pattern: bytes) -> None:
        """Avanza hasta justo despues de la proxima aparicion de `pattern`."""
        idx = self.b.find(pattern, self.offset)
        if idx == -1:
            self.offset = len(self.b)
            raise EndOfFile
        self.offset = idx + len(pattern)

    # ---------------------------------------------------------------- listeners
    def listen(self, pattern: bytes, callback: Listener) -> None:
        for i, existing in enumerate(self._queries):
            if existing == pattern:
                self._listeners[i].append(callback)
                return
        self._queries.append(pattern)
        self._listeners.append([callback])

    def _scan(self, start: int, end: int) -> Iterator[tuple[int, int]]:
        """Devuelve (offset_del_ultimo_byte, indice_de_query) ordenado por offset.

        Se usa bytes.find (implementado en C) en vez del matcher incremental del
        original: para estos patrones el resultado es identico y es ~100x mas
        rapido en Python.
        """
        hits: list[tuple[int, int]] = []
        for j, query in enumerate(self._queries):
            pos = self.b.find(query, start, end)
            step = len(query)
            while pos != -1:
                hits.append((pos + step - 1, j))
                pos = self.b.find(query, pos + 1, end)
        hits.sort(key=lambda h: h[0])
        return iter(hits)

    def read(self) -> None:
        """Recorre la telemetria completa disparando los listeners."""
        from .events import round_end

        start = self.offset
        end = len(self.b)
        if self.read_partial:
            end = end // 3

        for offset, listener_index in self._scan(start, end):
            for listener in self._listeners[listener_index]:
                self.offset = offset + 1
                try:
                    listener(self)
                except EndOfFile:
                    continue
                except InvalidStringSep:
                    continue

        if not self.read_partial:
            round_end(self)
        self.b = b""  # libera memoria: la telemetria cruda ya no se necesita

    def read_partial_players(self) -> None:
        """Lectura rapida: solo hasta tener la lista de jugadores."""
        self.read_partial = True
        try:
            self.read()
        finally:
            self.read_partial = False
