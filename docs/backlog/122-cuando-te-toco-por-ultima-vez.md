# 122. Cuando te toco por ultima vez

estado: entregado
candado: -
rama: claude/equipo-dev/122-cuando-te-toco-por-ultima-vez
tipo: funcionalidad
epica: rivales
area: backend
prioridad: 3
fuente: ALCANCE.md D10
archivos: backend/replays/analytics/aggregates.py (_record, repeated_rivals, _filas_de_stacks), backend/tests/test_duels.py, backend/tests/test_stacks_rivales.py, frontend/src/ultimaVez.js (nuevo), frontend/src/ultimaVez.test.js (nuevo), frontend/src/pages/Duelos.jsx, frontend/e2e/humo.spec.js, docs/metricas.md
turnos: po 20261113T1650Z-c9H2L8Y, arquitecto 20261113T1802Z-c8dAf7p, dev 20261113T1830Z-c2rHpej, revisor 20261113T1858Z-cxdASk3, qa 20261113T1926Z-cq9nfTP, release 20261113T1926Z-cq9nfTP

## PR

Titulo: `[equipo-dev][backend] Duelos: cuando te toco cada rival por ultima vez`

### Que cambia

En Duelos, las tablas Rivales repetidos y Stacks rivales que se repiten suman la columna "Última vez": la fecha de la partida mas reciente contra esa persona o ese grupo, entre las que cuenta la fila (respeta los filtros). Se ordena por ella y sale en el CSV como AAAA-MM-DD. `/api/duels/` y el aviso de stacks del detalle de partida traen `last_played`.

### Por que esto y no otra cosa

Ficha 122 (ALCANCE D10). Sale de la misma consulta que ya traia el resultado de cada partida (una columna mas): sin migracion ni consultas nuevas.

### Como se probo

- `check.sh` (con `verificar.sh`): VERDE c7a8e7a25, 1258 tests backend, 398 vitest, 106 e2e.
- Tests nuevos: `test_la_ultima_vez_es_la_partida_mas_reciente`, `test_la_ultima_vez_respeta_el_filtro_de_fechas`, `test_la_ultima_vez_de_cada_rival_sale_de_sus_propias_partidas` (QA, mata el mutante "fecha de cualquier partida de la consulta"), `test_el_stack_trae_la_ultima_vez`, `test_el_aviso_de_la_partida_da_la_misma_ultima_vez_que_duelos`; vitest `ultimaVez.test.js`; e2e en `Duelos muestra rivales repetidos con enlace al perfil`.
- Verificacion manual (QA): `seed_demo` + `runserver`; `last_played` recalculado a mano con `until=2026-08-03` (18 partidas, `2026-08-03T23:00:00`); Playwright en `/duelos`: orden por teclado, contraste 14.17:1, consola limpia.
- OMC: plan=— · revisión=— · verificación=—
- OMC: plan=— · revisión=0 hallazgos · verificación=—
- OMC: plan=— · revisión=1 hallazgo LOW (0 arreglados: al humano) · verificación=—
- OMC: plan=— · revisión=— · verificación=PASS
- Skills del repo: testing-strategy (Django para el max y el filtro, vitest para el formato, humo e2e para la columna), statistical-analysis (no aplica: una fecha, no una tasa).
- Skills del repo: testing-strategy, ux-copy (`help` con tildes, `—` como el resto), modern-web-guidance (no aplica).
- Skills del repo: accessibility-review (0 Critical, 0 Major), validate-data (2 valores recalculados).

### Riesgos y lo que no entra

Campo aditivo en `/api/duels/` y en el detalle; el CSV de las dos tablas gana una columna. Sin migracion ni `recompute`. Fuera: enlace de la fecha a la partida, columna en la tabla Por rival, mostrarla en el aviso del detalle.

### Como probarlo en 2 minutos

```powershell
cd backend; python manage.py seed_demo; python manage.py runserver
```
Abrir `http://127.0.0.1:8000/duelos`: columna "Última vez" con `05-08-2026` en las dos tablas; con el filtro hasta 03-08-2026, baja a `03-08-2026`. "Descargar CSV" la trae como `2026-08-05`.

### Para el humano

Nada que decidir. Aviso: `fechaCorta` de `ultimaVez.js` duplica `fecha` de `Jugador.jsx:21` (LOW del revisor).

### Candidatos descubiertos

Ninguno.

## Que gana quien usa la app

En Duelos, Rivales repetidos y Stacks rivales que se repiten muestran "Última vez": se distingue al rival que te sigue tocando esta semana del de una racha de hace meses, sin abrir su perfil.

## Criterios de aceptacion

- [x] Cada fila de `repeated_rivals` y `rival_stacks` trae `last_played` (ISO, `max(Match.played_at)` de sus partidas). Test con tres fechas.
- [x] Con `since`/`until`, `last_played` sale de las partidas filtradas. Test.
- [x] `rival_stacks_de_partida` no cambia su record y da la misma fecha que Duelos. Test.
- [x] `Duelos.jsx`: columna "Última vez" en las dos tablas, fecha corta, ordenable.
- [x] e2e: en `seed_demo`, la columna con fecha no vacia; consola limpia.

## Diseno

(arquitecto 20261113T1802Z-c8dAf7p) `_record(ids, resultado, fechas)` suma `last_played`; `repeated_rivals` y `_filas_de_stacks` traen `played_at` en la misma consulta; `rival_stacks_de_partida` lo hereda. Frontend: `ultimaVez.js` (`fechaCorta`, `fechaCsv`) y columna en las dos tablas. `metricas.md`: *Última vez* en Rival repetido y Stack rival repetido. Detalle en `git log`.

## Implementacion

(dev 20261113T1830Z-c2rHpej) Diseno completo; `_resultados_y_fechas` reemplaza la consulta que habia. Tests vistos en rojo antes del codigo. Chunk inicial 200.00 kB (Duelos lazy). verificar.sh: VERDE 8aa8d4de8.

## Revision 2026-11-13 sobre 5dd09ad

(revisor 20261113T1858Z-cxdASk3) Aprobar. 1 LOW sin arreglar (duplicado de `fechaCorta` con `Jugador.jsx`), al humano.

## QA 2026-11-13 sobre c7a8e7a

(qa 20261113T1926Z-cq9nfTP) Merge limpio de `origin/dev`; VERDE c7a8e7a25 (1258/398/106). Base vacia y `seed_demo`: `last_played` recalculado a mano (`2026-08-05T08:00:00`; con `until=2026-08-03`, 18 partidas y `2026-08-03T23:00:00`); bordes (`until=foo`, `page=-1`, `until=2000-01-01`) en 200; detalle = Duelos. Playwright: orden por teclado (`aria-sort`), contraste 14.17:1, consola limpia. Mutacion: `max`->`min` cae; `max(fechas.values())` sobrevivia y la mata el test nuevo de QA. omc-verifier: PASS. Detalle en `git log`.

## Para el humano

- (revisor 2026-11-13, no bloquea) `fechaCorta` de `ultimaVez.js` duplica `fecha` de `Jugador.jsx:21`; que `Jugador.jsx` la importe. Lo puede hacer un Dev despues.
