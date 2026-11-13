# 134. En que estado de vivos matas

estado: propuesto
candado: arquitecto 2026-11-13T23:22Z
rama: -
tipo: funcionalidad
epica: impacto
area: backend
prioridad: 3
fuente: ALCANCE.md K8; Fuera de alcance de la ficha 116 ("el reverso, tus bajas por estado (K8): otro tramo de la epica")
archivos: -
turnos: po 20261113T1954Z-cfZTvvE

## PR

## Que gana quien usa la app

Tus bajas repartidas por el estado de vivos de la ronda en el instante en
que las haces (5v5, 5v4, 4v5, 2v3...) y el winrate de esas rondas: si tus
bajas abren ventajas o llegan cuando la ronda ya estaba decidida. Es el
reverso de Estado al morir (ficha 116), que ya esta en Duelos.

## Criterios de aceptacion

- [ ] Un agregado devuelve, por estado `tuyos vivos v rivales vivos` justo
      antes de cada baja tuya a un rival, `kills` y `winrate` de esas rondas
      (sobre las que tienen ganador; una ronda con dos bajas tuyas cuenta
      en los dos estados). Test con una ronda armada: tu primera baja en
      `5v5`, la segunda en `5v4`.
- [ ] Los teamkills no cuentan como baja tuya (como `kills` desde la
      ficha 67) pero si restan un vivo de tu equipo; un `PlayerLeave` resta
      un vivo (como `pydissect/stats.py`). Test de los dos.
- [ ] Ventaja, paridad y desventaja agregadas (`ahead`, `even`, `behind`)
      ademas del estado exacto, con su winrate, con la misma recorrida de
      vivos que `death_state` (`metrics.estado_al_morir` o su vecina). Test.
- [ ] Los filtros globales aplican (lado, mapa, operador, tipo, fechas,
      sesion). Test de lado.
- [ ] Se ve en Duelos junto a Estado al morir, con la muestra minima de
      `metricas.md` como aviso; sin bajas, un texto y no un error; e2e por
      esa pagina con la consola limpia. Fila nueva en `docs/metricas.md`
      ("Estado al matar").

## Fuera de alcance

- Probabilidad de ganar por estado o impacto por baja (K1, K2).
- Bajas de tus compañeros por estado.
- Partidas con menos de 5 por lado: el estado se cuenta con los jugadores
  que hay, sin normalizar a 5v5 (como la 116).

## Diseno

## Implementacion

## Revision

## QA

## Para el humano

(nada)
