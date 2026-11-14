# 137. Cuantas de tus muertes son headshot

estado: implementado
candado: -
rama: claude/equipo-dev/137-cuantas-de-tus-muertes-son-headshot
tipo: funcionalidad
epica: rivales
area: fullstack
prioridad: 3
fuente: ALCANCE.md D8
archivos: backend/replays/analytics/aggregates.py, backend/replays/views.py, backend/tests/test_muertes_headshot.py, frontend/src/muertesHeadshot.js, frontend/src/muertesHeadshot.test.js, frontend/src/pages/Duelos.jsx, frontend/e2e/humo.spec.js, docs/metricas.md
turnos: po 20261113T2157Z-cG2vDSe, arquitecto 20261114T0040Z-chQsvnq

## PR

## Que gana quien usa la app

El HS% que muestra la app es el tuyo al matar; el reverso no existe. En Duelos,
de tus muertes a manos de rivales, cuantas fueron headshot, por lado, al lado
del mismo numero para tus compañeros en las mismas rondas: si te enganchan la
cabeza mas que al resto del equipo, te asomas expuesto.

## Criterios de aceptacion

- [ ] Agregado nuevo: de los `Event` de baja cuyo `target` eres tu y cuyo
      autor es rival (`_solo_rivales`, sin teamkills), `deaths`,
      `with_data` (`headshot` no nulo), `headshots` y `pct` =
      headshots / with_data, por lado de tu fila (`Attack`, `Defense`) y
      total. `headshot` nulo no entra en el porcentaje. Test con muertes con
      y sin dato y un teamkill que no cuenta.
- [ ] La referencia: el mismo calculo sobre las muertes de tus compañeros
      (tu `team_index`, `is_me=False`) en tus rondas filtradas. Test.
- [ ] Los filtros globales aplican sobre tu fila de la ronda; test con
      filtro de lado.
- [ ] Se ve en Duelos (clave nueva en el endpoint que ya usa la pagina o uno
      nuevo de lectura) como una tabla chica Tú / Tus compañeros por lado, con
      el `n` (muertes con dato) a la vista y aviso si es chico; sin dato,
      una nota. e2e sobre `seed_demo` con los numeros de la API y consola
      limpia.
- [ ] Fila nueva en `docs/metricas.md`.

## Fuera de alcance

- Partirlo por operador rival (otro tramo).
- Señal del Coach.

## Diseno

(arquitecto 20261114T0040Z-chQsvnq) Filtros duros: pasa (`Event.headshot`,
`Event.target`, `team_index` por ronda; sin red, sin dependencias, sin POST,
sin migracion; se calcula al consultar como `nemesis` y `death_state`: es
conteo de eventos, no columna nueva). Una sola forma: sin arena ni consenso.

**Regla** (va tal cual a `metricas.md`). Universo: tus rondas filtradas,
`mine = base_queryset(**filters)` (los filtros aplican sobre tu fila,
incluido el lado). Eventos: `_mis_bajas(mine)` (los `Kill` de esas rondas)
pasados por `_solo_rivales(qs, "actor_id")` (autor con fila en la ronda y en
el equipo contrario al tuyo: fuera teamkills y bajas sin autor). *Tú*:
`target_id` en `_me_ids()`. *Tus compañeros*: `target_id` fuera de
`_me_ids()` y con `_equipo_de("target_id") == mi_equipo` (victima con fila
en la ronda y en tu equipo). Lado de la fila: el `side` de tu `RoundPlayer`
de esa ronda (tus compañeros juegan el mismo lado). Por grupo y por lado
(`Attack`, `Defense`, y `total`): `deaths` (todas), `with_data`
(`headshot` no nulo), `headshots` (`headshot=True`) y
`pct = _pct(headshots, with_data)` (None con 0). Conteos sumados, nunca
promedio por partida ni por compañero.

**Archivos:**
- `backend/replays/analytics/aggregates.py`: `headshot_deaths(**filters) ->
  dict` despues de `death_state`. Forma:
  `{"me": {"Attack": {...}, "Defense": {...}, "total": {...}},
    "teammates": {...mismo...}}`, las seis celdas siempre presentes. Una
  consulta con `.values("lado", "es_mia").annotate(deaths=Count("id"),
  with_data=Count("id", filter=Q(headshot__isnull=False)),
  headshots=Count("id", filter=Q(headshot=True)))`, donde `lado` es un
  `Subquery` del `side` de tu fila (como `_MI_EQUIPO`) y `es_mia` un
  `Case` sobre `target_id__in=me_ids`; el `total` se suma en Python.
- `backend/replays/views.py`, `duels()`: clave `"headshot_deaths"`. No hay
  URL nueva (urls.py lo toca la 134).
- `backend/tests/test_muertes_headshot.py` (Django, `factories.py`):
  `test_cuenta_tus_muertes_headshot_sobre_las_que_tienen_dato`;
  `test_headshot_nulo_cuenta_en_muertes_y_no_en_el_porcentaje`;
  `test_un_teamkill_no_cuenta_ni_para_ti_ni_para_tus_companeros`;
  `test_muerte_sin_autor_no_cuenta`;
  `test_las_muertes_de_tus_companeros_van_aparte`;
  `test_un_rival_no_cuenta_como_companero` (bajas entre rivales: nada);
  `test_parte_por_tu_lado_y_suma_el_total`;
  `test_filtro_de_lado_deja_solo_ese_lado`;
  `test_sin_dato_el_porcentaje_es_nulo`;
  `test_api_duels_trae_headshot_deaths`;
  `assertNumQueries` fijo sobre `headshot_deaths`.
- `frontend/src/muertesHeadshot.js`: `filasMuertesHeadshot(data)` -> filas
  `{clave, grupo: 'Tú' | 'Tus compañeros', ataque, defensa, total}` con cada
  celda `{pct, with_data}`; `[]` si los dos grupos tienen `with_data` 0 en
  `total` (para la nota y no ceros). `conPocaMuestra(filas)`: alguna celda
  con `0 < with_data < 30`, con `MUESTRA_CORTE` de `muestra.js` (no se
  define otro numero).
- `frontend/src/muertesHeadshot.test.js` (vitest): sin datos `[]`; orden Tú
  y despues compañeros; celda sin dato queda con `pct` null; aviso solo con
  muestra entre 1 y 29.
- `frontend/src/pages/Duelos.jsx`: Panel "Muertes por headshot" despues de
  "Por rival" (`Duelos.jsx:218`) y antes de "Rivales repetidos", con
  `data.headshot_deaths`. Tabla con columnas Quién, Ataque, Defensa, Total;
  cada celda `NN % (n)` y "—" sin dato; `hint`: "De tus muertes a manos de
  rivales, cuántas fueron headshot, al lado del mismo número para tus
  compañeros en las mismas rondas. Sin teamkills. n = muertes con dato de
  headshot." Nota de muestra chica si `conPocaMuestra`; sin filas,
  `<p className="note">` "No hay muertes con dato de headshot con estos
  filtros." Sin grafico (dataviz: no aplica, dos filas).
- `frontend/e2e/humo.spec.js`: test "Duelos muestra las muertes por
  headshot": panel por `section.panel` + heading, numeros de la fila Tú
  iguales a los de `/api/duels/` sobre `seed_demo` (el seed crea tu muerte
  con `headshot=indice % 4 == 0` y no crea muertes de compañeros, asi que
  esa fila queda en "—"; calcular los valores corriendo el seed en una base
  temporal), consola limpia.
- `docs/metricas.md`: fila **Muertes por headshot** en la tabla de Duelos,
  con la regla de arriba, junto a **HS%** dejando claro que es el reverso.

**Orden:** tests Django en rojo -> `headshot_deaths` -> clave -> vitest ->
helper -> panel -> e2e -> `metricas.md` -> `npm run build`.

**Puede romperse:** `_solo_rivales` anota `op_rival` (Subquery extra, sin
costo de filas); si el `.values()` agrupa tambien por esas anotaciones,
el conteo se parte: agrupar solo por `lado` y `es_mia` (test de totales lo
cubre). Rondas sin tu fila no entran (salen de `mine`).

**Archivos ocupados:** la 132 (en QA) toca `Duelos.jsx` en la columna
"Revanchas esa noche" de Rivales repetidos y `aggregates.py` en
`repeated_rivals`; este panel va en otro bloque y la funcion es nueva: sin
pisada real, no se frena. Si la 132 ya esta en dev al reclamar, nada que
hacer; si no, el que mergee segundo resuelve el contexto del `Panel`.

**Verificacion manual:** en una base real, el total de *Tú* con dato no
pasa de tus muertes de Resumen; con `side=Attack`, la columna Defensa
queda en "—".

Skills: no aplica (conteo sobre el feed con precedentes `nemesis` y `death_state`).
Skills del repo: statistical-analysis (denominador = muertes con dato, `n` en cada celda, corte de 30 de `muestra.js`, conteos sumados y no promedio de promedios), testing-strategy (Django para la regla, vitest para el helper, e2e para el panel).
OMC: plan=— · revisión=— · verificación=—

## Implementacion

## Revision

## QA

## Para el humano

(nada)
