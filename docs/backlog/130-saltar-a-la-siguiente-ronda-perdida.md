# 130. Saltar a la siguiente ronda perdida

estado: propuesto
candado: -
rama: -
tipo: funcionalidad
epica: revision-de-rondas
area: frontend
prioridad: 3
fuente: ALCANCE.md F24
archivos: -
turnos: po 20261113T1858Z-cxQ3TuB

## PR

## Que gana quien usa la app

En el detalle de partida, un boton "Siguiente ronda perdida" (y la tecla
`p`) lleva a la proxima ronda que tu equipo perdio desde la elegida, dando la
vuelta al final. Revisar solo lo que salio mal sin recorrer las rondas una por
una con las flechas.

## Criterios de aceptacion

- [ ] Logica pura (en `navegacionRondas.js` o un modulo vecino): dado el
      indice elegido y `rounds`, devuelve el indice de la proxima ronda con
      `my_team_won === false` despues de la elegida, dando la vuelta; las
      rondas sin ganador (`my_team_won` nulo) no cuentan como perdidas; sin
      ninguna perdida (o con la elegida como unica perdida) devuelve null o la
      misma, segun se fije en el diseno. vitest con vuelta al final, ronda sin
      ganador salteada y partida sin perdidas.
- [ ] La tecla `p` hace el salto con las mismas exclusiones que las flechas
      (`pasoDeTecla`: no en campos, no con modificadores, no si otro widget
      la tomo). vitest.
- [ ] En `MatchDetail.jsx`, un boton con nombre accesible junto a las
      pestañas de ronda; deshabilitado (o ausente) en una partida sin rondas
      perdidas; el salto actualiza el ancla `#ronda-N` como cambiar de ronda
      a mano. e2e sobre `seed_demo`: elegir R1, apretar el boton, la ronda
      elegida es la primera perdida que da `/api/matches/<id>/`; con `p`
      igual; consola limpia.
- [ ] El atajo figura donde la pagina ya explica las flechas (hint o
      `title`), con tildes.

## Fuera de alcance

- Saltar a la anterior perdida (Shift+p) o a la siguiente ganada.
- Filtrar las pestañas para que solo queden las perdidas.
- La misma navegacion en la comparacion de dos partidas.

## Diseno

## Implementacion

## Revision

## QA

## Para el humano

(nada)
