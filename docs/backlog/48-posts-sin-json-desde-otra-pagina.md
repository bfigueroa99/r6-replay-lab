# 48. POST de etiquetas y de Ubisoft aceptan formularios de otra pagina

estado: aprobado
candado: release 2026-10-15T16:12Z
rama: claude/equipo-dev/48-posts-sin-json-desde-otra-pagina
tipo: bug
epica: -
area: backend
prioridad: 2
fuente: QA 20261015T1012Z probando la ficha 47: `curl -X POST -H "Content-Type: text/plain" --data '{"gamemodes": {"999": "Ataque nuevo"}}' localhost:8766/api/overrides/` -> 200 y reetiqueta 2 partidas. `save_overrides` (views.py:587 en main 17f0ae1) y `player_ubisoft` (views.py:264) no llaman a `_es_json`; `app_settings` y `make_backup` si.
archivos: backend/replays/views.py, frontend/src/api.js, backend/tests/test_unknowns.py, backend/tests/test_externo.py, backend/tests/test_import_job.py, backend/tests/test_api.py, frontend/e2e/humo.spec.js
turnos: qa 20261015T1012Z, arquitecto 20261015T1211Z, dev 20261015T1311Z, revisor 20261015T1411Z, qa 20261015T1511Z

## PR

(La escribe el Release manager al final.)

## Que gana quien usa la app

Hoy cualquier pagina abierta en el navegador puede mandar un formulario a
`127.0.0.1` que reescribe `overrides.json` y renombra partidas ya
importadas (sin vuelta atras), o que dispara la consulta a Ubisoft sin el
clic del usuario. Con esto esos dos POST piden `application/json`, como ya
lo hacen Ajustes y Respaldo (`_es_json`, views.py:111), y esa puerta se
cierra sin tokens ni sesiones.

## Criterios de aceptacion

- [ ] `POST /api/overrides/` con `Content-Type: text/plain` (o
      `application/x-www-form-urlencoded`) devuelve 415 y no escribe
      `overrides.json` ni toca `Match`. Test.
- [ ] `POST /api/players/<id>/ubisoft/` sin `application/json` devuelve 415
      y no llama a `perfil_externo.abrir` (reemplazado en el test). Test.
- [ ] Con `application/json` los dos siguen igual (tests existentes en
      verde).
- [ ] La UI sigue funcionando: Datos ya manda JSON; `PerfilUbisoft.jsx`
      llama `post(...)` sin cuerpo, asi que no manda `Content-Type`: pasa
      a mandar `{}`. El e2e del perfil o de Datos sigue en verde.
- [ ] `CLAUDE.md` ya dice que los POST que cambian configuracion exigen
      JSON; el docstring de `_es_json` nombra tambien estos dos (sin tocar
      `CLAUDE.md`).

## Fuera de alcance

- `POST /api/import/` (solo relee la carpeta configurada; no escribe nada
  que el usuario no pidiera). Si el Arquitecto lo ve barato, puede sumarlo
  con su test; si no, queda anotado.
- Tokens CSRF o sesiones: la app es local y sin cuentas.

## Diseno

Filtros duros: pasa todos (sin dependencias, sin red nueva, sin tocar
`CLAUDE.md`; la regla "los que cambian configuracion exigen JSON" ya esta
escrita y esto la cumple). Ninguna rama de trabajo abierta: no pisa nada.

Decision: **`POST /api/import/` entra tambien.** Cuesta una linea en el
backend y la UI se arregla sola con el cambio de `api.js` (abajo); con
`?force=1` una pagina ajena puede forzar la reimportacion entera, que es
CPU y disco del usuario sin su clic. Quedan los cinco POST de la API con la
misma regla.

**1. `backend/replays/views.py`**
- `player_ubisoft` (hoy l.264): primera linea del cuerpo, antes de buscar
  el jugador, `if not _es_json(request): return _ok({"error": "se esperaba
  application/json"}, status=415)`. Antes del 404 y del `configurado()` a
  proposito: una pagina ajena no tiene que poder sondear que ids existen ni
  si hay cuenta configurada.
- `save_overrides` (hoy l.587): el mismo chequeo antes del `json.loads`.
- `run_import` (hoy l.686): el mismo chequeo antes de leer `force`/`limit`.
  El cuerpo se ignora (los parametros siguen en la query, sin cambio).
- Docstring de `_es_json`: cambiar "Los POST que cambian la configuracion"
  por "Todos los POST de la API" y nombrar los cinco (`/api/import/`,
  `/api/overrides/`, `/api/players/<id>/ubisoft/`, `/api/settings/`,
  `/api/backup/`). El mensaje 415 es el mismo texto que ya usan
  `app_settings` y `make_backup`: no inventar otro.

**2. `frontend/src/api.js`**: `post(path, params, body = {})`: el cuerpo
por defecto pasa a `{}`, asi que todo POST de la UI manda
`Content-Type: application/json`. Sacar el `if (body !== undefined)` y
dejar `headers` y `body` siempre. Con esto `App.jsx` (`post('/import/')`)
y `PerfilUbisoft.jsx` no se tocan. No cambia `get`.

**3. Tests backend** (los helpers existentes pasan a mandar JSON):
- `test_externo.py`, helper `consultar` (l.~281): agregar
  `data="{}", content_type="application/json"`. Test nuevo en la clase que
  ya usa `consultar` con un `abrir` falso:
  `test_un_formulario_de_otra_pagina_no_consulta_a_ubisoft`: POST con
  `content_type="text/plain"` -> 415, y el falso de `abrir` levanta
  `AssertionError` (patron de `test_abrir_el_perfil_trae_los_enlaces_y_no_sale_a_la_red`).
  Si el jugador no tiene `PerfilUbisoft` antes, sigue sin tenerlo.
- `test_unknowns.py`, `EndpointTests`: `test_un_formulario_de_otra_pagina_no_reetiqueta`:
  POST de `{"gamemodes": {...}}` (el mismo payload que un test valido de
  la clase) con `content_type="text/plain"` -> 415; `overrides.json` no
  existe/no cambia y el `map_name` de la partida sigue `Unknown(...)`.
  Segundo caso en el mismo test o aparte con
  `application/x-www-form-urlencoded`.
- `test_import_job.py` (4 POST, l.~133-159) y `test_api.py` (l.~249): los
  `self.client.post("/api/import/")` pasan a
  `self.client.post("/api/import/", data="{}", content_type="application/json")`.
  Conviene un helper `_importar(self, query="")` en cada clase en vez de
  repetir. Test nuevo en `test_import_job.py`:
  `test_un_formulario_de_otra_pagina_no_lanza_la_importacion`: POST
  `text/plain` -> 415 y `start_import` no se llama (`mock.patch` sobre
  `replays.views.start_import`, con `assert_not_called`).
- Ojo: el cliente de Django sin `content_type` manda `multipart/form-data`,
  asi que cualquier POST que quede sin tocar en los tests va a dar 415:
  `grep -rn 'client.post(' backend/tests` y revisarlos todos (los de
  `/api/import/progress/` esperan 405 y siguen igual: `require_POST` no
  aplica ahi, es `require_GET`, y el 405 sale antes de la vista).

**4. e2e `frontend/e2e/humo.spec.js`**: test nuevo `los POST de la UI
mandan JSON`: `page.route('**/api/import/', ...)` captura la request,
guarda `request.headers()['content-type']` y responde
`{running: false, count: 0, ...}` con la forma que espera `App.jsx`
(copiar las claves de `job.as_dict()`); clic en `Importar replays`;
`expect(tipo).toContain('application/json')`. No llama al backend real,
asi que los numeros de `seed_demo` no cambian. Sin consola sucia.

**Orden:** views.py + tests backend (ver los 415 en rojo primero con los
helpers viejos) -> api.js -> e2e -> `check.sh`.

**Que puede romperse:** (a) un POST de test olvidado da 415 (lo atrapa la
suite); (b) si `api.js` dejara un POST sin cabecera, el boton de importar
o el de Ubisoft fallarian en runtime con "se esperaba application/json":
lo atrapa el e2e nuevo para importar; Ubisoft no tiene e2e (sale a la
red), queda en la verificacion manual; (c) la app de Electron no hace
POST (`main.cjs` solo GET a health y settings), no se afecta.

**Verificacion manual:** con `runserver` y `seed_demo`:
`curl -s -o /dev/null -w "%{http_code}" -X POST -H "Content-Type: text/plain" --data '{"gamemodes":{"999":"X"}}' localhost:8000/api/overrides/` -> 415, y lo mismo
para `/api/import/?force=1` y `/api/players/1/ubisoft/`. En la UI: boton
Importar replays funciona; Datos guarda una etiqueta; en un perfil, el
boton de Ubisoft sin cuenta configurada muestra el 400 de "Falta
configurar" (no un 415).

Sin metricas nuevas: no toca `docs/metricas.md`. Tamano estimado: ~80
lineas entre codigo y tests.

## Implementacion

Dev 20261015T1311Z. Todo el diseno, sin desvios de alcance.

- `views.py`: `player_ubisoft`, `save_overrides` y `run_import` devuelven
  415 (`se esperaba application/json`, el texto de siempre) si no llega
  JSON. En `player_ubisoft` el chequeo va antes del 404 y de
  `configurado()`. El docstring de `_es_json` nombra los cinco POST.
- `api.js`: `post(path, params, body = {})` manda siempre la cabecera y el
  cuerpo JSON. `App.jsx` y `PerfilUbisoft.jsx` no cambian.
- Tests nuevos, uno por criterio:
  `test_externo.PerfilJugadorTests.test_un_formulario_de_otra_pagina_no_consulta_a_ubisoft`
  (text/plain y urlencoded dan 415, con `abrir` prohibido; un id
  inexistente tambien da 415 y no 404; no crea `PerfilUbisoft`),
  `test_unknowns.EndpointTests.test_un_formulario_de_otra_pagina_no_reetiqueta`
  (415, no escribe `overrides.json`, `map_name` sigue `Unknown(...)`) y
  `test_import_job.HiloTests.test_un_formulario_de_otra_pagina_no_lanza_la_importacion`
  (`?force=1` con text/plain y urlencoded da 415 y `start_import` no se
  llama). El e2e `los POST de la UI mandan JSON` intercepta
  `/api/import/`, hace clic en Importar replays y comprueba la cabecera.
- Los POST existentes a `/api/import/` y a Ubisoft en los tests ahora
  mandan JSON (helper `_importar` en `HiloTests`).
- **Desvio de `archivos:`:** tambien `backend/tests/test_ajustes.py:428`
  (`OrigenDelTrabajoTests` postea a `/api/import/` y daba 415), y lo
  reformatee con `ruff format` en `test_externo.py`, que ya estaba
  formateado en main.
- Verificado: con los helpers viejos, 15 tests en rojo (415). Mutacion del
  e2e: con el `api.js` de main falla `expect(tipo).toContain('application/json')`.
  Revision ciega: aprobar, sin bugs; dos notas menores (abajo).
- `check.sh`: `Todo en verde.` (632 tests backend con 4 saltados, 86
  vitest, build, 37 e2e).

## Revision 2026-10-15 sobre 31529d4

Revisor 20261015T1411Z. Rama al dia con `origin/main` (591a300), sin
conflicto. `check.sh` en `Todo en verde.` antes de revisar (632 tests
backend con 4 saltados, 86 vitest, build, 37 e2e).

Revision ciega (subagente con `revision.md` sobre el diff sin
`docs/backlog`): aprobar, sin bugs ni reglas rotas. Confirmado a mano:

- Los tres chequeos 415 van antes del 404, de `configurado()` y de
  `start_import`; el texto es el mismo que usan `app_settings` y
  `make_backup`.
- Todo POST del frontend pasa por `post()` de `api.js` (App, PerfilUbisoft,
  Datos, Ajustes x3); `frontend/electron/` y `scripts/` no postean a la API.
  `grep 'client.post('` en `backend/tests`: los que quedan sin
  `content_type` son a `/import/progress/` (espera 405) o ya mandan JSON.
- Los tests nuevos caen con el bug presente (darian 200/404, crearian
  `PerfilUbisoft`, llamarian `start_import`, escribirian `overrides.json`).

Criterios: 415 en overrides -> `test_unknowns...test_un_formulario_de_otra_pagina_no_reetiqueta`;
415 en Ubisoft sin `abrir` -> `test_externo...test_un_formulario_de_otra_pagina_no_consulta_a_ubisoft`;
JSON sigue igual -> suite existente en verde; UI manda JSON -> e2e
`los POST de la UI mandan JSON` (importar; Ubisoft cubierto por el mismo
`post()`, sin e2e porque sale a la red); docstring de `_es_json` -> diff.
Desvio de `archivos:` (`test_ajustes.py:428`) explicado en Implementacion.

Hallazgos: ninguno que bloquee. La frase de `CLAUDE.md` ya esta en
`## Para el humano`.

Nota fuera de esta ficha (preexistente, tambien en `origin/main`):
`python3 manage.py test tests.test_import_job tests.test_ajustes` da 4
fallos en `test_ajustes.VigilanteTests` (dependen del orden; la suite
completa y el modulo solo pasan). Candidato a ficha `bug`/`tests` del PO.

Veredicto: aprobar.

## QA 2026-10-15 sobre b538bd2

QA 20261015T1511Z. Codigo de 31529d4, rama al dia con `origin/main`
(591a300). Bases en el scratchpad con `R6_ENV_FILE` propio: una vacia
(`migrate`) y una con `seed_demo` (29 partidas). Nada de eso al repo.

- `./scripts/check.sh` -> `Todo en verde.` (ruff ok, 632 tests backend con
  4 saltados, 86 vitest, build, 37 e2e).
- **415 sin JSON**, en las dos bases (`B=localhost:<puerto>/api`):
  `curl -X POST -H "Content-Type: text/plain" --data '{"gamemodes":{"999":"X"}}' $B/overrides/`,
  `--data 'gamemodes=x'` (urlencoded), `-F a=b` (multipart), sin cuerpo,
  `$B/import/?force=1` text/plain, `"$B/import/?force=1&limit=foo"`
  urlencoded, `$B/players/1/ubisoft/` y `$B/players/99999/ubisoft/`
  text/plain -> todos 415 `{"error": "se esperaba application/json"}`.
  Despues de esos POST no existe `overrides.json` en ninguna base. El id
  inexistente da 415 y no 404 (no se pueden sondear ids).
- **Con JSON sigue igual:** overrides `{"gamemodes":{"999":"Ataque nuevo"}}`
  -> 200 y escribe el archivo; `import/?force=1` con `{}` -> 200 con la
  forma de `job.as_dict()`; Ubisoft id 1 -> 400 `Falta configurar
  UBI_EMAIL...` (base sembrada) y 404 (base vacia, id 99999);
  `application/json; charset=utf-8` y `APPLICATION/JSON` -> 400 de
  configuracion, no 415. Cuerpo `no-json` -> 400, `[]` -> 400. GET a
  overrides e import -> 405. Settings y backup siguen en 415.
- **UI en Chromium** (script de Playwright temporal contra la base
  sembrada, consola sin errores propios): Importar replays -> POST
  `application/json` 200; Ajustes: respaldo y el interruptor de
  importacion automatica -> POST `application/json` 200; Datos: con una
  partida pasada a `Unknown(424242)`, "Guardar y reetiquetar" -> 200 y el
  aviso `Unknown(424242) → Mapa QA. Reetiquetadas 1 partidas`; Perfil con
  `UBI_EMAIL` falso en el `.env`: "Consultar Ubisoft" manda
  `application/json` con cuerpo `{}` (interceptado con `page.route` y
  respondido en el navegador: nada salio a la red) y el panel muestra el
  error.
- **Mutacion** (con `PYTHONDONTWRITEBYTECODE=1`; con `.pyc` el resultado
  se corre de a uno): sacar el chequeo de `player_ubisoft`, de
  `save_overrides` o de `run_import` hace caer solo
  `test_un_formulario_de_otra_pagina_no_consulta_a_ubisoft`,
  `..._no_reetiqueta` y `..._no_lanza_la_importacion` respectivamente (el
  ultimo como ERROR: el `start_import` falso devuelve un MagicMock que no
  serializa; igual lo atrapa). El e2e ya tenia su mutacion anotada por Dev.
- **Chunk inicial:** `index-*.js` 186.78 kB contra 186.80 kB de main. No
  crece.
- Sin migraciones, parser, `recompute`, Electron ni `.ps1`: no hace falta
  `## Verificar en el PC`.

Criterios: los 5 con evidencia arriba. Veredicto: aprobar.

## Para el humano

- `CLAUDE.md` ("La API es de lectura") dice que exigen `application/json`
  "los que cambian configuracion". Con esta ficha lo exigen todos los
  POST. La ficha dice que no se toque `CLAUDE.md`, asi que si se quiere
  cambiar la frase la cambia el humano.
- Despues de mergear, `npm run build` antes de `runserver`: un
  `frontend/dist` viejo manda los POST sin cabecera, y los botones de
  Importar y de Ubisoft darian 415.
