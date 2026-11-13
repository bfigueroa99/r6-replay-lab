# 126. A qué operador cambias tras perder

estado: entregado
candado: -
rama: claude/equipo-dev/126-a-que-operador-cambias-tras-perder
tipo: funcionalidad
epica: operadores
area: fullstack
prioridad: 3
fuente: ALCANCE.md O13 (Fuera de alcance de la ficha 113)
archivos: backend/replays/analytics/aggregates.py (operator_after_result, OPERADOR_CAMBIO_MIN_RONDAS), backend/tests/test_operador_tras_resultado.py, frontend/src/operadorTrasResultado.js (filasCambioTrasPerder), frontend/src/operadorTrasResultado.test.js, frontend/src/pages/Operators.jsx (TrasResultado), frontend/e2e/humo.spec.js, docs/metricas.md
turnos: po 20261113T1643Z-c4P1LiD, arquitecto 20261113T1802Z-c8dAf7p, dev 20261113T1830Z-cTivbSq, revisor 20261113T1858Z-cxdASk3, qa 20261113T1926Z-cNCxUZs, release 20261113T1926Z-cNCxUZs

## PR

**[equipo-dev][frontend] A qué operador cambias tras perder, en Operadores**

### Que cambia
Debajo de "Repetir o cambiar tras perder" (ficha 113), Operadores suma la tabla "A qué operador cambias tras perder": por lado y operador con el que perdiste, a qué operador cambiaste en tu siguiente ronda del mismo lado, cuántas rondas y qué winrate. Responde "cuando pierdo con Ash, ¿me va mejor yendo a Thermite o a Sledge?". `/api/operators/after-result/` suma las claves `switches` y `switch_min_rounds` (aditivas; el panel de la 113 y su CSV no cambian).

### Por que esto y no otra cosa
Ficha 126 (ALCANCE.md O13, el "Fuera de alcance" de la 113). Las filas salen del mismo bucle que la celda *Tras perder · Cambia*, así suman exactamente esa celda. Descartado: recomendar a qué cambiar (se muestran números, no consejos) y lo mismo tras ganar (la base de la 113 ya lo cubre).

### Como se probo
- `check.sh` (con `verificar.sh`) sobre la rama fusionada con `origin/dev@84c575b`: VERDE 5e1b906, 1261 tests backend, 399 vitest, 107 e2e.
- Tests nuevos (`AQueOperadorCambiasTests`): Ash->Thermite y Ash->Sledge (criterio 1), suma de filas == switch de la 113, tras ganar no entra, repetir tras perder no entra, filtro de operador elige desde dónde, segunda sin ganador fuera del winrate, orden por lado/operador/rondas, la API trae `switches`. Vitest de `filasCambioTrasPerder` (lados, filtro de lado, sin datos, marca de pocas rondas). e2e de humo de Operadores (filas == API, suma == Cambia de defensa, `?side=Attack` da la nota, consola limpia).
- QA: base vacía, `seed_demo` y base de `factories.py` con valores recalculados a mano (50 %, —, 0 %), parámetros borde, accesibilidad en Chromium (teclado, `aria-sort`, contraste 14,17:1 y 5,71:1), CSV, 5 mutaciones que caen.
- OMC: plan=— · revisión=— · verificación=— (diseño); plan=— · revisión=0 hallazgos · verificación=— (implementación); plan=— · revisión=2 hallazgos LOW (0 arreglados: al humano) · verificación=— (revisión); plan=— · revisión=— · verificación=PASS (QA).
- Skills del repo: statistical-analysis, testing-strategy (diseño e implementación); accessibility-review (0 Critical, 0 Major), validate-data, design-critique (QA).

### Riesgos y lo que no entra
Sin migración, sin `recompute`, sin parser. Umbral de 5 rondas por par sin calibrar con una base real. Fuera: lo mismo tras ganar, recomendar operador, el mismo corte para el spawn (S3).

### Como probarlo en 2 minutos
```
cd backend; python manage.py seed_demo; python manage.py runserver
curl -s localhost:8000/api/operators/after-result/ | python -m json.tool   # mirar "switches"
```
En `http://localhost:8000/operadores`: la tabla nueva debajo del panel de la 113; con "Solo defensa" solo filas de defensa; "Descargar CSV".

### Para el humano
Calibrar con tu base el umbral de 5 rondas por par (`OPERADOR_CAMBIO_MIN_RONDAS`). Dos LOW de tests del revisor (abajo), no bloquean.

### Candidatos descubiertos
Ninguno.

🤖 Generated with [Claude Code](https://claude.com/claude-code)

https://claude.ai/code/session_01CqYLDXzAeFMLJ5RJNCxUZs
## Que gana quien usa la app

El panel "Repetir o cambiar tras perder" de Operadores (ficha 113) dice si
cambiar de operador despues de una ronda perdida te sirve; esto dice a cual:
por operador con el que perdiste y lado, a que operadores cambias en tu
siguiente ronda del mismo lado y que winrate tiene esa ronda con cada uno.
Responde "cuando pierdo con Ash, ¿me va mejor yendo a Thermite o a Sledge?".

## Criterios de aceptacion

- [x] `/api/operators/after-result/` (o una clave nueva de la misma
      respuesta) devuelve filas `from_operator`, `side`, `to_operator`,
      `rounds`, `won`, `winrate` con los mismos pares que el caso
      `switch` de `after_loss` de la 113 (misma partida, mismo lado,
      sin hueco de numeracion, sin operador vacio). Test con rondas armadas:
      pierdes con Ash, cambias dos veces a Thermite (ganas una) y una a
      Sledge (pierdes) -> Ash->Thermite 2 rondas 50 %, Ash->Sledge 1 ronda 0 %.
- [x] La suma de `rounds` de las filas de un lado es igual al `rounds` de
      `after_loss.switch` de ese lado con los mismos filtros. Test.
- [x] Los filtros globales aplican como en la 113 (`operator` elige la
      primera ronda del par: con `?operator=Ash` solo salen filas desde
      Ash). Test.
- [x] Se ve en Operadores debajo del panel de la 113, con el aviso de muestra
      de la pagina (se avisa, no se oculta); sin cambios tras perder, un
      texto y no un error. El e2e de humo pasa por Operadores con la consola
      limpia.
- [x] Fila nueva en `docs/metricas.md` ("A qué operador cambias tras perder").

## Fuera de alcance

- Lo mismo tras ganar (la base de la 113 ya lo cubre en agregado).
- Recomendar a que operador cambiar: se muestran los numeros, no un consejo.
- El mismo corte para el spawn (S3).

## Diseno

(arquitecto 20261113T1802Z-c8dAf7p) En el bucle de `operator_after_result`, el caso `after_loss`/`switch` suma también a `cambios[(lado, op_previo, op)]`; la respuesta trae `switches` (lado, desde, -rondas, hacia) y `switch_min_rounds = OPERADOR_CAMBIO_MIN_RONDAS = 5` (por par, más fino que el 12 de la 113: se avisa, no se oculta). UI: `<h3>` y `DataTable` en el mismo `Panel` de la 113, misma request. Detalle completo en `git log`.
OMC: plan=— · revisión=— · verificación=—

## Implementacion

(dev 20261113T1830Z-cTivbSq) Diseño completo, más dos tests backend extra (repetir tras perder no entra; orden de filas). `verificar.sh` VERDE 5563bae26 (1247, 392, 106).
OMC: plan=— · revisión=0 hallazgos · verificación=—

## Revision 2026-11-13 sobre 8932c28

(revisor 20261113T1858Z-cxdASk3) Aprobar. Dos LOW, sin arreglar, no bloquean:
- L1 `test_las_filas_van_por_lado_operador_y_rondas` no detecta quitar `-rounds` del orden (sí lo detecta `test_ash_a_thermite_y_a_sledge`).
- L2 la suma de filas == switch de la 113 se prueba en Django solo sin filtros (QA la comprobó a mano con `operator=Jager`).
OMC: plan=— · revisión=2 hallazgos LOW (0 arreglados: al humano) · verificación=—

## QA 2026-11-13 sobre 5e1b906

(qa 20261113T1926Z-cNCxUZs) `verificar.sh` VERDE 5e1b906 (1261, 399, 107). Base vacía (`switches []`), `seed_demo` (suma Defensa 58 == switch), parámetros borde todos 200, base de `factories.py` recalculada a mano (Ash->Thermite 2 rondas 50 %, Jager->Mute sin ganador —, Mute->Jager 0 %, sin par por hueco ni entre partidas), chunk inicial sin cambio (200116 B), accesibilidad sin Critical ni Major, CSV correcto, 5 mutaciones caen. Comandos completos en el commit `Prueba: 126 a que operador cambias tras perder`. Aprobado.
Skills del repo: accessibility-review (0 Critical, 0 Major), validate-data (50 % y — recalculados), design-critique (nada nuevo).
OMC: plan=— · revisión=— · verificación=PASS

## Para el humano

- (arquitecto 2026-11-13, no bloquea) Calibrar con tu base el umbral de 5 rondas por par (`OPERADOR_CAMBIO_MIN_RONDAS`).
- (revisor 2026-11-13, no bloquea) Dos LOW de tests (arriba): los puede sumar un Dev después.
