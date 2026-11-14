# 131. Rondas que el equipo gano sin ti

estado: implementado
candado: revisor 2026-11-14T00:16Z
rama: claude/equipo-dev/131-rondas-que-el-equipo-gano-sin-ti
tipo: funcionalidad
epica: escuadra
area: fullstack
prioridad: 3
fuente: ALCANCE.md C13
archivos: backend/replays/analytics/aggregates.py, backend/replays/views.py, backend/tests/test_ganadas_sin_ti.py, frontend/src/ganadasSinTi.js, frontend/src/ganadasSinTi.test.js, frontend/src/pages/Teammates.jsx, frontend/e2e/humo.spec.js, docs/metricas.md
turnos: po 20261113T1858Z-cxQ3TuB, arquitecto 20261113T2157Z-cG2vDSe, dev 20261113T2345Z-c6MAT6w

## PR

## Que gana quien usa la app

En Compañeros, de las rondas en que caiste, cuantas igual gano tu equipo, por
lado, y que compañero habitual seguia vivo al final de esas rondas: si el
equipo te cubre cuando mueres y quien cierra las rondas por ti. Hoy solo se ve
tu winrate cuando moris, no quien lo sostiene.

## Criterios de aceptacion

- [ ] Agregado nuevo en `aggregates.py`: sobre tus filas con `died=True` y
      ronda con ganador (`round__my_team_won` no nulo), rondas, ganadas y %
      por lado (`Attack`, `Defense`) y total. Las rondas sin ganador no
      cuentan. Test con rondas armadas de resultado conocido.
- [ ] Por compañero habitual (5 partidas juntas, `MIN_PARTIDAS_HABITUAL`,
      agrupado por `Player`): en cuantas de esas rondas ganadas sin ti
      sobrevivio (`survived` en su fila, mismo `team_index` que la tuya).
      Test con dos compañeros y un no habitual que no sale.
- [ ] Los filtros globales aplican sobre tu fila (como `teammate_synergy`);
      test con filtro de lado.
- [ ] `/api/teammates/` suma la clave; en `Teammates.jsx` un panel o tabla
      con el total por lado y la lista de compañeros con su `n`; sin rondas,
      una nota. e2e sobre `seed_demo` con los numeros de la API y consola
      limpia.
- [ ] Fila nueva en `docs/metricas.md` (y en `## Muestra minima` si se avisa
      muestra chica).

## Fuera de alcance

- El reverso (rondas perdidas sobreviviendo, F11).
- Quien hizo las bajas despues de que caiste (otro tramo: necesita el feed).
- Señales del Coach sobre esto.

## Diseno

Una sola forma obvia: el total por lado tiene la forma de `first_teammate_death`
(misma pagina, tabla por lado con fila Total) y la lista por compañero la de
`teammate_clutches` (habituales, `Player`, `*` de muestra chica). Sin arena
ni consenso (chica, sin migracion, sin `recompute`, sin parser). No duplica
"Primero en caer": aquella cuenta solo la primera baja de tu equipo; esta,
toda ronda en que caiste, y agrega quien seguia vivo.

**Backend** (`backend/replays/analytics/aggregates.py`, justo despues de
`teammate_clutches`):

- Constante `GANADA_SIN_TI_MIN = 5` con comentario: muestra minima por
  compañero, la de `CLUTCH_COMPANERO_MIN` (misma pagina, misma marca `*`).
- `won_without_me(**filters) -> dict`. Docstring: rondas en que caiste
  (`died=True` en tu fila) con ganador conocido; ganadas = tu equipo gano
  (`round__my_team_won=True`); por compañero habitual, en cuantas de las
  ganadas seguia vivo al final (`survived` en su fila, tu mismo
  `team_index`).
  - `caidas = base_queryset(**filters).filter(died=True, round__my_team_won__isnull=False)`.
  - Lados: `("Attack", "Defense")`, o solo `(filters["side"],)` si viene y es
    un lado (la regla de `by_overtime_side`); por lado `caidas.filter(side=lado)`
    con `.aggregate(rounds=Count("id"), won=Count("id", filter=Q(round__my_team_won=True)))`;
    mas una fila `"total"` sobre `caidas` entera. Cada fila: `side`,
    `rounds`, `won`, `pct` (`_pct(won, rounds)`, `None` con 0).
  - Habituales: la subconsulta `habituales` de `teammate_clutches`, copiada
    tal cual (si la 79 ya esta en dev, la de esa rama, que sale de
    `rondas_contables()`: una partida excluida no hace habitual). No extraer
    un helper: la 79 toca esa funcion y el refactor chocaria.
  - `mia_ganada = caidas.filter(round__my_team_won=True, round_id=OuterRef("round_id"), team_index=OuterRef("team_index"))`
    (correlacionada, por el tope de parametros de SQLite, como
    `teammate_clutches`); `filas = RoundPlayer.objects.filter(is_me=False,
    player_id__in=habituales).filter(Exists(mia_ganada)).values("player_id",
    "player__username").annotate(rounds=Count("id"), survived=Count("id",
    filter=Q(survived=True))).order_by("-survived", "-rounds", "player__username")`.
    `rounds` es el `n` del compañero: ganadas sin ti con el en tu equipo.
  - Devuelve `{"min_rounds": GANADA_SIN_TI_MIN, "sides": [...filas por lado..., total],
    "mates": [{"player_id", "username", "rounds", "survived", "pct",
    "low_sample": rounds < GANADA_SIN_TI_MIN}]}`.

**API:** `backend/replays/views.py`, vista `teammates`: clave
`"won_without_me": agg.won_without_me(**filters)` debajo de
`teammate_clutches`. Sin ruta nueva.

**Frontend:**

- `frontend/src/ganadasSinTi.js` (logica pura): `filasPorLadoSinTi(data)`:
  `[]` si la fila `total` tiene 0 rondas; si no, las filas de `sides` con
  `orden` (en el orden de la API: lados y despues Total).
  `filasSostienen(data)`: `data.mates` mapeadas a `{ clave: player_id,
  playerId, nombre: username, rounds, survived, pct, low_sample, orden }`.
- `frontend/src/pages/Teammates.jsx`: panel nuevo debajo de "Primero en
  caer": `<Panel title="Rondas que tu equipo ganó sin ti" hint="Rondas en que
  caíste y tu equipo igual ganó, y qué compañero habitual seguía vivo al
  final. Las rondas sin ganador no cuentan.">`. Sin filas por lado:
  `<p className="dim">Sin rondas en que hayas caído con estos filtros.</p>`.
  Si hay: un `DataTable` (Lado con `SideChip` o "Total" como en "Primero en
  caer"; `rounds` "Rondas en que caíste"; `won` "Ganadas"; `pct` "% ganadas"
  con `pct()`), `csvName="ganadas-sin-ti"`; debajo `<h3>Quién la sostiene</h3>`
  y, con compañeros, otro `DataTable` (Compañero con `Link` a
  `/jugadores/:id`; `rounds` "Ganadas sin ti juntos"; `survived` "Seguía vivo";
  `pct` "%" con el `*` de `muestra-chica` y su `title` "Menos de 5 rondas",
  como la tabla de clutches de compañeros), `initialSort={{ key: 'orden', dir: 'asc' }}`,
  `csvName="quien-la-sostiene"`; sin compañeros,
  `<p className="dim">Ningún compañero habitual en esas rondas.</p>`.

**Tests** (testing-strategy: el numero en Django, la forma en vitest, la
pantalla en e2e):

- `backend/tests/test_ganadas_sin_ti.py`, `GanadasSinTiTests`. La factory no
  expone `survived`: se marca con `RoundPlayer.objects.filter(pk=fila.pk).update(survived=True)`
  (no tocar `factories.py`, que la 79 tambien toca). Los habituales con un
  helper `partidas_juntas` como el de `test_clutch_companeros.py`.
  `test_cuenta_las_rondas_en_que_caiste_y_cuantas_gano_tu_equipo_por_lado`,
  `test_una_ronda_en_que_sobreviviste_no_cuenta`,
  `test_una_ronda_sin_ganador_no_cuenta`,
  `test_la_fila_total_suma_los_dos_lados`,
  `test_cuenta_que_companero_habitual_seguia_vivo`,
  `test_un_companero_no_habitual_no_sale`,
  `test_un_rival_que_sobrevive_no_cuenta` (otro `team_index`),
  `test_una_ronda_perdida_no_suma_al_companero`,
  `test_con_filtro_de_lado_sale_ese_lado_y_el_total`,
  `test_marca_muestra_chica_debajo_de_cinco_rondas`,
  `test_teammates_devuelve_ganadas_sin_ti`.
- `frontend/src/ganadasSinTi.test.js`: `sin rondas no hay tabla`, `deja las
  filas en el orden de la API con el total al final`, `mapea los compañeros
  con su enlace y su muestra`.
- `frontend/e2e/humo.spec.js`: test nuevo `Compañeros muestra las rondas que
  el equipo ganó sin ti`, al lado de `Compañeros muestra quien cae primero`:
  el panel por su heading, la fila Total con los numeros que da
  `/api/teammates/` sobre `seed_demo` (fijados con un comentario) y consola
  limpia (`vigilarConsola`).

**`docs/metricas.md`**, seccion "Duelos de apertura", fila nueva debajo de
"Primero de tu equipo en caer": **Rondas que tu equipo ganó sin ti** = tus
rondas con `died=True` y ganador conocido; Ganadas = las que gano tu equipo;
% = ganadas / rondas en que caiste, por lado de tu fila y total; con filtro de
lado sale ese lado y el total. *Quién la sostiene*: por compañero habitual
(la regla de "Clutches de tus compañeros": 5 partidas en tu equipo, todo el
historial, por `Player`), de esas rondas ganadas con el en tu equipo, en
cuantas seguia vivo al final (`survived` en su fila); un `*` marca menos de 5
rondas (`GANADA_SIN_TI_MIN`), sale igual. Filtros de la barra sobre tu fila.
Y en `## Muestra minima`: "Quién la sostiene | habitual para salir; 5 rondas
por fila (`GANADA_SIN_TI_MIN`): se avisa con *".

**Orden:** agregado y tests Django -> clave en `teammates` ->
`ganadasSinTi.js` y vitest -> panel -> e2e con los numeros del seed ->
`metricas.md` -> `npm run build`.

**Que puede romperse:** `survived` sale del `.rec` (lo escribe el parser al
importar); si en algun replay falta, el compañero no suma y el `n` lo deja
ver. "Seguia vivo" no es "hizo las bajas" (fuera de alcance). Archivos
compartidos con ramas abiertas: `aggregates.py` y `views.py` con la 133 y la
79, `humo.spec.js` con la 129, la 130 y la 133, `metricas.md` con la 129, la
133 y la 79; `Teammates.jsx` con ninguna. Funciones y filas distintas, sin
migracion: no espera a ninguna. Relacion con la 109 (frenada por la 79,
misma epica): ninguna dependencia de archivos ni de datos.

**Verificacion manual:** `/companeros` sobre el seed: panel "Rondas que tu
equipo ganó sin ti" debajo de "Primero en caer"; con lado Ataque, la fila de
ataque y la Total; el enlace de un compañero abre su perfil. Umbral: el 5 de
la tabla de clutches de compañeros, sin calibracion nueva.

Skills: no aplica (sin dominio nuevo).
Skills del repo: statistical-analysis (denominador = rondas en que caiste con
ganador; el `n` por compañero a la vista y `*` debajo de 5; sin promedio de
promedios: conteos sobre filas), testing-strategy (Django, vitest y e2e
repartidos arriba); dataviz no aplica (tablas).
OMC: plan=— · revisión=— · verificación=—

## Implementacion

Quedo el diseno completo, sin desvios de alcance:

- `aggregates.won_without_me` (despues de `teammate_clutches`) con la constante
  `GANADA_SIN_TI_MIN = 5`; lados con la regla de `by_overtime_side`
  (`PRORROGA_LADOS`), fila `total`; `habituales` copiada tal cual de
  `teammate_clutches` (la 79 no esta en dev); `mia_ganada` correlacionada por
  `round_id` y `team_index`.
- `/api/teammates/` suma `won_without_me`. Sin ruta nueva.
- `frontend/src/ganadasSinTi.js` (`filasPorLadoSinTi`, `filasSostienen`) y el
  panel "Rondas que tu equipo ganó sin ti" en `Teammates.jsx`, debajo de
  "Primero en caer", con la tabla por lado y "Quién la sostiene" (enlace al
  perfil, `*` debajo de 5 rondas).
- `docs/metricas.md`: fila debajo de "Primero de tu equipo en caer" y fila en
  `## Muestra minima`.

Desvios menores del diseno:

- Tests: la factory ya deriva `survived = not died`, asi que los companeros
  vivos se arman con `died=False` en vez de `update(survived=True)`; no se toca
  `factories.py`.
- Test extra `test_un_habitual_que_juega_de_rival_no_suma_esa_ronda` (pedido por
  la revision ciega): `test_un_rival_que_sobrevive_no_cuenta` lo cubria la regla
  de habitual, no la correlacion por `team_index`. Con la correlacion quitada a
  mano, el test nuevo falla (visto); restaurada, pasa.
- Filtro de mapa probado (`test_el_filtro_de_mapa_va_sobre_tu_fila`) en vez de
  solo el de lado.
- Hint del panel suma "Seguir vivo no es haber hecho las bajas" (lo que el
  diseno pone en "Que puede romperse").

Criterios -> tests: (1) `test_cuenta_las_rondas_en_que_caiste_y_cuantas_gano_tu_equipo_por_lado`,
`test_una_ronda_sin_ganador_no_cuenta`, `test_una_ronda_en_que_sobreviviste_no_cuenta`,
`test_la_fila_total_suma_los_dos_lados`; (2) `test_cuenta_que_companero_habitual_seguia_vivo`,
`test_un_companero_no_habitual_no_sale`, `test_un_rival_que_sobrevive_no_cuenta`,
`test_un_habitual_que_juega_de_rival_no_suma_esa_ronda`, `test_una_ronda_perdida_no_suma_al_companero`,
`test_marca_muestra_chica_debajo_de_cinco_rondas`; (3) `test_con_filtro_de_lado_sale_ese_lado_y_el_total`,
`test_el_filtro_de_mapa_va_sobre_tu_fila`; (4) `test_teammates_devuelve_ganadas_sin_ti`,
`ganadasSinTi.test.js` (4 tests) y e2e `Compañeros muestra las rondas que el equipo ganó sin ti`
(seed_demo: Total 173 rondas, 98 ganadas, 57 %; Seba 98 juntos, 38 vivo);
(5) `docs/metricas.md`.

TDD: los tests Django se escribieron antes del agregado (primera corrida en
rojo por un `won=None` en la factory del test, corregido en el helper); el
vitest antes de usarlo en el panel.

Verificacion manual sugerida: `/companeros` sobre el seed, con lado Ataque
(sale Ataque y Total) y el enlace de Seba al perfil.

Skills: no aplica (sin dominio nuevo).
Skills del repo: testing-strategy (numero en Django, forma en vitest, pantalla
en e2e), statistical-analysis (denominador = rondas en que caiste con ganador,
`n` por compañero a la vista, `*` debajo de 5), ux-copy (textos en voseo
neutro con tildes, como el resto de la pagina); modern-web-guidance no se
consulto: el JSX copia el patron vecino de la misma pagina (DataTable, Panel).
OMC: plan=— · revisión=3 hallazgos (3 arreglados) · verificación=—

## Revision

## QA

## Para el humano

(nada)
