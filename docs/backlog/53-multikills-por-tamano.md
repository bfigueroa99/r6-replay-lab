# 53. Multikills por tamaño: 2K, 3K, 4K y ace

estado: propuesto
candado: arquitecto 2026-10-17T16:04Z
rama: -
tipo: funcionalidad
epica: revision-de-rondas
area: fullstack
prioridad: 3
fuente: ALCANCE.md F10 ([CS Demo Manager](https://cs-demo-manager.com/changelog), [vlr.gg](https://www.vlr.gg/188013/velaris-vs-clg-red-complexity-paradox-invitational-playoffs-lr3/?game=all&tab=performance))
archivos: -
turnos: po 20261017T1204Z

## PR

(La escribe el Release manager al final.)

## Que gana quien usa la app

Ver cuantas rondas de 2, 3 y 4 bajas hiciste y cuantos aces, en el
scoreboard de cada partida y en la pagina de un jugador. Hoy existe
`multikill_rounds` (2 o mas) y `triple_plus_rounds` (3 o mas) en
`AGGREGATES` (`aggregates.py:147`), pero ninguna pantalla muestra multikills:
`grep -i multi frontend/src` no encuentra nada.

## Criterios de aceptacion

- [ ] `_match_scoreboard` (`views.py:515`) agrega por fila `k2`, `k3`, `k4`
      y `aces`: rondas de ese jugador con exactamente 2, 3, 4 y 5 o mas
      bajas. Test con un jugador con una ronda de cada tamaño y una de 6
      bajas (cuenta como ace).
- [ ] `/api/matches/<id>/` las devuelve en `scoreboard` y en `my_totals`;
      el scoreboard de `MatchDetail.jsx` muestra una columna "Multikills"
      con el formato `2K·3K·4K·ACE` solo con los tamaños mayores que 0
      (vacio si no hubo ninguno), ordenable por el total de rondas con 2 o
      mas bajas.
- [ ] El perfil de jugador (`player_profile`, pagina Jugador) muestra los
      mismos cuatro conteos sobre todas las rondas filtradas de ese jugador,
      y los mismos para vos en el Resumen (`overview`). Las claves nuevas
      salen de `AGGREGATES`/`derive` para que cualquier tabla agrupada las
      tenga sin codigo extra.
- [ ] Teamkills no suman: `RoundPlayer.kills` ya los excluye o no; el test
      fija el comportamiento actual de `kills` y la fila de `docs/metricas.md`
      lo dice.
- [ ] `docs/metricas.md` cambia la fila **Multikill** a la definicion por
      tamaño (2K, 3K, 4K exactos; ace = 5 o mas) sin cambiar `multikill_pct`.
- [ ] El e2e abre una partida de `seed_demo` y encuentra la columna
      "Multikills"; consola limpia.

## Fuera de alcance

- Duracion del multikill (F8) y records por tamaño (E4 ya tiene "mas bajas
  en una ronda").
- Filtro de rondas por tamaño (va con el buscador F1).
- Cambiar `multikill_pct` o el rating.
