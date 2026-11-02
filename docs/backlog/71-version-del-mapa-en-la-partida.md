# 71. La partida dice que version del mapa se jugo

estado: aprobado
candado: release 2026-11-02T12:11Z
rama: claude/equipo-dev/71-version-del-mapa-en-la-partida
tipo: funcionalidad
epica: temporada-y-modo
area: backend
prioridad: 2
fuente: idea A6 de `ALCANCE.md` ("Implementar despues de #70"; la 70 esta en `dev` desde 0fedc7b, PR #65). Fuera de alcance de la ficha 70: "listado, records, sesiones y detalle de partida". `etiqueta_de_version` (`pydissect/header.py:239`) y `etiquetas_de_version` (`replays/analytics/aggregates.py:481`) ya existen; `match_list` y `match_detail` (`replays/views.py:434` y `:543`) devuelven `map: match.map_name`
archivos: backend/replays/analytics/aggregates.py, backend/replays/views.py, backend/tests/test_mapa_de_la_partida.py, docs/metricas.md
turnos: po 20261030T1653Z, arquitecto 20261030T1652Z, dev 20261031T2135Z, revisor 20261102T0805Z-cD882za, qa 20261102T1206Z-cLhn4iG

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

Dev 20261031T2135Z sobre `origin/dev@9de28fa`. Quedo todo el diseno, sin
tocar frontend. `check.sh` en `Todo en verde.` (858 backend, 133 vitest,
build, 53 e2e):

- `aggregates.etiquetas_de_mapas(slugs=None)`: `Match.objects.values(map_slug,
  map_name, map_id).distinct()` ordenado como `_opciones_de_mapa`, acotado
  por `map_slug__in` si vienen slugs, y `etiquetas_de_version` encima.
- `views.match_list`: una consulta por pagina con los slugs de la pagina;
  `map` = etiqueta, con `match.map_name` de respaldo. `map_slug` igual.
  Pagina vacia: `map_slug__in=[]` no llega a la base.
- `views.match_detail`: la misma expresion sobre el slug de la partida.
- `docs/metricas.md`, fila **Mapa** de `## Cortes`: la frase del diseno.

Tests (`backend/tests/test_mapa_de_la_partida.py`, 6): criterio 1
`test_el_listado_dice_la_version_del_mapa`; criterio 2
`test_el_detalle_dice_la_version_del_mapa`; criterio 3
`test_listado_y_detalle_dicen_lo_mismo_que_mapas` y
`test_la_etiqueta_no_cambia_con_la_pagina`; criterio 5
`test_el_filtro_del_listado_sigue_igual` y
`test_el_listado_no_hace_una_consulta_por_partida`. Criterio 4 (resumen
copiado): sin test, como decia el diseno; `resumenPartida.js:69` toma
`match.map` del detalle. Los 6 fallaban antes del cambio.

Desvios del diseno:
- Test extra `test_la_etiqueta_no_cambia_con_la_pagina`: recorre el listado
  con `limit=1` y exige el "(id 999)" aunque la otra "Consulate" este en
  otra pagina. Es el caso que justifica mirar todas las partidas del slug.
- `test_el_listado_no_hace_una_consulta_por_partida` compara el numero de
  consultas con la base del setUp y con el doble de partidas, en vez de
  fijar 5 con `assertNumQueries`: otra consulta por pagina no es el bug que
  vigila, y un numero fijo se rompia con cualquier cambio ajeno a la vista.

Mutaciones (codigo roto a proposito, restaurado): etiquetar solo con las
filas de la pagina (`etiquetas_de_version` sobre `page`) hace caer
`test_la_etiqueta_no_cambia_con_la_pagina`; etiquetar dentro del bucle hace
caer el test de consultas (13 contra 9).

Revision previa: `OMC: no disponible (la sesion no tiene herramienta Agent
para el subagente ciego)`. La pasada de `revision.md` la hice yo sobre el
diff sin `docs/backlog`; unico hallazgo, corregido: el `assertNumQueries(5)`
de arriba. La revision independiente queda para el Revisor.

Skills: no aplica (el patron ya esta en `etiquetas_de_version` y
`_opciones_de_mapa`). Arena: no, una sola forma.

## Revision 2026-11-02 sobre 0e9ae7b

Revisor 20261102T0805Z-cD882za. Rama fusionada con `origin/dev@e146e74` (solo playbook;
sin conflicto). `verificar.sh`: VERDE 0e9ae7b (858 backend, 133 vitest,
53 e2e).

Revision a ciegas (subagente con el prompt de `revision.md`, eje de
estandares; diff de 125 lineas y un solo tema, sin eje de intencion; no toca
POST, red, `.rec` ni rutas, sin eje de seguridad). Hallazgos, los dos
confirmados leyendo el codigo:

- [regla] LOW `backend/replays/analytics/aggregates.py:501`
  Que pasa: el docstring dice "la misma que usa Mapas", pero
  `etiquetas_de_mapas` mira todas las `Match`, como el selector
  (`views._opciones_de_mapa`), y `by_map` etiqueta sobre las filas filtradas.
  Como reproducirlo: Consulate sin sufijo fuera del rango de fechas y un id
  999 llamado "Consulate" dentro: Mapas dice "Consulate", Partidas "Consulate
  (id 999)". Es la diferencia que el diseno ya dejo fuera de alcance (A8).
  Arreglo sugerido: "la misma que usa el selector de mapa (y Mapas sin
  filtros)".
- [estilo] LOW `backend/replays/views.py:155`
  Que pasa: `_opciones_de_mapa` repite la consulta que ahora encapsula
  `etiquetas_de_mapas` (mismo `values`, `distinct` y `order_by`).
  Como reproducirlo: si alguien cambia el orden en una sola, el `setdefault`
  de `etiquetas_de_version` puede elegir otro `map_name` y el selector y
  Partidas dejan de coincidir.
  Arreglo sugerido: que `_opciones_de_mapa` use `etiquetas_de_mapas()` cuando
  se toque (A8).

Ficha:
- Criterio 1 (listado: Y10, sin sufijo, `map_id=0`):
  `test_el_listado_dice_la_version_del_mapa`. Cubierto.
- Criterio 2 (detalle): `test_el_detalle_dice_la_version_del_mapa`. Cubierto.
- Criterio 3 (misma etiqueta que `by_map`, con "(id N)"):
  `test_listado_y_detalle_dicen_lo_mismo_que_mapas` y
  `test_la_etiqueta_no_cambia_con_la_pagina`. Cubierto.
- Criterio 4 (resumen copiado): sin test, `resumenPartida.js` toma
  `match.map` del detalle; queda para QA, como dice el diseno.
- Criterio 5 (`seed_demo`, filtros): `test_el_filtro_del_listado_sigue_igual`
  y el e2e sin cambios en verde. Cubierto.
- Archivos: los cuatro de `archivos:`, nada fuera.
- `docs/metricas.md`: sin numero nuevo; fila **Mapa** al dia.
- Identificadores sin tildes, sin `print` ni `console.log`, tests en espanol.

Veredicto: aprobar. Solo dos LOW, ninguno cambia un dato que ve el usuario.

Skills: no aplica. OMC: plan=— · revisión=2 hallazgos (0 arreglados, LOW) · verificación=—

## QA 2026-11-02 sobre 0c7be44

QA 20261102T1206Z-cLhn4iG. Rama sin conflicto con `origin/dev@e146e74`
(`git merge-tree --write-tree origin/dev HEAD`, salida 0).

- `check.sh`: `git show origin/dev:scripts/equipo-dev/verificar.sh | bash -s --`
  -> `VERDE 0c7be4453 en 118s: 858 tests backend, 133 vitest, 53 e2e. Todo en verde.`
  (criterio 5: el e2e corre sobre `seed_demo`, con `map_id=0`, sin cambios).
- Base vacia (`SQLITE_PATH=<scratch>/vacia.sqlite3 python3 manage.py migrate`,
  `runserver 8701`): `GET /api/matches/` 200 con 0 partidas;
  `?page=-1` 200 vacio; `/api/matches/1/` 404.
- Base sembrada con `tests/factories.py` (script en el scratchpad, `manage.py
  shell < sembrar.py`): Consulate `2609221242`, `418126004176` (dos, una sin
  rondas), `379218689149`, `999` llamado "Consulate", Kanal `1460220617`, Club
  House `0`. `runserver 8702`:
  - `GET /api/matches/` -> 7 filas: "Consulate (Y10)" x2, "Club House",
    "Kanal", "Consulate (id 999)", "Consulate", "Consulate (Y7)"; `map_slug`
    sin cambios (criterio 1).
  - `?map=consulate` -> las 5 Consulate con su etiqueta; `?map=418126004176`
    -> solo las 2 Y10; `?map=` -> 7; `?map=foo` -> 0 (criterio 5).
  - `?until=foo`, `?page=-1`, `?page=999` -> 200 con 7, como en `dev`.
  - `?limit=1&offset=3` -> "Consulate (id 999)" aunque la otra Consulate
    este en otra pagina (criterio 3).
  - Detalle: `/2/` "Consulate (Y10)", `/4/` "Consulate (id 999)", `/6/` "Club
    House", `/7/` (partida sin rondas) "Consulate (Y10)", `/999/` 404
    (criterio 2).
  - `GET /api/export/?table=maps` (`by_map`): Club House, Consulate (id 999),
    Consulate (Y7), Consulate, Consulate (Y10), Kanal: el mismo conjunto que
    el listado (criterio 3).
  - Ningun 500 en el log de los dos servidores. Servidores bajados.
- Resumen copiado (criterio 4): `textoResumenPartida` de
  `frontend/src/resumenPartida.js` con node sobre el JSON real de
  `/api/matches/2/` -> primera linea `Consulate (Y10) · 4-2 · victoria`.
- Frontend sin tocar: no hay chunk que medir. Sin migracion, `recompute` ni
  parser: nada para el PC.
- Mutaciones (`python3 manage.py test tests.test_mapa_de_la_partida`,
  restauradas con `git checkout`): detalle con `match.map_name` -> 4 fallos;
  `etiquetas_de_mapas` con `map_slug__in` vacio -> 5 fallos; listado y
  detalle con `match.map_name` -> 5 fallos.

Observacion, no bloquea (fuera de los criterios): la tabla `matches` de
Exportar (`/api/export/?table=matches`) sigue diciendo "Consulate" sin
version, mientras `maps` ya la dice. Va como idea a `ALCANCE.md` junto a A8.

Veredicto: aprobado.

Skills: no aplica. OMC: plan=— · revisión=— · verificación=PASS (5 de 5 VERIFIED, 0 bloqueantes)

## Verificar en el PC

## Pendiente

## Para el humano

Nada pendiente: la decision de separar versiones la tomaste el 2026-10-28
(ficha 70).
