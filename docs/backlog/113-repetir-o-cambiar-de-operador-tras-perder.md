# 113. Repetir o cambiar de operador después de perder

estado: revisado
candado: qa 2026-11-13T04:04Z
rama: claude/equipo-dev/113-repetir-o-cambiar-de-operador-tras-perder
tipo: funcionalidad
epica: operadores
area: fullstack
prioridad: 3
fuente: ALCANCE.md O10
archivos: backend/replays/analytics/aggregates.py (operator_after_result, OPERADOR_TRAS_RESULTADO_*), backend/replays/views.py (operators_after_result), backend/replays/urls.py, backend/tests/test_operador_tras_resultado.py, frontend/src/operadorTrasResultado.js, frontend/src/operadorTrasResultado.test.js, frontend/src/pages/Operators.jsx, frontend/e2e/humo.spec.js, docs/metricas.md
turnos: po 20261112T1204Z-chGLrtC, arquitecto 20261112T1603Z-cor3JBP, dev 20261112T2004Z-cbaTGDt, revisor 20261113T0003Z-cVnayJ8

## PR

## Que gana quien usa la app

En Operadores, despues de perder una ronda con un operador, la app dice
cuantas veces lo repetiste en la siguiente ronda del mismo lado de la partida
y cuantas cambiaste, con el winrate de esa ronda siguiente en cada caso (y lo
mismo despues de ganar, como base). Responde si cambiar de operador tras una
ronda mala te ayuda o es tilt, cosa que la tabla por operador no puede decir.

## Criterios de aceptacion

- [ ] Un agregado devuelve, por lado y en total, para pares de rondas tuyas
      consecutivas del mismo lado en la misma partida (por `Round.number`,
      saltando las del otro lado), separados por el resultado de la primera
      (`after_loss`, `after_win`): `repeat` y `switch` con `rounds` y
      `winrate` de la segunda. Test con una partida armada: perder con Ash y
      volver a Ash cuenta `repeat`; pasar a Thermite cuenta `switch`.
- [ ] Una ronda sin `.rec` entre medio (hueco en `number`), un operador
      vacio o `Unknown(...)` cortan el par, y los pares no cruzan partidas
      ni lados. Test.
- [ ] Una primera ronda sin ganador no entra ni en `after_loss` ni en
      `after_win`; una segunda sin ganador cuenta en `rounds` y no en el
      winrate. Test.
- [ ] Los filtros de mapa, tipo, modo, fechas y sesion aplican; el de lado
      elige que bloque se muestra; el de operador filtra el operador de la
      ronda perdida o ganada (la primera del par). Test del de operador.
- [ ] Se ve en Operadores con la muestra minima de operador (12 rondas) como
      aviso, no como recorte; sin pares, un texto y no un error. El e2e de
      humo pasa por Operadores con la consola limpia.
- [ ] Fila nueva en `docs/metricas.md` ("Repetir o cambiar de operador").

## Fuera de alcance

- El mismo corte para el spawn (S3) o el sitio de defensa (ficha 107).
- Separar por operador de destino o recomendar a cual cambiar.
- Operadores de tus compañeros.

## Diseno

(arquitecto 20261112T1603Z-cor3JBP) Filtros duros: pasa. Usa `RoundPlayer.operator`,
`side`, `Round.number` y `my_team_won`, que el `.rec` entrega; sin red,
sin dependencias, sin POST, sin migracion. Una forma obvia y chica (~350
lineas), gemela de la 107 (mismo recorrido de pares): sin arena ni consenso.

**Pagina: Operadores**, panel propio **al final**, despues de `PorSitio`
(la 102 mete `TuPool` antes de `PorSitio`: asi los dos no se pisan).
Endpoint propio `GET /api/operators/after-result/`, pedido aparte: un
error no tumba la pagina.

**Backend, `aggregates.py`**, despues de `operator_by_site`:

- `OPERADOR_TRAS_RESULTADO_MIN_RONDAS = 12`, la de "Operador" de la tabla
  de muestra minima (la misma que usa el coach con `by_operator`): debajo
  se avisa, no se oculta. `OPERADOR_TRAS_RESULTADO = ("after_loss",
  "after_win")` y casos `("repeat", "switch")`.
- `operator_after_result(**filters) -> dict`:
  1. `operador = filters.get("operator")`; `base = {k: v for k, v in
     filters.items() if k not in ("side", "operator")}`. `side` no filtra
     el queryset (las rondas del otro lado hacen falta para ver huecos; el
     frontend elige el bloque); `operator` elige la primera ronda del par
     (paso 4), no filtra las filas: filtrarlo dejaria solo pares que
     repiten.
  2. Una consulta: `base_queryset(**base).order_by("round__match_id",
     "round__number").values("round__match_id", "round__number", "side",
     "operator", "round__my_team_won")`. Por `base_queryset` entran las
     exclusiones de la 79 cuando se mergee.
  3. Recorrido en orden, con un pendiente por lado (`dict` lado -> fila):
     - se vacian **los dos** pendientes si la fila cambia de partida, si su
       numero no es el anterior + 1 (ronda sin `.rec` o sin fila tuya) o si
       `side == ""`;
     - una fila con `operator == ""` o que empieza con
       `unknowns.UNKNOWN_PREFIX` corta su lado (pendiente de ese lado fuera)
       y no abre par;
     - si hay pendiente de su lado, cuenta el par: `repeat` si el operador
       es el mismo, si no `switch`; resultado del pendiente
       (`after_win` si gano, `after_loss` si perdio); suma `rounds` y,
       si la fila tiene ganador, `decided` y `won`;
     - despues la fila queda como pendiente de su lado solo si tiene
       ganador (sin ganador no entra ni en `after_loss` ni en
       `after_win`) y, con `operador`, si es ese operador; si no, el
       pendiente de su lado se borra.
     Las rondas del otro lado no tocan el pendiente: el par es "tu siguiente
     ronda de ataque" aunque haya defensas en medio.
  4. `winrate = _pct(won, decided)` por caso.
  5. Respuesta:
     ```
     {"min_rounds": 12, "pairs": <total>,
      "sides": {"Attack": B, "Defense": B}, "total": B}
     ```
     con `B = {"after_loss": {"repeat": C, "switch": C}, "after_win": {...}}`
     y `C = {"rounds", "decided", "won", "winrate"}`; `total` suma los dos
     lados. Sin pares: todo en 0, `winrate: None`, `pairs: 0`.

**`views.py`**: `operators_after_result` con `@require_GET` y
`_ok(agg.operator_after_result(**_filters(request)))`, junto a
`operators_by_site`. **`urls.py`**: `path("operators/after-result/",
views.operators_after_result, name="operators-after-result")` despues de
`operators/sites/`.

**Frontend.**

- `frontend/src/operadorTrasResultado.js` (logica pura):
  `filasTrasResultado(data, lado)` devuelve las filas de la tabla: con
  `lado` `Attack`/`Defense`, las dos de ese lado; si no, Total, Ataque y
  Defensa, cada uno con "tras perder" y "tras ganar" (6 filas). Cada fila:
  `clave` (`Attack-after_loss`...), `lado` (`Total`/`Ataque`/`Defensa`),
  `tras` (`Tras perder`/`Tras ganar`), `repeat_rounds`,
  `repeat_winrate`, `switch_rounds`, `switch_winrate`, `repeat_poca`,
  `switch_poca` (`rounds < min_rounds`). Filas con 0 pares en los dos
  casos se omiten. `hayPares(data)` (`!!data?.pairs`).
  `textoWinrate(winrate, poca)`: `Math.round` + `%`, `—` si null, y
  " · pocas rondas" si `poca` (igual que `repetirSitio.js` de la 107; no
  se importa de ahi porque la 107 no esta en dev: si al implementar ya
  esta, importarla y no duplicarla).
- `operadorTrasResultado.test.js` (vitest): sin datos y `pairs: 0` ->
  `hayPares` false; sin lado salen Total, Ataque y Defensa en ese orden;
  con lado solo ese; una fila sin pares se omite; `poca` debajo y en el
  minimo; `textoWinrate`.
- `Operators.jsx`: `TrasResultado({ filters })` con
  `useApi('/operators/after-result/', filters)`, mismo patron que
  `PorSitio` (ErrorBox / Loading / nota). `<Panel title="Repetir o
  cambiar tras perder" hint="Tu siguiente ronda del mismo lado en la
  partida: si repetiste el operador o cambiaste, y cuánto la ganaste. «Tras
  ganar» es la base para comparar. Con el filtro de operador, solo las
  rondas jugadas con ese operador antes del cambio.">`. `DataTable` con
  columnas Lado, Tras, Repite (rondas), Winrate repitiendo, Cambia (rondas),
  Winrate cambiando; las de winrate con `render: textoWinrate(...)` y
  `csv` con el numero crudo (como hace el Coach en la 107);
  `csvName="operador-tras-resultado"`, sin orden inicial distinto del de
  las filas (`initialSort` por `lado` no: dejar el orden de
  `filasTrasResultado`, `sortable` normal). Sin pares: `<p
  className="note">` "Sin rondas seguidas del mismo lado con estos
  filtros.".

**Tests backend, `backend/tests/test_operador_tras_resultado.py`** (con
`factories`; `make_round_player(..., won=bool(gano))` porque
`RoundPlayer.won` no admite nulo):

- `test_perder_con_ash_y_volver_a_ash_cuenta_repeat` y
  `test_pasar_a_thermite_cuenta_switch`.
- `test_tras_ganar_va_a_after_win`.
- `test_las_rondas_del_otro_lado_no_cortan_el_par` (A0 perdida, D1, A2).
- `test_una_ronda_faltante_entre_medio_corta_el_par` (0 y 2 sin 1).
- `test_operador_vacio_o_unknown_corta_el_par` (como primera y como
  segunda).
- `test_los_pares_no_cruzan_partidas`: la segunda partida arranca en la
  ronda 2 (numeros 0 y 1 sin crear) para que solo el cambio de partida
  corte (leccion de la revision de la 107: con la ronda 0 corta el hueco y
  el test no prueba nada).
- `test_los_pares_no_cruzan_lados` (A0, D1: ningun par).
- `test_primera_sin_ganador_no_abre_par` y
  `test_segunda_sin_ganador_cuenta_en_rondas_y_no_en_winrate`.
- `test_el_filtro_de_operador_elige_la_primera_ronda`: A0 Ash perdida ->
  A1 Thermite, A2 Thermite perdida -> A3 Ash; con `?operator=Ash` solo el
  primer par (`switch`, 1).
- `test_el_filtro_de_lado_se_ignora`: misma respuesta con `?side=Attack`.
- `test_el_filtro_de_mapa_aplica`.
- `test_total_suma_los_dos_lados`.
- `test_sin_pares_responde_vacio_sin_error` (200, `pairs: 0`).

**e2e, `humo.spec.js`**, test `Operadores muestra si repites o cambias
de operador` junto a los de Operadores. Calculado con `seed_demo` en una
base temporal (el seed rota operador cada ronda, gana todo el ataque y
pierde toda la defensa): 145 pares, todos `switch`; Ataque tras ganar
87 (winrate 100%), Defensa tras perder 58 (winrate 0%), ninguna fila de
"Ataque · Tras perder" ni "Defensa · Tras ganar"; con `?operator=Ash`,
Ataque tras ganar 29. Afirmar: sin filtros, 4 filas (Total tras perder 58,
Total tras ganar 87, Ataque tras ganar 87, Defensa tras perder 58); la de
Ataque/Tras ganar dice 0 en Repite y 87 en Cambia; con
`/operadores?side=Defense` una sola fila; consola limpia. Si el Dev
cambia la regla de corte, recalcular con `seed_demo` en base temporal
(`SQLITE_PATH=<tmp> manage.py migrate && seed_demo`).

**`docs/metricas.md`**, tabla de `## Cortes`, fila "**Repetir o cambiar
de operador**" despues de "Operador por sitio": pares de rondas tuyas
consecutivas del mismo lado en la misma partida (por numero, saltando las
del otro lado; cortado por un numero faltante, una ronda sin lado o un
operador vacio o `Unknown(...)`), separados por el resultado de la
primera (sin ganador no abre par); *repite* si la segunda es con el mismo
operador; winrate de la segunda sobre las que tienen ganador. Mapa, tipo,
modo, fechas y sesion aplican; el lado elige el bloque; el operador elige
la primera ronda. Muestra minima 12 pares por caso
(`OPERADOR_TRAS_RESULTADO_MIN_RONDAS`): se avisa "pocas rondas", no se
oculta. Y la fila en `## Muestra minima`.

**Orden.** aggregates + tests backend, vista + url,
`operadorTrasResultado.js` + vitest, `Operators.jsx`, e2e,
`metricas.md`, `npm run build`.

**Que puede romperse.** `Filters` de Operadores va con
`showOperator={false}`: el filtro de operador solo llega por la URL o por
el filtro global de otra pagina; el hint lo explica y no se cambia el
selector. Un `is_me` duplicado en la misma ronda repetiria el numero y
cortaria el par (no pasa en datos reales: una fila tuya por ronda).

**Archivos ocupados.** La 102 (`revisado`) toca `aggregates.py`,
`views.py`, `urls.py`, `Operators.jsx`, `humo.spec.js` y
`metricas.md`; la 107 (`implementado`) los mismos menos `Operators.jsx`;
la 79 `aggregates.py`, `views.py` y `urls.py`. Todas agregan funciones
nuevas en lugares distintos y la 113 tambien (panel al final de
Operadores, despues de `PorSitio`; funcion despues de
`operator_by_site`; url despues de `operators/sites/`, donde la 102 pone
`operators/pool/`: el Dev que llegue segundo resuelve una linea). No se
frena, como no se frenaron la 98, la 100, la 103 ni la 107.

**Verificacion manual.** `seed_demo`, `/operadores`: panel con 4 filas;
`?side=Defense` solo Defensa; `?operator=Ash` 29 en Ataque tras ganar;
base vacia: la pagina muestra el EmptyState de siempre.

Skills: no aplica (tabla en una pagina existente; el repo ya lo resuelve con `PorSitio`).
OMC: plan=— · revisión=— · verificación=—

## Implementacion

(dev 20261112T2004Z-cbaTGDt) Diseno completo:

- `aggregates.py`, despues de `operator_pool` (la 102 ya esta en dev):
  `OPERADOR_TRAS_RESULTADO_MIN_RONDAS = 12`, `OPERADOR_TRAS_RESULTADO`,
  `OPERADOR_TRAS_RESULTADO_CASOS` y `operator_after_result(**filters)`: una
  consulta ordenada por partida y numero, recorrida con `.iterator()` y un
  pendiente por lado. Helper `_bloque_tras_resultado` con nombre propio para
  no chocar con `_caso_vacio`/`_sumar_caso` de la 107 cuando entre.
- Vista `operators_after_result` + url `operators/after-result/` (despues de
  `operators/pool/`).
- `operadorTrasResultado.js` (`hayPares`, `filasTrasResultado`,
  `textoWinrate`, `winrateCsv`) + vitest (7). Panel `TrasResultado` al final
  de `Operators.jsx`, despues de `PorSitio`; `DataTable` con
  `initialSort={{ key: 'orden', dir: 'asc' }}` sobre un campo `orden` de las
  filas, asi la tabla arranca en el orden Total, Ataque, Defensa y sigue
  siendo ordenable.
- e2e `Operadores muestra si repites o cambias de operador`: 4 filas con los
  numeros del diseno (58/87, recalculados con `seed_demo` en base temporal:
  145 pares, `?operator=Ash` 29), `?side=Defense` una fila, consola limpia.
- Filas en `docs/metricas.md` (`## Cortes` y `## Muestra minima`).

Desvios del diseno:
- **`site` tambien elige la primera ronda** (el diseno no lo nombraba y lo
  dejaba en `base_queryset`): filtrar las filas por sitio abria huecos de
  numero y solo quedaban pares de dos rondas seguidas en ese sitio. Mismo
  criterio que la 107 (el sitio mira la ronda perdida). Test
  `test_el_filtro_de_sitio_elige_la_primera_ronda`; hint y `metricas.md` lo
  dicen.
- El CSV de los winrates sale con coma decimal (`winrateCsv`), no con el
  numero crudo: la revision de la 107 encontro que un `csv:` propio se salta
  la coma de `celdaCsv`.
- `textoWinrate` vive en `operadorTrasResultado.js`: la 107 no esta en dev.
  Cuando entre, se puede unificar con `repetirSitio.js`.

Tests backend (`tests/test_operador_tras_resultado.py`, 18): los 15 del
diseno mas `test_el_filtro_de_sitio_elige_la_primera_ronda`,
`test_el_filtro_de_tipo_de_partida_aplica` y
`test_una_ronda_sin_lado_corta_el_par` (de la revision ciega).

Criterios -> tests: repeat/switch (`test_perder_con_ash_y_volver_a_ash_cuenta_repeat`,
`test_pasar_a_thermite_cuenta_switch`, `test_tras_ganar_va_a_after_win`,
`test_total_suma_los_dos_lados`); cortes (`test_una_ronda_faltante_entre_medio_corta_el_par`,
`test_operador_vacio_o_unknown_corta_el_par`, `test_los_pares_no_cruzan_partidas`,
`test_los_pares_no_cruzan_lados`); sin ganador (`test_primera_sin_ganador_no_abre_par`,
`test_segunda_sin_ganador_cuenta_en_rondas_y_no_en_winrate`); filtros
(`test_el_filtro_de_operador_elige_la_primera_ronda`, `test_el_filtro_de_lado_se_ignora`,
`test_el_filtro_de_mapa_aplica`, `test_el_filtro_de_tipo_de_partida_aplica`); UI
(vitest de `pocas rondas` y e2e); vacio (`test_sin_pares_responde_vacio_sin_error`);
metricas (filas nuevas).

Skills: no aplica (el repo ya lo resuelve con `PorSitio`).
OMC: plan=— · revisión=2 hallazgos LOW (2 arreglados) · verificación=—

## Revision 2026-11-13 sobre 4a8ec36

(revisor 20261113T0003Z-cVnayJ8) Rama fusionada con `origin/dev` (entraron #109 y #110, sin
conflictos). Partida de verde: verificar.sh VERDE 4a8ec36 (1181 backend, 336
vitest, 95 e2e). Una primera corrida dio rojo en
`e2e/accesibilidad.spec.js:226` ("los graficos dicen ...", punteadas
`[false, false]`) con dos subagentes corriendo `seed_demo` a la vez; con
`--de-nuevo` y la maquina libre, verde. Es de #109, ya en dev, y no toca
Operadores: anotado en `ESTADO.md`. Revision a ciegas en dos ejes
(estandares e intencion, `omc-code-reviewer` cada uno); cada hallazgo
confirmado por el lider.

Reglas: endpoint `@require_GET`, sin dependencias, sin `pydissect/` ni
Electron, agrega columnas existentes (lado, operador, ganador), filas en
`metricas.md` (Cortes y Muestra minima), e2e por Operadores, sin tildes en
identificadores y con tildes en la UI, sin `print` ni `console.log`.
Criterios: los seis cubiertos (los dos revisores corrieron `seed_demo`
aparte y reprodujeron los numeros del e2e: 145 pares, 58 cambia tras perder
0 %, 87 cambia tras ganar 100 %, `operator=Ash` 29).

Hallazgos (ninguno CRITICAL ni HIGH):

- [test] MEDIUM `backend/tests/test_operador_tras_resultado.py:99` -> **cerrado con test**
  Que pasa: `test_el_filtro_de_operador_elige_la_primera_ronda` pasa igual si
  el filtro de operador mirara la segunda ronda (Ash->Thermite y
  Thermite->Ash caen los dos en `after_loss/switch`).
  Por que es cierto: mutacion (filtro movido a la segunda ronda) deja ese test
  en verde. Agregado `test_el_filtro_de_operador_no_mira_la_segunda_ronda`
  (Ash ganada->Thermite, Thermite perdida->Ash, `operator=Ash`:
  `after_win/switch=1`, `after_loss/switch=0`): pasa con el codigo y cae con
  la mutacion.
- [estilo] LOW `backend/replays/analytics/aggregates.py:849` y `:896`
  Que pasa: la celda y su suma a mano duplican `_caso_vacio()` y
  `_sumar_caso()` de la 107, y `OPERADOR_TRAS_RESULTADO_CASOS` repite
  `REPETIR_SITIO_CASOS`. Arreglo sugerido: usar los helpers.
- [bug] LOW `frontend/src/operadorTrasResultado.js:58` (`winrateCsv`)
  Que pasa: repite lo que `celdaCsv` ya hace desde #109 (coma decimal y `''`
  para `null`). Arreglo sugerido: quitar `csv:` de la columna y `winrateCsv`.
- [intencion] LOW `frontend/src/operadorTrasResultado.js:51`
  Que pasa: "pocas rondas" se mide sobre `rounds` y el winrate sobre
  `decided`; fiel a la letra de la ficha y de `metricas.md`. Sin cambio.
- [estilo] LOW `frontend/src/pages/Operators.jsx:548`: el `?? 12` del hint
  copia la constante del backend mientras `data` no cargo. Sin efecto en datos.

Con el test nuevo: verificar.sh VERDE f30df34 (1182 backend, 336 vitest, 95 e2e).

Veredicto: aprobar -> `revisado`. Los LOW quedan para pulir; no frenan.

Skills: no aplica.
OMC: plan=— · revisión=5 hallazgos (1 MEDIUM cerrado con test; 4 LOW sin arreglar) · verificación=—

## QA

## Para el humano

(nada)
