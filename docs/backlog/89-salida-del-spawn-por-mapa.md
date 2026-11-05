# 89. Salida del spawn por mapa

estado: revisado
candado: -
rama: claude/equipo-dev/89-salida-del-spawn-por-mapa
tipo: funcionalidad
epica: posicionamiento
area: fullstack
prioridad: 2
fuente: S2 de ALCANCE.md (idea del PR #22 que el humano cerro sin merge el 2026-11-05, rama `ccr-ec8265ab-4qn7k2`, commit c994090); `ROTACION` de estado.sh marca `posicionamiento` como epica sin entrega
archivos: backend/replays/analytics/aggregates.py (spawn_exits, positioning), backend/tests/test_salida_del_spawn.py, frontend/src/posicion.js, frontend/src/posicion.test.js, frontend/src/pages/Coach.jsx, frontend/e2e/humo.spec.js, docs/metricas.md
turnos: po 20261105T1759Z-cCJ5erc, arquitecto 20261105T1825Z-cVr9Dsg, dev 20261105T1851Z-cBJfgUn, revisor 20261105T1920Z-cSTWy1D

## PR

(La escribe el Release manager al final.)

## Que gana quien usa la app

En el Coach, junto a "Dónde quedas fuera de posición", un panel por mapa y
spawn de ataque con cuantas rondas mueres en los primeros 15 s de accion y
cuantas bajas sacas en esa misma ventana: ver si un spawn te cuesta rondas
por salir a pelear antes de tiempo (runout o spawn peek que sale mal) o si
ese arranque te rinde. Es lo que R6 Analyst llamaba muertes tempranas por
spawn, con la granularidad que el `.rec` trae (spawn, no coordenadas).

## Criterios de aceptacion

- [ ] `GET /api/positioning/` (o un campo nuevo de la misma respuesta) trae
      `spawn_exits`: una fila por mapa (con la etiqueta de version de
      `etiquetas_de_version`) y spawn de ataque, con `rounds`,
      `early_deaths` (rondas tuyas de ataque con `death_elapsed < 15`),
      `early_death_pct`, `early_kills` (tus bajas a rivales con
      `Event.elapsed < 15`, teamkills afuera) y el mismo `early_death_pct` del
      resto de tu ataque para comparar. Test en `backend/tests/` con rondas
      armadas a mano: una muerte a los 14.9 s cuenta, una a los 15.0 s no.
- [ ] Respeta los filtros globales (mapa, lado, temporada, tipo de partida,
      fechas) y la muestra minima de posicion (`POSICION_MIN_RONDAS`): un
      spawn con menos rondas no sale. Las rondas sin spawn (`spawn=""`) y las
      de defensa no cuentan. Test con un filtro de mapa.
- [ ] Una muerte sin reloj (`death_elapsed=None`) no cuenta como temprana ni
      rompe la fila (test).
- [ ] En el Coach, el panel "Salida del spawn" lista las filas ordenadas por
      `early_death_pct` y marca las que estan por encima del resto de tu
      ataque; con cero filas dice por que (sin rondas de ataque con spawn o
      sin muestra) en vez de una tabla vacia.
- [ ] Fila nueva en `docs/metricas.md` ("Muertes tempranas por spawn" y
      "Bajas tempranas por spawn") con el corte de 15 s y su motivo, y caso
      en el e2e (`frontend/e2e/`) con un numero de `seed_demo` afirmado.

## Fuera de alcance

- El enlace por mapa a la biblioteca de spawn peeks de peekabooR6 que traia
  la idea: es un sitio de terceros nuevo y va a `## Para el humano`; este
  tramo no agrega enlaces externos.
- Una señal nueva del Coach sobre esto: primero el panel; la señal es el
  tramo siguiente si el panel muestra algo.
- Defensa: el `.rec` no trae spawn de defensa; el sitio ya lo cubre "Dónde
  quedas fuera de posición".
- Coordenadas, rutas o mapas dibujados: el formato no las trae.

## Diseno

(arquitecto 20261105T1825Z-cVr9Dsg)

Una sola forma obvia: el panel vive dentro de la respuesta de
`/api/positioning/` (la misma que ya pinta "Dónde quedas fuera de posición"),
con los mismos filtros, la misma muestra minima y la misma comparacion
"zona contra el resto de tu ataque". Sin migracion, sin `recompute`, sin
parser: todo sale de `RoundPlayer.death_elapsed` y `Event.elapsed`, que ya se
guardan al importar. Sin arena ni consenso (ficha chica, una forma).
Skills: no aplica (reusa `DataTable` y el patron de `posicion.js`; ningun
dominio nuevo).

### Archivos y por que

- `backend/replays/analytics/aggregates.py`: constante, funcion nueva y una
  clave mas en `positioning()`. Al lado de `POSICION_*` porque comparte
  muestra, bandas y filtros.
- `backend/tests/test_salida_del_spawn.py` (nuevo): tests de la ficha. Aparte
  de `test_posicion.py` para no inflarlo; reusa su helper de estilo (`zona`)
  copiado y adaptado, no importado.
- `frontend/src/posicion.js` + `frontend/src/posicion.test.js`: helpers puros
  del panel nuevo (veredicto y texto de vacio), igual que la ficha 80.
- `frontend/src/pages/Coach.jsx`: panel `PanelSalidaSpawn` debajo de
  `PanelPosicion`, con el mismo `posicion` de `useApi('/positioning/')`: cero
  requests nuevos.
- `frontend/e2e/humo.spec.js`: un `test(...)` nuevo junto al de la linea ~937
  ("el Coach muestra dónde quedas fuera de posición").
- `docs/metricas.md`: dos filas en la tabla de `## Trades` justo debajo de
  "Fuera de posición" (linea ~195) y una fila en `## Muestra minima`.

### Backend

En `aggregates.py`, despues de `POSICION_BANDAS`:

```python
#: Segundos jugados de la fase de accion que cuentan como "salida del spawn".
#: Es la mitad del primer tramo de "Sales muy temprano" (30 s): a los 15 s el
#: atacante todavia esta saliendo del spawn o en el runout, y morir ahi no es
#: lo mismo que morir en el primer contacto armado.
SALIDA_SPAWN_SEGUNDOS = 15
```

`_temprano(campo)` devuelve `Q(**{f"{campo}__gt": 0, f"{campo}__lt": SALIDA_SPAWN_SEGUNDOS})`.
**El 0 no cuenta**: `metrics.py` (linea ~287) escribe `elapsed = 0.0`
cuando el feed no trae reloj, y `first_teammate_death` ya lo trata como "sin
reloj" (linea ~1712). En una ventana de 15 s un 0 espurio pesaria mucho; se
documenta en `metricas.md`. `None` tampoco cuenta (no hubo muerte o no hay
reloj).

Nueva `spawn_exits(ataque: QuerySet[RoundPlayer], min_rounds: int) -> list[dict]`
(docstring: por que 15 s y por que contra el resto del ataque):

1. `ataque = ataque.exclude(spawn="")` (el que llega ya es
   `base_queryset(**filters).filter(side="Attack")`, el mismo que usa
   `positioning()`).
2. Filas crudas: `ataque.values(*_MAPA, "spawn").annotate(rounds=Count("id"),
   early_deaths=Count("id", filter=Q(died=True) & _temprano("death_elapsed")))`.
   Renombrar a `slug`, `map_id`, `map_name`, `spawn` como hace `group_by`, y
   pasar por `_etiquetar` (agrega `map` con la etiqueta de version). No usar
   `group_by` entero: arrastra todas las columnas de `AGGREGATES` y aca
   solo hacen falta dos.
3. Bajas tempranas: `me_ids = _me_ids()`; si hay, `_, a_favor = _duelos(ataque, me_ids)`
   (teamkills afuera por `_solo_rivales`), `a_favor.filter(_temprano("elapsed"))`,
   anotado con el mapa y el spawn de **tu** fila de la ronda
   (`Subquery(RoundPlayer.objects.filter(round_id=OuterRef("round_id"), is_me=True).values("spawn")[:1])`,
   y `round__match__map_slug` / `round__match__map_id` directo del evento),
   `.values(...).annotate(n=Count("id"))`, y se suman a la fila por
   `(slug, map_id, spawn)`. Sin `me_ids`, `early_kills = 0` en todas.
4. Total del ataque (antes del minimo, asi ocultar una fila no mueve las
   demas, como en Presencia): `rounds` y `early_deaths` de todo `ataque` con
   spawn.
5. Por fila: `early_death_pct = _pct(early_deaths, rounds)`,
   `early_kills`, `early_kills_per_round = _ratio(early_kills, rounds)`,
   `rest_rounds`, `rest_early_death_pct` (total menos la fila),
   `early_death_delta = _delta(...)`, `margin` con `_ruido_combinado(...)` y
   `POSICION_BANDAS`, igual que `_contra_el_resto`, y `verdict`:
   `"temprano"` si `delta > margin`, `"aguanta"` si `delta < -margin`,
   `"ruido"` si no o si falta algo. No se toca `_contra_el_resto`: sus claves
   (`caught_out_*`, `dormidero`/`solido`) ya estan en el JSON de la ficha 80.
   Si el Dev ve que la duplicacion pasa de ~10 lineas, puede extraer el
   calculo de `margin`/`verdict` a un helper que ambos usen, sin cambiar
   ninguna clave de salida.
6. Filtrar `rounds >= min_rounds` y ordenar por `early_death_pct` desc (None
   al final), desempate por `rounds` desc y `spawn`.

`positioning()` agrega `"spawn_exits": spawn_exits(ataque, min_rounds)` y
`"spawn_exit_seconds": SALIDA_SPAWN_SEGUNDOS` (la UI no hardcodea el 15). El
total del ataque para comparar va en `"spawn_exit_attack": {"rounds",
"early_deaths", "early_death_pct", "early_kills"}`.

`views.positioning` no cambia: ya pasa `min_rounds` y los filtros.

### Frontend

- `posicion.js`: `VEREDICTOS_SALIDA = { temprano: 'Caes temprano', aguanta:
  'Sales bien', ruido: 'Sin señal' }`, `etiquetaSalida(v)`, `claseSalida(v)`
  (`temprano` -> `loss`, `aguanta` -> `win`), y
  `textoSinSalidas(datos)`: si `spawn_exit_attack.rounds` es 0 o falta,
  "Todavía no hay rondas de ataque con spawn con estos filtros."; si hay
  rondas pero ninguna fila, "Ningún spawn llega a {min_rounds} rondas de
  ataque." Vitest para los tres casos y el veredicto desconocido.
- `Coach.jsx`: `PanelSalidaSpawn({ data, error, loading })` con el mismo
  `posicion`. Titulo **"Salida del spawn"**, hint "Rondas de ataque en que
  moriste en los primeros {spawn_exit_seconds} s de acción, por spawn, contra
  el resto de tu ataque." Una nota con el % del ataque entero
  (`spawn_exit_attack.early_death_pct`). `DataTable` con columnas: Mapa,
  Spawn, Rondas, Mueres temprano (`early_deaths`), % (`early_death_pct`),
  Resto (`rest_early_death_pct`), Diferencia (`conSigno`), Margen
  (`comoMargen`), Bajas tempranas (`early_kills`), Veredicto (chip).
  `initialSort={{ key: 'early_death_pct', dir: 'desc' }}`,
  `csvName="salida-del-spawn"`. Sin filas, `textoSinSalidas`.
  El panel respeta el filtro Lado sin logica extra: con `?side=Defense`
  `ataque` queda vacio y sale el texto de vacio.

### Tests nuevos (`backend/tests/test_salida_del_spawn.py`)

- `test_una_muerte_a_los_14_9_cuenta_y_a_los_15_no`
- `test_una_muerte_sin_reloj_no_cuenta_ni_rompe_la_fila` (`death_elapsed=None`
  con `died=True`, y otra con `death_elapsed=0.0`)
- `test_las_rondas_de_defensa_y_sin_spawn_no_cuentan`
- `test_un_spawn_con_menos_rondas_que_el_minimo_no_sale`
- `test_las_bajas_tempranas_cuentan_solo_rivales` (un teamkill a los 5 s no
  suma; ojo: `make_event` calcula `elapsed = clock_start - clock`, asi que
  para 5 s jugados va `clock=rnd.clock_start - 5`; el rival necesita su
  `RoundPlayer` con el otro `team_index` o `_solo_rivales` lo descarta)
- `test_el_spawn_se_compara_contra_el_resto_del_ataque` (dos spawns, uno
  con 8/10 tempranas y otro con 0/10: el primero `temprano`, el segundo
  `aguanta`; `rest_early_death_pct` del primero es 0.0)
- `test_respeta_el_filtro_de_mapa` (`/api/positioning/?map=...`)
- `test_con_filtro_de_defensa_no_hay_salidas` (`?side=Defense` -> lista
  vacia y `spawn_exit_attack.rounds == 0`)

Vitest: `posicion.test.js` suma los casos de `etiquetaSalida`, `claseSalida`
y `textoSinSalidas`.

### e2e

`seed_demo` no tiene ninguna baja antes de los 30 s (medido con un spike en
el scratchpad: 116 rondas de ataque con spawn, 0 muertes y 0 bajas tuyas
antes de 15 s; seis spawns con 16 o 20 rondas). **No se cambia el seed**: mover
un `death_elapsed` cambia "Mueres a los", "Cuando mueres" y varios numeros
ya afirmados. El caso e2e ("el Coach muestra la salida del spawn"):
`vigilarConsola`, `/coach`, panel por heading "Salida del spawn", 6 filas en
la tabla, la fila de `Bank` / `Boulevard` con `20` rondas y `0` muertes
tempranas, y el texto del % del ataque entero en `0%` (formato el que use la
nota). El veredicto con señal lo cubren los tests de backend y vitest.

### Orden de implementacion

1. Tests de backend en rojo, `SALIDA_SPAWN_SEGUNDOS`, `spawn_exits`, clave en
   `positioning()`. 2. `posicion.js` + vitest. 3. Panel en `Coach.jsx`.
4. e2e. 5. `metricas.md`. 6. `npm run build` y `check.sh`.

### Que puede romperse

- `test_posicion.py` compara el JSON de `positioning()`? No: lee claves
  sueltas. Agregar claves no rompe nada; igual correr la suite entera.
- `_duelos` sobre un queryset de ataque: `_mis_bajas` filtra eventos por
  ronda con `Exists(mine...)`, asi que solo entran rondas de ataque con
  spawn. Si se le pasa `ataque` **sin** el `exclude(spawn="")`, las bajas de
  rondas sin spawn caerian en una fila con `spawn=""`; usar el mismo
  queryset del paso 1.
- El Subquery del spawn de tu fila: si en una ronda tu fila no existe (no
  pasa con `_mis_bajas`, que exige tu fila), la baja queda con `spawn=None`
  y se descarta al sumar.
- Ficha 79 (pendiente del humano) agrega `Match.excluded` al filtro de
  `base_queryset`: esta ficha ya pasa por `base_queryset`, asi que hereda la
  exclusion sin tocar nada. No pisa archivos de la 79 salvo `aggregates.py`
  (regiones distintas) y `metricas.md` (filas distintas): no hace falta
  esperarla.

### Verificacion manual

Con una base real: Coach, panel "Salida del spawn"; filtrar un mapa y ver que
las filas son solo de ese mapa; filtro Lado = Defensa muestra el texto de
vacio; el CSV baja con las columnas de la tabla. Un spawn marcado "Caes
temprano" deberia coincidir con el que en "Cuando mueres" concentra muertes
en el primer tramo de ataque.

### Umbral a calibrar

15 s es una eleccion, no un dato medido: con la base real del humano, mirar
si `spawn_exit_attack.early_death_pct` queda en un rango util (si es ~0 %
en todo, el corte es demasiado chico y conviene 20 s). Va a `## Verificar en
el PC` de QA, no bloquea.

### docs/metricas.md

En `## Trades`, debajo de "Fuera de posición":

- **Muertes tempranas por spawn** (panel "Salida del spawn" del Coach): rondas
  de ataque con ese spawn en que moriste con `0 < death_elapsed < 15` segundos
  jugados de la fase de accion / rondas de ataque con ese spawn. Un reloj en 0
  es "sin reloj" y no cuenta. Se compara contra el resto de tu ataque con la
  misma banda que "Dónde quedas fuera de posición" (`POSICION_BANDAS` errores
  estandar de la proporcion combinada).
- **Bajas tempranas por spawn**: tus bajas a rivales (teamkills afuera) con
  `0 < Event.elapsed < 15` en esas rondas.

En `## Muestra minima`: "Salida del spawn | 5 rondas de ataque por spawn
(`POSICION_MIN_RONDAS`)".

OMC: plan=— · revisión=— · verificación=—

## Implementacion

(dev 20261105T1851Z-cBJfgUn)

Quedo el diseno completo, sin desvios de contrato:

- `aggregates.py`: `SALIDA_SPAWN_SEGUNDOS = 15`, `_temprano(campo)` (0 y
  `None` no cuentan), `spawn_exits(ataque, min_rounds)` que devuelve
  `(filas, total)`, y `positioning()` suma `spawn_exits`,
  `spawn_exit_attack` y `spawn_exit_seconds`. El calculo de margen y
  veredicto se extrajo a `_margen_y_veredicto`, que tambien usa
  `_contra_el_resto` sin cambiar ninguna clave (los 15 tests de
  `test_posicion.py` siguen verdes).
- Desvio menor: las bajas tempranas se agrupan con la misma clave que las
  filas (`_MAPA` entero, con `map_name`, mas tu spawn), no solo por
  `(slug, map_id, spawn)`. Asi, si una version de mapa tiene dos nombres,
  cada fila suma solo sus bajas y la suma cuadra con el total (hallazgo LOW
  del revisor ciego).
- Frontend: `VEREDICTOS_SALIDA`, `etiquetaSalida`, `claseSalida` y
  `textoSinSalidas` en `posicion.js`; `PanelSalidaSpawn` en `Coach.jsx`
  debajo de `PanelPosicion`, con el mismo `useApi('/positioning/')`. La nota
  del ataque entero lleva la clase `salida-ataque` para el e2e.
- `metricas.md`: filas "Muertes tempranas por spawn" y "Bajas tempranas por
  spawn" bajo "Fuera de posición", y "Salida del spawn" en `## Muestra minima`.

Tests (criterio -> test):
- 14.9 s cuenta, 15.0 no: `test_una_muerte_a_los_14_9_cuenta_y_a_los_15_no`.
- Muerte sin reloj (`None` y `0.0`): `test_una_muerte_sin_reloj_no_cuenta_ni_rompe_la_fila`.
- Defensa y sin spawn afuera: `test_las_rondas_de_defensa_y_sin_spawn_no_cuentan`.
- Muestra minima (y total antes del minimo): `test_un_spawn_con_menos_rondas_que_el_minimo_no_sale`.
- Solo rivales, ventana y reloj 0: `test_las_bajas_tempranas_cuentan_solo_rivales`.
- Cada baja en su spawn: `test_cada_baja_temprana_cae_en_el_spawn_de_su_ronda`.
- Contra el resto del ataque y orden: `test_el_spawn_se_compara_contra_el_resto_del_ataque`,
  `test_un_solo_spawn_no_tiene_resto_y_es_ruido`, `test_la_fila_lleva_la_etiqueta_del_mapa`.
- Filtros: `test_respeta_el_filtro_de_mapa`, `test_con_filtro_de_defensa_no_hay_salidas`.
- Vitest (`posicion.test.js`): etiquetas, clases y los dos textos de vacio.
- e2e: `el Coach muestra la salida del spawn` (6 filas, Bank / Boulevard con
  20 rondas y 0 tempranas, "en el 0% de las rondas (0 de 116)").

No quedo: nada del alcance. Limitacion conocida (LOW del revisor, aceptada):
el e2e solo ve el panel neutro porque `seed_demo` no tiene muertes antes de
los 35 s; los chips con señal los cubren backend y vitest. El umbral de 15 s
sigue a calibrar con la base real (ver Diseno).

verificar.sh: VERDE 6be48daed (974 tests backend, 203 vitest, 65 e2e).
Skills: no aplica (el diseno ya resolvia el dominio).
OMC: plan=— · revisión=3 hallazgos LOW (2 arreglados) · verificación=—

## Revision 2026-11-05 sobre 2f17f03

Veredicto: aprobar -> `revisado`.

Revision a ciegas (eje de estandares, `omc-code-reviewer`) y eje de
intencion (diff de 443 lineas, otro `omc-code-reviewer` contra Que gana,
Criterios y Fuera de alcance); sin eje de seguridad (no toca POST, `.rec`,
rutas, `externo/` ni dependencias). Ninguno de los dos encontro CRITICAL ni
HIGH. Confirmado por el lider:

- [test] MEDIUM `frontend/e2e/humo.spec.js:382-394` (los dos ejes)
  Que pasa: en `seed_demo` la primera muerte y la primera baja son a los
  35 s, asi que todas las columnas tempranas valen 0 y el veredicto es "Sin
  señal" en las 6 filas; si el render cruzara `early_deaths` con
  `early_kills` o el conteo diera siempre 0 en la app real, el e2e seguiria
  verde. El calculo lo cubren backend y vitest. Es la limitacion que la
  Implementacion ya anoto como aceptada; no bloquea.
  Arreglo sugerido: si un tramo futuro toca `seed_demo`, sumarle muertes
  antes de 15 s en un spawn y afirmar ese conteo (mueve numeros de otros
  casos e2e: va con su propia ficha).
- [test] LOW `backend/tests/test_salida_del_spawn.py`: el borde 14.9 / 15.0
  estaba probado para muertes y no para bajas. Agregado por el Revisor,
  pasa: `test_una_baja_a_los_14_9_cuenta_y_a_los_15_no`.
- [intencion] LOW: el criterio dice `< 15` y el codigo `0 < x < 15`; el 0.0
  es el "sin reloj" que escribe `metrics.py`, y `metricas.md` lo dice igual.
  Desviacion correcta, sin cambio.
- [intencion] LOW: "marca las que estan por encima del resto" se resuelve
  con la banda de ruido del panel hermano (chip "Caes temprano" solo si la
  diferencia pasa el margen). Coherente con `metricas.md`; sin cambio.

Checklist: cada criterio tiene test o verificacion (tabla de la
Implementacion, mas el test de bajas de arriba); el diff no sale de
`archivos:`; filas nuevas en `docs/metricas.md` (muertes y bajas tempranas
por spawn, muestra minima); identificadores sin tildes, UI con tildes; sin
`print` ni `console.log`. Numeros del e2e reproducidos con `seed_demo` por
los dos subagentes (116 rondas, 6 filas, Bank / Boulevard 20 y 0).

verificar.sh: VERDE (ver el commit de la revision).
Skills: no aplica.
OMC: plan=— · revisión=4 hallazgos (1 MEDIUM, 3 LOW; 1 arreglado con test) · verificación=—

## Para el humano

- ¿Se suma un enlace por mapa a la biblioteca de spawn peeks de peekabooR6
  (lo abre el navegador, como los de stats.cc; la app no le pide nada)? Este
  tramo sale sin el; si decis que si, entra como tramo aparte.
