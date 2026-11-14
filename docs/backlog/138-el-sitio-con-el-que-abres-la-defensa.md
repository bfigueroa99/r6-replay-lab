# 138. El sitio con el que abres la defensa

estado: disenado
candado: -
rama: -
tipo: funcionalidad
epica: posicionamiento
area: fullstack
prioridad: 3
fuente: ALCANCE.md S7
archivos: backend/replays/analytics/aggregates.py, backend/replays/views.py, backend/replays/urls.py, backend/tests/test_apertura_defensa.py, frontend/src/aperturaDefensa.js, frontend/src/aperturaDefensa.test.js, frontend/src/pages/Coach.jsx, frontend/e2e/humo.spec.js, docs/metricas.md
turnos: po 20261113T2157Z-cG2vDSe, arquitecto 20261114T0040Z-c3LsMAo

## PR

## Que gana quien usa la app

En el Coach, por mapa, que sitio defiende tu equipo en la primera ronda de
defensa de cada partida, cuantas veces y con que winrate esa ronda, contra el
winrate de ese sitio en el resto de tus rondas de defensa: si tu apertura en
defensa es predecible y si arrancar ahi te cuesta.

## Criterios de aceptacion

- [ ] Agregado nuevo: primera ronda de defensa = la de menor `Round.number`
      con `my_side="Defense"` de la partida, leida de la partida entera (como
      `_primera_ronda`); si falta una ronda antes (hueco de numeracion desde
      la primera ronda de la partida) o no tiene sitio, la partida no entra.
      Por mapa (con su version) y sitio: `opens` (partidas que abrieron
      ahi), `opens_decided`, `opens_winrate`, y `rest_rounds`,
      `rest_winrate` del mismo sitio en las demas rondas de defensa. Test con
      tres partidas y un hueco.
- [ ] Una ronda sin ganador cuenta en las rondas y no en el winrate. Test.
- [ ] Filtros globales de partida (mapa, tipo, modo, fechas, sesion) aplican;
      lado y operador no (es siempre defensa y del equipo), como "Repetir el
      sitio tras perderlo". Test con filtro de mapa.
- [ ] Se ve en el Coach, junto a "Repetir el sitio tras perderlo", con aviso
      de muestra (se avisa, no se oculta) y una nota sin datos; e2e sobre
      `seed_demo` con los numeros de la API y consola limpia.
- [ ] Fila nueva en `docs/metricas.md`.

## Fuera de alcance

- El sitio con el que abres tras el cambio de lado o en prorroga.
- Recomendar un sitio.

## Diseno

(arquitecto 20261114T0040Z-c3LsMAo, sobre dev f34baba) Filtros duros: pasa (sitio de bomba y
lado de `Round`, que el `.rec` entrega; sin red, sin dependencias, sin POST,
sin migracion, sin `recompute`). Una sola forma obvia, con precedente
`site_after_loss`: sin arena ni consenso.

**Regla** (va tal cual a `metricas.md`). Se leen tus filas de la partida
(`base_queryset` sin `side`, `site` ni `operator`, ordenadas por
`round__match_id, round__number`), como `site_after_loss`. Por partida, la
**apertura de defensa** es tu primera fila con `side == "Defense"`, siempre
que: tu primera fila de la partida sea la ronda mas baja de la partida
(`Round.number` minimo de `Round` de esa partida, no solo de tus filas: si
falta tu fila de la ronda 0 no se sabe si la defensa empezo antes); los
numeros sean consecutivos desde ahi hasta la apertura (un hueco = ronda sin
`.rec` o sin fila tuya); ninguna fila antes tenga `side` vacio; y la apertura
tenga `round__site`. Si algo falla, la partida no aporta apertura (sus otras
rondas de defensa si entran al resto). El **resto** son todas tus demas
rondas de defensa con sitio de las partidas filtradas, aperturas excluidas.
Por (mapa con version, sitio): `opens`, `opens_decided`, `opens_won`,
`opens_winrate`, `rest_rounds`, `rest_decided`, `rest_winrate`, y
`opens_share` = `opens` / aperturas del mapa (que tan predecible es: 100 =
siempre abris ahi). Una ronda sin ganador (`my_team_won` nulo) cuenta en
`opens`/`rest_rounds` y no en el winrate. Mapa, tipo, modo, fechas y sesion
aplican; lado, operador y sitio no (la fila es de la defensa y del equipo; el
filtro de sitio partiria la comparacion contra el resto). Prorroga: no se
excluye; la apertura de defensa nunca cae en prorroga porque la defensa
empieza en la ronda 0 o 1 de tiempo regular.

**Archivos:**
- `backend/replays/analytics/aggregates.py`: debajo de `site_after_loss`,
  `APERTURA_DEFENSA_MIN_PARTIDAS = 5` y `defense_opener(**filters) -> dict`.
  Dos consultas fijas: tus filas (`values_list` de match_id, number, side,
  site, my_team_won y `*_MAPA`) y `Round.objects.values("match_id")
  .annotate(Min("number"))` filtrado a los match_id de las filas (o sin
  filtro: el `dict` es chico). Un solo recorrido. Devuelve
  `{"min_matches", "matches" (partidas con apertura), "skipped" (partidas
  con rondas de defensa que no aportan apertura), "maps": [{map, slug,
  map_id, "opens_total", "sites": [fila por sitio]}]}`, mapas por
  `opens_total` desc y sitios por `opens` desc, despues `rest_rounds` desc,
  despues nombre; un sitio con 0 aperturas y rondas en el resto tambien sale
  (con `opens 0`: es dato de que nunca abris ahi). `_etiquetar` para la
  version del mapa.
- `backend/replays/views.py` + `urls.py`: `GET
  /api/positioning/defense-opener/` -> `defense_opener(**_filters(request))`,
  al lado de `site-after-loss`.
- `backend/tests/test_apertura_defensa.py` (Django, `factories.py`): helper
  `_partida(index, lados_y_sitios, ganadas)` con `make_round(match, n,
  side=..., site=..., won=...)` + `make_round_player`. Tests:
  `test_tres_partidas_una_con_hueco_dan_dos_aperturas` (la del hueco entra
  al resto con su defensa y suma a `skipped`);
  `test_la_apertura_es_la_primera_defensa_aunque_arranques_en_ataque`;
  `test_sin_tu_fila_de_la_primera_ronda_no_hay_apertura` (`Round` 0 sin
  `RoundPlayer` tuyo);
  `test_una_ronda_sin_lado_antes_corta_la_apertura`;
  `test_una_apertura_sin_ganador_cuenta_y_no_entra_al_winrate`;
  `test_el_resto_es_el_mismo_sitio_sin_las_aperturas`;
  `test_el_porcentaje_de_aperturas_es_sobre_las_del_mapa`;
  `test_el_filtro_de_mapa_aplica_y_el_de_lado_no`;
  `test_consultas_constantes` (`assertNumQueries(2)` con 2 y con 6 partidas);
  `test_api_defense_opener_responde_con_filtros`.
- `frontend/src/aperturaDefensa.js` + `aperturaDefensa.test.js` (vitest):
  `hayAperturas(data)`, `filasAperturaDefensa(data)` (una fila por mapa y
  sitio, con `map` repetido y `poca: opens < min_matches`),
  `textoAperturas(n)` ("1 partida con apertura de defensa" / "N partidas
  ..."). Tests: sin datos; plural; marca `poca`; orden.
- `frontend/src/pages/Coach.jsx`: `PanelAperturaDefensa` justo debajo de
  `PanelRepetirSitio` (mismo patron: `useApi`, `ErrorBox`, `Loading`, nota
  sin datos). Titulo "El sitio con el que abres la defensa"; hint: "En cada
  partida, el sitio que tu equipo defendió en su primera ronda de defensa,
  cuántas veces y cuánto la ganó, contra ese mismo sitio en el resto de tus
  rondas de defensa. Lado, operador y sitio de la barra no aplican." Tabla:
  Mapa, Sitio, Abre (`opens` con `opens_share` en %), Winrate abriendo
  (con "pocas partidas" si `poca`, como `winrateConMuestra`), Resto (rondas),
  Winrate resto. Nota sin datos: "Con estos filtros no hay partidas con su
  primera ronda de defensa completa."
- `frontend/e2e/humo.spec.js`: test "Coach muestra el sitio con el que
  abres la defensa": panel por `section.panel` + heading; numeros contra
  `/api/positioning/defense-opener/` sobre `seed_demo` (ahi la ronda 1 es
  siempre defensa y perdida: `opens_winrate` 0 en todas las filas; el Dev
  confirma con el seed en una base temporal); consola limpia.
- `docs/metricas.md`: fila **El sitio con el que abres la defensa** debajo
  de **Repetir el sitio tras perderlo** (linea ~215) y su corte en la tabla
  de muestras minimas (linea ~429): "5 partidas por apertura
  (`APERTURA_DEFENSA_MIN_PARTIDAS`): no se oculta, se avisa".

**Numero (statistical-analysis):** winrate de ronda sobre decididas, con el
`n` (`opens`) a la vista; el porcentaje de aperturas es sobre las aperturas
del mapa, no sobre todas las partidas (un mapa poco jugado no diluye a otro).
Corte de 5 partidas para avisar (una apertura por partida: juntar 8 como
`site_after_loss` tarda mucho en un mapa); no hay delta ni veredicto contra
el resto: con 5 a 20 aperturas la diferencia es ruido casi siempre y un
veredicto engañaria. Umbral sin calibrar con datos reales: anotado abajo.

**Orden:** tests Django en rojo -> `defense_opener` -> vista/URL -> vitest
-> helper -> panel -> e2e -> `metricas.md` -> `npm run build`.

**Puede romperse:** el e2e del Coach que cuente paneles por posicion (ubicar
por heading); `Round.number` minimo cuando una partida tiene rondas
importadas sin fila tuya (es justo el caso que corta; test).

**Archivos ocupados:** `aggregates.py`, `views.py`, `urls.py`,
`humo.spec.js` y `metricas.md` los tocan 134, 135 y 79 con agregados
lejanos; `Coach.jsx` no lo toca ninguna rama abierta. No se frena.

**Verificacion manual:** `seed_demo` + `runserver`, Coach: el panel con una
fila por mapa y sitio, `Abre` sumando 100 % por mapa.

Skills: no aplica (panel con precedente `PanelRepetirSitio`).
Skills del repo: statistical-analysis (winrate sobre decididas, `n` a la vista, porcentaje sobre las aperturas del mapa, sin veredicto por ruido), testing-strategy (Django para la regla, vitest para el helper, e2e para el panel).
OMC: plan=— · revisión=— · verificación=—

## Implementacion

## Revision

## QA

## Para el humano

- Calibrar con la base real el corte de 5 partidas por apertura (`APERTURA_DEFENSA_MIN_PARTIDAS`), puesto solo con datos sinteticos.
