# 57. Teamkills: a quien mataste y quien te mato

estado: propuesto
candado: -
rama: -
tipo: funcionalidad
epica: escuadra
area: fullstack
prioridad: 3
fuente: ALCANCE.md C7 ([Siege.GG](https://siege.gg/news/support-value-in-siege-explained-with-the-new-rating-model), "Teamkills per Round")
archivos: -
turnos: po 20261019T0004Z

## PR

(La escribe el Release manager al final.)

## Que gana quien usa la app

Los teamkills estan en el feed pero ninguna pantalla los muestra: Duelos los
descarta y las Bajas los suman sin avisar. Ver cuantos compañeros mataste,
cuantas veces te mato uno, con quien, y cuanto se pierde la ronda cuando pasa,
dice si es un problema real o anecdota.

## Criterios de aceptacion

- [ ] Agregado nuevo en `aggregates.py` sobre `Event` (bajas `Kill` cuyo autor
  y victima estan en el mismo `team_index` en esa ronda, la condicion inversa
  de `_solo_rivales`): teamkills tuyos, teamkills sufridos, rondas con algun
  teamkill de tu equipo y winrate de esas rondas contra el resto. Test con
  una ronda sintetica con un teamkill tuyo y otra con uno sufrido.
- [ ] Una fila por compañero (nick y `player_id`) con teamkills hechos y
  sufridos, ordenada por el total. La misma persona como rival en otra ronda
  no cuenta (test: su baja sobre ti cuando era rival no suma).
- [ ] Respeta los filtros de la barra (mapa, fechas, lado, ranked). Test con
  `?side=attack`.
- [ ] Panel "Teamkills" en la pagina Compañeros con los tres numeros y la
  tabla; sin teamkills dice "Ningún teamkill en las rondas filtradas". Entra
  al e2e con `seed_demo` (si el seed no tiene teamkills, el e2e verifica el
  texto vacio y un test de Django cubre el caso con datos).
- [ ] Fila en `docs/metricas.md` ("Teamkills") con la definicion y la nota de
  que siguen contando en Bajas.

## Fuera de alcance

- Sacar los teamkills de Bajas, KPR, Rating o multikills: cambia numeros que
  ya se muestran (seria decision del humano, P10).
- Columna nueva en `RoundPlayer` o migracion: sale del feed al consultar,
  como Duelos.
- Teamkills de rivales entre ellos.

## Diseno

## Implementacion
