# 108. Rivales que te abren

estado: descartado (premisa falsa: Duelos, tabla Por rival, ya tiene la columna De apertura con le abriste-te abrió por rival, con el mismo criterio de nemesis, sin teamkills y con los filtros globales)
candado: -
rama: -
tipo: funcionalidad
epica: rivales
area: fullstack
prioridad: 3
fuente: ALCANCE.md D11 (PO 20261105T1945Z-cvqUYh1)
archivos: backend/replays/analytics/aggregates.py, backend/replays/views.py (duels), frontend/src/pages/Duelos.jsx, docs/metricas.md
turnos: po 20261112T1127Z-cT8M5Vz, arquitecto 20261112T1204Z-chGLrtC

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

(arquitecto 20261112T1204Z-chGLrtC) **Descartada: premisa falsa.** `agg.nemesis`
(`aggregates.py`, ~linea 2714) ya suma por rival `opening_deaths` (la
primera baja de la ronda, `_PRIMER_EVENTO`, fue de el sobre ti) y
`opening_kills` (tuya sobre el), sobre `_solo_rivales` (los teamkills y las
bajas sin autor no cuentan: si la primera baja fue un teamkill, la ronda no
suma a nadie, justo lo que pide el segundo criterio). `Duelos.jsx` lo muestra
en la tabla **Por rival**, columna **De apertura** (`k-d`), con `min_duels`
y los filtros globales. Lo unico que la ficha agrega es ordenar por
`opened_you`, y la tabla ya ordena por columna: no hay nada que el usuario
gane. Si se quiere, una mejora chica (ordenar "De apertura" por
`opening_deaths` en vez de `opening_duels`) es cosmetica y no paga ficha.

## Implementacion

## Revision

## QA

## Para el humano

(nada)
