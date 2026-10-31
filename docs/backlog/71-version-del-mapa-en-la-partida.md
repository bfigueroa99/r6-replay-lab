# 71. La partida dice que version del mapa se jugo

estado: en curso 2026-10-31
candado: dev 2026-10-31 21:36 UTC
rama: claude/equipo-dev/71-version-del-mapa-en-la-partida
tipo: funcionalidad
epica: temporada-y-modo
area: backend
prioridad: 2
fuente: idea A6 de `ALCANCE.md` ("Implementar despues de #70"; la 70 esta en `dev` desde 0fedc7b, PR #65). Fuera de alcance de la ficha 70: "listado, records, sesiones y detalle de partida". `etiqueta_de_version` (`pydissect/header.py:239`) y `etiquetas_de_version` (`replays/analytics/aggregates.py:481`) ya existen; `match_list` y `match_detail` (`replays/views.py:434` y `:543`) devuelven `map: match.map_name`
archivos: backend/replays/analytics/aggregates.py, backend/replays/views.py, backend/tests/test_mapa_de_la_partida.py, docs/metricas.md
turnos: po 20261030T1653Z, arquitecto 20261030T1652Z, dev 20261031T2135Z

## PR

(La escribe el Release manager al final.)

## Que gana quien usa la app

Desde la ficha 70, Mapas separa "Consulate (Y10)" de "Consulate (Y7)", pero
Partidas, el detalle de la partida y el resumen copiado siguen diciendo
"Consulate" a secas: no se sabe a que fila de Mapas suma cada partida. Con
esto la partida lleva el mismo nombre que su fila.

## Criterios de aceptacion

- [ ] `/api/matches/` devuelve en `map` la etiqueta con version para un mapa
      rehecho (`map_id` 418126004176, `ConsulateY10`: "Consulate (Y10)") y el
      nombre sin cambios para un mapa sin sufijo (Kanal) y para `map_id=0`.
      Test en `backend/tests/test_api.py`.
- [ ] `/api/matches/<id>/` devuelve la misma etiqueta en `map`. Test en
      `test_api.py`.
- [ ] Para la misma `(map_slug, map_id)`, la etiqueta del listado y del
      detalle es la misma que la fila de `by_map` (incluido el caso de un id
      que el usuario nombro en Datos igual que una version conocida, donde
      `etiquetas_de_version` le suma "(id N)"). Test que compara las dos
      salidas sobre partidas de dos versiones del mismo mapa.
- [ ] El resumen copiado (`frontend/src/resumenPartida.js:69`) arranca con
      la etiqueta. Hoy toma `match.map` del detalle, asi que alcanza con el
      criterio anterior: QA lo verifica copiando el resumen de una partida
      "(Y10)" sembrada con `factories`.
- [ ] Con `seed_demo` (todo `map_id=0`) el listado, el detalle y el e2e no
      cambian, y `?map=<slug>` y `?map=<map_id>` en `/api/matches/` filtran
      igual que antes.

## Fuera de alcance

- Records, Sesiones, el "mejor y peor mapa" del Inicio, Clutch por mapa y
  sitio, Progreso por mapa y Duelos: siguen por slug (idea A8 de
  `ALCANCE.md`).
- Filtro o etiqueta de temporada (A3).
- IDs de mapa que faltan en `MAPS` (ficha 73).
- Guardar la etiqueta en la base: se calcula al consultar, como en la 70.

## Diseno

Arquitecto 20261030T1652Z sobre `origin/dev@0fedc7b`. Filtros duros: pasa
(dato ya en `Match.map_id` y `MAPS`; sin red, sin dependencias, sin
migracion, ningun numero nuevo). Spike en el scratchpad, sin commitear: con
lo de abajo, sobre Consulate Y7, Y10, `379218689149`, un id 999 nombrado
"Consulate", Kanal y Club House con `map_id=0`, las etiquetas del listado
son exactamente las de `by_map()`, el detalle repite la del listado, el
listado hace 5 consultas (una mas que hoy, por pagina y no por fila) y
`test_api` y `test_export` siguen verdes. Skills: no aplica (el patron esta
en `etiquetas_de_version` y `_opciones_de_mapa`). Arena: no, una sola forma
obvia.

**No espera a la 68:** la 68 toca `test_api.py`; los tests de esta van en un
archivo nuevo (abajo), asi `archivos:` no pisa ninguna rama abierta y el Dev
la puede tomar ya. Los criterios dicen `test_api.py`: es el mismo cliente de
Django en otro archivo. `docs/metricas.md` tambien lo toca la 68, pero en
`## Base` (fila Partidas ganadas, linea 13) y esta en `## Cortes` (245):
git los junta sin conflicto, no hace falta esperar.

**La regla, una sola.** La etiqueta de una `(map_slug, map_id)` sale siempre
de `aggregates.etiquetas_de_version`, que ya usan Mapas (`_etiquetar`) y el
selector de filtros (`views._opciones_de_mapa`, sobre todas las partidas). El
"(id N)" depende de que otras versiones del slug existan, asi que no alcanza
con `etiqueta_de_version` de una fila sola: hay que mirar todas las partidas
del slug.

**Archivos** (y por que):
- `backend/replays/analytics/aggregates.py`: funcion nueva
  `etiquetas_de_mapas(slugs: Iterable[str] | None = None) -> dict[tuple[str, int], str]`
  junto a `etiquetas_de_version` (antes de `_etiquetar`, linea 499):
  `Match.objects.values("map_slug", "map_name", "map_id").distinct()`,
  filtrado por `map_slug__in` si vienen slugs, ordenado como
  `_opciones_de_mapa` (`map_name`, `map_id`), y `etiquetas_de_version` sobre
  eso. Filtrar por slug no cambia ninguna etiqueta: la desambiguacion es
  dentro del slug (`usos` cuenta `(slug, etiqueta)`). Docstring: por que
  mira todas las partidas del slug y no la fila.
- `backend/replays/views.py`:
  - `match_list`: despues de `page` (404) y antes del bucle, una consulta
    `etiquetas = agg.etiquetas_de_mapas({m.map_slug for m in page})`; en la
    fila (434), `"map": etiquetas.get((match.map_slug, match.map_id),
    match.map_name)` (el `get` cubre una partida borrada entre las dos
    consultas). `map_slug` queda igual.
  - `match_detail` (543): `"map"` con la misma expresion sobre
    `agg.etiquetas_de_mapas({match.map_slug})`.
  - `_opciones_de_mapa` no se toca: ya etiqueta sobre todas las partidas,
    que es lo mismo que hace la funcion nueva.
- Frontend: nada. `Matches.jsx` (columna `map`), `MatchDetail.jsx:53` y
  `resumenPartida.js:69` muestran `match.map` tal cual. Ninguna pagina usa
  `match.map` como clave ni como filtro (el filtro va por `map_slug`/`map_id`).
- `docs/metricas.md`: no hay numero nuevo, pero la fila **Mapa** de
  `## Cortes` (linea 245) enumera donde se separan las versiones; suma una
  frase despues de "...del Coach de mapa, sitio y spawn.": "Partidas, el
  detalle de la partida y su resumen copiado dicen la version con la misma
  etiqueta."

**Tests**, archivo nuevo `backend/tests/test_mapa_de_la_partida.py`
(`TestCase`, `self.client`), setUp con `make_match` + `make_round` +
`make_round_player` para Consulate `2609221242` y `418126004176`, Kanal
`1460220617` y Club House `map_id=0` (criterios 1, 2 y 5):
- `test_el_listado_dice_la_version_del_mapa`: en `/api/matches/`, Y10 ->
  "Consulate (Y10)", Y7 -> "Consulate (Y7)", Kanal -> "Kanal", Club House
  -> "Club House" (por `id`, no por posicion).
- `test_el_detalle_dice_la_version_del_mapa`: `/api/matches/<id>/` de la Y10
  y de la Club House.
- `test_listado_y_detalle_dicen_lo_mismo_que_mapas` (criterio 3): suma
  Consulate `379218689149` y un id 999 llamado "Consulate"; el conjunto de
  `map` del listado es el de `agg.by_map()`, con "Consulate (id 999)", y
  cada detalle repite la etiqueta de su fila del listado.
- `test_el_filtro_del_listado_sigue_igual` (criterio 5): `?map=consulate` da
  las dos versiones con su etiqueta; `?map=418126004176`, solo la Y10.
- `test_el_listado_no_hace_una_consulta_por_partida`: `assertNumQueries` con
  la base de arriba y con el doble de partidas da el mismo numero (5 en el
  spike).
- Criterio 4 (resumen copiado): sin test nuevo, `resumenPartida.js` toma
  `match.map` del detalle; lo verifica QA.

**Orden:** tests en rojo; `etiquetas_de_mapas`; `match_list`;
`match_detail`; `check.sh`.

**Que puede romperse.** Nada del esquema: no hay migracion ni recompute.
`seed_demo` y las factories dejan `map_id=0`, que no esta en `MAPS`: la
etiqueta es el nombre guardado y el e2e no cambia. Una consulta mas en el
listado, por pagina. Un `map_name` editado en Datos y `retag` se ven igual
que en Mapas, porque las dos salen de la misma funcion.

**Verificacion manual (QA).** Base de `factories` con las partidas del
setUp; `curl /api/matches/` y `curl /api/matches/<id>/` ven "Consulate
(Y10)"; en la app, Partidas y el detalle lo muestran, y "Copiar resumen"
arranca con "Consulate (Y10) · ". Con `seed_demo`, Partidas igual que antes.

**Fuera de alcance (anotado):** con filtros que esconden una version, Mapas
puede perder el "(id N)" de la otra (calcula sobre las filas filtradas) y el
listado lo conserva; unificarlo es la A8.

## Implementacion

## Revision <fecha> sobre <sha>

## QA <fecha> sobre <sha>

## Verificar en el PC

## Pendiente

## Para el humano

Nada pendiente: la decision de separar versiones la tomaste el 2026-10-28
(ficha 70).
