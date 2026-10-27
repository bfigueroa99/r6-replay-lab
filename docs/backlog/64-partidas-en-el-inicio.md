# 64. Partidas en el Inicio: ganadas, rondas por partida y mejor y peor mapa

estado: propuesto
candado: -
rama: -
tipo: funcionalidad
epica: paridad-referencia
area: fullstack
prioridad: 3
fuente: ALCANCE.md R1 (replica/features.csv fila 11, must, clone partial; [aurelix](https://aurelix.app/))
archivos: -
turnos: po 20261027T1205Z

## PR

(La escribe el Release manager al final.)

## Que gana quien usa la app

El Inicio hoy cuenta todo en rondas; lo primero que uno quiere saber es
cuantas partidas gano. Este item suma una fila de partida al Inicio: partidas
ganadas sobre jugadas, rondas promedio por partida y tu mejor y peor mapa por
winrate de partida, con los mismos filtros que el resto de la pagina.

## Criterios de aceptacion

- [ ] `GET /api/overview/` trae en `total` (o en una clave nueva `matches_summary`)
      `matches_won`, `matches_lost`, `matches_decided` (con ganador) y
      `match_winrate` = ganadas / decididas; empates e incompletas
      (`Match.won` nulo) quedan fuera del denominador y se cuentan aparte
      (`matches_undecided`). Test con 3 ganadas, 1 perdida y 1 con `won=None`:
      75 %.
- [ ] Trae `rounds_per_match` = rondas importadas / partidas (un decimal),
      sobre las mismas partidas que cuentan los filtros. Test con partidas de 7 y 9
      rondas: 8.0.
- [ ] Trae `best_map` y `worst_map` (nombre, slug, partidas decididas y winrate
      de partida) entre los mapas con al menos la muestra minima de partidas que
      fije el diseno; con un solo mapa que la pase, el mismo mapa no sale como
      mejor y peor (el peor va `null`); sin ninguno, los dos `null`. Test con
      cada caso.
- [ ] Base vacia y filtros que no dejan partidas: 200, `match_winrate` y los
      mapas `null`, sin dividir por cero.
- [ ] El Inicio (`Dashboard.jsx`) muestra la fila nueva con textos en
      castellano ("Partidas ganadas", "Rondas por partida", "Mejor mapa", "Peor
      mapa"), y el e2e (`frontend/e2e/`) afirma que aparece con los numeros de
      `seed_demo`.
- [ ] Cada numero nuevo tiene fila en `docs/metricas.md`, con la muestra
      minima del mapa.

## Fuera de alcance

- "Partidas cerradas" (margen de 1 ronda): ya esta en Tendencias (ficha 50).
- Cambiar como se calcula `Match.won` o el empate que hoy se ve como
  "incompleta" (aviso de la ficha 54 en ESTADO.md): este item solo cuenta lo
  que `won` ya dice.
- Winrate de partida por lado, por operador o por compañero.

## Para el humano

(Nada por ahora.)
