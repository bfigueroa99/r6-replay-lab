# 114. Qué operadores te abren

estado: propuesto
candado: arquitecto 2026-11-13T12:31Z
rama: -
tipo: funcionalidad
epica: rivales
area: fullstack
prioridad: 3
fuente: ALCANCE.md D7
archivos: backend/replays/analytics/aggregates.py (duels_by_operator o funcion nueva), backend/replays/views.py (duels), frontend/src/pages/Duelos.jsx, docs/metricas.md
turnos: po 20261112T1204Z-chGLrtC

## PR

## Que gana quien usa la app

En Duelos, por lado, que operadores rivales te sacan en el primer duelo de la
ronda (tu muerte de apertura) y a cuales abris tu, con cuantas veces y en que
proporcion de tus aperturas perdidas. La tabla "Por operador rival" cuenta
todos los duelos de la ronda; esta dice a que operador tenes que aprender a
jugarle la entrada.

## Criterios de aceptacion

- [ ] `/api/duels/` devuelve una clave nueva con filas por operador rival y
      tu lado: `opened_you` (rondas donde la primera baja de la ronda fue de
      ese operador sobre ti), `you_opened` (tuya sobre ese operador),
      `share` (`opened_you` sobre todas tus muertes de apertura de ese lado)
      y el balance. Test con rondas armadas: Ash te abre en dos y tu abres a
      Ash en una.
- [ ] Un teamkill o una baja sin autor como primera baja de la ronda no
      suma a ningun operador (mismo criterio que la columna De apertura de
      "Por rival"), y un operador rival vacio o `Unknown(...)` tampoco. Test.
- [ ] Respeta los filtros globales; el de lado separa (tu lado de esa ronda);
      muestra minima propia y documentada (aperturas con ese operador), y
      ordenada por `opened_you` descendente.
- [ ] La tabla se ve en Duelos; sin filas, un texto y no un error. El e2e
      de humo pasa por Duelos con la consola limpia.
- [ ] Fila nueva en `docs/metricas.md` ("Operadores que te abren").

## Fuera de alcance

- Rivales que te abren por persona: ya esta en la columna De apertura de
  "Por rival" (ficha 108, descartada por eso).
- Que operador te abre por mapa o sitio (D2).
- Aperturas entre compañeros.

## Diseno

## Implementacion

## Revision

## QA

## Para el humano

(nada)
