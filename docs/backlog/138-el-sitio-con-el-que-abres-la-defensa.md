# 138. El sitio con el que abres la defensa

estado: propuesto
candado: -
rama: -
tipo: funcionalidad
epica: posicionamiento
area: fullstack
prioridad: 3
fuente: ALCANCE.md S7
archivos: -
turnos: po 20261113T2157Z-cG2vDSe

## PR

## Que gana quien usa la app

En el Coach, por mapa, que sitio defiende tu equipo en la primera ronda de
defensa de cada partida, cuantas veces y con que winrate esa ronda, contra el
winrate de ese sitio en el resto de tus rondas de defensa: si tu apertura en
defensa es predecible y si arrancar ahi te cuesta.

## Criterios de aceptacion

- [ ] Agregado nuevo: primera ronda de defensa = la de menor `Round.number`
      con `my_side="Defense"` de la partida, leida de la partida entera (como
      `_primera_ronda`); si falta una ronda antes (hueco de numeracion desde
      la primera ronda de la partida) o no tiene sitio, la partida no entra.
      Por mapa (con su version) y sitio: `opens` (partidas que abrieron
      ahi), `opens_decided`, `opens_winrate`, y `rest_rounds`,
      `rest_winrate` del mismo sitio en las demas rondas de defensa. Test con
      tres partidas y un hueco.
- [ ] Una ronda sin ganador cuenta en las rondas y no en el winrate. Test.
- [ ] Filtros globales de partida (mapa, tipo, modo, fechas, sesion) aplican;
      lado y operador no (es siempre defensa y del equipo), como "Repetir el
      sitio tras perderlo". Test con filtro de mapa.
- [ ] Se ve en el Coach, junto a "Repetir el sitio tras perderlo", con aviso
      de muestra (se avisa, no se oculta) y una nota sin datos; e2e sobre
      `seed_demo` con los numeros de la API y consola limpia.
- [ ] Fila nueva en `docs/metricas.md`.

## Fuera de alcance

- El sitio con el que abres tras el cambio de lado o en prorroga.
- Recomendar un sitio.

## Diseno

## Implementacion

## Revision

## QA

## Para el humano

(nada)
