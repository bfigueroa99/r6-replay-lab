# 47. Modos y tipos de partida desconocidos en Datos

estado: entregado
candado: -
rama: claude/equipo-dev/47-modos-desconocidos-en-datos
tipo: funcionalidad
epica: temporada-y-modo
area: fullstack
prioridad: 4
fuente: ALCANCE.md A2; candidato de `mercado/2026-09-13`. `gamemode_name` y `match_type_name` (`backend/pydissect/header.py:229-234`) devuelven `Unknown(<id>)` sin llamar a `record_unknown`, a diferencia de mapas y operadores
archivos: backend/pydissect/overrides.py, backend/pydissect/header.py, backend/replays/unknowns.py, backend/replays/retag.py, backend/replays/views.py, backend/replays/management/commands/unknown_ids.py, backend/tests/test_pydissect.py, backend/tests/test_unknowns.py, backend/tests/test_retag.py, backend/tests/factories.py, frontend/src/pages/Datos.jsx, frontend/e2e/humo.spec.js, README.md
turnos: po 20261014T1911Z, arquitecto 20261014T2311Z, dev 20261015T0812Z, revisor 20261015T0912Z, qa 20261015T1012Z, release 20261015T1111Z

## PR

Titulo: `[equipo-dev][fullstack] Modos y tipos de partida desconocidos en Datos`

### Que cambia

Cuando Ubisoft agrega un modo o un tipo de partida nuevo y aparece como
`Unknown(<id>)`, ahora sale en Datos > "Sin identificar" junto a mapas y
operadores (con partidas, fechas y pista del otro campo), se le pone nombre
ahi y las partidas ya importadas lo toman sin reimportar. `overrides.json`
suma las claves `gamemodes` y `match_types`; `/api/unknown/`,
`POST /api/overrides/` y `manage.py unknown_ids` las manejan.

### Por que esto y no otra cosa

Ficha 47 (ALCANCE.md A2, candidato de `mercado/2026-09-13`): mapas y
operadores ya tenian este camino y modos/tipos no llamaban a
`record_unknown`. Sin migracion: el id sale del propio texto
`Unknown(<id>)`. Descartado: columnas `gamemode_id`/`match_type_id`
(migracion + recompute, ver Para el humano de la ficha).

### Como se probo

- `./scripts/check.sh` -> `Todo en verde.`: ruff ok, 629 tests backend, 86
  vitest, build ok, 36 e2e (sobre la rama con `origin/main@b3b33a6`, ya con
  la ficha 46).
- Tests nuevos: 6 en `test_pydissect.py` (etiqueta del override, anotado
  sin etiqueta, conocidos no se anotan, `pydissect` sin Django, JSON viejo),
  11 en `test_unknowns.py` (listas, pista, pendiente, base vacia,
  `Unknown(0)`, POST con 400 por id no numerico, guardar mapa no borra
  modos), 8 en `test_retag.py` (`Unknown(999)` pasa a la etiqueta, nunca
  degrada, dry run, misma partida cuenta una vez). e2e `Datos muestra Sin
  identificar sin pendientes` y `Datos lista modos y tipos de partida sin
  nombre`.
- QA: JSON viejo, base sembrada con modos y tipos desconocidos, `curl` al
  POST con ids y etiquetas borde, `unknown_ids --write`, `retag --dry-run`,
  UI real en Chromium sin errores de consola, chunk inicial sin cambio
  (186.80 kB), 4 mutaciones detectadas.

### Riesgos y lo que no entra

Toca el parser (`header.py`, `overrides.py`): verificar con `.rec` reales
(abajo). Una etiqueta puesta mal no se corrige sobre lo ya importado (no
hay id guardado). Fuera: reglas de match point para un modo nuevo,
selector de tipo de partida (PR #14), temporada como dimension (A3).

### Como probarlo en 2 minutos

```
cd backend; python manage.py seed_demo; python manage.py runserver
curl -s localhost:8000/api/unknown/
```

Esperado: JSON con `gamemodes` y `match_types` (vacias en `seed_demo`).
Abrir `http://localhost:8000/datos`: "Sin identificar" sin pendientes y sin
errores de consola.

#### Verificar en el PC

```powershell
cd backend; ..\.venv\Scripts\python.exe manage.py unknown_ids
cd backend; ..\.venv\Scripts\python.exe manage.py retag --dry-run
```

Sin error; si hay modos o tipos `Unknown(...)`, aparecen en la lista y en
Datos > Sin identificar.

### Para el humano

Nada que decidir. Avisos en la ficha: sin id guardado no se corrige una
etiqueta mal puesta; `POST /api/overrides/` no exige `application/json`
(preexistente, ficha 48 `propuesto`).

### Candidatos descubiertos

48 (bug, `propuesto` en `backlog`): POSTs sin JSON desde otra pagina.

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

## Diseno (resumen)

Arquitecto 20261014T2311Z: claves `gamemodes` y `match_types` en
`pydissect/overrides.py`; `gamemode_name`/`match_type_name` usan la etiqueta
o llaman a `record_unknown`; `unknowns.py` lista desde `Match.gamemode` y
`match_type`; `retag.py` reetiqueta leyendo el id del texto; dos bloques en
Datos. Detalle en `git log`.

## Implementacion

Dev 20261015T0812Z: todo el diseno, 25 tests y 2 e2e; README y
`docs/formato-rec.md`. Desvios: `read_overrides()` tolera un JSON que no es
objeto; por la revision ciega previa, `RetagResult.matches` cuenta partidas
unicas (antes contaba una vez por campo).

## Revision 2026-10-15 sobre 75d7e0c

Revisor 20261015T0912Z: revision ciega sin hallazgos, criterios cubiertos
por tests con nombre, largo de `Unknown(<id 64 bits>)` dentro de 32
confirmado. Veredicto: aprobar.

## QA 2026-10-15 sobre 2e02c03

QA 20261015T1012Z: `check.sh` verde (610, 35 e2e), JSON viejo, base
sembrada, POST con bordes (400 y 200 segun corresponde), comandos, UI real
sin errores, chunk sin cambio, mutaciones detectadas. Veredicto: `aprobado`.

## Verificar en el PC

Toca el parser (`header.py`, `overrides.py`). Sobre la base y los `.rec`
reales:

```powershell
cd backend; ..\.venv\Scripts\python.exe manage.py unknown_ids
cd backend; ..\.venv\Scripts\python.exe manage.py retag --dry-run
```

Esperado: sin error; si hay modos o tipos `Unknown(...)`, aparecen en la
lista y en Datos > Sin identificar.

## Para el humano

- Arquitecto 20261014T2311Z (aviso, no frena): `Match` no guarda el id del
  modo ni del tipo, asi que una etiqueta puesta mal no se corrige sobre lo
  ya importado (solo sobre lo que se importe despues). Si se quiere poder
  corregirla, hace falta una ficha aparte con columnas `gamemode_id` y
  `match_type_id`, migracion y `recompute`.
- QA 20261015T1012Z (aviso, no frena, preexistente en main): `POST
  /api/overrides/` no exige `application/json` (`_es_json` lo usan los POST
  de configuracion, este no): un `text/plain` desde cualquier pagina abierta
  en el navegador escribe `overrides.json` y reetiqueta. Con esta ficha
  tambien alcanza a modos y tipos. Queda como ficha `propuesto` tipo bug en
  `backlog`.
