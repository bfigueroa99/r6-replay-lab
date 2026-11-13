# 125. Teamkill marcado en la timeline de la ronda

estado: propuesto
candado: -
rama: -
tipo: funcionalidad
epica: revision-de-rondas
area: frontend
prioridad: 3
fuente: ALCANCE.md F14
archivos: -
turnos: po 20261113T1703Z-ctZvzXQ

## PR

## Que gana quien usa la app

En la timeline de una ronda del detalle de partida, una baja entre
compañeros lleva un chip "TK" y no se pinta como baja de tu equipo ni del
rival: desde la ficha 67 los teamkills no suman a las bajas, y hoy el feed
los muestra igual que cualquier baja, asi que el numero de la ronda no
cuadra con lo que se lee.

## Criterios de aceptacion

- [ ] Funcion pura nueva en el frontend que dice si un evento es teamkill:
      `kind == "Kill"` y autor y victima estan en `players` de la ronda con
      el mismo `team_index` (la misma comparacion por nick que `_teamkills`
      de `aggregates.py`). Vitest: teamkill, baja a un rival, autor o
      victima que no esta entre los jugadores de la ronda (no es teamkill) y
      evento `Death` (no es teamkill).
- [ ] La linea de un teamkill en la timeline lleva el chip `TK` con
      `title` "Baja entre compañeros: no suma a las bajas", junto a `HS` y
      `tradeada`, y no lleva la clase `mine` ni `against`.
- [ ] Una ronda sin teamkills se ve igual que hoy (el e2e
      `el timeline marca la apertura de cada ronda` sigue verde sin cambios).
- [ ] e2e: con la respuesta de `/api/matches/<id>/` interceptada (como
      `una partida sin rondas muestra su cabecera y un aviso`) para que una
      baja de la primera ronda sea entre dos jugadores del mismo equipo, el
      chip `TK` aparece en esa linea y en ninguna otra; consola limpia.
- [ ] Si la ficha 121 (copiar una ronda como texto) ya esta en dev al
      implementar, el texto copiado marca la misma baja con `TK` entre sus
      marcas; vitest. Si no esta, esta casilla no aplica y la 121 queda
      avisada en `## Para el humano` de esta ficha.

## Fuera de alcance

- Cambiar como se cuentan los teamkills (ficha 67) o la matriz de duelos.
- Marcar teamkills fuera del detalle de partida.
- Backend: `/api/matches/<id>/` ya trae `team_index` de cada jugador y
  autor y victima de cada evento.

## Diseno

## Implementacion

## Revision

## QA

## Para el humano

(nada)
