# 48. POST de etiquetas y de Ubisoft aceptan formularios de otra pagina

estado: entregado
candado: -
rama: claude/equipo-dev/48-posts-sin-json-desde-otra-pagina
tipo: bug
epica: -
area: backend
prioridad: 2
fuente: QA 20261015T1012Z probando la ficha 47: `curl -X POST -H "Content-Type: text/plain" --data '{"gamemodes": {"999": "Ataque nuevo"}}' localhost:8766/api/overrides/` -> 200 y reetiqueta 2 partidas.
archivos: backend/replays/views.py, frontend/src/api.js, backend/tests/test_unknowns.py, backend/tests/test_externo.py, backend/tests/test_import_job.py, backend/tests/test_api.py, backend/tests/test_ajustes.py, frontend/e2e/humo.spec.js
turnos: qa 20261015T1012Z, arquitecto 20261015T1211Z, dev 20261015T1311Z, revisor 20261015T1411Z, qa 20261015T1511Z, release 20261015T1612Z

## PR

**Titulo:** `[equipo-dev][backend] Los POST de la API exigen JSON`

### Que cambia

Una pagina cualquiera abierta en el navegador ya no puede mandar un formulario a `127.0.0.1` que renombre partidas importadas (`/api/overrides/`), dispare la consulta a Ubisoft sin el clic del usuario (`/api/players/<id>/ubisoft/`) o fuerce una reimportacion entera (`/api/import/?force=1`). Los cinco POST de la API piden ahora `application/json`, como ya lo hacian Ajustes y Respaldo; la UI manda siempre JSON y sigue funcionando igual.

### Por que esto y no otra cosa

Ficha 48, bug encontrado por QA probando la ficha 47. Tokens CSRF o sesiones se descartaron: la app es local y sin cuentas, y un formulario HTML de otro origen no puede mandar `application/json` sin preflight CORS, que el servidor no autoriza. `/api/import/` entra tambien porque cuesta una linea y `?force=1` es CPU y disco del usuario sin su clic.

### Como se probo

- `./scripts/check.sh`: `Todo en verde.` (632 tests backend con 4 saltados, 86 vitest, build, 37 e2e), sobre la rama fusionada con `origin/main` 591a300.
- Tests nuevos: `test_externo.PerfilJugadorTests.test_un_formulario_de_otra_pagina_no_consulta_a_ubisoft` (415, `abrir` prohibido, id inexistente da 415 y no 404, no crea `PerfilUbisoft`); `test_unknowns.EndpointTests.test_un_formulario_de_otra_pagina_no_reetiqueta` (415, no escribe `overrides.json`, el mapa sigue `Unknown(...)`); `test_import_job.HiloTests.test_un_formulario_de_otra_pagina_no_lanza_la_importacion` (415, `start_import` no se llama); e2e `los POST de la UI mandan JSON`.
- Revision ciega + revisor: aprobar, sin hallazgos. QA con `curl` en base vacia y sembrada (text/plain, urlencoded, multipart, sin cuerpo -> 415; JSON -> igual que antes), la UI en Chromium (Importar, Ajustes, Datos, Ubisoft interceptado) y mutacion: sacar cada chequeo hace caer su test.

### Riesgos y lo que no entra

Sin migraciones, parser ni `recompute`. Chunk inicial sin cambio (186.78 kB). Un `frontend/dist` viejo manda POST sin cabecera: hay que reconstruir.

### Como probarlo en 2 minutos

```powershell
cd frontend; npm run build; cd ..\backend; python manage.py runserver
# en otra terminal:
curl.exe -s -w " %{http_code}" -X POST -H "Content-Type: text/plain" --data "{}" http://localhost:8000/api/overrides/   # 415
curl.exe -s -w " %{http_code}" -X POST -H "Content-Type: text/plain" "http://localhost:8000/api/import/?force=1"   # 415
```

En la UI: "Importar replays" funciona; en Datos, guardar una etiqueta funciona; en un perfil, "Consultar Ubisoft" sin cuenta muestra "Falta configurar" (no un 415).

### Para el humano

- `CLAUDE.md` ("La API es de lectura") dice que exigen JSON "los que cambian configuracion"; ahora lo exigen todos los POST. Si se quiere ajustar la frase, la cambia el humano.
- Despues de mergear, `npm run build` antes de `runserver`.

### Candidatos descubiertos

- Preexistente en `main`: `manage.py test tests.test_import_job tests.test_ajustes` da 4 fallos en `test_ajustes.VigilanteTests` (dependen del orden; la suite completa pasa). Candidato a ficha del PO.

## Que gana quien usa la app

Hoy cualquier pagina abierta en el navegador puede mandar un formulario a `127.0.0.1` que reescribe `overrides.json` y renombra partidas ya importadas, o que dispara la consulta a Ubisoft sin el clic del usuario. Con esto esos POST piden `application/json` y esa puerta se cierra sin tokens ni sesiones.

## Criterios de aceptacion

- [x] `POST /api/overrides/` sin JSON -> 415, no escribe `overrides.json` ni toca `Match`.
- [x] `POST /api/players/<id>/ubisoft/` sin JSON -> 415, no llama a `abrir`.
- [x] Con `application/json` los dos siguen igual.
- [x] La UI sigue funcionando: `post()` de `api.js` manda siempre `{}` JSON.
- [x] Docstring de `_es_json` nombra los cinco POST (sin tocar `CLAUDE.md`).

## Implementacion

Dev 20261015T1311Z, sin desvios de alcance. Chequeo `_es_json` al principio de `player_ubisoft` (antes del 404 y de `configurado()`), `save_overrides` y `run_import`; `api.js` con cuerpo `{}` por defecto. Desvio de `archivos:`: `test_ajustes.py:428` (posteaba a `/api/import/` sin JSON).

## Revision 2026-10-15 sobre 31529d4

Revisor 20261015T1411Z. Veredicto: aprobar, sin hallazgos. Nota preexistente: orden de `VigilanteTests` (arriba, candidatos).

## QA 2026-10-15 sobre b538bd2

QA 20261015T1511Z. Los 5 criterios con evidencia (curl en dos bases, UI en Chromium, mutacion por chequeo, chunk sin crecer). Veredicto: aprobar. Detalle en `git log` de esta rama.

## Para el humano

- Frase de `CLAUDE.md` sobre los POST con JSON (aviso informativo; ver PR).
- `npm run build` despues de mergear.
