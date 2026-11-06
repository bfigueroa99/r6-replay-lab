# 92. El stack rival en el detalle de la partida

estado: implementado
candado: -
rama: claude/equipo-dev/92-stack-rival-en-la-partida
tipo: funcionalidad
epica: rivales
area: fullstack
prioridad: 3
fuente: D9 de ALCANCE.md (idea del arquitecto 20261105T1920Z-cAaALb8 al disenar la 90); tramo siguiente de la ficha 90
archivos: backend/replays/analytics/aggregates.py, backend/replays/views.py, frontend/src/stacksRivales.js, frontend/src/stacksRivales.test.js, frontend/src/pages/MatchDetail.jsx, backend/tests/test_stacks_rivales.py, frontend/e2e/stacks-rivales.spec.js, docs/metricas.md
turnos: po 20261105T1945Z-cvqUYh1, arquitecto 20261106T0015Z-cR6uHk3, dev 20261106T0041Z-cqfAePA

## PR

(La escribe el Release manager al final.)

## Que gana quien usa la app

Al abrir una partida, ves sobre el scoreboard si en el equipo rival venia un
grupo que ya te toco junto en otras partidas ("Kaid_, Mozzie99 y Thorn.exe ya
te tocaron juntos en 4 partidas, récord 1-3"), con enlace a Duelos. Saber que
el stack de enfrente ya te gano sin ir a buscarlo a otra pagina; es el
segundo tramo de la epica de rivales despues de la tabla de stacks (ficha 90).

**Implementar despues de que #90 se mergee**: usa `rival_stacks` de esa ficha (`replays/analytics/aggregates.py`) y suma una clave a `match_detail` (`replays/views.py`).

## Criterios de aceptacion

- [ ] `GET /api/matches/<id>/` trae una clave `rival_stacks`: lista de los
      grupos de `rival_stacks` (ficha 90, sin filtros globales: sobre todas
      tus partidas) cuyas partidas incluyen esta, cada uno con sus jugadores
      (id y nick), partidas juntos, ganadas y perdidas contra ellos. Lista
      vacia si no hay ninguno, nunca ausente.
- [ ] El record de cada grupo cuenta esta partida igual que la tabla de
      Duelos (mismos numeros que la fila de la ficha 90 para ese grupo): test
      con una base de `factories.py` donde el mismo trio rival aparece en 3
      partidas.
- [ ] Si un grupo esta contenido en otro mas grande que tambien aplica a esta
      partida, se muestra solo el mas grande (mismo criterio de maximalidad
      que la ficha 90; si la 90 no lo define, el Arquitecto lo fija aca).
- [ ] En `MatchDetail` se ve un aviso sobre el scoreboard por grupo, con los
      nicks enlazados a su perfil y un enlace a Duelos; sin grupos, no se
      renderiza nada (ni panel vacio).
- [ ] Una partida sin rondas o sin rivales identificados devuelve
      `rival_stacks: []` y el detalle no se rompe (e2e de la partida sin rondas
      sigue verde).
- [ ] e2e: una partida de `seed_demo` con stack repetido muestra el aviso con
      los numeros que fija el seed (si el seed no tiene ninguno, el Arquitecto
      decide si se agrega uno y actualiza los numeros que cambien).

## Fuera de alcance

- La columna "Última vez" (D10, otra idea).
- Stacks de tus compañeros (C1).
- Recalcular con los filtros globales: el aviso es sobre todo tu historial.
- Nombres de equipo o clan: el `.rec` no los trae.

## Diseno

(arquitecto 20261106T0015Z-cR6uHk3, sobre `origin/dev@c63314e`, con la ficha 90 ya en dev)

**Forma.** Una sola forma obvia: reusar el calculo de `rival_stacks` sin
filtros y quedarse con los grupos cuyas partidas incluyen esta. Sin arena ni
consenso (no hay migracion, parser, `recompute` ni POST). `Skills:` no aplica
(un aviso de texto con enlaces, como `textoDeRachas`; nada de un dominio nuevo).

### Backend

1. `backend/replays/analytics/aggregates.py`: partir `rival_stacks` en dos.
   - `_stacks_rivales(min_matches, **filters) -> list[tuple[frozenset[int], frozenset[int]]]`:
     el cuerpo actual hasta `mejor` inclusive (pares `(partidas, grupo)`,
     maximalidad por conjunto de partidas igual que hoy). Devuelve `[]` sin
     `me_ids`.
   - `_filas_de_stacks(pares) -> list[dict]`: lo que hoy va despues de `mejor`
     (resultado, nicks, `_record`, orden). Las dos funciones publicas lo usan
     y por eso el record es el mismo numero que la fila de Duelos.
   - `rival_stacks(min_matches=2, **filters)` queda como
     `_filas_de_stacks(_stacks_rivales(min_matches, **filters))`: mismo
     contrato, los tests de `test_stacks_rivales.py` no cambian.
   - Nueva `rival_stacks_de_partida(match_id: int, min_matches: int = 2) -> list[dict]`:
     `pares = [(ids, g) for ids, g in _stacks_rivales(min_matches) if match_id in ids]`
     (sin filtros: todo tu historial, como pide la ficha). **Maximalidad de
     esta partida** (lo fija este diseno; la de la 90 es por conjunto de
     partidas y no alcanza): se descarta un grupo si su conjunto de jugadores
     es subconjunto estricto del de otro par de la lista,
     `not any(g < otro for _, otro in pares)`. Ejemplo: A+B en 3 partidas y
     A+B+C en 2, las dos con esta partida: en Duelos salen las dos filas, aca
     solo A+B+C; en la partida donde estuvo A+B sin C, sale A+B. Despues
     `_filas_de_stacks(pares)`, mismo orden que Duelos. Docstring con el por que.
   - Nota: con la ficha 79 en dev, `base_queryset` deja afuera las partidas
     excluidas; una partida excluida no aparece en ningun grupo y su aviso
     queda vacio. Es lo coherente con Duelos; no hace falta codigo extra.
2. `backend/replays/views.py`, `match_detail`: clave
   `"rival_stacks": agg.rival_stacks_de_partida(match.id)` en el payload,
   al lado de `phases`/`team_trades`. Siempre presente (lista vacia si no hay).
   Costo: recorre las rondas de todo el historial una vez por apertura del
   detalle, lo mismo que hace Duelos; con miles de partidas sigue siendo una
   consulta y combinaciones de a lo sumo 5 rivales (26 subconjuntos por ronda).

### Frontend

3. `frontend/src/stacksRivales.js` (nuevo), logica pura:
   - `nombresDelGrupo(players)`: "A", "A y B", "A, B y C".
   - `textoStackRival(grupo)`: `"ya te tocaron juntos en 4 partidas, récord 1-3"`;
     singular "en 1 partida" (con `min_matches=1` no pasa hoy, pero el
     formateador no lo rompe); si hay partidas sin resultado
     (`matches - wins - losses > 0`) agrega `" (2 sin resultado)"`.
     El record es `wins-losses` desde tu lado, como en Duelos.
4. `frontend/src/stacksRivales.test.js` (nuevo, vitest):
   `une dos nombres con y`, `une tres nombres con comas y y`,
   `el texto lleva partidas y record`, `una sola partida va en singular`,
   `avisa las partidas sin resultado`.
5. `frontend/src/pages/MatchDetail.jsx`: componente `StacksRivales({ stacks })`
   que devuelve `null` con lista vacia o ausente (`data.rival_stacks ?? []`).
   Va **entre las `kpis` y el panel Rondas** (arriba de todo lo demas, y por
   lo tanto sobre el scoreboard), como `<div className="note stacks-rivales">`
   con una linea por grupo: los nicks como `<Link to={`/jugadores/${id}`}>`
   unidos con el mismo separador que `nombresDelGrupo` (renderizar las
   partes, no un string), el texto de `textoStackRival` y al final
   `<Link to="/duelos">Ver en Duelos</Link>`. Sin panel ni titulo si no hay
   grupos. Si hace falta CSS, una regla minima en `styles.css`
   (`margin-bottom` igual al de `.kpis`).

### Tests backend

6. `backend/tests/test_stacks_rivales.py` (agregar a la clase existente, que
   ya tiene el helper `_partida`):
   - `test_el_detalle_trae_el_stack_con_el_mismo_record_que_duelos`: trio
     A, B, C en 3 partidas (2 ganadas, 1 perdida); `GET /api/matches/<id>/`
     de una de ellas trae un grupo con `matches=3, wins=2, losses=1` e igual
     a `agg.rival_stacks()[0]`.
   - `test_el_detalle_muestra_solo_el_grupo_mas_grande_que_aplica`: A+B+C en
     las partidas 0 y 1, A+B+Z en la 2; la partida 0 trae solo A+B+C; la 2
     trae solo A+B (con `matches=3`).
   - `test_una_partida_sin_stack_trae_lista_vacia`: rivales que no se repiten
     -> `rival_stacks == []` (la clave existe).
   - `test_el_detalle_no_aplica_los_filtros`: `GET /api/matches/<id>/?map=border`
     trae el mismo grupo (la vista no lee filtros; el test lo fija).
   - `test_una_partida_sin_rondas_trae_lista_vacia`: `make_match` sin rondas
     -> 200 y `rival_stacks == []`.

### e2e

7. `frontend/e2e/stacks-rivales.spec.js`: test nuevo
   `el detalle de la partida avisa del stack rival repetido`. `seed_demo` ya
   pone al trio Kaid_, Mozzie99 y Thorn.exe en todas las rondas de las 29
   partidas, todas ganadas: no hace falta tocar el seed. Ir a `/partidas`,
   abrir la primera, y en `.stacks-rivales` esperar los tres enlaces
   (`toHaveText(['Kaid_', 'Mozzie99', 'Thorn.exe', 'Ver en Duelos'])`), el
   texto `29 partidas, récord 29-0`, y que `Ver en Duelos` lleve a `/duelos`.
   Consola limpia (`vigilarConsola`). La partida sin rondas
   (`partida-sin-rondas.json`) ya tiene su e2e: tiene que seguir verde sin
   tocarlo. Ojo: si algun e2e existente del detalle busca
   `getByRole('link', { name: 'Kaid_' })` sin acotar al panel, ahora hay dos
   enlaces; acotar ese selector al panel del scoreboard (hoy ninguno lo
   hace: `git grep -n "Kaid_" frontend/e2e` solo da `stacks-rivales.spec.js`).

### docs

8. `docs/metricas.md`, seccion `## Duelos`, fila nueva debajo de **Stack rival
   repetido**: **Stack rival en la partida** — los stacks rivales repetidos
   (misma definicion, mismo record) calculados sobre **todo** tu historial,
   sin filtros, que incluyen esta partida; si un grupo esta contenido en otro
   que tambien aplica a esta partida, sale solo el mas grande. El record
   cuenta esta partida. Detalle de la partida, aviso arriba de las rondas.

### Orden

1 -> 6 (backend en verde) -> 2 -> 3, 4 -> 5 -> `npm run build` -> 7 -> 8 -> `check.sh`.

### Que puede romperse

- El refactor de `rival_stacks`: los 10 tests de `test_stacks_rivales.py` y el
  e2e de Duelos tienen que seguir iguales sin tocarlos.
- Una partida con un solo rival repetido (no grupo) no muestra nada: correcto,
  eso es Rivales repetidos, otra tabla.
- Archivos compartidos con la rama abierta de la 79 (`aggregates.py`,
  `views.py`, `MatchDetail.jsx`, `metricas.md`, esperando merge del humano):
  zonas distintas de cada archivo, se resuelve con `git merge origin/dev`.
  Prioriza, no bloquea. Sin migracion.

### Verificacion manual

`manage.py seed_demo`, `runserver`, abrir cualquier partida: arriba de Rondas
la linea "Kaid_, Mozzie99 y Thorn.exe ya te tocaron juntos en 29 partidas,
récord 29-0 · Ver en Duelos"; clic en un nick abre su perfil; la fila de
Duelos dice lo mismo. Con la base real: abrir una partida contra rivales
nuevos y ver que no aparece nada.

OMC: plan=— (ficha chica, una forma obvia) · revisión=— · verificación=—

## Implementacion

(dev 20261106T0041Z-cqfAePA, sobre `origin/dev@c63314e`)

Quedo el diseno completo, sin desvios de forma:

- `aggregates.py`: `rival_stacks` partida en `_stacks_rivales` (pares
  partidas/grupo) y `_filas_de_stacks` (nicks, record, orden). Nueva
  `rival_stacks_de_partida(match_id)`: sin filtros, se queda con los pares que
  incluyen la partida y descarta un grupo si es subconjunto estricto de otro
  par que tambien aplica. Los 10 tests previos de `test_stacks_rivales.py` no
  se tocaron y siguen verdes.
- `views.py` `match_detail`: clave `rival_stacks`, siempre presente.
- `frontend/src/stacksRivales.js` + test (6 vitest): `nombresDelGrupo`,
  `textoStackRival` y, ademas del diseno, `separadorAntes(i, total)`, que usa
  la vista para poner los nicks como enlaces con la misma puntuacion (un test
  fija que reconstruye el mismo texto que `nombresDelGrupo`).
- `MatchDetail.jsx`: `StacksRivales` entre las `kpis` y el panel Rondas;
  `null` sin grupos. CSS: `.stacks-rivales` (margen 18px, 13px).
- `docs/metricas.md`: fila **Stack rival en la partida** en Duelos.

Desvio no previsto en el diseno: `frontend/e2e/partida-sin-rondas.json` suma
`"rival_stacks": []`; `test_partida_sin_rondas` compara el payload entero y
obliga a regenerarlo (lo dice su docstring).

Criterios -> tests:
- clave siempre presente / lista vacia: `test_una_partida_sin_stack_trae_lista_vacia`,
  `test_una_partida_sin_rondas_trae_lista_vacia`, `test_el_detalle_de_una_partida_sin_rondas_responde_200`.
- mismo record que Duelos (trio en 3 partidas): `test_el_detalle_trae_el_stack_con_el_mismo_record_que_duelos`.
- solo el grupo mas grande: `test_el_detalle_muestra_solo_el_grupo_mas_grande_que_aplica`.
- sin filtros: `test_el_detalle_no_aplica_los_filtros` (por la vista y por la funcion).
- aviso en el detalle con enlaces y Duelos: e2e `el detalle de la partida avisa del stack rival repetido`
  (Kaid_, Mozzie99 y Thorn.exe, 29 partidas, récord 29-0; seed sin cambios).
- partida sin rondas no se rompe: e2e existente de la partida sin rondas, verde sin tocarlo.

Revision ciega (omc-code-reviewer, revision.md): 0 CRITICAL/HIGH, 1 MEDIUM, 3 LOW.
Arreglados: MEDIUM (el test de filtros pasaba siempre porque la vista no lee
`request.GET`: ahora tambien afirma sobre `rival_stacks_de_partida` contra
`rival_stacks(map=...)`), LOW de doc (el record coincide con Duelos *sin
filtros*) y LOW de `nombresDelGrupo` (comentario de para que existe). Queda el
LOW de costo: cada apertura del detalle recorre el historial como Duelos; lo
asume el diseno.

verificar.sh: VERDE f14af40eb (1005 tests backend, 216 vitest, 68 e2e).

Skills: no aplica (lo dice el diseno). 
OMC: plan=— · revisión=4 hallazgos (3 arreglados) · verificación=—

## Revision

## QA

## Pendiente

## Para el humano
