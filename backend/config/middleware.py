"""Middleware propio del proyecto. Uno solo: el corte por Host."""

from __future__ import annotations

from django.core.exceptions import DisallowedHost
from django.http import HttpResponseBadRequest


class HostPermitido:
    """Corta con un 400 plano toda request cuyo Host no es el de la app.

    Django ya valida el Host contra `ALLOWED_HOSTS`, pero lo hace tarde y
    contesta con su manejador de errores: con `DJANGO_DEBUG=true`, que es el
    default al correr desde el repo, ese 400 es la pagina tecnica, con los
    settings y el entorno del proceso (cuenta de Ubisoft, rutas del disco).

    Importa por DNS rebinding: una pagina ajena reapunta su nombre a 127.0.0.1
    y le habla a la app con su propio Host. Para el navegador esa respuesta es
    del mismo origen que la pagina, asi que la lee entera. Va primero en
    `MIDDLEWARE`: nada del proyecto corre para un Host ajeno.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        try:
            request.get_host()
        except DisallowedHost:
            return HttpResponseBadRequest(
                "Host no permitido. Abre la app por 127.0.0.1 o localhost.",
                content_type="text/plain; charset=utf-8",
            )
        return self.get_response(request)
