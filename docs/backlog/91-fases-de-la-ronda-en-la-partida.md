# 91. Fases de la ronda en el detalle de partida

estado: propuesto
candado: -
rama: -
tipo: funcionalidad
epica: paridad-referencia
area: fullstack
prioridad: 3
fuente: R3 de ALCANCE.md; `replica/features.csv` "Analisis de ronda en fases early, mid y execute" (could, partial: los tramos existen entre partidas en Tendencias, no por partida); [aurelix](https://aurelix.app/blog/how-to-analyse-r6-siege-replays)
archivos: -
turnos: po 20261105T1759Z-cCJ5erc

## PR

(La escribe el Release manager al final.)

## Que gana quien usa la app

En el detalle de una partida, las bajas de cada equipo partidas en temprano,
medio y tarde de la ronda, y cuantas rondas gano cada equipo segun quien
saco mas bajas en cada fase: ver si esa partida se decidio en el primer
contacto o en el cierre. Hoy eso existe solo como agregado de tus bajas y
muertes en Tendencias, nunca para una partida y los dos equipos.

## Criterios de aceptacion

- [ ] `GET /api/matches/<id>/` trae `phases`: tres filas (temprano < 30 s
      jugados, medio de 30 a 120 s, tarde 120 s o mas, sobre `Event.elapsed`
      de los `Kill`) con las bajas de tu equipo y del rival en cada una,
      teamkills afuera (no cuentan para ningun equipo). Test con una partida
      armada a mano: una baja a los 29.9 s cae en temprano, una a 30.0 s en
      medio, una a 120.0 s en tarde.
- [ ] Cada fila trae tambien en cuantas rondas tu equipo saco mas bajas que el
      rival en esa fase y cuantas de esas rondas ganaste (`Round.my_team_won`;
      las rondas con resultado desconocido fuera del denominador). Test.
- [ ] Una baja cuyo autor no tiene fila en la ronda (equipo desconocido) no
      suma a ningun equipo ni rompe la respuesta (test).
- [ ] En `MatchDetail`, un panel "Fases de la ronda" con las tres filas;
      una partida sin bajas muestra el panel con ceros o un texto, nunca un
      error de consola. Caso en el e2e con un numero de `seed_demo`.
- [ ] Fila en `docs/metricas.md` con los cortes (los mismos tramos que
      el Arquitecto alinee con "Cuando matas" y "Cuando mueres" si conviene;
      si cambia los cortes, lo dice el diseno).

## Fuera de alcance

- La misma vista agregada entre partidas: ya esta en Tendencias.
- Fases por plant o post-plant: el formato no trae el plant en temporadas
  nuevas.
- Una timeline grafica nueva: la ronda ya tiene su timeline.

## Diseno

(Arquitecto)

## Implementacion

(Dev)
