"""Barrido de la API con parametros borde, sin servidor ni red.

Recorre **todas** las rutas de `replays/urls.py` (una ruta nueva entra sola)
con el test client de Django, sobre una base vacia y sobre la de
`manage.py seed_demo`, cada una con una lista fija de parametros borde y
combinaciones al azar con semilla fija. Los POST van con cuerpos rotos,
tipos de contenido equivocados y valores fuera de rango. Todo corre en un
directorio temporal: base, `.env`, overrides y copias de seguridad propias.

Las fichas 32 y 33 salieron de barridos a mano que no dejaron script; el PO
del 2026-10-10 repitio "19 endpoints con ~50 parametros borde" y tampoco.
Esto es ese barrido, repetible.

Uso (desde la raiz del repo, con el entorno instalado):
    git show $EQUIPO_REF:scripts/equipo-dev/barrido_api.py | python3 - [opciones]
    python3 scripts/equipo-dev/barrido_api.py --base ambas --semilla 7
Opciones: --base vacia|demo|ambas (ambas), --rapido (solo la lista fija),
--semilla N (7), --combinaciones N por ruta (12), --autoprueba (inyecta una
ruta que revienta y otra que miente JSON, y verifica que el barrido las vea).

Salida: una linea por hallazgo, `HALLAZGO <tipo> <metodo> <url>: <detalle>`
(tipo: 500, excepcion, json, red, lento), las 3 rutas mas lentas, y al final
`BARRIDO_OK (<n> pedidos, <m> rutas)` (salida 0) o `BARRIDO_FALLA: <k>
hallazgos en <n> pedidos` (salida 1). Con --autoprueba: `AUTOPRUEBA_OK` o
`AUTOPRUEBA_FALLA`.
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import random
import socket
import subprocess
import sys
import tempfile
import time
import traceback
from pathlib import Path

LENTO_SEGUNDOS = 2.0

#: Parametros borde de la query string. Cada uno vino de un bug real o de la
#: forma en que el frontend y un usuario escriben a mano la URL.
PARAMETROS: list[dict[str, str]] = [
    {},
    {"since": "foo"},
    {"until": "foo"},
    {"since": "2026-01-01T00:00Z"},
    {"until": "2026-01-01T00:00:00+14:00"},
    {"since": "0001-01-01T00:00Z"},
    {"until": "9999-12-31T23:59:59-12:00"},
    {"since": "2026-13-45"},
    {"since": "2026-02-01", "until": "2025-01-01"},
    {"days": "99999999999"},
    {"days": "-1"},
    {"days": "0"},
    {"days": "1e3"},
    {"days": "NaN"},
    {"page": "-1"},
    {"page": "abc"},
    {"limit": "-1"},
    {"limit": "0"},
    {"limit": "99999999999999999999999"},
    {"offset": "-5"},
    {"offset": "abc"},
    {"offset": "99999999999"},
    {"min_rounds": "-1"},
    {"min_rounds": "abc"},
    {"min_rounds": "0"},
    {"min_duels": "0"},
    {"n": "0"},
    {"n": "999999"},
    {"by": "days"},
    {"by": "x"},
    {"side": ""},
    {"side": "Attack"},
    {"side": "foo"},
    {"map": "\x00"},
    {"map": "' OR 1=1 --"},
    {"operator": ";"},
    {"operator": "Ñandú ñ 🙂"},
    {"site": "A" * 5000},
    {"session": "x"},
    {"session": "-1"},
    {"session": "99999"},
    {"ranked_only": "2"},
    {"ranked_only": "true"},
    {"match_type": "x"},
    {"table": ""},
    {"table": "maps", "sep": ";"},
    {"table": "../../etc/passwd"},
    {"table": "maps", "since": "foo", "days": "-1"},
]
#: Valores sueltos para las combinaciones al azar.
POZO = {
    "since": ["foo", "2026-01-01", "2026-01-01T00:00Z", "0001-01-01", ""],
    "until": ["foo", "2026-12-31", "9999-12-31", ""],
    "days": ["-1", "0", "7", "99999999999", "x"],
    "side": ["Attack", "Defense", "", "x"],
    "map": ["", "x", "\x00", "clubhouse"],
    "operator": ["Ash", "", "ñ", "x" * 300],
    "site": ["", "A", "x"],
    "session": ["", "1", "x", "-3"],
    "ranked_only": ["1", "0", "si", "x"],
    "match_type": ["", "Ranked", "x"],
    "min_rounds": ["-1", "1", "100000", "x"],
    "limit": ["-1", "1", "200", "x"],
    "offset": ["-1", "0", "100000000", "x"],
    "n": ["0", "1", "365", "x"],
    "by": ["days", "matches", "x"],
    "table": ["", "maps", "x"],
}
#: Cuerpos para los POST. (content_type, cuerpo)
CUERPOS: list[tuple[str, str]] = [
    ("application/json", ""),
    ("application/json", "{}"),
    ("application/json", "{"),
    ("application/json", "[]"),
    ("application/json", '"x"'),
    ("application/json", "null"),
    ("application/json", json.dumps({"a": {"b": {"c": [1] * 1000}}})),
    ("text/plain", "{}"),
    ("application/x-www-form-urlencoded", "a=1"),
]
CUERPOS_POR_RUTA: dict[str, list[dict]] = {
    "overrides": [
        {"maps": {"1": "x"}},
        {"maps": {"abc": "x"}},
        {"operators": {"1": "A" * 1000}},
        {"maps": "x"},
        {"operators": {"-1": ""}},
        {"maps": {"99999999999999999999": "Ñandú"}},
    ],
    "settings": [
        {"replay_dir": "/no/existe"},
        {"replay_dir": 123},
        {"replay_dir": ""},
        {"replay_dir": "a\nB=1"},
        {"auto_import": "maybe"},
        {"auto_import": False},
        {"zzz": 1},
    ],
    "backup": [{}],
    "import": [{}],
}


def repo_raiz() -> Path:
    salida = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"], capture_output=True, text=True, check=False
    )
    if salida.returncode != 0:
        sys.exit("no es un repo git: correr desde la raiz del repo")
    return Path(salida.stdout.strip())


def preparar_entorno(tmp: Path) -> None:
    """Base, datos y .env propios: nada del usuario se toca."""
    (tmp / "data").mkdir()
    (tmp / ".env").write_text(f"REPLAY_DIR={tmp / 'sin-replays'}\n", encoding="utf-8")
    os.environ.update(
        {
            "DJANGO_SETTINGS_MODULE": "config.settings",
            "SQLITE_PATH": str(tmp / "db.sqlite3"),
            "DATA_DIR": str(tmp / "data"),
            "OVERRIDES_PATH": str(tmp / "data" / "overrides.json"),
            "R6_ENV_FILE": str(tmp / ".env"),
            "AUTO_IMPORT": "false",
            "UBI_EMAIL": "",
            "UBI_PASSWORD": "",
            "DJANGO_DEBUG": "false",
            "LOG_LEVEL": "CRITICAL",
            "PYDISSECT_LOG_LEVEL": "CRITICAL",
        }
    )


class SalidaALaRed(Exception):
    pass


def cerrar_la_red() -> None:
    """Cualquier conexion fuera de localhost es un hallazgo, no un pedido real."""
    original = socket.socket.connect

    def connect(self, direccion):
        host = direccion[0] if isinstance(direccion, tuple) else str(direccion)
        if host not in ("127.0.0.1", "::1", "localhost"):
            raise SalidaALaRed(f"intento de conexion a {direccion!r}")
        return original(self, direccion)

    socket.socket.connect = connect


def rutas(urlpatterns, pks: dict[str, list[str]]) -> list[tuple[str, str]]:
    """(nombre, url) por patron; los `<int:pk>` con ids que existen y que no."""
    salida = []
    for patron in urlpatterns:
        crudo = str(patron.pattern)
        nombre = patron.name or crudo
        if "<int:pk>" in crudo:
            clave = "players" if crudo.startswith("players/") else "matches"
            for pk in pks.get(clave, []) + ["999999", "0"]:
                salida.append((nombre, "/api/" + crudo.replace("<int:pk>", pk)))
        else:
            salida.append((nombre, "/api/" + crudo))
    return salida


def barrer(cliente, lista, *, rapido: bool, semilla: int, combinaciones: int, etiqueta: str):

    hallazgos: list[str] = []
    tiempos: dict[str, float] = {}
    pedidos = 0
    azar = random.Random(semilla)

    def pedir(metodo: str, url: str, **kw):
        nonlocal pedidos
        pedidos += 1
        t0 = time.perf_counter()
        try:
            if metodo == "GET":
                r = cliente.get(url, kw.get("datos") or {})
            else:
                r = cliente.post(url, data=kw.get("cuerpo", ""), content_type=kw.get("tipo", "application/json"))
        except SalidaALaRed as exc:
            hallazgos.append(f"HALLAZGO red {metodo} {url} [{etiqueta}]: {exc}")
            return None
        except Exception as exc:  # el test client relanza la excepcion de la vista
            ultima = traceback.extract_tb(exc.__traceback__)[-1]
            hallazgos.append(
                f"HALLAZGO excepcion {metodo} {url} {kw.get('datos') or kw.get('cuerpo', '')!r} [{etiqueta}]: "
                f"{type(exc).__name__}: {exc} ({Path(ultima.filename).name}:{ultima.lineno})"
            )
            return None
        dt = time.perf_counter() - t0
        tiempos[f"{metodo} {url}"] = max(tiempos.get(f"{metodo} {url}", 0.0), dt)
        if r.status_code >= 500:
            entrada = kw.get("datos") or kw.get("cuerpo", "")
            hallazgos.append(f"HALLAZGO 500 {metodo} {url} {entrada!r} [{etiqueta}]: status {r.status_code}")
        tipo = r.get("Content-Type", "")
        if "json" in tipo:
            try:
                json.loads(r.content or b"null")
            except ValueError as exc:
                hallazgos.append(f"HALLAZGO json {metodo} {url} [{etiqueta}]: dice JSON y no lo es ({exc})")
        if dt > LENTO_SEGUNDOS:
            hallazgos.append(f"HALLAZGO lento {metodo} {url} {kw.get('datos') or ''!r} [{etiqueta}]: {dt:.1f} s")
        return r

    for nombre, url in lista:
        r = pedir("GET", url)
        acepta_post = r is not None and r.status_code == 405
        if acepta_post:
            corto = nombre.split("-")[0] if nombre else url
            for tipo, cuerpo in CUERPOS:
                pedir("POST", url, cuerpo=cuerpo, tipo=tipo)
            for clave, cuerpos in CUERPOS_POR_RUTA.items():
                if clave in url or clave == corto:
                    for c in cuerpos:
                        pedir("POST", url, cuerpo=json.dumps(c), tipo="application/json")
            if "import" in url:
                for q in ("?force=1&limit=-1", "?limit=abc", "?force=x&limit=99999"):
                    pedir("POST", url + q, cuerpo="{}", tipo="application/json")
                esperar_importacion()
            continue
        for datos in PARAMETROS:
            pedir("GET", url, datos=datos)
        if not rapido:
            claves = list(POZO)
            for _ in range(combinaciones):
                k = azar.randint(2, 4)
                datos = {c: azar.choice(POZO[c]) for c in azar.sample(claves, k)}
                pedir("GET", url, datos=datos)
            # claves repetidas: QueryDict se queda con la ultima, el codigo no deberia romper
            pedir("GET", url + "?side=Attack&side=Defense&days=1&days=x")
    return hallazgos, tiempos, pedidos


def esperar_importacion() -> None:
    """El POST de importacion lanza un hilo; se espera para no pisar la base."""
    from replays.ingest import import_job

    for _ in range(100):
        estado = import_job().as_dict()
        if not estado.get("running"):
            return
        time.sleep(0.05)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--base", choices=["vacia", "demo", "ambas"], default="ambas")
    ap.add_argument("--rapido", action="store_true")
    ap.add_argument("--semilla", type=int, default=7)
    ap.add_argument("--combinaciones", type=int, default=12)
    ap.add_argument("--autoprueba", action="store_true")
    args = ap.parse_args()

    repo = repo_raiz()
    backend = repo / "backend"
    with tempfile.TemporaryDirectory(prefix="barrido-") as d:
        tmp = Path(d)
        preparar_entorno(tmp)
        sys.path.insert(0, str(backend))
        os.chdir(backend)
        import django

        django.setup()
        from django.core.management import call_command
        from django.test import Client
        from django.test.utils import setup_test_environment

        setup_test_environment()
        # La traza ya va en el hallazgo; el log de Django la repetiria entera.
        logging.getLogger("django.request").setLevel(logging.CRITICAL)
        cerrar_la_red()
        from replays import perfil_externo

        def abrir_prohibido(*a, **k):
            raise SalidaALaRed("perfil_externo.abrir llamado durante el barrido")

        perfil_externo.abrir = abrir_prohibido

        from replays import urls as rutas_api

        if args.autoprueba:
            from django.http import HttpResponse
            from django.urls import clear_url_caches, path

            def revienta(request):
                return 1 / 0

            def miente(request):
                return HttpResponse("{no es json", content_type="application/json")

            rutas_api.urlpatterns.append(path("autoprueba-revienta/", revienta, name="autoprueba-revienta"))
            rutas_api.urlpatterns.append(path("autoprueba-miente/", miente, name="autoprueba-miente"))
            clear_url_caches()

        call_command("migrate", verbosity=0)
        cliente = Client(raise_request_exception=True)
        bases = ["vacia", "demo"] if args.base == "ambas" else [args.base]
        hallazgos: list[str] = []
        tiempos: dict[str, float] = {}
        pedidos = 0
        n_rutas = 0
        for base in bases:
            if base == "demo":
                call_command("seed_demo", "--force", verbosity=0)
            from replays.models import Match, Player

            pks = {
                "players": [str(p) for p in Player.objects.order_by("pk").values_list("pk", flat=True)[:1]],
                "matches": [str(m) for m in Match.objects.order_by("pk").values_list("pk", flat=True)[:1]],
            }
            lista = rutas(rutas_api.urlpatterns, pks)
            n_rutas = max(n_rutas, len({n for n, _ in lista}))
            if args.autoprueba:
                lista = [x for x in lista if "autoprueba" in x[1]] + lista[:2]
            h, t, n = barrer(
                cliente, lista, rapido=args.rapido or args.autoprueba, semilla=args.semilla,
                combinaciones=args.combinaciones, etiqueta=base,
            )
            hallazgos += h
            pedidos += n
            for k, v in t.items():
                tiempos[k] = max(tiempos.get(k, 0.0), v)

        if args.autoprueba:
            vio_500 = any("autoprueba-revienta" in h and "ZeroDivisionError" in h for h in hallazgos)
            vio_json = any("autoprueba-miente" in h and "HALLAZGO json" in h for h in hallazgos)
            if vio_500 and vio_json:
                print("AUTOPRUEBA_OK: el barrido ve una vista que revienta y una que miente JSON")
                return 0
            print(f"AUTOPRUEBA_FALLA: revienta={vio_500} miente={vio_json}")
            for h in hallazgos:
                print(h)
            return 1

        for h in hallazgos:
            print(h)
        for clave, seg in sorted(tiempos.items(), key=lambda kv: -kv[1])[:3]:
            print(f"MAS_LENTO {seg * 1000:.0f} ms {clave}")
        if hallazgos:
            print(f"BARRIDO_FALLA: {len(hallazgos)} hallazgos en {pedidos} pedidos")
            return 1
        print(f"BARRIDO_OK ({pedidos} pedidos, {n_rutas} rutas)")
        return 0


if __name__ == "__main__":
    sys.exit(main())
