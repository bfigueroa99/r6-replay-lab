# 47. Modos y tipos de partida desconocidos en Datos

estado: aprobado
candado: -
rama: claude/equipo-dev/47-modos-desconocidos-en-datos
tipo: funcionalidad
epica: temporada-y-modo
area: fullstack
prioridad: 4
fuente: ALCANCE.md A2; candidato de `mercado/2026-09-13`. `gamemode_name` y `match_type_name` (`backend/pydissect/header.py:229-234`) devuelven `Unknown(<id>)` sin llamar a `record_unknown`, a diferencia de mapas y operadores
archivos: backend/pydissect/overrides.py, backend/pydissect/header.py, backend/replays/unknowns.py, backend/replays/retag.py, backend/replays/views.py, backend/replays/management/commands/unknown_ids.py, backend/tests/test_pydissect.py, backend/tests/test_unknowns.py, backend/tests/test_retag.py, backend/tests/factories.py, frontend/src/pages/Datos.jsx, frontend/e2e/humo.spec.js, README.md
turnos: po 20261014T1911Z, arquitecto 20261014T2311Z

## PR

(La escribe el Release manager al final.)

## Que gana quien usa la app

Cuando Ubisoft agrega un modo o un tipo de partida nuevo, hoy se ve como
`Unknown(123)` en Partidas y en los filtros, y no hay como arreglarlo
desde la app. Con esto aparecen en la seccion "Sin identificar" de Datos
junto a mapas y operadores, se les pone nombre ahi y las partidas ya
importadas toman el nombre sin reimportar.

## Criterios de aceptacion

- [ ] `pydissect/overrides.py` acepta las claves `gamemodes` y
      `match_types` en `overrides.json` (mismo formato que `maps`), y
      `gamemode_name` / `match_type_name` usan esa etiqueta antes de
      devolver `Unknown(...)`, y anotan el id con `record_unknown` cuando
      no la hay. `pydissect/` sigue sin importar Django (test del parser).
- [ ] `/api/unknown/` devuelve tambien los modos y tipos de partida sin
      nombre, cada uno con su id, cantidad de partidas, primera y ultima
      fecha, y la etiqueta pendiente si ya hay una en el JSON. Una base
      sin desconocidos devuelve listas vacias.
- [ ] `POST /api/overrides/` (el que ya existe, `application/json`) guarda
      etiquetas de modos y tipos; un id no numerico o una etiqueta vacia se
      rechaza igual que hoy para mapas. Un `overrides.json` viejo sin las
      claves nuevas sigue leyendose sin error.
- [ ] Despues de guardar, `retag.py` renombra `Match.gamemode` y
      `Match.match_type` de las partidas ya importadas (sin reimportar);
      test con una partida `Unknown(999)` que pasa a la etiqueta nueva.
      `Match` no guarda el id del modo ni del tipo (solo el texto, `models.py:55-56`):
      el id se lee del propio `Unknown(<id>)`, asi que no hace falta migracion;
      como en mapas, nunca se degrada una etiqueta buena a `Unknown`.
- [ ] Datos muestra las dos tablas nuevas en "Sin identificar" con su
      campo para nombrar; el e2e verifica que la pagina carga sin errores
      de consola sobre `seed_demo`.

## Fuera de alcance

- Reglas de match point para un modo nuevo (`reglas_partida.REGLAS`): un
  modo etiquetado sigue en `unknown` en Match point hasta que alguien
  agregue su regla en codigo.
- Selector de tipo de partida en la barra de filtros (A1, lo toca PR #14).
- Temporada como dimension (A3).

## Diseno

Arquitecto 20261014T2311Z, sobre `origin/main@f74a16f`. Pasa los filtros
duros: `pydissect/` sigue sin Django (la config llega por el mismo
`PYDISSECT_OVERRIDES` de hoy), sin red, sin dependencias, sin migracion.
El POST es el `/api/overrides/` que ya existe. No choca con PR #14 (el
selector de tipo en `Filters.jsx`): esta ficha no toca la barra.

**Limite asumido (variante conservadora):** `Match` guarda solo el texto
(`gamemode`, `match_type`, `models.py:55-56`), no el id. El id se lee del
propio texto `Unknown(<id>)`; una vez etiquetada, la partida ya no tiene
el id, asi que **cambiar despues una etiqueta mal puesta no reetiqueta lo
ya importado** (si se aplica a lo que se importe despues). La
alternativa, columnas `gamemode_id` y `match_type_id` con migracion y
`recompute`, queda en `## Para el humano`; no frena la ficha.

**Parser: `backend/pydissect/overrides.py`**
- `_cache` y `_unknown` pasan a tener cuatro claves: `maps`, `operators`,
  `gamemodes`, `match_types` (constante `CLAVES` de modulo, que usan
  `load` y el estado inicial). `load` las lee igual que `maps`; un JSON
  viejo sin las claves nuevas da dicts vacios. Docstring del modulo con el
  formato nuevo.
- `extra_gamemode(id)` y `extra_match_type(id)`, gemelas de `extra_map`.

**Parser: `backend/pydissect/header.py:229-234`**
- `match_type_name(i)`: `MATCH_TYPES.get(i) or extra_match_type(i)`; si
  no hay, `record_unknown("match_types", i)` y `Unknown(i)`. Igual
  `gamemode_name` con `"gamemodes"`. `record_unknown` ya ignora el 0.
  Importar las dos funciones nuevas junto a `extra_map`.

**Backend: `backend/replays/unknowns.py`**
- `read_overrides()` devuelve las cuatro claves; `write_overrides(maps,
  operators, gamemodes=None, match_types=None)` (keywords con default, asi
  `unknown_ids` y los tests viejos no cambian); `add_placeholders` igual
  con dos kwargs opcionales.
- Helper `_id_de_unknown(texto) -> int | None` con
  `re.fullmatch(r"Unknown\((\d+)\)", texto)`; `0` devuelve `None` (no se
  puede etiquetar, como `map_id=0`).
- `unknown_gamemodes()` y `unknown_match_types()`: sobre
  `Match.objects.filter(<campo>__startswith=UNKNOWN_PREFIX)`, agrupar por
  id en Python, filas `{"id", "label", "matches", "first_seen",
  "last_seen", "pending": overrides.extra_gamemode(id) or ""}` (mismo
  formato que `unknown_maps`, sin `sites`). Pista extra para el tipo:
  `"gamemodes": sorted(set(...))` de esas partidas; para el modo,
  `"match_types"` (lo que si se sabe ayuda a adivinar lo que no).
- Se puede compartir una funcion `_desconocidos_de_partida(campo, extra,
  pista)` para las dos; queda a criterio del Dev.

**Backend: `backend/replays/retag.py`**
- `_retag_texto(result, dry_run, campo, nombrar, kind)` llamada dos veces
  desde `retag()`: para `gamemode` con `gamemode_name` (kind `"modo"`) y
  para `match_type` con `match_type_name` (kind `"tipo de partida"`).
  Por cada valor distinto de `Match.<campo>` que empieza con `Unknown(`:
  sacar el id, `nombre = nombrar(id)`; si sigue siendo `Unknown`, saltar
  (nunca degrada); si no, `update(<campo>=nombre)` (o `count()` en
  `dry_run`), sumar a `result.matches` y anotar el `Change`. Nunca toca
  valores que no son `Unknown(...)`. Docstring del modulo: agregar que
  modo y tipo se leen del texto porque no hay id guardado.

**Backend: `backend/replays/views.py`**
- `unknown`: agrega `"gamemodes": unknowns.unknown_gamemodes()` y
  `"match_types": unknowns.unknown_match_types()`.
- `save_overrides`: `clean_labels` tambien sobre `payload.get(
  "gamemodes")` y `payload.get("match_types")`; el 400 de "no mandaste
  ninguna etiqueta" mira las cuatro; `write_overrides` con las cuatro;
  `"saved"` con las cuatro claves.
- `backend/replays/management/commands/unknown_ids.py`: dos bloques mas
  ("Modos sin nombre", "Tipos de partida sin nombre") y `--write` con los
  ids; el "Todo identificado" mira las cuatro listas.

**Frontend: `frontend/src/pages/Datos.jsx`**
- Estado `labels` con las cuatro claves; `pendientes` y el POST las
  incluyen; dos bloques mas dentro del `Panel` "Sin identificar", con el
  mismo `input` y la misma forma que mapas: "Modo de juego" (pista: tipos
  de partida vistos) y "Tipo de partida" (pista: modos vistos), con
  `plural(n, 'partida', 'partidas')` y `rango(row)`. La condicion del
  panel lleno pasa a mirar las cuatro listas. Textos con tildes ("Modo de
  juego", "Tipo de partida").

**Tests nuevos**
- `backend/tests/test_pydissect.py`: `test_modo_desconocido_usa_la_etiqueta_del_override`,
  `test_modo_desconocido_sin_etiqueta_queda_anotado` (`unknown_ids()` trae
  `gamemodes`), `test_tipo_de_partida_desconocido_queda_anotado`,
  `test_overrides_viejo_sin_claves_nuevas_se_lee` (escribir el JSON en un
  tmp y apuntar `PYDISSECT_OVERRIDES`, como los tests existentes de
  mapas). Hoy no hay test que verifique que `pydissect/` no importa
  Django: agregar `test_pydissect_no_importa_django` que recorre con `ast`
  los `.py` de `backend/pydissect/` y falla si alguno importa `django`
  (barato, y cubre el criterio de la ficha).
- `backend/tests/test_unknowns.py`: `test_modo_desconocido_lista_sus_partidas_y_fechas`,
  `test_tipo_desconocido_trae_los_modos_como_pista`,
  `test_unknown_0_no_se_lista`, `test_base_sin_desconocidos_da_listas_vacias`,
  `test_guardar_etiqueta_de_modo_y_reetiqueta`,
  `test_id_de_modo_no_numerico_da_400_y_no_escribe`,
  `test_solo_etiquetas_de_tipo_alcanza_para_guardar`.
- `backend/tests/test_retag.py`: `test_modo_unknown_999_pasa_a_la_etiqueta`,
  `test_tipo_unknown_pasa_a_la_etiqueta`,
  `test_no_toca_un_modo_que_ya_tenia_nombre`,
  `test_sin_etiqueta_el_modo_sigue_unknown`, `test_dry_run_no_escribe_el_modo`.
- `make_match` no recibe `gamemode`: agregar el kwarg `gamemode: str =
  "Bomb"` a `backend/tests/factories.py` (default igual al de hoy, no
  cambia ningun test existente).

**e2e:** `seed_demo` no tiene desconocidos y no se toca. El humo ya
recorre `/datos` sin errores de consola; agregar en
`frontend/e2e/humo.spec.js` un `test('Datos muestra Sin identificar sin
pendientes', ...)` que afirma el panel "Sin identificar" con su texto de
vacio, para que el render con las cuatro listas vacias quede cubierto.

**`docs/metricas.md`:** no hay numero nuevo. Si `docs/formato-rec.md` o el
README hablan de `overrides.json` con solo mapas y operadores, actualizar
el ejemplo (README seccion de overrides).

**Orden:** parser (overrides + header) y sus tests -> `unknowns.py` ->
`retag.py` -> vistas y comando -> Datos.jsx -> e2e -> docs -> `check.sh`.

**Que puede romperse:** el cache global de `overrides` entre tests (los
tests existentes llaman `overrides.load(force=True)` y `reset_unknown()`;
seguir ese patron). Un `overrides.json` del usuario con las claves viejas
tiene que seguir funcionando (test). Un modo etiquetado no gana regla de
match point (fuera de alcance, ya anotado).

**Verificacion manual:** con una base real, `manage.py shell -c "from
replays.models import Match; Match.objects.filter(pk=1).update(gamemode='Unknown(999)')"`,
abrir Datos, nombrarlo, guardar, y ver en Partidas el nombre nuevo.
`## Verificar en el PC`: `manage.py unknown_ids` y `manage.py retag
--dry-run` sobre la base real.

## Implementacion

## Revision

## QA

## Para el humano

- Arquitecto 20261014T2311Z (aviso, no frena): `Match` no guarda el id del
  modo ni del tipo, asi que una etiqueta puesta mal no se corrige sobre lo
  ya importado (solo sobre lo que se importe despues). Si se quiere poder
  corregirla, hace falta una ficha aparte con columnas `gamemode_id` y
  `match_type_id`, migracion y `recompute`.
