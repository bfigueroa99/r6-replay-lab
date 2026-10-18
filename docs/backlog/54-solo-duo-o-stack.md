# 54. Solo, en duo o en stack

estado: entregado (PR pendiente de merge: el merge fue denegado por los permisos de la sesion; lo mergea el humano o el proximo Release)
candado: -
rama: claude/equipo-dev/54-solo-duo-o-stack
tipo: funcionalidad
epica: escuadra
area: fullstack
prioridad: 3
fuente: ALCANCE.md C5 (historial acumulado: la app es la unica que ve con quien jugaste cada partida)
archivos: backend/replays/analytics/aggregates.py, backend/replays/views.py, backend/tests/test_grupo.py, backend/tests/test_api.py, frontend/src/grupo.js, frontend/src/grupo.test.js, frontend/src/pages/Teammates.jsx, frontend/e2e/humo.spec.js, docs/metricas.md
turnos: po 20261017T1204Z, arquitecto 20261017T1603Z, dev 20261017T2004Z, revisor 20261018T0004Z, qa 20261018T0404Z, release 20261018T0804Z

## PR

Titulo: `[equipo-dev][fullstack] Solo, en duo o en stack`

### Que cambia

Compañeros suma el panel **Solo, en dúo o en stack**: tu winrate de partida, de ronda y tu
rating segun cuantos compañeros habituales jugaron esa partida con vos (0, 1, 2 o 3 o mas).
Habitual = jugo en tu equipo en 5 o mas partidas de todo tu historial. `/api/teammates/`
trae la clave nueva `by_stack`.

### Por que esto y no otra cosa

Ficha 54, epica `escuadra` (ALCANCE.md C5): solo el historial acumulado sabe con quien
jugaste cada partida, y Sinergia lo mira de a un compañero. Descartado: grupo exacto de
compañeros (C1), umbral configurable, cruce con lado o mapa.

### Como se probo

- `./scripts/check.sh`: Todo en verde (662 tests backend, 103 frontend, build ok, 40 e2e).
- `backend/tests/test_grupo.py` (16 tests: umbral de habitual, rivales, filas en orden,
  una partida en una sola fila, 4 habituales = stack, empate fuera del winrate de partida,
  cambio de nick, filtro de mapa y de lado sin cambiar el grupo, base vacia, rating
  ponderado, consultas constantes); `test_teammates_trae_by_stack` y su version con base
  vacia; `frontend/src/grupo.test.js` (4); e2e `Compañeros muestra solo, en dúo o en stack`.
- Revision a ciegas: aprobar, sin hallazgos. QA con base sembrada de 10 partidas
  (habituales con 6, 6 y 5 partidas, uno con 4, rivales frecuentes, un empate y un cambio de
  nick) y `curl` con filtros; mutacion sobre 4 tests de backend y 2 de vitest.

### Riesgos y lo que no entra

Sin migracion ni `recompute`: es agregacion al consultar, como Sinergia. `/api/teammates/`
suma 5 consultas fijas. El umbral de 5 partidas no se calibro con una base real.

### Como probarlo en 2 minutos

```
cd backend; python manage.py seed_demo; python manage.py runserver
curl -s localhost:8000/api/teammates/ | python -m json.tool | grep -A60 by_stack
```

Con `seed_demo` las 29 partidas caen en `stack` (habituales Chamo, Nico y Seba; 203 rondas,
57 %, rating 1.00) y las demas filas en 0. Abrir Compañeros -> panel debajo de Sinergia.

### Para el humano

Avisos, no preguntas: el umbral de 5 partidas se probo solo con datos sinteticos (es una
constante). Bug latente fuera de esta ficha: un empate queda `won=None` y la app lo muestra
como "incompleta" (`ingest.py:169`, `models.py:13-20`); candidato a ficha `bug`.

### Candidatos descubiertos

Ninguno.

## Que gana quien usa la app

En Compañeros, tu winrate de partida y de ronda y tu rating segun cuantos
compañeros habituales jugaron esa partida con vos: solo (0), en duo (1),
con dos (2) o en stack de tres o mas. Responde si te conviene entrar solo o
esperar a tu grupo; `teammate_synergy` hoy lo mira de a un compañero.

## Criterios de aceptacion

- [x] Habitual = un `Player` (no `is_me`) que estuvo en tu equipo
      (`team_index` igual al tuyo en la misma ronda) en 5 o mas partidas
      distintas de todo tu historial, sin aplicar los filtros de la consulta
      (asi un filtro de mapa no cambia quien es habitual). El 5 es una
      constante del modulo, sin ajuste en la UI.
- [x] `/api/teammates/` (`views.teammates`) trae la clave
      nueva `by_stack`: filas `solo`, `duo`, `trio` y `stack` (3 o mas
      habituales), cada una con `matches`, `matches_won`, `match_winrate`,
      `rounds`, `rounds_won`, `winrate` y `rating`. Una partida cuenta en
      una sola fila, por los habituales distintos que aparecen en tu equipo
      en cualquiera de sus rondas.
- [x] Partida sin resultado (`Match.result` vacio o empate) cuenta en
      `matches` y en las rondas, no en `match_winrate`. Test con una partida
      de cada fila, un empate y un cambio de nick de un habitual (sigue
      siendo el mismo `Player`).
- [x] Los filtros de siempre recortan que partidas y rondas entran; con base
      vacia o sin habituales, `by_stack` existe con las cuatro filas y todo
      en `solo` o en 0.
- [x] Compañeros muestra el panel "Solo, en duo o en stack" con las cuatro
      filas; el e2e lo encuentra con datos de `seed_demo` y la consola queda
      limpia.
- [x] `docs/metricas.md` tiene la fila **Tamaño del grupo** con la
      definicion de habitual y el aviso de que el umbral se mide sobre todo
      el historial.

## Fuera de alcance

- Winrate por grupo exacto de compañeros (C1).
- Umbral de habitual configurable.
- Lado (C10) o mapa por tamaño de grupo.

## Diseno

(Arquitecto 20261017T1603Z, sobre main 9e3d660; detalle completo en `git log`.)
`MIN_PARTIDAS_HABITUAL = 5` sobre todo el historial sin filtros; el grupo de una partida
son los habituales de cualquiera de sus rondas; los filtros eligen partidas y rondas;
sin resultado = `Match.won is None`. Panel en `Teammates.jsx` despues de Sinergia.

## Implementacion

(Dev 20261017T2004Z) Diseno completo. Desvios tecnicos: `.order_by()` antes de
`.distinct()` en los pares (partida, habitual); filas vacias con `rounds` 0 y no `None`.
Test extra: `test_una_derrota_baja_el_winrate_de_partida`.

## Revision 2026-10-18 sobre d01dbd1

(Revisor 20261018T0004Z) Veredicto: aprobar, sin hallazgos.

## QA 2026-10-18 sobre 0017292

(QA 20261018T0404Z) `check.sh` en verde; chunk inicial +0.04 %; base sembrada, los 6
criterios con evidencia por `curl`; mutacion: caen los tests de umbral, rivales, empate y
DISTINCT. Veredicto: `aprobado`.

## Para el humano

- Umbral de 5 partidas probado solo con datos sinteticos: calibrar con la base real.
- Bug latente fuera de esta ficha: un empate se muestra como "incompleta"; candidato a ficha `bug` del PO.
