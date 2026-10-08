"""Lectura y escritura del `.env`.

El `.env` es el unico lugar de la configuracion: lo que se cambia en la pagina
Ajustes se escribe aca y no en un archivo aparte, para que no haya dos fuentes
que se contradigan. Por eso la escritura respeta lo que el usuario puso a mano:
los comentarios, el orden y las otras claves quedan igual; solo cambia la linea
de la clave tocada.

Sin Django a proposito: lo importa `settings.py` antes de que exista Django.
"""

from __future__ import annotations

import os
import re
from pathlib import Path

_CLAVE = re.compile(r"^[A-Z_][A-Z0-9_]*$")


class ValorInvalido(ValueError):
    """Un valor que no se puede escribir en una linea del `.env`."""


def _clave_de(linea: str) -> str | None:
    """La clave de una linea `CLAVE=valor`, o None si es comentario o basura."""
    linea = linea.strip()
    if not linea or linea.startswith("#") or "=" not in linea:
        return None
    return linea.partition("=")[0].strip()


def leer(ruta: Path) -> dict[str, str]:
    """Pares clave -> valor del archivo. Sin archivo, vacio.

    Si una clave aparece dos veces gana la primera, que es lo que hace
    `settings.py` al cargarlo con `setdefault`.
    """
    try:
        texto = Path(ruta).read_text(encoding="utf-8")
    except FileNotFoundError:
        return {}
    salida: dict[str, str] = {}
    for linea in texto.splitlines():
        clave = _clave_de(linea)
        if clave is None or clave in salida:
            continue
        valor = linea.partition("=")[2].strip().strip('"').strip("'")
        salida[clave] = valor
    return salida


def escribir(ruta: Path, cambios: dict[str, str | None]) -> None:
    """Fija o borra claves. `None` borra la linea, que es volver al default.

    Valida todo antes de tocar el archivo, y lo reemplaza de una vez: un corte
    a la mitad no puede dejar un `.env` partido.
    """
    for clave, valor in cambios.items():
        if not _CLAVE.match(clave):
            raise ValorInvalido(f"clave invalida: {clave!r}")
        # un salto de linea en el valor colaria una clave nueva en el archivo
        if valor is not None and any(c in valor for c in "\r\n\0"):
            raise ValorInvalido(f"{clave} no puede tener saltos de linea")

    ruta = Path(ruta)
    try:
        lineas = ruta.read_text(encoding="utf-8").splitlines()
    except FileNotFoundError:
        lineas = []

    pendientes = dict(cambios)
    salida: list[str] = []
    for linea in lineas:
        clave = _clave_de(linea)
        if clave not in cambios:
            salida.append(linea)
            continue
        if clave in pendientes:
            valor = pendientes.pop(clave)
            if valor is not None:
                salida.append(f"{clave}={valor}")
        # una segunda aparicion de la clave se descarta: confundiria a quien
        # abra el archivo, porque esa linea no tiene efecto

    nuevas = [f"{clave}={valor}" for clave, valor in pendientes.items() if valor is not None]
    if nuevas:
        if salida and salida[-1].strip():
            salida.append("")
        salida.extend(nuevas)

    ruta.parent.mkdir(parents=True, exist_ok=True)
    temporal = ruta.with_name(ruta.name + ".tmp")
    temporal.write_text("\n".join(salida) + "\n", encoding="utf-8")
    os.replace(temporal, ruta)
