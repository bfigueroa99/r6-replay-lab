# 84. Un enlace a una partida o jugador que no existe dice que Django no corre

estado: propuesto
candado: arquitecto 2026-11-05T14:29Z
rama: -
tipo: bug
epica: -
area: fullstack
prioridad: 4
fuente: QA 20261105T0418Z-cq6Wet6, prueba de bordes sobre dev ed39632 con `seed_demo` y Chromium. `frontend/src/components/ui.jsx:236` (`ErrorBox`) trata todo error como API caida; `backend/config/urls.py:35` (`re_path(r"^(?P<path>.*)$", spa)`) tambien atrapa `/api/<ruta desconocida>`
archivos: frontend/src/components/ui.jsx, frontend/src/api.js, frontend/src/pages/MatchDetail.jsx, frontend/src/pages/Jugador.jsx, backend/config/urls.py, backend/tests/, frontend/e2e/
turnos: qa 20261105T0418Z-cq6Wet6

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

## Implementacion

## Revision <fecha> sobre <sha>

## QA <fecha> sobre <sha>

## Pendiente
