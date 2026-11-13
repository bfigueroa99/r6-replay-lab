# 123. Clutches de tus companeros

estado: propuesto
candado: -
rama: -
tipo: funcionalidad
epica: escuadra
area: backend
prioridad: 3
fuente: ALCANCE.md C15
archivos: -
turnos: po 20261113T1650Z-c9H2L8Y

## PR

## Que gana quien usa la app

En Compañeros, una tabla nueva con cada compañero habitual: cuantas veces
quedo ultimo vivo de tu equipo en rondas contigo, contra cuantos y cuantas
convirtio, al lado de tu propia conversion. Saber a quien conviene dejarle
la ronda y quien la regala; hoy los clutches de esa pagina son solo tuyos.

## Criterios de aceptacion

- [ ] Funcion nueva en `replays/analytics/aggregates.py` (p. ej.
      `teammate_clutches`): por compañero (agrupado por `player_id`, como
      `teammate_synergy`, un cambio de nick no parte la fila) cuenta
      intentos (`clutch_vs > 0` en su fila, misma ronda y `team_index` que
      la tuya) y ganados (`Round.my_team_won`), con el mismo descarte que
      `clutch_conversion`: rondas con `my_team_won` nulo no cuentan. Test
      con dos compañeros y un intento ganado y uno perdido.
- [ ] Muestra minima por fila (habitual = el mismo corte de partidas
      compartidas de la ficha 54, o un minimo de intentos fijado en el
      diseno); los compañeros bajo el corte no salen. Test.
- [ ] Los filtros globales (mapa, lado, fechas) aplican igual que al resto
      de `/api/teammates/`; test con filtro de lado.
- [ ] `/api/teammates/` suma la clave nueva; la tabla en `Teammates.jsx`
      muestra intentos, ganados y % con su `n`, mas tu propia fila como
      referencia; e2e en `seed_demo` sin errores de consola (con datos o
      con el estado vacio si la semilla no da clutches de compañeros).
- [ ] Fila nueva en `docs/metricas.md` con la definicion (ultimo vivo con
      rivales vivos, mismo algoritmo que `clutch_vs`).

## Fuera de alcance

- Partir la tabla por cantidad de rivales (1v1, 1v2...) o por lado: se
  puede como tramo siguiente.
- Clutches de los rivales (D12).
- Señales del Coach sobre esto.

## Diseno

## Implementacion

## Revision

## QA

## Para el humano

(nada)
