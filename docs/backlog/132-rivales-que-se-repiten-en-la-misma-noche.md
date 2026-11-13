# 132. Rivales que se repiten en la misma noche

estado: disenado
candado: -
rama: -
tipo: funcionalidad
epica: rivales
area: fullstack
prioridad: 3
fuente: ALCANCE.md D13
archivos: backend/replays/analytics/aggregates.py, backend/tests/test_duels.py, frontend/src/pages/Duelos.jsx, frontend/e2e/humo.spec.js, docs/metricas.md
turnos: po 20261113T1926Z-ce4Pmp6, arquitecto 20261113T2318Z-chc2kiA

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

## Revision

## QA

## Para el humano

(nada)
