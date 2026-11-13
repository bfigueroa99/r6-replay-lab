# 127. Partidas que van a prorroga: cuantas ganas

estado: implementado
candado: -
rama: claude/equipo-dev/127-partidas-que-van-a-prorroga
tipo: funcionalidad
epica: lado-y-marcador
area: fullstack
prioridad: 3
fuente: ALCANCE.md B22 (salio del Fuera de alcance de la 115)
archivos: backend/replays/analytics/aggregates.py, backend/replays/views.py, backend/tests/test_prorroga_por_lado.py, frontend/src/prorrogaPorLado.js, frontend/src/prorrogaPorLado.test.js, frontend/src/pages/Trends.jsx, frontend/e2e/humo.spec.js, docs/metricas.md
turnos: po 20261113T1858Z-cxdASk3, arquitecto 20261113T2157Z-cG2vDSe, dev 20261113T2252Z-cQac5RQ

## PR

## Que gana quien usa la app

En Tendencias, junto a la prorroga por lado de la 115 (winrate de ronda), el
winrate de partida de las que llegaron a prorroga, en la misma tabla,, partido por el lado con el
que la arrancaste: lo que se juega en la prorroga es la partida, no una ronda.
Responde "cuando llego a prorroga en defensa, ¿la gano?".

## Criterios de aceptacion

- [ ] Un agregado nuevo en `replays/analytics/aggregates.py` devuelve, por
      lado de tu primera ronda de prorroga (`Round.overtime_number` mas bajo
      `> 0` de la partida, su `Round.my_side`), `matches`, `wins`,
      `decided` y `winrate` (claves de `by_start_side`) (sobre las partidas con `Match.won` no nulo).
      Test con tres partidas a prorroga (dos arrancadas en defensa, una
      ganada; una en ataque, ganada) -> defensa 2 partidas 50 %, ataque 1
      partida 100 %.
- [ ] Una partida sin prorroga no entra; una con `won` nulo cuenta en
      `matches` y no en `decided` ni en el winrate. Test.
- [ ] Los filtros globales de partida (mapa, tipo, modo, fechas) aplican; con
      `?side=` solo sale la fila de ese lado (como `by_overtime_side`). Test.
- [ ] Se ve en Tendencias como columnas nuevas (Partidas, % ganadas) de la
      tabla de prorroga por lado de la 115, sin tarjeta nueva (la pagina esta
      en `saturadas` de `ROTACION`), con el aviso de muestra de la pagina (se
      avisa, no se oculta); un lado sin partidas a prorroga muestra `—`. e2e
      de humo pasa por ahi con la consola limpia.
- [ ] Fila nueva en `docs/metricas.md` ("Partidas a prorroga por lado").

## Fuera de alcance

- Winrate de ronda en prorroga (ya lo da la 115).
- Partir por cuantas prorrogas hubo o por el marcador al llegar.
- Sumarlo al Coach como señal.

## Diseno

Una sola forma obvia: es `by_start_side` (lado inicial, partidas y winrate de
partida) leyendo la primera ronda de prorroga en vez de la primera sin
prorroga, pegado a la tabla de la 115. Sin arena ni consenso (chica, sin
migracion, sin `recompute`, sin parser). No duplica "Margen final" (tramo
`Prorroga`, todas las partidas a prorroga juntas): esto las parte por lado.

**Backend** (`backend/replays/analytics/aggregates.py`, justo despues de
`by_overtime_side`):

- `_lado_de_prorroga(match_ref: str) -> Subquery`: `Round.objects.filter(
  match_id=OuterRef(match_ref), overtime_number__gt=0).order_by(
  "overtime_number", "number").values("my_side")[:1]`. Docstring: se lee de
  la partida entera, como `_lado_inicial`; con `?side=` el filtro limita las
  rondas, no cambia con que lado arrancaste la prorroga. Lado vacio: la
  partida no cae en ninguna fila (igual que `_lado_inicial`).
- `by_overtime_start_side(**filters) -> list[dict]`, copia de la forma de
  `by_start_side`: `ids = base_queryset(**filters).filter(
  round__overtime_number__gt=0).values_list("round__match_id",
  flat=True).distinct()`; `partidas = Match.objects.filter(id__in=ids)
  .annotate(lado=_lado_de_prorroga("id"))`; filas en el orden de
  `PRORROGA_LADOS`, o solo `(filters["side"],)` si viene y es un lado (la
  misma linea que `by_overtime_side`). Cada fila: `side`, `matches`,
  `decided` (`won` no nulo), `wins`, `winrate` (`_pct(wins, decided)`, `None`
  sin decididas). Con `?side=Attack` los `ids` ya son solo partidas con alguna
  ronda de prorroga en ataque, y toda partida cuya primera ronda de prorroga
  fue en ataque esta ahi: la fila no pierde partidas.
- Si cuando se implemente la 79 ya esta en dev, `Match.objects.filter(id__in=ids)`
  es igual de valido (asi quedo `by_start_side` en esa rama: los `ids` ya
  salen de `base_queryset`, que excluye); no hace falta `partidas_contables`.

**API** (`backend/replays/views.py`, vista `trends`): clave nueva
`"by_overtime_start_side": agg.by_overtime_start_side(**filters)`, debajo de
`by_overtime_side`. Sin ruta nueva.

**Frontend:**

- `frontend/src/prorrogaPorLado.js`: `filasProrrogaPorLado(rows, partidas)`
  (segundo argumento opcional; los llamados viejos siguen andando). Por cada
  fila de ronda busca la de `partidas` con el mismo `side` y agrega
  `matches` (0 si no hay) y `match_winrate` (`winrate` de la fila de
  partidas, `null` si no hay). La regla de "todo en cero es `[]`" sigue
  mirando solo `rounds`. Constante `PARTIDAS_CORTE = 10` (la de "Margen
  final") y `conPocasPartidas(filas)`: `true` si alguna fila tiene
  `0 < matches < PARTIDAS_CORTE`.
- `frontend/src/pages/Trends.jsx`: `filasProrrogaPorLado(data.by_overtime_side,
  data.by_overtime_start_side)`. La tabla "Prórroga por lado" pasa a usar
  `COLUMNAS_PRORROGA_POR_LADO = [...COLUMNAS_POR_TRAMO, { key: 'matches',
  label: 'Partidas', sortable: false, help: 'Partidas que llegaron a prórroga y la arrancaste de este lado (el de tu primera ronda de prórroga).' },
  { key: 'match_winrate', label: 'Partidas ganadas', digits: 0, suffix: '%', sortable: false, help: 'Sobre las que tienen resultado; las incompletas cuentan en Partidas pero no acá.' }]`
  (no tocar `COLUMNAS_POR_TRAMO`: la usan las otras tablas). `null` ya sale
  `—` (`components/ui.jsx`). Debajo del aviso de rondas que ya existe, otro
  `<p className="note">` si `conPocasPartidas(prorrogaPorLado)`: "Ojo: algún
  lado tiene menos de {PARTIDAS_CORTE} partidas a prórroga; el porcentaje de
  partidas puede ser varianza." El CSV (`csvName="prorroga-por-lado"`) lleva
  las columnas nuevas solo por estar en `columns`.

**Tests** (Django para el numero, vitest para la union de filas, e2e solo de
humo: `seed_demo` no tiene prorroga):

- `backend/tests/test_prorroga_por_lado.py`, clase nueva
  `PartidasAProrrogaPorLadoTests`:
  `test_cuenta_partidas_y_ganadas_por_el_lado_de_la_primera_ronda_de_prorroga`
  (el caso del criterio: defensa 2 partidas 50 %, ataque 1 partida 100 %),
  `test_el_lado_es_el_de_la_primera_ronda_de_prorroga_y_no_el_de_la_mayoria`
  (prorroga D, A, A -> cuenta en defensa),
  `test_una_partida_sin_prorroga_no_entra`,
  `test_sin_resultado_cuenta_en_partidas_y_no_en_el_porcentaje`,
  `test_con_filtro_de_lado_sale_solo_esa_fila`,
  `test_el_filtro_de_mapa_aplica`,
  `test_sin_prorrogas_las_dos_filas_en_cero_y_winrate_nulo`, y
  `test_trends_devuelve_partidas_a_prorroga_por_lado` (clave en `/api/trends/`).
  Las partidas con prorroga se arman con `make_round(..., )` y
  `overtime_number` como ya hace la clase de la 115 en ese archivo.
- `frontend/src/prorrogaPorLado.test.js`: `une las partidas por lado`,
  `un lado sin partidas queda en 0 y sin porcentaje`, `sin el segundo
  argumento las filas no cambian` (los tests viejos siguen igual),
  `conPocasPartidas avisa entre 1 y 9 partidas y no con 0 ni con 10`.
- `frontend/e2e/humo.spec.js`, junto a la linea de `by_overtime_side`:
  `expect(datos.by_overtime_start_side.map((f) => [f.side, f.matches])).toEqual([['Attack', 0], ['Defense', 0]])`.

**`docs/metricas.md`**, tabla "Mitades y prorroga", fila nueva debajo de
"Prorroga": **Partidas a prórroga por lado** = partidas con al menos una
ronda de prorroga (`overtime_number > 0`) entre tus rondas filtradas,
partidas por el lado de tu primera ronda de prorroga (menor
`overtime_number`, despues menor `number`); Partidas ganadas = ganadas sobre
las que tienen resultado (`won` no nulo), las incompletas cuentan en
Partidas y no en el porcentaje; se lee de la partida entera (el filtro de lado
elige la fila, no cambia el lado de arranque); lado vacio no entra en
ninguna; aviso de varianza con menos de 10 partidas en un lado; no es el
winrate de ronda de las columnas de la izquierda, que parten cada ronda por
su propio lado.

**Orden:** agregado y tests Django -> clave en `trends` -> `prorrogaPorLado.js`
y vitest -> `Trends.jsx` -> e2e -> `metricas.md` -> `npm run build`.

**Que puede romperse:** la tabla mezcla dos unidades (ronda a la izquierda,
partida a la derecha): las ayudas de columna lo dicen, y la fila de
`metricas.md` tambien. `COLUMNAS_POR_TRAMO` es compartida: tocarla cambiaria
cuatro tablas. Archivos compartidos con ramas abiertas: `aggregates.py` y
`views.py` con la 133 y la 79, `humo.spec.js` con la 129, la 130 y la 133,
`metricas.md` con la 129, la 133 y la 79; son funciones y filas distintas, sin
migracion: no hace falta esperar a ninguna, el conflicto (si sale) es de
lineas vecinas.

**Verificacion manual:** `/tendencias` con una base con prorrogas: la tabla
"Prórroga por lado" tiene las columnas Partidas y Partidas ganadas; con el
filtro de lado en Defensa, una sola fila; con un mapa sin prorrogas, la nota
"Sin rondas de prórroga con estos filtros." como hoy. Umbral de 10 partidas:
el mismo de "Margen final", no requiere calibracion nueva.

Skills: no aplica (sin dominio nuevo: tabla existente, agregado con forma ya
usada).
Skills del repo: statistical-analysis (denominador `decided`, `n` a la vista
en Partidas, aviso con menos de 10 partidas como "Margen final"),
testing-strategy (numero en Django, union de filas en vitest, e2e de humo por
la API porque el seed no tiene prorroga); dataviz no aplica (tabla, sin
grafico).
OMC: plan=— · revisión=— · verificación=—

## Implementacion

(dev 20261113T2252Z-cQac5RQ) Diseno completo, sobre `origin/dev@39e22c0`:

- `aggregates.py`: `_lado_de_prorroga` (Subquery, primera ronda con `overtime_number > 0` por `overtime_number`, `number`) y `by_overtime_start_side`, con la forma de `by_start_side` y el `?side=` de `by_overtime_side`. `views.py`: clave `by_overtime_start_side` en `/api/trends/`.
- `prorrogaPorLado.js`: `filasProrrogaPorLado(rows, partidas)` agrega `matches` y `match_winrate` solo si viene el segundo argumento; `PARTIDAS_CORTE = 10` y `conPocasPartidas`.
- `Trends.jsx`: `COLUMNAS_PRORROGA_POR_LADO` (Partidas, Partidas ganadas, con las ayudas del diseno; `COLUMNAS_POR_TRAMO` sin tocar) y la nota de varianza de partidas debajo de la de rondas.
- e2e de humo: `by_overtime_start_side` en cero en el seed. `metricas.md`: fila "Partidas a prórroga por lado" debajo de "Prorroga".

Tests vistos en rojo antes del codigo: Django `PartidasAProrrogaPorLadoTests` (8 errores, funcion inexistente) y vitest (3 fallas). Criterios -> tests: 1 `test_cuenta_partidas_y_ganadas_por_el_lado_de_la_primera_ronda_de_prorroga` y `test_el_lado_es_el_de_la_primera_ronda_de_prorroga_y_no_el_de_la_mayoria`; 2 `test_una_partida_sin_prorroga_no_entra`, `test_sin_resultado_cuenta_en_partidas_y_no_en_el_porcentaje`; 3 `test_con_filtro_de_lado_sale_solo_esa_fila`, `test_el_filtro_de_mapa_aplica`; 4 vitest `une las partidas por lado`, `un lado sin partidas queda en 0 y sin porcentaje`, `conPocasPartidas avisa entre 1 y 9...` y e2e de humo (consola limpia); 5 la fila de `metricas.md`.

Revision ciega (`omc-code-reviewer`, eje de estandares): aprobar, 2 LOW. Arreglado 1: test nuevo `test_con_un_filtro_que_solo_deja_rondas_normales_la_partida_no_entra` (sin el `.filter(round__overtime_number__gt=0)` de los `ids` el test cae; mutante visto y restaurado). No arreglado: el e2e no renderiza las columnas nuevas porque `seed_demo` no tiene prorroga (el diseno ya lo preveia: e2e solo de humo por la API; cambiar el seed cambia los numeros de otras pruebas).

Desvios del diseno: ninguno, mas el test de arriba.

Skills: no aplica.
Skills del repo: statistical-analysis (denominador `decided`, n en Partidas, aviso con menos de 10), testing-strategy (numero en Django con mutante, union en vitest, e2e de humo por la API); modern-web-guidance no leida (sin CSS ni markup nuevo: columnas y una nota con los componentes existentes); ux-copy (ayudas y nota con tildes, como las vecinas).
OMC: plan=— · revisión=2 hallazgos LOW (1 arreglado) · verificación=—

## Revision

## QA

## Para el humano

(nada)
