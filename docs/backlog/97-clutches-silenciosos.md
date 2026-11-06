# 97. Clutches silenciosos

estado: entregado
candado: -
rama: claude/equipo-dev/97-clutches-silenciosos
tipo: funcionalidad
epica: impacto
area: fullstack
prioridad: 3
fuente: K11 de ALCANCE.md; [Siege.GG, rating rebalance](https://siege.gg/blog/946-player-rating-rebalance) (2026-08-11: "It also allows for 'quiet' clutches to have an impact on rating"); investigador 2026-11-03
archivos: backend/replays/analytics/metrics.py, backend/replays/models.py, backend/replays/migrations/0005_roundplayer_clutch_kills.py, backend/replays/ingest.py, backend/replays/recompute.py, backend/replays/management/commands/recompute.py, backend/replays/analytics/aggregates.py, backend/replays/views.py, backend/replays/management/commands/seed_demo.py, backend/tests/test_clutch.py, backend/tests/test_recompute.py, backend/tests/test_seed_demo.py, frontend/src/clutchSilencioso.js, frontend/src/clutchSilencioso.test.js, frontend/src/pages/Teammates.jsx, frontend/e2e/humo.spec.js, docs/metricas.md
turnos: po 20261106T0041Z-cSxDY1g, arquitecto 20261106T0200Z-ct6rosE, dev 20261106T0319Z-csweoG8, revisor 20261106T0345Z-cTsg2Tv, qa 20261106T0404Z-ckvVNri, release 20261106T0404Z-ckvVNri

## PR

Titulo: `[equipo-dev][fullstack] Clutches silenciosos`

### Que cambia

La tabla "Conversión por rivales" de Compañeros gana la columna
**Silenciosos**: cuántos de tus clutches ganados fueron sin ninguna baja tuya
desde que quedaste solo (cantidad y % de los ganados, `*` con menos de 5
ganados), y una nota que los reparte por condición de victoria (eliminación,
sin eliminación —plant, defuse o tiempo, inferido del reloj— y sin dato).

### Por que esto y no otra cosa

Ficha 97 (K11 de `ALCANCE.md`; Siege.GG premia los clutches "quiet" en su
rating). Se descartaron un booleano `clutch_silent` (denormaliza el
resultado) y calcularlo al consultar desde `Event` (las métricas se calculan
al importar). El Rating no se toca (P10).

### Como se probo

- `check.sh` (con `verificar.sh`): VERDE 8515aed, 1069 tests backend, 257 vitest, 76 e2e (se repite sobre el commit de entrega).
- Tests nuevos: `ClutchKillsTests` (12: 1v2 con dos bajas, 1v1 por tiempo, baja antes de quedar solo, suicidio, nick desconocido, quien nunca quedo solo...), `ImportClutchTests` (2), `MigracionClutchKillsTests` (2), `RecomputeClutchKillsTests` (4), `ConversionTests` (5), `ClutchSilenciosoTests` (5), 3 en `test_seed_demo.py`, 6 vitest; e2e de Compañeros afirma la celda `1 (50%)` y la nota.
- QA: base sintetica con feed real, `recompute` idempotente y con los mismos valores; migracion 0005 desde el esquema de dev llena lo ya importado; `/api/teammates/` con filtros borde y base vacia en 200; chunk inicial sin crecer; 4 mutaciones, las 4 caen.
- OMC: plan=APPROVE (2 rondas) · revisión=— · verificación=—
- OMC: plan=— · revisión=4 hallazgos (4 arreglados o documentados) · verificación=—
- OMC: plan=— · revisión=3 hallazgos (0 arreglados: 1 MEDIUM, 2 LOW, ninguno bloquea) · verificación=—
- OMC: plan=— · revisión=— · verificación=PASS (omc-verifier, 5 de 5 VERIFIED, 0 bloqueantes)

### Riesgos y lo que no entra

Migracion `0005_roundplayer_clutch_kills` (AddField + llenado desde el feed
de las rondas con intento) y columna nueva en `recompute`. Si la migracion
no corriera, todo ganado se veria silencioso. **La ficha 79 (PR #81) trae
otra `0005`**: tiene que renumerarse a `0006_match_excluded` con
dependencia `0005_roundplayer_clutch_kills`. Fuera: Rating, señal del
Coach (K9), separar silencioso vivo de muerto.

### Como probarlo en 2 minutos

```powershell
cd backend; python manage.py test tests.test_clutch tests.test_recompute tests.test_seed_demo
python manage.py seed_demo; python manage.py runserver   # Compañeros -> Conversión por rivales: 1v1 "1 (50%)*" y la nota "De tus 2 clutches ganados, 1 fue silencioso"
```

### Verificar en el PC

```powershell
cd backend; python manage.py backup
python manage.py migrate                 # aplica 0005_roundplayer_clutch_kills
python manage.py recompute --dry-run     # no deberia sumar filas por clutch_kills
```

En Compañeros, Silenciosos con numeros creibles (no 100 % en todas las
filas); una ronda contada como silenciosa no tiene bajas tuyas en el feed
despues de caer tu ultimo compañero.

### Para el humano

Dos preguntas para fichas futuras, no bloquean esta: ¿separar el clutch
silencioso en el que moriste (plant y la defensa no desactivo) del que
sobreviviste? ¿Que el clutch silencioso pese en el Rating (P10)?

### Candidatos descubiertos

Ninguno.

## Que gana quien usa la app

Ver si cuando quedas solo ganas peleando o escondiendote: cuantos clutches
ganados fueron sin bajas tuyas, por lado y por condicion de victoria.

## Criterios de aceptacion

- [x] `clutch_kills` al importar (bajas a rivales desde que quedo unico vivo, sin teamkills), `recompute` y migracion la llenan; tests de `metrics.py`.
- [x] La API de `clutch_conversion` suma silenciosos por fila y lado, y `clutch_silent` el reparto por `win_condition`.
- [x] Columna "Silenciosos" (cantidad y %, `*` bajo 5 ganados) y nota en `Teammates.jsx`.
- [x] Fila "Clutch silencioso" en `docs/metricas.md`.
- [x] e2e de Compañeros con `seed_demo` (clutch silencioso en demo-21 ronda 6, Bank, inferido).

## Diseno, Implementacion, Revision y QA (condensado)

- Diseno (arquitecto ct6rosE, plan por consenso APPROVE): `_quedar_solo` comparte el instante de `clutch_vs` (firma intacta, la usan las migraciones 0003 y 0005); `clutch_kills` cuenta `bajas_a_rivales` de los eventos posteriores, con una clave por nick de `team_of`.
- Implementacion (dev csweoG8): todo el diseno; desvios: nota en singular ("De tu único clutch ganado"), encabezado del e2e como `cell`, `make_round_player` gana `clutch_kills`.
- Revision (revisor cTsg2Tv): aprobar. Hallazgos no bloqueantes abiertos: `attack/defense.silent` sin mostrar en la UI (MEDIUM), comentario con ñ en `clutchSilencioso.test.js` y `notaSilenciosos` llamada dos veces (LOW).
- QA (ckvVNri, sobre 8515aed): todos los criterios con evidencia (comandos en `git log`, commit "Prueba: 97"); verificacion PASS.
