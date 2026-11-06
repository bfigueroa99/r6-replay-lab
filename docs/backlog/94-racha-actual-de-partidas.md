# 94. Racha actual de partidas

estado: propuesto
candado: arquitecto 2026-11-06 00:15
rama: -
tipo: funcionalidad
epica: progreso
area: fullstack
prioridad: 3
fuente: E14 de ALCANCE.md (salio del PR #14, cerrado sin merge el 2026-11-05; la rama `claude/dazzling-einstein-w3qcyq` sirve de referencia)
archivos: -
turnos: po 20261105T1945Z-cvqUYh1

## PR

(La escribe el Release manager al final.)

## Que gana quien usa la app

En el Inicio, cuantas partidas seguidas llevas ganando o perdiendo ahora
("3 victorias seguidas", "2 derrotas seguidas"), al lado de la forma
reciente: saber de un vistazo si conviene seguir jugando o cortar. Hoy hay
que contar los puntos de la forma reciente a mano, y solo se ven 10.

## Criterios de aceptacion

- [ ] `GET /api/overview/` trae en `matches_summary` una clave
      `current_streak`: `{"result": "win"|"loss", "length": n, "since": <fecha
      de la primera partida de la racha>, "match_ids": [...]}`, o `null` si no
      hay ninguna partida decidida.
- [ ] Orden por `played_at` y `id` (igual que `matches_summary`); las
      partidas con `won=None` (incompletas o empate, ficha 68) no cortan ni
      suman la racha: test con G, None, G -> racha de 2 victorias.
- [ ] Se calcula sobre las partidas del filtro, como el resto de
      `matches_summary` (el lado no parte una partida): test con filtro de
      mapa que cambia la racha.
- [ ] Una racha de 1 se muestra igual ("1 victoria"); singular y plural
      correctos en la UI.
- [ ] El Inicio muestra la racha junto a la forma reciente, sin renderizar
      nada con `current_streak: null`; e2e con el numero que fija
      `seed_demo`.
- [ ] Fila nueva en `docs/metricas.md`.

## Fuera de alcance

- La racha mas larga de partidas (record): otra idea, junto a los records (E4).
- Racha de rondas (ya existe, ficha 60).
- Señal del Coach sobre la racha (E6 cubre "despues de perder seguido").

## Diseno

## Implementacion

## Revision

## QA

## Pendiente

## Para el humano
