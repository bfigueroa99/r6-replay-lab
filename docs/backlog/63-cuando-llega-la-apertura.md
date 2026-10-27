# 63. Cuando llega la apertura

estado: revisado
candado: -
rama: claude/equipo-dev/63-cuando-llega-la-apertura
tipo: funcionalidad
epica: lado-y-marcador
area: fullstack
prioridad: 3
fuente: ALCANCE.md B14
archivos: backend/replays/analytics/aggregates.py, backend/replays/views.py, backend/tests/test_deaths.py, frontend/src/pages/Trends.jsx, frontend/e2e/humo.spec.js, docs/metricas.md
turnos: po 20261024T1204Z, arquitecto 20261024T1605Z, dev 20261027T0004Z, revisor 20261027T0404Z

## Que gana quien usa la app

El segundo de la fase de accion en que cae la primera baja de la ronda (sea
de quien sea) y tu winrate segun si llego temprano, al medio o tarde: si en
defensa te abren de entrada o si en ataque tardas en forzar el primer duelo.
Las aperturas de hoy dicen quien gana el primer duelo, no cuando llega.

## Criterios de aceptacion

- [ ] `/api/trends/` trae una clave nueva `opening_timing`: por lado
  (`attack`, `defense`), tres tramos fijos (temprano: menos de 30 s; medio:
  30 a 90 s; tarde: 90 s o mas; constantes en `aggregates.py`) mas una fila
  "Sin bajas", cada uno con `rounds`, `won`, `winrate` y
  `opening_won` (rondas en que la primera baja fue de tu equipo). La
  primera baja es el primer evento `Kill` o `Death` de la ronda por
  `order`, el mismo que define `opening_kill`/`opening_death` en
  `metrics.py`; su segundo es `Event.elapsed`. Test con rondas en 10 s,
  60 s y 120 s.
- [ ] Bordes: 29.9 s es temprano y 30 s es medio; 90 s es tarde (test).
- [ ] Rondas con `my_team_won` nulo no entran en `won` ni en `rounds`;
  rondas sin ningun evento de baja van a "Sin bajas" (test).
- [ ] Respeta los filtros de la barra; con `side=Attack` la parte de
  `defense` queda en cero; base vacia: 200 con los tramos en cero.
- [ ] Tendencias: tabla "Cuándo llega la apertura" (Lado, Tramo, Rondas,
  Winrate, Primera baja tuya %) con boton CSV `apertura-por-tiempo`; e2e
  sobre `seed_demo` que la encuentra.
- [ ] Fila nueva en `docs/metricas.md`.

## Fuera de alcance

- Por mapa: la ficha queda por lado; el corte por mapa es un tramo siguiente
  si la muestra da (anotarlo en ALCANCE si el Arquitecto lo ve).
- Cualquier cosa anclada al plant (`docs/formato-rec.md`).

## Diseno

(arquitecto 20261024T1605Z) Implementar despues de que #62 se mergee (mismo
panel vecino en `Trends.jsx` y misma seccion de `aggregates.py`; prioriza,
no bloquea). Una forma obvia, sin arena, sin migracion: una consulta sobre
tus `RoundPlayer` con dos anotaciones.

**Decision de definicion (reversible):** "primera baja tuya" se lee de
`RoundPlayer.opening_kill` de cualquier jugador de **tu equipo** en esa
ronda, no del autor del evento. Es exactamente lo que ya cuentan "Duelos de
apertura" y "winrate tras apertura" (lo escribe `metrics.py` desde el mismo
primer evento), asi que los numeros de las dos pantallas cuadran. El
segundo sale del `Event.elapsed` de ese mismo primer evento.

**Archivos y por que**

- `backend/replays/analytics/aggregates.py`, debajo de `death_timing`:
  - Constantes `APERTURA_TEMPRANA = 30` y `APERTURA_TARDIA = 90` con
    comentario del por que (30 es el tramo de "sales muy temprano"; 90 es
    la mitad de los 180 s de accion).
  - `_tramo_apertura(elapsed) -> str`: `None` -> `"sin_bajas"`, `< 30` ->
    `"temprano"`, `< 90` -> `"medio"`, resto `"tarde"`.
  - `opening_timing(**filters) -> dict`:
    `base_queryset(**filters).filter(round__my_team_won__isnull=False).annotate(t_apertura=Subquery(Event.objects.filter(kind__in=(Event.KILL, Event.DEATH), round_id=OuterRef("round_id")).order_by("order").values("elapsed")[:1]), apertura_mia=Exists(RoundPlayer.objects.filter(round_id=OuterRef("round_id"), team_index=OuterRef("team_index"), opening_kill=True))).values("side", "t_apertura", "apertura_mia", "round__my_team_won")`.
    Plegar en Python por `side` en `("Attack", "Defense")` (otros lados se
    ignoran) y tramo. Salida
    `{"attack": [fila x4], "defense": [fila x4]}`, siempre los 4 tramos en
    orden temprano, medio, tarde, sin bajas, cada fila con `key`, `label`
    ("Temprano (<30 s)", "Medio (30–90 s)", "Tarde (90 s o más)", "Sin
    bajas"), `rounds`, `won`, `winrate=_pct(won, rounds)`, `opening_won`
    (cuantas), `opening_won_pct=_pct(opening_won, rounds)`. En "Sin bajas"
    `opening_won` es 0 siempre. Con base vacia o `side=Attack`, el lado
    ausente sale con sus 4 filas en cero (`winrate: None`).
  - Docstring: las aperturas de hoy dicen quien gana el primer duelo; esto
    dice cuando llega.
- `backend/replays/views.py`, `trends`: `"opening_timing": agg.opening_timing(**filters)`.
- `backend/tests/test_deaths.py`: clase nueva `AperturaPorTiempoTests`.
  Tests:
  - `test_aperturas_a_los_10_60_y_120_caen_en_temprano_medio_y_tarde`
  - `test_29_9_es_temprano_30_es_medio_y_90_es_tarde`
  - `test_la_primera_baja_es_la_de_menor_order_no_la_de_menor_elapsed`
    (dos eventos con `order` y `elapsed` invertidos)
  - `test_una_ronda_sin_ganador_no_entra`
  - `test_una_ronda_sin_eventos_de_baja_va_a_sin_bajas`
  - `test_la_apertura_de_un_companero_cuenta_como_tuya` (opening_kill en
    otro `RoundPlayer` de tu `team_index`)
  - `test_con_side_attack_la_defensa_queda_en_cero`
  - `test_base_vacia_trae_los_tramos_en_cero_en_la_api` (`/api/trends/`
    200, 4 filas por lado, `rounds` 0)
- `frontend/src/pages/Trends.jsx`: `const apertura = data.opening_timing`;
  panel `title="Cuándo llega la apertura"` inmediatamente despues de
  "Cuando mueres" (deja juntos los tres paneles de tiempo), renderizado si
  alguna fila tiene `rounds > 0`. Una tabla aplanada: filas
  `[...attack.map(f => ({...f, side: 'Attack'})), ...defense.map(...)]`,
  columnas Lado (`SideChip`, csv en texto), Tramo (`left`), Rondas, Winrate
  (%), Primera baja tuya (`opening_won_pct`, %, con `help` "De esas rondas,
  en cuántas la primera baja la hizo tu equipo."), `sortable: false` en
  Lado y Tramo; `DataTable` sin `initialSort` ordena por la primera
  columna desc, asi que cada fila lleva `orden` (indice al aplanar, como
  `porSitio` en Teammates) e `initialSort={{ key: 'orden', dir: 'asc' }}`
  para conservar ataque y despues defensa, temprano/medio/tarde/sin bajas; `rowKey={(row) => `${row.side}-${row.key}`}`,
  `csvName="apertura-por-tiempo"`. Hint: "Segundo de la fase de acción en
  que cae la primera baja de la ronda, sea de quien sea. Si en defensa
  pierdes las que llegan temprano, te abren de entrada; si en ataque las
  tardías te cuestan, tardas en forzar el primer duelo."
- `frontend/e2e/humo.spec.js`: `test('Tendencias muestra cuando llega la
  apertura', ...)`: heading exacto "Cuándo llega la apertura", 8 filas en
  `tbody` (4 tramos x 2 lados con la base demo, que juega los dos lados),
  consola limpia. En `seed_demo` el evento de tu muerte se crea con `order`
  0 aunque tus bajas tengan menor `elapsed`: no afirmar a ojo que tramo
  gana, sacar los numeros corriendo el seed.
- `docs/metricas.md`, seccion `## Duelos de apertura`: fila **Cuándo llega
  la apertura** (en la doc sin tilde, como el resto): el segundo
  (`Event.elapsed`) del primer `Kill` o `Death` de la ronda por `order`;
  tramos temprano < 30 s, medio 30-90 s, tarde >= 90 s, y "Sin bajas";
  winrate de tus rondas en cada tramo por lado; "Primera baja tuya" = rondas
  donde algun jugador de tu equipo tiene `opening_kill`. Rondas sin ganador
  conocido afuera.

**Orden:** constantes + helper + funcion + tests, views, Trends.jsx,
build, e2e, metricas, `check.sh`.

**Que puede romperse:** `Event.elapsed = 0.0` en eventos sin reloj cae en
"temprano" (mismo criterio que 62 y que "Cuando mueres"); si al revisar la
base real del humano aparecen muchas aperturas en 0.0 exacto, es una ficha
aparte para tratarlas como "sin reloj". Los umbrales 30/90 no se calibraron
contra la base real: anotar en `## Revision 2026-10-27 sobre 093fffc

(revisor 20261027T0404Z) Revision ciega (subagente con `revision.md` sobre el diff sin
`docs/backlog`) y confirmacion del lider. `check.sh`: Todo en verde (788 tests
backend, 120 frontend, build, 50 e2e). `origin/main` ya estaba fusionado.

Criterios: cada uno cubierto por un test de `AperturaPorTiempoTests` (tramos
10/60/120, bordes 29.9/30/90, primera por `order`, sin ganador afuera, sin
bajas, companero, `side=Attack`, base vacia en la API) y el e2e
`Tendencias muestra cuando llega la apertura` (numeros confirmados corriendo
`seed_demo`: Ataque tarde 66 / 100 % / 13.6 %; Defensa medio 37 / 0 % / 0 %).
Fila en `metricas.md`; el diff no sale de `archivos:`; sin `print` ni
`console.log`; UI con tildes, identificadores sin. Sin doble conteo:
`base_queryset` deja una fila `is_me` por ronda.

Hallazgos (menores, no bloquean; van a `## Para el humano`):

- [bug menor] `aggregates.py` (`apertura_mia`): si la primera baja de la ronda
  es un teamkill de tu equipo, cuenta como "Primera baja tuya" (`metrics.py:216-220`
  marca `opening_kill` al autor aunque la victima sea aliada). Es el mismo
  criterio que ya usa *Duelos de apertura*, que el diseno pidio cuadrar.
  Arreglo posible: exigir ademas `~Exists(opening_death)` en tu equipo; mejor
  en `metrics.py` para que lo herede Duelos tambien (ficha aparte).
- [bug menor] `_tramo_apertura`: un primer evento sin reloj (`elapsed` 0.0)
  cae en *Temprano*; documentado en `metricas.md` y anotado por el diseno.

Veredicto: aprobar.

## Para el humano` del PR que se pueden
mover cambiando las dos constantes.

**Verificacion manual:** `/tendencias`, la tabla aparece debajo de "Cuando
mueres" con 8 filas; `curl -s 'localhost:8000/api/trends/?side=Attack'`
trae `defense` con `rounds: 0` en las 4 filas.

**Tramo siguiente (para ALCANCE.md, no se propone aca):** el mismo corte
por mapa, si la muestra da.

## Implementacion

(dev 20261027T0004Z) Diseno completo, sin migracion y sin desvios de alcance.

- `aggregates.py`: `APERTURA_TEMPRANA`/`APERTURA_TARDIA`, `_tramo_apertura` y
  `opening_timing` debajo de `death_timing`, con la consulta del diseno
  (Subquery del `elapsed` del primer `Kill`/`Death` por `order` + Exists de
  `opening_kill` en tu `team_index`), plegada en Python. `views.trends` la
  expone como `opening_timing`.
- Desvio menor (de la revision ciega): en "Sin bajas" `opening_won` es 0 como
  pide el diseno, pero `opening_won_pct` es `None` (la UI muestra `—`): un
  `0 %` ahi se leia como aperturas perdidas. Documentado en `metricas.md`.
- `test_deaths.py`: `AperturaPorTiempoTests`, los 8 tests del diseno con sus
  nombres. El de "sin bajas" fuerza `opening_kill` sin evento para cubrir el
  guard. La ronda sin ganador se arma poniendo `my_team_won = None` despues
  del factory (como en `test_clutch.py`): el factory no acepta `won=None`.
- `Trends.jsx`: panel "Cuándo llega la apertura" debajo de "Cuando mueres",
  8 filas aplanadas con `orden`, CSV `apertura-por-tiempo`; se muestra si
  alguna fila tiene rondas.
- e2e `Tendencias muestra cuando llega la apertura`: 8 filas y dos filas
  afirmadas con los numeros de `seed_demo` (Ataque tarde 66 / 100 % / 14 %;
  Defensa medio 37 / 0 % / 0 %). En la demo no hay aperturas antes de 30 s ni
  rondas sin bajas.
- `check.sh`: Todo en verde (788 tests backend, 120 frontend, build, 50 e2e).

## Para el humano

- Los cortes 30/90 s no se calibraron con la base real; se mueven cambiando
  `APERTURA_TEMPRANA` y `APERTURA_TARDIA` en `aggregates.py`.
- Un evento sin reloj (`elapsed` 0.0) cae en "Temprano", igual que en
  "Cuando mueres" y "Cuándo matas".
- Revisor 2026-10-27 (aviso, no bloquea): una apertura que es teamkill de tu
  equipo cuenta como "Primera baja tuya" (igual que en *Duelos de apertura*,
  donde ya pasaba). Corregirlo en `metrics.py` cambia un numero que ya se
  muestra: decilo en `## Para el equipo` si lo queres.
