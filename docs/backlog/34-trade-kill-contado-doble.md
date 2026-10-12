# 34. Una baja que venga a dos compañeros cuenta como dos trade kills

estado: entregado
candado: -
rama: claude/equipo-dev/34-trade-kill-contado-doble
area: backend
prioridad: 2
fuente: bug reproducido en main 0b547d7 llamando a `metrics.annotate_trades` directo: eventos `d1 -> a1` (150 s), `d1 -> a2` (149 s), `a3 -> d1` (148 s), equipos `a1/a2/a3 = 0`, `d1 = 1`, ventana 5 s. Resultado: `a3.trade_kills == 2` con una sola baja. El bucle de `annotate_trades` recorre cada muerte y busca la venganza; si el asesino mato a dos, la misma baja vengadora suma una vez por cada victima. `docs/metricas.md` define trade kill como "una baja que ademas deshace una perdida" (+0.3 en el rating) y "veces que tu mataste al asesino de un compañero".
archivos: backend/replays/analytics/metrics.py, backend/tests/test_metrics.py, backend/tests/test_recompute.py, docs/metricas.md
turnos: po 20261010T0301Z, arquitecto 20261010T0602Z, dev 20261010T0902Z, revisor 20261010T1202Z, qa 20261010T1801Z, release 20261012T1640Z

## PR

Titulo: `[equipo-dev][backend] Una baja que venga a dos compañeros cuenta como un solo trade kill`

## Que cambia

Cuando un rival hace un doble y lo matas dentro de la ventana de trade, la app te contaba dos trade kills y +0.6 de rating por una sola baja; ahora cuenta una, y `trade_kills` nunca supera a `kills`. Las dos muertes de tus compañeros siguen contando como tradeadas, que es lo que paso.

## Por que esto y no otra cosa

Bug encontrado por el PO (ficha 34) y reproducido en main 0b547d7: `annotate_trades` sumaba el trade kill dentro del bucle de muertes vengadas, una vez por victima. Ahora junta los indices de las bajas vengadoras en un `set` y suma uno por baja al final; la deteccion de "muerte vengada" no cambia. Se descarto tocar la ventana, la regla de quien cuenta como vengador o el peso del trade kill en el rating (fuera de alcance). `replays/recompute.py` no se toca: ya llama a `annotate_trades` y compara `trade_kills`, asi que `manage.py recompute` corrige las partidas importadas.

## Como se probo

- `./scripts/check.sh`: `Todo en verde.` (ruff, tests backend, 53 vitest, build, 17 e2e) sobre la rama con `origin/main` fusionado.
- Tests nuevos:
  - `TradeTests.test_una_baja_que_venga_a_dos_companeros_cuenta_una_vez`: doble vengado -> `trade_kills == 1` y las dos victimas `was_traded`.
  - `TradeTests.test_dos_venganzas_sobre_dos_asesinos_suman_dos`: dos bajas vengadoras distintas siguen sumando 2 (pasa tambien en main, a proposito).
  - `TradeTests.test_trade_kills_nunca_supera_a_kills`: doble y triple vengados, `trade_kills <= kills` para todos.
  - `RecomputeDobleTests.test_recompute_corrige_el_trade_kill_contado_doble`: una fila guardada con 2 queda en 1 despues de `recompute`, que lo cuenta como cambio; un segundo `recompute` no cambia nada.
- Revision ciega sin hallazgos. QA: `recompute` real sobre filas sembradas como el import viejo corrige 2 -> 1 y 3 -> 1, deja 2 donde son dos venganzas, es idempotente; `seed_demo` + `recompute`: 0 de 1320 filas con `trade_kills > kills`. 3 mutaciones, las 3 caen.

## Riesgos y lo que no entra

Cambian numeros historicos: trade kills y rating de las rondas con un doble o triple vengado, una vez que se corre `recompute` en la base real. Sin migracion, sin cambios de API, de frontend ni del parser. `seed_demo` escribe `trade_kills` a mano, asi que los numeros del e2e no se mueven.

## Como probarlo en 2 minutos

```bash
cd backend
python manage.py test tests.test_metrics tests.test_recompute
```

Tienen que pasar los 32 tests, entre ellos los cuatro nuevos de arriba.

### Verificar en el PC

En la base real, desde `backend/`:

```powershell
..\.venv\Scripts\python.exe manage.py recompute --dry-run   # cuantas filas cambiarian
..\.venv\Scripts\python.exe manage.py backup                # por las dudas
..\.venv\Scripts\python.exe manage.py recompute
```

Despues, en la UI, ninguna fila de jugador muestra mas trade kills que bajas.

## Para el humano

Nada que decidir. Despues del merge, correr el `recompute` de "Verificar en el PC".

## Candidatos descubiertos

Ninguno.

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

(Arquitecto 20261010T0602Z, sobre main 0b547d7.) En `annotate_trades`, juntar
los indices de las bajas vengadoras en un `set` y sumar 1 por indice al final
(`range(i + 1, len(...))` para tener el indice); mismas condiciones de
venganza. `replays/recompute.py` lo hereda sin tocarlo. Tests en
`test_metrics.py` (parametro `extra_players` en `_round`) y
`RecomputeDobleTests` en `test_recompute.py`. Fila **Trade kills** de
`docs/metricas.md` aclarada. Sin migracion, sin frontend, sin numero nuevo.

## Implementacion

(Dev 20261010T0902Z.) Tal cual el diseno, sin desvios. Sin el arreglo fallan
4 tests nuevos; el de dos venganzas pasa en main, como pide el criterio 2.
Revision ciega: aprobar; unico hallazgo, una ñ en un comentario, corregido.

## Revision 2026-10-10 sobre 9faff04

(Revisor 20261010T1202Z.) `check.sh` en verde. Revision ciega sin hallazgos;
mutacion confirmada por el lider (con `metrics.py` de main caen exactamente
los 4 nuevos). Veredicto: aprobar.

## QA 2026-10-10 sobre 3dd63a0

(QA 20261010T1801Z.) main 0b547d7 incluido; `check.sh` en verde (399 backend,
53 vitest, build, 17 e2e). `recompute --dry-run` y `recompute` reales sobre una
base sembrada como el import viejo: doble 2 -> 1, triple 3 -> 1, dos venganzas
siguen en 2, 0 filas con `trade_kills > kills`, segundo `recompute` sin cambios.
`seed_demo` + `recompute`: 0 de 1320 filas con `trade_kills > kills`.
Mutaciones (`metrics.py` de main, lista en vez de `set`, sin `was_traded`):
las 3 caen. Veredicto: aprobado.
