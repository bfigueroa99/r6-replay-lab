# 39. Inercia entre rondas: como juegas despues de ganar y despues de perder

estado: propuesto
candado: arquitecto 2026-10-13T20:12Z
rama: -
tipo: funcionalidad
epica: lado-y-marcador
area: fullstack
prioridad: 2
fuente: ALCANCE.md B4 (idea del PO 20261013T0511Z); epica lado-y-marcador en curso (B1 en main por #25)
archivos: backend/replays/analytics/aggregates.py, backend/replays/views.py, frontend/src/pages/Trends.jsx, docs/metricas.md, backend/tests/, frontend/e2e/
turnos: po 20261013T1915Z

## PR

(La escribe el Release manager al final.)

## Que gana quien usa la app

Ver en Tendencias si una ronda perdida te arrastra a la siguiente: tu winrate
y tu rating en las rondas que vienen despues de ganar contra las que vienen
despues de perder. Es un dato que solo sale del historial acumulado y que
ninguna pantalla muestra hoy.

## Criterios de aceptacion

- [ ] `GET /api/trends/` devuelve `by_previous_round`: tres filas en orden fijo
      `after_win`, `after_loss`, `no_previous`, cada una con las metricas de
      `totals()` (rondas, ganadas, winrate, rating, KPR...). La ronda anterior
      es la de `number - 1` de la misma partida; su resultado es
      `Round.my_team_won` de esa ronda.
- [ ] Va a `no_previous` la primera ronda de la partida, la que no tiene
      ronda `number - 1` importada (falta el `.rec`) y la que tiene la
      anterior con `my_team_won` nulo. Ninguna ronda queda contada en dos
      filas: la suma de `rounds` de las tres filas es igual a `rounds` de
      `/api/overview/` con los mismos filtros (test).
- [ ] La ronda anterior se lee de la partida entera, no del queryset
      filtrado: con `?side=Attack` una ronda de ataque cuya anterior fue de
      defensa sigue cayendo en `after_win`/`after_loss` (test, igual que
      `_lado_inicial` en `by_half`).
- [ ] Tendencias muestra el panel "Despues de ganar o perder la ronda
      anterior" con las tres filas y CSV, con la banda de ruido o un aviso de
      muestra chica cuando alguna fila tiene menos de 30 rondas.
- [ ] `docs/metricas.md` tiene la fila de la metrica; el e2e de Tendencias
      ve el panel con los datos de `seed_demo` sin errores de consola.
- [ ] Base vacia y filtros raros (`days=-1`, `since=foo`, `map=%00`)
      devuelven 200 con las tres filas en 0.

## Fuera de alcance

- Rachas de mas de una ronda (despues de 2 o 3 perdidas seguidas): otra ficha
  si esta sale util.
- Marcador antes de la ronda (adelante, empatado, atras): ficha 41.
- Cualquier cambio en el Coach o en las reglas de señales.

## Diseno

(Arquitecto)

## Para el humano

Nada por ahora.
