# 46. Primero de tu equipo en caer

estado: propuesto
candado: arquitecto 2026-10-14T23:11Z
rama: -
tipo: funcionalidad
epica: escuadra
area: fullstack
prioridad: 3
fuente: ALCANCE.md C4 (idea del PO); abre la epica escuadra (C1-C5 libres)
archivos: -
turnos: po 20261014T1911Z

## PR

(La escribe el Release manager al final.)

## Que gana quien usa la app

Hoy la app cuenta tu "primera muerte" solo cuando eres la primera baja de
toda la ronda. Con esto ves cuantas rondas eres el primero de tu equipo en
caer (aunque ya haya muerto un rival) y el winrate de esas rondas contra
las que cae primero un compañero, por lado: si tu forma de abrir le cuesta
rondas al equipo.

## Criterios de aceptacion

- [ ] Agregado nuevo (p. ej. `first_teammate_death` en `aggregates.py`)
      que, por ronda con al menos una muerte de tu equipo, decide quien
      cayo primero de tu equipo comparando `RoundPlayer.death_elapsed` de
      las filas con tu `team_index`. Devuelve por lado (`Attack`,
      `Defense`, total): rondas en que caiste primero, rondas en que cayo
      primero un compañero, rondas sin muertes de tu equipo, y el winrate
      de ronda de cada grupo.
- [ ] Una ronda donde murio primero un rival y despues tu, antes que tus
      compañeros, cuenta como "caiste primero" aunque `opening_death` sea
      falso. Test con esa ronda exacta.
- [ ] Empate de `death_elapsed` entre tu y un compañero (mismo segundo):
      la regla queda escrita en el diseno y tiene test. Filas con
      `death_elapsed` nulo (no moriste) nunca cuentan como primera muerte.
- [ ] Sale en `/api/teammates/` (o el endpoint que fije el diseno) y
      respeta los filtros de la barra; base vacia y filtros raros dan 200.
- [ ] La pagina Compañeros muestra un panel "Primero en caer" con la tabla
      por lado; el e2e lo afirma sobre `seed_demo`.
- [ ] Fila en `docs/metricas.md` ("Primero de tu equipo en caer" y su
      winrate), distinguiendola de "Primera muerte" de la ronda.

## Fuera de alcance

- Desglose por compañero (quien cae primero mas seguido): puede ser el
  siguiente tramo de la epica escuadra.
- Cambiar la definicion de `opening_death`: se queda como esta (P10).
- Abandonos (`PLAYER_LEAVE`) como caso aparte: cuentan como muerte, igual
  que en `stats.py`, sin desglose (eso es D3).

## Diseno

## Implementacion

## Revision

## QA

## Para el humano
