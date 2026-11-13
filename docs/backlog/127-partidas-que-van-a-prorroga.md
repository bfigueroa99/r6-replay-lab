# 127. Partidas que van a prorroga: cuantas ganas

estado: propuesto
candado: -
rama: -
tipo: funcionalidad
epica: lado-y-marcador
area: fullstack
prioridad: 3
fuente: ALCANCE.md B22 (salio del Fuera de alcance de la 115)
archivos: -
turnos: po 20261113T1858Z-cxdASk3

## PR

## Que gana quien usa la app

En Tendencias, junto a la prorroga por lado de la 115 (winrate de ronda), el
winrate de partida de las que llegaron a prorroga, en la misma tabla,, partido por el lado con el
que la arrancaste: lo que se juega en la prorroga es la partida, no una ronda.
Responde "cuando llego a prorroga en defensa, ¿la gano?".

## Criterios de aceptacion

- [ ] Un agregado nuevo en `replays/analytics/aggregates.py` devuelve, por
      lado de tu primera ronda de prorroga (`Round.overtime_number` mas bajo
      `> 0` de la partida, su `Round.my_side`), `matches`, `won`,
      `decided` y `winrate` (sobre las partidas con `Match.won` no nulo).
      Test con tres partidas a prorroga (dos arrancadas en defensa, una
      ganada; una en ataque, ganada) -> defensa 2 partidas 50 %, ataque 1
      partida 100 %.
- [ ] Una partida sin prorroga no entra; una con `won` nulo cuenta en
      `matches` y no en `decided` ni en el winrate. Test.
- [ ] Los filtros globales de partida (mapa, tipo, modo, fechas) aplican; con
      `?side=` solo sale la fila de ese lado (como `by_overtime_side`). Test.
- [ ] Se ve en Tendencias como columnas nuevas (Partidas, % ganadas) de la
      tabla de prorroga por lado de la 115, sin tarjeta nueva (la pagina esta
      en `saturadas` de `ROTACION`), con el aviso de muestra de la pagina (se
      avisa, no se oculta); un lado sin partidas a prorroga muestra `—`. e2e
      de humo pasa por ahi con la consola limpia.
- [ ] Fila nueva en `docs/metricas.md` ("Partidas a prorroga por lado").

## Fuera de alcance

- Winrate de ronda en prorroga (ya lo da la 115).
- Partir por cuantas prorrogas hubo o por el marcador al llegar.
- Sumarlo al Coach como señal.

## Diseno

## Implementacion

## Revision

## QA

## Para el humano

(nada)
