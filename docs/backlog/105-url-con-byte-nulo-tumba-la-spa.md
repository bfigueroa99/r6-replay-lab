# 105. Una URL con byte nulo tumba la SPA con un 500

estado: entregado
candado: -
rama: claude/equipo-dev/105-url-con-byte-nulo-tumba-la-spa
tipo: bug
epica: -
area: backend
prioridad: 2
fuente: dev 20261111T1603Z-ctict1j, sin trabajo tomable (83 espera a la 79): barrido de la UI en Chromium sobre `seed_demo` con rutas y queries raras
archivos: backend/config/urls.py, backend/tests/test_spa.py
turnos: dev 20261111T1603Z-ctict1j, revisor 20261111T2003Z-c5GamMd, qa 20261112T0003Z-cymg32T, release 20261112T0003Z-cymg32T

## PR

Titulo: `[equipo-dev][backend] Una URL con byte nulo ya no tumba la SPA con un 500`

### Que cambia

Un enlace con `%00` (`/partidas/%00`, `/comparar/3/%00`) devolvia
"Internal Server Error" de Django; ahora llega la app, que muestra su "no
existe". Ademas el atrapa-todo de la SPA ya no sirve archivos de una carpeta
hermana cuyo nombre empiece con `dist` (`frontend/dist-viejo/...`): la
contencion compara por componentes (`is_relative_to`), no como texto.

### Por que esto y no otra cosa

Bug encontrado en un barrido de 436 rutas raras en Chromium sobre
`seed_demo` (ficha 105): lo unico que dio 5xx. Se descarto validar la ruta
como texto antes del `resolve()`: el `try/except` cubre cualquier nombre que
el sistema no admita, no solo el byte nulo.

### Como se probo

- `check.sh` (con `verificar.sh`): VERDE 7075aba, 1105 tests backend, 295 vitest, 84 e2e.
- Tests nuevos en `backend/tests/test_spa.py` (build falso en carpeta temporal):
  `test_una_url_con_byte_nulo_devuelve_el_index_y_no_un_500` (3 URLs),
  `test_no_sirve_archivos_de_una_carpeta_hermana_con_el_mismo_prefijo`,
  `test_un_archivo_del_build_se_sirve_tal_cual`,
  `test_una_ruta_de_la_app_devuelve_el_index`,
  `test_no_sirve_archivos_fuera_del_build`.
- Servidor real: con el `urls.py` de dev las 3 URLs con `%00` dan 500 y
  `/..%2Fdist-viejo%2Fsecreto.txt` sirve el archivo; con la rama, todas dan
  200 con el index. Mutaciones M1/M2/M3 hacen caer los tests nuevos.
- OMC: implementacion: plan=— · revisión=2 hallazgos (2 arreglados) · verificación=—
- OMC: revision: plan=— · revisión=3 hallazgos (0 arreglados: 2 LOW, 1 MEDIUM fuera del diff) · verificación=—
- OMC: qa: plan=— · revisión=— · verificación=PASS (3/3 VERIFIED)

### Riesgos y lo que no entra

Sin migraciones, sin `recompute`, sin frontend. Quedan para una ficha de
seguimiento (anotados abajo): un symlink en bucle dentro de `dist` sigue
dando 500 (`RuntimeError`, preexistente); `test_no_sirve_archivos_fuera_del_build`
no protege nada; y en Windows una ruta con `\\srv\...` llegaria a `resolve()`
como UNC (MEDIUM, preexistente, no verificado en Windows).

### Como probarlo en 2 minutos

    cd backend; python manage.py test tests.test_spa      # 5 OK
    cd frontend; npm run build; cd ../backend; python manage.py runserver
    # abrir http://127.0.0.1:8000/partidas/%00 : la app, no "Internal Server Error"

### Para el humano

Nada.

### Candidatos descubiertos

Ninguno abierto todavia: los tres hallazgos de abajo esperan su ficha (PO).

## Que gana quien usa la app

Un enlace roto o pegado a mano con `%00` da la app con su pantalla de "no
existe" en vez de un 500, y el atrapa-todo no sirve nada fuera del build.

## Criterios de aceptacion

- [x] `GET /partidas/%00`, `/assets/app%00.js` y `/comparar/3/%00` devuelven
      200 con el `index.html`, no 500.
- [x] `GET /..%2Fdist-viejo%2Fsecreto.txt` no sirve el archivo de la carpeta hermana.
- [x] Los archivos del build y las rutas de la app se siguen sirviendo igual.

## Diseno e implementacion

`config/urls.py`, `spa`: `try/except (OSError, ValueError)` alrededor del
`resolve()` y caida al `index.html`; `startswith` por
`candidate.is_relative_to(DIST.resolve())`, antes del `is_file()`. Test
primero: contra dev, 4 de 5 fallan. verificar.sh VERDE aaab2a2.

## Revision 2026-11-11 sobre f82fd98

Aprobar (solo LOW en el diff). Hallazgos sin arreglar, para ficha propia:

- [test] [LOW] `test_spa.py:58`: `test_no_sirve_archivos_fuera_del_build` pasa
  sin chequeo de contencion. Arreglo: crear `raiz / "secreto.txt"` y pedir `/..%2Fsecreto.txt`.
- [bug] [LOW] `urls.py:22`: symlink en bucle -> `RuntimeError` -> 500. Arreglo: sumarlo al `except`.
- [seguridad] [MEDIUM, solo Windows, ya en dev] `urls.py:17`: `GET /%5C%5Csrv%5Cs%5Cx`
  da `\\srv\s\x` en Windows y `resolve()` abre el UNC (hash NTLM) antes de la
  contencion. Arreglo: rechazar como texto `\`, `:` o ancla de `PureWindowsPath`.

## QA 2026-11-12 sobre 7075aba

Aprobado: los 3 criterios con test, servidor real (vacia y `seed_demo`),
contraste contra dev (500 y fuga reproducidos) y mutacion M1/M2/M3; los dos
LOW del Revisor confirmados. Detalle y comandos en el commit 662a484.

## Verificar en el PC

## Pendiente
