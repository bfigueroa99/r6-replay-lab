# 59. Clutch por mapa y sitio

estado: disenado
candado: -
rama: -
tipo: funcionalidad
epica: impacto
area: fullstack
prioridad: 3
fuente: ALCANCE.md K5
archivos: backend/replays/analytics/aggregates.py, backend/replays/views.py, backend/tests/test_clutch.py, frontend/src/pages/Teammates.jsx, frontend/e2e/humo.spec.js, docs/metricas.md
turnos: po 20261019T0325Z, arquitecto 20261022T0804Z

Implementar despues de #55: usa la columna `RoundPlayer.clutch_vs` que esa
ficha agrega con su migracion.

## PR

(La escribe el Release manager al final.)

## Que gana quien usa la app

La ficha 55 da la conversion de clutch por X y lado; esta la parte por mapa
y por sitio de bomba. Se ve en que sitio cierras las rondas que quedan en tus
manos y en cual te quedas solo y pierdes siempre, que es donde conviene
revisar como se juega el final de ronda.

## Criterios de aceptacion

- [ ] Agregado nuevo `clutch_by_site` en `replays/analytics/aggregates.py`:
  una fila por mapa y sitio (`Match.map_slug`, `map_name`, `Round.site`) y
  otra de total por mapa, con intentos (`clutch_vs > 0`), ganados
  (`clutch_vs > 0` y `won`) y %. Respeta los filtros de la barra (lado,
  fechas, ranked, operador). Rondas sin sitio van a una fila "Sin sitio" del
  mapa, no se pierden. Test de Django con dos mapas y tres sitios armados.
- [ ] Muestra minima: un sitio con menos de 5 intentos sale igual pero con
  `low_sample: true`, para que la UI lo marque; el umbral es una constante
  con nombre. Test del borde (4 y 5 intentos).
- [ ] Se sirve en el mismo endpoint que la tabla de conversion de la ficha
  55, como `clutch_by_site`; con base vacia devuelve lista vacia sin 500.
- [ ] En la pagina donde la ficha 55 deja la tabla de conversion, una tabla
  "Clutch por mapa y sitio" debajo, ordenada por mapa y con el % de cada
  sitio, boton CSV y la marca de muestra chica. Sin intentos dice
  "Todavía no quedaste último en ninguna ronda". Entra al e2e con
  `seed_demo`.
- [ ] Fila nueva en `docs/metricas.md` ("Clutch por mapa y sitio") que remite
  a la definicion de intento y ganado de la ficha 55.

## Fuera de alcance

- Clutch por operador (idea O6): otra ficha, misma columna.
- La parte "cuantos se esperaban" de K3, que necesita la tabla de K1.
- Cambiar `one_vx`, el Rating o la tabla de la ficha 55.

## Diseno

La 55 ya esta en `main` (`clutch_vs`, migracion 0003, `clutch_conversion` en
`/api/teammates/`, tabla en el Panel "Clutches" de Compañeros): la
dependencia esta cumplida. Una sola forma obvia, sin migracion.

**Backend, `backend/replays/analytics/aggregates.py`**, debajo de
`clutch_conversion`:

1. Constante `CLUTCH_SITIO_MIN = 5` con comentario (por debajo, el % de un
   sitio es anecdota; la fila sale igual, marcada).
2. `clutch_by_site(**filters) -> list[dict]`: mismo queryset que
   `clutch_conversion` (`clutch_vs__gt=0`, `round__my_team_won__isnull=False`,
   el comentario de por que ya esta ahi) agrupado por
   `round__match__map_slug`, `round__match__map_name`, `round__site` con
   `attempts=Count("id")` y `won=Count("id", filter=Q(round__my_team_won=True))`.
   Por mapa, primero una fila total (`kind: "map"`, `site: None`) y despues
   una por sitio (`kind: "site"`), con `slug`, `map`, `site` (`""` se
   devuelve como `"Sin sitio"`, ultima del mapa), `attempts`, `won`,
   `pct=_pct(won, attempts)` y `low_sample = attempts < CLUTCH_SITIO_MIN`
   (tambien en la fila total). Mapas por nombre; sitios por intentos desc y
   nombre. Base vacia: `[]`.
3. `views.teammates`: clave `"clutch_by_site": agg.clutch_by_site(**filters)`.

**Tests, `backend/tests/test_clutch.py`** (clase nueva al final, con las
factories que ya usa el archivo):
- `test_clutch_por_sitio_agrupa_por_mapa_y_sitio` (dos mapas, tres sitios,
  totales por mapa que suman sus sitios)
- `test_una_ronda_sin_sitio_va_a_sin_sitio`
- `test_cuatro_intentos_son_muestra_chica_y_cinco_no`
- `test_una_ronda_sin_ganador_no_cuenta_como_intento_por_sitio`
- `test_clutch_por_sitio_respeta_el_filtro_de_lado` (via
  `/api/teammates/?side=Attack`)
- `test_clutch_por_sitio_con_base_vacia_es_lista_vacia`

**Frontend, `frontend/src/pages/Teammates.jsx`**, dentro del Panel
"Clutches", entre la tabla de conversion y la de clutches ganados: subtitulo
`<h3>` "Clutch por mapa y sitio" y `DataTable` con Mapa / Sitio (la fila
total en negrita con el nombre del mapa y sitio "Total"), Intentos,
Ganados, % (con `Bar` como Sinergia), `csvName="clutch-por-sitio"`. Orden
fijo del backend: aplanar con un indice `orden` y `initialSort` por el, como
"Primero en caer". `low_sample`: clase `dim` en la fila o `*` junto al % con
`help` "Menos de 5 intentos". Sin filas:
`<p className="dim">Todavía no quedaste último en ninguna ronda.</p>`. Ojo
con el e2e existente de conversion: afirma `panel.locator('table').first()`,
asi que la tabla nueva tiene que ir **despues** de la de conversion.

**e2e, `frontend/e2e/humo.spec.js`**: `test('Compañeros muestra el clutch
por mapa y sitio')`. Medido sobre `seed_demo`: 10 intentos, Border 5 (B
Armory 3, A Ventilation 2), Bank 3 (B Lockers 3), Club House 2 (uno en cada
sitio de B Church y A Bedroom). Afirmar la fila total de Border con 5
intentos sin marca de muestra chica y una fila de sitio marcada; consola
limpia.

**`docs/metricas.md`**, seccion `## Impacto`, debajo de "Clutch: intentos y
conversión": fila "Clutch por mapa y sitio" (mismo intento y ganado que la
fila de arriba, agrupado por mapa y sitio de bomba; rondas sin sitio en
"Sin sitio"; menos de 5 intentos se marca como muestra chica).

**Orden:** constante + funcion -> tests -> vista -> Teammates.jsx -> e2e ->
metricas.md -> `check.sh`.

**Que puede romperse:** el e2e de conversion si la tabla nueva queda
primera (ver arriba). Nada de datos: es una clave nueva del JSON.

**Verificacion manual:** `/companeros` con la base real; que la suma de los
totales por mapa coincida con los intentos de la tabla de conversion.

**Archivos ocupados:** `aggregates.py`, `views.py`, `metricas.md`,
`humo.spec.js` tambien en la rama de la 60 (PR #48) y en las fichas 56 y
57: zonas distintas, se implementa ya y se resuelve con `git merge
origin/main` (P3). Con la 57 comparte `views.teammates` y `Teammates.jsx`:
si las dos van en paralelo, la segunda en mergear resuelve.

## Implementacion
