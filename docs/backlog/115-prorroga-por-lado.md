# 115. Prorroga por lado

estado: propuesto
candado: arquitecto 2026-11-12T20:25Z
rama: -
tipo: funcionalidad
epica: lado-y-marcador
area: fullstack
prioridad: 3
fuente: ALCANCE.md B18
archivos: backend/replays/analytics/aggregates.py (by_half), backend/replays/views.py, frontend/src/pages/Trends.jsx, docs/metricas.md
turnos: po 20261112T1603Z-cor3JBP

## PR

## Que gana quien usa la app

En Tendencias, la fila de prorroga se parte en ataque y defensa: winrate de
ronda y rating en las rondas de prorroga segun el lado que te toco. Responde
si en la prorroga defiendes mejor de lo que atacas, que la fila unica de hoy
no separa.

## Criterios de aceptacion

- [ ] El corte por mitad (`by_half` o una clave nueva de la misma respuesta)
      devuelve, para `overtime`, una fila por lado (`Attack`, `Defense`)
      con `rounds`, `winrate` y `rating` de las rondas con
      `Round.overtime_number > 0`. Test con una partida armada: dos rondas
      de prorroga en ataque ganadas y una en defensa perdida dan 100 % y 0 %.
- [ ] Las filas de primera y segunda mitad no cambian (test que compara la
      respuesta de esas filas antes y despues).
- [ ] Los filtros globales aplican; con el filtro de lado solo sale la fila
      de ese lado. Test.
- [ ] Se ve en Tendencias junto a la fila de prorroga actual, con el aviso
      de muestra minima de los cortes de Tendencias (30 rondas: se avisa,
      no se oculta); sin prorrogas, un texto y no un error. El e2e de humo
      pasa por Tendencias con la consola limpia.
- [ ] `docs/metricas.md` actualiza la fila de mitades y prorroga con el
      corte por lado.

## Fuera de alcance

- Winrate de partida de las que fueron a prorroga segun el lado (otro tramo).
- Lado inicial de la prorroga o quien la elige: el `.rec` no lo dice.
- Prorroga en modos sin regla de partida (A9).

## Diseno

## Implementacion

## Revision

## QA

## Para el humano

(nada)
