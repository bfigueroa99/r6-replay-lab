# 128. Repetir o cambiar el spawn tras perder

estado: revisado
candado: qa 2026-11-14T00:04Z
rama: claude/equipo-dev/128-repetir-o-cambiar-el-spawn-tras-perder
tipo: funcionalidad
epica: posicionamiento
area: fullstack
prioridad: 3
fuente: ALCANCE.md S3
archivos: backend/replays/analytics/aggregates.py, backend/replays/views.py, backend/replays/urls.py, backend/tests/test_repetir_spawn.py, frontend/src/repetirSpawn.js, frontend/src/repetirSpawn.test.js, frontend/src/pages/Coach.jsx, frontend/e2e/humo.spec.js, docs/metricas.md
turnos: po 20261113T1858Z-cxdASk3, arquitecto 20261113T2157Z-cG2vDSe, dev 20261113T2345Z-c5J2BqJ, revisor 20261113T2345Z-c6MAT6w

## PR

## Que gana quien usa la app

En ataque, despues de perder una ronda, cuantas veces vuelves a salir del
mismo spawn y cuantas cambias, con el winrate de la ronda siguiente en cada
caso (y lo mismo tras ganar, como base). Dice si insistir con el spawn que
te acaba de costar la ronda te sale caro; es el gemelo de spawn de la 113
(operador).

## Criterios de aceptacion

- [ ] Un agregado nuevo arma pares de tus rondas de ataque consecutivas de
      la misma partida (`Round.number` siguiente, sin hueco de numeracion,
      las dos con `RoundPlayer.side` ataque y `RoundPlayer.spawn` no vacio)
      y devuelve, por resultado de la primera (`after_loss`, `after_win`) y
      caso (`repeat`, `switch`), `rounds`, `decided`, `won` y
      `winrate` de la segunda. Test: pierdes desde el spawn A, repites A dos
      veces (ganas una) y cambias a B una vez (ganas) -> repeat 2 rondas
      50 %, switch 1 ronda 100 %.
- [ ] Un par con una ronda sin spawn, de defensa o con hueco de numeracion
      no entra; una segunda sin ganador cuenta en `rounds` y no en el
      winrate. Test.
- [ ] Los filtros globales aplican; `site` y `operator` eligen la primera
      ronda del par (como la 113). Test con filtro de mapa.
- [ ] Se ve en la pagina donde vive "Salida del spawn" (Coach), con el aviso
      de muestra de la pagina (se avisa, no se oculta) y un texto sin pares;
      e2e de humo con la consola limpia.
- [ ] Fila nueva en `docs/metricas.md` ("Repetir o cambiar el spawn tras perder").

## Fuera de alcance

- A que spawn cambias (el desglose por par, como la 126 para operadores).
- Defensa: el defensor no elige spawn como el atacante.
- Recomendar un spawn.

## Diseno

Una sola forma obvia: es `site_after_loss` (107, el panel vecino del Coach)
leyendo tu spawn de ataque en vez del sitio de defensa, con los dos bloques
`after_loss`/`after_win` de `operator_after_result` (113). Sin arena ni
consenso (chica, sin migracion, sin `recompute`, sin parser).

**Ajuste al criterio 1 (decision de diseno, no de alcance):** el par es tu
ronda de ataque y tu *siguiente ronda de ataque* de la partida, sin hueco de
numeracion; las de defensa entre medio no lo cortan. Es la regla de la 107 y
la 113, que viven en la misma pagina y en la misma tabla de `metricas.md`;
"`Round.number` siguiente" estricto cambiaria la regla solo para este panel.
En la practica casi todos los pares son consecutivos (el ataque se juega en
bloque).

**Backend** (`backend/replays/analytics/aggregates.py`, justo despues de
`site_after_loss`):

- `spawn_after_result(**filters) -> dict`. Docstring con la regla del par y
  los filtros. Cuerpo, con el bucle de `site_after_loss` como molde:
  `operador = filters.get("operator")`, `sitio = filters.get("site")`,
  `base = {k: v for k, v in filters.items() if k not in ("side", "operator", "site")}`;
  `filas = base_queryset(**base).order_by("round__match_id", "round__number")
  .values_list("round__match_id", "round__number", "side", "spawn",
  "operator", "round__site", "round__my_team_won")`. Recorrido: se corta
  (`previa = None`) si cambia la partida, si `numero != anterior + 1` o si la
  fila no tiene lado; las filas que no son `"Attack"` se saltan sin cortar;
  una de ataque sin `spawn` corta. Con `previa`: `caso = "repeat"` si el
  spawn es el mismo, si no `"switch"`; `tras = "after_win"` si `previa` gano,
  si no `"after_loss"`; `_sumar_caso(bloques[tras][caso], gano)` (ya existe);
  `pares += 1`. Despues, `previa = (spawn, gano)` solo si `gano is not None`
  y la fila cumple `operator` y `site` (eligen la primera ronda del par, como
  la 113); si no, `previa = None`.
- Devuelve `{"min_rounds": REPETIR_SITIO_MIN_RONDAS, "pairs": pares,
  "after_loss": {"repeat": caso, "switch": caso}, "after_win": {...}}`, cada
  caso con `rounds`, `decided`, `won`, `winrate` (`_pct`, `None` sin
  decididas; `_caso_vacio()` ya existe). Muestra minima: la misma constante
  de 8 de la 107 (tabla "Sitio / spawn" de `metricas.md`), sin constante nueva.
- Sin desglose por mapa ni por par de spawns (fuera de alcance).

**API:** `backend/replays/urls.py`, `path("positioning/spawn-after-result/",
views.spawn_after_result, name=...)` al lado de `site-after-loss`;
`backend/replays/views.py`, vista `@require_GET def spawn_after_result`
igual a `site_after_loss`. Si la 79 ya esta en dev, su guardia pide la ruta
nueva clasificada en `tests/test_excluir_partida.py` (`COMPARADAS` y
`_rutas()`): pasa por `base_queryset`, va como comparada.

**Frontend:**

- `frontend/src/repetirSpawn.js` (logica pura, como `repetirSitio.js`):
  `hayParesSpawn(data)` (`!!data?.pairs`); `textoParesSpawn(n)`:
  `'1 par de rondas de ataque seguidas'` / `` `${n} pares de rondas de ataque seguidas` ``;
  `filasRepetirSpawn(data)`: dos filas en orden fijo, `{ tras: 'after_loss',
  tramo: 'Tras perder' }` y `{ tras: 'after_win', tramo: 'Tras ganar' }`, cada
  una con `repeat_rounds`, `repeat_winrate`, `repeat_poca`, `switch_rounds`,
  `switch_winrate`, `switch_poca` (`poca = rounds < min_rounds`), `orden`.
  Reusa `textoWinrate` de `repetirSitio.js` (importarla, no copiarla).
- `frontend/src/pages/Coach.jsx`: `PanelRepetirSpawn({ filters })` debajo de
  `PanelRepetirSitio`, con `useApi('/positioning/spawn-after-result/', filters)`.
  Titulo "Repetir o cambiar el spawn"; hint: "En ataque, después de una
  ronda, si en tu siguiente ronda de ataque de esa partida saliste del mismo
  spawn o de otro, y cuánto la ganaste. Tras ganar es la base para comparar.
  Con el filtro de operador o de sitio, solo las rondas que lo cumplen abren
  el par." Error/carga como el panel de arriba; sin pares,
  `<p className="note">Sin rondas de ataque seguidas de otra con spawn con estos filtros.</p>`;
  con pares, la nota `textoParesSpawn(data.pairs)` y un `DataTable` de dos
  filas: `{ key: 'tramo', label: 'Tras', left: true, sortable: false }`,
  Repite (`repeat_rounds`, help "Rondas en que saliste del mismo spawn."),
  `winrateConMuestra('repeat', 'Winrate repitiendo')`, Cambia
  (`switch_rounds`, help "Rondas en que saliste de otro spawn."),
  `winrateConMuestra('switch', 'Winrate cambiando')` (ya estan en
  `Coach.jsx`); `initialSort={{ key: 'orden', dir: 'asc' }}`,
  `rowKey={(row) => row.tras}`, `csvName="repetir-spawn"`. El aviso de
  muestra es el "· pocas rondas" de `textoWinrate`, como la 107.

**Tests** (testing-strategy: el numero en Django, la forma de las filas en
vitest, la pantalla en e2e con el seed):

- `backend/tests/test_repetir_spawn.py`, `RepetirSpawnTests`:
  `test_tras_perder_cuenta_repetir_y_cambiar_con_el_winrate_de_la_segunda`
  (el caso del criterio: repeat 2 rondas 50 %, switch 1 ronda 100 %),
  `test_tras_ganar_va_a_su_propio_bloque`,
  `test_una_ronda_de_defensa_entre_medio_no_corta_el_par`,
  `test_un_hueco_de_numeracion_corta_el_par`,
  `test_una_ronda_de_ataque_sin_spawn_corta_el_par`,
  `test_una_primera_sin_ganador_no_abre_par`,
  `test_una_segunda_sin_ganador_cuenta_en_rondas_y_no_en_el_winrate`,
  `test_el_filtro_de_operador_elige_la_primera_ronda`,
  `test_el_filtro_de_mapa_aplica`,
  `test_el_filtro_de_lado_no_cambia_nada`,
  `test_el_endpoint_responde_con_base_vacia` (`pairs` 0, winrate `None`).
- `frontend/src/repetirSpawn.test.js`: `sin pares no hay panel`,
  `dos filas en orden fijo aunque falte un bloque`, `marca pocas rondas debajo
  del minimo y no en el minimo`, `texto de pares en singular y plural`.
- `frontend/e2e/humo.spec.js`, test nuevo `el Coach muestra si repites el
  spawn tras perder`, al lado del de la 107: el panel por su heading, la nota
  con los pares que da `seed_demo` y las dos filas; consola limpia
  (`vigilarConsola`). Los numeros se leen de `/api/positioning/spawn-after-result/`
  sobre el seed y se fijan en el test con un comentario, como el de la 107.

**`docs/metricas.md`**, fila nueva debajo de "Repetir el sitio tras
perderlo": **Repetir o cambiar el spawn** = panel del Coach
(`/api/positioning/spawn-after-result/`); pares de tus rondas de ataque
consecutivas de la misma partida (por `Round.number`, saltando las de defensa
entre medio), cortados por un numero faltante, una ronda sin lado o una de
ataque sin spawn; separados por el resultado de la primera (*Tras perder*,
*Tras ganar*; una primera sin ganador no abre par); *Repite* si la segunda
sale del mismo spawn (`RoundPlayer.spawn`), *Cambia* si no; winrate de la
segunda sobre las que tienen ganador (una sin ganador cuenta en las rondas,
no en el winrate); mapa, tipo, modo, fechas y sesion aplican; lado no (es
siempre ataque); operador y sitio eligen la primera ronda del par; muestra
minima 8 rondas por caso (la de la 107): se avisa "pocas rondas", no se oculta.

**Orden:** agregado y tests Django -> ruta y vista -> `repetirSpawn.js` y
vitest -> panel en `Coach.jsx` -> e2e con los numeros del seed ->
`metricas.md` -> `npm run build`.

**Que puede romperse:** el spawn depende del nombre que da el `.rec` por
mapa; dos versiones de un mapa con el mismo nombre de spawn no importan
porque el par es dentro de una partida. Archivos compartidos con ramas
abiertas: `aggregates.py`, `views.py` y `urls.py` con la 133 y la 79,
`humo.spec.js` con la 129, la 130 y la 133, `metricas.md` con la 129, la 133 y
la 79; `Coach.jsx` con ninguna. Funciones, rutas y filas distintas, sin
migracion: no espera a ninguna.

**Verificacion manual:** `/coach` sobre el seed: el panel "Repetir o cambiar
el spawn" debajo de "Repetir el sitio tras perderlo", dos filas; con el filtro
de lado Defensa, los mismos numeros; con un operador de defensa, sin pares
(la nota). Umbral: el 8 de la 107, sin calibracion nueva.

Skills: no aplica (sin dominio nuevo: panel y agregado con molde en el repo).
Skills del repo: statistical-analysis (denominador `decided`, `n` a la vista
en Repite/Cambia, base "Tras ganar" para no leer la tasa sin comparacion,
muestra minima ya calibrada de la 107), testing-strategy (Django, vitest y
e2e repartidos arriba); dataviz no aplica (tabla, sin grafico).
OMC: plan=— · revisión=— · verificación=—

## Implementacion

(dev 20261113T2345Z-c5J2BqJ)

Quedo el diseno completo, sin desvios de forma:

- `aggregates.spawn_after_result` (despues de `site_after_loss`), con la
  regla del par de la 113: las de defensa entre medio no cortan; un numero
  faltante, una ronda sin lado o una de ataque sin spawn si. `side` no
  filtra; `operator` y `site` eligen la primera ronda. Devuelve
  `min_rounds` (el 8 de la 107), `pairs`, `after_loss` y `after_win` con
  `repeat`/`switch`. Sin filtro de `UNKNOWN_PREFIX`: el parser no produce
  spawns desconocidos (lo confirmo la revision ciega).
- Ruta `positioning/spawn-after-result/` y vista plana al lado de
  `site-after-loss`. La 79 no esta en dev: no hay `test_excluir_partida.py`
  que clasificar; cuando entre, la ruta va como comparada (pasa por
  `base_queryset`).
- `frontend/src/repetirSpawn.js` (reusa `textoWinrate` via
  `winrateConMuestra` de `Coach.jsx`, sin copiarla) y `PanelRepetirSpawn`
  debajo de `PanelRepetirSitio`.
- Fila en `docs/metricas.md` y su linea en la tabla de muestras minimas.

Criterios -> tests:
- Criterio 1: `test_tras_perder_cuenta_repetir_y_cambiar_con_el_winrate_de_la_segunda`,
  `test_tras_ganar_va_a_su_propio_bloque`, `test_una_ronda_de_defensa_entre_medio_no_corta_el_par`.
- Criterio 2: `test_un_hueco_de_numeracion_corta_el_par`,
  `test_una_ronda_de_ataque_sin_spawn_corta_el_par`, `test_una_ronda_sin_lado_corta_el_par`,
  `test_los_pares_no_cruzan_partidas`, `test_una_primera_sin_ganador_no_abre_par`,
  `test_una_segunda_sin_ganador_cuenta_en_rondas_y_no_en_el_winrate`.
- Criterio 3: `test_el_filtro_de_operador_elige_la_primera_ronda`,
  `test_el_filtro_de_sitio_elige_la_primera_ronda`, `test_el_filtro_de_mapa_aplica`,
  `test_el_filtro_de_lado_no_cambia_nada`, `test_el_endpoint_responde_con_base_vacia`.
- Criterio 4: vitest `repetirSpawn.test.js` (4) y e2e `el Coach muestra si
  repites el spawn tras perder`. Sobre `seed_demo` son 87 pares, todos tras
  ganar y repitiendo (100 %); "Tras perder" queda en 0 con "— · pocas
  rondas". El seed no ejercita "Cambia" con datos; eso lo cubren Django y
  vitest.
- Criterio 5: fila "Repetir o cambiar el spawn" en `metricas.md`.

TDD: los 12 tests de Django en rojo (`errors=12`, sin `spawn_after_result`)
antes del agregado; vitest en rojo (sin modulo) antes de `repetirSpawn.js`.

Revision ciega (`omc-code-reviewer`): aprobar, 4 LOW, los 4 atendidos
(tests de sitio y de ronda sin lado; nota sin pares reescrita sin el doble
"con"; hint "cuánto ganaste esa siguiente ronda"). El del e2e que no ve
"Cambia" queda anotado arriba: es el seed, no el panel.

Skills: no aplica (sin dominio nuevo).
Skills del repo: test-driven-development (rojo visto en Django y vitest
antes del codigo), modern-web-guidance (sin CLI: `npx` bloqueado en esta
sesion; guia local `accessibility/accessibility.md`, tablas con cabecera: se
reusa `DataTable`, sin JSX ni CSS nuevo fuera de el), ux-copy (estado vacio
y hint reescritos por claridad, con tildes como el resto de la UI).
OMC: plan=— · revisión=4 hallazgos (4 arreglados) · verificación=—

## Revision 2026-11-14T00:00Z sobre dfde6d7

(revisor 20261113T2345Z-c6MAT6w)

Eje de estandares, a ciegas (`omc-code-reviewer` con `revision.md`, sin la
ficha): aprobar, 0 CRITICAL/HIGH/MEDIUM, 2 LOW confirmados por el lider.
Eje de intencion (diff de 336 lineas): lo hizo el lider contra `## Que gana`,
`## Criterios` y `## Fuera de alcance`, sin subagente aparte.

- [estilo] LOW docs/metricas.md:215
  Que pasa: la fila dice "(`REPETIR_SITIO_MIN_RONDAS`, la de la 107)".
  Como reproducirlo o por que es cierto: `grep -n "la de la 107" docs/metricas.md`; la
  fila hermana "Repetir el sitio tras perderlo" no nombra fichas, y
  `metricas.md` es doc para quien usa la app.
  Arreglo sugerido: borrar ", la de la 107".
- [regla] LOW frontend/src/pages/Coach.jsx:359
  Que pasa: con el filtro de lado en Defensa el panel muestra los mismos pares
  de ataque y el hint no lo explica (solo nombra operador y sitio).
  Como reproducirlo o por que es cierto: `test_el_filtro_de_lado_no_cambia_nada`
  fija que `?side=Defense` devuelve lo mismo que sin filtro.
  Arreglo sugerido: sumar al hint "El filtro de lado no aplica: siempre es ataque."
- [test] LOW frontend/e2e/humo.spec.js:1710
  Que pasa: en `seed_demo` todas tus rondas de ataque se ganan y el spawn
  siempre se repite, asi que la fila "Tras perder" sale en 0 y "Cambia" en 0:
  el e2e no ve en pantalla el caso que motiva la ficha.
  Como reproducirlo o por que es cierto: el e2e afirma 87 pares, todos "Tras
  ganar" al 100 %. El numero lo cubren los tests Django; es limite del seed.
  Arreglo sugerido: ninguno en esta ficha (cambiar `seed_demo` mueve los
  numeros de otros e2e); anotado por si una ficha futura toca el seed.

Ficha: cada criterio tiene test con nombre (criterio 1:
`test_tras_perder_cuenta_repetir_y_cambiar_con_el_winrate_de_la_segunda`, el
caso exacto del criterio; 2: hueco, sin spawn, sin lado, primera y segunda sin
ganador, partidas distintas; 3: operador, sitio, mapa y lado; 4: e2e `el Coach
muestra si repites el spawn tras perder`; 5: fila en `metricas.md`). El diff
no toca archivos fuera de `archivos:`. Fuera de alcance respetado (sin
desglose por par, sin defensa, sin recomendacion). Identificadores sin
tildes, UI con tildes; sin `print` ni `console.log`. Sin dependencias, sin
POST, sin calculo al consultar fuera de agregar.

check.sh sobre dfde6d7 (rama al dia con dev): verificar.sh VERDE, 1335 tests
backend, 435 vitest, 116 e2e.

Veredicto: aprobar.

OMC: plan=— · revisión=2 LOW + 1 LOW del lider (0 arreglados: el Revisor no arregla) · verificación=—
Skills del repo: ninguna

## QA

## Para el humano

(nada)
