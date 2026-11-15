# 106. Una ruta UNC en la URL hace que la SPA toque la red en Windows

estado: entregado
candado: -
rama: claude/equipo-dev/106-ruta-unc-en-la-spa
tipo: bug
epica: -
area: backend
prioridad: 1
fuente: revision de la 105 (omc-security-reviewer, revisor 20261111T2003Z-c5GamMd) y `## Para el humano` de ESTADO.md; escrita por el Dev sin trabajo (la 83 espera a la 79)
archivos: backend/config/urls.py, backend/tests/test_spa.py
turnos: dev 20261112T0403Z-cLKK8wJ, revisor 20261112T1127Z-cT8M5Vz, qa 20261112T1128Z-cKKCvKD, release 20261112T1128Z-cKKCvKD

## PR

Titulo: `[equipo-dev][backend] Una ruta UNC en la URL ya no hace que la SPA toque la red`

### Que cambia

El atrapa-todo que sirve el build de React decide por la forma de la ruta,
sin tocar el disco, si puede ser un archivo del build. Una URL con barra
invertida, doble barra, unidad (`C:`), `..` o punto/espacio final va
directo al index: en Windows ya no se arma una ruta UNC que haga que el
sistema abra SMB contra un host ajeno (y le entregue el hash NTLM) por
una pagina cualquiera abierta en el navegador. Un bucle de symlinks en el
build da el index y no un 500.

### Por que esto y no otra cosa

Hallazgo del security reviewer en la ficha 105. Servir el build con
whitenoise o `django.views.static` era dependencia nueva o cambio de modelo;
un filtro puro de tramos antes de `joinpath` alcanza, y el
`is_relative_to` despues de `resolve()` se queda por los symlinks.

### Como se probo

- `check.sh` (con `verificar.sh`): VERDE 7ef161370, 1109 tests backend, 295 vitest, 84 e2e.
- Tests nuevos en `backend/tests/test_spa.py`:
  `test_una_ruta_que_no_puede_ser_del_build_no_toca_el_disco` (9 casos, con
  espia sobre `Path.resolve`/`Path.is_file`),
  `test_un_bucle_de_symlinks_devuelve_el_index`,
  `test_un_runtimeerror_de_resolve_devuelve_el_index` (Python 3.11/3.12),
  `test_los_nombres_que_genera_un_build_se_siguen_sirviendo`; y
  `test_no_sirve_archivos_fuera_del_build` ahora afirma que el `..` no toca
  el disco.
- Manual (QA): `runserver` con base vacia y con `seed_demo`; `curl --path-as-is`
  a 14 rutas hostiles, todas 200 con el index; un asset real 200 JS;
  symlinks a mano en `dist` (afuera e infinito) dan el index. Mutacion: 4 de 4 mueren.
- OMC: Implementacion: plan=— · revisión=4 hallazgos (4 arreglados) · verificación=—
- OMC: Revision: plan=— · revisión=2 hallazgos (1 cubierto con test) · verificación=—
- OMC: QA: plan=— · revisión=— · verificación=PASS (omc-verifier, 0 bloqueantes)

### Riesgos y lo que no entra

Sin migraciones, sin `recompute`, sin parser. Un nombre de archivo del build
que termine en punto o espacio dejaria de servirse; Vite no los genera.
`/%0A` sigue dando el 404 de Django (preexistente, no es 500). No se probo
en Windows real.

### Como probarlo en 2 minutos

```powershell
cd backend; python manage.py test tests.test_spa   # 9 tests, OK
python manage.py runserver
curl.exe -s -o NUL -w "%{http_code}" "http://127.0.0.1:8000/%5C%5Chost%5Cs%5Cx"   # 200 al instante
```

y la app sigue cargando en `http://127.0.0.1:8000/`.

### Verificar en el PC

En Windows, con `runserver` levantado: `curl -s -o NUL -w "%{http_code}" http://127.0.0.1:8000/%5C%5C127.0.0.1%5Cc$%5Cnada`
responde 200 al instante (sin esperar a SMB) y la app sigue cargando sus
`assets/`. En la suite de Windows, `test_un_bucle_de_symlinks_devuelve_el_index`
sale `skipped` si no tenes modo de desarrollador.

### Para el humano

Nada.

### Candidatos descubiertos

Ninguno.

## Implementacion, Revision y QA

Implementacion (dev 20261112T0403Z-cLKK8wJ): `_partes_del_build(path)` en
`config/urls.py` descarta tramos vacios, que terminan en `.` o espacio, o con
`\`, `:` o byte nulo; `spa` solo toca el disco con `DIST.joinpath(*partes)`;
`RuntimeError` entra al `except`. Revision ciega: HIGH del symlink en
Windows (`skipTest` ante `OSError`) y 3 LOW, arreglados. Revision (revisor
20261112T1127Z-cT8M5Vz): aprobar; agrego el test del `RuntimeError`
parcheado (en 3.13 `resolve()` no lanza); LOW sin arreglar: el comentario
del `except` dice 3.11 y vale tambien 3.12. Seguridad: 0 hallazgos. QA
(20261112T1128Z-cKKCvKD, sobre 7ef1613): aprobado, evidencia arriba. Detalle
completo en `git log` de la rama.

## Para el humano

Verificar en el PC: lo de `## PR`.
