# 48. POST de etiquetas y de Ubisoft aceptan formularios de otra pagina

estado: disenado
candado: -
rama: -
tipo: bug
epica: -
area: backend
prioridad: 2
fuente: QA 20261015T1012Z probando la ficha 47: `curl -X POST -H "Content-Type: text/plain" --data '{"gamemodes": {"999": "Ataque nuevo"}}' localhost:8766/api/overrides/` -> 200 y reetiqueta 2 partidas. `save_overrides` (views.py:587 en main 17f0ae1) y `player_ubisoft` (views.py:264) no llaman a `_es_json`; `app_settings` y `make_backup` si.
archivos: backend/replays/views.py, frontend/src/api.js, backend/tests/test_unknowns.py, backend/tests/test_externo.py, backend/tests/test_import_job.py, backend/tests/test_api.py, frontend/e2e/humo.spec.js
turnos: qa 20261015T1012Z, arquitecto 20261015T1211Z

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

## Revision

## QA

## Para el humano
