# 34. Una baja que venga a dos compañeros cuenta como dos trade kills

estado: aprobado
candado: -
rama: claude/equipo-dev/34-trade-kill-contado-doble
area: backend
prioridad: 2
fuente: bug reproducido en main 0b547d7 llamando a `metrics.annotate_trades` directo: eventos `d1 -> a1` (150 s), `d1 -> a2` (149 s), `a3 -> d1` (148 s), equipos `a1/a2/a3 = 0`, `d1 = 1`, ventana 5 s. Resultado: `a3.trade_kills == 2` con una sola baja. El bucle de `annotate_trades` recorre cada muerte y busca la venganza; si el asesino mato a dos, la misma baja vengadora suma una vez por cada victima. `docs/metricas.md` define trade kill como "una baja que ademas deshace una perdida" (+0.3 en el rating) y "veces que tu mataste al asesino de un compañero".
archivos: backend/replays/analytics/metrics.py, backend/tests/test_metrics.py, backend/tests/test_recompute.py, docs/metricas.md
turnos: po 20261010T0301Z, arquitecto 20261010T0602Z, dev 20261010T0902Z, revisor 20261010T1202Z, qa 20261010T1801Z

## PR

(La escribe el Release manager al final: titulo `[equipo-dev][area] Titulo`,
cuerpo segun `.claude/skills/equipo-dev/plantilla-pr.md` y una seccion
"Como probarlo en 2 minutos" con comandos exactos.)

## Que gana quien usa la app

Cuando un rival hace un doble y vos lo matas, hoy la app te cuenta dos trade
kills y te suma +0.6 al rating por una sola baja; con el arreglo cuenta una, y
`trade_kills` nunca supera a `kills`. Las dos muertes de tus compañeros siguen
contando como tradeadas, que es lo que realmente paso.

## Criterios de aceptacion

- [x] Con los eventos de la fuente (3 atacantes, un defensor que mata a dos y muere a manos del tercero dentro de la ventana), `analyse_round` deja `trade_kills == 1` al vengador y `was_traded == True` a las dos victimas (test en `tests/test_metrics.py`).
- [x] Dos bajas vengadoras distintas sobre dos asesinos distintos siguen sumando 2 (test: el caso que hoy funciona no cambia).
- [x] En cualquier ronda, `trade_kills <= kills` para cada jugador: test que arma una ronda con un doble y un triple vengados y lo afirma para todos.
- [x] `manage.py recompute` corrige las filas ya importadas: una ronda guardada con `trade_kills = 2` para esa secuencia queda en 1 despues del recompute, y el resumen lo cuenta como cambio (test en `tests/test_recompute.py`).
- [x] Los tests existentes de `TradeTests` y de `test_recompute.py` siguen en verde sin cambios.

## Fuera de alcance

- Cambiar la ventana de trade, la regla de quien cuenta como vengador o el peso del trade kill en el rating.
- Que una muerte vengada cuente distinto segun cuantos compañeros cayeron antes.
- `seed_demo`: no pasa por `annotate_trades` (escribe `trade_kills` a mano), asi que los numeros del e2e no se mueven.

## Diseno

(Arquitecto 20261010T0602Z, sobre main 0b547d7.) Bug confirmado con un spike en
el scratchpad: con la secuencia de la fuente `a3.trade_kills` da 2 en main y 1
con el arreglo, y las dos muertes siguen `traded`. Sin migracion, sin frontend,
sin numero nuevo.

**Archivos y por que**

- `backend/replays/analytics/metrics.py`: `annotate_trades` es la unica
  implementacion de la regla (la llaman `analyse_round` y `replays/recompute.py`),
  asi que el arreglo va solo ahi y el recompute lo hereda sin tocarlo.
- `backend/tests/test_metrics.py`: casos de `analyse_round`.
- `backend/tests/test_recompute.py`: el recompute corrige filas viejas.
- `docs/metricas.md`: precisar la definicion de **Trade kills** (no es un
  numero nuevo, es la misma fila con la aclaracion).

`replays/recompute.py` no se toca: ya llama a `annotate_trades` y compara
`trade_kills` campo a campo (`CAMPOS`), asi que una fila con 2 que pasa a 1
cuenta como `players_changed`.

**Cambio en `annotate_trades`**

La pregunta "esta muerte fue vengada" sigue igual (por cada muerte `e`, la
primera baja posterior dentro de la ventana sobre el asesino, hecha por un
compañero de la victima). Lo que cambia es como se cuenta el vengador: en vez
de `trade_kills += 1` dentro del bucle, se juntan los **indices** de las bajas
vengadoras en un `set` y al final se suma 1 por indice. Asi una baja vengadora
que deshace dos muertes cuenta una vez. Esbozo:

```python
vengadoras: set[int] = set()
for i, e in enumerate(kill_events):
    ...
    for j in range(i + 1, len(kill_events)):
        later = kill_events[j]
        ...  # mismas condiciones de hoy
        e["traded"] = True
        if victim in metrics:
            metrics[victim]["was_traded"] = True
        vengadoras.add(j)
        break
for j in vengadoras:
    actor = kill_events[j]["actor"]
    if actor in metrics:
        metrics[actor]["trade_kills"] += 1
```

Cambiar `kill_events[i + 1 :]` por `range(i + 1, len(...))` hace falta para
tener el indice; el resto de las condiciones (`gap`, `break`, `continue`) queda
literal. Comentario de una linea arriba del `set` con el por que (una baja que
venga a dos compañeros es una sola baja). El reset del principio no cambia.

**Tests nuevos** (todos con la ventana por defecto de settings, 3 s; la secuencia
de la fuente cabe: gaps de 1 y 2 s)

`_round` arma 2 contra 2. Agregar en `test_metrics.py` un parametro opcional
`extra_players` a `_round` (lista de dicts de jugador que se suman a `players`
y a las `stats` por defecto) en vez de un helper paralelo; los tests viejos no
lo pasan y no cambian. En `TradeTests`:

1. `test_una_baja_que_venga_a_dos_companeros_cuenta_una_vez`. Eventos
   `def1 -> atk1` (150), `def1 -> atk2` (149), `atk3 -> def1` (148). Afirma
   `atk3.trade_kills == 1`, `atk1.was_traded` y `atk2.was_traded`, y
   `events[0]["traded"]` y `events[1]["traded"]`.
2. `test_dos_venganzas_sobre_dos_asesinos_suman_dos`: `def1 -> atk1` (150),
   `atk3 -> def1` (149), `def2 -> atk2` (140), `atk3 -> def2` (139). Afirma
   `atk3.trade_kills == 2`.
3. `test_trade_kills_nunca_supera_a_kills`: dos rondas en el mismo test, un
   `subTest` por ronda.
   - Doble vengado: `extra_players` con `atk3`; `def1 -> atk1` (150),
     `def1 -> atk2` (149), `atk3 -> def1` (148).
   - Triple vengado: `extra_players` con `atk3` y `atk4` (3 victimas y el
     vengador); `def1 -> atk1` (150), `def1 -> atk2` (149), `def1 -> atk3`
     (148), `atk4 -> def1` (147).
   En las dos, las `stats` de cada jugador llevan `kills` igual a sus bajas del
   guion y `died` segun corresponda (el `kills` de `analyse_round` sale de
   `stats`, no del kill feed). El test recorre **todos** los jugadores
   afirmando `trade_kills <= kills`, y ademas `atk4.trade_kills == 1` en la
   segunda.
4. En `test_recompute.py`, clase nueva `RecomputeDobleTests(TestCase)`
   (el `setUp` de `RecomputeTests` arma otra ronda):
   `test_recompute_corrige_el_trade_kill_contado_doble`. Con `factories`:
   ronda con `ME` (atk, muere), `amigo` (atk, muere), `vengador` (atk,
   `kills=1`, `died=False`, `trade_kills=2` guardado a mano, como lo dejo el import viejo) y
   `rival` (def, `kills=2`, muere); eventos `rival -> ME` (100), `rival ->
   amigo` (99), `vengador -> rival` (98). `recompute(window=3.0)`; afirma
   `vengador.trade_kills == 1`, `result.players_changed >= 1` y
   `result.changed`. Un segundo `recompute` deja `changed` en `False`
   (idempotente).

Los tests existentes de `TradeTests`, `VentanaTests`, `RecomputeTests` y
`ComandoTests` no se tocan y tienen que seguir verdes.

**Orden**

1. Tests 1, 2 y 3 (fallan el 1 y el 3 en main; el 2 pasa).
2. Arreglo en `annotate_trades`; los tres en verde.
3. Test 4 del recompute (en main falla igual: el recompute recalcula 2).
4. `docs/metricas.md`, fila **Trade kills** de la tabla de `## Trades`:
   "Veces que **tu** mataste al asesino de un compañero dentro de la ventana.
   Cuenta bajas, no compañeros vengados: si el rival habia matado a dos y lo
   matas, es un trade kill (y las dos muertes cuentan como tradeadas)."
5. `check.sh`.

**Que puede romperse**

- Rating: `trade_kills` pesa +0.3 en el rating por ronda; las rondas con
  dobles vengados bajan. Es el arreglo, no un efecto colateral, pero cambia
  numeros historicos despues de `recompute`.
- `seed_demo` escribe `trade_kills` a mano y no pasa por `annotate_trades`: el
  e2e no se mueve. Si el Dev ve que si pasa, parar y anotarlo.
- Sin migracion, sin cambios de API ni de frontend, sin build afectado.

**Verificacion manual**

`cd backend && python manage.py test tests.test_metrics tests.test_recompute`.
En una base real (PC del humano): `python manage.py recompute --dry-run`
muestra cuantas filas cambiarian; despues `python manage.py recompute`. Va a
`## Verificar en el PC` (lo escribe QA). README: la fila de `recompute` ya dice
que recalcula trades; no hace falta tocarlo.

**Choques:** ninguno. La unica rama abierta (#33) toca `replays/views.py` y
`tests/test_dates.py`.

## Implementacion

(Dev 20261010T0902Z.) Implementado tal cual el diseno, sin desvios de alcance.

- `annotate_trades` junta los indices de las bajas vengadoras en un `set` y
  suma 1 por indice al final; la deteccion de "muerte vengada" no cambio.
- `test_metrics.py`: parametro `extra_players` en `_round` (los tests viejos no
  lo pasan); helpers `_atacante` y `_stats_del_guion` (stats coherentes con el
  kill feed, porque `kills` sale de `stats`). Tests nuevos en `TradeTests`:
  `test_una_baja_que_venga_a_dos_companeros_cuenta_una_vez`,
  `test_dos_venganzas_sobre_dos_asesinos_suman_dos`,
  `test_trade_kills_nunca_supera_a_kills` (subTest doble y triple).
- `test_recompute.py`: `RecomputeDobleTests.test_recompute_corrige_el_trade_kill_contado_doble`
  (incluye el segundo recompute idempotente).
- `docs/metricas.md`: fila **Trade kills** con la aclaracion.

Criterios -> tests: 1 `..._cuenta_una_vez`; 2 `..._suman_dos`; 3
`..._nunca_supera_a_kills`; 4 `RecomputeDobleTests`; 5 suite completa verde sin
tocar tests existentes.

Verificado: sin el arreglo en `metrics.py` fallan 4 (el 1, el 3 en sus dos
subtests y el 4); el 2 pasa en main como se esperaba. `seed_demo` no pasa por
`annotate_trades`: e2e sin cambios. Revision ciega (`revision.md`): veredicto
aprobar; unico hallazgo, una ñ en un comentario, corregido.
`check.sh`: Todo en verde (399 backend, 53 frontend, 17 e2e, build ok).

## Revision 2026-10-10 sobre 9faff04

(Revisor 20261010T1202Z.) Rama ya contiene main 0b547d7 (merge-tree limpio); `check.sh`
en verde sobre 9faff04: ruff ok, 399 backend, 53 vitest, build, 17 e2e.

Revision a ciegas (subagente con `revision.md` sobre el diff sin
`docs/backlog`): sin hallazgos. Confirmado por el lider:

- Mutacion: con `metrics.py` de `origin/main` y los tests de la rama fallan
  exactamente los 4 nuevos (`..._cuenta_una_vez`, `..._nunca_supera_a_kills`
  [doble] y [triple], `RecomputeDobleTests`); `..._suman_dos` pasa en los dos,
  como pide el criterio 2. Los asserts ven el bug.
- La deteccion de muerte vengada no cambio (mismas condiciones, mismo
  `break`); solo se mueve la suma al final, por indice. El reset de
  `trade_kills` sigue arriba, asi que `recompute` baja los 2 viejos a 1 y lo
  cuenta en `players_changed` (`trade_kills` esta en `CAMPOS`).
- `_stats_del_guion` saca `kills` del mismo guion de eventos: el
  `trade_kills <= kills` del criterio 3 compara contra bajas reales, no
  contra un 0 por defecto.

Ficha: criterios 1-4 con test con nombre, 5 con la suite completa sin tocar
tests existentes. Diff dentro de `archivos:`. Sin numero nuevo (fila
**Trade kills** aclarada en `metricas.md`). Sin tildes en identificadores ni
comentarios, sin `print`.

Veredicto: aprobar

## QA 2026-10-10 sobre 3dd63a0

(QA 20261010T1801Z.) La rama ya contiene `origin/main` 0b547d7. Sin `.env`.
Los scripts de siembra viven en el scratchpad (`sembrar.py`, `ver.py`, con
`tests/factories.py`); nada de `.rec` ni `.sqlite3` al repo.

- `check.sh` -> `Todo en verde.`: ruff ok, 399 tests backend (4 skipped),
  53 vitest, build, 17 e2e. Cubre los pasos de `ci.yml`.
- Criterios 1-4 de punta a punta con el comando real, base nueva
  (`DATA_DIR=<tmp> migrate`) sembrada con filas como las dejaba el import
  viejo: ronda 1 doble vengado (`vengador` con `trade_kills=2`), ronda 2
  triple vengado por `ME` (`trade_kills=3`), ronda 3 dos venganzas sobre dos
  asesinos (`trade_kills=2`), ronda 4 sin bajas.
  - Antes: 2 filas con `trade_kills > kills`.
  - `manage.py recompute --dry-run` -> "cambiarian 9 filas de jugador y 7
    eventos sobre 4 rondas"; `manage.py recompute` -> "se actualizaron 9
    filas ...".
  - Despues: ronda 1 `vengador` 1, ronda 2 `ME` 1, ronda 3 `ME` sigue en 2
    (criterio 2); 0 filas con `trade_kills > kills` (criterio 3); todas las
    victimas de las rondas 1-3 con `untraded_death=False` (las muertes
    siguen contando como tradeadas).
  - Segundo `recompute` -> "Nada que recalcular ... las 4 rondas ya estan al
    dia" (idempotente).
- API sobre esa base (`runserver :8767`): `overview` da `trade_kills` 3 para
  `ME` (1 + 2; con el bug eran 5) y `traded_pct` 100. overview, coach,
  teammates, duels, sessions, players/1, trends y operators con `""`,
  `since=foo`, `page=-1` -> 200. Con `until=2026-08-03T18:00Z` dan 500: es
  el bug de la ficha 33 (`aprobado`), que esta rama todavia no trae; no es
  de este diff.
- `seed_demo` + `recompute`: 1320 filas, 0 con `trade_kills > kills`.
- Mutacion (`tests.test_metrics tests.test_recompute`, 32 tests):
  `metrics.py` de `origin/main` -> 4 fallos (`..._cuenta_una_vez`,
  `..._nunca_supera_a_kills` [doble] y [triple], `RecomputeDobleTests`);
  `vengadoras` como lista en vez de `set` -> los mismos 4; sin marcar
  `was_traded` -> 6 fallos (incluido `..._cuenta_una_vez`). Restaurado: 32 OK.
  `..._suman_dos` pasa con el codigo de main, como pide el criterio 2.
- Criterio 5: el diff no toca tests existentes; suite completa en verde.
- Merge de prueba: 34 x 33 y 34 x 35 limpios.

Veredicto: aprobado.

## Verificar en el PC

Cambian numeros historicos (trade kills y rating de las rondas con un doble
o triple vengado). En la base real, desde `backend/`:

```powershell
..\.venv\Scripts\python.exe manage.py recompute --dry-run   # cuantas filas cambiarian
..\.venv\Scripts\python.exe manage.py backup                # por las dudas
..\.venv\Scripts\python.exe manage.py recompute
```

Despues, en la UI, que ninguna fila de jugador muestre mas trade kills que
bajas.

## Pendiente

(Solo si alguien dejo trabajo a medias: que falta y donde se trabo.)

## Para el humano

(Cualquiera, solo si hace falta una decision suya.)
