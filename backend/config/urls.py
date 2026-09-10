"""URLs del proyecto: la API bajo /api/ y el build de React en el resto."""

from django.conf import settings
from django.contrib import admin
from django.http import FileResponse, HttpResponse
from django.urls import include, path, re_path

INDEX = settings.REPO_DIR / "frontend" / "dist" / "index.html"


def spa(request, path: str = ""):
    """Sirve el build de React si existe; si no, explica como levantarlo."""
    if path:
        candidate = (settings.REPO_DIR / "frontend" / "dist" / path).resolve()
        dist = (settings.REPO_DIR / "frontend" / "dist").resolve()
        if candidate.is_file() and str(candidate).startswith(str(dist)):
            return FileResponse(open(candidate, "rb"))
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


urlpatterns = [
    path("api/", include("replays.urls")),
    path("admin/", admin.site.urls),
    re_path(r"^(?P<path>.*)$", spa, name="spa"),
]
