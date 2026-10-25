"""Prueba de mutacion sobre las lineas que cambio una rama.

Revisor y QA ya mutaban a mano ("~19 mutaciones sobre copia", "3 mutaciones,
las 3 caen"), cada vez distinto y sin dejar como repetirlo. Esto lo hace igual
cada vez: toma las lineas de un archivo que difieren de `--base` (o las que se
le digan), les aplica mutaciones simples de a una, corre el comando de tests
y cuenta las que sobreviven. Un mutante vivo es un test que no prueba lo que
dice, o un caso que ningun test mira.

Uso (desde la raiz del repo):
    git show $EQUIPO_REF:scripts/equipo-dev/mutar.py | python3 - \\
        --archivo backend/replays/analytics/metrics.py \\
        --comando "cd backend && python3 manage.py test tests.test_metrics" \\
        [--base origin/main | --lineas 40-80] [--max 30] [--timeout 300]
    ... | python3 - --autoprueba
El archivo se restaura siempre (tambien con Ctrl-C); si una corrida anterior
murio a mitad, el respaldo queda en `<archivo>.mutar-respaldo` y esta se
niega a correr hasta que se restaure.

Salida: `MUTANTE vivo <archivo>:<linea>: <antes> -> <despues>` por
sobreviviente y al final `MUTACION_OK <m> de <n> muertos` (salida 0) o
`MUTACION_VIVOS <v> de <n>` (salida 1). La base tiene que estar en verde.
"""

from __future__ import annotations

import argparse
import os
import re
import shutil
import signal
import subprocess
import sys
import tempfile
from pathlib import Path

#: (patron, reemplazo, nombre). Se aplica una sola ocurrencia por mutante.
OPERADORES: list[tuple[str, str, str]] = [
    (r"==", "!=", "== por !="),
    (r"!=", "==", "!= por =="),
    (r"<=", "<", "<= por <"),
    (r">=", ">", ">= por >"),
    (r"(?<![<>=!-])<(?![<=])", "<=", "< por <="),
    (r"(?<![<>=!-])>(?![>=])", ">=", "> por >="),
    (r"\band\b", "or", "and por or"),
    (r"\bor\b", "and", "or por and"),
    (r"&&", "||", "&& por ||"),
    (r"\|\|", "&&", "|| por &&"),
    (r"\bTrue\b", "False", "True por False"),
    (r"\bFalse\b", "True", "False por True"),
    (r"\btrue\b", "false", "true por false"),
    (r"\bfalse\b", "true", "false por true"),
    (r"\bnot\s+", "", "quita not"),
    (r"(?<![+=])\+(?![+=])", "-", "+ por -"),
    (r"(?<![-=>])-(?![-=>])", "+", "- por +"),
    (r"(?<![\w.])(\d+)(?![\w.])", None, "constante +1"),
    (r"\breturn\s+(?!None\b)(.+)", "return None", "return por None"),
    (r"\bbreak\b", "continue", "break por continue"),
    (r"\bmax\(", "min(", "max por min"),
    (r"\bmin\(", "max(", "min por max"),
]


def repo_raiz() -> Path:
    salida = subprocess.run(["git", "rev-parse", "--show-toplevel"], capture_output=True, text=True, check=False)
    if salida.returncode != 0:
        sys.exit("no es un repo git: correr desde la raiz del repo")
    return Path(salida.stdout.strip())


def lineas_cambiadas(repo: Path, archivo: str, base: str) -> list[int]:
    diff = subprocess.run(
        ["git", "diff", "-U0", f"{base}...HEAD", "--", archivo],
        cwd=repo, capture_output=True, text=True, check=False,
    ).stdout
    # el working tree tambien cuenta: el Dev muta antes de commitear
    diff += subprocess.run(["git", "diff", "-U0", "--", archivo], cwd=repo, capture_output=True, text=True).stdout
    salida: set[int] = set()
    for m in re.finditer(r"^@@ -\d+(?:,\d+)? \+(\d+)(?:,(\d+))? @@", diff, re.M):
        inicio, largo = int(m.group(1)), int(m.group(2) or 1)
        salida.update(range(inicio, inicio + largo))
    return sorted(salida)


def es_mutable(linea: str) -> bool:
    s = linea.strip()
    if not s or s.startswith(("#", "//", "*", "/*", "import ", "from ", '"""', "'''", "@")):
        return False
    return not (s.startswith(("def ", "class ", "function ")) and s.endswith((":", "{")))


def mutantes(texto: str, numeros: list[int]):
    lineas = texto.split("\n")
    for n in numeros:
        if n < 1 or n > len(lineas) or not es_mutable(lineas[n - 1]):
            continue
        original = lineas[n - 1]
        # no mutar dentro de strings: se enmascaran antes de buscar
        mascara = re.sub(r"(\"[^\"\\n]*\"|'[^'\\n]*')", lambda m: "\0" * len(m.group(0)), original)
        # ni dentro de un comentario al final de la linea (# o //)
        for marca in ("#", "//"):
            i = mascara.find(marca)
            if i >= 0:
                mascara = mascara[:i] + "\0" * (len(mascara) - i)
        for patron, reemplazo, nombre in OPERADORES:
            m = re.search(patron, mascara)
            if not m:
                continue
            nuevo_valor = str(int(m.group(1)) + 1) if reemplazo is None else reemplazo
            mutada = original[: m.start()] + nuevo_valor + original[m.end():]
            if mutada == original:
                continue
            copia = list(lineas)
            copia[n - 1] = mutada
            yield n, original.strip(), mutada.strip(), nombre, "\n".join(copia)


def purgar_bytecode(ruta: Path) -> None:
    """Borra el .pyc del modulo mutado.

    Python valida el .pyc por fecha (en segundos) y tamano de la fuente: un
    mutante del mismo largo que el original, escrito y restaurado en el mismo
    segundo, dejaba el .pyc del mutante como valido y los tests de la fuente
    ya restaurada fallaban sin que `git diff` mostrara nada.
    """
    for pyc in ruta.parent.glob(f"__pycache__/{ruta.stem}.*.pyc"):
        pyc.unlink(missing_ok=True)


def correr(comando: str, cwd: Path, timeout: int) -> bool:
    entorno = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
    try:
        r = subprocess.run(comando, shell=True, cwd=cwd, capture_output=True, timeout=timeout, env=entorno)
    except subprocess.TimeoutExpired:
        return False  # un mutante que cuelga los tests esta muerto
    return r.returncode == 0


def mutar(repo: Path, archivo: str, comando: str, numeros: list[int], maximo: int, timeout: int) -> int:
    ruta = repo / archivo
    respaldo = ruta.with_name(ruta.name + ".mutar-respaldo")
    if respaldo.exists():
        print(f"MUTACION_ABORTA: existe {respaldo}: una corrida anterior murio. Restaurar con: mv '{respaldo}' '{ruta}'")
        return 2
    original = ruta.read_text(encoding="utf-8")
    purgar_bytecode(ruta)
    if not correr(comando, repo, timeout):
        print(f"MUTACION_ABORTA: la base no esta en verde con: {comando}")
        return 2
    shutil.copy2(ruta, respaldo)

    def restaurar(*_):
        ruta.write_text(original, encoding="utf-8")
        purgar_bytecode(ruta)
        respaldo.unlink(missing_ok=True)

    previos = {s: signal.signal(s, lambda *a: (restaurar(), sys.exit(130))) for s in (signal.SIGINT, signal.SIGTERM)}
    vivos = muertos = 0
    try:
        for n, antes, despues, nombre, texto in mutantes(original, numeros):
            if vivos + muertos >= maximo:
                break
            ruta.write_text(texto, encoding="utf-8")
            purgar_bytecode(ruta)
            if correr(comando, repo, timeout):
                vivos += 1
                print(f"MUTANTE vivo {archivo}:{n}: {antes} -> {despues} ({nombre})")
            else:
                muertos += 1
    finally:
        restaurar()
        for s, h in previos.items():
            signal.signal(s, h)
    total = vivos + muertos
    if total == 0:
        print("MUTACION_SIN_MUTANTES: ninguna linea elegida se puede mutar")
        return 0
    if vivos:
        print(f"MUTACION_VIVOS {vivos} de {total}")
        return 1
    print(f"MUTACION_OK {muertos} de {total} muertos")
    return 0


def autoprueba() -> int:
    """Un modulo con un test que mira un caso y no el otro: tiene que quedar vivo un mutante.

    Ademas `LIMITE = 5` -> `LIMITE = 6` es un mutante del mismo largo: despues
    de la corrida, importar el modulo restaurado tiene que dar 5 (sin .pyc
    viejo del mutante).
    """
    with tempfile.TemporaryDirectory(prefix="mutar-") as d:
        repo = Path(d)
        (repo / "calc.py").write_text(
            "LIMITE = 5\n\n\ndef mayor(a, b):\n    if a >= b:  # a == b tambien\n        return a\n    return b\n",
            encoding="utf-8",
        )
        (repo / "prueba.py").write_text(
            "from calc import LIMITE, mayor\nassert LIMITE == 5\nassert mayor(3, 1) == 3\nassert mayor(1, 3) == 3\n",
            encoding="utf-8",
        )
        cmd = f"{sys.executable} prueba.py"
        # El test no prueba el empate: `>=` por `>` sobrevive; `return a` por None
        # muere; el `==` del comentario no se muta (seria un vivo falso).
        subprocess.run(cmd, shell=True, cwd=repo, check=False)  # deja un .pyc del original
        codigo = mutar(repo, "calc.py", cmd, [1, 5, 6], 10, 30)
        intacto = (repo / "calc.py").read_text(encoding="utf-8").startswith("LIMITE = 5\n")
        # Determinista: ningun .pyc del modulo sobrevive a la corrida (el de un
        # mutante del mismo largo pasaria por valido si cae en el mismo segundo).
        sin_pyc = not list(repo.glob("__pycache__/calc.*.pyc"))
        sano = sin_pyc and subprocess.run(cmd, shell=True, cwd=repo, check=False).returncode == 0
        if codigo == 1 and intacto and sano and not (repo / "calc.py.mutar-respaldo").exists():
            print("AUTOPRUEBA_OK: un mutante vivo se reporta y el archivo y su bytecode quedan como estaban")
            return 0
        print(f"AUTOPRUEBA_FALLA: codigo={codigo} intacto={intacto} sano={sano}")
        return 1


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--archivo")
    ap.add_argument("--comando")
    ap.add_argument("--base", default="origin/main")
    ap.add_argument("--lineas", help="rango A-B; si no, las que difieren de --base")
    ap.add_argument("--max", type=int, default=30)
    ap.add_argument("--timeout", type=int, default=300)
    ap.add_argument("--autoprueba", action="store_true")
    args = ap.parse_args()
    if args.autoprueba:
        return autoprueba()
    if not args.archivo or not args.comando:
        ap.error("--archivo y --comando son obligatorios")
    repo = repo_raiz()
    if args.lineas:
        a, _, b = args.lineas.partition("-")
        numeros = list(range(int(a), int(b or a) + 1))
    else:
        numeros = lineas_cambiadas(repo, args.archivo, args.base)
    if not numeros:
        print(f"MUTACION_SIN_MUTANTES: {args.archivo} no cambia respecto de {args.base}")
        return 0
    return mutar(repo, args.archivo, args.comando, numeros, args.max, args.timeout)


if __name__ == "__main__":
    sys.exit(main())
