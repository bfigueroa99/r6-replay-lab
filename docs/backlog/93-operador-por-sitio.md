# 93. Operador por sitio contra el resto del sitio

estado: entregado
candado: -
rama: claude/equipo-dev/93-operador-por-sitio
tipo: funcionalidad
epica: paridad-referencia
area: fullstack
prioridad: 3
fuente: O1 de ALCANCE.md; `replica/features.csv` "Delta de win rate de un operador contra la base, por mapa y sitio" (must, partial: la ficha 65 da el delta contra tu lado, falta el corte por mapa y sitio); [aurelix](https://aurelix.app/blog/how-to-analyse-r6-siege-replays)
archivos: backend/replays/analytics/aggregates.py, backend/replays/views.py, backend/replays/urls.py, backend/tests/test_operador_por_sitio.py, frontend/src/operadorSitio.js, frontend/src/operadorSitio.test.js, frontend/src/pages/Operators.jsx, frontend/e2e/humo.spec.js, docs/metricas.md
turnos: po 20261105T1945Z-cvqUYh1, arquitecto 20261106T0109Z-cMAPx7f, dev 20261106T0135Z-cYfUHhx, revisor 20261106T0200Z-cC8Xgpa, dev 20261106T0228Z-c6PJnck, revisor 20261106T0228Z-cgEzFUY, qa 20261106T0252Z-c2pqRwT, release 20261106T0252Z-c2pqRwT

## PR

Titulo: `[equipo-dev][backend] Operador por sitio contra el resto del sitio`

### Que cambia

En Operadores aparece el panel **Por sitio**: con que operador ganas mas o menos rondas en un sitio que con el resto de tus operadores ahi (mismo mapa por version, sitio y lado), con margen de ruido y veredicto *Te rinde* / *Te hunde* / *Sin señal*. Endpoint nuevo `GET /api/operators/sites/` (`?min_rounds=`, default 10), que respeta los filtros de la barra.

### Por que esto y no otra cosa

Ficha 93, idea O1 de `ALCANCE.md` (paridad con la referencia: delta de winrate de un operador por mapa y sitio). Endpoint propio en vez de una clave en `/api/operators/`: tiene su propio minimo. Se compara contra el resto del sitio y no contra el total, que contiene al operador (mismo criterio que Fuera de posicion, ficha 80).

### Como se probo

- `check.sh` (con `verificar.sh`): VERDE en la QA sobre 5898350 (1030 tests backend, 227 vitest, 69 e2e) y de nuevo sobre el commit de entrega.
- `backend/tests/test_operador_por_sitio.py` (14): rinde/hunde con numeros fijos, ruido, resto y no total, orden por mayor diferencia, minimo del operador y del resto, rondas sin ganador, sin sitio/lado/operador, otro lado u otro sitio no es el resto, versiones de un mapa separadas, filtro de operador que no vacia el resto, filtros de lado y mapa, base vacia, solo GET.
- `frontend/src/operadorSitio.test.js`: etiquetas, clases, texto vacio con el minimo de la api, orden del backend.
- e2e `Operadores muestra el operador por sitio` (humo.spec.js): texto vacio con `seed_demo`, tabla con `min_rounds=5` y orden por |delta| con respuesta simulada; consola limpia.
- QA: runserver con base vacia y sembrada desde `factories.py`, numeros cuadrados a mano, 24 parametros borde, filtros de la barra en Chromium, chunk inicial +0.07 %, 4 mutantes que caen.
- OMC: plan=— · revisión=— · verificación=— (diseno)
- OMC: plan=— · revisión=2 hallazgos (2 arreglados) · verificación=— (implementacion)
- OMC: plan=— · revisión=3 hallazgos (1 cubierto con test, 1 LOW al humano, 1 descartado) · verificación=— (revision)
- OMC: plan=— · revisión=— · verificación=PASS (QA)

### Riesgos y lo que no entra

Sin migracion ni `recompute`: se calcula al consultar sobre columnas que ya existen. El minimo 10 esta calibrado con datos sinteticos; con la base real la tabla puede quedar corta (se baja en `OPERADOR_SITIO_MIN_RONDAS` y `metricas.md`). Fuera: señal del Coach, operadores rivales por sitio (D2), corte por temporada (A3).

### Como probarlo en 2 minutos

```powershell
cd backend; python manage.py test tests.test_operador_por_sitio
python manage.py runserver
```

Abrir `http://127.0.0.1:8000/operadores`, panel **Por sitio** al final. Con la base real: elegir un mapa o Lado = Solo defensa en la barra y ver que las filas se recortan; `http://127.0.0.1:8000/api/operators/sites/?min_rounds=5` muestra mas filas.

### Para el humano

Nada que decidir. Aviso LOW del revisor: el texto vacio dice "Ningún operador llega a N rondas" tambien cuando el que no llega es el resto del sitio.

### Candidatos descubiertos

Ninguno.

## Que gana quien usa la app

En Operadores, una tabla por mapa y sitio que dice con que operador ganas mas
o menos rondas en ese sitio que con el resto de tus operadores ahi: que
operador te rinde en Cocina de Oregon y cual te hunde. Hoy el winrate por
operador (ficha 65) y por sitio van por separado, y la referencia los cruza.

## Criterios de aceptacion

- [x] Endpoint (o clave nueva en `/api/operators/`, a eleccion del
      Arquitecto) con filas `mapa (version) / sitio / lado / operador`:
      rondas, winrate, winrate del resto del sitio (mismas mapa, sitio y lado,
      otros operadores), delta y margen de ruido. Respeta los filtros globales.
- [x] Solo filas con al menos 10 rondas del operador en ese sitio y al menos
      10 rondas del resto; el minimo vive en una constante y en
      `docs/metricas.md`.
- [x] La comparacion es contra el resto del sitio, no contra el total del
      sitio (el operador esta dentro del total: mismo motivo que
      `_contra_el_resto` de la ficha 80), con banda de ruido de proporcion
      combinada (`_ruido_combinado`): veredicto `rinde`, `hunde` o `ruido`.
      Test con numeros fijos de `factories.py` para los tres veredictos.
- [x] Rondas sin ganador (`my_team_won` nulo) y rondas sin sitio u operador
      quedan fuera del numerador y del denominador; test.
- [x] En Operadores se ve la tabla nueva, ordenada por |delta|, con texto
      cuando no hay filas con muestra suficiente; e2e con los numeros de
      `seed_demo` (o el texto vacio si el seed no llega a 10 rondas: el
      Arquitecto decide si baja el minimo por parametro en el e2e o ajusta el
      seed).
- [x] Fila nueva en `docs/metricas.md` con la definicion y el minimo.

## Fuera de alcance

- Señal nueva del Coach sobre esto (si sirve, otra ficha).
- Operadores rivales por sitio (D2, otra idea).
- Corte por temporada (A3).

## Diseno, implementacion y revision (resumen)

Diseno (arquitecto cMAPx7f): endpoint propio `GET /api/operators/sites/`,
`operator_by_site()` en `aggregates.py` con una consulta agrupada por mapa
(version), sitio, lado y operador; totales del sitio en Python antes del
minimo; resto = total - operador; `_margen_y_veredicto(..., ("rinde",
"hunde"))`; el filtro `operator` recorta filas, no la base; solo rondas con
ganador. Implementacion (dev cYfUHhx, correccion c6PJnck): todo el diseno,
mas un paso de e2e que renderiza la tabla y tests extra de mapa y 405.

Revision 1 (cC8Xgpa): HIGH, la tabla salia ordenada por Mapa (default de
`DataTable`) y no por |delta|; LOW, test de rondas sin sitio que no caia con
el mutante. Los dos corregidos (`conOrdenDelBackend` + `initialSort`, tandas
de 10 sin sitio). Revision 2 (cgEzFUY): aprobar; agrego
`test_las_filas_salen_por_mayor_diferencia_y_no_por_nombre_ni_rondas`
(el orden del backend no tenia test). Detalle en `git log`.

## QA 2026-11-06 sobre 5898350 (resumen)

(qa c2pqRwT) `verificar.sh` VERDE 5898350 (1030/227/69). Base vacia: 200 con
`rows: []`, pagina vacia de siempre. Base sembrada (factories): 9 filas que
cuadran a mano (Ash Club House 20 rondas sin las 5 sin ganador, resto 32 =
Zofia 20 + Sledge 12, 40.6 %, +49.4 ± 28.0, rinde; compañero, sin sitio y
sin operador fuera; Consulate Y7/Y10 separados). 24 parametros borde, todos
200 y coherentes con `/api/operators/`. UI en Chromium: filtros de lado,
version de mapa y tipo recortan el panel; con 0 rondas manda
`SinRondasFiltradas`; consola limpia. Chunk inicial +0.07 %. Mutantes (resto
= total, sin filtro de ganador nulo, operador en la base, minimo solo del
operador): los 4 caen.

OMC: plan=— · revisión=— · verificación=PASS

## Para el humano

- (revisor cgEzFUY, LOW, no bloquea) El texto vacio de la tabla Por sitio dice "Ningún operador llega a N rondas" tambien cuando el que no llega es el resto del sitio; podria ser "Ninguna combinación de operador y sitio llega a N rondas propias y N del resto."
