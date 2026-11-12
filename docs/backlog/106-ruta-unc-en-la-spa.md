# 106. Una ruta UNC en la URL hace que la SPA toque la red en Windows

estado: en curso 2026-11-12
candado: dev 2026-11-12T04:14Z
rama: claude/equipo-dev/106-ruta-unc-en-la-spa
tipo: bug
epica: -
area: backend
prioridad: 1
fuente: revision de la 105 (omc-security-reviewer, revisor 20261111T2003Z-c5GamMd) y `## Para el humano` de ESTADO.md; escrita por el Dev sin trabajo (la 83 espera a la 79)
archivos: backend/config/urls.py, backend/tests/test_spa.py
turnos: dev 20261112T0403Z-cLKK8wJ

## PR

(La escribe el Release manager al final.)

## Que gana quien usa la app

Con la app levantada, cualquier pagina abierta en el navegador puede pedir
`http://127.0.0.1:8000/%5C%5Chost%5Cs%5Cx` (o `///host/s/x`): el atrapa-todo
`spa` arma `DIST / "\\\\host\\s\\x"`, que en Windows reemplaza a `DIST` por
una ruta UNC, y `resolve()` la abre antes del chequeo de contencion: Windows
intenta SMB contra un host ajeno y puede entregar el hash NTLM del usuario.
Con el arreglo, la ruta se valida como texto antes de tocar el disco y una
ruta que no puede ser del build nunca llega al sistema de archivos.

## Criterios de aceptacion

- [ ] Una URL con barra invertida (`/%5C%5Chost%5Cs%5Cx`, `/assets%5Capp.js`),
      con doble barra (`///host/s/x`), con unidad (`/C:%5Cx`, `/C:/x`) o
      con `..` devuelve el index (200) sin que `Path.resolve` ni
      `Path.is_file` se llamen sobre ninguna ruta: test
      `test_una_ruta_que_no_puede_ser_del_build_no_toca_el_disco`.
- [ ] Un bucle de symlinks dentro del build devuelve el index y no un 500
      (`RuntimeError` en `resolve()` de Python 3.11): test
      `test_un_bucle_de_symlinks_devuelve_el_index`.
- [ ] `test_no_sirve_archivos_fuera_del_build` deja de pasar sin chequeo:
      afirma que el `..` se rechaza antes de tocar el disco.
- [ ] Los archivos del build (`/assets/app.js`) y las rutas de la app
      (`/partidas/12`) siguen igual; los tests de la 105 siguen en verde.

## Fuera de alcance

- Cambiar como se sirve el build (whitenoise, `django.views.static`):
  dependencia o cambio de modelo, no hace falta.
- Probarlo en Windows: va a `## Verificar en el PC`.

## Diseno

(Dev, ficha de bug escrita en el momento.) Un helper puro
`_partes_del_build(path)` en `config/urls.py` parte la ruta por `/` y
devuelve `None` si algun tramo es vacio, `.`, `..`, o tiene `\\`, `:` o
un byte nulo; si no, la tupla de tramos. `spa` solo toca el disco con
`DIST.joinpath(*partes)`, que lexicamente queda dentro de `DIST` en Linux y
en Windows; el `is_relative_to` despues de `resolve()` se queda por los
symlinks. `RuntimeError` se suma al `except`. Test primero: un espia sobre
`Path.resolve` y `Path.is_file` que anota cada ruta tocada.

## Implementacion

## Revision

## QA

## Verificar en el PC

## Para el humano
