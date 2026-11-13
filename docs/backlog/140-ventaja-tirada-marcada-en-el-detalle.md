# 140. Ventaja tirada marcada en el detalle de partida

estado: propuesto
candado: -
rama: -
tipo: funcionalidad
epica: revision-de-rondas
area: fullstack
prioridad: 3
fuente: ALCANCE.md F26 (salio del Fuera de alcance y de la lista de la 133, ya en dev)
archivos: -
turnos: po 20261113T2318Z-cpCpgff

## PR

## Que gana quien usa la app

En el detalle de partida, las pestañas de las rondas que tu equipo perdio
despues de quedar con mas vivos llevan una marca, con la ventaja maxima en el
`title`: ves en la propia partida cuales se tiraron sin ir a Duelos. Duelos
(ficha 133) da el total entre partidas; esto lo pone donde se revisa la ronda.

## Criterios de aceptacion

- [ ] `/api/matches/<id>/` suma a cada ronda `max_advantage`: el valor de
      `metrics.ventaja_maxima` sobre el feed de esa ronda (`Kill`, `Death`,
      `PlayerLeave` en orden, con `clock`) para tu equipo, o `null` si no
      hubo ventaja medible. Misma regla que `/api/duels/thrown-advantage/`, sin
      reimplementarla: test que para una partida sembrada compara cada ronda
      con lo que cuenta `thrown_advantage` filtrado a esa partida.
- [ ] Test de la vista: ronda 5v4 perdida -> `max_advantage: 1`; ronda que
      llego a 5v3 y se perdio -> `2`; eliminacion ganada sin ventaja previa ->
      `null` o `< 1`; ronda sin bajas -> `null`. Sin consultas extra por
      ronda (`assertNumQueries` constante con 1 y con 3 rondas).
- [ ] Funcion pura en el frontend `esVentajaTirada(ronda)`:
      `my_team_won === false` y `max_advantage >= 1`; vitest con ganada con
      ventaja, perdida con ventaja, perdida sin ventaja y sin ganador.
- [ ] La pestaña de una ronda tirada lleva una marca visible (clase y texto
      corto, no solo color) y su `title` suma "Ventaja tirada: +N"; las
      demas pestañas se ven igual que hoy. e2e sobre `seed_demo`: la primera
      ronda tirada que da la API tiene la marca y una ronda ganada no;
      consola limpia.
- [ ] Fila en `docs/metricas.md` (o la de Ventaja numérica tirada ampliada)
      que diga que el detalle usa la misma regla.

## Fuera de alcance

- Marcar las rondas dadas vuelta en inferioridad (F12).
- La linea de vivos de la ronda (F13).
- Un filtro de "solo rondas tiradas" en la tira de rondas.
