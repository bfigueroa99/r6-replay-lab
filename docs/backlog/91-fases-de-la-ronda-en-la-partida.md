# 91. Fases de la ronda en el detalle de partida

estado: disenado
candado: -
rama: -
tipo: funcionalidad
epica: paridad-referencia
area: fullstack
prioridad: 3
fuente: R3 de ALCANCE.md; `replica/features.csv` "Analisis de ronda en fases early, mid y execute" (could, partial: los tramos existen entre partidas en Tendencias, no por partida); [aurelix](https://aurelix.app/blog/how-to-analyse-r6-siege-replays)
archivos: backend/replays/analytics/aggregates.py (fases_de_partida), backend/replays/views.py (match_detail), backend/tests/test_fases_de_la_ronda.py, frontend/e2e/partida-sin-rondas.json, frontend/src/fasesRonda.js, frontend/src/fasesRonda.test.js, frontend/src/pages/MatchDetail.jsx, frontend/e2e/humo.spec.js, docs/metricas.md
turnos: po 20261105T1759Z-cCJ5erc, arquitecto 20261105T1825Z-cVr9Dsg

## PR

(La escribe el Release manager al final.)

## Que gana quien usa la app

En el detalle de una partida, las bajas de cada equipo partidas en temprano,
medio y tarde de la ronda, y cuantas rondas gano cada equipo segun quien
saco mas bajas en cada fase: ver si esa partida se decidio en el primer
contacto o en el cierre. Hoy eso existe solo como agregado de tus bajas y
muertes en Tendencias, nunca para una partida y los dos equipos.

## Criterios de aceptacion

- [ ] `GET /api/matches/<id>/` trae `phases`: tres filas (temprano < 30 s
      jugados, medio de 30 a 120 s, tarde 120 s o mas, sobre `Event.elapsed`
      de los `Kill`) con las bajas de tu equipo y del rival en cada una,
      teamkills afuera (no cuentan para ningun equipo). Test con una partida
      armada a mano: una baja a los 29.9 s cae en temprano, una a 30.0 s en
      medio, una a 120.0 s en tarde.
- [ ] Cada fila trae tambien en cuantas rondas tu equipo saco mas bajas que el
      rival en esa fase y cuantas de esas rondas ganaste (`Round.my_team_won`;
      las rondas con resultado desconocido fuera del denominador). Test.
- [ ] Una baja cuyo autor no tiene fila en la ronda (equipo desconocido) no
      suma a ningun equipo ni rompe la respuesta (test).
- [ ] En `MatchDetail`, un panel "Fases de la ronda" con las tres filas;
      una partida sin bajas muestra el panel con ceros o un texto, nunca un
      error de consola. Caso en el e2e con un numero de `seed_demo`.
- [ ] Fila en `docs/metricas.md` con los cortes (los mismos tramos que
      el Arquitecto alinee con "Cuando matas" y "Cuando mueres" si conviene;
      si cambia los cortes, lo dice el diseno).

## Fuera de alcance

- La misma vista agregada entre partidas: ya esta en Tendencias.
- Fases por plant o post-plant: el formato no trae el plant en temporadas
  nuevas.
- Una timeline grafica nueva: la ronda ya tiene su timeline.

## Diseno

(arquitecto 20261105T1825Z-cVr9Dsg)

Una sola forma obvia, calcada de "Trades por equipo" (ficha 75): una funcion
pura que recorre las rondas ya armadas de `match_detail`, cero queries
nuevas, y un panel en `MatchDetail` con su logica en un modulo aparte. Sin
migracion, sin `recompute`, sin parser. Sin arena ni consenso.
Skills: no aplica (tabla de tres filas como `TradesPorEquipo`; ningun
dominio nuevo).

**Implementar despues de que #79 se mergee** (prioriza, no bloquea): la 79
toca `views.py` y `MatchDetail.jsx`. Las regiones son distintas (la 79 agrega
el boton de excluir en la cabecera y su POST), asi que si la 79 sigue
esperando al humano cuando el Dev llegue, se implementa igual sobre `dev` y
el que mergee segundo resuelve un conflicto de pocas lineas.

### Cortes

Temprano `0 < elapsed < 30`, medio `30 <= elapsed < 120`, tarde
`elapsed >= 120`, en segundos jugados de la fase de accion (`Event.elapsed`).
30 es el mismo corte de "Sales muy temprano" (`DEATH_BUCKET`) y de la
apertura temprana (`APERTURA_TEMPRANA`); 120 deja el ultimo minuto de los
180 s como "tarde" (la ejecucion). No se alinea con el 90 de
`APERTURA_TARDIA` a proposito: ese corte habla de cuando llega la primera
baja, no de en que fase de la ronda se pelea; se dice en `metricas.md`.
`elapsed == 0` es "sin reloj" (`metrics.py` linea ~287 lo escribe asi
cuando el feed no trae `timeInSeconds`): no entra a ninguna fase y se cuenta
aparte en `untimed_kills`, para que las tres filas mas eso cuadren con las
bajas del feed. Es el mismo criterio que la ficha 89.

### Archivos y por que

- `backend/replays/analytics/aggregates.py`: constantes `FASE_MEDIA = APERTURA_TEMPRANA`
  (30), `FASE_TARDIA = 120`, `FASES` (clave, etiqueta, inicio, fin) y la
  funcion pura `fases_de_partida(rondas, my_team_index) -> dict`, al lado de
  `opening_timing` (bloque de tiempos de la ronda). Pura y sobre dicts, como
  `rachas_de_rondas`, asi se prueba sin base.
- `backend/replays/views.py`: `match_detail` agrega
  `"phases": agg.fases_de_partida(rounds, match.my_team_index)` a la
  respuesta, despues de `team_trades`.
- `backend/tests/test_fases_de_la_ronda.py` (nuevo).
- `frontend/e2e/partida-sin-rondas.json`: suma la clave `phases` vacia (ver
  "Que puede romperse").
- `frontend/src/fasesRonda.js` + `frontend/src/fasesRonda.test.js` (nuevos):
  filas del panel y textos, como `tradesEquipo.js`.
- `frontend/src/pages/MatchDetail.jsx`: componente `FasesDeLaRonda` y su
  `Panel` despues de "Trades por equipo".
- `frontend/e2e/humo.spec.js`: un test nuevo junto a "el detalle de una
  partida muestra los trades por equipo" (linea ~370).
- `docs/metricas.md`: fila en `## Trades`, debajo de "Trades por equipo".

### Backend: `fases_de_partida(rondas, my_team_index)`

Por ronda (mismo criterio que `_trades_por_equipo` en `views.py`):
`yo = next(p for p in ronda["players"] if p["is_me"])`,
`mio = yo["team_index"] if yo else my_team_index`, y
`equipo = {p["username"]: p["team_index"] for p in ronda["players"]}` (el
feed nombra por nick, y dentro de una misma ronda el nick del feed y el de
la fila son el mismo; la matriz de duelos del frontend resuelve igual).

Por cada evento con `kind == "Kill"` (los `Death` sin autor no son bajas de
ningun equipo):

- `elapsed` falsy (0 o None) -> `untimed_kills += 1`, sigue.
- `a = equipo.get(actor)`, `t = equipo.get(target)`. `a is None` ->
  `unknown_team_kills += 1`, sigue (la baja no se le suma a nadie).
- `t is not None and a == t` -> teamkill o suicidio, `teamkills += 1`, sigue.
- Si no, suma a `mine` si `a == mio`, a `rival` si no, en la fase de su
  `elapsed`, y en un contador por ronda `(fase, lado)`.

Al cerrar cada ronda, por fase: si `mine > rival` en esa fase y
`ronda["my_team_won"] is not None` -> `rounds_ahead += 1` y
`rounds_ahead_won += my_team_won`; si `rival > mine` (y resultado conocido)
-> `rounds_behind += 1`, `rounds_behind_won += my_team_won`. Empates y
rondas sin bajas en la fase no cuentan en ninguno de los dos. Rondas con
resultado desconocido no suman a `rounds_*` pero sus bajas si a `mine`/`rival`.

Salida:

```python
{
    "rows": [
        {"key": "temprano", "label": "Temprano (<30 s)", "start": 0, "end": 30,
         "mine": 0, "rival": 0,
         "rounds_ahead": 0, "rounds_ahead_won": 0, "rounds_ahead_winrate": None,
         "rounds_behind": 0, "rounds_behind_won": 0, "rounds_behind_winrate": None},
        {"key": "medio", "label": "Medio (30–120 s)", "start": 30, "end": 120, ...},
        {"key": "tarde", "label": "Tarde (120 s o más)", "start": 120, "end": None, ...},
    ],
    "untimed_kills": 0,
    "unknown_team_kills": 0,
    "teamkills": 0,
}
```

`*_winrate` con `_pct` (None sin rondas). Siempre tres filas, tambien con
`rondas == []`. La ficha pedia "rondas ganadas cuando tu equipo saco mas";
`rounds_behind` es su espejo y cuesta dos lineas: deja ver "esta partida se
perdio en el cierre" sin otra ficha.

### Frontend

- `fasesRonda.js`: `filasDeFases(phases)` -> `[]` sin `phases` o sin
  `rows`; si no, una fila por fase con `label`, `mine`, `rival`, y los
  textos `ganadasAdelante` = `"{won} de {n}"` o `"—"` con `n == 0` (igual
  para `Behind`), y `mejor` (`'mine'`, `'rival'` o `null` en empate) para
  resaltar la celda de bajas como hace `tradesEquipo.js`.
  `notaDeFases(phases)`: `null` si todo cuadra; si `untimed_kills` o
  `unknown_team_kills` > 0, "N bajas sin reloj o de un jugador sin fila
  quedan fuera de las fases."; `hayBajas(phases)` = alguna fila con
  `mine + rival > 0`.
- `MatchDetail.jsx`: `<Panel title="Fases de la ronda" hint="Bajas de cada
  equipo según el momento de la ronda, y cómo terminaron las rondas en que
  un equipo dominó esa fase.">`. Tabla de columnas: Fase, Tu equipo, Rival,
  Rondas que dominaste (ganadas), Rondas que dominó el rival (ganadas). Sin
  bajas (`!hayBajas`): `<p className="note">Esta partida no tiene bajas con
  reloj entre equipos.</p>` en vez de la tabla. La partida sin rondas
  muestra ese mismo texto (su `phases` trae tres filas en cero).

### Tests nuevos (`backend/tests/test_fases_de_la_ronda.py`)

Con `make_match`, `make_round`, `make_round_player` (los dos equipos: tu
fila con `team_index` 0 y un rival con 1) y `make_event`. **Ojo**:
`make_event` toma `clock`, no `elapsed`, y calcula
`elapsed = rnd.clock_start - clock`; para 29.9 s jugados va
`clock=rnd.clock_start - 29.9`. Los tests llaman a `/api/matches/<id>/`.

- `test_los_cortes_de_las_fases_caen_donde_dicen` (29.9 temprano, 30.0
  medio, 119.9 medio, 120.0 tarde)
- `test_las_bajas_se_reparten_entre_tu_equipo_y_el_rival`
- `test_un_teamkill_no_suma_a_ningun_equipo`
- `test_una_baja_de_un_jugador_sin_fila_no_suma_ni_rompe`
- `test_una_baja_sin_reloj_queda_fuera_de_las_fases` (`elapsed == 0`)
- `test_rondas_dominadas_y_ganadas_por_fase` (dos rondas en que tu equipo
  saca mas temprano, una ganada y una perdida -> `rounds_ahead=2`,
  `rounds_ahead_won=1`, `rounds_ahead_winrate=50.0`)
- `test_una_ronda_sin_resultado_no_entra_al_denominador`
- `test_tu_equipo_se_lee_por_ronda` (tu `team_index` cambia de 0 a 1 en la
  segunda ronda: las bajas siguen a tu fila)
- `test_partida_sin_bajas_trae_tres_fases_en_cero`

Vitest `fasesRonda.test.js`: sin `phases` lista vacia; `"—"` con cero
rondas; `mejor` en empate es `null`; la nota aparece solo con bajas fuera de
fase.

### e2e

Test "el detalle de una partida muestra las fases de la ronda", como el de
trades: `/partidas`, primer enlace, panel por heading exacto "Fases de la
ronda", 3 filas, y cada celda de bajas igual a lo que trae
`/api/matches/<id>/` en `phases.rows`. Ademas un numero del seed afirmado:
`seed_demo` no tiene ninguna baja antes de 30 s (spike en el scratchpad:
272 bajas, 186 entre 30 y 120 s, 86 de 120 s o mas, ninguna en 0), asi que
la fila Temprano dice `0` y `0` en cualquier partida. No se toca el seed.
`expect(errores).toEqual([])`.

### Orden de implementacion

1. Tests de backend en rojo, constantes y `fases_de_partida`, clave en
   `match_detail`, `partida-sin-rondas.json`. 2. `fasesRonda.js` + vitest.
3. Panel. 4. e2e. 5. `metricas.md`. 6. `npm run build` y `check.sh`.

### Que puede romperse

- **`test_partida_sin_rondas.py` compara la respuesta entera** con
  `frontend/e2e/partida-sin-rondas.json`: agregar `phases` sin actualizar el
  JSON lo pone en rojo. El JSON suma `"phases"` con las tres filas en cero y
  los tres contadores en 0, exactamente como lo devuelve la funcion (el
  e2e "una partida sin rondas" usa ese mismo archivo como respuesta mockeada:
  el panel tiene que renderizar el texto sin errores con el).
- Comparte `aggregates.py`, `humo.spec.js` y `metricas.md` con la ficha 89
  (regiones distintas: bloque de tiempos contra bloque de posicion, un test
  de MatchDetail contra uno del Coach, filas en distinto lugar de
  `## Trades`); se pueden implementar en paralelo.
- `_trades_por_equipo` y esta funcion leen el equipo igual pero se escriben
  aparte; no se refactoriza la de trades en este tramo.
- Un nick repetido en los dos equipos de una ronda (no deberia pasar en el
  feed) haria que el dict se quede con el ultimo; queda dicho en el docstring.

### Verificacion manual

Abrir una partida real que se gano remontando y otra perdida: la suma de
Tu equipo + Rival de las tres filas, mas teamkills, sin reloj y sin fila,
tiene que dar el total de bajas del feed de la partida (las bajas de las
timelines de sus rondas).

### docs/metricas.md

En `## Trades`, debajo de "Trades por equipo": **Fases de la ronda** (detalle
de partida): bajas de cada equipo segun los segundos jugados de la fase de
accion (`Event.elapsed`): temprano `< 30`, medio `30–120`, tarde `>= 120`.
30 es el mismo corte de "Sales muy temprano"; 120 deja el ultimo minuto de
los 180 s como cierre. Teamkills, bajas sin reloj (`elapsed` en 0) y bajas
de un jugador sin fila en la ronda no van a ningun equipo. "Rondas que
dominaste": rondas con resultado conocido en que tu equipo saco mas bajas
que el rival en esa fase, y cuantas ganaste; "que dominó el rival", el
espejo; los empates no cuentan en ninguna. El equipo se lee ronda a ronda,
como en "Trades por equipo".

OMC: plan=— · revisión=— · verificación=—

## Implementacion

(Dev)
