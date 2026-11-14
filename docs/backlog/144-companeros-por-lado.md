# 144. Compañeros por lado

estado: propuesto
candado: -
rama: -
tipo: funcionalidad
epica: escuadra
area: fullstack
prioridad: 3
fuente: ALCANCE.md C10
archivos: -
turnos: po 20261114T0104Z-choi73m

## PR

## Que gana quien usa la app

En Compañeros, tu winrate de ronda y tu rating con cada compañero habitual
partidos en ataque y defensa, en la misma tabla: hay duos que funcionan
atacando y se hunden defendiendo, y el numero junto los esconde. Hoy hay que
poner el filtro de lado y comparar dos pantallas a ojo.

## Criterios de aceptacion

- [ ] El agregado de sinergia (`teammate_synergy` o una vecina) devuelve
      por compañero, ademas del total, `attack` y `defense` con
      `rounds`, `won`, `winrate` y `rating` de tus rondas con el en ese
      lado (el lado de tu fila, `RoundPlayer.side`). Test con un compañero
      con 3 rondas de ataque ganadas y 2 de defensa perdidas.
- [ ] La suma de rondas de ataque y defensa de un compañero es su total
      menos las rondas de lado vacio. Test.
- [ ] Los filtros globales aplican igual que hoy; con el filtro de lado
      puesto, la columna del otro lado queda en 0 y la UI la muestra como
      `—`. Test de API con `side=Attack`.
- [ ] En la pagina Compañeros, columnas por lado (o un selector Total /
      Ataque / Defensa en la tabla) con aviso de muestra chica por lado,
      con el mismo corte de rondas que la tabla ya usa. e2e con
      `seed_demo`: los numeros de un compañero salen de la API y la consola
      queda limpia.
- [ ] La fila de Compañeros en `docs/metricas.md` dice como se parte por
      lado.

## Fuera de alcance

- Lado por compañero en su perfil (`/jugadores/<id>`).
- Grupos exactos de compañeros (C1).
- Cambiar el minimo de rondas de la tabla.

## Diseno

## Implementacion

## Revision

## QA

## Para el humano

(nada)
