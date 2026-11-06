# 95. Partida anterior y siguiente, y flechas para cambiar de ronda

estado: entregado
candado: -
rama: claude/equipo-dev/95-partida-anterior-y-siguiente
tipo: funcionalidad
epica: revision-de-rondas
area: fullstack
prioridad: 3
fuente: F17 de ALCANCE.md; idea del PR #14 (cerrado sin merge el 2026-11-05, rama `claude/dazzling-einstein-w3qcyq` como referencia, decision del humano en `## Para el equipo` del 2026-11-05)
archivos: backend/replays/views.py, backend/tests/test_partida_anterior_y_siguiente.py, frontend/src/navegacionRondas.js, frontend/src/navegacionRondas.test.js, frontend/src/pages/MatchDetail.jsx, frontend/e2e/navegar-partidas.spec.js
turnos: po 20261106T0041Z-cSxDY1g, arquitecto 20261106T0109Z-cMAPx7f, dev 20261106T0200Z-cK8ypRQ, revisor 20261106T0228Z-cgEzFUY, qa 20261106T0252Z-cf6G6Cs, release 20261106T0252Z-cf6G6Cs

## PR

Titulo: `[equipo-dev][frontend] Partida anterior y siguiente, y flechas para cambiar de ronda`

### Que cambia

En el detalle de una partida aparecen "← Partida anterior" y "Partida siguiente →" para recorrer el historial sin volver al listado, y las flechas del teclado cambian de ronda. La API del detalle suma `prev_id` y `next_id`, y el listado desempata por `id` partidas con la misma fecha.

### Por que esto y no otra cosa

Ficha 95 (F17 de `ALCANCE.md`, idea del PR #14 que el humano cerro y devolvio a idea). Navegar respetando los filtros globales queda para despues de la 96 (filtros en la URL); atajos de teclado para cambiar de partida, fuera.

### Como se probo

- `check.sh` (con `verificar.sh`): VERDE sobre el commit de QA, 1022 tests backend, 232 vitest, 69 e2e; repetido sobre la entrega.
- Tests nuevos: `test_partida_anterior_y_siguiente.py` (del medio, extremos, una sola, empate de fecha recorrido en los dos sentidos, orden por fecha y no por id, listado desempata por id); `navegacionRondas.test.js` (11: tope, total 0, modificadores, campos, contenteditable, tablas con scroll, `defaultPrevented`); e2e `navegar-partidas.spec.js` (enlaces, fecha y titulo de la vecina, flechas, consola limpia).
- QA: base vacia y sembrada con `factories.py` (empate de fecha, partida importada despues pero jugada antes, partida sin rondas); Chromium por la cadena entera; mutaciones en vista, listado y logica de teclas, todas detectadas.
- OMC: plan=— · revisión=— · verificación=— (diseno)
- OMC: plan=— · revisión=5 hallazgos LOW (3 arreglados) · verificación=— (implementacion)
- OMC: plan=— · revisión=2 hallazgos (1 arreglado, 1 descartado) · verificación=— (revision)
- OMC: plan=— · revisión=— · verificación=PASS (QA)

### Riesgos y lo que no entra

Sin migraciones ni `recompute`. Orden sobre el historial completo, sin filtros e incluidas las excluidas de la 79. Al seguir un enlace con Enter el foco queda en `body` (accesibilidad, para otra ficha). Chunk inicial +0,05 %.

### Como probarlo en 2 minutos

```powershell
cd backend; python manage.py runserver
```
Abrir una partida en `http://127.0.0.1:8000/partidas/<id>`: "← Partida anterior" y "Partida siguiente →" llevan a la vecina y la ronda vuelve a la primera; en la mas nueva "Partida siguiente →" esta deshabilitado. Con ← y → cambia la ronda marcada sin pasarse de los extremos; Alt+← sigue siendo Atras.

### Para el humano

Nada.

### Candidatos descubiertos

Ninguno.

## Que gana quien usa la app

Revisar una sesion de partidas hoy obliga a volver al listado entre una y otra, y cambiar de ronda dentro del detalle es solo con el mouse. Con esto se pasa a la partida anterior o siguiente con un enlace, y las rondas se recorren con las flechas del teclado.

## Criterios de aceptacion

- [x] `GET /api/matches/<id>/` suma `prev_id` y `next_id` por `(played_at, id)`, `null` en los extremos; empates sin saltos ni repeticiones.
- [x] Enlaces "← Partida anterior" / "Partida siguiente →" (deshabilitados en los extremos); al navegar, primera ronda y sin datos de la previa.
- [x] Flechas ← → cambian la ronda con tope, no actuan en campos; logica pura con vitest.
- [x] e2e sobre `seed_demo`: enlace, cambio de partida, flecha, consola limpia.

## Diseno

(arquitecto 20261106T0109Z-cMAPx7f) Orden total `(played_at, id)` en el detalle y en `match_list` (no en `match_queryset`, que otros agregan con `values().annotate()`); historial completo; `MatchDetail` devuelve `<DetallePartida key={id}>` para resetear el estado al cambiar de partida; flechas sin modificadores y fuera de campos, con `preventDefault` solo si se toman. Detalle en `git log`.

OMC: plan=— · revisión=— · verificación=—

## Implementacion

(dev 20261106T0200Z-cK8ypRQ) Todo el diseno. Desvios: `partida-sin-rondas.json` no se regenero (el test saca `match` antes de comparar); `pasoDeTecla` ademas ignora `defaultPrevented` y el foco dentro de `.table-wrap`/`.matriz-scroll`; barra del encabezado con `flexWrap`. No arreglado (LOW): foco en `body` tras el remonte; roles ARIA no excluidos.

OMC: plan=— · revisión=5 hallazgos LOW (3 arreglados) · verificación=—

## Revision 2026-11-06 sobre 9f2cd96

(revisor 20261106T0228Z-cgEzFUY) Aprobar. Hallazgo MEDIUM arreglado: en `seed_demo` las tres partidas mas nuevas son `Bank 4-3` y el `h1` no cambiaba; el e2e ahora afirma la fecha distinta de cada vecina. LOW del hint descartado (estaba en el diseno).

OMC: plan=— · revisión=2 hallazgos (1 arreglado, 1 descartado) · verificación=—

## QA 2026-11-06 sobre f22461d

(qa 20261106T0252Z-cf6G6Cs) `verificar.sh`: VERDE f22461d8e (1022 backend, 232 vitest, 69 e2e). Base vacia: listado vacio, 404 limpios. Base sembrada (empate de fecha 2/3, 4 jugada antes e importada despues, sin rondas): 4 `prev None next 1`, 1 `4/2`, 2 `1/3`, 3 `2/None`; listado `[3,2,1,4]`; parametros borde sin 500. Chromium: extremos deshabilitados, primera ronda al cambiar, tope de flechas, Shift+← ignorado, Atras ok, consola limpia. Mutaciones (`id__lt`->`id__gt`, orden del listado, tope de `rondaVecina`, `CAMPOS`) detectadas. Bundle inicial 192,50 -> 192,59 kB. Nada para el PC. Comandos completos en `git log` (commit "Prueba: 95").

OMC: plan=— · revisión=— · verificación=PASS

## Para el humano

(Nada por ahora.)
