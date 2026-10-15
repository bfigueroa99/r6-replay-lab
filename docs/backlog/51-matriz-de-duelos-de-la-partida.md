# 51. Matriz de duelos de la partida

estado: propuesto
candado: -
rama: -
tipo: funcionalidad
epica: revision-de-rondas
area: frontend
prioridad: 3
fuente: ALCANCE.md F7 ([CS Demo Manager v3.5.0](https://cs-demo-manager.com/changelog), "players duels matrix"; selector de aperturas de [vlr.gg](https://www.vlr.gg/188013/velaris-vs-clg-red-complexity-paradox-invitational-playoffs-lr3/?game=all&tab=performance))
archivos: -
turnos: po 20261015T1711Z

## PR

(La escribe el Release manager al final.)

## Que gana quien usa la app

En el detalle de una partida, una tabla 5x5 de quien mato a quien (filas tu
equipo, columnas el rival, y al reves), con los headshots: de un vistazo se
ve que rival te paso por encima esa partida y a quien le ganaste todos los
duelos. Duelos agrega entre partidas; esto es una sola, y no necesita
backend: `/api/matches/<id>/` ya trae el feed de cada ronda.

## Criterios de aceptacion

- [ ] Funcion pura en `frontend/src/` que recibe las rondas de
      `/api/matches/<id>/` y devuelve la matriz: por par (autor, victima)
      bajas y headshots, con el equipo de cada uno sacado de las filas de
      jugadores de la ronda (`team_index`); test vitest con una partida de 2
      rondas.
- [ ] Las bajas entre compañeros (teamkills) y las que no tienen autor no
      entran en la matriz (test).
- [ ] Selector "Todas / Solo aperturas": con aperturas, solo cuenta la
      primera baja de cada ronda (test).
- [ ] Una partida sin eventos de baja muestra un texto vacio, no una tabla
      de ceros ni un error.
- [ ] La tabla aparece en `MatchDetail.jsx` y el e2e (`frontend/e2e/`) la
      ve en una partida de `seed_demo` sin errores de consola.

## Fuera de alcance

- Matriz entre partidas (eso es Duelos).
- Endpoint nuevo o columnas nuevas: se arma en el navegador.
- Flechas de ronda y navegacion de PR #14: disenar sin pisar ese diff.

## Diseno

(Arquitecto)

## Implementacion
