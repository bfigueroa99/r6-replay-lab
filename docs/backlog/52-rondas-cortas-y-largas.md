# 52. Rondas cortas y rondas largas

estado: propuesto
candado: -
rama: -
tipo: funcionalidad
epica: lado-y-marcador
area: fullstack
prioridad: 3
fuente: ALCANCE.md B9 (y B12, que entra como columna de este tramo)
archivos: -
turnos: po 20261017T1204Z

## PR

(La escribe el Release manager al final.)

## Que gana quien usa la app

En Tendencias, tu winrate de ronda segun cuanto duro la fase de accion,
separado por lado: si en ataque solo ganas las ejecuciones rapidas o si en
defensa te quiebras cuando la ronda se alarga. Hoy la duracion solo aparece
como texto suelto en cada ronda del detalle (`MatchDetail.jsx:98`) y ningun
agregado la usa.

## Criterios de aceptacion

- [ ] `/api/trends/` trae la clave nueva `by_round_length`: una fila por
      tramo fijo de duracion (`0-45 s`, `45-90 s`, `90-135 s`, `135 s o mas`)
      y una fila aparte `Posible plant`, cada una con `rounds`, `rounds_won`,
      `winrate`, `rating` y `kpr`, por lado (`Attack`, `Defense`) y total.
      Tramo con 0 rondas: fila con `rounds: 0` y `winrate: null`, no se omite.
- [ ] La duracion es `Round.duration` (`clock_start - clock_end`). Una ronda
      con `possible_plant=True` cuenta solo en la fila `Posible plant` y en
      ningun tramo (despues del plant el reloj no mide la misma fase,
      `docs/formato-rec.md`); una ronda con `clock_start == 0` (reloj
      desconocido) no cuenta en ninguna fila. Test con una ronda de cada caso.
- [ ] Los filtros de siempre (`map`, `side`, `since`/`until`, `ranked`,
      sesion) recortan la tabla igual que al resto de Tendencias; con base
      vacia la clave existe y todas las filas tienen `rounds: 0`.
- [ ] Cada fila trae `avg_duration_won` y `avg_duration_lost` (segundos con
      un decimal, `null` sin rondas): cuanto tardas en ganar y en perder en
      ese lado (B12, sin separar por condicion de victoria).
- [ ] Tendencias muestra el panel "Rondas cortas y largas" con los tramos
      en filas y ataque, defensa y total en columnas; el e2e
      (`frontend/e2e/`) lo encuentra con datos de `seed_demo` y la consola
      queda limpia. La logica de armado de la tabla vive en un modulo puro con
      su test de vitest.
- [ ] `docs/metricas.md` tiene la fila **Duracion de la ronda** con los
      tramos, la exclusion de posible plant y de reloj desconocido.

## Fuera de alcance

- Tramos configurables desde la UI o el `.env`.
- Separar las rondas por condicion de victoria (eliminacion, objetivo,
  tiempo): `round_endings` ya lo hace por otro eje.
- Cualquier lectura del momento del plant: solo se infiere y no entra en
  metricas.
- CSV dedicado (va con H3 si alguien lo pide).

## Para el humano

Los tramos de 45 s son una eleccion del PO sobre una fase de accion de
~180 s. Si con la base real casi todo cae en un tramo, el Arquitecto puede
ajustarlos antes de implementar; es reversible.
