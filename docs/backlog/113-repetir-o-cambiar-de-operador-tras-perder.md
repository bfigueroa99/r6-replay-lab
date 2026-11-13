# 113. Repetir o cambiar de operador después de perder

estado: entregado (PR pendiente de merge: check.sh rojo por e2e/accesibilidad.spec.js:235, que tambien cae en dev; lo arregla el hotfix 117)
candado: -
rama: claude/equipo-dev/113-repetir-o-cambiar-de-operador-tras-perder
tipo: funcionalidad
epica: operadores
area: fullstack
prioridad: 3
fuente: ALCANCE.md O10
archivos: backend/replays/analytics/aggregates.py (operator_after_result, OPERADOR_TRAS_RESULTADO_*), backend/replays/views.py (operators_after_result), backend/replays/urls.py, backend/tests/test_operador_tras_resultado.py, frontend/src/operadorTrasResultado.js, frontend/src/operadorTrasResultado.test.js, frontend/src/pages/Operators.jsx, frontend/e2e/humo.spec.js, docs/metricas.md
turnos: po 20261112T1204Z-chGLrtC, arquitecto 20261112T1603Z-cor3JBP, dev 20261112T2004Z-cbaTGDt, revisor 20261113T0003Z-cVnayJ8, qa 20261113T0404Z-cnRfz4a, release 20261113T0404Z-cnRfz4a

## PR

PR #111: https://github.com/bfigueroa99/r6-replay-lab/pull/111

Titulo: `[equipo-dev][backend] Repetir o cambiar de operador tras perder, en Operadores`

### Que cambia

Operadores tiene un panel nuevo, al final: despues de perder una ronda con un
operador, cuantas veces lo repetiste en tu siguiente ronda del mismo lado de
la partida y cuantas cambiaste, con el winrate de esa ronda en cada caso (y lo
mismo tras ganar, como base). Endpoint `GET /api/operators/after-result/`.

### Por que esto y no otra cosa

Ficha 113 (`ALCANCE.md` O10, epica operadores): la tabla por operador no
dice si cambiar tras una ronda mala ayuda o es tilt. Mismo recorrido de pares
que la 107 (sitio que repetis tras perderlo). Descartado: separar por
operador de destino o recomendar a cual cambiar (fuera de alcance).

### Como se probo

- `check.sh` (con `verificar.sh`): VERDE 268c81b, 1182 tests backend, 336 vitest, 95 e2e (QA); se repite sobre el commit de entrega.
- Tests nuevos: `backend/tests/test_operador_tras_resultado.py` (19: repeat/switch, after_win, otro lado no corta, hueco, operador vacio/Unknown, partidas, lados, sin ganador primera y segunda, filtros de operador -primera y no segunda ronda-, lado, mapa, tipo y sitio, total, vacio); `operadorTrasResultado.test.js` (7); e2e `Operadores muestra si repites o cambias de operador`.
- Verificacion manual (QA): base vacia con parametros borde (200, `pairs: 0`); base sembrada a mano, API identica al calculo (50.0, null, 100.0, 0.0; total 66.7 = suma, no promedio); Chromium sobre `seed_demo` con teclado, `aria-sort`, contraste 5.71:1 y consola limpia; 4 mutaciones, todas atrapadas.
- OMC: plan=— · revisión=— · verificación=— (diseno)
- OMC: plan=— · revisión=2 hallazgos LOW (2 arreglados) · verificación=— (implementacion)
- OMC: plan=— · revisión=5 hallazgos (1 MEDIUM cerrado con test; 4 LOW sin arreglar) · verificación=— (revision)
- OMC: plan=— · revisión=— · verificación=PASS (QA)
- Skills del repo: validate-data (0 hallazgos; recalculados 66.7 y 50.0), accessibility-review (0 Critical, 0 Major).

### Riesgos y lo que no entra

Sin migracion, sin `recompute`, sin parser. Una consulta ordenada recorrida
con `.iterator()`. Quedan 4 LOW de pulido: helpers duplicados con la 107
(`_caso_vacio`/`_sumar_caso`), `winrateCsv` que repite `celdaCsv`, y el `?? 12`
del hint. Fuera: el mismo corte para el spawn (S3) y operadores de compañeros.

### Como probarlo en 2 minutos

```
cd backend; python manage.py seed_demo; python manage.py runserver
```
Abrir `/operadores`: al final, panel "Repetir o cambiar tras perder" con 4
filas (Total tras perder 58 cambia 0 %, Total tras ganar 87 cambia 100 %,
Ataque tras ganar 87, Defensa tras perder 58). `/operadores?side=Defense`: una
fila. `/operadores?operator=Ash`: Ataque tras ganar 29.

### Para el humano

Nada.

### Candidatos descubiertos

Ninguno.

## Que gana quien usa la app

En Operadores, despues de perder una ronda con un operador, la app dice
cuantas veces lo repetiste en la siguiente ronda del mismo lado de la partida
y cuantas cambiaste, con el winrate de esa ronda siguiente en cada caso (y lo
mismo despues de ganar, como base). Responde si cambiar de operador tras una
ronda mala te ayuda o es tilt, cosa que la tabla por operador no puede decir.

## Criterios de aceptacion

- [x] Un agregado devuelve, por lado y en total, para pares de rondas tuyas
      consecutivas del mismo lado en la misma partida (por `Round.number`,
      saltando las del otro lado), separados por el resultado de la primera
      (`after_loss`, `after_win`): `repeat` y `switch` con `rounds` y
      `winrate` de la segunda. Test con una partida armada: perder con Ash y
      volver a Ash cuenta `repeat`; pasar a Thermite cuenta `switch`.
- [x] Una ronda sin `.rec` entre medio (hueco en `number`), un operador
      vacio o `Unknown(...)` cortan el par, y los pares no cruzan partidas
      ni lados. Test.
- [x] Una primera ronda sin ganador no entra ni en `after_loss` ni en
      `after_win`; una segunda sin ganador cuenta en `rounds` y no en el
      winrate. Test.
- [x] Los filtros de mapa, tipo, modo, fechas y sesion aplican; el de lado
      elige que bloque se muestra; el de operador filtra el operador de la
      ronda perdida o ganada (la primera del par). Test del de operador.
- [x] Se ve en Operadores con la muestra minima de operador (12 rondas) como
      aviso, no como recorte; sin pares, un texto y no un error. El e2e de
      humo pasa por Operadores con la consola limpia.
- [x] Fila nueva en `docs/metricas.md` ("Repetir o cambiar de operador").

## Implementacion

(dev 20261112T2004Z-cbaTGDt) Segun el diseno (`git log` de la rama tiene el
detalle): `operator_after_result` en `aggregates.py` (una consulta ordenada
por partida y numero, un pendiente por lado), vista + url
`operators/after-result/`, `operadorTrasResultado.js` + vitest, panel
`TrasResultado` al final de `Operators.jsx`, e2e y filas en `metricas.md`.
Desvios: `site` tambien elige la primera ronda (como en la 107); el CSV de los
winrates sale con coma decimal.

## Revision 2026-11-13 sobre 4a8ec36

(revisor 20261113T0003Z-cVnayJ8) Aprobar -> `revisado`. Hallazgo corregido:
MEDIUM, el test del filtro de operador pasaba igual si el filtro mirara la
segunda ronda; agregado `test_el_filtro_de_operador_no_mira_la_segunda_ronda`
(cae con la mutacion). 4 LOW sin arreglar (ver Riesgos del PR).
verificar.sh VERDE f30df34 (1182 backend, 336 vitest, 95 e2e).
OMC: plan=— · revisión=5 hallazgos (1 MEDIUM cerrado con test; 4 LOW sin arreglar) · verificación=—

## QA 2026-11-13 sobre 268c81b

(qa 20261113T0404Z-cnRfz4a) Scripts temporales en el scratchpad (sembrado con
`factories.py`, Playwright); nada de `.rec` ni `.sqlite3` al repo.

- **check.sh**: `verificar.sh` -> `VERDE 268c81b33 en 177s: 1182 tests backend, 336 vitest, 95 e2e`.
- **Base vacia** (`SQLITE_PATH=<tmp> manage.py migrate`, `runserver`):
  `curl /api/operators/after-result/` con `''`, `until=foo`, `page=-1`,
  `side=`, `operator=`, `map=`, `side=Attack`, `operator=Unknown(3)`,
  `days=999999999999`, `since=2026-13-45`: todos 200, `pairs: 0`,
  `winrate: null`. POST -> 403 (CSRF). Log sin tracebacks.
- **Base sembrada** (`manage.py shell < sembrar113.py`): partida 0 Club House
  [A0 Ash L, D1 Mute W, A2 Ash W, D3 Jager L, A4 Thermite sin ganador, A5
  Thermite L, D6 Jager W]; partida 1 Oregon [A0 Ash L, A1 Ash L, (falta 2),
  A3 Ash W, A4 Unknown(7) L, A5 Ash W]. Calculado a mano y devuelto por la
  API, identico: `pairs 5`; Ataque tras perder repite 2/2/1 -> 50.0;
  Ataque tras ganar cambia 1/0/0 -> null (segunda sin ganador); Defensa tras
  perder repite 1/1/1 -> 100.0; Defensa tras ganar cambia 1/1/0 -> 0.0.
  `operator=Ash` 3 pares (solo ataque), `map=oregon` 1 (repite 0.0),
  `side=Defense` igual que sin filtro, `operator=Nadie` 0. Vecinos
  `operators/`, `operators/sites/`, `operators/pool/` -> 200.
- **validate-data** sobre la fila de `metricas.md`: division por cero ->
  `_pct` da `None` (se ve `—`); Total suma numeradores y denominadores
  (tras perder repite 3/3/2 = 66.7, no el 75 del promedio de promedios); cada
  winrate va junto a su n de rondas y con aviso bajo 12; redondeo 1 decimal en
  la API y entero en la UI. Sin hallazgos.
- **Chunk inicial**: Operadores es lazy; "Tras perder" aparece 0 veces en
  `index-2JPF6dan.js` (196964 B) y 1 en `Operators-*.js`: no crece.
- **accessibility-review** (Chromium, `seed_demo`, `/operadores`): 6
  `columnheader` con nombre, 6 botones de orden enfocables, Enter ordena y
  pone `aria-sort`; contraste minimo medido 5.71:1 (hint); filas
  `Total/Tras perder 0 — 58 0%`, `Total/Tras ganar 0 — 87 100%`,
  `Ataque/Tras ganar 0 — 87 100%`, `Defensa/Tras perder 0 — 58 0%`;
  `?side=Defense` una fila; 0 errores de consola. Sin Critical ni Major.
- **Mutacion** (aggregates.py, restaurado): sin corte por hueco -> cae
  `test_una_ronda_faltante_entre_medio_corta_el_par`; sin corte por partida
  -> cae `test_los_pares_no_cruzan_partidas`; repeat/switch invertido -> caen
  11; abrir par sin ganador -> cae `test_primera_sin_ganador_no_abre_par`.
- Sin migracion, parser, Electron ni `.ps1`: nada para verificar en el PC.

Veredicto: `aprobado`.

Skills del repo: validate-data (0 hallazgos; recalculados 66.7 y 50.0),
accessibility-review (0 Critical, 0 Major), design-critique no aplica (panel
en pagina existente, mismo patron que `PorSitio`).
OMC: plan=— · revisión=— · verificación=PASS

## Para el humano

(nada)
