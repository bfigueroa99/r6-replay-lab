# 107. Sitio que tu equipo repite tras perderlo

estado: entregado
candado: -
rama: claude/equipo-dev/107-sitio-que-tu-equipo-repite-tras-perderlo
tipo: funcionalidad
epica: posicionamiento
area: fullstack
prioridad: 3
fuente: ALCANCE.md S4 (PO 20261105T1759Z-cCJ5erc)
archivos: backend/replays/analytics/aggregates.py (site_after_loss, REPETIR_SITIO_*), backend/replays/views.py (site_after_loss), backend/replays/urls.py, backend/tests/test_repetir_sitio.py, frontend/src/repetirSitio.js, frontend/src/repetirSitio.test.js, frontend/src/pages/Coach.jsx, frontend/e2e/humo.spec.js, docs/metricas.md
turnos: po 20261112T1127Z-cT8M5Vz, arquitecto 20261112T1204Z-chGLrtC, dev 20261112T1603Z-cor3JBP, revisor 20261112T2004Z-cbaTGDt, qa 20261113T0003Z-cVnayJ8, release 20261113T0003Z-cVnayJ8

## PR

Titulo: `[equipo-dev][backend] Repetir el sitio tras perderlo, en el Coach`

### Que cambia

Panel nuevo en el Coach, "Repetir el sitio tras perderlo": despues de perder
una ronda defendiendo un sitio, cuantas veces tu equipo vuelve a ese sitio en
la siguiente ronda de defensa de la partida y cuantas cambia, con el winrate
de cada caso, en total y por mapa (con CSV). Endpoint nuevo
`GET /api/positioning/site-after-loss/`.

### Por que esto y no otra cosa

Ficha 107 (ALCANCE.md S4, epica `posicionamiento`). Repetir un sitio que el
rival ya leyo es una decision de la defensa que ninguna tabla mostraba.
Descartado: el lado de ataque (spawn tras perder, otra idea) y recomendar
sitio (solo se cuenta).

### Como se probo

- `check.sh` (con `verificar.sh`): VERDE (ver el commit de Entrega), 1163 tests backend, 329 vitest, 94 e2e.
- Tests nuevos: `backend/tests/test_repetir_sitio.py` (17: repeat/switch, ataque
  entre medio no corta, sitio vacio y numero faltante cortan, no cruza partidas,
  tras ganar o sin ganador no hay par, winrate sin la sin ganador, filtros de
  sitio (mira la perdida y no la segunda), lado/operador ignorados, mapa, tipo,
  fechas, versiones del mapa, vacio sin error); `repetirSitio.test.js` (6);
  e2e `el Coach muestra si repites el sitio tras perderlo` (56 / 2, Club House 19 y 1).
- QA: curl con bordes en base vacia y `seed_demo`; recalculo independiente por
  SQL (56/2, 11/1 con sitio) y con `factories` (2/2 con 50 %); 3 mutaciones caen;
  chunk inicial igual que dev; accesibilidad del panel en Chromium sin hallazgos.
- OMC: plan=— · revisión=— · verificación=— (Diseno)
- OMC: plan=— · revisión=3 hallazgos (3 arreglados; 0 CRITICAL/HIGH) · verificación=— (Implementacion)
- OMC: plan=— · revisión=4 hallazgos (1 MEDIUM cerrado con test; 3 LOW sin arreglar) · verificación=— (Revision)
- OMC: plan=— · revisión=— · verificación=PASS (QA)
- Skills del repo: accessibility-review (0 Critical, 0 Major, 0 Minor), validate-data (0 hallazgos; valores recalculados 56/2, 11/1, 2/2 con 50 %).

### Riesgos y lo que no entra

Sin migracion, sin `recompute`, sin parser, sin POST. Una consulta sobre tus
rondas, en orden por partida y numero. El par se corta tambien si falta un
numero de ronda (conservador, documentado en `metricas.md`). Fuera: lado de
ataque y pares tras ronda ganada.

### Como probarlo en 2 minutos

```powershell
cd backend; python manage.py seed_demo; python manage.py runserver
```
Abrir `http://127.0.0.1:8000/coach`: panel "Repetir el sitio tras perderlo"
con 56 en "Repite el sitio", 2 en "Cambia de sitio" ("pocas rondas") y la
tabla por mapa (Bank 19/1, Club House 19/1, Border 18/0). Con `?side=Attack`
los numeros no cambian; con un sitio de Bank solo cuentan las perdidas ahi.

### Para el humano

Nada.

### Candidatos descubiertos

Ninguno.

## Que gana quien usa la app

Despues de perder una ronda defendiendo un sitio, la app dice cuantas veces
tu equipo vuelve a ese sitio en la siguiente ronda de defensa y cuantas
cambia, con el winrate de cada caso, en total y por mapa. Si el rival ya leyo
el sitio, repetir cuesta: es una decision de la defensa, o sea tuya y de tu
equipo, que ninguna tabla muestra hoy.

## Criterios de aceptacion

- [ ] Un agregado devuelve, para pares de rondas de defensa consecutivas de
      la misma partida (por `Round.number`, saltando las de ataque entre
      medio) donde la primera se perdio: `repeat` y `switch` con
      `rounds` y `winrate` de la segunda ronda, en total y por mapa. Test
      con una partida armada: perder en "2F Kitchen" y volver a "2F Kitchen"
      cuenta `repeat`; ir a "1F Bar" cuenta `switch`.
- [ ] Una ronda con `site=""` corta el par (no cuenta ni como primera ni
      como segunda) y el test lo afirma; los pares no cruzan partidas.
- [ ] Los filtros globales (mapa, tipo de partida, fechas, sesion) aplican;
      el de lado se ignora (solo hay pares de defensa) y el de sitio filtra
      por el sitio de la ronda perdida. Test del filtro de sitio.
- [ ] Se ve en la UI con los dos casos lado a lado y la muestra minima de
      `metricas.md` para winrates; sin pares, un texto vacio y no un error.
      El e2e de humo pasa por esa pagina con la consola limpia.
- [ ] Fila nueva en `docs/metricas.md` ("Repetir el sitio tras perderlo").

## Fuera de alcance

- El lado de ataque (S3, spawn tras perder): otra idea.
- Pares que siguen a una ronda ganada.
- Recomendar que sitio jugar: solo se cuenta.

## Diseno

(arquitecto 20261112T1204Z-chGLrtC) Panel propio en el Coach, endpoint aparte, sin migracion; detalle en `git log` de esta ficha.
OMC: plan=— · revisión=— · verificación=—

## Implementacion

(dev 20261112T1603Z-cor3JBP) `aggregates.site_after_loss` y
`REPETIR_SITIO_MIN_RONDAS = 8`, vista y url `positioning/site-after-loss/`,
`repetirSitio.js` + vitest, `PanelRepetirSitio` en el Coach (dos `Stat` y
`DataTable` por mapa con CSV), e2e, filas en `metricas.md`. Desvios del
diseno: los huecos se ven en la misma consulta (tus rondas de los dos lados;
un numero que no sigue al anterior corta), y "pocas rondas" tambien por mapa.
OMC: plan=— · revisión=3 hallazgos (3 arreglados; 0 CRITICAL/HIGH) · verificación=—

## Revision 2026-11-12 sobre b2c94af

(revisor 20261112T2004Z-cbaTGDt) Aprobar -> `revisado`. MEDIUM corregido: el
test del filtro de sitio pasaba igual si mirara la segunda ronda; agregados
`test_el_filtro_de_sitio_no_mira_la_segunda_ronda` y
`test_el_filtro_de_fechas_aplica`. LOW sin arreglar: hint sin lado/operador;
CSV con punto (resuelto despues por #109 en `celdaCsv`); un filtro que vacia
el Coach esconde la pagina (como el resto del Coach).
OMC: plan=— · revisión=4 hallazgos (1 MEDIUM cerrado con test; 3 LOW sin arreglar) · verificación=—

## QA 2026-11-13 sobre 22dc59d

(qa 20261113T0003Z-cVnayJ8) Rama fusionada con `origin/dev` (entro #109, sin conflictos). Datos
en `$S` = el scratchpad; nada al repo.

- **check.sh**: `git show origin/dev:scripts/equipo-dev/verificar.sh | bash -s --`
  -> `VERDE 22dc59dc9 en 167s: 1163 tests backend, 329 vitest, 94 e2e. Todo en verde.`
- **Base vacia** (`SQLITE_PATH=$S/vacia.sqlite3 python manage.py migrate`, `runserver 8031`):
  `curl /api/positioning/site-after-loss/` con `""`, `?site=2F%20Kitchen`,
  `?side=Attack&operator=Ash`, `?until=foo`, `?since=2099-01-01`, `?page=-1`,
  `?map=`, `?site=` -> 200 y `pairs: 0`, `winrate: null` en todos. POST -> 403.
- **Base `seed_demo`** (`runserver 8032`): sin filtros -> 58 pares, repeat 56, switch 2,
  Bank 19/1, Club House 19/1, Border 18/0 (= diseno y e2e). `?side=Attack&operator=Ash`,
  `?side=Defense`, `?until=foo`, `?page=-1`, `?site=` -> igual (58). `?map=bank` -> 20.
  `?site=Inexistente`, `?since=2099-01-01` -> 0, 200. Vecinos `/api/positioning/` y
  `/api/coach/` -> 200 (tambien con `?until=foo`).
- **Valores recalculados a mano** (`python -I $S/recalculo.py <db> [sitio]`, SQL crudo
  sobre `replays_roundplayer`/`replays_round`, logica propia por partida):
  seed_demo -> repeat 56, switch 2 (API 56/2); `site=B Church, B Arsenal Room` ->
  11/1 (API 11/1, 12 pares). Base de `factories` (3 partidas: ataque entre medio,
  hueco de numero, sitio vacio, segunda sin ganador, dos mapas) -> a mano y SQL:
  repeat 2 (1 ganada), switch 2 (1 ganada); API 50 % y 50 %; con `site=2F Kitchen`
  1/1 y 1/1 (API 100 % y 100 %).
- **Mutacion** (`python manage.py test tests.test_repetir_sitio`, codigo restaurado):
  sin reset por sitio vacio -> cae `test_una_ronda_sin_sitio_corta_el_par`; sin corte
  por numero faltante -> cae `test_una_ronda_faltante_entre_medio_corta_el_par`;
  sin ganador como derrota -> cae `test_tras_ganar_o_sin_ganador_no_hay_par`.
- **Chunk inicial**: `index-*.js` 196964 B en la rama y en `origin/dev` (worktree,
  `npx vite build`): +0 %. Chunk lazy del Coach 6232 -> 8643 B.
- **Accesibilidad** (`node $S/a11y.js`, Chromium sobre `/coach` con seed_demo): titulo
  `h2`/`h3` con nombre, 5 cabeceras de tabla con texto (0 vacias), botones con nombre
  ("Descargar CSV" y los de orden), Tab llega al panel con foco visible
  (outline auto), contraste minimo 5.21:1 (claro y oscuro), consola sin errores.
  Sin Critical ni Major.
- **validate-data** sobre la fila de `metricas.md`: division por cero -> `null`
  ("—"); totales sumados de conteos, no promedio de promedios; winrate siempre junto a
  su `n` (rondas) y aviso bajo 8; redondeo igual en tarjetas y tabla.
- **LOW de la revision**: el CSV con punto quedo resuelto por #109 (`celdaCsv`
  pasa a coma lo que devuelve `csv`). Los otros dos LOW (hint sin lado/operador,
  filtro que vacia el Coach) siguen anotados; no frenan.
- Cosmetico, no frena: con 0 pares en un caso la tabla dice "— · pocas rondas".

Criterios: los cinco cumplidos. Veredicto: `aprobado`.

Skills del repo: accessibility-review (0 Critical, 0 Major, 0 Minor), validate-data (0 hallazgos; valores recalculados 56/2, 11/1, 2/2 con 50 %).
OMC: plan=— · revisión=— · verificación=PASS

## Para el humano

(nada)
