# 119. Mejor y peor partida de cada sesion

estado: propuesto
candado: arquitecto 2026-11-13T17:08Z
rama: -
tipo: funcionalidad
epica: progreso
area: fullstack
prioridad: 3
fuente: ALCANCE.md E18
archivos: -
turnos: po 20261113T0404Z-cnRfz4a

## PR

## Que gana quien usa la app

En Tendencias, cada sesion dice cual fue su mejor y su peor partida (por
rating, con mapa y marcador) y enlaza a las dos: se ve de un vistazo si la
noche se cayo en una sola partida o fue pareja, cosa que los totales de la
sesion esconden.

## Criterios de aceptacion

- [ ] `sessions()` (`aggregates.py`) suma a cada sesion `best_match` y
      `worst_match` (`id`, `map`, marcador, `rating`), por el rating de
      la partida calculado como `trend_by_match` (`totals()` por partida);
      test con una sesion de 3 partidas de rating conocido.
- [ ] Una sesion de una sola partida trae `best_match` y `worst_match`
      `null` (no hay reparto que mostrar); test. Empate de rating: gana la
      partida mas vieja, determinista; test.
- [ ] Los filtros que ya aplican a `sessions()` aplican igual (la partida
      mejor y peor sale de las rondas filtradas); test con filtro de mapa.
- [ ] En Tendencias, la tabla de sesiones muestra "Mejor" y "Peor" con mapa,
      marcador y rating, cada una enlazada a `/partidas/<id>`; con una sola
      partida, `—`. e2e sobre `seed_demo` con el numero de una fila y la
      consola limpia.
- [ ] Fila nueva en `docs/metricas.md` ("Mejor y peor partida de la
      sesion").

## Fuera de alcance

- Elegir el criterio (KD, winrate de rondas): se usa el rating, el mismo de
  Tendencias por partida.
- Mejor y peor ronda de la sesion (F9 elige la ronda para revisar).

## Para el humano

(nada)
