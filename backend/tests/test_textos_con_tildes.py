"""Guardia de las tildes en los textos que arma el backend y la UI muestra tal cual.

La narrativa de cada ronda y los consejos del Coach llegan como texto hecho:
el frontend no los toca, asi que una palabra sin tilde en estos modulos se ve
igual en pantalla. Se recorren los literales con `ast` y no con grep para no
confundir comentarios, docstrings ni claves (`"fatiga-sesion"`) con texto.
"""

from __future__ import annotations

import ast
import re
import tempfile
from pathlib import Path

from django.test import SimpleTestCase

from replays.analytics import coach, narrative

# Solo palabras que sin tilde no existen en espanol (o casi): `esta`, `que`,
# `donde`, `el`, `tu` o `como` son ambiguas y darian falsos positivos.
SIN_TILDE = (
    "despues mas tambien sesion ultimo ultimas angulo angulos informacion "
    "ejecucion mecanica mecanico historico fijate priorizalo aprendetelo manten "
    "aprovechala camara explicitamente todavia mato murio perdio abrio arranco "
    "vengo cerro paro eliminacion accion jugo llego quedandote ahi"
).split()
PATRON = re.compile(r"\b(" + "|".join(SIN_TILDE) + r")\b", re.IGNORECASE)


def _docstrings(arbol):
    ids = set()
    for nodo in ast.walk(arbol):
        if isinstance(nodo, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
            cuerpo = nodo.body
            if cuerpo and isinstance(cuerpo[0], ast.Expr) and isinstance(cuerpo[0].value, ast.Constant):
                ids.add(id(cuerpo[0].value))
    return ids


def palabras_sin_tilde(ruta):
    arbol = ast.parse(Path(ruta).read_text(encoding="utf-8"))
    saltar = _docstrings(arbol)
    hallazgos = []
    for nodo in ast.walk(arbol):
        if not (isinstance(nodo, ast.Constant) and isinstance(nodo.value, str)):
            continue
        # sin espacio es una clave o un identificador, no una frase
        if id(nodo) in saltar or " " not in nodo.value:
            continue
        for encontrada in PATRON.finditer(nodo.value):
            hallazgos.append(f"{Path(ruta).name}:{nodo.lineno} {encontrada.group(0)!r}")
    return hallazgos


class TextosConTildesTests(SimpleTestCase):
    def test_los_textos_del_coach_y_la_narrativa_no_pierden_las_tildes(self):
        hallazgos = palabras_sin_tilde(coach.__file__) + palabras_sin_tilde(narrative.__file__)
        self.assertEqual(hallazgos, [], "\n".join(hallazgos))

    def test_la_guardia_encuentra_una_palabra_sin_tilde(self):
        # sin este caso, un patron roto pasaria el test de arriba sin mirar nada
        self.assertTrue(PATRON.search("te mato Rival. Nadie la vengo."))
        self.assertIsNone(PATRON.search("te mató Rival. Nadie la vengó."))

    def test_el_recorrido_encuentra_el_literal_y_salta_docstrings_y_claves(self):
        # el control de arriba prueba la regex; este prueba que `ast` visita los literales
        fuente = (
            '"""Docstring que dice mato y no cuenta."""\n'
            'CLAVE = "fatiga-sesion"\n'
            'def f(x):\n'
            '    """Otra docstring con despues."""\n'
            '    return f"{x} te mato. Nadie la vengó."\n'
        )
        with tempfile.TemporaryDirectory() as carpeta:
            ruta = Path(carpeta) / "modulo.py"
            ruta.write_text(fuente, encoding="utf-8")
            self.assertEqual(palabras_sin_tilde(ruta), ["modulo.py:5 'mato'"])
