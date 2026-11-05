# 89. Salida del spawn por mapa

estado: propuesto
candado: -
rama: -
tipo: funcionalidad
epica: posicionamiento
area: fullstack
prioridad: 2
fuente: S2 de ALCANCE.md (idea del PR #22 que el humano cerro sin merge el 2026-11-05, rama `ccr-ec8265ab-4qn7k2`, commit c994090); `ROTACION` de estado.sh marca `posicionamiento` como epica sin entrega
archivos: -
turnos: po 20261105T1759Z-cCJ5erc

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

(Arquitecto)

## Implementacion

(Dev)

## Para el humano

- ¿Se suma un enlace por mapa a la biblioteca de spawn peeks de peekabooR6
  (lo abre el navegador, como los de stats.cc; la app no le pide nada)? Este
  tramo sale sin el; si decis que si, entra como tramo aparte.
