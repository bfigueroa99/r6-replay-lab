"""Fuzz del parser con .rec sinteticos, rotos y truncados.

En la nube no hay replays reales, asi que se arman: una cabecera `dissect`
con pares clave/valor plausibles (version de codigo, mapa, jugadores con
operadores conocidos), telemetria comprimida con zstd que contiene los
patrones que escuchan los listeners de `Reader` seguidos de bytes al azar, y
despues se rompe todo eso de formas que pasan en la realidad: archivo
cortado a mitad (Siege grabando cuando se cae el juego), bits cambiados,
valores de cabecera que no son numeros, tamanos que mienten.

El contrato que se prueba: con cualquier entrada, `Reader(raw)`, `.read()`
y `round_to_dict()` terminan bien o levantan un `DissectError` (rechazo
limpio). Cualquier otra excepcion es un hallazgo: `ingest` la atrapa, pero
la partida entera queda sin importar por una sola ronda rara (severidad S2
del playbook). Un caso que tarda mas de 5 s es un cuelgue.

Uso (desde la raiz del repo):
    git show $EQUIPO_REF:scripts/equipo-dev/fuzz_parser.py | python3 - [opciones]
Opciones: --casos N (400), --semilla N (7), --salida DIR (guarda cada
hallazgo como .bin con su repro), --autoprueba (rompe un listener a
proposito y verifica que el fuzz lo vea).

Salida: una linea por hallazgo distinto (tipo de excepcion y lugar),
`HALLAZGO <Excepcion> en <archivo:linea>: <mensaje> (n casos; ej: <generador>)`,
y al final `FUZZ_OK (<n> casos, <k> rechazos limpios)` (salida 0) o
`FUZZ_FALLA: <m> hallazgos distintos en <n> casos` (salida 1).
"""

from __future__ import annotations

import argparse
import random
import signal
import subprocess
import sys
import time
import traceback
import types
from pathlib import Path

LIMITE_SEGUNDOS = 5


def repo_raiz() -> Path:
    salida = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"], capture_output=True, text=True, check=False
    )
    if salida.returncode != 0:
        sys.exit("no es un repo git: correr desde la raiz del repo")
    return Path(salida.stdout.strip())


class Cuelgue(Exception):
    pass


class FallaDeAutoprueba(Exception):
    """La que levanta el listener roto de --autoprueba; no existe en pydissect."""


def _alarma(signum, frame):
    raise Cuelgue(f"mas de {LIMITE_SEGUNDOS} s")


def cadena_cabecera(texto: bytes) -> bytes:
    """`header_string`: un byte de largo, siete nulos y el texto."""
    return bytes([len(texto) % 256]) + b"\x00" * 7 + texto


def cabecera(azar: random.Random, constantes) -> bytes:
    codigos = [v for k, v in vars(constantes).items() if k.startswith("Y") and isinstance(v, int)]
    operadores = list(constantes.OPERATORS) or [1]
    pares: list[tuple[str, str]] = [
        ("version", "Y10S1"),
        ("code", str(azar.choice(codigos) + azar.randint(0, 5))),
        ("datetime", "2026-09-09-17-20-05"),
        ("worldid", str(azar.choice(list(constantes.MAPS) or [1]))),
        ("matchtype", str(azar.randint(0, 10))),
        ("gamemodeid", str(azar.randint(0, 10))),
        ("recordingplayerid", str(azar.randint(1, 10))),
        ("recordingprofileid", "14c9dacd-69a1-5ae1-80d8-ce1b96f8948f"),
        ("roundnumber", str(azar.randint(0, 12))),
        ("teamname0", "YOUR TEAM"),
        ("teamname1", "OPPONENTS"),
    ]
    for i in range(10):
        pares += [
            ("playerid", str(i + 1)),
            ("playername", azar.choice(["BearF99", "Ñandú", "x" * 40, "", "a b", "🙂"])),
            ("team", str(0 if i < 5 else 1)),
            ("heroname", str(azar.choice(operadores))),
            ("alliance", str(azar.randint(0, 1))),
        ]
    pares += [("id", "match-sintetico"), ("startingteamscore0", "0"), ("startingteamscore1", "0"),
              ("teamscore0", str(azar.randint(0, 5))), ("teamscore1", str(azar.randint(0, 5)))]
    cuerpo = b"".join(cadena_cabecera(k.encode()) + cadena_cabecera(v.encode()) for k, v in pares)
    # la firma, un esquema de versionado y dos tiras de siete nulos (read_header_magic)
    return b"dissect" + b"\x01\x02" + b"\x00" * 7 + b"\x03" + b"\x00" * 7 + cuerpo


def _cadena(texto: str) -> bytes:
    crudo = texto.encode("utf-8")
    return bytes([len(crudo) % 256]) + crudo


def baja(azar: random.Random, constantes) -> bytes:
    """Un evento de baja con la forma de Y9S1 update 3 en adelante.

    Sin esto la telemetria al azar casi nunca arma un kill y el fuzz no
    llega a `match_feedback`, `stats` ni `round_end`.
    """
    nombres = ["BearF99", "Chamo", "Seba", "Thorn.exe", "Kaid_", "", "Ñandú"]
    return (
        b"\x59\x34\xe5\x8b\x04" + bytes(azar.getrandbits(8) for _ in range(38)) + b"\x00"
        + constantes.KILL_INDICATOR + _cadena(azar.choice(nombres)) + bytes(15)
        + _cadena(azar.choice(nombres)) + bytes(56) + bytes([azar.randint(0, 1)])
    )


def telemetria(azar: random.Random, patrones: list[bytes], constantes=None) -> bytes:
    partes = []
    for _ in range(azar.randint(5, 60)):
        if constantes is not None and azar.random() < 0.3:
            partes.append(baja(azar, constantes))
            continue
        partes.append(azar.choice(patrones))
        partes.append(bytes(azar.getrandbits(8) for _ in range(azar.randint(0, 90))))
    return b"".join(partes)


def comprimir(datos: bytes) -> bytes:
    import zstandard

    return zstandard.ZstdCompressor().compress(datos)


def generar(azar: random.Random, constantes, patrones: list[bytes]) -> tuple[str, bytes]:
    """Un caso: (nombre del generador, bytes)."""
    base = cabecera(azar, constantes) + comprimir(telemetria(azar, patrones, constantes))
    tipo = azar.choice(
        ["valido", "cortado", "bits", "cabecera_rara", "tamano_miente", "basura", "zstd_viejo", "frames", "vacio"]
    )
    if tipo == "valido":
        return tipo, base
    if tipo == "cortado":
        return tipo, base[: azar.randint(0, len(base))]
    if tipo == "bits":
        b = bytearray(base)
        for _ in range(azar.randint(1, 20)):
            i = azar.randrange(len(b))
            b[i] ^= 1 << azar.randrange(8)
        return tipo, bytes(b)
    if tipo == "cabecera_rara":
        raro = azar.choice([b"abc", b"-1", b"99999999999999999999999", b"\xff\xfe", b"1e9", b" 3", b""])
        clave = azar.choice([b"playerid", b"team", b"code", b"recordingplayerid", b"teamscore1", b"roundnumber"])
        malo = cadena_cabecera(clave) + cadena_cabecera(raro)
        return tipo, b"dissect" + b"\x01\x02" + b"\x00" * 7 + b"\x03" + b"\x00" * 7 + malo + base[30:]
    if tipo == "tamano_miente":
        b = bytearray(base)
        for _ in range(azar.randint(1, 5)):
            pos = b.find(b"\x00" * 7, azar.randrange(len(b)))
            if pos > 0:
                b[pos - 1] = azar.randint(0, 255)
        return tipo, bytes(b)
    if tipo == "basura":
        return tipo, bytes(azar.getrandbits(8) for _ in range(azar.randint(0, 2000)))
    if tipo == "zstd_viejo":
        # formato anterior a Y8S4: todo el archivo es un frame zstd
        return tipo, comprimir(cabecera(azar, constantes) + telemetria(azar, patrones, constantes))
    if tipo == "frames":
        extra = b"".join(comprimir(telemetria(azar, patrones, constantes)) for _ in range(azar.randint(1, 4)))
        return tipo, base + extra + b"\x28\xb5\x2f\xfd" + b"\x00" * azar.randint(0, 30)
    return tipo, b""


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--casos", type=int, default=400)
    ap.add_argument("--semilla", type=int, default=7)
    ap.add_argument("--salida", type=Path)
    ap.add_argument("--autoprueba", action="store_true")
    args = ap.parse_args()

    sys.path.insert(0, str(repo_raiz() / "backend"))
    import logging

    logging.disable(logging.CRITICAL)
    from pydissect import constants, events
    from pydissect.errors import DissectError
    from pydissect.match import round_to_dict
    from pydissect.reader import Reader

    if args.autoprueba:
        # Un listener que revienta ante ciertos bytes: el fuzz tiene que
        # encontrarlo. Es la violacion que dice detectar.
        original = events.read_match_feedback

        def roto(r):
            if r.b[r.offset:r.offset + 1] in (b"\x00", b"\x01", b"\x02", b"\x03"):
                raise FallaDeAutoprueba("listener roto a proposito")
            return original(r)

        events.read_match_feedback = roto

    # Lo que los generadores necesitan del parser: versiones, mapas,
    # operadores y el indicador de baja, que vive en events.
    contexto = types.SimpleNamespace(**{k: v for k, v in vars(constants).items() if not k.startswith("__")})
    contexto.KILL_INDICATOR = events.KILL_INDICATOR
    constants = contexto
    sonda = Reader(cabecera(random.Random(0), constants) + comprimir(b"x"))
    patrones = list(sonda._queries)
    azar = random.Random(args.semilla)
    signal.signal(signal.SIGALRM, _alarma)
    hallazgos: dict[tuple[str, str], list] = {}
    limpios = 0
    for n in range(args.casos):
        nombre, datos = generar(azar, constants, patrones)
        signal.alarm(LIMITE_SEGUNDOS)
        t0 = time.perf_counter()
        try:
            r = Reader(datos)
            r.read()
            round_to_dict(r)
        except DissectError:
            limpios += 1
        except Exception as exc:  # cualquier otra cosa es el hallazgo
            marco = traceback.extract_tb(exc.__traceback__)[-1]
            clave = (type(exc).__name__, f"{Path(marco.filename).name}:{marco.lineno}")
            caso = hallazgos.setdefault(clave, [0, str(exc)[:120], nombre, datos, n])
            caso[0] += 1
            if len(datos) < len(caso[3]):
                caso[2], caso[3], caso[4] = nombre, datos, n
        finally:
            signal.alarm(0)
        if time.perf_counter() - t0 > LIMITE_SEGUNDOS:
            hallazgos.setdefault(("Lento", nombre), [0, f"{time.perf_counter() - t0:.1f} s", nombre, datos, n])[0] += 1

    if args.autoprueba:
        vio = any(k[0] == "FallaDeAutoprueba" for k in hallazgos)
        print("AUTOPRUEBA_OK: el fuzz ve un listener que revienta" if vio else "AUTOPRUEBA_FALLA: el listener roto paso")
        return 0 if vio else 1

    for (tipo, lugar), (veces, mensaje, gen, datos, n) in sorted(hallazgos.items(), key=lambda kv: -kv[1][0]):
        repro = ""
        if args.salida:
            args.salida.mkdir(parents=True, exist_ok=True)
            archivo = args.salida / f"{tipo}-{lugar.replace(':', '-')}.bin"
            archivo.write_bytes(datos)
            repro = (
                f" | repro: cd backend && python3 -c \"from pydissect.reader import Reader; "
                f"r = Reader(open('{archivo}', 'rb').read()); r.read()\""
            )
        print(f"HALLAZGO {tipo} en {lugar}: {mensaje} ({veces} casos; ej: {gen}, caso {n}, {len(datos)} bytes){repro}")
    if hallazgos:
        print(f"FUZZ_FALLA: {len(hallazgos)} hallazgos distintos en {args.casos} casos")
        return 1
    print(f"FUZZ_OK ({args.casos} casos, {limpios} rechazos limpios)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
