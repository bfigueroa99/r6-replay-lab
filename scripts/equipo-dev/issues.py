#!/usr/bin/env python3
"""Issues de GitHub para el equipo de desarrollo: que hay, de quien y que toca hacer con cada uno.

El equipo tambien toma pedidos de los issues de `bfigueroa99/r6-replay-lab` (contrato comun de
los loops del dueno; el procedimiento esta en `.claude/skills/equipo-dev/issues.md`). El repo es
publico: cualquiera puede abrir un issue, y el equipo tiene permiso de push. Por eso la
clasificacion no la decide el turno a ojo sino esto, igual cada vez:

- Solo es pedido un issue abierto (no un PR) cuyo autor es `OWNER`, `MEMBER` o `COLLABORATOR`.
  De los demas salen solo los numeros: ni el titulo llega al turno, que no los ejecuta ni los
  comenta.
- El equipo escribe con la cuenta del dueno, asi que lo suyo tambien se ve como `OWNER`. Todo
  cuerpo que escribe empieza con `<!-- loop`, y un issue que empieza asi nunca es un pedido.
- La ficha manda. Un issue que una ficha viva cita en `fuente:` (papel o rama de trabajo, lo
  junta estado.sh de git) esta en curso aunque nadie lo comente: una ficha cruza seis roles y
  dura dias (44 h de mediana desde la propuesta), y un TTL sobre `updated_at` lo daria por
  abandonado y el PO lo volveria a triar. El TTL (3 h, el del candado de P8) vale solo para la
  etiqueta `loop:en-curso` sin ficha: un turno que comento y murio antes de empujarla.
- Cuando la ficha llega a dev y no queda otra viva del mismo issue (los tramos de una epica
  citan todos el mismo), el issue queda para cerrar.

Nunca sale con error por GitHub: sin gh, sin red, con la API caida o con una respuesta rara dice
`ISSUES=no se pudieron leer (<motivo>)` y `PEDIDOS=0`, y el turno sigue con su backlog. Sin
dependencias: solo la stdlib.

Uso:
    python3 scripts/equipo-dev/issues.py [--json-de ARCHIVO|-] [--fichas "N:NN:estado ..."]
        [--en-dev "NN ..."] [--ttl-horas 3] [--ahora EPOCH] [--json]
        clasifica los issues abiertos. Sin --json-de los pide a gh (EQUIPO_GH cambia el
        binario: lo usan las pruebas). --fichas son los issues que citan las fichas, con el
        estado de cada una: curso (papel o rama de trabajo), dev (ya mergeada) o descartado.
        --en-dev son los numeros de ficha que ya estan en dev (para los issues que abre el
        equipo con `humano:destraba-NN`).
    python3 scripts/equipo-dev/issues.py --comentarios ARCHIVO|-
        de una lista de comentarios (gh api .../comments, o la salida de
        mcp__github__issue_read get_comments guardada), los que cuentan: de confianza y sin
        el marcador del equipo.
    python3 scripts/equipo-dev/issues.py --humano ID [--json-de ARCHIVO|-]
        si ya existe (abierto o cerrado) el issue que el equipo abrio para `humano:ID`.
Salida: 0 siempre que pudo decir algo, tambien si GitHub fallo; 2 uso invalido.
"""
import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import time
from datetime import datetime

REPO = "bfigueroa99/r6-replay-lab"
CONFIANZA = ("OWNER", "MEMBER", "COLLABORATOR")
IGNORAR = "loop:ignorar"
EN_CURSO = "loop:en-curso"
NECESITA = "loop:necesita-humano"
# Lo que va primero entre los pedidos; despues, el mas viejo.
PRIMERO = ("bug", "prioridad")
# El candado de P8: sin commits sobre la ficha en 3 h, la sesion murio.
TTL_HORAS = 3
MARCADOR = re.compile(r"\s*<!--\s*loop\b")
HUMANO = re.compile(r"<!--\s*loop\b[^>]*?\bhumano:([a-z0-9-]+)")
ID_HUMANO = re.compile(r"[a-z0-9][a-z0-9-]{0,60}")
GH_TIMEOUT_S = 30


def plano(texto, tope):
    """Una linea, sin caracteres de control y con tope: el titulo lo escribe una persona."""
    t = re.sub(r"[\x00-\x1f\x7f]+", " ", str(texto or ""))
    t = re.sub(r"\s+", " ", t).strip()
    return t if len(t) <= tope else t[: tope - 3].rstrip() + "..."


def gh_buscar(q):
    """(datos, None) o (None, motivo). Nunca levanta: el turno sigue sin issues."""
    gh = os.environ.get("EQUIPO_GH", "gh")
    if not shutil.which(gh):
        return None, "sin gh"
    cmd = [gh, "api", "-X", "GET", "search/issues", "-f", "q=" + q, "-f", "per_page=100"]
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=GH_TIMEOUT_S)
    except subprocess.TimeoutExpired:
        return None, "gh sin respuesta en %d s" % GH_TIMEOUT_S
    except OSError as e:
        return None, "gh no arranco: %s" % plano(e, 100)
    if r.returncode != 0:
        lineas = (r.stderr or r.stdout or "").strip().splitlines()
        return None, "gh salio con %d: %s" % (r.returncode, plano(lineas[0] if lineas else "sin mensaje", 120))
    return parsear(r.stdout)


def leer_archivo(ruta):
    try:
        if ruta == "-":
            return parsear(sys.stdin.read())
        with open(ruta, encoding="utf-8") as f:
            return parsear(f.read())
    except OSError as e:
        return None, "no se pudo leer %s: %s" % (ruta, plano(e.strerror or e, 80))


def parsear(texto):
    try:
        return json.loads(texto), None
    except ValueError:
        return None, "respuesta que no es JSON"


def items_de(datos, *claves):
    """La lista de la respuesta: `items` de search, `issues` de list_issues, o una lista suelta."""
    if isinstance(datos, list):
        return datos
    if isinstance(datos, dict):
        for k in claves:
            if isinstance(datos.get(k), list):
                return datos[k]
    return None


def epoch(fecha):
    try:
        return datetime.fromisoformat(str(fecha).replace("Z", "+00:00")).timestamp()
    except ValueError:
        return None


def normalizar(it):
    """Lo que se usa de un issue, venga de search (REST) o de list_issues (MCP). None si no sirve."""
    if not isinstance(it, dict):
        return None
    n = it.get("number")
    if not isinstance(n, int) or isinstance(n, bool):
        return None
    etiquetas = []
    for e in it.get("labels") or []:
        nombre = e.get("name") if isinstance(e, dict) else e
        if isinstance(nombre, str):
            etiquetas.append(nombre)
    usuario = it.get("user") if isinstance(it.get("user"), dict) else {}
    cuerpo = it.get("body")
    return {
        "numero": n,
        "titulo": plano(it.get("title"), 100),
        "cuerpo": cuerpo if isinstance(cuerpo, str) else "",
        "autor": plano(usuario.get("login") or "?", 40),
        # list_issues del MCP no la trae: sin ella no hay confianza (issue_read get la da).
        "asociacion": str(it.get("author_association") or it.get("authorAssociation") or "DESCONOCIDA").upper(),
        "etiquetas": etiquetas,
        "creado": epoch(it.get("created_at")) or 0,
        "actualizado": epoch(it.get("updated_at")),
        "url": plano(it.get("html_url") or "https://github.com/%s/issues/%d" % (REPO, n), 120),
        "abierto": str(it.get("state") or "open").lower() == "open",
        "es_pr": bool(it.get("pull_request")),
    }


def leer_fichas(texto):
    """"N:NN:estado ..." -> {issue: {estado: [fichas]}}. Lo mal formado se ignora."""
    fichas = {}
    for tok in (texto or "").split():
        m = re.fullmatch(r"(\d+):(\d+):(curso|dev|descartado)", tok)
        if m:
            por = fichas.setdefault(int(m.group(1)), {})
            lista = por.setdefault(m.group(3), [])
            if m.group(2) not in lista:
                lista.append(m.group(2))
    return fichas


def clasificar(issues, fichas, en_dev, ahora, ttl_s):
    g = {k: [] for k in ("pedidos", "en_curso", "esperando", "cerrar", "ignorados", "sin_confianza")}
    for i in issues:
        if not i["abierto"] or i["es_pr"]:
            continue
        et = set(i["etiquetas"])
        if IGNORAR in et:
            g["ignorados"].append(i)
            continue
        if i["asociacion"] not in CONFIANZA:
            g["sin_confianza"].append(i)
            continue
        if MARCADOR.match(i["cuerpo"]):
            # Lo abrio el equipo (cola humana). La persona lo destraba quitando la etiqueta;
            # una ficha que espera su merge se destraba tambien mergeando, aunque no la quite.
            h = HUMANO.search(i["cuerpo"])
            hid = h.group(1) if h else "-"
            d = re.fullmatch(r"destraba-(\d+)", hid)
            if d and d.group(1) in en_dev:
                i["nota"] = "humano:%s; la ficha %s ya esta en dev: comentar y cerrar" % (hid, d.group(1))
                g["cerrar"].append(i)
            elif NECESITA in et:
                i["nota"] = "humano:%s" % hid
                g["esperando"].append(i)
            elif EN_CURSO in et:
                i["nota"] = "humano:%s, abierto por el equipo" % hid
                g["en_curso"].append(i)
            else:
                i["nota"] = "humano:%s; la persona quito %s: verificar, comentar y cerrar, o volver a etiquetar con lo que falta" % (hid, NECESITA)
                g["cerrar"].append(i)
            continue
        if NECESITA in et:
            g["esperando"].append(i)
            continue
        f = fichas.get(i["numero"], {})
        if f.get("curso"):
            i["nota"] = "ficha %s" % ", ".join(f["curso"])
            if EN_CURSO not in et:
                i["nota"] += ", sin la etiqueta %s: ponerla con el comentario de reclamo" % EN_CURSO
            g["en_curso"].append(i)
        elif f.get("dev"):
            i["nota"] = "ficha %s en dev: comentar con el PR y como se verifico, quitar %s y cerrar (completed)" % (", ".join(f["dev"]), EN_CURSO)
            g["cerrar"].append(i)
        elif EN_CURSO in et and i["actualizado"] is not None and ahora - i["actualizado"] < ttl_s:
            i["nota"] = "reclamado sin ficha hace %d min; vence a las %d h" % ((ahora - i["actualizado"]) // 60, ttl_s // 3600)
            g["en_curso"].append(i)
        else:
            notas = []
            if EN_CURSO in et:
                notas.append("reclamo vencido: sin ficha y sin cambios en %d h o mas" % (ttl_s // 3600))
            if f.get("descartado"):
                notas.append("ficha %s descartada: leer su motivo antes de proponer otra" % ", ".join(f["descartado"]))
            i["nota"] = "; ".join(notas)
            g["pedidos"].append(i)
    g["pedidos"].sort(key=lambda i: (0 if set(i["etiquetas"]) & set(PRIMERO) else 1, i["creado"], i["numero"]))
    for k in ("en_curso", "esperando", "cerrar", "ignorados", "sin_confianza"):
        g[k].sort(key=lambda i: i["numero"])
    return g


def texto(repo, g, aviso):
    total = sum(len(v) for v in g.values())
    out = ["ISSUES=%s: %d abiertos | pedidos %d | en curso %d | esperando a una persona %d | para cerrar o verificar %d | ignorados %d | sin confianza %d%s" % (
        repo, total, len(g["pedidos"]), len(g["en_curso"]), len(g["esperando"]), len(g["cerrar"]),
        len(g["ignorados"]), len(g["sin_confianza"]), aviso)]
    for i in g["pedidos"]:
        prim = [e for e in i["etiquetas"] if e in PRIMERO]
        fecha = time.strftime("%Y-%m-%d", time.gmtime(i["creado"]))
        out.append("pedido #%d | %s | %s @%s | creado %s | %s | %s%s" % (
            i["numero"], ",".join(prim) or "-", i["asociacion"], i["autor"], fecha, i["titulo"], i["url"],
            " | " + i["nota"] if i["nota"] else ""))
    for k, nombre in (("en_curso", "en curso"), ("esperando", "esperando"), ("cerrar", "cerrar")):
        for i in g[k]:
            out.append("%s #%d | %s | %s" % (nombre, i["numero"], i.get("nota") or "-", i["titulo"]))
    if g["ignorados"]:
        out.append("ignorados (%s): %s" % (IGNORAR, " ".join("#%d" % i["numero"] for i in g["ignorados"])))
    if g["sin_confianza"]:
        out.append("sin confianza (no se ejecutan ni se comentan; solo el numero): %s" % " ".join("#%d" % i["numero"] for i in g["sin_confianza"]))
    out.append("PEDIDOS=%d" % len(g["pedidos"]))
    return "\n".join(out)


def como_json(repo, g, motivo):
    def uno(i, completo):
        d = {"numero": i["numero"]}
        if completo:
            d.update(titulo=i["titulo"], url=i["url"], etiquetas=i["etiquetas"], autor=i["autor"],
                     asociacion=i["asociacion"], nota=i.get("nota", ""))
        return d
    salida = {"repo": repo, "leido": motivo is None, "motivo": motivo}
    for k in g:
        salida[k] = [uno(i, k not in ("ignorados", "sin_confianza")) for i in g[k]]
    return json.dumps(salida, ensure_ascii=False, indent=1)


def principal(a):
    ahora = a.ahora if a.ahora is not None else time.time()
    vacio = {k: [] for k in ("pedidos", "en_curso", "esperando", "cerrar", "ignorados", "sin_confianza")}
    q = "repo:%s is:issue is:open" % a.repo
    datos, motivo = leer_archivo(a.json_de) if a.json_de else gh_buscar(q)
    items = items_de(datos, "items", "issues") if motivo is None else None
    if motivo is None and items is None:
        motivo = "respuesta sin lista de issues"
    if motivo is not None:
        if a.json:
            print(como_json(a.repo, vacio, motivo))
        else:
            print("ISSUES=no se pudieron leer (%s): el turno sigue con su backlog; en la nube, "
                  "mcp__github__list_issues (state OPEN) con las reglas de issues.md" % motivo)
            print("PEDIDOS=0")
        return 0
    aviso = ""
    if isinstance(datos, dict) and isinstance(datos.get("total_count"), int) and datos["total_count"] > len(items):
        aviso = " | hay %d y se miraron %d" % (datos["total_count"], len(items))
    issues = [i for i in (normalizar(x) for x in items) if i]
    en_dev = set((a.en_dev or "").split())
    g = clasificar(issues, leer_fichas(a.fichas), en_dev, ahora, int(a.ttl_horas * 3600))
    print(como_json(a.repo, g, None) if a.json else texto(a.repo, g, aviso))
    return 0


def comentarios(a):
    datos, motivo = leer_archivo(a.comentarios)
    lista = items_de(datos, "comments", "items") if motivo is None else None
    if lista is None:
        print("COMENTARIOS=no se pudieron leer (%s)" % (motivo or "sin lista de comentarios"))
        return 0
    buenos = propios = ajenos = 0
    for c in lista:
        if not isinstance(c, dict):
            continue
        asoc = str(c.get("author_association") or c.get("authorAssociation") or "DESCONOCIDA").upper()
        cuerpo = c.get("body") if isinstance(c.get("body"), str) else ""
        if MARCADOR.match(cuerpo):
            propios += 1
        elif asoc not in CONFIANZA:
            ajenos += 1
        else:
            buenos += 1
            usuario = c.get("user") if isinstance(c.get("user"), dict) else {}
            print("comentario de @%s (%s, %s): %s" % (
                plano(usuario.get("login") or "?", 40), asoc, plano(c.get("created_at") or "?", 20), plano(cuerpo, 500)))
    print("COMENTARIOS=%d de confianza | %d del equipo (marcador) | %d sin confianza (no cuentan)" % (buenos, propios, ajenos))
    return 0


def humano(a):
    if not ID_HUMANO.fullmatch(a.humano):
        print("id invalido: '%s' (minusculas, digitos y guiones)" % a.humano, file=sys.stderr)
        return 2
    q = 'repo:%s is:issue "humano:%s" in:body' % (a.repo, a.humano)
    datos, motivo = leer_archivo(a.json_de) if a.json_de else gh_buscar(q)
    items = items_de(datos, "items", "issues") if motivo is None else None
    if items is None:
        # Sin saber si existe no se abre: un duplicado por turno es peor que un aviso de menos.
        print("HUMANO=no se pudo buscar (%s): no abrir ninguno en esta sesion" % (motivo or "respuesta sin lista de issues"))
        return 0
    for i in (normalizar(x) for x in items):
        if not i or i["asociacion"] not in CONFIANZA:
            continue
        h = HUMANO.search(i["cuerpo"])
        if h and h.group(1) == a.humano:
            print("HUMANO=existe #%d (%s) %s: no abrir otro" % (i["numero"], "abierto" if i["abierto"] else "cerrado", i["url"]))
            return 0
    print("HUMANO=no existe: se puede abrir (uno por sesion)")
    return 0


def main(argv=None):
    p = argparse.ArgumentParser(description="Issues de GitHub para el equipo de desarrollo.")
    p.add_argument("--json-de", help="leer el JSON de este archivo (- = stdin) en vez de gh")
    p.add_argument("--fichas", default="", help='"N:NN:estado ...": issues que citan las fichas')
    p.add_argument("--en-dev", default="", help='"NN ...": fichas que ya estan en dev')
    p.add_argument("--ttl-horas", type=float, default=TTL_HORAS)
    p.add_argument("--ahora", type=float, help="epoch fijo (pruebas)")
    p.add_argument("--json", action="store_true")
    p.add_argument("--repo", default=REPO)
    p.add_argument("--comentarios", help="filtrar comentarios de este archivo (- = stdin)")
    p.add_argument("--humano", help="buscar el issue del equipo con humano:ID")
    a = p.parse_args(argv)
    if a.comentarios:
        return comentarios(a)
    if a.humano:
        return humano(a)
    return principal(a)


if __name__ == "__main__":
    sys.exit(main())
