# 106. Una ruta UNC en la URL hace que la SPA toque la red en Windows

estado: revisado
candado: qa 2026-11-12T11:35Z
rama: claude/equipo-dev/106-ruta-unc-en-la-spa
tipo: bug
epica: -
area: backend
prioridad: 1
fuente: revision de la 105 (omc-security-reviewer, revisor 20261111T2003Z-c5GamMd) y `## Para el humano` de ESTADO.md; escrita por el Dev sin trabajo (la 83 espera a la 79)
archivos: backend/config/urls.py, backend/tests/test_spa.py
turnos: dev 20261112T0403Z-cLKK8wJ, revisor 20261112T1127Z-cT8M5Vz

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

(dev 20261112T0403Z-cLKK8wJ, sobre dev 6af42af)

- **Test que falla primero (receta 4):** `omc-test-engineer` propuso el espia
  sobre `Path.resolve`/`Path.is_file` y el bucle de symlinks. Con el
  `urls.py` de dev, `cd backend && python manage.py test tests.test_spa`:
  `FAILED (failures=8, errors=1)`; los 7 casos de forma anotan rutas tocadas
  (p. ej. `['/host/s/x', '/tmp/.../dist']` para `//host/s/x`, que en Linux ya
  sale de `DIST`) y el bucle da `RuntimeError: Symlink loop`.
- **Arreglo** (`backend/config/urls.py`): `_partes_del_build(path)` parte por
  `/` y devuelve `None` si un tramo es vacio (doble barra, barra final),
  termina en `.` o espacio (cubre `.`, `..` y el recorte de Win32 de `.. `),
  o tiene `\`, `:` o byte nulo. `spa` solo toca el disco con
  `DIST.joinpath(*partes)`; `is_relative_to(DIST.resolve())` se queda por los
  symlinks del build; `RuntimeError` entra al `except`.
- **Tests** (`backend/tests/test_spa.py`):
  `test_una_ruta_que_no_puede_ser_del_build_no_toca_el_disco` (9 casos:
  UNC con `\`, `\` suelta, `///host`, `//host`, `C:\x`, `C:/x`, `..`,
  `.. ` y punto final), `test_un_bucle_de_symlinks_devuelve_el_index` (se
  salta si el sistema no deja crear symlinks, Windows sin modo de
  desarrollador), `test_los_nombres_que_genera_un_build_se_siguen_sirviendo`
  (`index-Ab_C1.js`, `@vite/x.js`, `a b.png`, `favicon.ico`), y
  `test_no_sirve_archivos_fuera_del_build` ahora afirma que el `..` no toca el
  disco (antes pasaba sin chequeo, LOW de la 105).
- **Revision ciega** (`omc-code-reviewer`): corregir antes de entregar. HIGH
  (symlink sin guarda rompe `check.ps1` en Windows) arreglado con `skipTest`
  ante `OSError`; LOW comentario de versiones, LOW nombres legitimos sin test
  y LOW `.. `/punto final en Win32, los tres arreglados. Su mutacion (filtro
  borrado) hace fallar 8 aserciones; con `PureWindowsPath` ninguna parte
  aceptada cambia el ancla del join (nombres reservados, separadores Unicode
  y `...` incluidos).
- Desvios del diseno: rechazar por "termina en `.` o espacio" en vez de
  listar `.` y `..` (los incluye).

Skills: no aplica (Django y `pathlib`, resuelto en el repo).
OMC: plan=— · revisión=4 hallazgos (4 arreglados) · verificación=—

## Revision 2026-11-12 sobre 15b47a9

(revisor 20261112T1127Z-cT8M5Vz; rama fusionada con dev 4e84ac2, cambios solo de maquinaria)

- **Revision ciega, eje de estandares** (`omc-code-reviewer`, prompt de
  `revision.md`): aprobar. Mutacion propia: con el filtro sin filtrar fallan
  los 9 subtests y `test_no_sirve_archivos_fuera_del_build`; sin la regla de
  punto/espacio final fallan los 4 casos que dependen de ella.
  - [test] LOW `test_spa.py` (bucle de symlinks): en Python 3.13 (el de la
    nube) `resolve()` no lanza ante el bucle, asi que borrar `RuntimeError`
    del `except` dejaba la suite verde. Confirmado y cubierto por el Revisor:
    `test_un_runtimeerror_de_resolve_devuelve_el_index` parchea
    `Path.resolve` con `RuntimeError`; con `RuntimeError` fuera del `except`
    da ERROR, con el codigo de la rama pasa.
  - [estilo] LOW `config/urls.py` comentario del `except`: dice "Python 3.11"
    y tambien vale 3.12. No bloquea; queda para quien toque el archivo.
- **Eje de seguridad** (`omc-security-reviewer`, toca rutas de archivos):
  aprobar, 0 hallazgos. Cubrio `%2F`/`%5C` ya decodificados, UNC, `\\?\`,
  unidades y ADS, byte nulo, punto/espacio final de Win32, separadores
  Unicode, nombres de dispositivo (`CON`, `nul.js`: quedan bajo DIST e
  `is_file` falso; analisis de `ntpath`, sin Windows), nombres de mas de 255
  bytes y `%0A` (404 de Django, no 500).
- **Criterios:** los cuatro cubiertos por los tests nombrados; los tests de
  la 105 siguen en verde. El diff solo toca `archivos:`. Sin numeros nuevos
  en la UI, sin tildes en identificadores, sin `print`.
- **Verificacion:** verificar.sh VERDE 15b47a9 (1109 tests backend, 295
  vitest, 84 e2e).

Veredicto: aprobar -> `revisado`.

Skills: no aplica.
OMC: plan=— · revisión=2 hallazgos (1 cubierto con test) · verificación=—

## QA

## Verificar en el PC

En Windows, con `runserver` levantado: `curl -s -o NUL -w "%{http_code}" http://127.0.0.1:8000/%5C%5C127.0.0.1%5Cc$%5Cnada`
responde 200 al instante (sin esperar a SMB) y la app sigue cargando sus
`assets/`. La suite en Windows: `test_un_bucle_de_symlinks_devuelve_el_index`
sale `skipped` si no tenes modo de desarrollador.

## Para el humano
