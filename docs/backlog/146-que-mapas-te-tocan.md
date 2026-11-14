# 146. Que mapas te tocan semana a semana

estado: propuesto
candado: -
rama: -
tipo: funcionalidad
epica: progreso
area: fullstack
prioridad: 3
fuente: ALCANCE.md E11
archivos: -
turnos: po 20261114T0104Z-choi73m

## PR

## Que gana quien usa la app

En Tendencias, cuantas partidas jugaste en cada mapa por semana en las
ultimas 8 semanas, con tu winrate de partida al lado: ver como rota el pool,
que mapa te sale cada vez mas y si tus numeros de un mapa son de hace un mes.
Ninguna pantalla muestra hoy la frecuencia de un mapa en el tiempo.

## Criterios de aceptacion

- [ ] Un agregado devuelve las ultimas 8 semanas ISO con partidas (desde la
      ultima partida filtrada hacia atras, no desde hoy) y, por mapa (por
      version, como Mapas), `matches` por semana y `matches`, `wins` y
      `winrate` de partida en esas 8 semanas. Test con partidas en tres
      semanas y dos mapas.
- [ ] Las partidas sin resultado cuentan en `matches` y no en el winrate
      (como `match_result`). Test.
- [ ] Los filtros globales aplican (tipo, modo, fechas, sesion; lado,
      operador y sitio se ignoran como en `match_queryset`). Test de tipo.
- [ ] Panel en Tendencias: tabla mapa x semana con el conteo por celda (o
      grafico de barras apiladas, lo decide el diseno con `dataviz`) y el
      winrate al lado; sin partidas, un texto y no un error; e2e con
      `seed_demo` y la consola limpia. Fila nueva en `docs/metricas.md`.

## Fuera de alcance

- Comparar contra el pool oficial de la temporada (dato de Ubisoft).
- Winrate por semana de cada mapa (muestra demasiado chica por celda).

## Diseno

## Implementacion

## Revision

## QA

## Para el humano

(nada)
