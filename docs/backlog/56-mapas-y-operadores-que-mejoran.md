# 56. Mapas y operadores que mejoran y empeoran

estado: entregado
candado: -
rama: claude/equipo-dev/56-mapas-y-operadores-que-mejoran
tipo: funcionalidad
epica: progreso
area: fullstack
prioridad: 3
fuente: ALCANCE.md E5 y E10
archivos: backend/replays/analytics/aggregates.py, backend/replays/views.py, backend/tests/test_compare.py, frontend/src/pages/Trends.jsx, frontend/e2e/humo.spec.js, docs/metricas.md
turnos: po 20261019T0004Z, arquitecto 20261022T0804Z, dev 20261022T1204Z, revisor 20261022T1604Z, qa 20261022T2004Z, release 20261023T0004Z

## PR

Titulo: `[equipo-dev][fullstack] Tendencias: mapas y operadores que mejoran y empeoran`

### Que cambia

Tendencias suma, dentro del panel Progreso, dos tablas: "Mapas" y
"Operadores" (operador + lado). Cada fila compara tus ultimas N partidas
contra las N anteriores: rondas, winrate y rating de cada periodo, el cambio
y el veredicto `mejor`/`peor`/`ruido` con la misma banda de ruido del total.
Solo salen las filas con 10+ rondas en los dos periodos. `/api/compare/`
trae `by_map`, `by_operator` y `min_rows` (parametro GET opcional).

### Por que esto y no otra cosa

Ficha 56, tramo de la epica `progreso` (ALCANCE.md E5 y E10). Reusa
`group_by` sobre los dos periodos que `compare_periods` ya arma: sin
migracion ni endpoint nuevo. Se descarto usar la muestra del total (20
rondas) por fila: con 10 partidas la tabla de operadores quedaria vacia.

### Como se probo

- `./scripts/check.sh` sobre la rama con `main` (ec438f9, con la 60 ya
  mergeada) fusionado: `Todo en verde.` (745 tests backend, 120 frontend,
  build ok, 45 e2e).
- `backend/tests/test_compare.py`: mapa que sube sale `mejor`, sin muestra
  en un periodo no sale, orden por delta, operador partido por lado, rating
  por periodo, rondas sin operador no forman fila, base vacia, `by=days` +
  filtro de lado, `min_rows` por parametro, veredicto del total sin cambios.
- e2e `Tendencias muestra mapas y operadores que cambian` (sobre
  `seed_demo`: mapas vacio y 6 filas de operadores, consola limpia).
- QA: `curl` con parametros borde sobre base vacia y sembrada (cero 500),
  pasada en Chromium y mutaciones que tumban los tests nuevos.

### Riesgos y lo que no entra

Sin migracion ni `recompute`. El JSON de `/api/compare/` crece con claves
nuevas. Fuera: sitios, compañeros, graficos por mapa en el tiempo, cambiar
la muestra o la formula del total.

### Como probarlo en 2 minutos

```
cd backend; python manage.py runserver
```
Abrir `http://127.0.0.1:8000/tendencias`: debajo de la tabla de Progreso
aparecen "Mapas" y "Operadores". `curl "http://127.0.0.1:8000/api/compare/?n=10"`
trae `by_map` y `by_operator`.

Verificar en el PC: con la base real, ventana 10 y 30 partidas, contar filas
de "Operadores"; si con 10 casi ninguna aparece, bajar
`COMPARE_MIN_ROUNDS_FILA` a 8 en `backend/replays/analytics/aggregates.py`.

### Para el humano

Nada que decidir; solo el aviso de calibracion de arriba.

### Candidatos descubiertos

Ninguno.

## Que gana quien usa la app

Tendencias compara hoy el total de tus ultimas N partidas contra las N
anteriores, pero no dice donde cambio. Con el mismo corte por mapa y por
operador ves en que mapa estas mejorando, cual se te cae y si el operador que
practicas rinde, con la banda de ruido que ya separa lo real de lo casual.

## Criterios de aceptacion

- [ ] `compare_periods` (o una funcion hermana en `aggregates.py`) devuelve,
  ademas del total, `by_map` y `by_operator`: por cada mapa (`map_slug`) y por
  cada par operador + lado con al menos `min_rounds` rondas en **los dos**
  periodos, rondas de cada periodo, winrate de ronda y rating actual y previo,
  delta, `noise` (el mismo `_ruido` del total) y `verdict`
  (`mejor`/`peor`/`ruido`). Lo que no llega a la muestra en un periodo no
  aparece. Test de Django con dos periodos sinteticos: un mapa que sube 30
  puntos con muestra sale `mejor`, uno sin muestra en el periodo previo no
  sale.
- [ ] Las filas vienen ordenadas por `delta` de winrate, de mayor a menor.
  Test.
- [ ] Respeta `by=matches|days` y `n` como el total, y los filtros de la barra
  que no son de tiempo. Test con `?by=days&n=30` y con `?side=defense`.
- [ ] `Trends.jsx` muestra dos tablas debajo de la comparacion actual ("Mapas"
  y "Operadores"), con el delta coloreado solo si el veredicto no es
  `ruido`; sin filas, "Sin muestra en los dos periodos". Entra al e2e sobre
  `seed_demo` (la pagina renderiza las dos tablas sin errores de consola).
- [ ] Fila en `docs/metricas.md` (seccion de comparacion de periodos) con la
  muestra minima y que significa el veredicto por fila.

## Fuera de alcance

- Sitios, compañeros u otras dimensiones: solo mapa y operador.
- Graficos de evolucion por mapa en el tiempo.
- Cambiar la muestra minima o la formula del ruido del total.

## Diseno

Arquitecto 20261022T0804Z. Corte con `group_by` sobre los dos periodos de
`compare_periods`; `_veredicto` extraido sin cambiar el total;
`COMPARE_MIN_ROUNDS_FILA = 10` por fila y periodo; `by_map` y `by_operator`
ordenados por delta desc; dos `DataTable` en `Trends.jsx`; e2e y fila en
`docs/metricas.md`. Detalle en `git log`.

## Implementacion

Dev 20261022T1204Z. Todo el diseno, mas `min_rows` en la vista. Sin desvios
de fondo. Revision ciega previa sin bloqueantes. Pendiente solo la
calibracion con la base real (Verificar en el PC).

## Revision 2026-10-22 sobre 6a5644a

Revisor 20261022T1604Z. Revision ciega sin hallazgos; numeros de los asserts
confirmados a mano; e2e cuadra con `seed_demo`. Veredicto: aprobar.

## QA 2026-10-22 sobre 6fe9317

QA 20261022T2004Z. `check.sh` en verde; chunk inicial sin crecer; `curl`
con bordes sobre base vacia y sembrada (cero 500, cuentas a mano
coinciden); UI en Chromium con filas y chips; 4 mutaciones tumban los tests
nuevos. Veredicto: `aprobado`.

## Para el humano

- Aviso (no bloquea): `COMPARE_MIN_ROUNDS_FILA = 10` se calibro solo con datos sinteticos. Calibrar con la base real: abrir `/tendencias` con ventana 10 y 30 partidas y contar filas de "Operadores"; si con 10 casi ninguna aparece, bajar la constante a 8 en `backend/replays/analytics/aggregates.py`.
