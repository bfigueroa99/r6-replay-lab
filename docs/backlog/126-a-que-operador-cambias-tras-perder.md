# 126. A qué operador cambias tras perder

estado: implementado
candado: -
rama: claude/equipo-dev/126-a-que-operador-cambias-tras-perder
tipo: funcionalidad
epica: operadores
area: fullstack
prioridad: 3
fuente: ALCANCE.md O13 (Fuera de alcance de la ficha 113)
archivos: backend/replays/analytics/aggregates.py (operator_after_result, OPERADOR_CAMBIO_MIN_RONDAS), backend/tests/test_operador_tras_resultado.py, frontend/src/operadorTrasResultado.js (filasCambioTrasPerder), frontend/src/operadorTrasResultado.test.js, frontend/src/pages/Operators.jsx (TrasResultado), frontend/e2e/humo.spec.js, docs/metricas.md
turnos: po 20261113T1643Z-c4P1LiD, arquitecto 20261113T1802Z-c8dAf7p, dev 20261113T1830Z-cTivbSq

## PR

## Que gana quien usa la app

El panel "Repetir o cambiar tras perder" de Operadores (ficha 113) dice si
cambiar de operador despues de una ronda perdida te sirve; esto dice a cual:
por operador con el que perdiste y lado, a que operadores cambias en tu
siguiente ronda del mismo lado y que winrate tiene esa ronda con cada uno.
Responde "cuando pierdo con Ash, ¿me va mejor yendo a Thermite o a Sledge?".

## Criterios de aceptacion

- [ ] `/api/operators/after-result/` (o una clave nueva de la misma
      respuesta) devuelve filas `from_operator`, `side`, `to_operator`,
      `rounds`, `won`, `winrate` con los mismos pares que el caso
      `switch` de `after_loss` de la 113 (misma partida, mismo lado,
      sin hueco de numeracion, sin operador vacio). Test con rondas armadas:
      pierdes con Ash, cambias dos veces a Thermite (ganas una) y una a
      Sledge (pierdes) -> Ash->Thermite 2 rondas 50 %, Ash->Sledge 1 ronda 0 %.
- [ ] La suma de `rounds` de las filas de un lado es igual al `rounds` de
      `after_loss.switch` de ese lado con los mismos filtros. Test.
- [ ] Los filtros globales aplican como en la 113 (`operator` elige la
      primera ronda del par: con `?operator=Ash` solo salen filas desde
      Ash). Test.
- [ ] Se ve en Operadores debajo del panel de la 113, con el aviso de muestra
      de la pagina (se avisa, no se oculta); sin cambios tras perder, un
      texto y no un error. El e2e de humo pasa por Operadores con la consola
      limpia.
- [ ] Fila nueva en `docs/metricas.md` ("A qué operador cambias tras perder").

## Fuera de alcance

- Lo mismo tras ganar (la base de la 113 ya lo cubre en agregado).
- Recomendar a que operador cambiar: se muestran los numeros, no un consejo.
- El mismo corte para el spawn (S3).

## Diseno

(arquitecto 20261113T1802Z-c8dAf7p, sobre `origin/dev@1de3c54`) Filtros
duros: pasa (operador y resultado por ronda, ya en `RoundPlayer` y
`Round`; sin red, sin dependencias, sin POST, sin migracion). Una forma
obvia, ~250 lineas: sin arena ni consenso. Sale del mismo bucle de la 113,
asi que los pares son exactamente los de `after_loss.switch` por
construccion.

**Backend, `backend/replays/analytics/aggregates.py`, `operator_after_result`.**
- Dentro del `if previa is not None:`, cuando `tras == "after_loss"` y
  `caso == "switch"`, sumar tambien a un `dict` `cambios[(lado, op_previo, op)]`
  con `{"rounds", "decided", "won"}`, con las mismas reglas que `celda`
  (una segunda sin ganador suma a `rounds`, no a `decided`).
- La respuesta suma la clave `"switches"`: lista de filas
  `{"side", "from_operator", "to_operator", "rounds", "decided", "won",
  "winrate"}` (`winrate = _pct(won, decided)`), ordenada por `side`
  (Attack antes que Defense), `from_operator`, `-rounds`, `to_operator`.
  Sin el lado: el filtro `side` no recorta el queryset (lo dice el docstring
  de la 113); la UI filtra, como en el panel de la 113.
- Constante `OPERADOR_CAMBIO_MIN_RONDAS = 5` junto a
  `OPERADOR_TRAS_RESULTADO_MIN_RONDAS`, y la respuesta la manda como
  `"switch_min_rounds"`. Por que 5 y no 12: cada fila es un par de
  operadores, una celda mucho mas fina que "cambia / repite"; con 12 casi
  todas saldrian "pocas rondas" y la tabla no diria nada. Con menos de 5
  el winrate de un par es casi ruido puro (una ronda mueve 20 puntos): se
  avisa, no se oculta. Umbral sin calibrar con una base real (abajo).
- `views.operators_after_result` no cambia: ya devuelve todo el dict.

**Tests, `backend/tests/test_operador_tras_resultado.py`**, clase nueva
`AQueOperadorCambiasTests` con el `_partida` de la clase vecina (copiarlo
o subirlo a una funcion del modulo):
- `test_ash_a_thermite_y_a_sledge`: el caso del criterio 1 (perder con Ash
  y cambiar dos veces a Thermite, una ganada, y una a Sledge, perdida) ->
  filas Ash->Thermite 2 rondas 50.0, Ash->Sledge 1 ronda 0.0, las dos en
  Attack, en ese orden.
- `test_la_suma_de_las_filas_es_el_switch_de_la_113`: historial con los dos
  lados, repeticiones, victorias y un hueco; por lado, la suma de `rounds`
  de `switches` == `sides[lado]["after_loss"]["switch"]["rounds"]`, y lo
  mismo con `decided` y `won`.
- `test_repetir_o_cambiar_tras_ganar_no_entra`: Ash gana y cambia a
  Thermite -> `switches` vacio.
- `test_el_filtro_de_operador_elige_desde_donde`: pares desde Ash y desde
  Jager; con `operator="Ash"` solo filas con `from_operator == "Ash"`.
- `test_una_segunda_sin_ganador_no_entra_al_winrate`: la ronda siguiente con
  `won=None` -> `rounds` 1, `decided` 0, `winrate` None.
- `test_la_api_trae_switches`: `self.client.get(URL)` con base vacia ->
  `switches == []` y `switch_min_rounds == 5`.

**Frontend.**
- `frontend/src/operadorTrasResultado.js` (logica pura, ya de la 113):
  `filasCambioTrasPerder(data, lado)` -> `[]` sin `data?.switches`; si
  `lado` es Attack o Defense, solo ese lado; cada fila `{clave:
  "<side>-<from>-<to>", lado: "Ataque"|"Defensa", desde, hacia, rondas,
  winrate, poca: rondas < data.switch_min_rounds}`. `textoWinrate` y
  `winrateCsv` ya existen y se reusan.
- `frontend/src/operadorTrasResultado.test.js`: `filasCambioTrasPerder`
  con los dos lados, con `lado='Defense'`, sin `switches` (`[]`) y la marca
  `poca` con 4 y 5 rondas.
- `frontend/src/pages/Operators.jsx`, componente `TrasResultado` (misma
  request, sin otra llamada): debajo de la tabla de la 113, dentro del
  mismo `Panel`, un `<h3>` "A qué operador cambias tras perder" y una
  `DataTable` con columnas Lado, Perdiste con, Cambiaste a, Rondas,
  Winrate (con `textoWinrate(winrate, poca)`; `csv` con `winrateCsv`),
  `initialSort` por `rondas` desc, `csvName="operador-cambio-tras-perder"`.
  Sin filas: `<p className="note">No cambiaste de operador tras perder con
  estos filtros.</p>`. El `hint` del panel suma una frase: "Abajo, a qué
  operador cambiaste y cómo te fue con cada uno; con menos de 5 rondas por
  par se avisa «pocas rondas»."
- Muestra: el `5` del texto sale de `data.switch_min_rounds`, no escrito a
  mano.

**e2e, `frontend/e2e/humo.spec.js`**: el test de humo de Operadores que hoy
busca el heading "Repetir o cambiar tras perder" (linea ~160) suma
`getByRole('heading', { name: 'A qué operador cambias tras perder' })`
visible; si `seed_demo` da `switches` (leer `/api/operators/after-result/`),
la primera fila de la tabla muestra el `from_operator` de la API; si no, la
nota. Consola limpia.

**`docs/metricas.md`**: fila nueva despues de "Repetir o cambiar de
operador":
`| **A qué operador cambias tras perder** | Debajo del panel Repetir o cambiar tras perder (clave `switches` de `/api/operators/after-result/`). Los pares *Tras perder · Cambia* de esa fila, partidos por operador de la primera ronda (*Perdiste con*), operador de la segunda (*Cambiaste a*) y lado. Winrate de la segunda sobre las que tienen ganador. Por lado, la suma de las filas es el *Cambia* de *Tras perder*. Mismos filtros que el panel. Muestra minima 5 rondas por par (`OPERADOR_CAMBIO_MIN_RONDAS`): se avisa *pocas rondas*, no se oculta. |`
y en `## Muestra minima`: `| A qué operador cambias tras perder | 5 rondas por par (`OPERADOR_CAMBIO_MIN_RONDAS`): no se oculta, se avisa |`.

**Orden.** Tests backend (rojo) -> `cambios` en el bucle y `switches` ->
vitest -> `filasCambioTrasPerder` -> tabla en `Operators.jsx` -> e2e ->
`metricas.md` -> `npm run build` -> `verificar.sh`.

**Que puede romperse.** La clave es aditiva: el panel de la 113 y su CSV no
cambian. Las tuplas del bucle no se tocan; solo se suma un contador en la
rama `after_loss`/`switch`. Un operador `Unknown(...)` ya corta el par antes
de llegar ahi.

**Archivos ocupados.** Ramas abiertas (79, 119, 120, 121): ninguna toca
`operator_after_result`, `test_operador_tras_resultado.py`,
`operadorTrasResultado.js` ni `Operators.jsx`; `humo.spec.js` y
`metricas.md` los tocan en otras zonas. No se frena.

**Verificacion manual.** `seed_demo`, `runserver`, `curl -s
localhost:8000/api/operators/after-result/ | python -m json.tool` y mirar
`switches`; `/operadores`: la tabla nueva debajo del panel; con
`?side=Defense` solo filas de defensa; con `?operator=<op>` solo filas desde
ese operador; "Descargar CSV" con coma decimal.

Skills: no aplica (una tabla mas sobre un dato que ya se calcula).
Skills del repo: statistical-analysis (winrate con su `n` y `decided` aparte; umbral 5 por par justificado y avisado, no oculto; suma de las filas == el agregado de la 113 como invariante testeado), testing-strategy (Django para el desglose y el invariante, vitest para las filas y el filtro de lado, humo e2e para el render).
OMC: plan=— · revisión=— · verificación=—

## Implementacion

Dev 20261113T1830Z-cTivbSq, sobre `origin/dev@ed7bb52`. Diseno completo.

- `aggregates.py`: `OPERADOR_CAMBIO_MIN_RONDAS = 5`; en el bucle de
  `operator_after_result`, el caso `after_loss`/`switch` suma ademas a
  `cambios[(lado, op_previo, op)]` con las mismas reglas que la celda; la
  respuesta suma `switches` (ordenadas por lado, desde, -rondas, hacia) y
  `switch_min_rounds`. La vista no cambia.
- Tests (`test_operador_tras_resultado.py`): `_partida` sube a un mixin
  `_ConPartidas` que comparten las dos clases; `AQueOperadorCambiasTests` con
  los seis del diseno mas `test_repetir_tras_perder_no_entra` y
  `test_las_filas_van_por_lado_operador_y_rondas`. Vistos en rojo (8 errores,
  `KeyError: 'switches'`) antes del codigo.
- `operadorTrasResultado.js`: `filasCambioTrasPerder(data, lado)`; 4 vitest
  (vistos en rojo: "not a function").
- `Operators.jsx`: `<h3>` y `DataTable` debajo de la tabla de la 113 dentro
  del mismo `Panel`, misma request; nota sin filas; el `hint` suma la frase
  con el `5` de `switch_min_rounds`. No se muestra mientras carga ni con error.
- e2e: el test de la 113 acota sus filas a la primera tabla del panel (la
  nueva vive en el mismo `section`); test nuevo `Operadores muestra a qué
  operador cambias tras perder` (heading, filas = `switches`, primera fila =
  par de mas rondas de la API, suma = Cambia de defensa, `?side=Attack` da la
  nota, consola limpia).
- `metricas.md`: fila y muestra minima.

Desvios: dos tests backend extra (repetir tras perder no entra; orden de las
filas). Con `pairs == 0` el panel muestra las dos notas seguidas (correcto,
algo redundante; anotado por la revision ciega, sin cambio).

Revision ciega (`omc-code-reviewer`, `revision.md`, eje de estandares):
aprobar, sin hallazgos.

Verificacion: `verificar.sh` VERDE 5563bae26 (1247 tests backend, 392 vitest, 106 e2e).

Skills del repo: statistical-analysis (winrate sobre `decided` con `rondas`
a la vista, umbral avisado, invariante suma == Cambia testeado en Django y en
el e2e), testing-strategy (Django, vitest, e2e). modern-web-guidance:
busque `responsive-table` y `accessibility`; ninguna se aplico porque la
tabla reusa `DataTable` y `Panel` de `ui.jsx`. ux-copy: nota vacia y
encabezados en el tono de la pagina ("No cambiaste de operador tras perder
con estos filtros.").
Skills: ninguna de afuera.
OMC: plan=— · revisión=0 hallazgos · verificación=—

## Revision

## QA

## Para el humano

- (arquitecto 2026-11-13, no bloquea) El umbral de 5 rondas por par (`OPERADOR_CAMBIO_MIN_RONDAS`) se fijo sin una base real: calibrar con la tuya (cuantos pares pasan de 5).
