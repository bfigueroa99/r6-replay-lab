# 79. Excluir una partida de los agregados

estado: entregado (PR pendiente de merge: toca CLAUDE.md, lo mergea el humano)
candado: revisor 2026-11-13T21:58Z
rama: claude/equipo-dev/79-excluir-una-partida-de-los-agregados
tipo: funcionalidad
epica: datos
area: fullstack
prioridad: 3
fuente: ALCANCE.md G2; decision del humano del 2026-11-05 (POST nuevo permitido, local y con application/json, entra a la lista de CLAUDE.md al disenarse)
archivos: backend/replays/models.py, backend/replays/migrations/0006_match_excluded.py, backend/replays/analytics/aggregates.py, backend/replays/views.py, backend/replays/urls.py, backend/replays/ingest.py (comentario), backend/tests/factories.py, backend/tests/test_excluir_partida.py, frontend/src/pages/MatchDetail.jsx, frontend/e2e/partidas-excluidas.spec.js, CLAUDE.md, docs/metricas.md
turnos: po 20261105T0230Z-c8Ahepa, arquitecto 20261105T0349Z-cCqeUqM, dev 20261105T1303Z-ciG2Prg, revisor 20261105T1330Z-cTQKqvr, qa 20261105T1358Z-ckVhKLL, release 20261105T1358Z-ckVhKLL

## PR

Titulo: `[equipo-dev][backend] Excluir una partida de tus números`

PR: https://github.com/bfigueroa99/r6-replay-lab/pull/81 (contra `dev`; lo mergea el humano porque toca `CLAUDE.md`)

### Que cambia

En el detalle de una partida aparece el boton "Excluir de mis números". Sirve para una custom, una partida con desconexion o una de calentamiento. Una partida excluida no cuenta en ningun agregado: Inicio, Coach, Operadores, Compañeros, Tendencias, Duelos, sesiones, filtros, el 1.00 del rating ni los CSV de agregados. Sigue apareciendo en Partidas, en su detalle y en el inventario. Un clic en "Volver a contarla" la devuelve, y nada se borra.

### Por que esto y no otra cosa

Es la ficha 79 (ALCANCE G2). El humano autorizo el POST el 2026-11-05. Hay una sola raiz para lo que cuenta: `rondas_contables()` y `partidas_contables()` en `aggregates.py`. Se descartaron dos alternativas:
- Filtrar en `base_queryset` con parches sueltos: la proxima consulta se olvida del filtro.
- Un manager por defecto filtrado: rompe el detalle, `ingest`, `seed_demo` y el admin.

Este PR es el tramo 1. El chip en Partidas y la lista en Datos quedan en la ficha 83.

### Como se probo

- `check.sh` (con `verificar.sh`): VERDE 19ca3b5 (973 backend, 186 vitest, 60 e2e) y, ya fusionada con dev a9f8a28 (la 85), VERDE fcba82e (973 tests backend, 190 vitest, 61 e2e).
- `test_excluir_partida.py` (20 tests):
  - POST: 415, 404, 400 y 405.
  - Cada GET agregado y cada tabla del CSV dan lo mismo que la base sin la partida. Un test de control comprueba que la partida X si mueve los numeros.
  - Toda ruta de `urls.py` tiene que estar clasificada.
  - La excluida sigue en el listado y su detalle queda completo.
  - Ida y vuelta exacta.
  - `--force` conserva la marca.
  - Guardia estatica (`ast`) sobre las raices de `aggregates.py`.
- e2e `partidas-excluidas.spec.js`: el Inicio pasa de 203/29 a 196/28 y vuelve a 203/29, con la consola limpia.
- QA con `runserver` y `curl`:
  - Migracion sobre una base con el esquema de dev: 10 rutas iguales antes y despues de `migrate` y de `recompute`.
  - Bordes del POST y de los filtros, base vacia y todas las partidas excluidas: todo da 200.
  - El chunk inicial no crece (190.71 kB).
  - 4 mutaciones, y las cuatro hacen fallar su test.
- OMC:
  - Diseno: plan=APPROVE (ronda 2) · revisión=— · verificación=—
  - Implementacion: plan=— · revisión=5 hallazgos LOW (1 arreglado) · verificación=—
  - Revision: plan=— · revisión=4 hallazgos (0 arreglados; 1 MEDIUM, 3 LOW) · verificación=—
  - QA: plan=— · revisión=— · verificación=PASS (6/6 VERIFIED)

### Riesgos y lo que no entra

- Trae la migracion `0006_match_excluded`. Es solo un `AddField` con default False, y se vuelve atras con `migrate replays 0005`.
- Al excluir una partida, los indices de `?session=` se pueden correr. El `my_rating` por partida se mide contra el 1.00 de las partidas que cuentan. Si la excluida era la unica de su version de mapa, esa version sale del selector. Todo esta documentado en `metricas.md`.
- Queda afuera, a proposito, y va a la ficha 83: el chip en Partidas, la lista en Datos y el rango "visto entre" del perfil, que hoy cuenta la excluida (MEDIUM de la revision).

### Como probarlo en 2 minutos

1. `cd backend; python manage.py migrate; python manage.py seed_demo; python manage.py runserver`
2. Abrir el Inicio: dice "203 rondas en 29 partidas".
3. Abrir el detalle de la partida mas reciente, apretar "Excluir de mis números" y ver el aviso "Esta partida no cuenta en tus números.". De vuelta en el Inicio dice "196 rondas en 28 partidas", y Partidas sigue mostrando 29.
4. Apretar "Volver a contarla": el Inicio vuelve a 203/29.

#Salud (revisor 20261105T1455Z-cwDWPd9, sin `implementado` ni `revisado` tomables): dev 85009f6 mezclado sin conflictos en fd3a41f; `verificar.sh`: VERDE fd3a41f9d (974 tests backend, 190 vitest, 62 e2e). Sigue lista para que la mergee el humano.

## Verificar en el PC

`python manage.py backup`, despues `python manage.py migrate`, y `python manage.py showmigrations replays` tiene que mostrar `[X] 0006_match_excluded`. Excluir una custom y comprobar que cambian el K/D, el rating y la cantidad de partidas. Volver a contarla. Correr `import_replays --force` con una partida excluida: la marca tiene que seguir.

### Para el humano

El PR cambia reglas de `CLAUDE.md`, asi que lo mergea el humano:
- suma el POST `/api/matches/<id>/exclude/`, autorizado el 2026-11-05;
- suma la regla de raices contables.

Variantes conservadoras que se pueden cambiar:
- la excluida sigue en Partidas;
- no une sesiones.

### Candidatos descubiertos

Ninguno nuevo; la 83 ya estaba en el papel. Para una ficha de deuda: `seed_demo` no deja los trades y clutch al dia, porque el primer `recompute` actualiza 981 filas.

## Que gana quien usa la app

Hoy una custom o una partida con desconexion ensucian el K/D, el rating y los winrates, y la unica salida es borrar el `.rec`. Con el boton, la partida sale de tus numeros sin borrarla.

## Criterios de aceptacion

- [x] `POST /api/matches/<id>/exclude/` con `application/json`: 415 sin JSON, 404 si la partida no existe, 400 si `excluded` no es booleano. El docstring de `_es_json` esta al dia.
- [x] La excluida no cuenta en overview, coach, operators, teammates ni trends, ni en el CSV de agregados. Lo prueba un test contra la base sin la partida.
- [x] Sigue en `/api/matches/` con `excluded: true` y su detalle queda completo. Ida y vuelta exacta.
- [x] `import_replays --force` no pierde la marca.
- [x] UI: el boton, el aviso y el e2e 203/29 -> 196/28 -> 203/29, sin errores de consola.
- [x] `CLAUDE.md`, con el POST y la regla, y `docs/metricas.md` al dia.

## Diseno, implementacion y revision (resumen)

- **Diseno.** Arquitecto, plan por consenso, opcion B. Tres helpers en `aggregates.py`: `rondas_contables`, `partidas_contables(incluir_excluidas=)` y `_mia_en_la_ronda`, con un inventario de cada consulta raiz. El tramo 2 es la ficha 83.
- **Implementacion.** Dev 20261105T1303Z-ciG2Prg. Hay dos desvios: la guardia `ast` mira solo `is_me=True`, y el e2e espera `networkidle` antes de salir del Inicio.
- **Revision.** Revisor 20261105T1330Z-cTQKqvr, en tres ejes, aprobo. Hallazgos que no bloquean y quedan para la 83:
  - MEDIUM: el "visto entre" del perfil cuenta la excluida.
  - LOW: falta en `metricas.md` una linea sobre `?session=` y Partidas.
  - LOW: la renumeracion de sesiones.
  - LOW: el chip en el titulo.

## QA 2026-11-05 sobre 19ca3b5

QA 20261105T1358Z-ckVhKLL. Aprobo: los 6 criterios estan probados, no hay hallazgos y `omc-verifier` dio PASS. La evidencia completa (comandos y salidas) esta en el commit `e681ae7`, "Prueba: 79 ...".

## Verificar en el PC

Trae migracion: `python manage.py backup`, `migrate` y `showmigrations replays`. Despues seguir los pasos de "Verificar en el PC" del PR.


## Mantenimiento 2026-11-13 (revisor 20261113T1733Z-cudo1Sw, salud de rama entregada)

Mezcla `origin/dev` (41 commits, con la 114 y la 116). Sin conflicto de texto,
pero `test_toda_ruta_esta_clasificada` cayo: la ruta `death-state` de la 116
no estaba en ninguna lista. Va a `COMPARADAS` con su URL en `_rutas`, y
`test_cada_get_agregado_da_lo_mismo_que_sin_la_partida` pasa con ella
(`death_state` sale de `base_queryset`). verificar.sh: VERDE 4c23b07e6
(1250 tests backend, 370 vitest, 102 e2e). Estado sin cambio: sigue esperando
el merge del humano.

## Para el humano

- (po y arquitecto) Variantes conservadoras:
  - la excluida sigue en Partidas y en el CSV de partidas;
  - no ocupa lugar en las sesiones.

  Si preferis otra cosa, decilo en la ficha.
- (release 20261105T1358Z-ckVhKLL) El PR toca `CLAUDE.md`, asi que lo mergea el humano (puerta d).
- (qa 20261106T0252Z-cf6G6Cs, P3) Dev ea8ccfa+96 chocaba en `MatchDetail.jsx`: botones de exclusion
  juntos con "Partida anterior/siguiente" de la 95 dentro de `DetallePartida` (remonte por
  `key`). La guardia de la 79 marco dos cosas llegadas a dev despues: la subconsulta de
  `spawn_exits` (89) pasa a `_mia_en_la_ronda()` (misma consulta) y `operators-by-site` (93)
  entra a `COMPARADAS`. VERDE 85e6cd228 (1056, 251, 77).
- (release 20261106T0411Z-cu3JEpz, P3) Dev f0444b5 trajo la 97 con `0005_roundplayer_clutch_kills`:
  la migracion de esta ficha pasa a `0006_match_excluded`, con dependencia en la 0005 de la 97
  (merge sin conflicto de texto, pero dos hojas `0005` rompian `migrate`). `makemigrations
  --check` sin cambios. VERDE da8a4f010 (1089, 257, 77). En el PC: `showmigrations replays`
  tiene que mostrar `[X] 0006_match_excluded`; para volver atras, `migrate replays 0005`.

## Salud 2026-11-12 (revisor 20261112T1128Z-cKKCvKD, sin implementado tomable)

Mezclado `origin/dev` (89 commits, sin conflictos; la migracion sigue en
`0006_match_excluded`, despues de la `0005` de dev). verificar.sh: VERDE
654b742 (1125 tests backend, 295 vitest, 85 e2e). Sigue esperando el merge
del humano: toca `CLAUDE.md`.

## Mantenimiento 2026-11-13 (20261113T1704Z-ctPFErG, revisor sin trabajo: salud de rama entregada)

Mezclado `origin/dev` (118 commits, sin conflictos de git). La guardia
`test_toda_ruta_esta_clasificada` caia: `site-after-loss`, `operators-pool` y
`operators-after-result` llegaron a dev despues de la 79. Las tres pasan por
`base_queryset`; van a `COMPARADAS` y a `_rutas()`, y dan lo mismo con la
partida excluida que borrada (`tests.test_excluir_partida`: 20 OK). Solo cambio
el test, no el codigo de la 79: la revision y la QA siguen valiendo.
verificar.sh: VERDE 52093dac1 (1220 tests backend, 351 vitest, 99 e2e).
Para el humano: si el PR se mergea despues de que entre otra ruta GET a dev,
esta guardia la va a pedir clasificada; es el comportamiento buscado.

## Mantenimiento 2026-11-13 18:50 (revisor 20261113T1830Z-cTivbSq, salud de rama entregada)

Rama 41 commits atras de `origin/dev` (entraron la 118, la 119 y la 121), sin
conflicto (`git merge-tree`). `git merge origin/dev` limpio; la guardia de
agregados de excluidas no pidio clasificar nada nuevo. `verificar.sh`: VERDE
ef17b0c86 (1259 backend, 388 vitest, 106 e2e). Sigue esperando el merge del
humano (toca `CLAUDE.md`).
