"""A cuantas rondas se gana cada tipo de partida, para saber cuando hay match point.

Es una regla del juego y no algo que el `.rec` diga, por eso vive aca y no en
`pydissect/`. No importa Django: las consultas viven en `aggregates.py` y
leen de aca que marcadores son match point.

Solo entra una regla con fuente citable. Un tipo sin regla no se adivina: sus
rondas van a "sin regla" en vez de contarse como rondas normales.
"""

from __future__ import annotations

from pydissect.constants import Y9S4

#: Por tipo de partida, sus reglas ordenadas por `desde` (code_version). Sin
#: prorroga, `prorroga_hasta == para_ganar`. Antes de Y9S4 no hay marcador por
#: ronda, asi que una regla mas vieja no cambiaria nada.
REGLAS: dict[str, tuple[dict, ...]] = {
    # Primero a 4; con 3-3 hay prorroga y gana el primero a 5. Fuente: Dexerto,
    # "Rainbow Six Siege ranks explained" (actualizado 2024-06-04),
    # https://www.dexerto.com/rainbow-six/rainbow-six-siege-ranked-all-ranks-climb-fast-tips-1627443/
    "Ranked": ({"desde": Y9S4, "para_ganar": 4, "prorroga_hasta": 5},),
}

#: Orden fijo de los estados, el mismo de las filas de `by_match_point`.
ESTADOS = ("mine", "theirs", "both", "normal")


def regla_para(match_type: str, code_version: int, reglas: dict | None = None) -> dict | None:
    """La regla de mayor `desde` que ya valia en esa version, o None."""
    candidatas = [
        r for r in (reglas if reglas is not None else REGLAS).get(match_type, ())
        if r["desde"] <= code_version
    ]
    return max(candidatas, key=lambda r: r["desde"]) if candidatas else None


def objetivo(propio: int, ajeno: int, regla: dict) -> int:
    """Rondas que hacen falta para ganar con este marcador.

    La prorroga arranca cuando los dos quedan a una ronda de la regla normal:
    desde ahi el objetivo sube y el empate deja de ser match point.
    """
    if min(propio, ajeno) >= regla["para_ganar"] - 1:
        return regla["prorroga_hasta"]
    return regla["para_ganar"]


def cierra(propio: int, ajeno: int, regla: dict) -> bool:
    """Si ganar la ronda con este marcador gana la partida."""
    return propio + 1 >= objetivo(propio, ajeno, regla)


def estado(mio: int, suyo: int, regla: dict) -> str:
    yo, el = cierra(mio, suyo, regla), cierra(suyo, mio, regla)
    if yo and el:
        return "both"
    if yo:
        return "mine"
    if el:
        return "theirs"
    return "normal"


def tramos(regla: dict) -> dict[str, list[tuple[int, int]]]:
    """Los marcadores previos a una ronda posibles con la regla, por estado.

    Un marcador fuera de rango (alguien ya gano) no aparece: la consulta lo
    deja en `normal`, que es lo que queda despues de sacar los demas.
    """
    salida: dict[str, list[tuple[int, int]]] = {nombre: [] for nombre in ESTADOS}
    for mio in range(regla["prorroga_hasta"]):
        for suyo in range(regla["prorroga_hasta"]):
            if max(mio, suyo) >= objetivo(mio, suyo, regla):
                continue
            salida[estado(mio, suyo, regla)].append((mio, suyo))
    return salida
