# 98. Lado inicial por mapa

estado: implementado
candado: -
rama: claude/equipo-dev/98-lado-inicial-por-mapa
tipo: funcionalidad
epica: lado-y-marcador
area: fullstack
prioridad: 3
fuente: B17 de ALCANCE.md; [Siege.GG, win probability](https://siege.gg/news/how-analysts-estimate-win-probability-in-pro-siege-matches) (2026-04-27: "A team starting on defense may carry a higher early probability simply because of the map's structure"); investigador 2026-11-03
archivos: backend/replays/analytics/aggregates.py (by_start_side_map, MIN_PARTIDAS_LADO_INICIAL), backend/replays/views.py (trends), backend/tests/test_mitades.py, frontend/src/ladoInicialMapa.js, frontend/src/ladoInicialMapa.test.js, frontend/src/pages/Trends.jsx, frontend/e2e/humo.spec.js, docs/metricas.md
turnos: po 20261106T0319Z-cqz8j6p, arquitecto 20261106T0345Z-cgK76Zp, dev 20261106T0411Z-cHA9KBb

## PR

(La escribe el Release manager al final.)

## Que gana quien usa la app

Hoy Tendencias dice tu winrate de partida segun arrancaste atacando o
defendiendo, pero junta todos los mapas, y el lado que conviene cambia de un
mapa a otro. Con esto se ve, mapa por mapa, si te va mejor arrancando en
defensa o en ataque ("en Bank gano mas arrancando en defensa"), con la
muestra a la vista para no leer ruido.

## Criterios de aceptacion

- [ ] `GET /api/trends/` agrega `by_start_side_map`: una fila por mapa (la
      misma clave y etiqueta con version que `by_map`, fichas 70 y 74, asi
      "Consulate (Y10)" no se mezcla con la vieja) con, para `Attack` y
      `Defense` como lado inicial, `matches`, `decided`, `wins` y
      `winrate` (el mismo `_lado_inicial` y el mismo criterio de
      `by_start_side`: `Match.won = None` cuenta en `matches` y no en el %).
      Test: dos partidas en Bank arrancando en defensa (G, P), una en Bank en
      ataque (G) y una en Oregon en ataque (P) dan las cuatro celdas a mano.
- [ ] Cada fila trae la diferencia en puntos entre los dos lados y su banda
      de ruido (`_ruido` de `aggregates.py`, la de Tendencias); con menos
      partidas decididas que el minimo por lado (`MIN_PARTIDAS_MAPA`, 3, de
      la ficha 64, o la constante que fije el Arquitecto) el lado sale con
      `winrate: null` y la fila no da veredicto. Test con un lado de 2
      partidas.
- [ ] Los filtros de la barra se respetan como en `by_start_side` (mapa,
      tipo, fechas, sesion); el filtro de lado no parte la partida (el lado
      inicial se lee de `Round`, no de las rondas filtradas). Test con
      `side=Attack` que deja las mismas partidas.
- [ ] En Tendencias, al lado del panel "Lado inicial", una tabla "Lado
      inicial por mapa" (mapa, partidas y winrate arrancando en ataque, lo
      mismo en defensa, diferencia con banda de ruido), ordenada por partidas;
      sin filas, un texto de vacio y no un panel en blanco. El e2e de
      Tendencias la renderiza con `seed_demo` y la consola limpia.
- [ ] Fila nueva en `docs/metricas.md` con la definicion y la muestra minima.

## Fuera de alcance

- Lado inicial por sitio o por operador.
- Llevarlo al Coach como señal (puede ser una idea aparte en `ALCANCE.md`
  cuando haya datos reales que calibren el minimo).
- Cambiar `by_start_side` global: sigue igual.

## Diseno

Una sola forma obvia (es `by_start_side` con un `group by` por version de
mapa): sin arena ni plan por consenso. Skills: no aplica (tabla nueva con el
`DataTable` de siempre, sin grafico ni migracion).

### Backend: `aggregates.py`

Al lado de `by_start_side` (linea ~1653 en dev 9ca7562):

```python
#: Partidas decididas por lado inicial para que un mapa de veredicto.
MIN_PARTIDAS_LADO_INICIAL = MIN_PARTIDAS_MAPA  # 3, el minimo de mapa de la ficha 64
```

`by_start_side_map(**filters) -> list[dict]`:

1. Partidas igual que `by_start_side`: `ids` desde `base_queryset(**filters)`
   (el filtro de lado ya no parte la partida porque el lado se lee de `Round`
   con `_lado_inicial("id")`), `Match.objects.filter(id__in=ids)
   .annotate(lado=_lado_inicial("id")).values("map_slug", "map_id",
   "map_name", "lado", "won")`. Se agrupa en Python (son decenas o cientos de
   partidas). Partida con `lado` nulo (primera ronda sin lado) no entra, como
   en `by_start_side`.
2. Clave `(map_slug, map_id)`; etiqueta con `etiquetas_de_mapas(slugs)` (la
   misma que Mapas, fichas 70 y 74). Salida por fila:
   `{"slug", "map_id", "map", "matches", "attack": celda, "defense": celda,
   "delta", "margin", "verdict"}`, celda =
   `{"matches", "decided", "wins", "winrate"}`; `winrate` es
   `_pct(wins, decided)` solo si `decided >= MIN_PARTIDAS_LADO_INICIAL`, si
   no `None` (los conteos salen igual, para que la UI muestre "2 partidas").
3. `delta = _delta(attack.winrate, defense.winrate)` (ya existe en el
   modulo, linea ~2758: redondea a 1 decimal y da `None` si falta un lado).
4. Banda de ruido: **no** `_ruido` (Wald) como dice el criterio 2 de la
   ficha, sino `_margen_y_veredicto(delta, attack.wins, attack.decided,
   attack.wins + defense.wins, attack.decided + defense.decided,
   ("ataque", "defensa"))`. Motivo: con 3 a 5 partidas por celda un 100 % o
   un 0 % es lo normal, y Wald da varianza cero ahi y veredicto por azar
   (el mismo problema que documenta `_ruido_combinado`, ficha 80). La
   proporcion combinada de los dos lados es el test de dos muestras de
   siempre y no colapsa en los bordes. `margin` = 2 errores estandar
   (`POSICION_BANDAS`). Si un lado no llega al minimo: `delta`, `margin` y
   `verdict` en `None` (sin muestra no hay veredicto; "ruido" queda para "hay
   muestra y la diferencia no alcanza").
   `verdict` es `"ataque"` (te va mejor arrancando en ataque), `"defensa"` o
   `"ruido"`.
5. Orden: `matches` descendente, despues `map` ascendente (determinista).

`views.trends`: agregar `"by_start_side_map": agg.by_start_side_map(**filters)`
justo debajo de `by_start_side`. `by_start_side` no cambia.

### Frontend

- `frontend/src/ladoInicialMapa.js`, puro y sin React (como `margen.js`):
  `filasLadoInicialMapa(filas)` aplana cada fila para el `DataTable`
  (`attack_matches`, `attack_winrate`, `defense_matches`, `defense_winrate`,
  `delta`, `margin`, `verdict`) y `textoVeredicto(fila)` devuelve
  `'Mejor arrancando en ataque'`, `'Mejor arrancando en defensa'`,
  `'Dentro del ruido'` o `'Poca muestra'` (verdict `null`).
- `Trends.jsx`, en el mismo panel del "Lado inicial" (debajo de la tabla
  "Según el lado con que arrancas", linea ~669), un `<h3>` "Lado inicial por
  mapa" y un `DataTable` con columnas: Mapa (left), Partidas en ataque,
  Ganadas en ataque (%), Partidas en defensa, Ganadas en defensa (%),
  Diferencia (`delta`, 1 decimal, sufijo " pts", `help`: "Ataque menos
  defensa. Si no supera el margen de ruido, es varianza."), Margen (± pts) y
  Veredicto (`textoVeredicto`). `initialSort` por `matches` desc,
  `rowKey` = `${slug}-${map_id}`, `csvName="lado-inicial-por-mapa"`. Debajo,
  `<p className="note">` "Un lado necesita {MIN_PARTIDAS_LADO} partidas con
  resultado para tener porcentaje.", con `MIN_PARTIDAS_LADO = 3` exportada de
  `ladoInicialMapa.js` y un comentario que apunte a
  `MIN_PARTIDAS_LADO_INICIAL` (la respuesta es una lista y no trae el minimo). Sin filas: `<p className="note">`
  "Todavía no hay partidas con lado inicial conocido." y no la tabla.

### Tests

`backend/tests/test_mitades.py`, clase nueva `LadoInicialPorMapaTests` (usa
`make_match`/`make_round`/`make_round_player` de `factories.py`, como
`LadoInicialTests`):

- `test_lado_inicial_por_mapa_cuenta_cada_mapa_por_separado`: Bank defensa
  (G, P), Bank ataque (G), Oregon ataque (P) -> Bank: defensa 2 partidas 1
  ganada, ataque 1 y 1; Oregon: ataque 1 y 0, defensa 0. Con
  `MIN_PARTIDAS_LADO_INICIAL` parcheado a 1 para ver los porcentajes (50, 100,
  0); con el valor real, `winrate` `None` en todas.
- `test_un_lado_bajo_el_minimo_no_da_porcentaje_ni_veredicto`: 3 partidas
  decididas en ataque y 2 en defensa -> `defense.winrate` `None`, `delta`,
  `margin` y `verdict` `None`, `defense.matches == 2`.
- `test_partida_sin_resultado_cuenta_en_partidas_y_no_en_el_porcentaje`.
- `test_el_filtro_de_lado_no_cambia_el_lado_inicial_por_mapa`: `side=Attack`
  da las mismas filas que sin filtro.
- `test_las_versiones_de_un_mapa_van_en_filas_distintas`: dos `map_id` del
  mismo slug -> dos filas con etiquetas distintas.
- `test_una_diferencia_grande_con_muestra_da_veredicto`: 8 partidas en
  ataque todas ganadas y 8 en defensa todas perdidas -> `verdict ==
  "ataque"`; 4 y 4 con 3-1 contra 2-2 -> `"ruido"`.
- En `TendenciasApiTests`, `test_trends_sin_datos_devuelve_las_filas_vacias_sin_500`
  suma `by_start_side_map == []`.

`frontend/src/ladoInicialMapa.test.js`: aplanado de una fila completa, una
con un lado `null` y los cuatro textos de veredicto.

`frontend/e2e/humo.spec.js`, en `'Tendencias muestra la tabla por mitad'`:
`await expect(panel.getByText('Lado inicial por mapa')).toBeVisible()` y que
haya una celda `Bank`. Con `seed_demo` todas las partidas arrancan en ataque
(ronda 0 es `Attack`) y todas se ganan 4-3: las columnas de defensa salen en
0 y "—", y el veredicto "Poca muestra". No se toca `seed_demo`.

### Orden

1. `aggregates.py` + tests backend. 2. `views.py`. 3. `ladoInicialMapa.js` +
vitest. 4. `Trends.jsx` + `npm run build`. 5. e2e. 6. `metricas.md`.

### Que puede romperse

Nada persistente: sin migracion ni `recompute` (se calcula al consultar a
partir de columnas que ya existen, como `by_start_side`). `aggregates.py` y
`views.py` tambien los tocan las ramas abiertas 79 (PR #81) y 97: son
hunks en otras funciones, merge textual; si la 79 entra antes, sus partidas
excluidas ya salen por `base_queryset` y esto las respeta sin cambios. La
ficha 99 tambien toca `Trends.jsx` (tabla Sesiones, otra zona): la que
entre segunda mergea `dev`.

### Verificacion manual

`runserver` con `seed_demo`, Tendencias: la tabla aparece bajo "Según el
lado con que arrancas" con Club House, Border y Bank y defensa en "—".
`curl -s localhost:8000/api/trends/ | python -m json.tool | grep -A12 by_start_side_map`.

### `docs/metricas.md`

Fila nueva en la tabla de Tendencias, debajo de **Lado inicial** (linea
~83): **Lado inicial por mapa** — el mismo lado inicial, por version de
mapa. Ganadas = partidas ganadas sobre las que tienen resultado, solo con 3
o mas por lado. Diferencia = ataque menos defensa; margen = 2 errores
estandar con la proporcion de los dos lados juntos; dentro del margen es
ruido.

OMC: plan=— · revisión=— · verificación=—

## Implementacion

dev 20261106T0411Z-cHA9KBb. Quedo el diseno completo, en su orden:

- `aggregates.py`: `MIN_PARTIDAS_LADO_INICIAL = MIN_PARTIDAS_MAPA` (3),
  `_celda_lado_inicial` y `by_start_side_map`, agrupado en Python por
  `(map_slug, map_id)` con `etiquetas_de_mapas`. Banda con
  `_margen_y_veredicto` (proporcion combinada), no `_ruido`, como pide el
  diseno. Con un lado bajo el minimo, `delta`, `margin` y `verdict` en `None`.
  Orden `matches` desc y `map` asc. `by_start_side` no cambia.
- `views.trends`: `by_start_side_map` debajo de `by_start_side`.
- `frontend/src/ladoInicialMapa.js` (puro): `filasLadoInicialMapa`,
  `textoVeredicto`, `MIN_PARTIDAS_LADO = 3`. La fila aplanada trae tambien
  `veredicto` (el texto) para que el CSV lo baje igual que la tabla.
- `Trends.jsx`: `<h3>` "Lado inicial por mapa" y `DataTable` debajo de "Según
  el lado con que arrancas", con la nota del minimo; sin filas, "Todavía no
  hay partidas con lado inicial conocido.".
- `docs/metricas.md`: fila **Lado inicial por mapa** debajo de **Lado inicial**.

Tests (cada criterio con nombre):

- Criterio 1: `test_lado_inicial_por_mapa_cuenta_cada_mapa_por_separado`
  (minimo parcheado a 1 para ver 50/100/0 y con el real todo `None`).
- Criterio 2: `test_un_lado_bajo_el_minimo_no_da_porcentaje_ni_veredicto`,
  `test_una_diferencia_grande_con_muestra_da_veredicto` (8 y 8 -> "ataque"),
  `test_una_diferencia_chica_con_poca_muestra_es_ruido` (3-1 contra 2-2).
- `won=None`: `test_partida_sin_resultado_cuenta_en_partidas_y_no_en_el_porcentaje`.
- Criterio 3: `test_el_filtro_de_lado_no_cambia_el_lado_inicial_por_mapa` y
  `test_el_filtro_de_mapa_de_la_api_deja_solo_ese_mapa`.
- Versiones: `test_las_versiones_de_un_mapa_van_en_filas_distintas`.
- Vacio: `test_trends_sin_datos_devuelve_las_filas_vacias_sin_500` suma
  `by_start_side_map == []`.
- Criterio 4: vitest `ladoInicialMapa.test.js` (5) y el e2e `'Tendencias
  muestra la tabla por mitad'` (tabla, celda `Bank`, "Poca muestra").
- Criterio 5: fila en `metricas.md`.

Desvios del diseno:

- Los dos porcentajes ("Ganadas en ataque/defensa") van con 1 decimal y no
  con 0: con 0 la resta visible no cuadraba con la Diferencia (67 % - 33 % =
  "33.4 pts"). Hallazgo LOW de la revision ciega.
- El test de paridad de la constante del frontend se llama "un lado necesita
  tres partidas con resultado": no puede verificar el backend y no lo promete.
- Test extra de ruido separado del de veredicto (el diseno los juntaba en uno).

Sin migracion ni `recompute`. Verificacion manual de la ficha (runserver) no
corrida aparte: el e2e la cubre sobre `seed_demo`.

verificar.sh: VERDE 9b16f4a27 (1044 tests backend, 256 vitest, 76 e2e).

Skills: no aplica (lo resolvio el diseno; tabla con el `DataTable` de siempre).

OMC: plan=— · revisión=3 hallazgos LOW (3 arreglados) · verificación=—
