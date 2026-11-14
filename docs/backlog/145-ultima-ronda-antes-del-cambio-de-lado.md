# 145. La ultima ronda antes del cambio de lado

estado: propuesto
candado: -
rama: -
tipo: funcionalidad
epica: lado-y-marcador
area: fullstack
prioridad: 3
fuente: ALCANCE.md B20 (reverso de la ficha 58, primera ronda de cada mitad)
archivos: -
turnos: po 20261114T0104Z-choi73m

## PR

## Que gana quien usa la app

Tu winrate en la ronda que cierra cada mitad (la ultima antes de cambiar de
lado, sin prorroga) contra el resto de tus rondas de ese lado: si el equipo
afloja o aprieta cuando sabe que cambia. La ficha 58 ya mide la primera ronda
de cada mitad; esta mira la otra punta.

## Criterios de aceptacion

- [ ] Un agregado devuelve, por lado (`Attack`, `Defense`), `rounds`,
      `won` y `winrate` de las ultimas rondas de mitad y del resto de tus
      rondas de ese lado. La ultima de la mitad es la anterior a la primera
      tras el cambio (la regla de la ficha 58, `_primera_tras_el_cambio`),
      nunca una de prorroga. Test con una partida de 8 rondas con cambio en
      la R5: la R4 es la ultima de la mitad.
- [ ] Una partida que termino antes del cambio no tiene ultima de mitad: sus
      rondas van al resto. Test.
- [ ] Rondas sin ganador no entran al winrate (como el resto de las tablas
      de ronda). Test.
- [ ] Los filtros globales aplican sobre tu fila. Test de mapa.
- [ ] Se ve en Tendencias junto a la tabla de la primera ronda de cada mitad,
      con su `n` y aviso de muestra chica; e2e con `seed_demo` y la consola
      limpia. Fila nueva en `docs/metricas.md`.

## Fuera de alcance

- La ronda de match point (ficha 43).
- Prorroga: el cambio de lado en prorroga es otra regla (ficha 115).

## Diseno

## Implementacion

## Revision

## QA

## Para el humano

(nada)
