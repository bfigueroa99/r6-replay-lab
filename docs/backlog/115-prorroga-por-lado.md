# 115. Prorroga por lado

estado: implementado
candado: -
rama: claude/equipo-dev/115-prorroga-por-lado
tipo: funcionalidad
epica: lado-y-marcador
area: fullstack
prioridad: 3
fuente: ALCANCE.md B18
archivos: backend/replays/analytics/aggregates.py (by_overtime_side, PRORROGA_LADOS), backend/replays/views.py (trends), backend/tests/test_prorroga_por_lado.py, frontend/src/prorrogaPorLado.js, frontend/src/prorrogaPorLado.test.js, frontend/src/pages/Trends.jsx, frontend/e2e/humo.spec.js, docs/metricas.md
turnos: po 20261112T1603Z-cor3JBP, arquitecto 20261112T2004Z-cbaTGDt, dev 20261113T1203Z-cWfR3tT

## PR

## Que gana quien usa la app

En Tendencias, la fila de prorroga se parte en ataque y defensa: winrate de
ronda y rating en las rondas de prorroga segun el lado que te toco. Responde
si en la prorroga defiendes mejor de lo que atacas, que la fila unica de hoy
no separa.

## Criterios de aceptacion

- [ ] El corte por mitad (`by_half` o una clave nueva de la misma respuesta)
      devuelve, para `overtime`, una fila por lado (`Attack`, `Defense`)
      con `rounds`, `winrate` y `rating` de las rondas con
      `Round.overtime_number > 0`. Test con una partida armada: dos rondas
      de prorroga en ataque ganadas y una en defensa perdida dan 100 % y 0 %.
- [ ] Las filas de primera y segunda mitad no cambian (test que compara la
      respuesta de esas filas antes y despues).
- [ ] Los filtros globales aplican; con el filtro de lado solo sale la fila
      de ese lado. Test.
- [ ] Se ve en Tendencias junto a la fila de prorroga actual, con el aviso
      de muestra minima de los cortes de Tendencias (30 rondas: se avisa,
      no se oculta); sin prorrogas, un texto y no un error. El e2e de humo
      pasa por Tendencias con la consola limpia.
- [ ] `docs/metricas.md` actualiza la fila de mitades y prorroga con el
      corte por lado.

## Fuera de alcance

- Winrate de partida de las que fueron a prorroga segun el lado (otro tramo).
- Lado inicial de la prorroga o quien la elige: el `.rec` no lo dice.
- Prorroga en modos sin regla de partida (A9).

## Diseno

(arquitecto 20261112T2004Z-cbaTGDt) Filtros duros: pasa. Usa `Round.overtime_number`
y `Round.my_side`, que el `.rec` entrega; sin red, sin dependencias, sin
POST, sin migracion. Una forma obvia (~150 lineas): sin arena ni consenso.

**Forma.** Clave nueva `by_overtime_side` en la respuesta de
`/api/trends/` (la vista que hoy arma `by_half`, `views.py` ~linea 281).
`by_half` **no se toca**: sus tres filas siguen identicas (criterio 2).

**Backend, `backend/replays/analytics/aggregates.py`**, despues de `by_half`:
- `PRORROGA_LADOS = ("Attack", "Defense")`.
- `by_overtime_side(**filters) -> list[dict]`:
  `qs = base_queryset(**filters).filter(round__overtime_number__gt=0)`;
  lados = `(filters["side"],)` si `filters.get("side")` esta en
  `PRORROGA_LADOS`, si no los dos; `return _filas_por_tramo("side", {lado:
  qs.filter(round__my_side=lado) for lado in lados})`. Mismas columnas que
  las filas de mitad (`totals()`: rondas, ganadas, rating, KPR, aperturas):
  la tabla del frontend reusa `COLUMNAS_POR_TRAMO`.
  `round__my_side` y no `side` de `RoundPlayer`: es el mismo campo que usa
  `by_half`. Con `?side=` el filtro ya recorta `qs` por `side`; la otra
  fila no se devuelve (saldria en 0).
- Sin prorrogas: dos filas con `rounds: 0` (como hoy la fila `overtime`).

**`views.py`**: `"by_overtime_side": agg.by_overtime_side(**filters),`
justo despues de `"by_half"`.

**Frontend.**
- `frontend/src/prorrogaPorLado.js` (logica pura):
  `filasProrrogaPorLado(rows)`: `[]` si no hay filas o todas tienen
  `rounds === 0`; si no, cada fila con `orden`, `tramo` (`Prórroga en
  ataque` / `Prórroga en defensa`) y el resto de la fila tal cual.
- `frontend/src/prorrogaPorLado.test.js` (vitest): vacio y todo en 0 dan
  `[]`; con una sola fila (filtro de lado) sale una; textos y orden.
- `frontend/src/pages/Trends.jsx`, dentro del panel "Por mitad de la
  partida", despues de la tabla de mitades y antes de "Primera ronda de cada
  lado": `<h3>Prórroga por lado</h3>` y `DataTable` con
  `COLUMNAS_POR_TRAMO`, `initialSort={{ key: 'orden', dir: 'asc' }}`,
  `rowKey={(row) => row.side}`, `csvName="prorroga-por-lado"`; debajo el
  mismo aviso que "Primera ronda de cada lado" con
  `filasConPocaMuestra(...)` y `MUESTRA_CORTE` (30 rondas: se avisa, no se
  oculta). Sin filas: `<p className="note">Sin rondas de prórroga con estos
  filtros.</p>` (el seed no tiene prorroga: es lo que ve el e2e).

**Tests backend, `backend/tests/test_prorroga_por_lado.py`** (con
`factories`; `make_round(..., overtime_number=1)` ya existe):
- `test_parte_la_prorroga_por_lado`: partida con dos rondas de prorroga en
  ataque ganadas y una en defensa perdida -> Attack 2 rondas 100 %, Defense
  1 ronda 0 %.
- `test_las_rondas_sin_prorroga_no_entran`.
- `test_by_half_no_cambia`: con la misma partida, `by_half` da sus tres
  filas con las rondas esperadas armadas a mano (first, second y overtime
  con 3 rondas): falla si alguien cambia la fila `overtime` al partirla.
- `test_con_filtro_de_lado_sale_solo_ese`: `/api/trends/?side=Defense` ->
  `by_overtime_side` con una fila `Defense`.
- `test_el_filtro_de_mapa_aplica`.
- `test_sin_prorroga_las_filas_salen_en_cero`.

**e2e, `frontend/e2e/humo.spec.js`**: test `Tendencias muestra la prórroga
por lado`: el seed no tiene prorroga (sus partidas son 4-3 sin
`overtime_number`), asi que el panel "Por mitad de la partida" muestra el
`h3` "Prórroga por lado" y la nota "Sin rondas de prórroga con estos
filtros."; consola limpia. Las filas con datos las cubren vitest y los tests
backend.

**`docs/metricas.md`**, `## Mitades y prorroga`: la fila **Prorroga** suma
"Partida por lado (*Prórroga en ataque* / *en defensa*): el lado de tu
ronda de prorroga (`Round.my_side`); los filtros globales aplican y con el
de lado sale solo esa fila. Aviso de muestra con 30 rondas, como los cortes
de Tendencias."

**Orden.** aggregates + tests, vista, `prorrogaPorLado.js` + vitest,
`Trends.jsx`, e2e, metricas, `npm run build`.

**Que puede romperse.** `_filas_por_tramo` calcula el baseline una vez; dos
filas mas son dos `totals()` mas por request de Tendencias, barato (solo
rondas de prorroga). Ningun test existente lee la lista de claves de
`/api/trends/` entera (verificar con `grep -rn by_half backend/tests`; si
alguno compara claves, sumarle `by_overtime_side`).

**Archivos ocupados.** `aggregates.py`, `views.py` y `humo.spec.js` los
tocan la 107 y la 113 en otras funciones y otros tests; `Trends.jsx` no lo
toca ninguna rama abierta. No se frena.

**Verificacion manual.** Base con alguna partida con prorroga (real):
Tendencias, "Prórroga por lado" con dos filas que suman la fila Prórroga de
arriba; `?side=Attack` una fila.

Skills: no aplica (tabla en un panel existente con las columnas de siempre).
OMC: plan=— · revisión=— · verificación=—

## Implementacion

(dev 20261113T1203Z-cWfR3tT) Diseno completo, sin desvios de forma:

- `aggregates.py`: `PRORROGA_LADOS` y `by_overtime_side(**filters)` despues
  de `by_half` (que no cambia), con `_filas_por_tramo("side", ...)` sobre
  `round__my_side`; con `?side=` sale solo esa fila. `views.trends` suma
  `by_overtime_side`.
- `prorrogaPorLado.js`: `filasProrrogaPorLado` (`[]` sin filas o todo en 0;
  `tramo` "Prórroga en ataque" / "en defensa" y `orden`).
- `Trends.jsx`: `h3` "Prórroga por lado" despues de la tabla de mitades,
  `DataTable` con `COLUMNAS_POR_TRAMO`, CSV `prorroga-por-lado`, aviso de
  `MUESTRA_CORTE`; sin filas, la nota "Sin rondas de prórroga con estos filtros."
- `metricas.md`: la fila Prorroga suma el corte por lado, y (revision ciega,
  LOW) que las rondas de prorroga sin lado no entran en ninguna de las dos.

Tests, vistos en rojo antes del codigo: backend `test_prorroga_por_lado.py`
(7; 6 caian con `AttributeError`, el de `by_half` pasaba como debe), vitest
`prorrogaPorLado.test.js` (4; sin modulo no corrian). e2e `Tendencias
muestra la prórroga por lado` (API con las dos filas en 0, `h3`, nota, sin
filas en la tabla, consola limpia). Criterios -> tests: filas por lado con
100 % y 0 % (`test_parte_la_prorroga_por_lado`); mitades intactas
(`test_by_half_no_cambia`, mas `test_mitades.py` sin tocar); filtros
(`test_con_filtro_de_lado_sale_solo_ese`, `test_el_filtro_de_mapa_aplica`);
Tendencias con aviso y nota (vitest + e2e); fila en `metricas.md`.

verificar.sh: VERDE 21b599c79 (1172 backend, 338 vitest, 96 e2e; el commit
siguiente solo toca esta ficha).

Skills: no aplica.
Skills del repo: modern-web-guidance (leida; ninguna guia aplica: tabla con `DataTable` y `h3` existentes, sin CSS ni componente nuevo), ux-copy no leida (los dos textos nuevos son los del diseno y siguen a "Primera ronda de cada lado").
OMC: plan=— · revisión=2 hallazgos (1 arreglado, 1 LOW de comentario sin cambio; 0 CRITICAL/HIGH) · verificación=—

## Revision

## QA

## Para el humano

(nada)
