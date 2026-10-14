# 40. Rendimiento por hora del dia y dia de la semana

estado: revisado
candado: qa 2026-10-14T07:12Z
rama: claude/equipo-dev/40-hora-y-dia-de-la-semana
tipo: funcionalidad
epica: progreso
area: fullstack
prioridad: 3
fuente: ALCANCE.md E3 (idea del PO 20261013T0511Z)
archivos: backend/replays/analytics/aggregates.py, backend/replays/views.py, frontend/src/pages/Trends.jsx, docs/metricas.md, backend/tests/test_hora_y_dia.py, frontend/e2e/humo.spec.js
turnos: po 20261013T1915Z, arquitecto 20261013T2011Z, dev 20261014T0511Z, revisor 20261014T0611Z, qa 20261014T0712Z

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

(Arquitecto 20261013T2011Z, sobre main 5d2aecc. Spike en el scratchpad con
`seed_demo`: franjas [28, 28, 28, 21, 21, 21, 28, 28] y dias
[56, 56, 21, 0, 0, 14, 56], las dos suman 203 = total.)

**Implementar despues de que #41 se mergee** (y la 41 despues de la 39):
usa `_filas_por_tramo`, `TablaDeCorte` y `muestra.js` de la 39 y toca los
mismos archivos. Prioriza, no bloquea; si se implementa antes, crear esos
ayudantes con los nombres y firmas del diseno de la 39.

**Archivos y por que**

- `backend/replays/analytics/aggregates.py`:
  - `by_hour(**filters)`: 8 tramos `qs.filter(round__match__played_at__hour__gte=h, round__match__played_at__hour__lt=h + 3)`
    para `h in range(0, 24, 3)`. Filas `{"hour_from": h, **totals}` con un
    solo `rating_baseline()` (no usar `_filas_por_tramo` tal cual porque la
    clave es un entero; si se generaliza para aceptar claves int, mejor).
  - `by_weekday(**filters)`: 7 tramos `qs.filter(round__match__played_at__iso_week_day=d)`
    para `d in 1..7`, filas `{"weekday": d, **totals}`. Usar
    `iso_week_day` (1=lunes) y **no** `week_day` (1=domingo): comentario
    corto con ese por que.
  - Hora tal cual esta en la base (`USE_TZ = False`, hora local del PC):
    sin conversion. 15 `totals()` son ~30 consultas chicas; con miles de
    rondas sigue siendo instantaneo en SQLite. No hace falta agrupar en SQL.
- `backend/replays/views.py`: `"by_hour"` y `"by_weekday"` en `trends`.
- `frontend/src/pages/Trends.jsx`: dos paneles despues de "Según el marcador"
  y antes de "Por numero de ronda", con `TablaDeCorte`:
  - "Por hora del día": etiqueta `${h}–${h + 3} h` (ej. "21–24 h"),
    `csvName="por-hora"`. Hint: "Hora de inicio de la partida, tal como la
    guardó tu PC."
  - "Por día de la semana": `['Lunes','Martes','Miércoles','Jueves','Viernes','Sábado','Domingo'][weekday - 1]`,
    `csvName="por-dia"`.
  - Las filas en 0 se muestran (son fijas y dicen "no juegas a esa hora");
    aviso de `filasConPocaMuestra` en el hint como en la 39.
- `docs/metricas.md`: seccion `## Cuando juegas` (despues de `## Sesiones`)
  con **Por hora del dia** (franjas de 3 h por la hora de inicio de la
  partida, hora local guardada, sin zona horaria; una partida que cruza la
  medianoche cuenta entera en la franja en que empezo) y **Por dia de la
  semana** (lunes a domingo del inicio de la partida).
- `backend/tests/test_hora_y_dia.py` (nuevo), con `make_match(played_at=...)`:
  - `test_ocho_franjas_fijas_aunque_no_haya_rondas` (`hour_from` 0..21, rounds 0)
  - `test_siete_dias_fijos_de_lunes_a_domingo`
  - `test_domingo_23_30_y_lunes_00_30_caen_en_su_dia_y_su_franja`
    (2026-09-06 es domingo: 23:30 -> weekday 7 y franja 21; 2026-09-07
    00:30 -> weekday 1 y franja 0)
  - `test_las_filas_suman_las_rondas_del_resumen` (las dos listas)
  - `test_base_vacia_y_filtros_raros_dan_200`
- `frontend/e2e/humo.spec.js`: `Tendencias muestra hora y dia de la semana`:
  paneles por titulo, celdas "21–24 h", "Lunes" y "Domingo", consola limpia.

**Orden:** test backend -> aggregates -> views -> Trends.jsx -> e2e ->
metricas.md -> `check.sh`.

**Que puede romperse:** nada de base; el guion largo `–` en las etiquetas
tiene que coincidir entre Trends.jsx y el e2e (copiarlo, no tipearlo).
`seed_demo` no cambia.

**Verificacion manual:** `seed_demo`, `/api/trends/` -> las sumas de arriba,
y `/tendencias` con jueves y viernes en 0.

## Implementacion

(Dev 20261014T0511Z, sobre main a233a03.)

Quedo el diseno completo, sin desvios de alcance:

- `aggregates.by_hour` (8 franjas fijas `hour_from` 0..21 con `__hour__gte/lt`)
  y `aggregates.by_weekday` (7 dias `weekday` 1..7 con `iso_week_day`), los dos
  sobre `_filas_por_tramo`, que ahora acepta claves `int` (solo cambio el type
  hint; la 39 ya la habia dejado generica en el cuerpo).
- `/api/trends/` suma `by_hour` y `by_weekday`.
- Tendencias: paneles "Por hora del día" (`21–24 h`, CSV `por-hora`) y "Por día
  de la semana" (CSV `por-dia`) con `TablaDeCorte` y aviso de muestra chica,
  entre "Según el marcador" y "Por numero de ronda". Filas en 0 visibles.
- `docs/metricas.md`: seccion `## Cuando juegas` despues de `## Sesiones`, y la
  fila de muestra minima de los cortes de Tendencias nombra hora y dia.
- Tests (`backend/tests/test_hora_y_dia.py`, 8): los cinco del diseno mas
  `test_el_borde_de_la_franja_es_la_hora_de_inicio` (2:59 / 3:00),
  `test_cada_fila_trae_las_metricas_de_siempre` y
  `test_trends_con_datos_trae_hora_y_dia`. La prueba de sumas usa filtros de
  mapa y de lado que recortan de verdad (lo pidio la revision ciega previa).
- e2e: `Tendencias muestra hora y dia de la semana` (paneles, "21–24 h",
  "Lunes", "Domingo", consola limpia).

Criterio -> test: `by_hour` -> `test_ocho_franjas_fijas_aunque_no_haya_rondas`;
`by_weekday` y borde domingo/lunes -> `test_siete_dias_fijos_de_lunes_a_domingo`,
`test_domingo_23_30_y_lunes_00_30_caen_en_su_dia_y_su_franja`; sumas ->
`test_las_filas_suman_las_rondas_del_resumen`; UI -> e2e; base vacia y filtros
raros -> `test_base_vacia_y_filtros_raros_dan_200`.

Revision ciega previa: 2 hallazgos (archivo de tests sin trackear, filtro de
lado que no recortaba), los dos corregidos.

## Revision 2026-10-14 sobre 4f01bb7

(Revisor 20261014T0611Z. Revision ciega con el prompt de `revision.md` sobre el diff sin
`docs/backlog`, despues confirmacion del lider. `check.sh` en verde sobre la rama,
que ya contiene main a233a03: 520 tests backend, 69 vitest, build ok, 29 e2e.)

Hallazgos:

- [bug, menor, preexistente] backend/replays/ingest.py:313 (lo expone aggregates.py:469)
  Que pasa: si el header del `.rec` no trae `datetime` o lo trae invalido,
  `_parse_ts` cae a `datetime.now()` y la partida cuenta en la franja y el dia
  en que se importo, no en los que se jugo.
  Como reproducirlo o por que es cierto: confirmado leyendo `_parse_ts`; un
  header con `datetime=foo` importado un martes a las 10:00 suma sus rondas a
  "9–12 h" y "Martes". El fallback ya existia y ya afectaba la fecha y las
  sesiones; con los `.rec` reales el campo siempre viene, asi que no bloquea.
  Arreglo sugerido: ficha aparte si alguien lo ve en datos reales (marcar las
  partidas sin hora real y sacarlas de estos cortes); no se amplia esta.

Ficha:

- Cada criterio tiene test o verificacion: `by_hour` 8 franjas fijas y borde
  2:59/3:00, `by_weekday` con `iso_week_day` y el cruce domingo 23:30 / lunes
  00:30, sumas iguales a `overview` con filtros que recortan de verdad (16 y
  24 rondas), base vacia y filtros raros 200, paneles y celdas en el e2e.
- El diff no toca archivos fuera de `archivos:`.
- `docs/metricas.md` tiene `## Cuando juegas` y la fila de muestra minima
  actualizada; las filas en 0 no disparan el aviso (`filasConPocaMuestra`
  exige `rounds > 0`).
- Identificadores y comentarios sin tildes; UI con tildes (`Miércoles`,
  `Sábado`, `Por día de la semana`); sin `print` ni `console.log`.

Veredicto: aprobar.

## Para el humano

Nada por ahora.
