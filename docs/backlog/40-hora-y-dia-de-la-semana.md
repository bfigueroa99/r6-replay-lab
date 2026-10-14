# 40. Rendimiento por hora del dia y dia de la semana

estado: entregado
candado: -
rama: claude/equipo-dev/40-hora-y-dia-de-la-semana
tipo: funcionalidad
epica: progreso
area: fullstack
prioridad: 3
fuente: ALCANCE.md E3 (idea del PO 20261013T0511Z)
archivos: backend/replays/analytics/aggregates.py, backend/replays/views.py, frontend/src/pages/Trends.jsx, docs/metricas.md, backend/tests/test_hora_y_dia.py, frontend/e2e/humo.spec.js
turnos: po 20261013T1915Z, arquitecto 20261013T2011Z, dev 20261014T0511Z, revisor 20261014T0611Z, qa 20261014T0712Z, release 20261014T0811Z

## PR

**Titulo:** `[equipo-dev][fullstack] Rendimiento por hora del dia y dia de la semana en Tendencias`

### Que cambia

Tendencias suma dos paneles, "Por hora del día" (8 franjas fijas de 3 h) y
"Por día de la semana" (lunes a domingo), con rondas, winrate, rating, CSV y
aviso de muestra chica. `/api/trends/` devuelve `by_hour` y `by_weekday`,
segun la hora de inicio de la partida tal como quedo guardada.

### Por que esto y no otra cosa

Ficha 40, epica `progreso` (ALCANCE E3). La hora ya estaba en cada partida y
ninguna pantalla la usaba. Descartados: zona horaria configurable (la base
guarda hora local) y el cruce hora x dia 7x8 (la muestra no alcanza).

### Como se probo

- `./scripts/check.sh` en `Todo en verde.` sobre la rama con `main` a233a03
  fusionado: 520 tests backend (4 skipped), 69 frontend, build ok, 29 e2e.
- Tests nuevos (`backend/tests/test_hora_y_dia.py`, 8): ocho franjas fijas sin
  rondas; siete dias fijos; domingo 23:30 y lunes 00:30 caen en su dia y su
  franja (`iso_week_day`, no `week_day`); borde 2:59 / 3:00; cada fila trae
  las metricas de `totals()`; las filas suman las rondas de `/api/overview/`
  con filtros que recortan; base vacia y filtros raros dan 200; trends con
  datos. E2E `Tendencias muestra hora y dia de la semana`.
- QA: `seed_demo` da franjas [28, 28, 28, 21, 21, 21, 28, 28] y dias
  [56, 56, 21, 0, 0, 14, 56] (203 rondas); sumas = overview con 11 combinaciones
  de filtros; mutaciones (`week_day`, `hour__lte`, sin franja 0, etiquetas
  corridas) caen todas; chunk inicial sin cambio.

### Riesgos y lo que no entra

Sin migracion, sin parser, sin `recompute`: se calcula al consultar desde
`Match.played_at`. ~30 consultas chicas por pedido, instantaneo en SQLite.
Una partida que cruza la medianoche cuenta entera donde empezo. Fuera: zona
horaria y mapa de calor hora x dia.

### Como probarlo en 2 minutos

```
cd backend; python manage.py seed_demo; python manage.py runserver
```

Abrir `http://localhost:8000/tendencias`: paneles "Por hora del día" (filas
"0–3 h" a "21–24 h") y "Por día de la semana" con jueves y viernes en 0. En
`http://localhost:8000/api/trends/`, `by_hour` y `by_weekday` suman 203.

### Para el humano

Nada que decidir. Avisos: con datos reales casi siempre habra una franja con
menos de 30 rondas, asi que el hint mostrara el aviso de muestra chica en vez
de la explicacion de la hora; y una partida con `datetime` invalido en el
header cae en la hora de importacion (preexistente, `ingest._parse_ts`).

### Candidatos descubiertos

Ninguno.

## Que gana quien usa la app

Saber si juegas peor de madrugada o los domingos, con la muestra a la vista
para no creerle a 6 rondas. La hora ya esta guardada en cada partida y ninguna
pantalla la usa.

## Criterios de aceptacion

- [ ] `GET /api/trends/` devuelve `by_hour`: 8 filas fijas de 3 horas
      (`0-3`, `3-6`, ..., `21-24`, campo `hour_from` 0..21) segun la hora
      local de `Match.played_at` (la base guarda hora local, `USE_TZ = False`),
      con las metricas de `totals()` y las franjas sin rondas en 0.
- [ ] `GET /api/trends/` devuelve `by_weekday`: 7 filas fijas de lunes a
      domingo (campo `weekday` 1=lunes .. 7=domingo, ISO), con las metricas
      de `totals()`. Test con partidas en domingo 23:30 y lunes 00:30 que
      caen en el dia y la franja correctos (el borde de `ExtractWeekDay` de
      Django, que cuenta 1=domingo, es justo lo que se rompe facil).
- [ ] La suma de `rounds` de `by_hour` y la de `by_weekday` es igual a
      `rounds` de `/api/overview/` con los mismos filtros.
- [ ] Tendencias muestra dos paneles "Por hora del día" y "Por día de la
      semana" con rondas, winrate y rating, CSV, y aviso de muestra chica en
      las filas con menos de 30 rondas.
- [ ] `docs/metricas.md` tiene las filas; el e2e de Tendencias ve los dos
      paneles con `seed_demo` (que ya reparte partidas cada 3 horas) sin
      errores de consola. Base vacia y filtros raros devuelven 200.

## Fuera de alcance

- Zona horaria configurable o conversion: se usa la hora tal cual quedo en la
  base.
- Cruces hora x dia (mapa de calor 7x8): la muestra no alcanza; otra ficha si
  alguien lo pide.
- Sesiones: ya tienen su vista (`/api/sessions/`).

## Diseno

(Arquitecto 20261013T2011Z, sobre main 5d2aecc.) `by_hour` con 8 tramos
`__hour__gte/lt` y `by_weekday` con `iso_week_day` (1=lunes; `week_day` cuenta
1=domingo) sobre `_filas_por_tramo`; dos paneles `TablaDeCorte` en Tendencias
entre "Según el marcador" y "Por numero de ronda"; seccion `## Cuando juegas`
en `docs/metricas.md`. Hora tal cual esta en la base, sin conversion. Detalle
en `git log`.

## Implementacion

(Dev 20261014T0511Z, sobre main a233a03.) Diseno completo, sin desvios:
`aggregates.by_hour` y `by_weekday` sobre `_filas_por_tramo` (ahora con claves
`int`), `/api/trends/` los devuelve, paneles en Tendencias con CSV `por-hora` y
`por-dia`, `## Cuando juegas` en metricas, 8 tests en `test_hora_y_dia.py` y el
e2e. Revision ciega previa: 2 hallazgos corregidos.

## Revision 2026-10-14 sobre 4f01bb7

(Revisor 20261014T0611Z, revision ciega + confirmacion; check.sh en verde.)
Veredicto: aprobar. Un hallazgo menor preexistente, no bloquea:
`ingest._parse_ts` cae a `datetime.now()` si el header no trae `datetime`
valido, y esa partida cuenta en la hora de importacion. Detalle en `git log`.

## QA 2026-10-14 sobre fe15095

(QA 20261014T0712Z.) check.sh en verde (520 / 69 / build / 29 e2e). Base
vacia y filtros raros 200; cruce domingo/lunes y borde 2:59:59 / 3:00 donde
dice el criterio; sumas = overview con 11 combinaciones de filtros;
`seed_demo` igual al spike; mutaciones caen todas. Veredicto: aprobado. Nada
que verificar en el PC. Detalle en `git log`.

## Para el humano

Avisos informativos, sin preguntas abiertas:

- (QA) Con datos reales casi siempre habra alguna franja con menos de 30
  rondas, asi que el hint del panel mostrara el aviso de muestra chica y casi
  nunca la explicacion "Hora de inicio de la partida, tal como la guardó tu
  PC". Si molesta, una ficha chica puede mostrar las dos frases.
- (Revisor) Partidas con `datetime` invalido en el header caen en la hora de
  importacion (`ingest._parse_ts`); preexistente, no bloquea.
