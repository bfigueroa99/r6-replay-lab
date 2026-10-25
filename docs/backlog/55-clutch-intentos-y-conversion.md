# 55. Clutch: intentos y conversion por X

estado: entregado
candado: -
rama: claude/equipo-dev/55-clutch-intentos-y-conversion
tipo: funcionalidad
epica: impacto
area: fullstack
prioridad: 2
fuente: ALCANCE.md K3 ([Siege.GG](https://siege.gg/blog/946-player-rating-rebalance), [vlr.gg](https://www.vlr.gg/713548/vlr-cl-knowers-come))
archivos: backend/replays/analytics/metrics.py, backend/replays/models.py, backend/replays/migrations/0003_roundplayer_clutch_vs.py, backend/replays/ingest.py, backend/replays/recompute.py, backend/replays/analytics/aggregates.py, backend/replays/views.py, backend/replays/management/commands/seed_demo.py, backend/tests/test_clutch.py, backend/tests/test_recompute.py, backend/tests/factories.py, frontend/src/pages/Teammates.jsx, frontend/e2e/humo.spec.js, docs/metricas.md
turnos: po 20261019T0004Z, arquitecto 20261019T0404Z, dev 20261019T0804Z, revisor 20261019T1604Z, dev 20261019T2004Z, revisor 20261020T0003Z, qa 20261020T0404Z, release 20261020T0804Z


## PR

Titulo: `[equipo-dev][fullstack] Clutch: intentos y conversión por rivales`

### Que cambia

Compañeros -> Clutches muestra arriba una tabla nueva, "Conversión por
rivales": por cada 1vX (1v1 a 1v5+) cuántas veces quedaste último de tu
equipo, cuántas ganaste y el %, total y por lado. Hasta ahora la app solo
contaba los clutches ganados (`one_vx`); ahora se ven también los perdidos.
Columna nueva `RoundPlayer.clutch_vs` (migración `0003`) calculada al
importar, por `recompute` y por la propia migración con la misma función.

### Por que esto y no otra cosa

Ficha 55, tramo K3 de la épica `impacto` en `ALCANCE.md` (Siege.GG, vlr.gg).
La parte "cuántos se esperaban" queda para cuando exista la tabla de K1.
`one_vx`, el Rating, el récord "Clutch más grande" y la regla del Coach no
cambian.

### Como se probo

- `./scripts/check.sh` en esta sesión sobre la rama al día con `main`:
  Todo en verde (711 tests backend, 115 frontend, build, 44 e2e).
- Tests nuevos: `tests/test_clutch.py` (función pura: 1v3, 1v1 a los dos,
  `PlayerLeave` como muerte, solo desde el inicio, valor que no se pisa,
  nick desconocido; import; conversión por X y lado, 5+ agrupado, ronda sin
  ganador fuera, API con `?side=`; migración), `RecomputeClutchTests` en
  `test_recompute.py`, e2e `Compañeros muestra la conversion de clutch`.
- Dos revisiones independientes (la primera encontró CRLF del README y el
  caso "solo desde el inicio", corregidos) y QA con base sintética, `curl`
  de bordes, migración `0002 -> 0003 -> 0002 -> 0003` y prueba de mutación.

### Riesgos y lo que no entra

Migración con `RunPython` sobre la base real al primer `runserver`; tolera
rondas sin jugadores y eventos sin nick. `recompute` ahora también corrige
`clutch_vs`. Afuera: K3 "esperados", clutches de compañeros o rivales.

### Como probarlo en 2 minutos

```bash
cd backend && python manage.py seed_demo --force && python manage.py runserver
curl -s localhost:8000/api/teammates/ | python -m json.tool | grep -A3 '"label"'   # 1v1 2/2 y 1v2 8/0
curl -s 'localhost:8000/api/teammates/?side=Defense' | python -m json.tool | grep -c '"label"'
```

En la UI: Compañeros -> Clutches, tabla "Conversión por rivales" arriba y
"Clutches ganados" debajo.

### Verificar en el PC

Con la base real (antes `POST /api/backup/` o copia de `data/db.sqlite3`):

```powershell
cd backend; ..\.venv\Scripts\python.exe manage.py migrate
..\.venv\Scripts\python.exe manage.py recompute --dry-run   # esperado: sin cambios de clutch_vs
```

Compañeros -> Clutches: intentos >= clutches ganados de la lista de abajo.

### Para el humano

Avisos, sin decisión pendiente: (1) si `clutch_vs` y `one_vx` difieren en el
X de una ronda ganada, la tabla agrupa por `clutch_vs` (reversible; avisar
si se prefiere unificar). (2) Con `.rec` anteriores a Y9S1, mirar si
aparecen `PlayerLeave` después del final de la ronda: contarían intentos
falsos (el `1vX` de `pydissect/stats.py` comparte el supuesto).

### Candidatos descubiertos

Ninguno (la 59, clutch por mapa y sitio, ya está en `propuesto`).

## Que gana quien usa la app

Hoy la app solo cuenta los clutches que ganaste (`one_vx`): no sabes cuántas
veces quedaste último y la perdiste. Con los intentos se ve el % real de
conversión en 1v1, 1v2, 1v3... por lado.

## Criterios de aceptacion

- [x] `RoundPlayer.clutch_vs` al importar, gane o pierda, con `Kill`,
  `Death` y `PlayerLeave` como muerte.
- [x] Migración y `recompute` llenan lo ya importado.
- [x] `/api/teammates/` -> `clutch_conversion` por X (5+ agrupado) y lado,
  con los filtros de la barra.
- [x] Tabla en Compañeros -> Clutches con texto vacío; en el e2e.
- [x] Fila "Clutch: intentos y conversión" en `docs/metricas.md`.

## Resumen del camino

- Diseño (arquitecto 20261019T0404Z): función pura `metrics.clutch_vs`
  única para import, `recompute` y migración.
- Implementación (dev 20261019T0804Z): todo el diseño; desvíos explicados:
  `management/commands/recompute.py` y una línea del README.
- Revisión 2b44e75: corregir. Hallazgos corregidos por dev 20261019T2004Z:
  README volvía a LF (restaurado CRLF, diff de 1 línea) y quedar solo desde
  el inicio no contaba (`marcar_solos()` antes del loop + 2 tests).
- Revisión a96ed14: aprobar, sin hallazgos.
- QA b70e347: aprobado; los 5 criterios con evidencia y 6 mutaciones que
  hacen caer sus tests. Detalle completo en `git log` de la rama.
