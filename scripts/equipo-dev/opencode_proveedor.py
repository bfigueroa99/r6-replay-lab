#!/usr/bin/env python3
"""El proveedor de OmniRoute para un turno del equipo en OpenCode (`scripts/equipo-dev/opencode.sh`).

`opencode.sh` corre `opencode run --command equipo-dev -m <proveedor/modelo>`, y el modelo por
defecto es `omniroute/auto`: el combo automatico de OmniRoute, el gateway local que reparte las
llamadas entre los proveedores conectados (http://localhost:20128). OpenCode solo conoce un
proveedor si esta en su configuracion; esto arma el `OPENCODE_CONFIG_CONTENT` que lo agrega para
ese turno, sin escribir nada en disco.

Que imprime, segun el modelo y el entorno:
- modelo de otro proveedor (`anthropic/...`): nada; OpenCode usa lo suyo.
- OpenCode ya tiene "omniroute" en su configuracion global (lo deja `omniroute setup-opencode`) y
  no hay `OMNIROUTE_URL`: solo el modelo, sumado a su lista (OpenCode mezcla las configuraciones).
- si no: el proveedor entero, `@ai-sdk/openai-compatible` en `OMNIROUTE_URL` (con un solo `/v1`)
  y la clave como `{env:OMNIROUTE_API_KEY}` (OpenCode la lee del entorno: nunca queda escrita) o,
  sin ella, `sk_omniroute`, la que acepta OmniRoute cuando no exige clave.
Lo que ya traia `OPENCODE_CONFIG_CONTENT` se conserva. Sin dependencias: solo la stdlib.

Uso:
    python3 scripts/equipo-dev/opencode_proveedor.py omniroute/auto   # el JSON por stdout (o nada)

Salida: 0 | 2 uso invalido o `OPENCODE_CONFIG_CONTENT` que no es JSON.
"""
import json
import os
import re
import sys
from pathlib import Path

OMNIROUTE_URL = "http://localhost:20128"
CLAVE_LOCAL = "sk_omniroute"
# Un objeto "omniroute" dentro de la configuracion: basta para saber que el proveedor esta, sin
# parsear JSONC (comentarios, comas finales) a mano.
PROVEEDOR_RE = re.compile(r'"omniroute"\s*:\s*\{')


def url_v1(url):
    """La URL de OmniRoute con un solo `/v1` al final, se escriba como se escriba."""
    base = re.sub(r"/v1$", "", url.strip().rstrip("/"))
    return base + "/v1"


def configs_globales(env):
    """Donde busca OpenCode su configuracion global (y la que senala `OPENCODE_CONFIG`)."""
    rutas = []
    if env.get("OPENCODE_CONFIG"):
        rutas.append(Path(env["OPENCODE_CONFIG"]))
    base = Path(env.get("XDG_CONFIG_HOME") or Path(env.get("HOME", "~")).expanduser() / ".config") / "opencode"
    rutas += [base / n for n in ("opencode.json", "opencode.jsonc", "config.json")]
    return rutas


def ya_configurado(env):
    for ruta in configs_globales(env):
        try:
            if PROVEEDOR_RE.search(ruta.read_text(encoding="utf-8", errors="replace")):
                return True
        except OSError:
            continue
    return False


def config(modelo, env, configurado):
    """El `OPENCODE_CONFIG_CONTENT` para `modelo`, o None si no hace falta."""
    proveedor, _, ident = modelo.partition("/")
    if proveedor != "omniroute":
        return None
    previo = json.loads(env["OPENCODE_CONFIG_CONTENT"]) if env.get("OPENCODE_CONFIG_CONTENT") else {}
    modelos = {ident: {"name": ident}}
    if configurado and not env.get("OMNIROUTE_URL"):
        omniroute = {"models": modelos}
    else:
        clave = "{env:OMNIROUTE_API_KEY}" if env.get("OMNIROUTE_API_KEY") else CLAVE_LOCAL
        omniroute = {
            "npm": "@ai-sdk/openai-compatible",
            "name": "OmniRoute",
            "options": {"baseURL": url_v1(env.get("OMNIROUTE_URL") or OMNIROUTE_URL), "apiKey": clave},
            "models": modelos,
        }
    proveedores = dict(previo.get("provider") or {})
    proveedores["omniroute"] = omniroute
    return json.dumps({**previo, "provider": proveedores}, ensure_ascii=False)


def main(argv, env=os.environ):
    if len(argv) != 1 or not re.fullmatch(r"[^/\s]+/\S+", argv[0]):
        print("uso: opencode_proveedor.py <proveedor/modelo>", file=sys.stderr)
        return 2
    try:
        salida = config(argv[0], env, ya_configurado(env))
    except json.JSONDecodeError as err:
        print(f"OPENCODE_CONFIG_CONTENT no es JSON: {err}", file=sys.stderr)
        return 2
    if salida:
        print(salida)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
