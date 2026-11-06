# 98. Lado inicial por mapa

estado: propuesto
candado: -
rama: -
tipo: funcionalidad
epica: lado-y-marcador
area: fullstack
prioridad: 3
fuente: B17 de ALCANCE.md; [Siege.GG, win probability](https://siege.gg/news/how-analysts-estimate-win-probability-in-pro-siege-matches) (2026-04-27: "A team starting on defense may carry a higher early probability simply because of the map's structure"); investigador 2026-11-03
archivos: backend/replays/analytics/aggregates.py (by_start_side), backend/replays/views.py (trends), frontend/src/pages/Trends.jsx, backend/tests/, frontend/e2e/, docs/metricas.md
turnos: po 20261106T0319Z-cqz8j6p

## PR

(La escribe el Release manager al final.)

## Que gana quien usa la app

Hoy Tendencias dice tu winrate de partida segun arrancaste atacando o
defendiendo, pero junta todos los mapas, y el lado que conviene cambia de un
mapa a otro. Con esto se ve, mapa por mapa, si te va mejor arrancando en
defensa o en ataque ("en Bank gano mas arrancando en defensa"), con la
muestra a la vista para no leer ruido.

## Criterios de aceptacion

- [ ] `GET /api/trends/` agrega `by_start_side_map`: una fila por mapa (la
      misma clave y etiqueta con version que `by_map`, fichas 70 y 74, asi
      "Consulate (Y10)" no se mezcla con la vieja) con, para `Attack` y
      `Defense` como lado inicial, `matches`, `decided`, `wins` y
      `winrate` (el mismo `_lado_inicial` y el mismo criterio de
      `by_start_side`: `Match.won = None` cuenta en `matches` y no en el %).
      Test: dos partidas en Bank arrancando en defensa (G, P), una en Bank en
      ataque (G) y una en Oregon en ataque (P) dan las cuatro celdas a mano.
- [ ] Cada fila trae la diferencia en puntos entre los dos lados y su banda
      de ruido (`_ruido` de `aggregates.py`, la de Tendencias); con menos
      partidas decididas que el minimo por lado (`MIN_PARTIDAS_MAPA`, 3, de
      la ficha 64, o la constante que fije el Arquitecto) el lado sale con
      `winrate: null` y la fila no da veredicto. Test con un lado de 2
      partidas.
- [ ] Los filtros de la barra se respetan como en `by_start_side` (mapa,
      tipo, fechas, sesion); el filtro de lado no parte la partida (el lado
      inicial se lee de `Round`, no de las rondas filtradas). Test con
      `side=Attack` que deja las mismas partidas.
- [ ] En Tendencias, al lado del panel "Lado inicial", una tabla "Lado
      inicial por mapa" (mapa, partidas y winrate arrancando en ataque, lo
      mismo en defensa, diferencia con banda de ruido), ordenada por partidas;
      sin filas, un texto de vacio y no un panel en blanco. El e2e de
      Tendencias la renderiza con `seed_demo` y la consola limpia.
- [ ] Fila nueva en `docs/metricas.md` con la definicion y la muestra minima.

## Fuera de alcance

- Lado inicial por sitio o por operador.
- Llevarlo al Coach como señal (puede ser una idea aparte en `ALCANCE.md`
  cuando haya datos reales que calibren el minimo).
- Cambiar `by_start_side` global: sigue igual.
