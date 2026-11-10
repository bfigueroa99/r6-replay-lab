# 104. El hilo de importacion de un test ensucia los tests que vienen despues

estado: en curso 2026-11-10
candado: dev 2026-11-10T08:06Z
rama: claude/equipo-dev/104-hilo-de-importacion-ensucia-otros-tests
tipo: bug
epica: -
area: backend
prioridad: 2
fuente: dev 20261110T0805Z-ck1PCEC (sin trabajo: la 83 espera a la 79). Aviso "Tests dependientes del orden" de `## Para el humano` en ESTADO.md
archivos: backend/tests/test_import_job.py
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
- [ ] La suite completa sigue en verde (`check.sh`).

## Fuera de alcance

- Cambiar `ingest.start_import` o el vigilante: el codigo de la app esta bien.
- Correr la suite en orden aleatorio (`--shuffle`) en `check.sh`.

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

## Revision

## QA

## Verificar en el PC

## Para el humano

## Pendiente
