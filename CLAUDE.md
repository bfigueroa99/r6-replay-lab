# CLAUDE.md

Contexto para trabajar en este repo. Lee tambien `docs/roadmap.md` (backlog) y
`docs/formato-rec.md` (limites del formato).

## Que es

Analizador local de replays de Rainbow Six Siege. Parser propio en Python puro
(`backend/pydissect/`), Django + SQLite para la API, React + Vite para la UI.
Corre entero en el PC del usuario: sin servicios externos, sin cuentas, sin red.

## Comandos

```powershell
cd backend; python manage.py test tests    # suite completa, tiene que quedar en verde
cd backend; python manage.py runserver     # sirve el build de React en la misma URL
cd frontend; npm run build                 # obligatorio si tocas frontend/src
cd frontend; npm test                      # logica pura del frontend (vitest)
cd frontend; npm run e2e                   # end to end sobre la app real (playwright)
cd frontend; npm run e2e:browser           # baja Chromium, una sola vez
cd frontend; npm run dev                   # hot reload en :5173, proxea /api
cd frontend; npm run desktop               # app de escritorio (Electron)
.\scripts\check.ps1                        # lint + tests + build + e2e antes de commitear
.\scripts\check.ps1 -SinE2E                # lo mismo pero sin el e2e
```

El venv esta en `.venv` de la raiz. Desde `backend/` el interprete es
`../.venv/Scripts/python.exe`.

## Reglas de arquitectura

- **`pydissect/` no importa Django.** Es un parser independiente; recibe rutas y
  devuelve dicts. Si necesitas config, pasala como argumento.
- **Sin dependencias nuevas** salvo que no haya alternativa razonable. El
  backend tiene dos y punto: `django` y `zstandard`. Nada de DRF, pandas ni
  requests. En el frontend, `electron` es devDependency y solo la usa la app de
  escritorio: la UI web tiene que seguir funcionando sin ella.
- **La API es de lectura.** Vistas planas con `JsonResponse`, un solo POST
  (`/api/import/`). No agregues serializers ni viewsets.
- **Las metricas se calculan al importar**, no al consultar: `analytics/metrics.py`
  escribe columnas en `RoundPlayer`, y `analytics/aggregates.py` solo agrega.
- **Todo numero que muestra la UI tiene definicion en `docs/metricas.md`.** Si
  agregas una metrica, agregas su fila ahi.

## Estilo

- Comentarios, docstrings y nombres en espanol **sin tildes** (`configuracion`,
  `metricas`). Los textos que ve el usuario en la UI si llevan tildes y ñ
  (`Compañeros`, `Señales`).
- Los comentarios explican *por que*, no *que*. Si el codigo ya lo dice, sobra.
- Tests en espanol, nombres descriptivos (`test_un_cambio_de_nick_no_parte_la_fila`).
- Cada feature nueva llega con tests. La suite no baja de verde nunca.
- Una pagina nueva entra tambien al e2e (`frontend/e2e/`). El build y los tests
  unitarios no ven un error de runtime en una pantalla que nadie renderiza; el
  e2e maneja la app en Chromium y falla si la consola se ensucia. Sus datos
  salen de `manage.py seed_demo`, que es deterministico: si cambias ese comando
  cambias los numeros que afirman las pruebas.

## Lo que el formato .rec NO entrega

No propongas features que dependan de esto (esta documentado en el README):

- **Coordenadas de jugadores o bajas.** No hay heatmap sobre minimapa. La
  granularidad espacial real es sitio de bomba y spawn.
- **Plants y defuses** en temporadas nuevas: solo se infieren del reloj.
- **Asistencias y score por jugador**: los paquetes existen pero ya no se pueden
  atribuir.
- **Armas, dano, disparos, precision.**
- **MMR, rango, historial de temporada, stats de rivales fuera de tus partidas.**
  Eso vive en la API de Ubisoft, que este proyecto no usa a proposito.

## No-goals

- **Overlay in-game. Nunca.** Ni ventana flotante, ni hook al juego, ni captura
  de pantalla, ni lectura de memoria. Es la linea que separa esto de stats.cc y
  de cualquier cosa que Ubisoft pueda leer como cheat.
  La app de Electron **no** es un overlay ni el primer paso hacia uno: es una
  ventana normal con marco, sin always-on-top y sin transparencia. Si alguna
  iteracion propone `alwaysOnTop`, `transparent` o `setIgnoreMouseEvents`, la
  respuesta es no.
- Cuentas, login, telemetria, sincronizacion a la nube.
- Integracion con la API de Ubisoft.
