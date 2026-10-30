# 67. Teamkills fuera de las bajas

estado: entregado
candado: -
rama: claude/equipo-dev/67-teamkills-fuera-de-las-bajas
tipo: bug
epica: -
area: backend
prioridad: 1
fuente: decision del humano 2026-10-28 en `## Para el equipo` de `ESTADO.md` (pregunta de la ficha 53); `pydissect/stats.py:81-85` suma todo `Kill` del autor; `docs/metricas.md` filas Bajas, Multikill, Teamkills y Mejor ronda
archivos: backend/replays/analytics/metrics.py, backend/replays/recompute.py, backend/replays/management/commands/recompute.py, backend/replays/analytics/aggregates.py (comentario l.133), backend/tests/test_metrics.py, backend/tests/test_recompute.py, backend/tests/test_player_stats.py (comentario), backend/tests/test_teamkills.py, docs/metricas.md, README.md (fila de `recompute`)
turnos: po 20261029T0004Z, arquitecto 20261029T0404Z, dev 20261029T0805Z, revisor 20261029T1223Z, dev 20261029T1607Z, revisor 20261029T2004Z, qa 20261030T0004Z, release 20261030T0004Z

## PR

Titulo: `[equipo-dev][backend] Teamkills fuera de las bajas`

### Que cambia

Matar a un compañero ya no suma una baja: Bajas, HS%, K/D, KPR, rating, 2K/3K/ace y Mejor ronda cuentan solo rivales. El panel de Teamkills (Compañeros) los sigue mostrando igual. `manage.py recompute` corrige lo ya importado sin reparsear.

### Por que esto y no otra cosa

Decision del humano del 2026-10-28 (pregunta de la ficha 53). La regla vive en `metrics.bajas_a_rivales`, que usan el import y `recompute` (como `clutch_vs`); `pydissect/` sigue entregando lo de r6-dissect. Descartado: migracion de datos para lo ya importado (la decision fue "con `recompute`"; ver Para el humano).

### Como se probo

- `./scripts/check.sh`: `Todo en verde.` (lint, 823 tests backend, 130 vitest, build, 53 e2e).
- Tests nuevos: `test_metrics.BajasARivalesTests` (teamkill no suma, teamkill con HS no suma headshots, ronda con solo un teamkill sin `kst`, nick desconocido cuenta, suicidio no es baja, paridad con el parser sin teamkills, teamkill de apertura sigue siendo apertura); `test_recompute.RecomputeBajasTests` (corrige, `--dry-run` no escribe, idempotente, overview/perfil/scoreboard con 2 bajas); `test_teamkills.test_el_panel_de_teamkills_no_cambia_al_sacarlos_de_las_bajas`.
- QA: base sembrada con `factories` como el import viejo; `recompute --dry-run` cuenta 7 filas sin escribir, `recompute` las corrige, la segunda corrida dice "Nada que recalcular"; `curl` a overview, partida, perfil y compañeros con los numeros esperados y bordes en 200/404. Mutacion: 4 de 4 mutantes caen.

### Riesgos y lo que no entra

Sin migracion: hasta correr `recompute` la base mezcla rondas viejas (teamkills en Bajas) y nuevas. Fuera: apertura/entry con teamkill (siguen contando, lo dice `metricas.md`), `trade_kills` cuando un compañero mata al que hizo el teamkill, el 1vX con `PlayerLeave` (ficha 69).

### Como probarlo en 2 minutos

`cd backend; python manage.py test tests.test_metrics tests.test_recompute tests.test_teamkills` -> OK.

Verificar en el PC: `python manage.py backup; python manage.py recompute --dry-run; python manage.py recompute; python manage.py recompute` (la ultima: "Nada que recalcular"). K/D, KPR y rating bajan solo donde hubo teamkills.

### Para el humano

Nada que decidir. Aviso: la app de escritorio (`serve.py`) solo corre `migrate`, asi que quien usa el `.exe` no puede correr `recompute`; si importa, una migracion de datos (como la 0003 de `clutch_vs`) es otra ficha.

### Candidatos descubiertos

Ninguno.

## Que gana quien usa la app

Hoy matar a un compañero suma una baja: sube tu K/D, tu KPR y tu rating, y puede convertir una ronda de 4 rivales en un "ace". Con el arreglo las bajas cuentan solo rivales; los teamkills siguen en su panel (ficha 57).

## Criterios de aceptacion

- [x] `analyse_round`: 2 rivales + 1 compañero -> `kills == 2`, headshots sin el del compañero; solo un teamkill no da `kst`.
- [x] `recompute` corrige sin reparsear, `--dry-run` no escribe, segunda corrida sin cambios; una sola funcion para import y `recompute`.
- [x] Overview, perfil y scoreboard cuentan 2 y no 3; el panel de Teamkills no cambia.
- [x] `metricas.md` (Bajas, HS%, Teamkills, Multikill, Cuando matas, Mejor ronda, Duelos de apertura) y comentario de `aggregates.py` al dia.
- [x] Suite, vitest y e2e en verde sin mover `seed_demo`.

## Resumen del recorrido

- Diseno (arquitecto 20261029T0404Z): regla en `metrics.py`, no en el parser; el test del parser queda con comentario nuevo y la inversion es un test de la app.
- Implementacion (dev 20261029T0805Z): sin desvios de alcance. `seed_demo` no se puede usar para verificar `recompute` (siembra bajas sin eventos, ya pasaba en dev).
- Revision 1 (20261029T1223Z): corregir H1, la fila Teamkills decia que no pesan en el Rating, falso para un teamkill de apertura. Corregido por dev 20261029T1607Z (filas Teamkills y Duelos de apertura + `test_un_teamkill_de_apertura_sigue_siendo_apertura`).
- Revision 2 (20261029T2004Z): aprobar. Confirmado que `ingest.py` guarda todos los `Kill` como `Event`, asi que `recompute` sobre `.rec` importados no baja bajas por falta de feed.
- QA (20261030T0004Z, sobre 9070d2e): aprobado; evidencia completa en `git log` de la rama (commit `Prueba: 67`).
- Release (20261030T0004Z): fila de `recompute` del README al dia.

## Verificar en el PC

`cd backend; python manage.py backup; python manage.py recompute --dry-run; python manage.py recompute; python manage.py recompute` (la ultima debe decir "Nada que recalcular").

## Para el humano

Avisos (no bloquean): hasta `recompute` la base mezcla las dos definiciones de Bajas; el `.exe` no tiene como correr `recompute` (una migracion de datos seria otra ficha); `trade_kills` sigue contando al compañero que mata al que hizo el teamkill dentro de la ventana.
