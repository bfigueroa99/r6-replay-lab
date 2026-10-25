# 57. Teamkills: a quien mataste y quien te mato

estado: entregado
candado: -
rama: claude/equipo-dev/57-teamkills
tipo: funcionalidad
epica: escuadra
area: fullstack
prioridad: 3
fuente: ALCANCE.md C7 ([Siege.GG](https://siege.gg/news/support-value-in-siege-explained-with-the-new-rating-model), "Teamkills per Round")
archivos: backend/replays/analytics/aggregates.py, backend/replays/views.py, backend/tests/test_teamkills.py, frontend/src/pages/Teammates.jsx, frontend/e2e/humo.spec.js, docs/metricas.md
turnos: po 20261019T0004Z, arquitecto 20261022T0804Z, dev 20261023T0404Z, revisor 20261023T0805Z, qa 20261023T1205Z, release 20261023T1606Z

## PR

Titulo: `[equipo-dev][fullstack] Teamkills: a quien mataste y quien te mato`

### Que cambia

La pagina Compañeros suma un panel "Teamkills": cuantos compañeros mataste,
cuantas veces te mato uno, en cuantas rondas hubo un teamkill de tu equipo y
el winrate de esas rondas contra el de las demas, con una tabla por
compañero (hechos, sufridos, total, CSV). Respeta los filtros de la barra.
Hasta ahora los teamkills estaban en el feed pero ninguna pantalla los
mostraba: Duelos los descarta y Bajas los suma sin avisar.

### Por que esto y no otra cosa

Ficha 57, epica `escuadra` de `ALCANCE.md` (C7, "Teamkills per Round" de
Siege.GG). Descartado: sacar los teamkills de Bajas, KPR, Rating o
multikills (cambia numeros que ya se muestran, decision del humano);
columna nueva en `RoundPlayer` con migracion (sale del feed al consultar,
como Duelos).

### Como se probo

- `./scripts/check.sh`: `Todo en verde.` con 757 tests backend, 120 vitest,
  build y 46 e2e, sobre la rama al dia con `origin/main` (93fe22c).
- Tests nuevos en `backend/tests/test_teamkills.py` (12): teamkill tuyo y
  sufrido, la misma persona como rival no suma, winrate aparte de las rondas
  con teamkill, teamkill entre otros dos compañeros cuenta la ronda pero no
  la tabla, filtro de lado, sin teamkills devuelve ceros, suicidio, bajas
  sobre rivales, orden por total y nick, baja sin autor o sin victima, base
  vacia.
- e2e `Compañeros muestra el panel de teamkills` (estado vacio: `seed_demo`
  no tiene teamkills y no se toco).
- Revision a ciegas sin hallazgos; Revisor y QA tumbaron el codigo con
  mutaciones distintas (condicion de equipo de autor y victima, suicidios,
  winrate cruzado, orden, filtros) y los tests cayeron en todas.
- QA con una base sembrada desde `factories.py`: `/api/teammates/` y la UI
  dan `1 / 1 / 3 rondas` (33% contra 54%) y la tabla `amigo 1 1 2`; con Lado
  = Ataque `1 / 0 / 1`; con otro mapa, el texto vacio. Consola limpia.
  `/api/duels/` sigue sin contar el teamkill sufrido.

### Riesgos y lo que no entra

Sin migracion, sin `recompute`, sin parser, sin Electron ni `.ps1`. Una
clave nueva en el JSON de `/api/teammates/`; dos subconsultas por baja, el
mismo patron que Duelos (47 ms con la base de QA). Una ronda sin ganador
conocido cuenta como no ganada en el winrate con/sin teamkill, igual que el
Winrate general (dicho en `metricas.md`). Fuera: teamkills de rivales entre
ellos y sacarlos de Bajas.

### Como probarlo en 2 minutos

```
cd backend; python manage.py test tests.test_teamkills
cd frontend; npm run build
cd backend; python manage.py runserver
```

Abrir `http://127.0.0.1:8000/companeros`: el panel "Teamkills" aparece
entre "Primero en caer" y "Clutches"; con la base real muestra los numeros
y la tabla, o "Ningún teamkill en las rondas filtradas.".

### Verificar en el PC

Con la base real, cruzar un teamkill de la tabla con el feed del detalle de
esa partida.

### Para el humano

Nada. (Opcional: si preferis excluir del winrate con/sin teamkill las
rondas sin ganador conocido, son dos filtros.)

### Candidatos descubiertos

Ninguno.

## Que gana quien usa la app

Ver cuantos compañeros mataste, cuantas veces te mato uno, con quien, y
cuanto se pierde la ronda cuando pasa, dice si es un problema real o
anecdota.

## Diseno (resumen)

Espejo de `_solo_rivales` en la seccion de duelos de `aggregates.py`:
helper `_equipo_de(campo)` (reusado por `_solo_rivales`), `_teamkills(mine)`
y `teamkills(**filters)`, servido como clave `teamkills` de
`/api/teammates/`. Panel en `Teammates.jsx`, fila "Teamkills" en
`## Duelos` de `docs/metricas.md`.

## Implementacion

Segun el diseno, sin desvios. Suicidios y bajas sin autor o sin victima no
cuentan. El detalle esta en `git log` (6c563d1).

## Revision 2026-10-23 sobre 6c563d1

**Aprobar.** Revision a ciegas sin hallazgos; los 5 criterios cubiertos;
mutaciones caen; `check.sh` en verde.

## QA 2026-10-23 sobre 8ee9f5b

**Aprobado.** `check.sh` en verde; API, filtros, base vacia, vecino Duelos y
UI verificados con una base sembrada; mutaciones distintas caen; chunk
inicial sin cambios.

## Entrega 2026-10-23 sobre 97f56e6

`check.sh` en `Todo en verde.` (757, 120, build, 46 e2e) con `origin/main`
(93fe22c) ya fusionado.
