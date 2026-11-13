# 131. Rondas que el equipo gano sin ti

estado: propuesto
candado: -
rama: -
tipo: funcionalidad
epica: escuadra
area: fullstack
prioridad: 3
fuente: ALCANCE.md C13
archivos: -
turnos: po 20261113T1858Z-cxQ3TuB

## PR

## Que gana quien usa la app

En Compañeros, de las rondas en que caiste, cuantas igual gano tu equipo, por
lado, y que compañero habitual seguia vivo al final de esas rondas: si el
equipo te cubre cuando mueres y quien cierra las rondas por ti. Hoy solo se ve
tu winrate cuando moris, no quien lo sostiene.

## Criterios de aceptacion

- [ ] Agregado nuevo en `aggregates.py`: sobre tus filas con `died=True` y
      ronda con ganador (`round__my_team_won` no nulo), rondas, ganadas y %
      por lado (`Attack`, `Defense`) y total. Las rondas sin ganador no
      cuentan. Test con rondas armadas de resultado conocido.
- [ ] Por compañero habitual (5 partidas juntas, `MIN_PARTIDAS_HABITUAL`,
      agrupado por `Player`): en cuantas de esas rondas ganadas sin ti
      sobrevivio (`survived` en su fila, mismo `team_index` que la tuya).
      Test con dos compañeros y un no habitual que no sale.
- [ ] Los filtros globales aplican sobre tu fila (como `teammate_synergy`);
      test con filtro de lado.
- [ ] `/api/teammates/` suma la clave; en `Teammates.jsx` un panel o tabla
      con el total por lado y la lista de compañeros con su `n`; sin rondas,
      una nota. e2e sobre `seed_demo` con los numeros de la API y consola
      limpia.
- [ ] Fila nueva en `docs/metricas.md` (y en `## Muestra minima` si se avisa
      muestra chica).

## Fuera de alcance

- El reverso (rondas perdidas sobreviviendo, F11).
- Quien hizo las bajas despues de que caiste (otro tramo: necesita el feed).
- Señales del Coach sobre esto.

## Diseno

## Implementacion

## Revision

## QA

## Para el humano

(nada)
