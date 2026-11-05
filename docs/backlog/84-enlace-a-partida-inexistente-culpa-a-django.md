# 84. Un enlace a una partida o jugador que no existe dice que Django no corre

estado: aprobado
candado: qa 2026-11-05 16:14 UTC
rama: claude/equipo-dev/84-enlace-a-partida-inexistente-culpa-a-django
tipo: bug
epica: -
area: fullstack
prioridad: 4
fuente: QA 20261105T0418Z-cq6Wet6, prueba de bordes sobre dev ed39632 con `seed_demo` y Chromium. `frontend/src/components/ui.jsx:236` (`ErrorBox`) trata todo error como API caida; `backend/config/urls.py:35` (`re_path(r"^(?P<path>.*)$", spa)`) tambien atrapa `/api/<ruta desconocida>`
archivos: backend/config/urls.py, backend/replays/views.py, backend/tests/test_api.py, backend/tests/test_player.py, frontend/src/api.js, frontend/src/api.test.js, frontend/src/components/ui.jsx, frontend/src/pages/MatchDetail.jsx, frontend/src/pages/Jugador.jsx, frontend/e2e/humo.spec.js
turnos: qa 20261105T0418Z-cq6Wet6, arquitecto 20261105T1429Z-c7UZ3T6, dev 20261105T1455Z-c4eLe1A, revisor 20261105T1521Z-c41wXWJ, dev 20261105T1547Z-cLk3BF3, revisor 20261105T1605Z-csxB8d1, qa 20261105T1613Z-cAimE1D

## PR

(La escribe el Release manager al final.)

## Que gana quien usa la app

Un enlace viejo (marcador del navegador, resumen copiado, base restaurada con
`/api/backup/`, id mal escrito) hoy muestra "No pude leer la API. 404 Not
Found... Revisa que Django este corriendo en el puerto 8000" con Django vivo,
y manda a buscar un problema que no existe. Con el arreglo se lee "Esa
partida no existe" (o "Ese jugador no existe") con un enlace a Partidas, como
ya hace la ruta `*` con "Esa pagina no existe".

## Repro (dev ed39632)

```bash
cd backend
export SQLITE_PATH=$SCRATCH/qa.sqlite3 R6_ENV_FILE=$SCRATCH/qa.env DATA_DIR=$SCRATCH/data
python manage.py migrate -v0 && python manage.py seed_demo
python manage.py runserver 127.0.0.1:8765 --noreload
curl -s -o /dev/null -w '%{http_code} %{content_type}\n' localhost:8765/api/matches/999999/  # 404 text/html (pagina de Django)
curl -s -o /dev/null -w '%{http_code} %{content_type}\n' localhost:8765/api/nada/            # 200 text/html (index.html de la SPA)
```

En Chromium (`main` de cada pagina):

- `/partidas/999999` y `/jugadores/999999`: "No pude leer la API. 404 Not Found en /matches/999999/ Revisa que Django este corriendo en el puerto 8000."
- `/partidas/abc` y `/jugadores/abc`: "No pude leer la API. Unexpected token '<', \"<!doctype \"... is not valid JSON Revisa que Django este corriendo..." (`/api/matches/abc/` no calza con `<int:pk>`, cae en el `spa` y devuelve el HTML con 200).

## Criterios de aceptacion

- [ ] `GET /api/<ruta desconocida>/` (p. ej. `/api/nada/`, `/api/matches/abc/`) responde 404 con JSON `{"error": ...}`, no el `index.html`; las rutas fuera de `/api/` siguen sirviendo la SPA. Test en `backend/tests/`.
- [ ] `GET /api/matches/999999/` y `/api/players/999999/` responden 404 con JSON `{"error": ...}`. Test.
- [ ] `/partidas/999999`, `/partidas/abc`, `/jugadores/999999` y `/jugadores/abc` muestran "Esa partida no existe" / "Ese jugador no existe" con enlace a la lista, sin "Revisa que Django este corriendo". Caso nuevo en el e2e.
- [ ] Con Django apagado (fetch que falla de verdad) el aviso de API caida sigue saliendo; su texto no fija el puerto 8000 (la app se puede servir en otro).

## Fuera de alcance

Redirigir a otra partida, buscar por nick o recuperar partidas borradas.
Cambiar el formato de los 400 que ya devuelven `{"error": ...}`.

## Diseno

Arquitecto 20261105T1429Z-c7UZ3T6 sobre dev 85009f6. Una sola forma obvia:
sin arena ni consenso (no toca datos, ni el `.env`, ni la logica de un POST:
solo el formato de su 404).

**Causas.** (1) `config/urls.py:35` atrapa todo con `spa`, asi que una ruta
`/api/...` que no calza (`/api/nada/`, `/api/matches/abc/`) devuelve el
`index.html` con 200. (2) `views.py:308`, `:327` y `:472` hacen `raise
Http404`, que Django contesta en HTML. (3) `api.js:get` tira un `Error` sin
el status y `useApi` guarda solo el texto, asi que la pagina no puede
distinguir un 404 de la API caida.

**Archivos y por que esos**

1. `backend/config/urls.py`: vista `api_no_existe(request, path="")` que
   devuelve `JsonResponse({"error": "esa ruta de la API no existe"},
   status=404)`, y `re_path(r"^api/", api_no_existe)` justo despues de
   `path("api/", include(...))` y antes de `admin/` y del `spa`. Va aca y no
   al final de `replays/urls.py` para que una ruta que agregue otra rama (la
   79 suma una) no quede detras del atrapa-todo. Con esto `/api/nada` (sin
   barra) tambien resuelve, asi que `APPEND_SLASH` no redirige: igual que hoy,
   que lo resolvia el `spa`.
2. `backend/replays/views.py`: los tres `raise Http404(...)` pasan a
   `return _ok({"error": "partida no encontrada"}, status=404)` /
   `{"error": "jugador no encontrado"}`. Sacar `Http404` del import si queda
   sin uso. `player_ubisoft` es POST: su chequeo de JSON sigue antes del 404
   (docstring), solo cambia el formato; `post()` de `api.js` ya lee `error`.
3. `frontend/src/api.js`: en `get`, el error lleva el status:
   `const error = new Error(`${response.status} ${response.statusText} en ${path}`); error.status = response.status; throw error`
   (el mensaje no cambia). En `useApi`, estado `status` (`null` al arrancar y
   en cada exito, `err.status ?? null` en el `catch`) y devolver
   `{ data, error, status, loading, reload }`. Un fetch que falla de verdad
   (`TypeError`) deja `status: null`: eso es "API caida".
4. `frontend/src/components/ui.jsx`:
   - componente `NoExiste({ titulo, a, texto })`: el mismo `empty-state` que
     la ruta `*` de `App.jsx` (`<h2>{titulo}</h2>` y un `Link` con
     `className="btn"`). `App.jsx` no se toca (la 81 cambia ese texto).
   - `ErrorBox`: la nota pasa a `Revisa que Django esté corriendo.` (sin
     puerto: la app se sirve en otro con `runserver` o Electron).
5. `frontend/src/pages/MatchDetail.jsx`: tomar `status` de `useApi` y, antes
   del `if (error)`, `if (status === 404) return <NoExiste titulo="Esa partida no existe" a="/partidas" texto="Ver tus partidas" />`.
6. `frontend/src/pages/Jugador.jsx`: lo mismo con `titulo="Ese jugador no
   existe"`, `a="/companeros"`, `texto="Ver tus compañeros"` (la lista de
   jugadores es Compañeros).

**Tests nuevos**

- `backend/tests/test_api.py`: ampliar `test_partida_inexistente_da_404` para
  que tambien afirme `Content-Type` `application/json` y `"error"` en el
  json; nuevos `test_una_ruta_desconocida_de_la_api_da_404_json`
  (`/api/nada/` y `/api/nada`), `test_una_partida_con_id_no_numerico_da_404_json`
  (`/api/matches/abc/`) y `test_fuera_de_la_api_se_sigue_sirviendo_la_spa`
  (`/partidas/999999` da 200 `text/html`; pasa con o sin build porque el
  `spa` tiene su HTML de respaldo).
- `backend/tests/test_player.py`: ampliar `test_jugador_inexistente_da_404`
  igual (json con `error`), y `test_el_post_de_ubisoft_a_un_jugador_inexistente_da_404_json`
  (POST json a `/api/players/99999/ubisoft/`; no sale a la red: el 404 va
  antes de `configurado()`, igual se parchea `perfil_externo.abrir` como el
  resto de `test_externo.py` si el test lo necesita).
- `frontend/src/api.test.js` (nuevo, vitest): `get con un 404 tira un error
  con el status` (stub de `globalThis.fetch` con `{ ok: false, status: 404,
  statusText: 'Not Found' }`) y `get con la red caida tira un error sin
  status` (fetch que rechaza con `TypeError`). Restaurar `fetch` en
  `afterEach`.
- `frontend/e2e/humo.spec.js`, dos tests:
  - `una partida o un jugador que no existe lo dice sin culpar a Django`:
    para `/partidas/999999`, `/partidas/abc`, `/jugadores/999999` y
    `/jugadores/abc`, ve el `h2` ("Esa partida no existe" / "Ese jugador no
    existe"), `getByText('Django')` con 0, y el enlace lleva a `h1` Partidas
    / Compañeros. **Consola:** Chromium loguea "Failed to load resource: the
    server responded with a status of 404" por cada 404 esperado; filtrar
    solo ese texto (`errores.filter((e) => !e.includes('status of 404'))`) y
    afirmar el resto vacio, con un comentario de por que.
  - `con la API caida el aviso sigue culpando a Django`: `page.route('**/api/matches/**', (r) => r.abort())`,
    `goto('/partidas/1')`, se ve "No pude leer la API" y "Revisa que Django
    esté corriendo", y el texto no contiene `8000`. Sin afirmar la consola
    (el abort es a proposito y `vigilarConsola` lo anota).

**Orden:** backend (urls, views, tests) -> `api.js` + vitest -> `ui.jsx` ->
paginas -> e2e -> `npm run build` -> `check.sh`.

**Que puede romperse:**
- Otras paginas que lean `error` de `useApi`: siguen recibiendo el mismo
  texto; `status` es un campo extra.
- `test_partida_sin_rondas.py` / e2e `partida-sin-rondas.json`: no cambian
  (solo cambia la respuesta de ids que no existen).
- Tests que hoy esperen HTML o 200 en `/api/<algo raro>`: buscar con
  `grep -rn "api/" backend/tests | grep -v "/api/[a-z]*/"` antes de cerrar.
- Sin migracion, recompute, parser ni Electron: no va a `## Verificar en el PC`.

**Archivos ocupados:** la 81 (`con hallazgos`) toca `ui.jsx` (justo la nota
de `ErrorBox`), `MatchDetail.jsx`, `Jugador.jsx` y `humo.spec.js`; la 79
(`entregado`, espera al humano) toca `views.py` y `MatchDetail.jsx`, en otras
lineas. Implementar despues de que #81 se mergee (prioriza, no bloquea; el
conflicto seria de texto y lo resuelve P3).

**Verificacion manual:** `seed_demo`, `runserver`, y en el navegador
`/partidas/999999`, `/partidas/abc`, `/jugadores/999999`, `/jugadores/abc`:
el aviso de que no existe con su enlace. `curl -i localhost:8000/api/nada/` da
404 `application/json`. Con Django apagado y `npm run dev`, abrir una
partida: "No pude leer la API" sin puerto.

**`docs/metricas.md`:** sin numero nuevo, sin fila.

Skills: no aplica (sin dominio nuevo: rutas de Django y un estado de error del hook que el repo ya tiene)
OMC: plan=— (ficha chica, una forma obvia) · revisión=— · verificación=—

## Implementacion

(dev 20261105T1455Z-c4eLe1A, sobre dev 85009f6)

Hecho todo el diseno, sin desvios de fondo:

- `config/urls.py`: `api_no_existe` (404 JSON) con `re_path(r"^api/(?P<path>.*)$")` despues del `include` y antes de `admin/` y del `spa`. Desvio: lleva `@csrf_exempt` (hallazgo LOW del revisor ciego): sin el, un POST a una ruta `/api/` desconocida recibia el 403 HTML de CSRF en vez del 404 JSON. No hace nada, asi que no abre nada.
- `replays/views.py`: los tres `raise Http404` pasan a `_ok({"error": ...}, status=404)`; `Http404` sale del import. En `player_ubisoft` el chequeo de JSON sigue antes del 404.
- `api.js`: `get` adjunta `error.status`; `useApi` devuelve `status` (null en exito y con la red caida).
- `ui.jsx`: `NoExiste({ titulo, a, texto })` y la nota de `ErrorBox` sin puerto ("Revisa que Django esté corriendo."). `App.jsx` no se toco.
- `MatchDetail.jsx` y `Jugador.jsx`: `status === 404` -> `NoExiste` con enlace a `/partidas` / `/companeros`.

Test que falla primero (tipo bug): `cd backend && python3 manage.py test tests.test_api tests.test_player` sobre dev sin el arreglo -> `FAILED (failures=6)` (`test_partida_inexistente_da_404`, `test_una_partida_con_id_no_numerico_da_404_json`, `test_una_ruta_desconocida_de_la_api_da_404_json` x2 subtests, `test_jugador_inexistente_da_404`, `test_el_post_de_ubisoft_a_un_jugador_inexistente_da_404_json`); vitest `get > con un 404 tira un error con el status` fallaba (`error.status` undefined). Con el arreglo, verdes.

Tests por criterio:
1. `/api/<desconocida>` 404 JSON y la SPA fuera de `/api/`: `test_una_ruta_desconocida_de_la_api_da_404_json`, `test_una_partida_con_id_no_numerico_da_404_json`, `test_un_post_a_una_ruta_desconocida_de_la_api_da_404_json`, `test_fuera_de_la_api_se_sigue_sirviendo_la_spa` (test_api.py).
2. Partida/jugador inexistente 404 JSON: `test_partida_inexistente_da_404` (ampliado), `test_jugador_inexistente_da_404` (ampliado), `test_el_post_de_ubisoft_a_un_jugador_inexistente_da_404_json` (test_player.py).
3. Paginas: e2e `una partida o un jugador que no existe lo dice sin culpar a Django` (humo.spec.js; los cuatro ids, h2, sin "Django", enlace a la lista). La consola admite exactamente los cuatro "status of 404" de los casos y nada mas (hallazgo LOW del revisor ciego: el filtro abierto escondia otros 404).
4. API caida: e2e `con la API caida el aviso sigue culpando a Django` y vitest `get con la red caida tira un error sin status` (`src/api.test.js`, nuevo).

`grep -rn "api/" backend/tests | grep -v "/api/[a-z_]*/"`: ningun test esperaba HTML o 200 en una ruta rara.

Conflictos previstos: la 81 toca la misma linea de `ErrorBox` y lineas cercanas en `MatchDetail.jsx`, `Jugador.jsx` y `humo.spec.js`; se tomo antes de que la 81 se mergee porque el diseno dice "prioriza, no bloquea". Si la 81 entra primero, P3 lo resuelve (choque de texto).

Skills: no aplica (el Arquitecto ya dijo que no hay dominio nuevo)
OMC: plan=— · revisión=2 hallazgos LOW (2 arreglados) · verificación=—

### Correccion de hallazgos (dev 20261105T1547Z-cLk3BF3, sobre 22fd925)

- [HIGH] e2e intermitente (`humo.spec.js`): despues de ver el `h1` de la lista, `await page.waitForLoadState('networkidle')` antes del `goto` siguiente, con un comentario de por que (la lista pide `/api/filters/` al montar). `npx playwright test e2e/humo.spec.js -g "no existe lo dice" --repeat-each=20`: 20 de 20 en verde.
- [LOW] `useApi` (`api.js`): `setStatus(null)` junto al `setLoading(true)` del efecto, asi al pasar de un id inexistente a uno valido se ve `<Loading />` y no "Esa partida no existe".

verificar.sh: VERDE 40e2eab (959 tests backend, 192 vitest, 63 e2e).

Skills: no aplica
OMC: plan=— · revisión=— (dos cambios de 3 lineas que pidio el revisor) · verificación=—

## Revision 2026-11-05 sobre 6bcdd7e

(revisor 20261105T1521Z-c41wXWJ, rama ya al dia con dev 85009f6)

Revision a ciegas: `omc-code-reviewer` (estandares) aprobar con 1 LOW; `omc-security-reviewer` (toca la vista POST `player_ubisoft` y agrega `@csrf_exempt`) aprobar, 0 hallazgos: `api_no_existe` no lee la request ni escribe, y en el POST el chequeo de JSON sigue antes del 404. Backend y vitest verdes. El veredicto lo cambia lo que encontro `check.sh`.

Hallazgos:

- [test] [HIGH] frontend/e2e/humo.spec.js:1020
  Que pasa: el e2e nuevo `una partida o un jugador que no existe lo dice sin culpar a Django` es intermitente y deja `check.sh` en rojo.
  Como reproducirlo o por que es cierto: `verificar.sh` sobre 6bcdd7e dio `ROJO` (1 failed, 62 passed) con `request fallida: http://127.0.0.1:8099/api/filters/ (net::ERR_ABORTED)` en la consola. Aislado, `npx playwright test e2e/humo.spec.js -g "no existe lo dice" --repeat-each=10` falla 1 de 10 con el mismo error. Causa: despues del clic en el enlace, la lista (Partidas o Compañeros) monta `Filters` y pide `/api/filters/`. Solo se espera el `h1`, asi que el `page.goto` de la vuelta siguiente corta esa request en vuelo y `vigilarConsola` la anota.
  Arreglo sugerido: despues de `await expect(page.locator('h1')).toHaveText(lista)` agregar `await page.waitForLoadState('networkidle')`. Probado en local sin empujar: 25 de 25 en verde con `--repeat-each=25`.

- [bug] [LOW] frontend/src/api.js:66 (`useApi`)
  Que pasa: al cambiar de `path` en el mismo componente (de `/partidas/999999` a `/partidas/1` con atras o adelante), `status` sigue en 404 hasta que llega la respuesta nueva. Mientras tanto se ve "Esa partida no existe" en vez de `<Loading />`.
  Como reproducirlo o por que es cierto: el efecto hace `setLoading(true)` pero no limpia `status`, y la pagina mira `status === 404` antes que `loading`. Con `error` ya pasaba lo mismo antes de este cambio, y se corrige solo cuando llega la respuesta. Confirmado leyendo el codigo, no en el navegador.
  Arreglo sugerido: `setStatus(null)` junto al `setLoading(true)` del efecto (opcional, no bloquea).

Ficha: los cuatro criterios tienen test (backend, vitest y e2e). Lo que toca el diff esta dentro de `archivos:`. No hay numeros nuevos, asi que no hace falta fila en `metricas.md`. Identificadores sin tildes y textos de UI con tildes. Sin `print` ni `console.log`.

Veredicto: corregir (el HIGH: un e2e intermitente deja `check.sh` en rojo; Principio 3).

Skills: no aplica
OMC: plan=— · revisión=2 hallazgos (0 arreglados; HIGH confirmado reproduciendo, LOW leyendo el codigo; seguridad 0) · verificación=—

## Revision 2026-11-05 sobre 48e989a (segunda pasada)

(revisor 20261105T1605Z-csxB8d1; rama mezclada con dev 0861b0b en 48e989a, sin conflictos.)

Revision a ciegas: `omc-code-reviewer` (estandares) aprobar con 3 LOW;
`omc-security-reviewer` (vista POST `player_ubisoft`, `@csrf_exempt` en
`api_no_existe`) aprobar, 0 hallazgos: la vista atrapa-todo no lee ni escribe
ni refleja la ruta, va despues del `include` asi que los POST reales siguen
con su chequeo de `application/json`, y en `player_ubisoft` el orden
JSON -> 404 -> `configurado()` se mantiene (el test no sale a la red).

Los dos hallazgos de la primera pasada quedaron resueltos: el HIGH (e2e
intermitente) con `waitForLoadState('networkidle')`, y `check.sh` completo
paso en verde; el LOW de `status` con `setStatus(null)` en el efecto.

Criterios: los cuatro cubiertos por test (backend `test_api.py` y
`test_player.py`, vitest `api.test.js`, e2e de no existe y de API caida). El
diff no sale de `archivos:`; sin numeros nuevos (sin fila en `metricas.md`);
identificadores sin tildes, UI con tildes; sin `print` ni `console.log`.
`verificar.sh`: VERDE 48e989a3a (960 tests backend, 199 vitest, 64 e2e).

Hallazgos (todos LOW, no bloquean):

- [bug] LOW frontend/src/api.js:69 (`useApi`)
  Que pasa: al pasar de un id con 404 a otro id sin desmontar la pagina,
  `status` vuelve a `null` pero `error` conserva "404 Not Found en ...", asi
  que mientras carga se ve el `ErrorBox` ("Revisa que Django esté
  corriendo") un instante.
  Por que es cierto: confirmado leyendo el codigo; el efecto limpia `status`
  y no `error`, y la pagina mira `if (error)` antes que `loading`. Dificil de
  alcanzar (el enlace de `NoExiste` lleva a una lista y desmonta), y el error
  que persiste mientras carga ya pasaba antes de este cambio.
  Arreglo sugerido: `setError(null)` junto al `setStatus(null)` del efecto.
- [test] LOW `frontend/src/api.test.js`: nada prueba la transicion de `status`
  en `useApi` (solo `get`). Un e2e de 404 a id valido sin recarga lo cubriria.
- [estilo] LOW `frontend/e2e/humo.spec.js` `networkidle`: hoy estable (no hay
  polling sin importacion activa); si se vuelve fragil,
  `page.waitForResponse('**/api/filters/**')`.

Veredicto: aprobar -> `revisado`. Los LOW quedan en `## Para el humano` de la
ficha.

Skills: no aplica
OMC: plan=— · revisión=3 hallazgos LOW (0 arreglados; el Revisor no arregla; seguridad 0) · verificación=—

## QA 2026-11-05 sobre f0aa83a

(qa 20261105T1613Z-cAimE1D; rama al dia con dev 0861b0b. Bases sinteticas en
el scratchpad: una vacia y una de `seed_demo`; nunca `.rec` ni `.sqlite3` al
repo.)

Como repetirlo:

```bash
cd backend
export SQLITE_PATH=$SCRATCH/qa.sqlite3 R6_ENV_FILE=$SCRATCH/qa.env DATA_DIR=$SCRATCH/data
python manage.py migrate -v0 && python manage.py seed_demo
python manage.py runserver 127.0.0.1:8766 --noreload
curl -s -w ' %{http_code} %{content_type}\n' localhost:8766/api/nada/
```

Evidencia por criterio:

1. `/api/<desconocida>` 404 JSON, SPA fuera de `/api/`: cubierto. Con base
   vacia y con base sembrada, `curl` a `/api/nada/`, `/api/nada`,
   `/api/matches/abc/`, `/api/players/abc/`, `/api/matches/-1/` y `/api/`:
   `404 application/json {"error": "esa ruta de la API no existe"}`.
   `/partidas/999999` y `/jugadores/abc`: `200 text/html` (la SPA);
   `/admin/`: 302. POST JSON a `/api/nada/`: 404 JSON (sin el 403 de CSRF).
   Borde LOW (no incumple, el criterio habla de `/api/<ruta>/`): `/api` sin
   barra da 200 con la SPA, porque la regex es `^api/`.
2. Partida/jugador inexistente 404 JSON: cubierto. `/api/matches/999999/` ->
   `404 {"error": "partida no encontrada"}`, `/api/players/999999/` ->
   `404 {"error": "jugador no encontrado"}`; en base vacia `/api/matches/1/`
   y `/api/players/1/` igual. Validos (`/api/matches/1/`, `/api/players/1/`)
   200 JSON; `/api/matches/?page=-1` y `?until=foo` 200 JSON. POST JSON a
   `/api/players/999999/ubisoft/` -> 404 JSON; con `text/plain` -> 415 (el
   chequeo de JSON sigue antes del 404); POST form a `/api/import/` -> 415.
3. Paginas: cubierto. Chromium sobre el `runserver`: `/partidas/999999`,
   `/partidas/abc` -> "Esa partida no existe" + enlace `/partidas`;
   `/jugadores/999999`, `/jugadores/abc` -> "Ese jugador no existe" + enlace
   `/companeros`; en base vacia `/partidas/1` y `/jugadores/1` igual. Ningun
   "Django" en `main`; la consola trae solo el "Failed to load resource ...
   404" de cada caso. De `/partidas/999999` a `/partidas/1` sin recargar
   (`pushState` + `popstate`): se ve la partida.
4. API caida: cubierto. Con `page.route('**/api/**', r => r.abort())` y
   `/partidas/1`: "No pude leer la API. Failed to fetch Revisa que Django
   esté corriendo." (sin 8000). e2e "con la API caida..." verde.

Mutacion (romper y ver caer, restaurar y ver verde):
- `config/urls.py` sin el `re_path` de `api_no_existe`:
  `python manage.py test tests.test_api tests.test_player` -> FAILED
  (failures=4: ruta desconocida x2, id no numerico, POST desconocido).
- `api.js` sin `error.status = response.status`: `npx vitest run src/api.test.js`
  -> 1 failed ("con un 404 tira un error con el status").
- `MatchDetail.jsx` sin la rama `status === 404`, `vite build` y
  `npx playwright test -g "no existe lo dice"` -> 1 failed.
- Restaurado: los dos e2e nuevos con `--repeat-each=10` -> 20 passed (sin
  intermitencia).

`check.sh`: `verificar.sh` VERDE f0aa83a57 (960 tests backend, 199 vitest,
64 e2e). Sin migracion, recompute, parser, Electron ni `.ps1`: no va a
`## Verificar en el PC`.

`omc-verifier`: PASS, 4 criterios VERIFIED; `@csrf_exempt` en
`api_no_existe` inocuo (no lee ni escribe). Gaps LOW: `/api` sin barra sirve
la SPA (arreglo posible `^api(/.*)?$`), y el e2e cuenta exactamente cuatro
404 en consola (estable hoy).

Choca con la 81 (`revisado` -> `con hallazgos` en este turno) en
`ui.jsx`, `MatchDetail.jsx`, `Jugador.jsx` y `humo.spec.js`
(`git merge-tree` de las dos ramas: conflicto). La que entre segunda
resuelve con P3.

Veredicto: `aprobado`.

OMC: plan=— · revisión=— · verificación=PASS

## Pendiente

- 2026-11-05 (revisor 20261105T1605Z-csxB8d1): LOW sin arreglar, no bloquean: `useApi` no limpia `error` al cambiar de path (un instante de "Revisa que Django esté corriendo" al ir de un id inexistente a uno valido sin desmontar); arreglo de una linea, `setError(null)` en el efecto.

## Para el humano

- 2026-11-05 (qa 20261105T1613Z-cAimE1D): LOW sin arreglar, no bloquean: `/api` sin barra final sigue sirviendo la SPA (200 HTML), la regex es `^api/`; y el LOW del revisor de `useApi` (no limpia `error` al cambiar de path) sigue en `## Pendiente`.
