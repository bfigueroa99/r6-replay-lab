"""URLs del proyecto: la API bajo /api/ y el build de React en el resto."""

from django.conf import settings
from django.contrib import admin
from django.http import FileResponse, HttpResponse, JsonResponse
from django.urls import include, path, re_path
from django.views.decorators.csrf import csrf_exempt

DIST = settings.FRONTEND_DIST
INDEX = DIST / "index.html"


def _partes_del_build(path: str) -> tuple[str, ...] | None:
    """Tramos de una ruta que puede ser un archivo del build, o None si no puede.

    Se decide por la forma, sin tocar el disco: en Windows `DIST / "\\\\host\\s"`
    o `DIST / "//host/s"` reemplazan a DIST por una ruta UNC, y un resolve()
    sobre ella abre SMB contra ese host (y le entrega el hash NTLM) antes de
    que ningun chequeo de contencion llegue a correr.
    """
    partes = tuple(path.split("/"))
    for parte in partes:
        # Win32 recorta el punto y el espacio del final (".. " vale ".."), y un
        # build de Vite nunca genera esos nombres
        if not parte or parte[-1] in ". " or any(c in parte for c in "\\:\x00"):
            return None
    return partes


def spa(request, path: str = ""):
    """Sirve el build de React si existe; si no, explica como levantarlo."""
    partes = _partes_del_build(path) if path else None
    if partes:
        try:
            candidate = DIST.joinpath(*partes).resolve()
            # is_relative_to y no un prefijo de texto: "dist-viejo" empieza
            # igual que "dist" y no es parte del build. Sigue haciendo falta
            # despues del filtro de forma por los symlinks del build
            if candidate.is_relative_to(DIST.resolve()) and candidate.is_file():
                return FileResponse(open(candidate, "rb"))
        except (OSError, ValueError, RuntimeError):
            # un nombre que el sistema no admite o un bucle de symlinks
            # (RuntimeError en Python 3.11) no pueden ser un archivo del
            # build: es una ruta de la app, que decide el 404
            pass
    if INDEX.exists():
        return FileResponse(open(INDEX, "rb"), content_type="text/html")
    return HttpResponse(
        "<h1>R6 Replay Lab</h1>"
        "<p>El frontend no esta compilado. En desarrollo corre "
        "<code>npm run dev</code> dentro de <code>frontend/</code> y abre "
        "<a href='http://localhost:5173'>localhost:5173</a>.</p>"
        "<p>La API esta viva en <a href='/api/health/'>/api/health/</a>.</p>",
        content_type="text/html",
    )


@csrf_exempt
def api_no_existe(request, path: str = ""):
    """404 en JSON para cualquier /api/ que no calce.

    Sin esto el atrapa-todo de la SPA devuelve el index.html con 200 y el
    frontend lo toma por la API caida. Va aca y no al final de replays/urls.py
    para que una ruta nueva de la API nunca quede detras de el. Sin CSRF
    porque no hace nada: un POST mal dirigido tambien recibe su 404 en JSON.
    """
    return JsonResponse({"error": "esa ruta de la API no existe"}, status=404)


urlpatterns = [
    path("api/", include("replays.urls")),
    re_path(r"^api/(?P<path>.*)$", api_no_existe),
    path("admin/", admin.site.urls),
    re_path(r"^(?P<path>.*)$", spa, name="spa"),
]
