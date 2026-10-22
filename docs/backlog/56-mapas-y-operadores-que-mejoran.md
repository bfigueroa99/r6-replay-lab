# 56. Mapas y operadores que mejoran y empeoran

estado: revisado
candado: -
rama: claude/equipo-dev/56-mapas-y-operadores-que-mejoran
tipo: funcionalidad
epica: progreso
area: fullstack
prioridad: 3
fuente: ALCANCE.md E5 y E10
archivos: backend/replays/analytics/aggregates.py, backend/replays/views.py, backend/tests/test_compare.py, frontend/src/pages/Trends.jsx, frontend/e2e/humo.spec.js, docs/metricas.md
turnos: po 20261019T0004Z, arquitecto 20261022T0804Z, dev 20261022T1204Z, revisor 20261022T1604Z

## PR

(La escribe el Release manager al final.)

## Que gana quien usa la app

Tendencias compara hoy el total de tus ultimas N partidas contra las N
anteriores, pero no dice donde cambio. Con el mismo corte por mapa y por
operador ves en que mapa estas mejorando, cual se te cae y si el operador que
practicas rinde, con la banda de ruido que ya separa lo real de lo casual.

## Criterios de aceptacion

- [ ] `compare_periods` (o una funcion hermana en `aggregates.py`) devuelve,
  ademas del total, `by_map` y `by_operator`: por cada mapa (`map_slug`) y por
  cada par operador + lado con al menos `min_rounds` rondas en **los dos**
  periodos, rondas de cada periodo, winrate de ronda y rating actual y previo,
  delta, `noise` (el mismo `_ruido` del total) y `verdict`
  (`mejor`/`peor`/`ruido`). Lo que no llega a la muestra en un periodo no
  aparece. Test de Django con dos periodos sinteticos: un mapa que sube 30
  puntos con muestra sale `mejor`, uno sin muestra en el periodo previo no
  sale.
- [ ] Las filas vienen ordenadas por `delta` de winrate, de mayor a menor.
  Test.
- [ ] Respeta `by=matches|days` y `n` como el total, y los filtros de la barra
  que no son de tiempo. Test con `?by=days&n=30` y con `?side=defense`.
- [ ] `Trends.jsx` muestra dos tablas debajo de la comparacion actual ("Mapas"
  y "Operadores"), con el delta coloreado solo si el veredicto no es
  `ruido`; sin filas, "Sin muestra en los dos periodos". Entra al e2e sobre
  `seed_demo` (la pagina renderiza las dos tablas sin errores de consola).
- [ ] Fila en `docs/metricas.md` (seccion de comparacion de periodos) con la
  muestra minima y que significa el veredicto por fila.

## Fuera de alcance

- Sitios, compañeros u otras dimensiones: solo mapa y operador.
- Graficos de evolucion por mapa en el tiempo.
- Cambiar la muestra minima o la formula del ruido del total.

## Diseno

Una sola forma obvia: el corte reusa `group_by` sobre los dos querysets que
`compare_periods` ya arma. Sin migracion, sin endpoint nuevo, sin modulo JS
nuevo (`Delta` de `Trends.jsx` ya pinta delta + veredicto).

**Backend, `backend/replays/analytics/aggregates.py`** (seccion de
`compare_periods`):

1. Extraer de `compare_periods` el calculo del veredicto a
   `_veredicto(delta, ruido, direccion) -> str | None` (mismo codigo, sin
   cambiar el comportamiento del total; `test_compare.py` actual tiene que
   seguir verde sin tocarlo).
2. Constante nueva `COMPARE_MIN_ROUNDS_FILA = 10` con comentario: es la
   muestra minima **por fila y por periodo**; no se usa `COMPARE_MIN_ROUNDS`
   (20) porque con 10 partidas por periodo un operador rara vez junta 20
   rondas de un lado y la tabla quedaria siempre vacia. Desvio deliberado del
   criterio 1 ("al menos `min_rounds`"): `min_rounds` sigue siendo la del
   total, como dice Fuera de alcance. Calibrar con la base real (ver abajo).
3. `_corte_por_periodo(actual, previo, baseline, campos, labels, min_rows)
   -> list[dict]`: `group_by(actual, *campos, labels=labels, baseline=baseline)`
   y lo mismo con `previo`, indexados por la tupla de `labels`; solo las
   claves presentes en los dos con `rounds >= min_rows` en cada uno. Por fila:
   las claves de `labels`, `current_rounds`, `previous_rounds`,
   `current_winrate`, `previous_winrate`, `delta` (winrate, `round(.., 1)`),
   `noise` (`_ruido(cur_wr, cur_rounds, prev_wr, prev_rounds)`), `verdict`
   (`_veredicto(delta, noise, "up")`), `current_rating`, `previous_rating`,
   `rating_delta` (None si falta alguno), y `suffix: "%"`,
   `direction: "up"` para que `Delta` del frontend la pinte igual que una
   metrica del total. Orden: `delta` de mayor a menor, `None` al final,
   desempate por la clave (estable para el e2e).
4. En `compare_periods`: firma nueva `min_rows: int = COMPARE_MIN_ROUNDS_FILA`;
   en el dict de salida `min_rows`, `by_map` (campos
   `round__match__map_slug`, `round__match__map_name`, labels `slug`, `map`)
   y `by_operator` (sobre `actual.exclude(operator="")` y lo mismo en previo;
   campos `operator`, `side`, labels `operator`, `side`).
5. `views.compare` no cambia salvo pasar `min_rows` leido con
   `_int_param(request, "min_rows", agg.COMPARE_MIN_ROUNDS_FILA, minimum=1,
   maximum=10_000)`. Es una linea en `backend/replays/views.py`: si el Dev
   prefiere no tocar `views.py` (lo toca la rama de la 60), el default
   alcanza y el test usa el argumento de la funcion.

**Tests, `backend/tests/test_compare.py`** (agregar, usando las factories del
archivo):
- `test_un_mapa_que_sube_con_muestra_sale_mejor`: periodo previo 12 rondas en
  un mapa con 3 ganadas, actual 12 con 10 ganadas (por partidas, n=1 con una
  partida por periodo, o `by=days`): fila `mejor`, delta positivo.
- `test_un_mapa_sin_muestra_en_el_periodo_previo_no_sale`.
- `test_las_filas_vienen_ordenadas_por_delta`.
- `test_el_operador_se_parte_por_lado`: mismo operador en ataque y defensa
  son dos filas.
- `test_respeta_by_days_y_el_filtro_de_lado` via `Client` a
  `/api/compare/?by=days&n=30&side=Defense` (solo filas `side=Defense` en
  `by_operator`).
- `test_base_vacia_devuelve_cortes_vacios`.

**Frontend, `frontend/src/pages/Trends.jsx`**: dentro del Panel "Progreso",
debajo del `DataTable` actual, dos subtitulos `<h3>` "Mapas" y "Operadores",
cada uno con un `DataTable` (`csvName` `progreso-mapas` y
`progreso-operadores`): columnas nombre (operador con `SideChip` para el
lado, si se importa de `ui.jsx`), rondas antes/ahora, winrate antes/ahora con
`fmt(.., 0, '%')`, Cambio con `<Delta metric={row} />` (ya colorea solo si
`verdict` no es `ruido`), Ruido como la tabla de arriba, rating antes/ahora.
`rowKey` = slug o `operator + side`; `initialSort` por `delta` desc. Sin
filas: `<p className="dim">Sin muestra en los dos periodos ({min_rows}+
rondas en cada uno).</p>`.

**e2e, `frontend/e2e/humo.spec.js`**: `test('Tendencias muestra mapas y
operadores que cambian')`. Medido sobre `seed_demo` con la ventana por
defecto (10 partidas): el periodo actual es todo Bank y el previo Border y
Club House, asi que "Mapas" muestra el texto vacio; cada operador tiene 10 a
14 rondas en los dos periodos, asi que "Operadores" tiene **6 filas**. El
test afirma las dos cosas y la consola limpia.

**`docs/metricas.md`**, seccion `## Progreso`: fila "Cambio por mapa y
operador" (muestra minima `COMPARE_MIN_ROUNDS_FILA` por fila en cada periodo,
banda = la misma formula sobre las rondas de esa fila, veredicto por fila,
rating por fila sin banda).

**Orden:** helper `_veredicto` -> `_corte_por_periodo` + tests -> vista ->
Trends.jsx -> e2e -> metricas.md -> `check.sh`.

**Que puede romperse:** el JSON de `/api/compare/` crece (las claves nuevas
no pisan ninguna); el refactor del veredicto (cubierto por los tests
existentes de `test_compare.py`).

**Verificacion manual:** `/tendencias` con la base real, ventana 10 y 30
partidas: cuantas filas salen. Si con 10 partidas casi ningun operador llega
a 10 rondas por lado, el umbral pide bajarlo a 8; anotarlo en Implementacion.

**Archivos ocupados:** `aggregates.py`, `views.py`, `metricas.md` y
`humo.spec.js` tambien los toca la rama de la 60 (PR #48, esperando al
humano). Son zonas distintas de cada archivo: se puede implementar ya; si el
merge de la 60 llega antes, `git merge origin/main` (P3).

## Implementacion

Dev 20261022T1204Z.

Que quedo, siguiendo el diseno:

- `aggregates.py`: `_veredicto` extraido de `compare_periods` (mismas reglas;
  los tests viejos de `test_compare.py` siguen verdes sin tocarlos, y
  `test_el_veredicto_del_total_no_cambia` fija los casos borde),
  `COMPARE_MIN_ROUNDS_FILA = 10`, `_corte_por_periodo` y las claves nuevas
  `min_rows`, `by_map` (`slug`, `map`) y `by_operator` (`operator`, `side`,
  sin las rondas con operador vacio). Orden: delta desc, `None` al final,
  desempate por clave.
- `views.compare`: acepta `min_rows` (1 a 10000), default la constante.
- `Trends.jsx`: `TablaDeCambio` con dos `<h3>` "Mapas" y "Operadores" dentro
  del panel Progreso; columnas rondas, ganadas, Cambio (`Delta`), Ruido y
  rating antes/ahora; operador con `SideChip`; CSV `progreso-mapas` y
  `progreso-operadores`; texto vacio con la muestra minima.
- e2e `Tendencias muestra mapas y operadores que cambian`: mapas vacios y 6
  filas de operadores, consola limpia (medido sobre `seed_demo` con la
  ventana de 10 partidas: coincide con el diseno).
- `docs/metricas.md`: fila "Cambio por mapa y operador" en `## Progreso`.

Tests por criterio:
1. `test_un_mapa_que_sube_con_muestra_sale_mejor`,
   `test_un_mapa_sin_muestra_en_el_periodo_previo_no_sale`,
   `test_un_mapa_que_no_jugaste_antes_no_sale`,
   `test_el_operador_se_parte_por_lado`, `test_trae_rating_de_cada_periodo`,
   `test_las_rondas_sin_operador_no_forman_fila`,
   `test_base_vacia_devuelve_cortes_vacios`.
2. `test_las_filas_vienen_ordenadas_por_delta` (tambien cubre `peor` y `ruido`).
3. `CortesApiTests.test_respeta_by_days_y_el_filtro_de_lado`,
   `test_sin_filtro_de_lado_salen_los_dos`,
   `test_la_muestra_minima_por_fila_se_puede_pedir`.
4. e2e `Tendencias muestra mapas y operadores que cambian`.
5. Fila en `docs/metricas.md`.

Desvios: ninguno de fondo. Se agrego `min_rows` a la vista (el diseno lo
dejaba opcional).

Sin hacer: la calibracion con la base real (ventana 10 y 30 partidas) que
pide la verificacion manual: la nube no tiene los replays del humano.
"Verificar en el PC": abrir `/tendencias` y contar filas; si con 10
partidas casi ningun operador llega a 10 rondas por lado, bajar
`COMPARE_MIN_ROUNDS_FILA` a 8.

Revision ciega previa (subagente con `revision.md`): sin bloqueantes. Dos
menores que quedan como estan: en `seed_demo` todos los operadores dan delta
0, asi que el e2e no ve un chip mejor/peor (cubierto por los tests de
Django; cambiar el seed moveria numeros de otras pruebas), y `Delta` muestra
dos decimales con |delta| < 1 (codigo previo, cosmetico).

check.sh: `Todo en verde.` (733 tests backend, 115 frontend, build ok, 45 e2e).

## Revision 2026-10-22 sobre 6a5644a

Revisor 20261022T1604Z. main ya estaba fusionado en la rama (sin cambios);
`check.sh` en `Todo en verde.` (733 tests backend, 115 frontend, build ok,
45 e2e).

Revision ciega (subagente con `revision.md` sobre el diff sin
`docs/backlog`): sin hallazgos, veredicto aprobar. Confirmado por el lider:

- Los numeros de los asserts nuevos salen a mano: Club House 25 % -> 83,3 %
  (+58,3); Bank -33,3 con banda ~18 (`peor`); Oregon +8,3 con banda ~20
  (`ruido`); Villa +41,7 (`mejor`); con `min_rows=13` los operadores (12
  rondas por periodo) quedan afuera y el mapa (24) queda.
- El e2e cuadra con `seed_demo` (base temporal en el scratchpad): ventana de
  10 partidas, `by_map` vacio y 6 filas en `by_operator`, Ash en ataque
  entre ellas.
- `_veredicto` conserva las reglas del total (los tests viejos de
  `test_compare.py` siguen verdes sin tocarlos).
- El corte por mapa agrupa por `map_slug` + `map_name`, igual que el
  `by_map` existente; `retag` cambia los dos juntos, asi que no se parte una
  fila.

Ficha: cada criterio tiene test con nombre (lista de Implementacion); el diff
no sale de `archivos:`; fila nueva en `docs/metricas.md`; sin tildes en
identificadores, UI con tildes; sin `print` ni `console.log`; sin
dependencias ni escrituras nuevas (`min_rows` es un parametro GET).

Observacion, no hallazgo: en `seed_demo` todos los operadores dan delta 0,
asi que el e2e no pinta un chip mejor/peor ni una tabla de mapas con filas;
los colores los cubren solo los tests de Django. Ya lo anoto el Dev.

Veredicto: aprobar -> `revisado`.
