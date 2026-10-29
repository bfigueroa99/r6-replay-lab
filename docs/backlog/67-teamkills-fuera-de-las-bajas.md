# 67. Teamkills fuera de las bajas

estado: propuesto
candado: -
rama: -
tipo: bug
epica: -
area: backend
prioridad: 1
fuente: decision del humano 2026-10-28 en `## Para el equipo` de `ESTADO.md` (pregunta de la ficha 53); `pydissect/stats.py:81-85` suma todo `Kill` del autor; `docs/metricas.md` filas Bajas, Multikill, Teamkills y Mejor ronda
archivos: -
turnos: po 20261029T0004Z

## PR

(La escribe el Release manager al final.)

## Que gana quien usa la app

Hoy matar a un compañero suma una baja: sube tu K/D, tu KPR y tu rating, y
puede convertir una ronda de 4 rivales en un "ace". Con el arreglo las bajas,
y todo lo que sale de ellas, cuentan solo rivales; los teamkills siguen a la
vista en su propio panel (Compañeros, ficha 57).

## Criterios de aceptacion

- [ ] `analyse_round` sobre una ronda con 2 bajas a rivales y 1 a un
      compañero (mismo `teamIndex`) deja `kills == 2` al autor; si la del
      compañero fue headshot, `headshots` tampoco la cuenta (el HS% nunca
      pasa de 100). Una ronda cuya unica baja es un teamkill no da `kst` por
      matar (test en `backend/tests/test_metrics.py`).
- [ ] `manage.py recompute` corrige lo ya importado sin reparsear: una
      `RoundPlayer` sembrada con `kills=3` y un evento `Kill` sobre un
      compañero queda en 2, `--dry-run` lo cuenta sin escribir, y una segunda
      corrida no cambia nada. La regla vive en una sola funcion que usan el
      import y `recompute` (como `clutch_vs`).
- [ ] Con esa ronda, 2K/3K/ace, K/D, KPR y rating de `/api/overview/`, el
      perfil de un jugador y el scoreboard de `/api/matches/<id>/` cuentan 2
      bajas y no 3; el test `test_un_teamkill_suma_a_las_bajas_del_autor` se
      invierte (decision del humano, no se borra) y el panel de Teamkills
      sigue devolviendo el mismo conteo.
- [ ] `docs/metricas.md` al dia: Bajas, Multikill, Teamkills ("siguen
      contando en Bajas..." deja de ser cierto), Cuando matas y Mejor ronda
      dicen que las bajas son solo a rivales; el comentario de
      `aggregates.py:133` sobre el ace tambien.
- [ ] Suite, vitest y e2e en verde sin tocar los numeros de `seed_demo`
      (no siembra teamkills; si alguno cambia, se explica en Implementacion).

## Fuera de alcance

- Apertura y entry (`opening_kill`, `entry_kill`) cuando la primera baja es
  un teamkill: sigue como hoy; si hace falta, otra ficha.
- El `1vX` de r6-dissect (`one_vx`) y la ficha del 1vX con `PlayerLeave`.
- Cambiar `pydissect/` si la regla puede vivir en `metrics.py` (el parser
  sigue entregando lo que entrega r6-dissect); lo decide el Arquitecto.
- Migracion: no hay columna nueva.

## Diseno

## Implementacion

## Revision <fecha> sobre <sha>

## QA <fecha> sobre <sha>

## Verificar en el PC

## Pendiente

## Para el humano

Sin decision pendiente (la tomaste el 2026-10-28). Al bajar este cambio:
`manage.py backup` y `manage.py recompute` en el PC para corregir el
historial; K/D, KPR y rating bajan un poco donde hubo teamkills.
