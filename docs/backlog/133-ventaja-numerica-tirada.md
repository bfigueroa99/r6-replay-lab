# 133. Ventaja numerica tirada

estado: propuesto
candado: -
rama: -
tipo: funcionalidad
epica: revision-de-rondas
area: fullstack
prioridad: 3
fuente: ALCANCE.md F5
archivos: -
turnos: po 20261113T1926Z-ce4Pmp6

## PR

## Que gana quien usa la app

Cuantas rondas perdio tu equipo despues de quedar con un jugador mas (o
dos), por lado y por mapa, con enlace a cada una para volver a verla. Es el
error que mas duele y el marcador no lo muestra; hoy solo lo cuenta la
narrativa de una ronda suelta en el detalle de partida.

## Criterios de aceptacion

- [ ] Agregado nuevo en `aggregates.py`: recorre las bajas de cada ronda en
      orden de reloj (`Event` de baja con el `team_index` de la victima;
      los abandonos cuentan como baja, igual que en `stats.py`) y marca la
      ronda si tu equipo llego a tener mas vivos que el rival y la perdio
      (`Round.my_team_won = False`). Rondas sin ganador no cuentan. Devuelve
      el total de rondas con ventaja, cuantas se tiraron y el %, por lado y
      por mapa. Test con una ronda 5v4 ganada, una 5v4 perdida y una sin
      ventaja.
- [ ] Separa ventaja de uno y de dos o mas (la maxima de la ronda). Test con
      una ronda que llego a 5v3.
- [ ] Lista de las rondas tiradas (partida, numero de ronda, mapa, lado,
      ventaja maxima) con enlace al detalle de la ronda, mas recientes
      primero y con tope; test del orden y del tope.
- [ ] Los filtros globales aplican sobre tu fila de la ronda; test con
      filtro de lado.
- [ ] Panel en una pagina que no este en `saturadas` de `ROTACION` (hoy
      Tendencias lo esta), con su nota sin rondas; e2e sobre `seed_demo`
      con los numeros de la API y consola limpia.
- [ ] Fila nueva en `docs/metricas.md` (y en `## Muestra minima` si avisa
      muestra chica).

## Fuera de alcance

- El reverso, rondas dadas vuelta en inferioridad (F12).
- Quien murio despues de la ventaja.
- Señales del Coach sobre esto.

## Diseno

## Implementacion

## Revision

## QA

## Para el humano

(nada)
