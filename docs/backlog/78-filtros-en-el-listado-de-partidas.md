# 78. Filtros en el listado de Partidas

estado: disenado
candado: -
rama: -
tipo: funcionalidad
epica: revision-de-rondas
area: fullstack
prioridad: 2
fuente: ALCANCE.md F16 (del PR #14, cerrado sin merge el 2026-11-05; rama claude/dazzling-einstein-w3qcyq como referencia, no se mergea)
archivos: backend/replays/models.py (filtro_resultado), backend/replays/analytics/aggregates.py (match_queryset), backend/replays/views.py (match_list), frontend/src/partidas.js, frontend/src/partidas.test.js, frontend/src/components/Filters.jsx, frontend/src/pages/Matches.jsx, backend/tests/test_filtros_de_partidas.py, frontend/e2e/humo.spec.js
turnos: po 20261105T0230Z-c8Ahepa, arquitecto 20261105T0349Z-cfLc9Nn

## PR

(La escribe el Release manager al final.)

## Que gana quien usa la app

La pagina Partidas lista todo el historial de a 50 y no filtra nada: para
encontrar "mis derrotas en Bank de esta semana" hay que recorrerla entera.
Con filtros de mapa, periodo, tipo y resultado la lista se achica a lo que
uno busca y el total dice cuantas son.

## Criterios de aceptacion

- [ ] `/api/matches/?result=<victoria|derrota|empate|incompleta>` devuelve
      solo partidas con ese `Match.result`, y `total` cuenta las filtradas
      (test por cada valor sobre una base con las cuatro). Un valor
      desconocido da 400 o se ignora, pero nunca 500.
- [ ] `/api/matches/` acepta `days`, `since`/`until` y `session` con la
      misma semantica que `_filters` (test: una partida fuera del periodo no
      sale; una fecha con zona horaria no da 500, como la ficha 33).
      `map` y `match_type` siguen como hoy.
- [ ] La paginacion respeta los filtros: con 60 victorias, `offset=50` trae
      las 10 restantes y no partidas de otro resultado.
- [ ] `Matches.jsx` muestra la barra de filtros (mapa, periodo, tipo) y un
      selector de resultado; cambiar un filtro vuelve a la primera pagina y
      el subtitulo dice "N partidas" con el total filtrado.
- [ ] e2e: elegir "Derrota" en Partidas deja solo filas con chip de derrota
      y la consola queda limpia.

## Fuera de alcance

- Filtros por lado, operador o sitio: son de ronda, no de partida.
- Guardar los filtros en la URL (A10) y partida anterior/siguiente (F17).
- Ordenar del lado del servidor por columna.

## Diseno

**Implementar despues de que #77 se mergee** (prioriza, no bloquea): la 77
toca `Filters.jsx` y `humo.spec.js`, y esta ficha usa lo que la 77 agrega
(`hayFiltros` de `tipoPartida.js` y el selector "Tipo" en lugar de "Solo
ranked"). Si la 77 no llegara a `dev`, el Dev define `hayFiltros` en
`partidas.js` con el mismo cuerpo y el selector de tipo queda fuera.

Sin migracion, sin `recompute`, sin metrica nueva: el subtitulo cuenta
partidas, que ya es un numero que la pagina muestra. No hay fila nueva en
`docs/metricas.md`. Sin arena (una forma obvia) y sin consenso (no toca
datos, POST, parser ni Electron).

**Decision de la pregunta del PO: se reusa la barra compartida de `App`.**
Variante conservadora y coherente con el resto de paginas; la pregunta
sigue en `## Para el humano`. Partidas manda a la API **solo los filtros que
son de partida** (mapa, periodo, sesion, tipo): lado, operador y sitio son de
ronda (fuera de alcance), asi que Partidas los esconde y no los manda aunque
vengan puestos desde otra pagina. El filtro de resultado es **local** a
Partidas (no entra al estado de `App`): en el Inicio o el Coach un
`result=` no significaria nada y prenderia "Limpiar" con un filtro invisible.

**Valor desconocido de `result`: se ignora** (como `days` o una fecha
invalida en `_filters`), nunca 500.

**Empate e incompleta, exactos.** El PR #14 (`claude/dazzling-einstein-w3qcyq`)
filtraba "empate" con `won=None`, que tambien trae las incompletas. Aca el
filtro sigue a `match_result` (`models.py:13`) caso por caso.

### Archivos y por que

1. **`backend/replays/models.py`**, junto a `match_result` (asi las dos
   reglas se leen y se cambian juntas):
   - `RESULTADOS = ("victoria", "derrota", "empate", "incompleta")`.
   - `filtro_resultado(result: str) -> Q | None`, el `Q` sobre `Match` que
     da cada etiqueta, en el mismo orden de decision que `match_result`:
     `incompleta` = `Q(won__isnull=True)`; `empate` =
     `Q(won__isnull=False, my_score=F("opponent_score"))`; `victoria` =
     `Q(won=True) & ~Q(my_score=F("opponent_score"))`; `derrota` =
     `Q(won=False) & ~Q(my_score=F("opponent_score"))`; cualquier otro
     valor -> `None`. Import de `F` y `Q` desde `django.db.models`.
2. **`backend/replays/analytics/aggregates.py`**, debajo de `base_queryset`:
   `match_queryset(**filters) -> QuerySet[Match]`, los filtros de la barra
   aplicados a partidas con la misma lectura que `base_queryset`: `map` con
   `filtro_mapa(..., prefijo="")`, `match_type`, `ranked_only`
   (`match_type="Ranked"`), `since`/`until` sobre `played_at`, `session` con
   `id__in=session_match_ids(...)`. `side`, `operator` y `site` se ignoran;
   el docstring dice por que (una partida tiene los dos lados y diez
   operadores) y que existe para que Partidas y el Resumen cuenten las
   mismas partidas. Va en `aggregates.py` y no en `views.py` para quedar al
   lado de `base_queryset`: si alguien agrega un filtro a uno, ve el otro.
3. **`backend/replays/views.py`, `match_list`**: reemplaza los dos `if`
   (`map`, `match_type`) por
   `qs = agg.match_queryset(**_filters(request))` y, si
   `filtro_resultado(request.GET.get("result", ""))` no es `None`,
   `qs = qs.filter(...)`. `total = qs.count()` ya queda sobre lo filtrado y
   el slice `offset`/`limit` tambien. El resto de la vista no cambia. El
   `ordering = ["-played_at"]` del modelo sigue mandando el orden.
4. **`frontend/src/partidas.js`** (nuevo), logica pura sin React:
   - `CLAVES_DE_PARTIDA = ['map', 'days', 'since', 'until', 'session', 'match_type', 'ranked_only']`.
   - `filtrosDePartida(filtros)` -> objeto solo con esas claves (las que
     esten en `filtros`; `null`/`undefined` -> `{}`).
   - `OPCIONES_DE_RESULTADO` -> `[{ value: '', label: 'Todos' },
     { value: 'victoria', label: 'Victoria' }, { value: 'derrota', label:
     'Derrota' }, { value: 'empate', label: 'Empate' }, { value:
     'incompleta', label: 'Incompleta' }]`.
   - `paramsDePartidas(filtros, resultado, offset, limite)` ->
     `{ ...filtrosDePartida(filtros), result: resultado, limit: limite,
     offset }` (`qs()` ya saca `''` y `false`).
   - `claveDeFiltros(filtros, resultado)` -> `qs(filtrosDePartida(filtros)) + '|' + resultado`
     (usa `qs` de `api.js`).
   - `offsetVigente(pagina, clave)` -> `pagina.clave === clave ? pagina.offset : 0`.
     Es lo que hace "cambiar un filtro vuelve a la primera pagina" **sin**
     un `useEffect` que dispararia una request de mas con el offset viejo.
   - `subtituloDePartidas(total, filtrado)` -> sin filtros
     `"29 partidas importadas."` (el texto de hoy); filtrado
     `"12 partidas con estos filtros."`; singular `"1 partida ..."`.
5. **`frontend/src/partidas.test.js`** (nuevo, vitest, estilo de
   `mapas.test.js`):
   - `filtros de partida dejan afuera lado operador y sitio`
   - `filtros de partida sin datos dan un objeto vacio`
   - `los params mandan el resultado y la pagina`
   - `resultado Todos no viaja en la query` (`qs(paramsDePartidas({}, '', 0, 50))` es `?limit=50&offset=0`)
   - `cambiar un filtro vuelve a la primera pagina` (`offsetVigente({ clave: 'a', offset: 50 }, 'b') === 0`)
   - `sin cambiar filtros la pagina se mantiene`
   - `cambiar el lado no cambia la clave de Partidas` (la clave ignora `side`: no se resetea la pagina por un filtro que Partidas no usa)
   - `el subtitulo dice importadas sin filtros y con estos filtros con filtros`
   - `el subtitulo usa singular con una partida`
6. **`frontend/src/components/Filters.jsx`** (despues de la 77):
   - prop nueva `showSide = true`; con `false` no se pinta "Lado".
   - prop nueva `children`, que se pinta dentro de `.filters` justo antes
     de "Limpiar" (asi el selector de resultado queda en la misma fila).
   - prop nueva `hayExtra = false`: "Limpiar" se muestra si
     `hayFiltros(value) || hayExtra`. "Limpiar" sigue llamando
     `onChange({})`. Defaults que dejan igual a todas las demas paginas.
7. **`frontend/src/pages/Matches.jsx`**: recibe `filters` y `setFilters`
   del `context` de `App` (ya llegan: `<Matches {...context} />`).
   - `const [resultado, setResultado] = useState('')`,
     `const clave = claveDeFiltros(filters, resultado)`,
     `const [pagina, setPagina] = useState({ clave, offset: 0 })`,
     `const offset = offsetVigente(pagina, clave)`; los botones hacen
     `setPagina({ clave, offset: ... })`.
   - `useApi('/matches/', paramsDePartidas(filters, resultado, offset, PAGE))`.
   - `filtrado = hayFiltros(filtrosDePartida(filters)) || Boolean(resultado)`.
   - Barra: `<Filters value={filters} onChange={cambiarFiltros}
     showSide={false} showOperator={false} showSession hayExtra={Boolean(resultado)}>`
     con hijo `<label>Resultado<select value={resultado}
     onChange={(e) => setResultado(e.target.value)}>` y
     `OPCIONES_DE_RESULTADO`. `cambiarFiltros(f)` hace `setFilters(f)` y, si
     `Object.keys(f).length === 0` (es "Limpiar"), tambien
     `setResultado('')`.
   - La barra va entre el `page-head` y el `Panel`, como en el Inicio.
   - Subtitulo: `subtituloDePartidas(data.total, filtrado)`.
   - Vacio: si `!data?.total` y `filtrado`, se pinta `page-head` (h1
     "Partidas", subtitulo `0 partidas con estos filtros.`), la barra y
     `<p className="note">Ninguna partida con estos filtros. Cambia alguno o
     usa Limpiar.</p>`, sin `Panel`. Sin filtros sigue el `EmptyState` de
     siempre (base vacia de verdad). Nada de clase `empty-state` en el caso
     filtrado (el e2e de "todas las paginas cargan" la busca en 0). Mismo
     criterio que el Inicio de la 77.
   - `if (loading && !data) return <Loading />` se queda: al cambiar un
     filtro `data` ya existe y la tabla vieja se ve hasta que llega la nueva,
     como hoy al paginar.
8. **`backend/tests/test_filtros_de_partidas.py`** (nuevo), con
   `factories.make_match` (`won` se pasa explicito; `index` distinto por
   partida; ninguna necesita rondas salvo donde se diga):
   - `test_cada_resultado_trae_solo_sus_partidas`: una victoria, una
     derrota, un empate (`won=False`, 3-3) y una incompleta (`won=None`);
     para cada valor de `RESULTADOS`, `/api/matches/?result=<v>` da
     `total == 1` y `matches[0]["result"] == v`.
   - `test_el_filtro_de_resultado_coincide_con_match_result`: para cada
     partida de la base anterior, `Match.objects.filter(filtro_resultado(m.result))`
     la contiene, y ninguna partida cae en dos filtros.
   - `test_un_resultado_desconocido_se_ignora_y_no_da_500`:
     `?result=ganada` -> 200 y `total` = todas.
   - `test_la_paginacion_respeta_el_resultado`: 60 victorias y 5 derrotas;
     `?result=victoria&limit=50&offset=50` -> `total == 60`, 10 filas, todas
     `victoria`.
   - `test_days_deja_afuera_una_partida_vieja`: una partida de hace 2 dias
     y otra de hace 40 (`datetime.now() - timedelta(...)`); `?days=30` -> 1.
   - `test_until_sin_hora_incluye_todo_ese_dia`: partida a las 22:00 del
     2026-09-08; `?until=2026-09-08` la trae y `?since=2026-09-09` no.
   - `test_una_fecha_con_zona_no_da_500`: `?since=2026-09-08T00:00:00Z`
     (urlencode del `+` si se usa offset) -> 200.
   - `test_la_sesion_trae_solo_sus_partidas`: dos grupos de partidas
     separados por un dia (mas que el corte de sesion); `?session=0` da las
     del grupo mas reciente, con `total` igual a
     `len(agg.session_match_ids(0))`.
   - `test_tipo_y_solo_ranked_filtran_partidas`: una Ranked y una
     Unranked; `?match_type=Unranked` -> 1 y `?ranked_only=1` -> 1 (la
     Ranked).
   - `test_lado_operador_y_sitio_no_filtran_partidas`:
     `?side=Attack&operator=Ash&site=X` da el mismo `total` que sin nada.
   - `test_mapa_y_resultado_se_combinan`: victoria en Bank, derrota en
     Bank, victoria en Border; `?map=bank&result=victoria` -> 1.
9. **`frontend/e2e/humo.spec.js`**, test nuevo `Partidas filtra por
   resultado y por mapa`, con `vigilarConsola`. `seed_demo` gana sus 29
   partidas (comentario de la linea 153), no se toca el seed:
   - `goto('/partidas')`: subtitulo `29 partidas importadas.`; la barra
     muestra "Mapa" y "Periodo" y **no** "Lado" ni "Operador"
     (`getByLabel('Lado')` en 0).
   - Elegir "Victoria" en `getByLabel('Resultado')` esperando
     `page.waitForRequest(/\/api\/matches\/\?.*result=victoria/)`:
     subtitulo `29 partidas con estos filtros.` y toda fila de la tabla
     tiene `.chip.win`.
   - Elegir "Derrota": nota "Ninguna partida con estos filtros", la barra
     sigue visible, `.empty-state` en 0.
   - "Limpiar": subtitulo vuelve a `29 partidas importadas.` y
     "Resultado" vuelve a "Todos".
   - Elegir el primer mapa de `getByLabel('Mapa')` (esperando la request
     con `map=`): el subtitulo dice `N partidas con estos filtros.` con
     N < 29 y toda celda de la columna Mapa es la etiqueta elegida.
   - Consola limpia.
   El paso "cambiar un filtro vuelve a la primera pagina" no se ve en el
   seed (29 < 50): lo cubren `partidas.test.js` y el test de paginacion del
   backend.

### Orden de implementacion

1. `models.py` (`RESULTADOS`, `filtro_resultado`) y
   `aggregates.match_queryset`, con los tests del backend.
2. `match_list` usando los dos; correr `manage.py test tests`.
3. `partidas.js` + `partidas.test.js`.
4. `Filters.jsx` (props) y `Matches.jsx`; `npm run build`.
5. e2e; `check.sh` completo con `verificar.sh`.

### Que puede romperse

- **Tests existentes de `/api/matches/`** (`test_api.py`, `test_rating.py`,
  `test_rachas.py`, `test_mapa_de_la_partida.py`, ...): piden sin filtros o
  con `map`/`match_type`; el contrato de la respuesta no cambia (mismas
  claves). Si alguno manda `days` o `since` esperando que se ignore, hoy se
  ignora y pasaria a filtrar: buscarlo con `grep -n "api/matches/?"
  backend/tests` antes de cerrar.
- **e2e de las lineas 434 y 460** (`/api/matches/?limit=200`): sin filtros,
  no cambian.
- **Barra compartida**: un `showSide` mal puesto o el `children` fuera de
  `.filters` cambia las otras paginas; las props nuevas tienen default que
  deja todo igual. El e2e de "todas las paginas cargan" lo cubre.
- **Filtros arrastrados desde otra pagina**: con Lado = Ataque elegido en el
  Inicio, Partidas no lo muestra ni lo manda, y "Limpiar" igual aparece
  (`hayFiltros(value)` lo ve). Es lo esperado: Limpiar borra tambien lo que
  Partidas no muestra, como en las demas paginas.
- **Sesiones**: `session_match_ids` usa todo el historial; un indice fuera
  de rango da lista vacia -> 0 partidas, no 500.

### Verificacion manual

`seed_demo`, `runserver`, abrir Partidas: barra sin Lado ni Operador; elegir
Victoria (29), Derrota (nota sin tabla), Limpiar; elegir un mapa y un
periodo de 7 dias; elegir Lado = Ataque en el Inicio y volver: Partidas
sigue con 29 y aparece "Limpiar". En la base real del PC (donde hay
derrotas y mas de 50 partidas): elegir Derrota, ir a "Siguientes", cambiar
el mapa y ver que vuelve a 1–N.

Skills: no aplica (la barra, la tabla y el filtro ya existen en el repo; no
es un dominio nuevo).
OMC: plan=— · revisión=— · verificación=— (ficha chica de una forma obvia: sin consenso)

## Implementacion

## Revision

## QA

## Para el humano

- (po) Si la barra compartida de `App` se reusa en Partidas, los filtros
  elegidos en Partidas siguen puestos al volver al Inicio, como en el resto de
  paginas. Variante conservadora: reusarla (coherente). Si preferis que
  Partidas tenga sus propios filtros, decilo en la ficha.
- (arquitecto) Disenado con la variante conservadora: barra compartida,
  sin Lado ni Operador en Partidas (son de ronda), y el filtro de resultado
  local a Partidas. Cambiarlo despues es tocar solo `Matches.jsx`.
