# 116. En que estado de vivos mueres

estado: propuesto
candado: arquitecto 2026-11-13T16:49Z
rama: -
tipo: funcionalidad
epica: impacto
area: fullstack
prioridad: 3
fuente: ALCANCE.md K6
archivos: backend/replays/analytics/aggregates.py, backend/replays/views.py, frontend/src/pages/Duelos.jsx o Trends.jsx (lo decide el Arquitecto), docs/metricas.md
turnos: po 20261112T1603Z-cor3JBP

## PR

## Que gana quien usa la app

Tus muertes repartidas por el estado de vivos de la ronda en el instante en
que caes (5v5, 5v4, 4v5, 3v3...) y el winrate de la ronda en cada caso. Dice
si mueres regalando una ventaja o cuando la ronda ya estaba perdida, que el
K/D y las aperturas no separan.

## Criterios de aceptacion

- [ ] Un agregado devuelve, por estado `tuyos vivos v rivales vivos` justo
      antes de tu muerte, `deaths` y `winrate` de esas rondas (sobre las
      que tienen ganador). Test con una ronda armada: caes cuando ya habia
      caido un rival y ninguno de los tuyos cuenta en `5v4`.
- [ ] Un `PlayerLeave` cuenta como baja para el estado (como
      `pydissect/stats.py`), un teamkill tambien resta un vivo de tu equipo,
      y una muerte tuya sin evento en el feed no entra. Test de los tres.
- [ ] Ventaja, paridad y desventaja agregadas (`ahead`, `even`, `behind`)
      ademas del estado exacto, con su winrate. Test.
- [ ] Los filtros globales aplican (lado, mapa, operador, tipo, fechas,
      sesion). Test de lado.
- [ ] Se ve en la UI con la muestra minima de `metricas.md` como aviso; sin
      muertes, un texto y no un error; e2e de humo por esa pagina con la
      consola limpia. Fila nueva en `docs/metricas.md` ("Estado al morir").

## Fuera de alcance

- El reverso, tus bajas por estado (K8): otro tramo de la epica.
- Probabilidad de ganar por estado o impacto por baja (K1, K2).
- Partidas con menos de 5 por lado: el estado se cuenta con los jugadores
  que hay, sin normalizar a 5v5.

## Diseno

## Implementacion

## Revision

## QA

## Para el humano

(nada)
