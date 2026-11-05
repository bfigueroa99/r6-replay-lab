# 79. Excluir una partida de los agregados

estado: disenado
candado: -
rama: -
tipo: funcionalidad
epica: datos
area: fullstack
prioridad: 3
fuente: ALCANCE.md G2; decision del humano del 2026-11-05 (POST nuevo permitido, local y con application/json, entra a la lista de CLAUDE.md al disenarse)
archivos: backend/replays/models.py, backend/replays/migrations/0005_match_excluded.py, backend/replays/analytics/aggregates.py, backend/replays/views.py, backend/replays/urls.py, backend/replays/ingest.py (comentario), backend/tests/factories.py, backend/tests/test_excluir_partida.py, frontend/src/pages/MatchDetail.jsx, frontend/e2e/partidas-excluidas.spec.js, CLAUDE.md, docs/metricas.md
turnos: po 20261105T0230Z-c8Ahepa, arquitecto 20261105T0349Z-cCqeUqM

## PR

(La escribe el Release manager al final.)

## Que gana quien usa la app

Una custom con amigos, una partida en la que se cayo internet o una de
calentamiento ensucian el K/D, el rating y los winrates, y hoy la unica salida
es borrar el `.rec`. Con "Excluir de mis numeros" en el detalle de partida la
partida sigue visible en Partidas pero deja de contar en todo agregado, y un
clic la vuelve a meter: nada se borra.

## Criterios de aceptacion

- [ ] `POST /api/matches/<id>/exclude/` (nombre final del Arquitecto) con
      `{"excluded": true|false}` y `Content-Type: application/json` marca o
      desmarca la partida; sin `application/json` da 415 como los demas POST (`_es_json`; test), y el docstring de `_es_json` suma la ruta nueva, y
      una partida inexistente da 404.
- [ ] Una partida excluida no cuenta en `/api/overview/`, `/api/coach/`,
      `/api/operators/`, `/api/teammates/`, `/api/trends/` ni en el CSV de
      agregados: test que compara cada uno contra la misma base sin esa
      partida importada.
- [ ] La partida sigue en `/api/matches/` (con `"excluded": true`) y su
      detalle `/api/matches/<id>/` sigue completo; volver a incluirla deja
      los agregados exactamente como antes (test ida y vuelta).
- [ ] Reimportar el `.rec` (`import_replays --force`) no pierde la marca
      (test: `update_or_create` no pisa el campo).
- [ ] UI: boton "Excluir de mis números" / "Volver a contarla" en el detalle,
      con aviso "Esta partida no cuenta en tus números." si esta excluida.
      e2e: excluir y volver a incluir una partida sembrada (Inicio 203/29 ->
      196/28 -> 203/29) sin errores de consola. (El chip en Partidas y la
      lista en Datos pasan al tramo 2, ficha 83.)
- [ ] `CLAUDE.md` suma el POST nuevo a la lista de POST permitidos y
      `docs/metricas.md` dice que toda metrica excluye las partidas marcadas.

## Fuera de alcance

- Borrar partidas o `.rec` desde la app.
- Excluir rondas sueltas o excluir por regla (todas las customs): eso seria
  un filtro, otra idea.
- Que el resumen copiado (H4) o el CSV de partidas cambien: la partida sigue
  siendo tuya; solo sale de los agregados.

## Diseno

(arquitecto 20261105T0349Z-cCqeUqM, sobre dev fb431f7. Plan por consenso en
modo deliberado: migracion + POST. Ronda 1 ITERATE, ronda 2 APPROVE del critic;
las correcciones menores de la ronda 2 ya estan aca.)

**Tramos.** Completa son ~630 lineas, 330 de ellas tests, asi que no entra en
un turno de Dev. Esta ficha es el **tramo 1** (~520): todo el backend con sus
guardias, el boton en el detalle, el e2e de ida y vuelta y los docs. Ya deja
algo a la vista: con el boton, el Inicio pasa de "203 rondas en 29 partidas" a
"196 rondas en 28 partidas". El **tramo 2** es la ficha 83 (`propuesto`): el
chip "excluida" en Partidas y la lista de excluidas en Datos. Los criterios de
arriba que hablan del chip y de Datos pasan a la 83.

**Implementar despues de que #78 se mergee** (prioriza, no bloquea). La 78
toca `views.py` (`match_list`) y la 79 tambien (`match_list`, `match_detail`).
La 80 toca `aggregates.py` (`by_site`, `by_spawn`, `AGGREGATES`); la 79 toca
otras funciones del mismo archivo, asi que el choque, si aparece, es de
contexto. Ninguna rama abierta agrega migracion: la de la 79 es la `0005`. Si
otra rama mergea una `0005` antes, esta renumera (P3).

### Decision: una sola raiz para lo que cuenta (opcion B)

- **(A)** Filtro en `base_queryset` mas parches sueltos. Se descarta: la
  proxima consulta raiz que alguien escriba se olvida del filtro y ningun test
  lo ve.
- **(C)** Manager por defecto filtrado. Se descarta porque rompe:
  - `match_detail` (`Match.objects.get(pk)` daria 404);
  - `ingest._import` (lineas 132 y 156: no ve la excluida y `update_or_create`
    choca con `unique`);
  - `seed_demo`, el admin, `recompute` y `retag`.
  - Ademas no cubre `RoundPlayer`.
- **(B) Elegida.** Tres helpers en `aggregates.py` mas dos redes de tests:
  1. La **primaria**, de comportamiento: cada ruta GET y cada tabla del CSV de
     agregados se compara contra la misma base con la partida borrada. Cada
     ruta de `urls.py` tiene que estar clasificada.
  2. La **secundaria**, estatica (`ast`). Acepta cualquier `id__in`, asi que no
     prueba semantica: atrapa la regresion tipica.

"Excluida" es igual a "nunca importada" en todo numero. Lo que es de una sola
partida la sigue mostrando: el listado de Partidas, su detalle, el CSV que baja
el boton de la pagina Partidas (`celdaCsv`) y el inventario (`/api/health/`,
la topbar). Nada se borra.

### Archivos y por que

**`backend/replays/models.py`** (`Match`, despues de `won`)
- `excluded = models.BooleanField(default=False)`, con el comentario "fuera de
  todo agregado; la partida se sigue mostrando".
- Sin indice: la tabla es chica.

**`backend/replays/migrations/0005_match_excluded.py`**
- `makemigrations replays -n match_excluded`.
- `AddField` que depende de `0004_roundplayer_opening_kill_traded`.
- Sin `RunPython`: el default `False` deja todo como esta.

**`backend/replays/analytics/aggregates.py`**

Los tres helpers van justo despues de `filtro_mapa` y **antes** de
`base_queryset`. Tienen que estar definidos ahi porque `_MI_EQUIPO` (~1911) se
evalua al cargar el modulo:

```python
def rondas_contables() -> QuerySet[RoundPlayer]:
    """Tus rondas que cuentan: sin las de partidas excluidas. Raiz de todo agregado."""
    return RoundPlayer.objects.filter(is_me=True, round__match__excluded=False)


def partidas_contables(*, incluir_excluidas: bool = False) -> QuerySet[Match]:
    """Unica raiz de Match en los agregados. `incluir_excluidas` es para lo que
    muestra partidas (listado, detalle), nunca para un numero."""
    return Match.objects.all() if incluir_excluidas else Match.objects.filter(excluded=False)


def _mia_en_la_ronda() -> QuerySet[RoundPlayer]:
    """Tu fila de una ronda, para correlacionar con OuterRef("round_id").

    Solo vale dentro de una consulta cuya ronda externa ya sale de
    `base_queryset`/`rondas_contables`: por eso no filtra excluidas, y asi el
    join round->match no se repite por cada evento en los duelos.
    """
    return RoundPlayer.objects.filter(is_me=True)
```

Inventario de consultas raiz. Las lineas son de dev fb431f7 y las verificaron
architect y critic.

| linea / funcion | cambio | motivo |
|---|---|---|
| 63 `base_queryset` | `qs = rondas_contables().select_related(...)` | raiz de casi todo: overview, by_*, clutch, duelos, trends, compare, data_health, player_profile, `_por_partida`, export |
| 143 `rating_baseline` | `rondas_contables().aggregate(...)`; el docstring dice "todo tu historial que cuenta" | es el 1.00: si no, una custom de 30 bajas mueve el rating de todo |
| 903 `comebacks`, 1025 `by_margin`, 1065 `matches_summary` | `rondas_contables().filter(round__match_id__in=...)` | ya derivan de ids contables; el cambio es para la guardia y el resultado no cambia |
| 1413-1415 `by_stack` (`mia`) | `rondas_contables().filter(round_id=OuterRef("round_id"), team_index=OuterRef("team_index"))` | los habituales (`MIN_PARTIDAS_HABITUAL=5`) se cuentan sin filtros y la raiz `companeros` no esta acotada: aca el join hace falta |
| 1911 `_MI_EQUIPO` y 2622 | `_mia_en_la_ronda().filter(round_id=OuterRef("round_id"))...` | son correlacionadas y sus consultas externas salen de `mine` (`_mis_bajas`, `_solo_rivales`, `_teamkills`, `repeated_rivals`, `_partidas_compartidas`, `kills_by_time`) |
| 551 `etiquetas_de_mapas` | firma `(slugs=None, *, incluir_excluidas=False)` y `partidas_contables(incluir_excluidas=...)` | el "(id N)" depende de las otras versiones del slug; la usan 1352, 1669 y 2446 sin el kwarg |
| 1779 `_sessions_raw` | `partidas_contables().order_by("played_at")` | **variante conservadora**: una excluida no ocupa posicion en su sesion ni une dos bloques; el docstring lo dice |
| 1963 `_me_ids` | nada | son ids de `Player`, no de partida |
| `Match.objects` con `pk__in`, `id__in` o `pk=` (442, 451, 898, 999, 1058, 1296, 1437, 2135) | nada | los ids ya salen de raices contables |

Lo demas es derivado y hereda la exclusion: `Exists` o `in` sobre
`base_queryset`, o correlacionado a una ronda que ya viene filtrada. Eso cubre
coach, export (`TABLES`), duelos, perfil de jugador y `data_health`.
`narrative.py` no consulta la base. Consecuencia visible: el perfil de un
jugador deja de listar la excluida en "Partidas compartidas", igual que si no
estuviera importada.

**`backend/replays/views.py`**
- Vista nueva `match_exclude`, junto a `match_detail`. Mismo orden que
  `player_ubisoft` (`views.py:307-320`): primero el JSON (415), despues el 404,
  despues el 400.

  ```python
  @csrf_exempt
  @require_POST
  def match_exclude(request: HttpRequest, pk: int) -> JsonResponse:
      """Saca o devuelve una partida de todos los agregados. No borra nada."""
      if not _es_json(request):
          return _ok({"error": "se esperaba application/json"}, status=415)
      if not Match.objects.filter(pk=pk).exists():
          raise Http404("partida no encontrada")
      try:
          body = json.loads(request.body or b"{}")
      except (ValueError, UnicodeDecodeError):
          body = None
      excluded = body.get("excluded") if isinstance(body, dict) else None
      if not isinstance(excluded, bool):
          return _ok({"error": "excluded tiene que ser true o false"}, status=400)
      # update y no save: save tocaria parsed_at (auto_now), que dice cuando se parseo
      Match.objects.filter(pk=pk).update(excluded=excluded)
      return _ok({"id": pk, "excluded": excluded})
  ```

  Si `views.py` no importa `json` o `csrf_exempt`, se importan como lo hacen
  `save_overrides` y `app_settings`.
- `_es_json` (111-119): el docstring suma `/api/matches/<id>/exclude/`.
- `filter_options` (193, `match_types`) y `_opciones_de_mapa` (156) pasan a
  `agg.partidas_contables()`. Son la barra de filtros de los agregados: una
  opcion que solo tiene la excluida daria un filtro vacio.
- `match_list`:
  - sigue con `Match.objects.all()` (398): la excluida se lista;
  - cada fila suma `"excluded": match.excluded`;
  - 426 pasa a `etiquetas_de_mapas(..., incluir_excluidas=True)`;
  - `my_rating` (410) se divide por el baseline contable, y eso es lo correcto;
  - sin filtro `?excluded=`.
- `match_detail`:
  - 538 pasa a
    `agg.totals(RoundPlayer.objects.filter(is_me=True, round__match=match))`,
    con el comentario "la partida se muestra completa aunque este excluida";
  - 539 pasa a `incluir_excluidas=True`;
  - el dict `match` suma `"excluded"`.
- `health` (141-142), `_catalogo_operadores` (234) e `import_status` no
  cambian: son inventario y catalogo.

**`backend/replays/urls.py`**: `path("matches/<int:pk>/exclude/", views.match_exclude, name="match-exclude")`.

**`backend/replays/ingest.py:156`**: comentario en `defaults`: "no agregar
`excluded`: una reimportacion no puede devolver a tus numeros una partida que
sacaste". Con `force=True`, `update_or_create` conserva el pk y la columna;
solo se borran las rondas (178). `recompute.py:136`
(`bulk_update(["won"])`) y `retag` no la tocan.

**`backend/tests/factories.py`**: `make_match(..., excluded=False)`.

**`frontend/src/pages/MatchDetail.jsx`**
- La linea 24 desestructura tambien `reload`, que `useApi` ya devuelve
  (`api.js:75`).
- `async function alternarExclusion()` llama a
  `post(\`/matches/${id}/exclude/\`, undefined, { excluded: !match.excluded })`
  y despues a `reload()`. `post(path, params, body)` esta en `api.js:26`.
- Si falla, el mensaje va a un `useState` y se muestra en
  `<span className="note">`, sin `console.error`.
- Boton `className="btn small"` antes de "Copiar resumen", con el texto
  `match.excluded ? 'Volver a contarla' : 'Excluir de mis números'`.
- Si esta excluida:
  - `<p className="note">Esta partida no cuenta en tus números.</p>` bajo la
    fecha;
  - `<span className="chip">excluida</span>` junto a `ResultChip`.

**`frontend/e2e/partidas-excluidas.spec.js`** (nuevo). Va en su propio
archivo para correr despues de `humo` (orden alfabetico) y no ensuciar sus
numeros.

**`CLAUDE.md`** y **`docs/metricas.md`**: los textos de abajo.

### Orden de implementacion

1. Modelo, migracion y `make_match(excluded=)`. La suite tiene que quedar en
   verde sin otros cambios.
2. Helpers y el inventario de `aggregates.py`, fila por fila. Revisar
   `tests/test_mapa_de_la_partida.py` y los demas llamadores de
   `etiquetas_de_mapas`: el kwarg es keyword-only y su default excluye.
3. `views.py`, `urls.py` y el comentario de `ingest.py`.
4. `backend/tests/test_excluir_partida.py`, con la suite en verde.
5. `MatchDetail.jsx`; correr `npm run build` y `npm test`.
6. El e2e y los docs; `check.sh` completo.

### Tests (`backend/tests/test_excluir_partida.py`)

Helpers del archivo:
- `_normalizar(obj)` redondea recursivamente los floats a 9 decimales. Absorbe
  diferencias de ultimo bit por el orden del JOIN y sigue atrapando cualquier
  cambio real.
- `_sin_rating(obj)` quita recursivamente la clave `"rating"`.

**`ExcluirPartidaPostTests`**
- `test_sin_json_da_415`: con form-data da 415 y la marca sigue en False.
- `test_partida_inexistente_da_404`.
- `test_json_sin_booleano_da_400`: `{}`, `{"excluded": "si"}` y un cuerpo que
  no es JSON.
- `test_get_no_esta_permitido`: 405.
- `test_excluir_y_volver_a_incluir_cambia_la_marca`: la respuesta es
  `{"id", "excluded"}`.
- `test_excluir_no_toca_parsed_at`.

**`ExcluidaIgualQueSinImportarTests`**

La partida X esta armada para tocar cada raiz:
- un rating muy alto;
- `played_at` a 100 minutos de la anterior y a 100 de la siguiente, con
  `SESSION_GAP_MINUTES=120`, asi une dos sesiones;
- un `map_id` unico dentro de un slug compartido;
- `match_type` "Custom", que solo tiene X;
- un compañero que llega a 5 partidas gracias a X;
- un rival repetido y un clutch.

Se guardan las respuestas con X excluida, despues `X.delete()`, se guardan de
nuevo y se afirma `assertEqual(_normalizar(a), _normalizar(b))`.

- `test_cada_get_agregado_da_lo_mismo_que_sin_la_partida`:
  - recorre `COMPARADAS`: filters, overview, coach, operators, trends,
    teammates, duels, sessions, compare `by=matches` y `by=days`, y
    `players/<id>` de cada compañero y rival;
  - repite overview y trends con `?session=0` y con `?map=<slug>&side=Attack`;
  - el docstring dice que esta comparacion cubre las raices de agregados de
    `views.py`, que la guardia estatica no mira.
- `test_cada_tabla_del_csv_da_lo_mismo_que_sin_la_partida`: `/api/export/?table=<clave>`
  para cada clave de `export.TABLES`, incluida `matches` (`trend_by_match`),
  que **si** excluye.
- `test_toda_ruta_esta_clasificada`: los `name` de `replays.urls.urlpatterns`
  tienen que ser exactamente la union disjunta de tres grupos. Una ruta nueva
  sin clasificar hace fallar el test.
  - `COMPARADAS`, con `export` incluido.
  - `NO_AGREGADOS`, cada uno con su motivo en un comentario: `health`
    (inventario), `operator-catalog` (catalogo del parser), `match-list` y
    `match-detail` (muestran la partida), `unknown` (etiquetado), `settings`
    (configuracion, GET y POST) e `import-status` e `import-progress`
    (inventario y estado del job).
  - `SOLO_POST`: `player-ubisoft`, `overrides`, `backup`, `import` y
    `match-exclude`. Para cada uno se afirma que un GET da 405.

**`ExcluidaSigueVisibleTests`**
- `test_sigue_en_el_listado_marcada`: `"excluded": true` y el `total` no
  cambia.
- `test_el_my_rating_de_una_excluida_se_mide_contra_el_baseline_contable`:
  afirma `my_rating == round(promedio de X / agg.rating_baseline(), 2)` y que
  difiere del valor que daria con X dentro del baseline.
- `test_el_detalle_de_una_excluida_sigue_completo`:
  - en `my_totals`, `rounds`, `rounds_won`, `kills`, `deaths`, `headshots`,
    `opening_kills` y `opening_deaths` iguales antes y despues de excluir;
  - `rounds` y `scoreboard` iguales despues de `_sin_rating`;
  - `match.excluded` en True;
  - `match.map` con su etiqueta de version.
- `test_health_cuenta_todas_las_importadas`.

**`IdaYVueltaTests`**
- `test_volver_a_incluirla_deja_los_agregados_exactamente_como_antes`: mismo
  set de rutas y tablas.

**`ReimportarConservaLaMarcaTests`**
- `test_reimportar_con_force_no_pierde_la_marca`: patron de
  `tests/test_ingest.py:158-172` (`mock.patch("replays.ingest.MatchReader")` y
  `_ronda`). Importa, marca, reimporta con `force=True` y afirma
  `excluded is True` y el mismo pk.

**`GuardiaEstaticaTests`** (`ast` sobre `replays/analytics/aggregates.py`)
- `test_tus_rondas_salen_de_rondas_contables`:
  - recorre cada `ast.Call` y baja por `Call.func` y `Attribute.value` hasta
    la raiz de la cadena, asi `RoundPlayer.objects.select_related(...).filter(is_me=True)`
    tampoco se escapa;
  - si la raiz es `RoundPlayer.objects` y algun eslabon lleva el keyword
    `is_me` o `player__is_me`, o un `Q(is_me=...)`, la funcion que la contiene
    (pila de `FunctionDef`) tiene que ser `rondas_contables` o
    `_mia_en_la_ronda`;
  - a nivel de modulo falla;
  - `Player.objects` (`_me_ids`) no entra.
- `test_las_partidas_salen_de_partidas_contables`: todo `Match.objects.<metodo>(...)`
  fuera de `partidas_contables` tiene que empezar con un `filter` que lleve
  `id__in` o `pk__in`, o con un `get` que lleve `pk`.
- El docstring dice que la guardia es secundaria.

**Vitest:** ninguno. No hay logica pura nueva: el texto del boton es un
ternario.

**e2e `frontend/e2e/partidas-excluidas.spec.js`**

El comentario de cabecera explica por que puede postear sin reiniciar la base:
`workers: 1`, `fullyParallel: false` y `retries: 0` (`playwright.config.js`),
y `servidor.js:51-52` rehace la base una sola vez por corrida. `ruleta.spec.js`
corre despues y no depende de la partida, porque `_catalogo_operadores` no
filtra.

- `let partidaId = null`.
- `test.afterEach`: si `partidaId == null`, sale. Si no, hace
  `request.post(\`/api/matches/${partidaId}/exclude/\`, { headers: { 'Content-Type': 'application/json' }, data: { excluded: false } })`.
  Es idempotente.
- Test `excluir y volver a contar una partida no ensucia la consola`, con
  `vigilarConsola(page)`:
  1. El id sale de `request.get('/api/matches/?limit=1')`.
  2. En `/` se ve "203 rondas en 29 partidas" (mismo locator que
     `humo.spec.js:514`).
  3. En el detalle, clic en "Excluir de mis números": aparecen "Volver a
     contarla" y el aviso.
  4. En `/` se ve "196 rondas en 28 partidas" (`RONDAS_POR_PARTIDA = 7`,
     `seed_demo.py:56`).
  5. En el detalle, clic en "Volver a contarla"; en `/`, otra vez 203/29.
  6. `expect(errores).toEqual([])`.

`seed_demo` no cambia, asi que ningun numero que ya afirma el e2e se mueve.

### Que puede romperse

- **Indices de `?session=`.** Si la excluida unia dos bloques, la sesion se
  parte en dos y los indices de las sesiones mas viejas se corren. Un filtro de
  sesion guardado en la URL pasa a apuntar a otra. Aceptado y documentado.
- **Barra de filtros.** Puede quedar con opciones viejas hasta recargar la
  pagina. Menor.
- **Rating por partida.** El `my_rating` de cada fila de Partidas y el rating
  del detalle se miden contra el 1.00 de las partidas que cuentan, asi que
  cambian un poco al excluir otra partida. Es correcto y documentado.
- **Etiqueta de version** (la tension del architect). Si la excluida era la
  unica partida de su version, los agregados dicen "Bank" y Partidas y el
  detalle dicen "Bank (id N)". Ademas esa version sale del selector.
  Documentado.
- **Invariante de `_mia_en_la_ronda`.** Un uso futuro de `_MI_EQUIPO` desde una
  raiz que no sea contable contaria la excluida, y la guardia no lo ve. Lo dice
  su docstring; la comparacion lo atrapa si la ruta esta en `COMPARADAS`.
- `Player.first_seen` y `last_seen` no se recalculan, pero no son metricas.

### Verificacion manual en el PC

1. Hacer un respaldo: Ajustes → copia, o `manage.py backup`.
2. Correr `manage.py migrate` y comprobar con `showmigrations replays` que
   `0005_match_excluded` quedo aplicada.
3. Anotar K/D, rating y la cantidad de partidas del Inicio. Excluir una custom
   desde su detalle y comprobar:
   - que esos numeros cambian;
   - que el detalle sigue completo;
   - que la partida sigue en Partidas.
4. "Volver a contarla" y comparar contra lo anotado.
5. Correr `import_replays --force` con la partida excluida: la marca sigue.
6. Para volver atras: `migrate replays 0004` o restaurar la copia.

### Textos exactos

**`CLAUDE.md`, la lista de POST** (lineas 74-78) queda asi:

```
- **La API es de lectura.** Vistas planas con `JsonResponse`. Los POST son
  pocos y locales: `/api/import/`, `/api/overrides/`,
  `/api/players/<id>/ubisoft/`, `/api/settings/`, `/api/backup/` y
  `/api/matches/<id>/exclude/`; todos exigen `application/json`, asi otra
  pagina abierta en el navegador no puede dispararlos. No agregues serializers
  ni viewsets.
```

**`CLAUDE.md`, regla nueva** despues de "Las metricas se calculan al importar":

```
- **Una partida excluida no cuenta en nada.** En `analytics/aggregates.py` tus
  rondas salen de `rondas_contables()` y las partidas de `partidas_contables()`;
  `test_excluir_partida.py` compara cada ruta y cada CSV contra la base sin la
  partida y falla si aparece una ruta sin clasificar.
```

**`docs/metricas.md`, al final de la intro** (despues de la linea 5):

```
**Partidas excluidas.** Una partida marcada con "Excluir de mis números" (en su
detalle) no cuenta en ninguna metrica de este documento ni en los CSV de
agregados (incluido el "por partida"): ni en el 1.00 del rating, ni en los
companeros habituales, ni en las sesiones, ni en las opciones de los filtros.
Es como si no estuviera importada. Sigue en la pagina Partidas (y en el CSV que
baja su boton), en su detalle y en el conteo de importadas; un clic la vuelve a
contar y nada se borra. Dos efectos a la vista: su detalle y su fila en
Partidas miden el rating contra el 1.00 de las que cuentan, y si era la unica
partida de una version de mapa, los agregados muestran el mapa sin "(id N)"
mientras Partidas y el detalle lo siguen desambiguando (y esa version sale del
selector de filtros).
```

**`docs/metricas.md`, seccion Sesiones** (empieza en la linea 113), despues de
"...tercera de su noche.":

```
Las partidas excluidas no entran al corte: no ocupan posicion y no unen dos
bloques, asi que excluir la que los juntaba parte la sesion en dos.
```

**PR.** Un parrafo propio para el humano: "Cambia reglas de `CLAUDE.md`: suma
el POST `/api/matches/<id>/exclude/` (autorizado el 2026-11-05) y la regla de
raices contables."

Skills: no aplica. El repo ya tiene el patron de migracion de una columna
(0003, 0004), de POST con `_es_json` y de e2e con `vigilarConsola`.
Arena: no. La eleccion entre A, B y C salio del plan por consenso, que las
compara.

OMC: plan=APPROVE (ronda 2; ronda 1 ITERATE: guardia estatica imposible por `_me_ids` y `etiquetas_de_mapas(incluir_excluidas)`, resueltas) · revisión=— · verificación=—

## Implementacion

## Revision

## QA

## Verificar en el PC

(Trae migracion: `manage.py backup` y `migrate` en el PC.)

## Para el humano

- (po) Variante conservadora elegida: la partida excluida sale de **todos**
  los agregados pero sigue en Partidas, en su detalle y en el CSV de
  partidas. Reversible con un clic; la migracion solo agrega una columna con
  default `False`. Si preferis que tambien salga del listado, decilo.
- (arquitecto 20261105T0349Z-cCqeUqM) Partida en dos tramos: esta (backend, boton, e2e, docs) y la 83 (chip en Partidas, lista en Datos). Variante conservadora en sesiones: la excluida no ocupa posicion ni une dos bloques (como si no estuviera importada), asi que excluir la que unia dos bloques parte la sesion. Si preferis que siga contando para el corte de sesiones, decilo en la ficha. El PR cambia `CLAUDE.md` (POST nuevo y regla de raices contables): lo dice en un parrafo propio. Abierto: si la topbar deberia sumar "· N excluidas" (fuera de alcance).
