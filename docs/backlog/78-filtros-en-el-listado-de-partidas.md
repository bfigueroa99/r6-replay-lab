# 78. Filtros en el listado de Partidas

estado: propuesto
candado: arquitecto 2026-11-05T03:49Z
rama: -
tipo: funcionalidad
epica: revision-de-rondas
area: fullstack
prioridad: 2
fuente: ALCANCE.md F16 (del PR #14, cerrado sin merge el 2026-11-05; rama claude/dazzling-einstein-w3qcyq como referencia, no se mergea)
archivos: backend/replays/views.py (match_list), frontend/src/pages/Matches.jsx, backend/tests, frontend/e2e/humo.spec.js
turnos: po 20261105T0230Z-c8Ahepa, arquitecto 20261105T0349Z-cfLc9Nn

## PR

(La escribe el Release manager al final.)

## Que gana quien usa la app

La pagina Partidas lista todo el historial de a 50 y no filtra nada: para
encontrar "mis derrotas en Bank de esta semana" hay que recorrerla entera.
Con filtros de mapa, periodo, tipo y resultado la lista se achica a lo que
uno busca y el total dice cuantas son.

## Criterios de aceptacion

- [ ] `/api/matches/?result=<victoria|derrota|empate|incompleta>` devuelve
      solo partidas con ese `Match.result`, y `total` cuenta las filtradas
      (test por cada valor sobre una base con las cuatro). Un valor
      desconocido da 400 o se ignora, pero nunca 500.
- [ ] `/api/matches/` acepta `days`, `since`/`until` y `session` con la
      misma semantica que `_filters` (test: una partida fuera del periodo no
      sale; una fecha con zona horaria no da 500, como la ficha 33).
      `map` y `match_type` siguen como hoy.
- [ ] La paginacion respeta los filtros: con 60 victorias, `offset=50` trae
      las 10 restantes y no partidas de otro resultado.
- [ ] `Matches.jsx` muestra la barra de filtros (mapa, periodo, tipo) y un
      selector de resultado; cambiar un filtro vuelve a la primera pagina y
      el subtitulo dice "N partidas" con el total filtrado.
- [ ] e2e: elegir "Derrota" en Partidas deja solo filas con chip de derrota
      y la consola queda limpia.

## Fuera de alcance

- Filtros por lado, operador o sitio: son de ronda, no de partida.
- Guardar los filtros en la URL (A10) y partida anterior/siguiente (F17).
- Ordenar del lado del servidor por columna.

## Diseno

## Implementacion

## Revision

## QA

## Para el humano

- (po) Si la barra compartida de `App` se reusa en Partidas, los filtros
  elegidos en Partidas siguen puestos al volver al Inicio, como en el resto de
  paginas. Variante conservadora: reusarla (coherente). Si preferis que
  Partidas tenga sus propios filtros, decilo en la ficha.
