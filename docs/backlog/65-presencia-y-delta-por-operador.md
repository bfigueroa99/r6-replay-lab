# 65. Presencia y delta de winrate por operador

estado: implementado
candado: -
rama: claude/equipo-dev/65-presencia-y-delta-por-operador
tipo: funcionalidad
epica: operadores
area: fullstack
prioridad: 3
fuente: ALCANCE.md O5 (replica/features.csv fila 26, must, clone partial; [r6tv](https://r6tv.online/how-it-works), [aurelix](https://aurelix.app/blog/how-to-analyse-r6-siege-replays))
archivos: backend/replays/analytics/aggregates.py, frontend/src/pages/Operators.jsx, backend/tests/test_operadores_presencia.py, frontend/e2e/humo.spec.js, docs/metricas.md
turnos: po 20261027T1205Z, arquitecto 20261027T1605Z, dev 20261028T0804Z

## PR

(La escribe el Release manager al final.)

## Que gana quien usa la app

En Operadores hoy se ve el winrate de cada operador, pero no si es mejor o
peor que tu winrate normal en ese lado ni cuanto lo juegas. Con dos columnas
nuevas, presencia (% de tus rondas de ese lado jugadas con el) y delta
(su winrate menos tu winrate base del lado), queda claro que operador te sube
y cual te baja, y si el numero se apoya en muchas rondas o en pocas.

## Criterios de aceptacion

- [ ] Cada fila de `GET /api/operators/` trae `presence_pct` = rondas con ese
      operador en ese lado / tus rondas de ese lado (con los mismos filtros), y
      `winrate_delta` = winrate del operador - winrate base del lado, en puntos.
      Test: 10 rondas de ataque, 4 con Ash (3 ganadas) y 6 con otro (3 ganadas):
      Ash con 40 % de presencia y +25 puntos (75 - 50).
- [ ] El winrate base del lado sale de todas tus rondas de ese lado con los
      filtros activos, aunque `min_rounds` oculte filas: ocultar un operador no
      mueve el delta de los demas. Test con `min_rounds`.
- [ ] Con filtro de operador o de lado (`side=Defense`), presencia y delta
      siguen definidos sobre las rondas que el filtro deja; una fila sin rondas
      ganadas ni perdidas (todas sin ganador) da `winrate_delta: null`. Base
      vacia: lista vacia, 200.
- [ ] La tabla de `Operators.jsx` muestra las columnas "Presencia" y "vs. tu
      lado" (con signo, +/-), ordenables, con ayuda que dice como se calculan,
      y el CSV de la tabla las incluye. El e2e afirma que la columna aparece.
- [ ] Filas en `docs/metricas.md` para las dos columnas; si el delta va con
      banda de ruido (`_ruido` de `aggregates.py`), la fila lo dice.

## Fuera de alcance

- El corte por mapa y sitio (idea O1): va despues, como su propio tramo.
- Cambiar la señal del Coach que ya compara operador contra tu promedio.
- Rating relativo al operador (idea O3).

## Diseno

(Arquitecto 20261027T1605Z, sobre origin/dev 2532ed1.) Sin migracion, sin
recompute, sin parser. Ninguna rama de trabajo abierta: no pisa nada. Toca
`aggregates.py` igual que la 64, en otra funcion: si las dos van en paralelo,
el merge es limpio (bloques distintos).

Skills: no aplica (dos columnas mas en una `DataTable` que ya existe). Sin
arena: una sola forma obvia.

**Decisiones:**

- Todo en `agg.by_operator`, para que `/api/operators/`, el CSV de la tabla y
  `/api/export/?table=operators` traigan lo mismo. `coach.py` (`_operators`,
  `min_rounds=12`) solo gana dos claves que no lee: no cambia ninguna señal.
- **Base del lado** = el mismo `qs` de la tabla (`base_queryset(**filters)
  .exclude(operator="")`) agrupado por `side`, **antes** de `min_rounds`: asi
  las presencias de un lado suman 100 % y ocultar filas no mueve nada.
  `presence_pct = _pct(rondas de la fila, rondas del lado)`.
- `winrate_delta = _delta(fila["winrate"], winrate_base_del_lado)` (en puntos,
  un decimal, con el `winrate` de siempre: rondas ganadas / rondas, el mismo
  numero que muestra la columna "Ganadas").
- **Sin ganador:** `RoundPlayer.won` no es nulo (default `False`); la ronda sin
  ganador es `Round.my_team_won` nulo. `winrate_delta` va `None` si la fila no
  tiene ninguna ronda con `round__my_team_won__isnull=False`, o si el lado
  entero no tiene ninguna. Se cuenta con una query aparte
  (`qs.filter(round__my_team_won__isnull=False).values("operator","side")
  .annotate(n=Count("id"))`), no en `AGGREGATES` (que usan todas las tablas).
- **Filtros:** `side` y `operator` recortan la base como cualquier filtro (lo
  pide el criterio). Consecuencia que se documenta: con `operator=Ash` la fila
  de Ash queda 100 % de presencia y delta 0. La pagina Operadores ya esconde
  el filtro de operador (`showOperator={false}`), asi que en la UI no pasa.
- **Sin banda de ruido:** la fila es un subconjunto de la base, no una muestra
  independiente, y `_ruido` supone dos muestras independientes. La columna
  Presencia es la que dice cuanto pesa el numero. La fila de `metricas.md` lo
  dice.

**Archivos:**

1. `backend/replays/analytics/aggregates.py`, `by_operator`:
   ```python
   qs = base_queryset(**filters).exclude(operator="")
   rows = group_by(qs, "operator", "side", labels=("operator", "side"), min_rounds=min_rounds)
   lados = {r["side"]: r for r in qs.values("side").annotate(
       rounds=Count("id"), rounds_won=Count("id", filter=Q(won=True)),
       decided=Count("id", filter=Q(round__my_team_won__isnull=False)))}
   decididas = {(r["operator"], r["side"]): r["n"] for r in ...}
   ```
   y por fila `presence_pct` y `winrate_delta` como arriba. Docstring de una
   linea con el por que de la base antes de `min_rounds`.
2. `frontend/src/pages/Operators.jsx`, `Table`: columna `presence_pct`
   "Presencia" (`digits: 0, suffix: '%'`, help: "Rondas con este operador /
   todas tus rondas de ese lado, con los filtros activos.") despues de
   "Rondas"; columna `winrate_delta` "vs. tu lado" despues de "Ganadas", con
   `render` que muestra `—` si es null, y si no `Math.round(v)` con `+` cuando
   es mayor que 0 (un -0.4 se ve `0`, no `-0`), en `chip win` / `chip loss`
   como el delta de `Teammates.jsx` (0 sin chip de color: `chip`); help:
   "Winrate con este operador menos tu winrate de todas las rondas de ese lado,
   en puntos. Un +10 con poca presencia puede ser varianza." Las dos son
   ordenables por defecto; el CSV del `DataTable` toma `row[col.key]` crudo
   (sin `csv:` propio: queda el numero con coma decimal, no el chip).
   Subtitulo de la pagina: agregar " «vs. tu lado» compara cada operador con tu
   winrate en ese lado."
3. `backend/tests/test_operadores_presencia.py` (nuevo), con `factories`:
   - `test_presencia_y_delta_contra_el_lado` (10 rondas de ataque: 4 Ash con 3
     ganadas, 6 Thermite con **2** ganadas -> base 5 de 10 = 50 %; Ash 40.0 y
     25.0, Thermite 60.0 y -16.7). **Correccion al criterio:** el ejemplo de la
     ficha pone 3 ganadas para el otro operador, pero entonces la base es 60 %
     y Ash da +15, no +25; con 2 ganadas los numeros del criterio (40 % y +25)
     cierran. QA marca la casilla con este caso.
   - `test_min_rounds_no_mueve_la_base` (`by_operator(min_rounds=5)`: Ash
     desaparece y Thermite conserva 60.0 y -16.7)
   - `test_cada_lado_tiene_su_base` (rondas de defensa no entran a la base de
     ataque)
   - `test_las_presencias_de_un_lado_suman_cien`
   - `test_filtro_de_lado_recorta_la_base` (`side="Defense"`: solo filas de
     defensa, presencia sobre defensa)
   - `test_fila_sin_rondas_decididas_no_tiene_delta` (rondas de un operador con
     `make_round(won=None)` -> `winrate_delta` `None`, `presence_pct` sigue)
   - `test_base_vacia_devuelve_lista_vacia` (por la API: 200, `operators: []`)
   - `test_el_export_de_operadores_trae_las_columnas` (`/api/export/?table=operators`
     tiene `presence_pct` y `winrate_delta` en la cabecera)
4. `frontend/e2e/humo.spec.js`: test `Operadores muestra presencia y delta`:
   en `/operadores`, panel "Ataque": los `th` "Presencia" y "vs. tu lado"
   visibles; la fila de Ash (seed: 39 de 116 rondas de ataque = 33.6 %) tiene
   la celda `34%`; con `seed_demo` todo el ataque se gana y toda la defensa se
   pierde, asi que el delta de Ash es `0` (afirmarlo: es el caso del `-0`).
5. `docs/metricas.md`, seccion `## Cortes`, debajo de **Operador**: filas
   **Presencia** y **vs. tu lado** con las definiciones de arriba, la base
   antes del minimo de rondas, el `null` sin rondas decididas, que el filtro
   de operador deja 100 % y 0, y que no lleva banda de ruido y por que.

**Orden:** 1 + 3 -> `python manage.py test tests` -> 2 -> `npm run build` ->
4 -> 5 -> `./scripts/check.sh`.

**Que puede romperse:** `test_rating.py:89` lee `by_operator` (solo mira el
rating: claves nuevas no le molestan). `test_export` si compara la cabecera
del CSV de operadores entera (revisar; si la compara, se agregan las dos
columnas al final, que es donde `_columnas` las pone).

**Verificacion manual:** `seed_demo --force`, `/operadores`: Ash 34 %, Zofia
34 %, Thermite 33 % (suman 101 por el redondeo; sin redondear, 100), deltas 0; ordenar por
"vs. tu lado" no deja nulos arriba (`ordenarFilas` ya los manda al final);
bajar el CSV de Ataque y ver las dos columnas.

## Implementacion

(Dev 20261028T0804Z.)

Skills: no aplica (lo resuelve el diseno; sin arena).

Quedo todo el diseno:

- `aggregates.by_operator`: `presence_pct` y `winrate_delta` por fila, con la
  base del lado contada sobre el queryset entero antes de `min_rounds` y una
  query aparte para las rondas con ganador. El delta es `None` si la fila no
  tiene ninguna ronda decidida (si el lado no tiene ninguna, sus filas
  tampoco: no hace falta mirar el lado aparte).
- `Operators.jsx`: columnas "Presencia" (despues de Rondas) y "vs. tu lado"
  (despues de Ganadas), con ayuda; el delta redondea antes de elegir signo y
  color (`-0.4` se ve `0`, chip neutro). Subtitulo actualizado.
- Tests (`backend/tests/test_operadores_presencia.py`): los ocho del diseno,
  mas `test_la_api_trae_las_columnas`. El primer criterio usa la correccion del
  Arquitecto (Thermite con 2 ganadas: 40 % y +25).
- e2e `Operadores muestra presencia y delta`: Ash en Ataque con `34%` y `0`.
- `docs/metricas.md`, `## Cortes`: filas Presencia y vs. tu lado.

Desvios: el diseno pedia `None` tambien si el lado no tiene rondas
decididas; esa rama era inalcanzable (la fila es parte del lado) y se quito
tras la revision ciega. El e2e no ejercita signo ni color del delta (en el
seed todos dan 0); esa logica es de render y no tiene test propio. `test_export` no compara la cabecera de operadores entera,
asi que no hubo que tocarlo.

## Para el humano

(Nada por ahora.)
