# 105. Una URL con byte nulo tumba la SPA con un 500

estado: revisado
candado: -
rama: claude/equipo-dev/105-url-con-byte-nulo-tumba-la-spa
tipo: bug
epica: -
area: backend
prioridad: 2
fuente: dev 20261111T1603Z-ctict1j, sin trabajo tomable (83 espera a la 79): barrido de la UI en Chromium sobre `seed_demo` con rutas y queries raras
archivos: backend/config/urls.py, backend/tests/test_spa.py
turnos: dev 20261111T1603Z-ctict1j, revisor 20261111T2003Z-c5GamMd

## PR

(La escribe el Release manager al final.)

## Que gana quien usa la app

Un enlace roto o pegado a mano con `%00` (`/partidas/%00`, `/comparar/3/%00`)
hoy da "Internal Server Error" de Django en vez de la app con su pantalla de
"no existe". Ademas el atrapa-todo de la SPA servia cualquier archivo de una
carpeta hermana cuyo nombre empiece con `dist` (`frontend/dist-viejo/...`),
porque comparaba rutas como texto: baja el riesgo de servir algo que no es
el build.

## Criterios de aceptacion

- [ ] `GET /partidas/%00`, `/assets/app%00.js` y `/comparar/3/%00` devuelven
      200 con el `index.html` (la app decide el 404), no 500:
      `test_una_url_con_byte_nulo_devuelve_el_index_y_no_un_500`.
- [ ] `GET /..%2Fdist-viejo%2Fsecreto.txt` no sirve el archivo de la carpeta
      hermana: `test_no_sirve_archivos_de_una_carpeta_hermana_con_el_mismo_prefijo`.
- [ ] Los archivos del build y las rutas de la app se siguen sirviendo igual:
      `test_un_archivo_del_build_se_sirve_tal_cual`,
      `test_una_ruta_de_la_app_devuelve_el_index` y
      `test_fuera_de_la_api_se_sigue_sirviendo_la_spa` (ya existia).

## Fuera de alcance

- La API: `/api/matches/%00/` ya da 400 (lo corta Django antes de la vista).
- Cambiar como el frontend muestra el 404.

## Diseno

(dev 20261111T1603Z-ctict1j, ficha de bug escrita en el momento.)

`config/urls.py`, `spa`: el `resolve()` de `DIST / path` levanta
`ValueError: embedded null byte` con un `%00` en la ruta, y nadie lo ataja.
Envolver la busqueda del archivo en `try/except (OSError, ValueError)` y caer
al `index.html`, como cualquier ruta de la app. El chequeo
`str(candidate).startswith(str(dist))` pasa a `candidate.is_relative_to(dist)`
(Python 3.9+, el repo pide 3.11): compara por componentes, asi
`dist-viejo` no cuenta como dentro de `dist`. El `is_relative_to` va antes
del `is_file()`, para no tocar el disco fuera del build.

Tests en `backend/tests/test_spa.py`, con un build falso en una carpeta
temporal (parchean `config.urls.DIST` e `INDEX`): no dependen de
`npm run build`.

## Implementacion

(dev 20261111T1603Z-ctict1j, sobre dev def7322.)

Como se encontro: barrido de la UI en Chromium (build + `e2e/servidor.js` con
`seed_demo`, 436 rutas: las 10 paginas con 14 claves de query x 2 valores
raros, ids raros en `/partidas/`, `/comparar/` y `/jugadores/`, las 29
partidas y 7 jugadores reales), mirando `console.error`, `pageerror` y
respuestas 5xx. Lo unico que aparecio: las 5 rutas con `%00` daban 500 del
atrapa-todo (`ValueError: embedded null byte` en `Path.resolve()`). Los 404
de ids inexistentes son el comportamiento esperado (`NoExiste`). Leyendo la
vista salio el segundo problema, el chequeo por prefijo de texto.

Test primero: `tests/test_spa.py` contra el `urls.py` de dev da
`FAILED (failures=1, errors=3)`: los 3 subtests del byte nulo con
`ValueError: embedded null byte` y la carpeta hermana con
`AssertionError: b'no se sirve' != b'<html>la app</html>'`. Con el arreglo,
5/5 OK. `test_no_sirve_archivos_fuera_del_build` ya pasaba antes: queda como
red de regresion, y asi lo dice su comentario.

Quedo todo lo de `## Diseno`, sin desvios. Revision ciega
`omc-code-reviewer`: aprobar, 2 LOW (assert de `status_code` faltante en el
ultimo test, `__import__("shutil")`), los dos corregidos en aaab2a2.

Desvio del playbook: el test que falla lo escribi yo antes de lanzar
`omc-test-engineer` (la receta 4 pide que lo proponga el agente); la falla
se vio igual antes del arreglo, y el revisor ciego confirmo que los tests
fallan contra el codigo de dev.

verificar.sh: VERDE aaab2a2d3 (1105 tests backend, 295 vitest, 84 e2e).

Skills: no aplica (una vista de Django y pathlib).
OMC: plan=— · revisión=2 hallazgos (2 arreglados) · verificación=—

## Revision 2026-11-11 sobre f82fd98

(revisor 20261111T2003Z-c5GamMd, dev sin moverse desde def7322: sin merge.)

Revision ciega (`omc-code-reviewer`, eje de estandares) y `omc-security-reviewer`
(el diff decide que archivos del disco se sirven). Diff chico (76 lineas, un
tema): sin eje de intencion aparte.

Hallazgos confirmados:

- [test] [LOW] backend/tests/test_spa.py:58 (`test_no_sirve_archivos_fuera_del_build`)
  Que pasa: pasa aunque se borre el chequeo de contencion; no protege nada.
  Como reproducirlo: `/..%2F..%2Fdist-viejo%2Fsecreto.txt` resuelve a
  `<tmp>/../dist-viejo/secreto.txt`, que no existe: `is_file()` da False con
  o sin chequeo. Su comentario ("el prefijo viejo ya rechazaba este") no es cierto.
  Arreglo sugerido: crear `raiz / "secreto.txt"` y pedir `/..%2Fsecreto.txt`.
- [bug] [LOW] backend/config/urls.py:22, ya existia
  Que pasa: un bucle de symlinks dentro de `dist` hace que `resolve()` levante
  `RuntimeError` (Python 3.11), que el `except (OSError, ValueError)` no ataja: 500.
  Como reproducirlo: `dist/loop -> loop` y `GET /loop/x`. Nadie de afuera lo
  puede crear: robustez, no seguridad.
  Arreglo sugerido: sumar `RuntimeError` al `except`.

Fuera del diff (ya estaba en dev, no lo introduce esta ficha; va a ficha propia):

- [seguridad] [MEDIUM, solo Windows] backend/config/urls.py:17
  Una ruta con barras invertidas llega tal cual a la vista
  (`GET /%5C%5Csrv%5Cs%5Cx` -> `path='\\\\srv\\s\\x'`, verificado con el cliente de
  Django) y en Windows `DIST / path` da `\\srv\s\x`: la raiz cambia a un
  recurso UNC, y `resolve()` (realpath) lo abre antes del `is_relative_to`.
  Cualquier pagina abierta en el navegador puede disparar ese GET (un `<img>`)
  mientras el servidor esta levantado, y Windows intentaria SMB contra ese host
  entregando el hash NTLM. No da lectura de archivos (la contencion la
  rechaza despues). No verificado en Windows real (la nube es Linux).
  Arreglo sugerido: antes de tocar el disco, rechazar como texto la ruta con
  `\`, `:` o ancla de `PureWindowsPath`, y un test que mockee `Path.resolve` y
  afirme que no se llama con `/%5C%5Csrv%5Cs%5Cx`.

Criterios de aceptacion: los tres cubiertos por los tests que nombran;
el revisor ciego corrio `tests.test_spa` contra el `urls.py` de dev y fallan 4
de 5 (3 subtests del byte nulo con error, carpeta hermana con fail), asi que
prueban el bug. `archivos:` coincide con el diff. Sin metricas nuevas, sin
tildes en identificadores, sin `print`.

verificar.sh: VERDE f82fd980c (1105 tests backend, 295 vitest, 84 e2e).

Veredicto: aprobar (solo LOW en el diff).

Skills: no aplica.
OMC: plan=— · revisión=3 hallazgos (0 arreglados: 2 LOW para el Dev si vuelve, 1 MEDIUM fuera del diff a ficha propia) · verificación=—

## QA

## Verificar en el PC

## Pendiente
