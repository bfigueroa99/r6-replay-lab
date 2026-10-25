# 46. Primero de tu equipo en caer

estado: entregado
candado: -
rama: claude/equipo-dev/46-primero-de-tu-equipo-en-caer
tipo: funcionalidad
epica: escuadra
area: fullstack
prioridad: 3
fuente: ALCANCE.md C4 (idea del PO); abre la epica escuadra (C1-C5 libres)
archivos: backend/replays/analytics/aggregates.py, backend/replays/views.py, backend/tests/test_primero_en_caer.py, frontend/src/pages/Teammates.jsx, frontend/e2e/humo.spec.js, docs/metricas.md
turnos: po 20261014T1911Z, arquitecto 20261014T2311Z, dev 20261015T0611Z, revisor 20261015T0711Z, dev 20261015T0812Z, revisor 20261015T0912Z, qa 20261015T1012Z, release 20261015T1111Z

## PR

Titulo: `[equipo-dev][fullstack] Primero de tu equipo en caer en Compañeros`

### Que cambia

Compañeros suma el panel "Primero en caer": por lado (Ataque, Defensa,
Total) cuantas rondas fuiste el primero de tu equipo en morir, cuantas cayo
primero un compañero y cuantas tu equipo no perdio a nadie, con el winrate
de ronda de cada grupo y CSV `primero-en-caer`. Cuenta aunque antes haya
muerto un rival, a diferencia de "Primera muerte" de Duelos.
`/api/teammates/` trae la clave nueva `first_down`. Abre la epica escuadra.

### Por que esto y no otra cosa

Ficha 46 (ALCANCE.md C4). Usa `RoundPlayer.death_elapsed`, `team_index`,
`side`, `won` e `is_me`, ya importados, y `Event.order` solo para
desempatar: sin migracion ni recompute, sin tocar `opening_death`.
Descartado: columna `first_team_death` al importar (queda como alternativa
si pesa, ver Para el humano).

### Como se probo

- `./scripts/check.sh` -> `Todo en verde.`: ruff ok, 604 tests backend, 86
  vitest, build ok, 34 e2e (sobre la rama con `origin/main@17f0ae1`).
- `backend/tests/test_primero_en_caer.py` (19 tests): rival antes que vos,
  companero primero, sin bajas, `death_elapsed` nulo, empate por orden del
  feed, empate sin eventos (va al companero), reloj en 0, rivales fuera,
  fila sin lado solo en el total, winrate por grupo, 60 empates con el tope
  de parametros de SQLite en 50, filtro de lado, API con base vacia y
  filtros raros. e2e `Compañeros muestra quien cae primero` (203 rondas,
  `53 (26%)`).
- QA: base vacia y sembrada con `factories.py` (9 rondas calculadas a
  mano), `curl` con filtros borde (todos 200), chunk inicial sin cambio
  (186.80 kB), 4 mutaciones detectadas.

### Riesgos y lo que no entra

Sin migracion, sin recompute, sin parser. Se calcula al consultar (como
Sinergia); con algun empate lee los KILL/DEATH de las rondas filtradas.
Fuera: desglose por companero (siguiente tramo de escuadra), abandonos
aparte (D3), cambiar `opening_death`.

### Como probarlo en 2 minutos

```
cd backend; python manage.py seed_demo; python manage.py runserver
curl -s localhost:8000/api/teammates/ | python -m json.tool | findstr /C:"me_first" /C:"\"rounds\""
```

Abrir `http://localhost:8000/companeros`: panel "Primero en caer" con filas
Ataque, Defensa y Total; Total 203 rondas, "Caíste primero" `53 (26%)`.
`seed_demo` gana todo el ataque y pierde toda la defensa, por eso los
winrates demo son 100 % y 0 %.

### Para el humano

Nada que decidir. Aviso en `## Para el humano` de la ficha (columna al
importar si el calculo al consultar pesa).

### Candidatos descubiertos

Ninguno.

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

## Diseno (resumen)

Arquitecto 20261014T2311Z. `aggregates.first_teammate_death(**filters)`:
por ronda tuya, filas de tu equipo con `death_elapsed` no nulo; la menor
decide (`me`, `mate`, `none`); empate al segundo lo decide el primer
evento KILL/DEATH del feed, y sin evento gana el companero (regla
conservadora). Salida por `Attack`, `Defense`, `total`. Panel en
`Teammates.jsx`, fila en `docs/metricas.md`. Detalle completo en `git log`.

## Implementacion

Dev 20261015T0611Z: todo el diseno, 17 tests, e2e, dos filas en
`metricas.md`. Desvio: un `elapsed` 0 (evento sin reloj) manda la ronda al
feed en vez de ganar como la mas temprana. Dev 20261015T0812Z corrigio los
hallazgos de la primera revision: definicion del % en `metricas.md` y
`Exists` correlacionado en `_primer_orden_de_muerte` (test con 60 empates).

## Revision

Revisor 20261015T0711Z sobre dd00dc4: corregir (dos hallazgos, % sin
definicion y tope de parametros). Revisor 20261015T0912Z sobre c62b7b3:
ambos corregidos, revision ciega sin bugs. Veredicto: aprobar.

## QA 2026-10-15 sobre 215f7d6

QA 20261015T1012Z: `check.sh` verde (604 con el test de borde agregado
`test_fila_sin_lado_cuenta_solo_en_el_total`), base vacia y sembrada con
resultados calculados a mano, vecinos 200, chunk sin cambio, mutaciones
detectadas. Veredicto: `aprobado`.

## Para el humano`.

Veredicto: aprobar -> `revisado`.

## QA 2026-10-15 sobre 215f7d6

QA 20261015T1012Z (sesion distinta de dev y revisor). Rama con
`origin/main@17f0ae1` (main no se movio). Base de prueba en el scratchpad
(`SQLITE_PATH` y `R6_ENV_FILE` apuntando ahi), nunca al repo.

- `./scripts/check.sh`: `Todo en verde.` (603 backend, 86 vitest, build, 34
  e2e); con el test de borde agregado, `Todo en verde.` con 604 backend.
- **Base vacia** (`migrate` + `runserver 8765`): `curl -s -o /dev/null -w
  "%{http_code}" "localhost:8765/api/teammates/$q"` con `q` en `""`,
  `?until=foo`, `?page=-1`, `?side=`, `?map=`, `?session=-1`, `?side=Attack`,
  `?min_rounds=abc`: todos 200; `first_down` trae las tres filas en 0 con
  winrates `null`.
- **Base sembrada con `factories.py`** (script `seed.py` por `manage.py
  shell`): 8 rondas calculadas a mano (rival cae antes que vos; companero
  primero; sin bajas; vos vivo y cae companero; vos con `died=True` y
  elapsed nulo; empate 45/45 con tu evento primero en el feed; empate 50/50
  sin eventos; rival a los 10 s y vos antes que el companero) mas una
  partida de un jugador solo (`Border`, vos caes a los 20 s). Esperado y
  obtenido en `/api/teammates/`:
  Attack 5 rondas, caiste 2 (2 ganadas, 100 %), companero 3 (1, 33.3 %),
  sin bajas 0; Defense 4, caiste 2 (1, 50 %), companero 1 (0, 0 %), sin
  bajas 1 (1, 100 %); total 9, 4/4/1. `?side=Attack` deja Defense en 0;
  `?map=border` da solo la ronda solitaria (1, caiste); `?map=Nada` todo
  en 0; `?until=foo` igual que sin filtro. Vecinos `/api/synergy/`,
  `/api/matches/`, `/api/overview/`, `/api/duels/`: 200.
- **Chunk inicial** (`vite build`): `index-*.js` 186.80 kB en main y en la
  rama (0 %); `Teammates-*.js` pasa de 3.33 a 4.50 kB (carga diferida).
- **Mutacion** sobre `aggregates.py` y `tests.test_primero_en_caer`:
  empate sin eventos resuelto a tu favor -> cae
  `test_empate_sin_eventos_va_al_companero`; sin `team_index` en el
  `Exists` -> caen 3 (`test_los_rivales_no_cuentan_como_companeros`, ...);
  reloj en 0 fuera del feed -> caen `test_reloj_en_cero_lo_decide_el_feed`
  y `test_clasifica_cada_caso`; fila sin lado sumada a Attack -> **no caia
  ninguno**. Agregue `test_fila_sin_lado_cuenta_solo_en_el_total` (pasa con
  el codigo de la rama, cae con ese mutante).
- Criterios: los seis con evidencia (tests de la rama, curls de arriba, e2e
  `Compañeros muestra quien cae primero`, filas en `metricas.md`).

Sin migracion, parser, Electron ni `.ps1`: no hace falta `## Verificar en el
PC`. Veredicto: `aprobado`.

## Para el humano

- Revisor 20261015T0912Z (aviso, no frena): la clasificacion se calcula al consultar
  (lee `Event` si hay empates). Si pesa o se quiere alinear con "metricas al
  importar", la alternativa es una columna `first_team_death` en
  `RoundPlayer` marcada en `metrics.analyse_round` (migracion + `recompute`),
  en ficha aparte.
