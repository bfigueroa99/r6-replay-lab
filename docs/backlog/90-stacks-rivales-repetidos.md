# 90. Stacks rivales repetidos

estado: entregado
candado: -
rama: claude/equipo-dev/90-stacks-rivales-repetidos
tipo: funcionalidad
epica: rivales
area: fullstack
prioridad: 3
fuente: D4 de ALCANCE.md; `replica/features.csv` "Historial contra un equipo rival concreto" (should, partial: la referencia lo tiene por equipo y la app solo por persona, D1 en dev)
archivos: backend/replays/analytics/aggregates.py (repeated_rivals, rival_stacks nueva), backend/replays/views.py (duels), frontend/src/pages/Duelos.jsx, backend/tests/test_stacks_rivales.py, frontend/e2e/stacks-rivales.spec.js, docs/metricas.md
turnos: po 20261105T1759Z-cCJ5erc, arquitecto 20261105T1920Z-cAaALb8, dev 20261105T1945Z-ceRZh1z, revisor 20261105T2004Z-cx71xGT, qa 20261106T0004Z-cibB3Yh, release 20261106T0004Z-cibB3Yh

## PR

Titulo: `[equipo-dev][backend] Stacks rivales que se repiten en Duelos`

### Que cambia

En Duelos, debajo de "Rivales repetidos", un panel nuevo "Stacks rivales que
se repiten": los grupos de 2 o más rivales que te tocaron juntos en el equipo
contrario en 2 o más partidas, con su récord y winrate, y cada nick enlazado a
su perfil. `GET /api/duels/` suma la clave `rival_stacks` (comparte
`min_matches` con `rivals`).

### Por que esto y no otra cosa

Ficha 90 (D4 de `ALCANCE.md`): la referencia tiene historial contra un equipo
rival y la app solo por persona. El `.rec` no trae nombre de equipo, asi que
el grupo es coincidencia de personas. Descartado: armar grupos por partida
(un rival y su reemplazo salian como stack sin haber jugado juntos).

### Como se probo

- `check.sh` (con `verificar.sh`): ver la linea VERDE de la QA y de la entrega abajo.
- Tests nuevos (`backend/tests/test_stacks_rivales.py`): grupo de tres en dos
  partidas da una sola fila; un subgrupo sale aparte solo con partidas propias;
  partidas sin resultado fuera del winrate; companero en una partida y rival en
  otra; filtro de mapa; un reemplazo no forma grupo con quien reemplazo; ronda
  con mas de 10 rivales no arma grupos; sin grupos; sin datos; la API trae
  `rival_stacks` y respeta `min_matches`. e2e nuevo
  `frontend/e2e/stacks-rivales.spec.js` (fila del seed, 29 y 29-0, enlaces).
  `test_duels.py` sin tocar, red del refactor de `repeated_rivals`.
- QA: `runserver` con base vacia, con base sembrada desde `factories.py`
  (reemplazos, nick repetido, cambio de nick, sin resultado) y con
  `seed_demo`; parametros borde en 200; 4 mutaciones, cada una tumba su test.
- OMC: diseno plan=— · implementacion revisión=5 hallazgos (3 arreglados) ·
  revision 1 hallazgo LOW (arreglado en QA) · QA verificación=PASS.

### Riesgos y lo que no entra

Sin migracion ni `recompute`. Memoria: hasta 26 subconjuntos por ronda (5
rivales); una ronda con mas de 10 rivales no arma grupos. Fuera: nombres de
equipo o clan (el `.rec` no los trae), stats de esos rivales fuera de tus
partidas, stacks de tus companeros (C1).

### Como probarlo en 2 minutos

```
cd backend; python manage.py seed_demo; python manage.py runserver
```
Abrir http://127.0.0.1:8000/duelos: panel "Stacks rivales que se repiten" con
una fila "Kaid_ · Mozzie99 · Thorn.exe", Juntos 3, Partidas 29, Récord 29-0.
Con el filtro de un mapa, Partidas baja a las de ese mapa.

### Para el humano

Nada.

### Candidatos descubiertos

Ninguno.

## Que gana quien usa la app

Reconocer al stack que ya te gano, no solo a la persona. Solo gente de tus
replays; no es scouting ni consulta a nadie.

## Criterios de aceptacion

- [x] `GET /api/duels/` trae `rival_stacks` (players, matches, wins, losses,
      winrate; por `Player`; `min_matches` 2 por defecto).
- [x] El grupo es el mas grande que se repite; uno mas chico sale aparte solo
      si suma partidas propias.
- [x] Equipo leido por ronda; respeta los filtros globales.
- [x] Panel en Duelos con nicks enlazados y record; vacio con mensaje.
- [x] Fila en `docs/metricas.md` y e2e con numero de `seed_demo`.

## Diseno

(Arquitecto 20261105T1920Z-cAaALb8.) `rival_stacks` al lado de
`repeated_rivals` con un helper de cruces compartido, conjuntos cerrados con
`itertools.combinations`, clave nueva en `duels`, panel con `DataTable` y
titulo "Stacks rivales que se repiten" (no choca con los locators de
`humo.spec.js`), e2e en archivo propio. Detalle en `git log` de esta ficha.

OMC: plan=— · revisión=— · verificación=—

## Implementacion

(Dev 20261105T1945Z-ceRZh1z.) Diseno completo. Desvios: el helper es
`_rivales_por_ronda` y los grupos se arman por ronda (un reemplazo no forma
grupo con quien reemplazo); por eso puede haber mas de un maximal con el mismo
conjunto de partidas; tope de 10 rivales por ronda. VERDE cbb28a5.

OMC: plan=— · revisión=5 hallazgos (3 arreglados: 2 MEDIUM y el LOW de test; 2 LOW aceptados) · verificación=—

## Revision 2026-11-05 sobre 441253b

(Revisor 20261105T2004Z-cx71xGT.) Dos ejes a ciegas; cinco criterios
cubiertos. Un LOW: la columna "Juntos" sin definicion en `metricas.md`
(arreglado en la QA). Veredicto: aprobar. VERDE 485e226.

OMC: plan=— · revisión=1 hallazgo LOW (0 arreglados) · verificación=—

## QA 2026-11-06 sobre 4025670

(QA 20261106T0004Z-cibB3Yh, rama ya fusionada con `origin/dev@9bc4bf6`.)

- `check.sh` con `verificar.sh`: VERDE 40256703f (1000 tests backend, 210
  vitest, 67 e2e).
- Base vacia (`SQLITE_PATH=<scratch>/vacia.sqlite3 python3 manage.py migrate`,
  `runserver 127.0.0.1:8765`): `curl /api/duels/` con ``, `?min_matches=1`,
  `=0`, `=foo`, `=-5`, `?until=foo`, `?map=` -> 200 y `rival_stacks: []`.
- Base sembrada con `factories.py` (script en el scratchpad, `manage.py shell
  < sembrar.py`): A+B+C en 2 partidas (1 perdida), A+B+Z en otra (Oregon), un
  reemplazo D->E con F en dos partidas, otra persona tambien llamada "A" con
  G, B con otro nick junto a A, A+B con `won=None`, una partida solo mia.
  `curl /api/duels/` -> `A+B 2 5 3-1 75.0`, `A+B+C 3 2 1-1 50.0`,
  `A(otro)+G 2 2 2-0`, `D+F 2 2`, `E+F 2 2`; D+E nunca. El cambio de nick no
  parte la fila (B suma 5) y el nick repetido no se mezcla (otro id).
  `?min_matches=3` -> solo A+B; `=1` suma A+B+Z (1); `?map=oregon` -> [];
  `?map=club-house` -> A+B 4 (2-1); `?map=%C2%B2` -> []; `?side=Defense` -> [];
  `?until=foo`, `?page=-1`, `?min_matches=foo` -> igual que sin parametros.
  `/duelos` -> 200.
- `seed_demo` en base del scratchpad: `rival_stacks` = Kaid_ · Mozzie99 ·
  Thorn.exe, size 3, 29 partidas, 29-0, 100.0: el numero que afirma
  `e2e/stacks-rivales.spec.js`.
- Chunk inicial: `index-*.js` 191939 bytes; Duelos es chunk lazy aparte
  (`Duelos-*.js` 7960 bytes) y el diff de frontend solo toca `Duelos.jsx`: el
  inicial no crece.
- Mutaciones en `aggregates.py` (restauradas, `git status` limpio), con
  `python3 manage.py test tests.test_stacks_rivales`: sin filtro de maximales
  -> caen `test_tres_rivales_juntos...` y `test_un_grupo_mas_chico...`; grupos
  por partida en vez de por ronda -> cae `test_un_reemplazo_no_forma_grupo...`;
  partida sin resultado como derrota -> cae `test_el_record_deja...`; tope de
  10 rivales ignorado -> cae `test_ronda_con_rivales_de_mas_no_arma_grupos`.
- LOW de la revision arreglado de paso (solo docs): la fila **Stack rival
  repetido** de `metricas.md` define *Juntos* y *Partidas*.

Sin migracion, `recompute`, parser, Electron ni `.ps1`: nada que verificar
en el PC. Sin umbral que calibrar.

Veredicto: aprobado.

OMC: plan=— · revisión=— · verificación=PASS (omc-verifier: 5 criterios VERIFIED)
