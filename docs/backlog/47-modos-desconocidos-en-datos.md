# 47. Modos y tipos de partida desconocidos en Datos

estado: propuesto
candado: arquitecto 2026-10-14T23:11Z
rama: -
tipo: funcionalidad
epica: temporada-y-modo
area: fullstack
prioridad: 4
fuente: ALCANCE.md A2; candidato de `mercado/2026-09-13`. `gamemode_name` y `match_type_name` (`backend/pydissect/header.py:229-234`) devuelven `Unknown(<id>)` sin llamar a `record_unknown`, a diferencia de mapas y operadores
archivos: -
turnos: po 20261014T1911Z

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

## Implementacion

## Revision

## QA

## Para el humano
