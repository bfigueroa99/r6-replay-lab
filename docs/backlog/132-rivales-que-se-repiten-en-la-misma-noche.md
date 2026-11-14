# 132. Rivales que se repiten en la misma noche

estado: aprobado
candado: release 2026-11-14T00:48Z
rama: claude/equipo-dev/132-rivales-que-se-repiten-en-la-misma-noche
tipo: funcionalidad
epica: rivales
area: fullstack
prioridad: 3
fuente: ALCANCE.md D13
archivos: backend/replays/analytics/aggregates.py, backend/tests/test_duels.py, frontend/src/pages/Duelos.jsx, frontend/e2e/humo.spec.js, docs/metricas.md
turnos: po 20261113T1926Z-ce4Pmp6, arquitecto 20261113T2318Z-chc2kiA, dev 20261114T0012Z-crDhgd7, revisor 20261114T0012Z-ccgaH14, qa 20261114T0040Z-c3LsMAo

## PR

## Que gana quien usa la app

En Duelos, la tabla de Rivales repetidos marca a los rivales que te tocaron
dos o mas veces dentro de una misma sesion (el lobby que vuelve a la cola
contigo esa noche) y tu record en esas revanchas. Separa al rival que
reencuentras por casualidad semanas despues del que te persigue esa noche.

## Criterios de aceptacion

- [ ] `repeated_rivals` (`aggregates.py`) suma por rival `same_session`:
      cuantas de sus partidas contra ti cayeron en una sesion donde ya lo
      habias enfrentado (la sesion es la de `_sessions_raw`, corte por
      `SESSION_GAP_MINUTES`), y el record (ganadas/perdidas) de esas
      revanchas con `Match.won` nulo fuera del record. Test con un rival
      que repite dentro de una sesion y otro que repite en sesiones
      distintas (este con `same_session = 0`).
- [ ] La primera partida contra el rival en una sesion no es revancha: con
      dos partidas en la misma noche, `same_session = 1`. Test.
- [ ] Los filtros globales aplican igual que al resto de `repeated_rivals`;
      test con filtro de mapa que deja una sola de las dos partidas de la
      sesion (`same_session = 0`).
- [ ] En Duelos, Rivales repetidos muestra la columna (p. ej. "Revanchas
      esa noche" con su record) y la ayuda dice que cuenta; e2e sobre
      `seed_demo` con los numeros de la API y consola limpia.
- [ ] Fila nueva en `docs/metricas.md`.

## Fuera de alcance

- Una pagina o panel aparte de revanchas: es una columna de la tabla que ya
  existe.
- Stacks rivales (ficha 90) en la misma noche.
- Señales del Coach sobre esto.

## Diseno

(arquitecto 20261113T2318Z-chc2kiA, sobre dev 39e22c0)

Implementar despues de que #133 se mergee: la 133 (`implementado`, en
revision) tambien toca `frontend/src/pages/Duelos.jsx`. El resto de
`archivos:` (`aggregates.py`, `test_duels.py`, `humo.spec.js`,
`metricas.md`) lo tocan casi todas las ramas con cambios aditivos y no frena.

Una sola forma obvia: tres claves mas en cada fila de `repeated_rivals`, una
columna mas en la tabla que ya existe. Sin endpoint nuevo, sin migracion,
sin `recompute`: se agrega sobre `Match.played_at` y `Match.won`, que ya
estan. Sin arena ni consenso (ficha chica, reversible).

### Archivos

- `backend/replays/analytics/aggregates.py`: helper nuevo
  `_session_index_map() -> dict[int, int]` (match_id -> `index` de su sesion,
  armado de `_sessions_raw()`, al lado de `_position_map`) y, en
  `repeated_rivals`, despues de filtrar por `min_matches`:
  - una sola llamada a `_session_index_map()` para todas las filas;
  - por rival, sus `ids` (ya filtrados) agrupados por sesion; en cada grupo
    ordenado por `(played_at, match_id)` la primera partida no es revancha y
    las demas si;
  - `same_session` = cantidad de revanchas; `same_session_wins` /
    `same_session_losses` = `Match.won` True / False de esas revanchas (el
    `resultado` que ya devuelve `_resultados_y_fechas`; `None` no suma a
    ninguno, igual que `_record`).
  - El orden de la tabla y `_record` no cambian. `_record` lo comparten los
    stacks: no tocarlo; las tres claves se agregan solo en `repeated_rivals`.
  - Docstring: la sesion es la de `_sessions_raw` (corte
    `SESSION_GAP_MINUTES`, sobre todas las partidas), pero la revancha se
    cuenta sobre las partidas filtradas: con filtro de mapa, una noche con
    una sola partida del rival en ese mapa no tiene revancha.
- `frontend/src/pages/Duelos.jsx`, panel *Rivales repetidos*: columna nueva
  despues de *Winrate*:
  `{ key: 'same_session', label: 'Revanchas esa noche', help: ..., render, csv }`.
  Render: `—` con 0; si no, `` `${n} (${w}-${l})` ``. `csv:` devuelve el
  mismo texto que el render (con `0` en vez de `—`), asi la celda no sale
  vacia en el CSV. Ayuda: "Partidas contra esa persona en una noche en que
  ya te había tocado (misma sesión, corte de SESSION_GAP_MINUTES sin
  jugar). La primera de cada noche no cuenta. Entre paréntesis, el récord
  de esas revanchas." Ordenable por `same_session` (numero). La clave de
  `rowKey` y el orden inicial no cambian.
- `backend/tests/test_duels.py`, clase `RivalesRepetidosTests` (ya tiene el
  helper `_partida`; sumarle `played_at=None` que pasa a `make_match`).
  `make_match` separa las partidas por 1 h segun `index`, dentro del corte
  de 120 min: para sesiones distintas hay que pasar `played_at` a mano con
  mas de 2 h entre partidas. Tests:
  - `test_un_rival_dos_veces_en_la_misma_noche_suma_una_revancha`: dos
    partidas a 1 h -> `same_session == 1`.
  - `test_un_rival_en_noches_distintas_no_suma_revanchas`: dos partidas a
    1 dia -> fila presente con `matches == 2` y `same_session == 0`.
  - `test_el_record_de_revanchas_es_el_de_las_partidas_despues_de_la_primera`:
    tres partidas en una noche, la primera perdida y las otras dos ganada y
    perdida -> `same_session == 2`, `same_session_wins == 1`,
    `same_session_losses == 1`.
  - `test_una_revancha_sin_resultado_no_entra_al_record`: segunda partida con
    `won=None` (`Match.objects.filter(...).update(won=None)`) ->
    `same_session == 1`, wins y losses en 0.
  - `test_el_filtro_de_mapa_deja_sin_revancha_a_la_noche_partida`: dos
    partidas en la misma noche, una en Club House y otra en Border, mas una
    tercera en Border otra noche; `repeated_rivals(map="border")` -> fila con
    `matches == 2` y `same_session == 0`.
  - `test_el_endpoint_de_duelos_trae_las_revanchas`: `GET /api/duels/` trae
    `same_session`, `same_session_wins`, `same_session_losses` en
    `rivals[0]`.
- `frontend/e2e/humo.spec.js`: extender `Duelos muestra rivales repetidos
  con enlace al perfil` (no un test nuevo: misma pagina, mismo panel): la
  cabecera `Revanchas esa noche` existe y la celda de la primera fila es la
  de la API (`—` si `rivals[0].same_session` es 0, si no
  `` `${n} (${w}-${l})` ``). `seed_demo` separa sus partidas por 3 h, asi
  que hoy todas valen 0 y la celda es `—`: el test se escribe contra la API
  y no contra el literal, para no cambiar `seed_demo` (sus numeros los
  afirman otras pruebas). El test del CSV no cambia.
- `docs/metricas.md`: fila nueva **Revanchas esa noche** justo antes de
  **Stack rival repetido** (linea ~238, junto a lo de rivales repetidos).

### Fila de `docs/metricas.md`

| **Revanchas esa noche** | En *Rivales repetidos*, cuantas de las partidas filtradas contra ese rival cayeron en una sesion (la de "Sesiones": corte de `SESSION_GAP_MINUTES` sin jugar, calculada sobre todas las partidas) en la que ya lo habias enfrentado antes; la primera partida de cada sesion contra el no cuenta. Entre parentesis, ganadas-perdidas de esas revanchas; las partidas sin resultado cuentan en el total y no en el record. Es un conteo, sin winrate: con 1 a 3 revanchas por rival un porcentaje seria ruido. `—` sin revanchas. Página Duelos. |

### Numero (statistical-analysis)

Conteo crudo y record, sin porcentaje ni umbral: el `n` de revanchas por
rival es chico (0 a 3 tipico) y un winrate sobre eso no se sostiene. El
minimo de la fila sigue siendo el de la tabla (`min_matches`, 2). No hay
umbral que calibrar con la base real.

### Orden de implementacion

1. Tests del backend (fallan), helper y claves en `repeated_rivals`.
2. Columna en `Duelos.jsx`, `npm run build`.
3. e2e y fila de `metricas.md`; `check.sh`.

### Que puede romperse

- Rendimiento: `_sessions_raw()` recorre todas las partidas una vez por
  request; ya lo hace el selector de sesiones. Una sola llamada por request,
  nunca por rival.
- Empate de `played_at` dentro de una sesion: el desempate por `match_id`
  hace deterministico cual es la primera.
- Nada de migraciones, `recompute`, parser, Electron ni `.ps1`.

### Verificacion manual

`seed_demo` + `runserver`, Duelos: la columna sale con `—` en todas las
filas y la ayuda se lee. Con datos reales (en el PC): un rival que te toco
dos veces seguidas una noche muestra `1 (1-0)` o `1 (0-1)`.

Skills: no aplica (sin dominio nuevo: ni tabla, ni migracion, ni flujo e2e nuevo).
Skills del repo: statistical-analysis (conteo sin winrate por `n` chico), testing-strategy (Django para la regla, e2e extendido para la columna; sin vitest porque no hay logica pura nueva en el front).
OMC: plan=— · revisión=— · verificación=—

## Implementacion

Quedo el diseno completo, sin desvios de alcance (la 133, de la que dependia
por `Duelos.jsx`, ya esta en dev: PR #130).

- `aggregates.py`: `_session_index_map()` (al lado de `_position_map`) y
  `_revanchas(ids, sesion_de, resultado, fechas)`; `repeated_rivals` llama una
  vez a `_session_index_map()` por request y suma `same_session`,
  `same_session_wins` y `same_session_losses` a cada fila. `_record` no se
  toco (lo comparten los stacks). Docstring con la regla del filtro.
- `Duelos.jsx`: columna "Revanchas esa noche" despues de Winrate, `—` con 0
  y `N (G-P)` si hay; CSV con el mismo texto (0 sin revanchas). Ordenable.
- `docs/metricas.md`: fila **Revanchas esa noche** antes de **Stack rival
  repetido**.
- e2e: `Duelos muestra rivales repetidos con enlace al perfil` extendido:
  cabecera y celda de la primera fila contra `/api/duels/`.

Desvios menores:
- Texto de ayuda: dice "la sesión se corta tras SESSION_GAP_MINUTES sin
  jugar, en el .env", como el hint de Sesiones en Tendencias.
- Tests extra: `test_la_primera_de_la_noche_es_la_mas_temprana_aunque_se_importe_despues`,
  `test_cada_noche_tiene_su_primera_partida` y
  `test_a_igual_hora_la_primera_de_la_noche_es_la_de_menor_id` (este ultimo
  lo pidio la revision ciega; con ids chicos el orden del set ya coincide, asi
  que fija el comportamiento mas que detectar su ausencia).

Criterios -> tests: (1) `test_un_rival_dos_veces_en_la_misma_noche_suma_una_revancha`,
`test_un_rival_en_noches_distintas_no_suma_revanchas`,
`test_el_record_de_revanchas_es_el_de_las_partidas_despues_de_la_primera`,
`test_una_revancha_sin_resultado_no_entra_al_record`; (2) el primero y
`test_cada_noche_tiene_su_primera_partida`; (3)
`test_el_filtro_de_mapa_deja_sin_revancha_a_la_noche_partida`; (4)
`test_el_endpoint_de_duelos_trae_las_revanchas` y el e2e extendido; (5)
`docs/metricas.md`.

TDD: los 8 tests Django se escribieron antes del codigo y fallaron (KeyError
`same_session`, 8 errores en `tests.test_duels`); despues, verde.

Revision ciega (omc-code-reviewer, eje estandares): aprobar, 3 LOW. Arreglados
2: JSDoc de `Balance` que habia quedado sobre `revanchas`, y test del
desempate a igual hora. El tercero (el e2e solo ve la rama `—` porque
`seed_demo` separa sus partidas 3 h) se acepta: la rama `N (G-P)` la cubren
los tests Django del numero y el formato es una linea; cambiar `seed_demo`
movería numeros de otras pruebas.

Verificacion manual sugerida: `seed_demo` + `runserver`, Duelos: columna con
`—` en todas las filas y la ayuda legible.

Skills: no aplica (sin dominio nuevo).
Skills del repo: test-driven-development (rojo visto antes del codigo),
statistical-analysis (conteo y record sin winrate, n chico), ux-copy (ayuda
con tildes, como el hint de Sesiones); modern-web-guidance no se consulto: la
columna copia el patron de `Récord` de la misma tabla (render + csv).
OMC: plan=— · revisión=3 LOW (2 arreglados) · verificación=—

## Revision 2026-11-14 sobre 24720ce

Veredicto: aprobar -> `revisado`.

Base: rama con `origin/dev` (bb92586, con la 128 y la 131) fusionado;
`verificar.sh`: VERDE 24720ce (1357 tests backend, 443 vitest, 119 e2e).

Revision a ciegas, dos ejes (omc-code-reviewer x2; diff de 276 lineas):
- Estandares: aprobar, sin hallazgos (la sesion sale de todas las partidas
  via `_sessions_raw`, las revanchas de las filtradas; `won=None` fuera del
  record; desempate `(played_at, id)` con test; cada test cae con el bug que
  nombra; `ruff` limpio).
- Intencion: aprobar; criterios 1, 2, 3 y 5 cubiertos, 4 parcial por el LOW de
  abajo.
- Confirmado por el lider (leido en el codigo, no arreglado: LOW):
  - [test] LOW `frontend/e2e/humo.spec.js:549-556`: `seed_demo` separa sus
    partidas 3 h (`seed_demo.py:192`, corte `SESSION_GAP_MINUTES`), asi que
    `same_session` es 0 para todo rival y el e2e solo ve `—`; el formato
    `N (G-P)` de `Duelos.jsx` no corre en ningun test. Arreglo: extraer el
    formato a una funcion pura con su vitest (sin tocar el seed, que mueve
    numeros de otras pruebas).

Ficha: criterios cubiertos por los tests de `test_duels.py` que lista
Implementacion; el diff no sale de `archivos:`; fila en `metricas.md`;
identificadores sin tildes, UI con tildes; sin `print` ni `console.log`.

Skills: no aplica.
Skills del repo: ninguna (revision con el prompt de `revision.md`).
OMC: plan=— · revisión=1 LOW (0 arreglados, confirmado) · verificación=—

## QA 2026-11-14 sobre 6ebf346

(qa 20261114T0040Z-c3LsMAo)

Veredicto: `aprobado`.

- `check.sh` completo: `git show origin/dev:scripts/equipo-dev/verificar.sh | bash -s --`
  -> `VERDE 6ebf3461c en 193s: 1357 tests backend, 443 vitest, 119 e2e. Todo en verde.`
- Base sembrada desde `factories.py` (script en el scratchpad, `SQLITE_PATH`
  temporal, nunca al repo): rival `acosador` en 5 partidas, noche 1
  (2026-09-01 20/21/22 h: Club House L, Border W, Club House L) y noche 2
  (2026-09-03 20/21 h: Border W, Border W); `casual` en la 1ra de cada noche;
  una baja por partida, `recompute`. `runserver` en 127.0.0.1:8132 y `curl`:
  - `/api/duels/` -> acosador `matches 5, same_session 3 (2-1)`; casual `2, 0`.
    A mano: revanchas = partidas 2 (W), 3 (L) y 5 (W) -> 3 (2-1). Antes del
    `recompute`, con `won=None` en la 5: `3 (1-1)` (sin resultado fuera del record).
  - `?map=border` -> 3 partidas, `1 (0-0)` con la None (la noche 1 queda con
    una sola en Border); `?map=club-house` -> 2 partidas, `1 (0-1)`.
  - `?session=0` -> `1`; `?session=1` -> `2 (1-1)`.
  - `?until=foo`, `?map=`, `?page=-1&min_duels=0` -> 200, igual que sin filtro;
    `?match_type=Casual` -> `rivals: []`; base vacia -> 200 con `rivals: []`.
  - Vecinos: `/api/duels/death-state/`, `/api/duels/thrown-advantage/?map=border`,
    `/api/players/1/` -> 200.
- Pantalla (Playwright, Chromium, base sembrada; accessibility-review):
  `columnheader` "Revanchas esa noche" con boton y `title` de ayuda; filas
  `acosador ... 3 (2-1)` y `casual ... —` (la rama `N (G-P)` que el e2e no ve
  y marco el LOW de la revision, vista aca); Enter con foco en el boton ordena
  (`aria-sort` descending, luego ascending); contraste celda 14.17:1, cabecera
  5.71:1 (AA); consola sin errores. CSV descargado: `3 (2-1)` y `0`.
  Sin Critical ni Major. Menor, no frena: `Récord` usa guion largo (`3–2`) y
  la columna nueva guion corto (`2-1`), como pedia el diseno.
- Chunk inicial: `Duelos` es `lazy` en `App.jsx`; `index-*.js` no cambia por la ficha.
- validate-data sobre la fila de `metricas.md`: conteo y record, sin tasa ni
  promedio; `—` en pantalla y 0 en CSV; la sesion sale de todas las partidas y
  las revanchas de las filtradas (coincide con `?map=`). Dos valores
  recalculados a mano arriba.
- Mutaciones en `_revanchas` (`python manage.py test tests.test_duels.RivalesRepetidosTests`):
  sin `[1:]` -> 8 fallan; `None` como derrota -> 1 falla; sesion ignorada -> 3
  fallan; desempate por `-id` -> 1 falla. Todas muertas; codigo restaurado.
- Sin migracion, parser, `recompute` nuevo, Electron ni `.ps1`: nada para
  `## Verificar en el PC`.

Skills: no aplica.
Skills del repo: accessibility-review (teclado, nombre, contraste: 0 Critical/Major), validate-data (2 valores recalculados), design-critique no aplica (sin pagina ni panel nuevo).
OMC: plan=— · revisión=— · verificación=PASS

## Para el humano

(nada)
