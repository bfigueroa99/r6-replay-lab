# 34. Una baja que venga a dos compañeros cuenta como dos trade kills

estado: propuesto
candado: -
rama: -
area: backend
prioridad: 2
fuente: bug reproducido en main 0b547d7 llamando a `metrics.annotate_trades` directo: eventos `d1 -> a1` (150 s), `d1 -> a2` (149 s), `a3 -> d1` (148 s), equipos `a1/a2/a3 = 0`, `d1 = 1`, ventana 5 s. Resultado: `a3.trade_kills == 2` con una sola baja. El bucle de `annotate_trades` recorre cada muerte y busca la venganza; si el asesino mato a dos, la misma baja vengadora suma una vez por cada victima. `docs/metricas.md` define trade kill como "una baja que ademas deshace una perdida" (+0.3 en el rating) y "veces que tu mataste al asesino de un compañero".
archivos: -
turnos: po 20261010T0301Z

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

- [ ] Con los eventos de la fuente (3 atacantes, un defensor que mata a dos y muere a manos del tercero dentro de la ventana), `analyse_round` deja `trade_kills == 1` al vengador y `was_traded == True` a las dos victimas (test en `tests/test_metrics.py`).
- [ ] Dos bajas vengadoras distintas sobre dos asesinos distintos siguen sumando 2 (test: el caso que hoy funciona no cambia).
- [ ] En cualquier ronda, `trade_kills <= kills` para cada jugador: test que arma una ronda con un doble y un triple vengados y lo afirma para todos.
- [ ] `manage.py recompute` corrige las filas ya importadas: una ronda guardada con `trade_kills = 2` para esa secuencia queda en 1 despues del recompute, y el resumen lo cuenta como cambio (test en `tests/test_recompute.py`).
- [ ] Los tests existentes de `TradeTests` y de `test_recompute.py` siguen en verde sin cambios.

## Fuera de alcance

- Cambiar la ventana de trade, la regla de quien cuenta como vengador o el peso del trade kill en el rating.
- Que una muerte vengada cuente distinto segun cuantos compañeros cayeron antes.
- `seed_demo`: no pasa por `annotate_trades` (escribe `trade_kills` a mano), asi que los numeros del e2e no se mueven.

## Diseno

(Arquitecto) Archivos exactos y por que esos; tests nuevos con nombre en
espanol; orden de implementacion; que puede romperse (migracion, recompute,
build, instalador); verificacion manual; fila de `docs/metricas.md` si hay
numero nuevo. Si pisa archivos de otra rama abierta o agrega migracion
mientras otra ya la agrega: "Implementar despues de que #NN se mergee".

Notas del PO para el diseno: el helper `_round` de `tests/test_metrics.py` arma
2 contra 2, asi que el caso necesita un tercer atacante. Sin migracion: la
columna `trade_kills` ya existe; el arreglo llega a las bases viejas con
`manage.py recompute` (hay que decirlo en "Verificar en el PC" y, si
corresponde, en el README).

## Implementacion

(Dev) Que quedo, que no, desvios del diseno y por que.

## Revision <fecha> sobre <sha>

(Revisor) Formato de `revision.md`. Veredicto al final.

## QA <fecha> sobre <sha>

(QA) Un comando y un resultado por criterio de aceptacion.

## Verificar en el PC

(QA, solo si toca migraciones, recompute, parser, Electron o `.ps1`.)

## Pendiente

(Solo si alguien dejo trabajo a medias: que falta y donde se trabo.)

## Para el humano

(Cualquiera, solo si hace falta una decision suya.)
