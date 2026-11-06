# 100. Modo de juego como dimension

estado: en curso 2026-11-06
candado: -
rama: claude/equipo-dev/100-modo-de-juego-como-dimension
tipo: funcionalidad
epica: temporada-y-modo
area: fullstack
prioridad: 3
fuente: A7 de ALCANCE.md; sigue a la ficha 77 (selector de tipo de partida) y a la 96 (filtros en la URL)
archivos: backend/replays/analytics/aggregates.py, backend/replays/views.py, frontend/src/modoDeJuego.js, frontend/src/modoDeJuego.test.js, frontend/src/components/Filters.jsx, frontend/src/filtrosUrl.js, frontend/src/filtrosUrl.test.js, frontend/src/pages/Trends.jsx, backend/tests/test_modo_de_juego.py, frontend/e2e/modo-de-juego.spec.js, docs/metricas.md
turnos: po 20261106T0319Z-cqz8j6p, arquitecto 20261106T0438Z-c2U4Qx9

## PR

(La escribe el Release manager al final.)

## Que gana quien usa la app

En partidas rapidas y no clasificatorias se juega Bomba, Rehen y Area
segura, y hoy todo se mezcla: los sitios, el winrate de ataque y la duracion
de las rondas de Bomba suman rondas de Rehen. Con un selector "Modo" en la
barra y una tabla "Por modo" en Tendencias se separa el modo que te va bien
del que no.

## Criterios de aceptacion

- [ ] `_filters` acepta `gamemode` (texto, como `match_type`) y
      `base_queryset` y `match_queryset` filtran por `Match.gamemode`; un
      modo que no existe da listas vacias y 200, no 500. Test con una partida
      `Bomb` y una `Hostage`: `/api/overview/?gamemode=Hostage` cuenta solo
      las rondas de la segunda.
- [ ] `GET /api/filters/` devuelve `gamemodes` (los valores presentes,
      ordenados, sin vacios) y la barra muestra el selector "Modo" con
      "Todos" y nombres en castellano para los conocidos (Bomba, Rehén, Área
      segura, Bomba rápida; un `Unknown(...)` sale tal cual). Con un solo
      modo en la base el selector no aparece. Vitest de la funcion que arma
      las opciones.
- [ ] `gamemode` entra a `CLAVES_DE_URL` de `filtrosUrl.js` (ficha 96), con
      la misma validacion de texto que `match_type`. Vitest: la query
      `?gamemode=Hostage` sobrevive ida y vuelta.
- [ ] `GET /api/trends/` agrega `by_gamemode`: por modo, partidas,
      winrate de partida (`won=None` fuera del %), winrate de ronda, K/D y
      rating con `derive`; Tendencias lo muestra en una tabla "Por modo"
      solo si hay mas de un modo. Test con los numeros a mano.
- [ ] El e2e cambia el selector de modo con `seed_demo` (si el seed tiene
      un solo modo, el Arquitecto decide si suma una partida de otro modo y
      ajusta los numeros que afirman las pruebas) y la consola queda limpia.

## Fuera de alcance

- Reglas propias por modo (sitios de Rehen, condicion de victoria de Area
  segura): el corte es solo de filtro y tabla.
- Temporada como dimension (A3): idea aparte.
- Cambiar el selector "Tipo" (ficha 77).
- Coordinar con la ficha 79 (PR #81, espera al humano), que tambien toca
  `base_queryset` y `match_queryset`: orden de merge, no decision.

## Diseno

Revisado contra `origin/dev@f0444b5`. Una sola forma obvia: copia el camino
del selector "Tipo" (ficha 77) y la fila por grupo de `by_stack` (ficha 54).
Sin migracion, sin `recompute`, sin parser: `Match.gamemode` ya existe
(`models.py:80`) y `ingest.py:166` lo llena con el nombre de
`pydissect/constants.py:GAME_MODES` (`Bomb`, `SecureArea`, `Hostage`,
`QuickMatchBomb`) o `Unknown(<id>)`. Sin arena ni consenso (chica, de una
forma, reversible). Sin cambio de `seed_demo`: el e2e mete el segundo modo
interceptando la API, como ya hace el de la 77 con `Unranked`
(`humo.spec.js:931`), asi ningun numero que afirman las pruebas se mueve.

### Backend

1. `backend/replays/analytics/aggregates.py`
   - `FILTER_KEYS`: agregar `"gamemode"` despues de `"match_type"`.
   - `base_queryset`: `if filters.get("gamemode"): qs = qs.filter(round__match__gamemode=filters["gamemode"])`,
     justo debajo del de `match_type`.
   - `match_queryset`: `if filters.get("gamemode"): qs = qs.filter(gamemode=filters["gamemode"])`,
     idem. Un modo inexistente da querysets vacios: el 200 sale solo.
   - Funcion nueva `by_gamemode(**filters) -> list[dict]`, al lado de
     `by_start_side` (misma familia: dato de la partida, no de la ronda).
     Calco de `by_stack` sin los habituales:
     ```python
     por_partida = _por_partida(**filters)
     datos = dict(Match.objects.filter(id__in=list(por_partida)).values_list("id", "gamemode"))
     won = dict(Match.objects.filter(id__in=list(por_partida)).values_list("id", "won"))
     baseline = rating_baseline()
     grupos: dict[str, list[int]] = {}
     for mid in por_partida: grupos.setdefault(datos.get(mid) or "", []).append(mid)
     ```
     (una sola query con `values_list("id", "gamemode", "won")` esta bien
     tambien.) Por grupo: `t = _fold([por_partida[m] for m in mids], baseline)`
     y la fila
     `{"gamemode", "matches", "matches_decided", "matches_won", "match_winrate", "rounds", "rounds_won", "winrate", "kd", "rating"}`
     con `match_winrate = _pct(ganadas, decididas)` sobre `won is not None`
     (como `by_stack`). Orden: `-matches`, despues `gamemode`. El modo vacio
     (`""`, partidas viejas sin cabecera de modo) sale como su propia fila con
     `gamemode: ""`; la UI lo llama "Sin modo". Ojo con el `IN`: `por_partida`
     puede tener cientos de ids; mismo patron que `by_stack` (`id__in` sobre
     una lista de ids de partidas, no de rondas), aceptado ahi.
     Docstring: el modo es de la partida; con filtro de lado, el winrate de
     partida sigue siendo el de la partida entera, como `by_start_side`.
2. `backend/replays/views.py`
   - `_filters`: agregar `"gamemode"` a la tupla de claves de texto
     (`views.py:59`).
   - `filter_options`: `"gamemodes": sorted({g for g in Match.objects.values_list("gamemode", flat=True).distinct() if g})`,
     al lado de `match_types`.
   - `trends`: `"by_gamemode": agg.by_gamemode(**filters)`.

### Frontend

3. `frontend/src/modoDeJuego.js` (nuevo, logica pura, para vitest):
   - `NOMBRES_DE_MODO = { Bomb: 'Bomba', Hostage: 'Rehén', SecureArea: 'Área segura', QuickMatchBomb: 'Bomba rápida' }`.
   - `nombreDeModo(modo)`: el nombre en castellano; `''` -> `'Sin modo'`;
     cualquier otro (incluido `Unknown(123)`) tal cual.
   - `opcionesDeModo(gamemodes)`: `[{value:'', label:'Todos'}, ...]`, sin
     vacios ni repetidos, en el orden de la API, label con `nombreDeModo`.
     Mismo contrato que `opcionesDeTipo` de `tipoPartida.js`.
   - `mostrarSelectorDeModo(gamemodes, elegido)`: `true` si hay 2 o mas
     modos distintos **o** si hay uno elegido (un enlace con `?gamemode=X`
     y una base de un solo modo tiene que mostrar que esta filtrando, si no el
     usuario ve 0 rondas sin selector que lo explique).
   - `filasPorModo(byGamemode)`: agrega `modo: nombreDeModo(row.gamemode)` a
     cada fila; `hayVariosModos(byGamemode)`: `(byGamemode ?? []).length > 1`.
4. `frontend/src/components/Filters.jsx`: `<label>Modo <select>` despues de
   "Tipo", `value={value.gamemode || ''}`, `onChange={set('gamemode')}`,
   opciones de `opcionesDeModo(data?.gamemodes)`, renderizado solo si
   `mostrarSelectorDeModo(data?.gamemodes, value.gamemode)`. "Limpiar" ya lo
   cubre (`hayFiltros`).
5. `frontend/src/filtrosUrl.js`: `'gamemode'` en `CLAVES_DE_URL` despues de
   `'match_type'`. Cae en el `default` de `validar` (texto de hasta 64): la
   misma validacion que `match_type`, nada que agregar al switch.
6. `frontend/src/pages/Trends.jsx`: Panel nuevo `title="Por modo"` con
   `hint="Partidas, rondas y rendimiento en cada modo de juego. Las partidas sin resultado no entran en Ganadas."`,
   **inmediatamente antes** del Panel "Por hora del día" (linea ~910 en
   dev), renderizado solo si `hayVariosModos(data.by_gamemode)`. `DataTable`
   con columnas `modo` (left, "Modo"), `matches` ("Partidas"),
   `match_winrate` ("Ganadas", `%`, help "Partidas ganadas sobre las que
   tienen resultado."), `winrate` ("Rondas ganadas", `%`), `kd` ("K/D", 2
   digitos), `rating` ("Rating", 2 digitos), `rowKey={(r) => r.gamemode || 'sin-modo'}`,
   `csvName="por-modo"`, `initialSort={{ key: 'matches', dir: 'desc' }}`.
   Se elige ese lugar y no junto a "Por mitad" porque las ramas 98 y 99
   tocan Trends.jsx en las lineas 18-21, 229-265, 468-516 y 678-700: abajo
   de 900 no choca con ninguna.

### Tests

- `backend/tests/test_modo_de_juego.py` (nuevo), `ModoDeJuegoTests` con
  `make_match(gamemode=...)` (la factory ya lo acepta): una `Bomb` de 3
  rondas ganada 3-0, una `Bomb` de 2 rondas perdida 0-2 (`my_score=0,
  opponent_score=2`) y una `Hostage` de 2 rondas; kills a mano.
  - `test_filtrar_por_hostage_cuenta_solo_sus_rondas` (`/api/overview/?gamemode=Hostage` -> 2 rondas; sin filtro -> 7).
  - `test_un_modo_que_no_existe_da_cero_rondas_y_no_500` (overview, trends, matches con `?gamemode=Nada`: 200 y 0).
  - `test_el_listado_de_partidas_respeta_el_modo` (lo que usa `match_queryset`: `GET /api/matches/`, `views.py:415`, con `?gamemode=Bomb` devuelve 2).
  - `test_las_opciones_listan_cada_modo_una_vez_sin_vacios` (con una partida `gamemode=""` extra: `["Bomb", "Hostage"]`).
  - `test_por_modo_suma_partidas_winrate_y_rating_por_modo`: `by_gamemode` con los numeros a mano (Bomb: 2 partidas, 1 de 2 ganadas = 50.0, rondas 5; Hostage: 1 partida); `rating` igual al de `agg.overview(gamemode="Bomb")["overall"]["rating"]`.
  - `test_por_modo_deja_fuera_del_porcentaje_las_partidas_sin_resultado` (una `won=None`: cuenta en `matches`, no en `matches_decided`).
  - `test_por_modo_con_filtro_de_lado_mantiene_el_resultado_de_la_partida`.
- `frontend/src/modoDeJuego.test.js`: `opcionesDeModo` (castellano, `Unknown(9)` tal cual, sin vacios ni repetidos, "Todos" primero); `mostrarSelectorDeModo` (1 modo -> false, 2 -> true, 1 modo y elegido -> true); `nombreDeModo('')` -> "Sin modo".
- `frontend/src/filtrosUrl.test.js`: un caso nuevo, `?gamemode=Hostage` ida y vuelta, y uno de 65 caracteres descartado.
- `frontend/e2e/modo-de-juego.spec.js` (nuevo, archivo propio para no chocar con `humo.spec.js`, que tocan 98 y 99): con `page.route('**/api/filters/**')` agrega `'Hostage'` a `gamemodes` (el seed es todo `Bomb`): el selector "Modo" aparece con "Rehén"; elegirlo dispara `/api/overview/?...gamemode=Hostage`, la URL lleva `gamemode=Hostage` y la pagina muestra el estado de 0 rondas filtradas; "Limpiar" lo saca. Segundo test: Tendencias sin intercepcion **no** muestra "Por modo" (un solo modo); con `page.route('**/api/trends/**')` sumando una fila `Hostage` a `by_gamemode`, el panel "Por modo" aparece con "Bomba" y "Rehén". Los dos con la consola limpia (`consola.js`, como el resto).

### Orden de implementacion

backend (aggregates -> views -> test_modo_de_juego) -> `modoDeJuego.js` y su
vitest -> `filtrosUrl.js` -> `Filters.jsx` -> `Trends.jsx` -> `metricas.md` ->
e2e -> `verificar.sh`.

### docs/metricas.md

Seccion nueva `## Modo de juego` despues de `## Mitades y prorroga`, una tabla:

| Metrica | Definicion |
|---|---|
| **Por modo** | Tus partidas agrupadas por el modo de la cabecera del `.rec` (Bomba, Rehén, Área segura, Bomba rápida; un id que el parser no conoce sale como `Unknown(<id>)`, y una partida sin modo como "Sin modo"). Partidas = partidas con alguna ronda tuya que pasa los filtros. Ganadas = partidas ganadas sobre las que tienen resultado; se lee de la partida entera, como "Lado inicial". Rondas ganadas, K/D y rating: las de siempre sobre las rondas de ese modo. |

`## Base` no describe los filtros de la barra; no se agrega nada ahi.

### Que puede romperse

- Conflicto de texto con ramas abiertas: 79 (PR #81, espera al humano) toca
  `base_queryset`, `match_queryset` y `views.py`; 98 y 99 tocan
  `aggregates.py`, `Trends.jsx` y `metricas.md`. Son lineas distintas, pero
  **Implementar despues de que #98 y #99 se mergeen** (prioriza, no
  bloquea; las dos estan `implementado`). Con 79 no se espera: espera al
  humano y el choque, si lo hay, es de dos `if` contiguos.
- `CLAVES_DE_URL` tiene orden fijo y la query sale canonica: un test de
  `filtrosUrl.test.js` que afirme la query entera con todas las claves puede
  necesitar la clave nueva. Correr vitest antes del e2e.
- Ningun numero existente cambia: sin `?gamemode` los querysets son los
  mismos. Nada que verificar en el PC (sin migracion, recompute, parser ni
  Electron).

### Verificacion manual

`manage.py seed_demo`, `runserver`; `curl -s localhost:8000/api/filters/ | python -m json.tool | grep -A2 gamemodes`
-> `["Bomb"]`; `curl -s "localhost:8000/api/overview/?gamemode=Hostage"` ->
`overall.rounds` 0 y 200; `curl -s localhost:8000/api/trends/ | python -c "import json,sys;print(json.load(sys.stdin)['by_gamemode'])"`
-> una fila `Bomb`. En la UI: con la base del seed no aparece el selector
"Modo" ni el panel "Por modo"; con `?gamemode=Hostage` en la URL el selector
aparece con "Rehén" elegido.

Skills: no aplica (filtro y tabla ya resueltos en el repo: `opcionesDeTipo`, `DataTable`, `by_stack`; sin busqueda).
OMC: plan=— · revisión=— · verificación=— (ficha chica de una forma, sin consenso)
