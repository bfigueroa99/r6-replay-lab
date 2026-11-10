# 104. Tests que ensucian a los que vienen despues (hilo de importacion y cache de overrides)

estado: implementado
candado: -
rama: claude/equipo-dev/104-hilo-de-importacion-ensucia-otros-tests
tipo: bug
epica: -
area: backend
prioridad: 2
fuente: dev 20261110T0805Z-ck1PCEC (sin trabajo: la 83 espera a la 79). Aviso "Tests dependientes del orden" de `## Para el humano` en ESTADO.md
archivos: backend/tests/test_import_job.py, backend/tests/test_pydissect.py
turnos: dev 20261110T0805Z-ck1PCEC

## PR

## Que gana quien usa la app

Nada visible: baja el riesgo de que la suite mienta. Hoy
`manage.py test tests.test_import_job tests.test_ajustes` da 4 fallos en
`VigilanteTests` aunque el codigo este bien; la suite completa pasa solo
porque el orden alfabetico corre `test_ajustes` antes. Un test nuevo con
nombre que ordene despues de `test_import_job` y cuente `ImportLog` fallaria
sin motivo, o peor, pasaria por la fila que dejo otro.

## Criterios de aceptacion

- [ ] `python manage.py test tests.test_import_job tests.test_ajustes` en verde.
- [ ] `python manage.py test tests.test_import_job.HiloTests.test_el_post_ya_trae_el_total tests.test_ajustes.VigilanteTests` en verde.
- [ ] `test_el_post_ya_trae_el_total` sigue afirmando `total == 2` y ademas que el trabajo recibio las dos carpetas, sin abrir un hilo real.
- [ ] `python manage.py test tests --reverse` en verde (hoy falla
      `ModoYTipoDesconocidoTests.test_modo_desconocido_sin_etiqueta_queda_anotado`:
      `'Arcade' != 'Unknown(999)'`).
- [ ] La suite completa sigue en verde (`check.sh`).

## Fuera de alcance

- Cambiar `ingest.start_import` o el vigilante: el codigo de la app esta bien.
- Correr la suite en orden aleatorio (`--shuffle`) en `check.sh`: hoy pasa con
  las semillas 1, 2 y 104, pero fijarlo es decision de la maquinaria.

## Diseno

(dev 20261110T0805Z-ck1PCEC, bug sin ficha previa: diseno de 5 lineas.)
Causa: `HiloTests.test_el_post_ya_trae_el_total` hace el POST a
`/api/import/` con dos carpetas `Match-a` y `Match-b` con `.rec` falsos.
`start_import` lanza un `threading.Thread` real con `run_import_job`; el hilo
abre su propia conexion a la base de test (sqlite en memoria compartida) y
crea dos `ImportLog` que commitea fuera de la transaccion del `TestCase`, asi
que el rollback no los borra. `VigilanteTests` cuenta `ImportLog` de
`Match-a` y ve el sobrante. Arreglo: el test reemplaza
`ingest.run_import_job` (que `start_import` busca al lanzar el hilo) por un
doble que guarda las carpetas y marca el trabajo terminado, y devuelve
`ingest._job` a uno vacio al terminar.

## Implementacion

(dev 20261110T0805Z-ck1PCEC, sobre dev 208e4f9.)

Reproduccion antes del arreglo (receta 4: el test que falla ya existia, solo
hacia falta el orden):

- `python3 manage.py test tests.test_import_job tests.test_ajustes` ->
  `FAILED (failures=4)` en `VigilanteTests` (`test_apagada_no_hace_nada`:
  `AssertionError: True is not false`; `test_importa_lo_que_ya_termino...` y
  `test_una_carpeta_que_falla...`: `2 != 1`; `test_no_se_mete_si_el_boton...`).
- Aislado: `tests.test_import_job.HiloTests.test_el_post_ya_trae_el_total
  tests.test_ajustes.VigilanteTests` -> los mismos 4; con
  `HiloTests.test_el_post_vuelve_enseguida` en su lugar -> OK. El culpable es
  el hilo real con dos carpetas.
- Buscando otras fugas, `python3 manage.py test tests --reverse` ->
  `FAILED (failures=1)`: `test_modo_desconocido_sin_etiqueta_queda_anotado`,
  `'Arcade' != 'Unknown(999)'`. Causa: `ModoYTipoDesconocidoTests.tearDown`
  hace `overrides.load(force=True)`, pero los cleanups (entre ellos
  `parche.stop` del entorno) corren despues de `tearDown`, asi que la recarga
  lee todavia el `overrides.json` temporal con `999 -> Arcade` y lo deja en el
  cache global. En orden alfabetico no se ve porque el test siguiente de la
  clase no usa el override.

Arreglo, solo en tests (el codigo de la app esta bien):

- `test_import_job.py`, `test_el_post_ya_trae_el_total`: reemplaza
  `ingest.run_import_job` (que `start_import` busca al lanzar el hilo) por un
  doble que anota las carpetas y marca el trabajo terminado; afirma ademas
  `["Match-a", "Match-b"]` y `running == False`, y devuelve `ingest._job` a uno
  vacio. El hilo se sigue lanzando (el POST no cambia); lo que no corre es la
  importacion por otra conexion.
- `test_pydissect.py`, `_con_overrides`: registra `overrides.load(force=True)`
  como cleanup antes de `parche.stop`, asi corre despues de parar el parche
  (LIFO).

Despues: los dos comandos de arriba OK (68 y 11 tests), `--reverse` OK y
`--shuffle` con semillas 1, 2 y 104 OK (1100 tests, 4 skipped).

Desvios: la ficha nacio con la fuga del hilo y sumo la del cache al correr
`--reverse`; mismo tipo de bug, mismo arreglo de una linea, misma ficha.

Verificacion: `verificar.sh` VERDE dc33c8294 en 155 s (1100 tests backend,
295 vitest, 84 e2e).

Revision ciega `omc-code-reviewer` (eje de estandares, `revision.md`): sin
hallazgos, aprobar. Corrio ademas `--reverse` de los tres modulos y `--shuffle`
7 y 42 en verde. Anoto su nota fuera del diff: `test_api.py:315`
(`test_import_sin_replays_no_importa_nada`) tambien lanza un hilo real, con
carpeta inexistente: lista vacia, no escribe `ImportLog`; no ensucia.

Skills: no aplica (dos tests de Django, sin dominio externo).
OMC: plan=— · revisión=0 hallazgos (0 arreglados) · verificación=—

## Revision

## QA

## Verificar en el PC

## Para el humano

## Pendiente
