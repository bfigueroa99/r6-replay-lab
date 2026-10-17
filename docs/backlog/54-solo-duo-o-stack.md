# 54. Solo, en duo o en stack

estado: propuesto
candado: arquitecto 2026-10-17T16:04Z
rama: -
tipo: funcionalidad
epica: escuadra
area: fullstack
prioridad: 3
fuente: ALCANCE.md C5 (historial acumulado: la app es la unica que ve con quien jugaste cada partida)
archivos: -
turnos: po 20261017T1204Z

## PR

(La escribe el Release manager al final.)

## Que gana quien usa la app

En Compañeros, tu winrate de partida y de ronda y tu rating segun cuantos
compañeros habituales jugaron esa partida con vos: solo (0), en duo (1),
con dos (2) o en stack de tres o mas. Responde si te conviene entrar solo o
esperar a tu grupo; `teammate_synergy` hoy lo mira de a un compañero.

## Criterios de aceptacion

- [ ] Habitual = un `Player` (no `is_me`) que estuvo en tu equipo
      (`team_index` igual al tuyo en la misma ronda) en 5 o mas partidas
      distintas de todo tu historial, sin aplicar los filtros de la consulta
      (asi un filtro de mapa no cambia quien es habitual). El 5 es una
      constante del modulo, sin ajuste en la UI.
- [ ] `/api/teammates/` (`views.teammates`) trae la clave
      nueva `by_stack`: filas `solo`, `duo`, `trio` y `stack` (3 o mas
      habituales), cada una con `matches`, `matches_won`, `match_winrate`,
      `rounds`, `rounds_won`, `winrate` y `rating`. Una partida cuenta en
      una sola fila, por los habituales distintos que aparecen en tu equipo
      en cualquiera de sus rondas.
- [ ] Partida sin resultado (`Match.result` vacio o empate) cuenta en
      `matches` y en las rondas, no en `match_winrate`. Test con una partida
      de cada fila, un empate y un cambio de nick de un habitual (sigue
      siendo el mismo `Player`).
- [ ] Los filtros de siempre recortan que partidas y rondas entran; con base
      vacia o sin habituales, `by_stack` existe con las cuatro filas y todo
      en `solo` o en 0.
- [ ] Compañeros muestra el panel "Solo, en duo o en stack" con las cuatro
      filas; el e2e lo encuentra con datos de `seed_demo` y la consola queda
      limpia.
- [ ] `docs/metricas.md` tiene la fila **Tamaño del grupo** con la
      definicion de habitual y el aviso de que el umbral se mide sobre todo
      el historial.

## Fuera de alcance

- Winrate por grupo exacto de compañeros (C1).
- Umbral de habitual configurable.
- Lado (C10) o mapa por tamaño de grupo.

## Para el humano

El umbral de 5 partidas sale de C5 y no se calibro con la base real. Si en
tu historial casi todo cae en `solo`, se baja en el diseno; es reversible.
