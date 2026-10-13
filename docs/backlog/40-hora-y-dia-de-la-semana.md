# 40. Rendimiento por hora del dia y dia de la semana

estado: propuesto
candado: -
rama: -
tipo: funcionalidad
epica: progreso
area: fullstack
prioridad: 3
fuente: ALCANCE.md E3 (idea del PO 20261013T0511Z)
archivos: backend/replays/analytics/aggregates.py, backend/replays/views.py, frontend/src/pages/Trends.jsx, docs/metricas.md, backend/tests/, frontend/e2e/
turnos: po 20261013T1915Z

## PR

(La escribe el Release manager al final.)

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

(Arquitecto) Toca `Trends.jsx` y `trends` igual que la 39 y la 41: si se
disenan juntas, ordenar la implementacion para que no choquen.

## Para el humano

Nada por ahora.
