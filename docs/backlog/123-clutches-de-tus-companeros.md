# 123. Clutches de tus companeros

estado: entregado
candado: -
rama: claude/equipo-dev/123-clutches-de-tus-companeros
tipo: funcionalidad
epica: escuadra
area: backend
prioridad: 3
fuente: ALCANCE.md C15
archivos: backend/replays/analytics/aggregates.py (teammate_clutches, CLUTCH_COMPANERO_MIN), backend/replays/views.py (teammates), backend/tests/test_clutch_companeros.py (nuevo), frontend/src/clutchCompaneros.js (nuevo), frontend/src/clutchCompaneros.test.js (nuevo), frontend/src/pages/Teammates.jsx (panel Clutches), frontend/e2e/humo.spec.js, docs/metricas.md
turnos: po 20261113T1650Z-c9H2L8Y, arquitecto 20261113T1830Z-cTivbSq, dev 20261113T1858Z-cxQ3TuB, revisor 20261113T1926Z-ce4Pmp6, qa 20261113T1954Z-cfZTvvE, release 20261113T1954Z-cfZTvvE

## PR

Titulo: `[equipo-dev][backend] Compañeros: clutches de tus compañeros habituales`

### Que cambia

En Compañeros, panel Clutches, una tabla nueva "Clutches de tus compañeros": por cada compañero habitual (5 partidas o mas en tu equipo), cuantas veces quedo ultimo vivo de tu equipo en rondas contigo, cuantas gano y su conversion, con tu propia fila ("Tú") arriba para comparar. Un `*` marca menos de 5 intentos. `/api/teammates/` suma la clave `teammate_clutches`.

### Por que esto y no otra cosa

Ficha 123 (ALCANCE C15). `RoundPlayer.clutch_vs` ya se calcula al importar para cada jugador de la ronda: sin migracion ni `recompute`. Descartado: partir por cantidad de rivales o por lado (tramo siguiente), clutches de rivales (D12), señales del Coach.

### Como se probo

- `check.sh` (con `verificar.sh`): VERDE 100ded971, 1279 tests backend, 405 vitest, 109 e2e (rama fusionada con `origin/dev@c332e72`).
- Tests nuevos (`backend/tests/test_clutch_companeros.py`, 13): intentos y ganados por compañero, ronda sin ganador fuera, no habitual no sale, rival (y habitual que clutchea como rival) no cuenta, filtro de lado, cambio de nick y nick repetido, tu fila igual a tu conversion y en cero, muestra chica bajo 5, `assertNumQueries(2)`, clave en la API. vitest `clutchCompaneros.test.js` (3). e2e: estado vacio con `seed_demo` y tabla con respuesta interceptada (orden, enlaces, `*`, consola limpia).
- Verificacion manual (QA): base sembrada desde `factories.py` y `runserver`; dos filas recalculadas a mano (Seba 3/2, Nico 6/4); `side`, fechas y parametros invalidos; Playwright en `/companeros` (teclado, nombres, contraste 14.17:1, consola limpia); 3 mutaciones, cada una cae en su test.
- OMC: plan=— · revisión=— · verificación=—
- OMC: plan=— · revisión=5 hallazgos (1 MEDIUM, 4 LOW; 5 arreglados) · verificación=—
- OMC: plan=— · revisión=3 hallazgos (0 arreglados, todos LOW) · verificación=—
- OMC: plan=— · revisión=— · verificación=PASS
- Skills del repo: statistical-analysis, testing-strategy (diseno).
- Skills del repo: statistical-analysis, testing-strategy, ux-copy, sql-queries (implementacion).
- Skills del repo: accessibility-review (0 Critical, 0 Major), validate-data (dos valores recalculados: Seba 3/2, Nico 6/4).

### Riesgos y lo que no entra

Clave aditiva en `/api/teammates/` y dos consultas mas en esa vista. Sin migracion ni `recompute`. La regla de habitual esta copiada de `by_stack`: si cambia, cambiar las dos. Ningun e2e contra la app real ve la tabla con numeros (`seed_demo` no da `clutch_vs` a los compañeros); la cubren los tests Django y el e2e interceptado.

### Como probarlo en 2 minutos

```powershell
cd backend; python manage.py seed_demo; python manage.py runserver
```
Abrir `http://127.0.0.1:8000/companeros`, panel Clutches: subtitulo "Clutches de tus compañeros" con la nota "Ningún compañero habitual quedó último..." (la semilla no da clutches a los compañeros). Con la base real: tabla con "Tú" arriba; `?side=Attack` cambia los numeros; `*` en filas con menos de 5 intentos.

### Para el humano

Nada que decidir. Aviso: el umbral de 5 intentos (`CLUTCH_COMPANERO_MIN`) no esta calibrado con tu base.

### Candidatos descubiertos

Ninguno.

## Que gana quien usa la app

En Compañeros, una tabla nueva con cada compañero habitual: cuantas veces
quedo ultimo vivo de tu equipo en rondas contigo, contra cuantos y cuantas
convirtio, al lado de tu propia conversion. Saber a quien conviene dejarle
la ronda y quien la regala; hoy los clutches de esa pagina son solo tuyos.

## Criterios de aceptacion

- [ ] Funcion nueva en `replays/analytics/aggregates.py` (p. ej.
      `teammate_clutches`): por compañero (agrupado por `player_id`, como
      `teammate_synergy`, un cambio de nick no parte la fila) cuenta
      intentos (`clutch_vs > 0` en su fila, misma ronda y `team_index` que
      la tuya) y ganados (`Round.my_team_won`), con el mismo descarte que
      `clutch_conversion`: rondas con `my_team_won` nulo no cuentan. Test
      con dos compañeros y un intento ganado y uno perdido.
- [ ] Muestra minima por fila (habitual = el mismo corte de partidas
      compartidas de la ficha 54, o un minimo de intentos fijado en el
      diseno); los compañeros bajo el corte no salen. Test.
- [ ] Los filtros globales (mapa, lado, fechas) aplican igual que al resto
      de `/api/teammates/`; test con filtro de lado.
- [ ] `/api/teammates/` suma la clave nueva; la tabla en `Teammates.jsx`
      muestra intentos, ganados y % con su `n`, mas tu propia fila como
      referencia; e2e en `seed_demo` sin errores de consola (con datos o
      con el estado vacio si la semilla no da clutches de compañeros).
- [ ] Fila nueva en `docs/metricas.md` con la definicion (ultimo vivo con
      rivales vivos, mismo algoritmo que `clutch_vs`).

## Fuera de alcance

- Partir la tabla por cantidad de rivales (1v1, 1v2...) o por lado: se
  puede como tramo siguiente.
- Clutches de los rivales (D12).
- Señales del Coach sobre esto.

## Diseno

(arquitecto 20261113T1830Z-cTivbSq, sobre `origin/dev@ed7bb52`) `clutch_vs` ya se escribe al importar para cada jugador: sin migracion. Dos cortes: habitual (`MIN_PARTIDAS_HABITUAL`, regla de `by_stack`, sin filtros) para salir y `CLUTCH_COMPANERO_MIN = 5` intentos para avisar con `*`. `teammate_clutches(**filters)` en `aggregates.py`: intentos del compañero con `Exists` sobre tu fila de `base_queryset` con el mismo `team_index` (patron de `teammate_synergy`); ganado = `my_team_won`; rondas sin ganador fuera; tu fila con la cuenta de `clutch_conversion`. Tabla en `Teammates.jsx` con logica pura en `clutchCompaneros.js`; e2e vacio y con respuesta interceptada; fila en `metricas.md`. El detalle completo, en `git log` de esta ficha.

Skills del repo: statistical-analysis, testing-strategy.
OMC: plan=— · revisión=— · verificación=—

## Implementacion

(dev 20261113T1858Z-cxQ3TuB, sobre `origin/dev@84c575b`) Diseno completo. `teammate_clutches` con los habituales como subconsulta: 2 consultas (`assertNumQueries(2)`). `filasClutchCompaneros` agrega `orden` para que `DataTable` mantenga tu fila arriba. Desvio: la fila propia dice "Tú" y no "Vos" (la UI habla de tú). Tests vistos en rojo antes del codigo: 13 Django, 3 vitest, 2 e2e (lista en `## PR`). verificar.sh: VERDE 6438bcd22 (1266 backend, 398 vitest, 108 e2e).

Skills del repo: statistical-analysis, testing-strategy, ux-copy, sql-queries.
OMC: plan=— · revisión=5 hallazgos (1 MEDIUM, 4 LOW; 5 arreglados) · verificación=—

## Revision 2026-11-13 sobre b871565

(revisor 20261113T1926Z-ce4Pmp6) verificar.sh: VERDE b871565e2 (1266 backend, 398 vitest, 108 e2e). Dos ejes a ciegas (`omc-code-reviewer`): aprobar. Hallazgos, todos LOW y sin cambio pedido: el e2e contra la app real solo ve el estado vacio (`seed_demo` no da `clutch_vs` a compañeros; tramo aparte); el 5 escrito a mano en la UI (convencion de las tablas vecinas); la consulta de habituales copia la de `by_stack` (pedido por el diseno). Veredicto: aprobar -> `revisado`.

Skills del repo: ninguna.
OMC: plan=— · revisión=3 hallazgos (0 arreglados, todos LOW) · verificación=—

## QA 2026-11-13 sobre 100ded9

(qa 20261113T1954Z-cfZTvvE; rama fusionada con `origin/dev@c332e72` en 100ded9, sin conflictos)

- `check.sh`: `verificar.sh` -> VERDE 100ded971 (1279 backend, 405 vitest, 109 e2e).
- API, `runserver` con base vacia (`SQLITE_PATH=<scratch>/vacia.sqlite3 python3 manage.py migrate` + `runserver`): `GET /api/teammates/` -> `teammate_clutches = {min_attempts: 5, me: {attempts: 0, won: 0, pct: null}, rows: []}`.
- API con base sembrada desde `factories.py` (script en el scratchpad; Seba y Nico habituales; Seba 2 ganados en ataque, 1 perdido en defensa y 1 en ronda con `my_team_won=None`; Nico 6 en ataque, 4 ganados, con un rival `team_index=1, clutch_vs=2` en cada una; Fugaz 5 partidas, 1 ganado; Breve 3 partidas, 1 intento; vos 2, 1 ganado):
  - sin filtros: Nico 6/4 66.7, Seba 3/2 66.7 `*`, Fugaz 1/1 100 `*`, Breve no sale (no habitual), Tú 2/1 50. **Recalculado a mano**: Seba 3 (la ronda sin ganador fuera) con 2 ganados; Nico 4/6 = 66.7 (el rival no suma). Coincide.
  - `?side=Defense` -> Tú 1/0, solo Seba 1/0; `?side=Attack` -> Nico 6/4, Seba 2/2, Fugaz 1/1, Tú 1/1.
  - `?until=foo`, `?page=-1`, `?map=`, `?side=` -> 200, igual que sin filtro. `?since=2099-01-01`, `?map=noexiste` -> `rows: []`, `pct: null`.
- Bundle: chunk inicial `index-*.js` 200116 bytes en `origin/dev` y en la rama (0 %); `Teammates` (lazy) 11611 -> 13145.
- accessibility-review (Playwright en `/companeros`, base sembrada): heading "Clutches de tus compañeros"; filas Tú, Nico, Seba, Fugaz; enlaces con nombre a `/jugadores/3,1,4`; `*` con `title` "Menos de 5 intentos" (markup de las tablas vecinas); foco de teclado visible en el enlace; contraste celdas 14.17:1, encabezados 5.71:1; consola sin errores. Sin Critical ni Major.
- validate-data sobre la fila de `metricas.md`: division por cero -> `pct: null`, la UI pone `—` (`ui.jsx fmt`); la fila Tú es la cuenta total, no un promedio de promedios; tasa con su `n` (Intentos); redondeo 66.7 -> 67 % como el resto.
- Mutacion (`cd backend; python3 manage.py test tests.test_clutch_companeros`): sin `round__my_team_won__isnull=False` cae `test_una_ronda_sin_ganador_no_cuenta`; sin el corte `n__gte=MIN_PARTIDAS_HABITUAL` cae `test_un_companero_que_no_es_habitual_no_sale`; sin `team_index` en la correlacion cae `test_un_habitual_que_clutchea_como_rival_no_cuenta`. Restaurado: 13 OK.
- design-critique: no aplica (tabla nueva en un panel existente).

Veredicto: `aprobado`.

Skills: no aplica.
Skills del repo: accessibility-review (0 Critical, 0 Major), validate-data (dos valores recalculados: Seba 3/2, Nico 6/4).
OMC: plan=— · revisión=— · verificación=PASS


## Para el humano

- (arquitecto 2026-11-13, no bloquea) El aviso de 5 intentos por compañero (`CLUTCH_COMPANERO_MIN`) copia el de Clutch por operador, sin calibrar con tu base: mira cuantas filas quedan con `*`.
