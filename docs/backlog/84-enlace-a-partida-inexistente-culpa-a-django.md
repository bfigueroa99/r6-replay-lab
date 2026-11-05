# 84. Un enlace a una partida o jugador que no existe dice que Django no corre

estado: entregado
candado: -
rama: claude/equipo-dev/84-enlace-a-partida-inexistente-culpa-a-django
tipo: bug
epica: -
area: fullstack
prioridad: 4
fuente: QA 20261105T0418Z-cq6Wet6, prueba de bordes sobre dev ed39632 con `seed_demo` y Chromium. `frontend/src/components/ui.jsx:236` (`ErrorBox`) trata todo error como API caida; `backend/config/urls.py:35` (`re_path(r"^(?P<path>.*)$", spa)`) tambien atrapa `/api/<ruta desconocida>`
archivos: backend/config/urls.py, backend/replays/views.py, backend/tests/test_api.py, backend/tests/test_player.py, frontend/src/api.js, frontend/src/api.test.js, frontend/src/components/ui.jsx, frontend/src/pages/MatchDetail.jsx, frontend/src/pages/Jugador.jsx, frontend/e2e/humo.spec.js
turnos: qa 20261105T0418Z-cq6Wet6, arquitecto 20261105T1429Z-c7UZ3T6, dev 20261105T1455Z-c4eLe1A, revisor 20261105T1521Z-c41wXWJ, dev 20261105T1547Z-cLk3BF3, revisor 20261105T1605Z-csxB8d1, qa 20261105T1613Z-cAimE1D, release 20261105T1613Z-cAimE1D

## PR

Titulo: `[equipo-dev][backend] Un enlace a una partida o jugador que no existe ya no culpa a Django`

### Que cambia

Un enlace viejo o mal escrito a una partida o a un jugador (`/partidas/999999`,
`/jugadores/abc`) muestra "Esa partida no existe" / "Ese jugador no existe" con
un enlace a la lista, en vez de "No pude leer la API ... Revisa que Django este
corriendo en el puerto 8000" con Django vivo. Toda ruta desconocida bajo
`/api/` responde 404 JSON `{"error": ...}` en vez del `index.html`, y el aviso
de API caida ya no fija el puerto 8000.

### Por que esto y no otra cosa

Ficha 84, bug que encontro QA probando bordes sobre dev ed39632. Un 404 JSON
es lo que ya devuelven los 400 de la API; redirigir o buscar por nick quedo
fuera de alcance.

### Como se probo

- `check.sh` (con `verificar.sh`): VERDE en el commit de entrega (960 tests backend, 199 vitest, 64 e2e).
- Tests nuevos: `test_una_ruta_desconocida_de_la_api_da_404_json`, `test_una_partida_con_id_no_numerico_da_404_json`, `test_un_post_a_una_ruta_desconocida_de_la_api_da_404_json`, `test_fuera_de_la_api_se_sigue_sirviendo_la_spa` (test_api.py); `test_el_post_de_ubisoft_a_un_jugador_inexistente_da_404_json` y los 404 de partida/jugador ampliados a JSON; vitest `src/api.test.js` (404 con status, red caida sin status); e2e `una partida o un jugador que no existe lo dice sin culpar a Django` y `con la API caida el aviso sigue culpando a Django`.
- QA: `curl` con base vacia y sembrada (rutas desconocidas, ids inexistentes y no numericos, POST JSON / text/plain), Chromium sobre los cuatro ids y la API abortada; mutacion de `urls.py`, `api.js` y `MatchDetail.jsx` hace caer sus tests; e2e nuevos 20 de 20 con `--repeat-each=10`.
- OMC: plan=— (ficha chica, una forma obvia) · revisión=— · verificación=—
- OMC: plan=— · revisión=2 hallazgos LOW (2 arreglados) · verificación=—
- OMC: plan=— · revisión=3 hallazgos LOW (0 arreglados; el Revisor no arregla; seguridad 0) · verificación=—
- OMC: plan=— · revisión=— · verificación=PASS

### Riesgos y lo que no entra

Sin migracion, recompute, parser ni Electron. `api_no_existe` lleva
`@csrf_exempt` (no lee ni escribe: solo contesta 404). Choca de texto con la
81 en `ui.jsx`, `MatchDetail.jsx`, `Jugador.jsx` y `humo.spec.js`; la 81
resuelve con P3. LOW abiertos: `/api` sin barra sigue sirviendo la SPA;
`useApi` no limpia `error` al cambiar de path.

### Como probarlo en 2 minutos

```powershell
cd backend; python manage.py seed_demo; python manage.py runserver
curl.exe -i http://localhost:8000/api/nada/          # 404 application/json
curl.exe -i http://localhost:8000/api/matches/999999/ # 404 {"error": "partida no encontrada"}
```

En el navegador: `/partidas/999999`, `/partidas/abc`, `/jugadores/999999`,
`/jugadores/abc` muestran que no existe, con enlace a Partidas o Compañeros.

### Para el humano

Nada.

### Candidatos descubiertos

Ninguno.

## Que gana quien usa la app

Un enlace viejo (marcador, resumen copiado, base restaurada, id mal escrito)
mostraba "Revisa que Django este corriendo en el puerto 8000" con Django vivo.
Ahora dice que la partida o el jugador no existe, con enlace a la lista.

## Criterios de aceptacion

- [x] `GET /api/<ruta desconocida>/` responde 404 JSON `{"error": ...}`; fuera de `/api/` sigue la SPA. Test en `backend/tests/`.
- [x] `GET /api/matches/999999/` y `/api/players/999999/` responden 404 JSON. Test.
- [x] Las cuatro paginas de ids inexistentes dicen que no existe, con enlace a la lista, sin culpar a Django. e2e.
- [x] Con la API caida el aviso sigue y no fija el puerto 8000.

## Diseno (resumen)

Arquitecto 20261105T1429Z-c7UZ3T6: `api_no_existe` en `config/urls.py` despues
del `include` y antes del `spa`; `Http404` -> `_ok({"error": ...}, status=404)`
en `views.py`; `get` adjunta `error.status` y `useApi` devuelve `status`;
`NoExiste` en `ui.jsx` y rama `status === 404` en `MatchDetail.jsx` y
`Jugador.jsx`. El detalle completo queda en `git log` de esta ficha.

## Revision (resumen)

Dos pasadas (revisor 20261105T1521Z-c41wXWJ y 20261105T1605Z-csxB8d1). La
primera pidio corregir un e2e intermitente (HIGH, arreglado con
`waitForLoadState('networkidle')`) y limpiar `status` en `useApi` (LOW,
arreglado). Seguridad: 0 hallazgos. La segunda aprobo con 3 LOW (ver abajo).

## QA 2026-11-05 sobre f0aa83a (resumen)

qa 20261105T1613Z-cAimE1D: los cuatro criterios con evidencia (curl en base
vacia y sembrada, Chromium, API abortada), tres mutaciones que hacen caer sus
tests, e2e nuevos 20 de 20. `omc-verifier`: PASS. Veredicto `aprobado`.

## Para el humano

- 2026-11-05 (qa 20261105T1613Z-cAimE1D): LOW sin arreglar, no bloquean: `/api` sin barra final sirve la SPA (regex `^api/`); `useApi` no limpia `error` al cambiar de path (un instante de "Revisa que Django esté corriendo" yendo de un id inexistente a uno valido sin desmontar; arreglo `setError(null)` en el efecto).
