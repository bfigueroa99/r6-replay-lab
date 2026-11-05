# 83. Partidas excluidas a la vista en Partidas y en Datos

estado: disenado
candado: -
rama: -
tipo: funcionalidad
epica: datos
area: fullstack
prioridad: 3
fuente: tramo 2 de la ficha 79 (G2 de ALCANCE.md), partida por el arquitecto 20261105T0349Z-cCqeUqM porque el total (~630 lineas) no entra en un turno de Dev
archivos: backend/replays/views.py (import_status), frontend/src/pages/Matches.jsx, frontend/src/pages/Datos.jsx, backend/tests/test_excluir_partida.py, frontend/e2e/partidas-excluidas.spec.js, docs/metricas.md
turnos: arquitecto 20261105T0349Z-cCqeUqM, arquitecto 20261105T1303Z-cfek47z

**Implementar despues de que #79 se mergee**: usa su columna `Match.excluded`,
el campo `"excluded"` de `/api/matches/`, el POST y el e2e
`partidas-excluidas.spec.js`.

## PR

(La escribe el Release manager al final.)

## Que gana quien usa la app

Con la 79, una partida excluida deja de contar, pero solo se nota desde su
detalle. Con este tramo, la fila de Partidas lleva el chip "excluida" y Datos
lista todas las que sacaste, cada una con su enlace para volver a contarla.
Asi ninguna queda olvidada fuera de tus números.

## Criterios de aceptacion

- [ ] La fila de una partida excluida en Partidas muestra el chip "excluida"
      junto a la fecha, dentro del `render` de `played_at`. El CSV del boton de
      Partidas queda byte a byte igual, porque `celdaCsv` (ui.jsx:85) exporta
      `row[col.key]`.
- [ ] `GET /api/import/status/` suma
      `"excluded": [{"id", "played_at", "map", "score"}]`, ordenado por
      `-played_at` y con la etiqueta de version (`etiquetas_de_mapas(...,
      incluir_excluidas=True)`). Lleva el test
      `test_import_status_lista_las_excluidas` en `test_excluir_partida.py`.
- [ ] En Datos, el panel "Fuera de tus números" (hint: "No cuentan en ningún
      agregado; se vuelven a contar desde su detalle.") muestra Cuándo (link a
      `/partidas/<id>`), Mapa y Marcador. Si no hay ninguna, dice "Ninguna
      partida excluida.".
- [ ] El e2e `partidas-excluidas.spec.js` suma dos pasos con la partida
      excluida: el chip en `/partidas` y el link en `/datos`. La consola tiene
      que quedar limpia.

## Fuera de alcance

- Excluir desde Partidas o desde Datos: el boton vive en el detalle.
- Un filtro `?excluded=` en el listado.
- Que la topbar diga "· N excluidas".

## Diseno

(arquitecto 20261105T1303Z-cfek47z, sobre dev 696c79d y el diseno de la 79.
Ficha chica y de una forma obvia: sin consenso ni arena.)

**Implementar despues de que la 79 se mergee.** Usa su columna
`Match.excluded`, `make_match(excluded=)`, el kwarg
`etiquetas_de_mapas(..., incluir_excluidas=True)`, el campo `"excluded"` de
cada fila de `/api/matches/` y el e2e `partidas-excluidas.spec.js`. Sin la 79
en dev esta ficha no compila: el Dev no la reclama antes. Comparte
`views.py` con la 79 (otra funcion) y `Datos.jsx` con la 81 si su barrido de
tildes llega ahi: choques de contexto, no de logica.

Sin migracion, sin ruta nueva, sin POST nuevo: `import-status` ya esta en
`NO_AGREGADOS` del test `test_toda_ruta_esta_clasificada` de la 79 (es
inventario), y sigue ahi. Sin numero nuevo: no hay fila nueva en la tabla de
`docs/metricas.md`, solo dos frases en el parrafo de partidas excluidas.

### Archivos y por que

**`backend/replays/views.py`, `import_status`** (hoy linea 831). Datos ya pide
`/api/import/status/` (inventario de la base); sumar ahi la lista evita una
ruta y un `useApi` mas. Antes del `return`:

```python
    # inventario, no agregado: las excluidas se listan para poder volver a contarlas
    excluidas = list(Match.objects.filter(excluded=True).order_by("-played_at"))
    etiquetas = agg.etiquetas_de_mapas({m.map_slug for m in excluidas}, incluir_excluidas=True)
```

y en el dict, despues de `"pending"`:

```python
            "excluded": [
                {
                    "id": m.pk,
                    "played_at": m.played_at.isoformat(),
                    "map": etiquetas.get((m.map_slug, m.map_id), m.map_name),
                    "score": f"{m.my_score}-{m.opponent_score}",
                }
                for m in excluidas
            ],
```

`played_at` con el mismo formato que `match_list` (el front corta con
`slice(0, 16)`). Sin tope: son las que el usuario marco a mano. Con el set
vacio, `etiquetas_de_mapas` filtra `map_slug__in=[]` y no lee nada.

**`frontend/src/pages/Matches.jsx`**, columna `played_at` (hoy linea 92). El
`render` pasa a:

```jsx
render: (row) => (
  <>
    <Link to={`/partidas/${row.id}`}>{row.played_at.slice(0, 16).replace('T', ' ')}</Link>
    {row.excluded ? (
      <>
        {' '}
        <span className="chip" title="No cuenta en tus números">excluida</span>
      </>
    ) : null}
  </>
),
```

Sin `csv:` en la columna: `celdaCsv` (`ui.jsx:85`) exporta `row.played_at`,
asi que el CSV de Partidas queda byte a byte igual. Orden por `played_at`
igual.

**`frontend/src/pages/Datos.jsx`**: panel nuevo al final, despues de
"Importacion" (lo de arriba sigue en el mismo lugar, y los e2e de Datos lo
buscan por texto):

```jsx
<Panel
  title="Fuera de tus números"
  hint="No cuentan en ningún agregado; se vuelven a contar desde su detalle."
>
  <DataTable
    columns={[
      {
        key: 'played_at',
        label: 'Cuándo',
        render: (row) => (
          <Link to={`/partidas/${row.id}`}>{row.played_at.slice(0, 16).replace('T', ' ')}</Link>
        ),
      },
      { key: 'map', label: 'Mapa' },
      { key: 'score', label: 'Marcador', sortable: false },
    ]}
    rows={status.data?.excluded || []}
    initialSort={{ key: 'played_at', dir: 'desc' }}
    rowKey={(row) => row.id}
    empty={status.data ? 'Ninguna partida excluida.' : 'Cargando...'}
  />
</Panel>
```

`empty` distingue carga de lista vacia para no mostrar "Ninguna" un instante
cuando si hay. Sin `csvName`. `Link` y `DataTable` ya estan importados.

**`backend/tests/test_excluir_partida.py`** (lo crea la 79): clase nueva
`ExcluidasEnDatosTests`, con `override_settings(REPLAY_DIR=<tmpdir vacio>)`
como `test_api.py:277` (`import_status` lee la carpeta):

- `test_import_status_lista_las_excluidas`: A = `make_match(map_name="Bank",
  map_id=1, index=0, excluded=True)`, C = `make_match(map_name="Bank",
  map_id=2, index=1)`, B = `make_match(map_name="Club House", index=2,
  excluded=True)`. Afirma:
  - `[e["id"] for e in excluded] == [B.pk, A.pk]` (mas nueva primero; C no esta);
  - las claves de cada fila son exactamente `{"id", "played_at", "map", "score"}`;
  - el `map` de A es igual al `map` de A en `/api/matches/` y contiene
    `"(id 1)"` (C comparte nombre y slug: es la etiqueta de version);
  - el `score` de A es `"4-2"` y su `played_at` es `A.played_at.isoformat()`.
- `test_import_status_sin_excluidas_da_lista_vacia`: con una partida que cuenta,
  `excluded == []`.

**`frontend/e2e/partidas-excluidas.spec.js`** (lo crea la 79). Dentro del
mismo test, entre el paso 3 (excluir en el detalle) y el 4 (Inicio 196/28):

- 3b. `page.goto('/partidas')`; la fila
  `page.locator('tbody tr', { has: page.locator(\`a[href="/partidas/${partidaId}"]\`) })`
  contiene `excluida`, y `page.locator('tbody .chip', { hasText: /^excluida$/ })`
  tiene `toHaveCount(1)` (solo esa).
- 3c. `page.goto('/datos')`; en
  `page.locator('section.panel', { has: page.getByRole('heading', { name: 'Fuera de tus números', exact: true }) })`
  hay un link `a[href="/partidas/${partidaId}"]`; clic, la URL termina en
  `/partidas/${partidaId}` y se ve el boton "Volver a contarla".

Y despues del paso 5 (vuelta a 203/29):

- 5b. En `/datos`, ese panel muestra "Ninguna partida excluida.", y en
  `/partidas` `tbody .chip` con `/^excluida$/` tiene `toHaveCount(0)`.

`expect(errores).toEqual([])` sigue al final. El `afterEach` de la 79 ya
devuelve la partida si algo falla a mitad.

**`docs/metricas.md`**, parrafo **Partidas excluidas** (lo escribe la 79): la
frase "Sigue en la pagina Partidas (y en el CSV que baja su boton), en su
detalle y en el conteo de importadas" pasa a:

```
Sigue en la pagina Partidas, con el chip "excluida" junto a la fecha (el CSV
que baja su boton no cambia), en su detalle, en el conteo de importadas y en
Datos, que las lista en "Fuera de tus números" con enlace a cada una
```

### Tests

Backend: los dos de arriba. Vitest: ninguno (no hay logica pura nueva; el
chip es un ternario). e2e: los pasos 3b, 3c y 5b.

### Orden de implementacion

1. `views.py` y los dos tests; suite en verde.
2. `Matches.jsx` y `Datos.jsx`; `npm run build` y `npm test`.
3. Pasos del e2e y la frase de `metricas.md`; `check.sh` completo.

### Que puede romperse

- **e2e de Datos en `humo.spec.js`** (`Datos avisa...`, `Datos muestra Sin
  identificar...`): buscan por texto otros paneles; el nuevo dice "Ninguna
  partida excluida." porque `humo` corre antes que `partidas-excluidas`
  (orden alfabetico, `workers: 1`). No deberian moverse.
- **CSV de Partidas**: no cambia porque la columna no tiene `csv:`. Si el Dev
  le agrega uno, cambia; no agregarlo.
- **Etiqueta de version**: Datos muestra la misma que Partidas y el detalle
  ("Bank (id 1)"), aunque los agregados digan "Bank" (lo documenta la 79).

### Verificacion manual en el PC

Con la 79 ya probada: excluir una partida desde su detalle, ver el chip en
Partidas (y que el CSV del boton no lo trae), ver la fila en Datos → "Fuera de
tus números", seguir el enlace y "Volver a contarla": la fila desaparece de
Datos y el chip de Partidas.

Skills: no aplica (panel y tabla con `Panel`/`DataTable` existentes, e2e que ya escribe la 79).
Arena: no (una sola forma obvia: la lista va en el inventario que Datos ya lee).

OMC: plan=— · revisión=— · verificación=—

Revalidado por arquitecto 20261105T1547Z-cDskDBu contra dev 0861b0b: sigue
valido. Unico ajuste: `import_status` esta ahora en `views.py:834` (la 86,
PR #83, sumo 3 lineas en `duels`); `Matches.jsx:92` y `celdaCsv`
(`ui.jsx:85`) sin cambios. La 79 sigue sin mergear (espera al humano por
`CLAUDE.md`) y su rama mergea limpio contra dev: el orden se mantiene.

## Implementacion

## Revision

## QA

## Verificar en el PC

## Para el humano
