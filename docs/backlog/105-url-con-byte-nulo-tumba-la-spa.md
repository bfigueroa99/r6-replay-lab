# 105. Una URL con byte nulo tumba la SPA con un 500

estado: en curso 2026-11-11
candado: dev 2026-11-11T16:40Z
rama: claude/equipo-dev/105-url-con-byte-nulo-tumba-la-spa
tipo: bug
epica: -
area: backend
prioridad: 2
fuente: dev 20261111T1603Z-ctict1j, sin trabajo tomable (83 espera a la 79): barrido de la UI en Chromium sobre `seed_demo` con rutas y queries raras
archivos: backend/config/urls.py, backend/tests/test_spa.py
turnos: dev 20261111T1603Z-ctict1j

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

## Revision

## QA

## Verificar en el PC

## Pendiente
