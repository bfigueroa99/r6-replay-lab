# 147. Headshots que recibes por operador rival

estado: propuesto
candado: -
rama: -
tipo: funcionalidad
epica: rivales
area: fullstack
prioridad: 3
fuente: ALCANCE.md D20 (Fuera de alcance de la ficha 137: "Partirlo por operador rival (otro tramo)")
archivos: -
turnos: po 20261114T0316Z-cwWsU9i

## PR

## Que gana quien usa la app

En Duelos, de tus muertes a manos de cada operador rival, que % fueron
headshot, al lado de tu % general: que operadores te enganchan la cabeza mas
que el resto, y contra cuales te asomas expuesto. Es el segundo tramo de la
137 (Muertes por headshot, por lado y contra tus compañeros), que da el
numero general; este lo parte por el operador que te mato. Implementar
despues de #137.

## Criterios de aceptacion

- [ ] Por operador rival que te mato (el operador de su fila en esa ronda,
      `op_rival` de `_solo_rivales`, como **Operador rival** de
      `metricas.md`): `deaths`, `with_data` (`headshot` no nulo),
      `headshots` y `pct` = headshots / with_data, con las reglas de la 137
      (sin teamkills ni bajas sin autor; un `headshot` nulo cuenta como
      muerte y no entra en el %). Test con dos operadores y una muerte sin
      dato.
- [ ] Cada fila trae tambien la diferencia en puntos contra tu % general
      (el `total` de *Tú* de la 137, con los mismos filtros). Test.
- [ ] Muestra minima con el selector "Muestra mínima" de Duelos
      (`min_duels`) sobre `with_data`, como la tabla *Por operador rival*:
      debajo la fila no sale. Test en el borde (n - 1 y n).
- [ ] Los filtros globales aplican sobre tu fila de la ronda; test con
      filtro de lado.
- [ ] Se ve en Duelos, dentro o debajo del panel "Muertes por headshot",
      como tabla Operador / Muertes con dato / % headshot / vs. tu %; sin
      filas, una nota. e2e con `seed_demo`, numeros de la API y consola
      limpia. Fila nueva en `docs/metricas.md`.

## Fuera de alcance

- Señal del Coach ("te enganchan la cabeza contra X").
- Partirlo por mapa o por tu operador.
- Las muertes de tus compañeros por operador rival.

## Diseno

## Implementacion

## Revision

## QA

## Para el humano

(nada)
