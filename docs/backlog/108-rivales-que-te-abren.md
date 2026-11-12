# 108. Rivales que te abren

estado: propuesto
candado: arquitecto 2026-11-12T12:15Z
rama: -
tipo: funcionalidad
epica: rivales
area: fullstack
prioridad: 3
fuente: ALCANCE.md D11 (PO 20261105T1945Z-cvqUYh1)
archivos: backend/replays/analytics/aggregates.py, backend/replays/views.py (duels), frontend/src/pages/Duelos.jsx, docs/metricas.md
turnos: po 20261112T1127Z-cT8M5Vz

## PR

## Que gana quien usa la app

En Duelos, por rival repetido: en cuantas rondas fue el que te saco a ti como
primera baja de la ronda y en cuantas lo abriste tu a el. Muestra al jugador
que te lee la entrada partida tras partida, que no siempre es el que mas te
mata: Nemesis cuenta todos los duelos, y la tabla por operador no los separa
por persona.

## Criterios de aceptacion

- [ ] `/api/duels/` devuelve una clave nueva con, por rival (mismo criterio
      de identidad y de "repetido" que `nemesis`): `opened_you` (rondas donde
      la primera `Kill` por `order` fue de el sobre ti), `you_opened` (tuya
      sobre el), `rounds` contigo y el balance. Test con dos rondas armadas
      donde el rival te abre en una y tu a el en la otra.
- [ ] Los teamkills y las bajas sin autor no cuentan como apertura entre
      ustedes (la primera baja de la ronda sigue siendo la que es: si fue un
      teamkill, esa ronda no suma a nadie). Test.
- [ ] Respeta `min_duels` (o una muestra minima propia, documentada) y los
      filtros globales; ordenada por `opened_you` descendente.
- [ ] La tabla se ve en Duelos; sin datos, un texto vacio y no un error. El
      e2e de humo pasa por Duelos con la consola limpia.
- [ ] Fila nueva en `docs/metricas.md` ("Rivales que te abren").

## Fuera de alcance

- Que operador te abre (D7) y rivales que te clutchean (D12).
- Aperturas entre compañeros y rivales que no son tu.

## Diseno

## Implementacion

## Revision

## QA

## Para el humano

(nada)
