# 123. Clutches de tus companeros

estado: implementado
candado: -
rama: claude/equipo-dev/123-clutches-de-tus-companeros
tipo: funcionalidad
epica: escuadra
area: backend
prioridad: 3
fuente: ALCANCE.md C15
archivos: backend/replays/analytics/aggregates.py (teammate_clutches, CLUTCH_COMPANERO_MIN), backend/replays/views.py (teammates), backend/tests/test_clutch_companeros.py (nuevo), frontend/src/clutchCompaneros.js (nuevo), frontend/src/clutchCompaneros.test.js (nuevo), frontend/src/pages/Teammates.jsx (panel Clutches), frontend/e2e/humo.spec.js, docs/metricas.md
turnos: po 20261113T1650Z-c9H2L8Y, arquitecto 20261113T1830Z-cTivbSq, dev 20261113T1858Z-cxQ3TuB

## PR

## Que gana quien usa la app

En Compañeros, una tabla nueva con cada compañero habitual: cuantas veces
quedo ultimo vivo de tu equipo en rondas contigo, contra cuantos y cuantas
convirtio, al lado de tu propia conversion. Saber a quien conviene dejarle
la ronda y quien la regala; hoy los clutches de esa pagina son solo tuyos.

## Criterios de aceptacion

- [ ] Funcion nueva en `replays/analytics/aggregates.py` (p. ej.
      `teammate_clutches`): por compañero (agrupado por `player_id`, como
      `teammate_synergy`, un cambio de nick no parte la fila) cuenta
      intentos (`clutch_vs > 0` en su fila, misma ronda y `team_index` que
      la tuya) y ganados (`Round.my_team_won`), con el mismo descarte que
      `clutch_conversion`: rondas con `my_team_won` nulo no cuentan. Test
      con dos compañeros y un intento ganado y uno perdido.
- [ ] Muestra minima por fila (habitual = el mismo corte de partidas
      compartidas de la ficha 54, o un minimo de intentos fijado en el
      diseno); los compañeros bajo el corte no salen. Test.
- [ ] Los filtros globales (mapa, lado, fechas) aplican igual que al resto
      de `/api/teammates/`; test con filtro de lado.
- [ ] `/api/teammates/` suma la clave nueva; la tabla en `Teammates.jsx`
      muestra intentos, ganados y % con su `n`, mas tu propia fila como
      referencia; e2e en `seed_demo` sin errores de consola (con datos o
      con el estado vacio si la semilla no da clutches de compañeros).
- [ ] Fila nueva en `docs/metricas.md` con la definicion (ultimo vivo con
      rivales vivos, mismo algoritmo que `clutch_vs`).

## Fuera de alcance

- Partir la tabla por cantidad de rivales (1v1, 1v2...) o por lado: se
  puede como tramo siguiente.
- Clutches de los rivales (D12).
- Señales del Coach sobre esto.

## Diseno

(arquitecto 20261113T1830Z-cTivbSq, sobre `origin/dev@ed7bb52`) Filtros
duros: pasa. `RoundPlayer.clutch_vs` ya se escribe al importar para **cada**
jugador de la ronda (`metrics.py:430`, `clutch_vs(events, team_of)` devuelve
un valor por nick), no solo para vos: no hace falta migracion ni `recompute`.
Sin red, sin dependencias, sin POST. Una forma obvia, ~300 lineas: sin arena
ni consenso.

**Muestra.** Dos cortes, los dos ya en uso en la pagina:
- Quien sale: los **habituales** (`MIN_PARTIDAS_HABITUAL = 5` partidas en tu
  equipo, sobre todo el historial y sin filtros, la regla de `by_stack`,
  ficha 54), y de ellos solo los que tienen al menos un intento con los
  filtros puestos. Un conocido de una noche no es "a quien dejarle la ronda".
- Que se avisa: `CLUTCH_COMPANERO_MIN = 5` intentos por fila; debajo, `*`
  "Menos de 5 intentos" como Clutch por mapa y sitio y por operador (sale
  igual: con 3 intentos el % no dice mucho, pero el `n` esta a la vista).

**Backend, `backend/replays/analytics/aggregates.py`**, funcion nueva
`teammate_clutches(**filters) -> dict`, despues de `clutch_by_operator` (zona
que no toca ninguna rama abierta):
- `CLUTCH_COMPANERO_MIN = 5` arriba de la funcion, con un comentario como los
  de `CLUTCH_SITIO_MIN`.
- Habituales: `player_id` con `Count("round__match_id", distinct=True) >=
  MIN_PARTIDAS_HABITUAL` sobre `RoundPlayer.objects.filter(is_me=False)
  .filter(Exists(mia))`, con `mia` la correlacionada sin filtros de `by_stack`
  (misma consulta; se copia en vez de extraer un helper de `by_stack` para no
  tocar esa funcion: un comentario lo dice).
- Intentos de compañeros: `RoundPlayer.objects.filter(is_me=False,
  player_id__in=<habituales>, clutch_vs__gt=0,
  round__my_team_won__isnull=False).filter(Exists(me_in_round))`, con
  `me_in_round = base_queryset(**filters).filter(round_id=OuterRef("round_id"),
  team_index=OuterRef("team_index"))` (el patron de `teammate_synergy`: los
  filtros de la barra, lado incluido, se aplican sobre tu fila de esa ronda;
  tu compañero esta del mismo lado). `.values("player_id",
  "player__username").annotate(attempts=Count("id"),
  won=Count("id", filter=Q(round__my_team_won=True)))`. El nombre sale de
  `Player` (un cambio de nick no parte la fila). Ganado = `my_team_won`: es tu
  equipo, el de el.
- Tu fila de referencia: `base_queryset(**filters).filter(clutch_vs__gt=0,
  round__my_team_won__isnull=False)` con `attempts` y `won` (la misma cuenta
  que la suma de `clutch_conversion`).
- Devuelve `{"min_attempts": CLUTCH_COMPANERO_MIN, "me": {"attempts", "won",
  "pct", "low_sample"}, "rows": [{"player_id", "username", "attempts", "won",
  "pct", "low_sample"}]}`, `pct = _pct(won, attempts)`, `low_sample =
  attempts < CLUTCH_COMPANERO_MIN`, filas ordenadas por `-attempts`,
  `username`.
- `views.teammates` suma `"teammate_clutches": agg.teammate_clutches(**filters)`
  al final del dict (una linea; la 79 no toca esa vista).

**Tests, `backend/tests/test_clutch_companeros.py`** (nuevo, con
`factories.py`; un helper que arma N partidas con vos y los compañeros en el
equipo 0 para que sean habituales, y fija `clutch_vs` y `won` por ronda con
`make_round_player`, que ya acepta esos campos o se setean despues):
- `test_cuenta_intentos_y_ganados_por_companero`: dos habituales; uno con un
  intento ganado y uno perdido (50.0), el otro con un ganado (100.0); orden
  por intentos.
- `test_una_ronda_sin_ganador_no_cuenta` (`my_team_won=None` con
  `clutch_vs=2`: no suma intentos).
- `test_un_companero_que_no_es_habitual_no_sale` (4 partidas juntas, con
  intentos: no sale; con 5, si).
- `test_un_rival_no_cuenta_aunque_clutchee` (fila con `team_index` 1 y
  `clutch_vs` > 0 en tu ronda: no sale ni suma).
- `test_el_filtro_de_lado_aplica` (intentos en ataque y en defensa; con
  `side="Defense"` solo los de defensa).
- `test_un_cambio_de_nick_no_parte_la_fila` (mismo `Player`, dos `username`
  de `RoundPlayer`: una fila con el nombre de `Player`).
- `test_tu_fila_es_tu_conversion` (`me` == suma de `attempts`/`won` de
  `clutch_conversion` con los mismos datos).
- `test_marca_muestra_chica_debajo_de_5` (4 intentos `low_sample` true, 5
  false).
- `test_la_api_trae_teammate_clutches` (`/api/teammates/` con base vacia:
  `rows == []`, `min_attempts == 5`, `me.attempts == 0`).

**Frontend.**
- `frontend/src/clutchCompaneros.js` (logica pura, nuevo):
  `filasClutchCompaneros(data)` -> `[]` si `data?.rows` vacio o ausente; si no,
  primero la fila `{clave: 'yo', nombre: 'Vos', esYo: true, ...data.me}` y
  despues una por compañero `{clave: player_id, nombre: username, playerId,
  attempts, won, pct, low_sample}`. Vitest
  `frontend/src/clutchCompaneros.test.js`: sin datos `[]`; con filas, `Vos`
  primero y despues en el orden de la API; `low_sample` pasa tal cual.
- `frontend/src/pages/Teammates.jsx`, panel "Clutches", un `<h3>Clutches de
  tus compañeros</h3>` entre la tabla "Clutch por operador" y "Clutches
  ganados", con `DataTable` sin `initialSort` (el orden lo da la API, con
  `Vos` primero): columnas Compañero (enlace a `/jugadores/<playerId>` como
  la tabla Sinergia; `Vos` en negrita y sin enlace), Intentos, Ganados,
  Conversión (`pct` con el `*` "Menos de 5 intentos" del mismo markup que
  Clutch por operador), `csvName="clutch-companeros"`. Sin filas: `<p
  className="note">Ningún compañero habitual quedó último en una ronda
  contigo con estos filtros.</p>`. El `hint` del panel suma: "Clutches de tus
  compañeros: los habituales (5 partidas o más en tu equipo) que quedaron
  últimos en rondas contigo, con tu conversión arriba para comparar."

**e2e, `frontend/e2e/humo.spec.js`**, dos tests junto a los de `/companeros`:
- `Compañeros muestra los clutches de tus compañeros`: `seed_demo` da tres
  habituales (Seba, Nico, Chamo, 29 partidas) y ninguno con `clutch_vs > 0`:
  heading visible y la nota vacia; consola limpia. (Si un cambio de
  `seed_demo` les da intentos, el test lee `/api/teammates/` y afirma la
  tabla en vez de la nota.)
- `la tabla de clutches de compañeros pone tu fila primero`: `page.route`
  sobre `**/api/teammates/**` con `route.fetch` + `route.fulfill`, la
  respuesta con `teammate_clutches` reemplazado por `me` (6 intentos, 3
  ganados, 50) y dos filas (8/2/25 y 3/3/100 con `low_sample`): filas en
  orden `Vos`, el de 8, el de 3; el de 3 con `*`; consola limpia.

**`docs/metricas.md`**: fila nueva despues de "Clutch por operador":
`| **Clutches de tus compañeros** | En Compañeros, panel Clutches (clave `teammate_clutches` de `/api/teammates/`). Por compañero habitual (5 partidas o mas en tu equipo, todo el historial, sin filtros: `MIN_PARTIDAS_HABITUAL`), las rondas en que quedo ultimo vivo de tu equipo con rivales vivos (`clutch_vs > 0` en su fila, el mismo algoritmo que el tuyo) y cuantas gano tu equipo. Agrupado por `Player`: un cambio de nick no parte la fila. Las rondas sin ganador no cuentan. Conversion = ganados / intentos. La fila Vos es tu conversion total con los mismos filtros. Un `*` marca menos de 5 intentos (`CLUTCH_COMPANERO_MIN`): sale igual. Respeta los filtros de la barra, aplicados a tu fila de esa ronda. |`
y en `## Muestra minima`: `| Clutches de tus compañeros | habitual (5 partidas juntas) para salir; 5 intentos por fila (`CLUTCH_COMPANERO_MIN`): no se oculta, se avisa con * |`.

**Orden.** Tests backend (rojo) -> `teammate_clutches` -> vista -> vitest ->
`clutchCompaneros.js` -> tabla en `Teammates.jsx` -> e2e -> `metricas.md` ->
`npm run build` -> `verificar.sh`.

**Que puede romperse.** `/api/teammates/` suma una clave: los consumidores
existentes no la leen. Rendimiento: dos consultas mas en una pagina que ya
hace nueve; la de habituales es la de `by_stack` (correlacionada, sin `IN`
de `round_id`); el `player_id__in` es de habituales (pocos). Un
`assertNumQueries(3)` en `test_la_api_trae_teammate_clutches` no: la vista
hace todas; ponerlo sobre `agg.teammate_clutches()` directo (habituales,
compañeros, vos).

**Archivos ocupados.** 79 (espera al humano): `aggregates.py` (guardia de
partidas excluidas: al mergearse, su test de guardia puede pedir clasificar
`teammate_clutches`; lo resuelve quien mergee el segundo, P3), `views.py`
en otras vistas. 120, 122, 126: `aggregates.py` en otras funciones,
`humo.spec.js` y `metricas.md` en otras zonas; ninguna toca
`Teammates.jsx` ni `views.teammates`. No se frena.

**Verificacion manual.** `seed_demo` + `runserver`, `/companeros`: el
subtitulo y la nota vacia. Con la base real: la tabla con `Vos` arriba;
`?side=Attack` cambia los numeros; un `*` en las filas con menos de 5.

Skills: no aplica (una tabla mas sobre un campo que ya se calcula).
Skills del repo: statistical-analysis (conversion con su `n`; dos cortes:
habitual para salir y 5 intentos para avisar, sin ocultar; tu fila con el
mismo denominador como referencia, no un promedio de promedios),
testing-strategy (Django para la cuenta, los cortes y los filtros, vitest
para el orden de filas, e2e vacio con `seed_demo` y con respuesta
interceptada para ver filas).
OMC: plan=— · revisión=— · verificación=—

## Implementacion

(dev 20261113T1858Z-cxQ3TuB) Diseno completo, sobre `origin/dev@84c575b`:

- `aggregates.py`: `CLUTCH_COMPANERO_MIN = 5` y `teammate_clutches(**filters)`
  despues de `clutch_by_operator`. Habituales con la regla de `by_stack`
  (copiada, sin tocar esa funcion) como subconsulta del `player_id__in`;
  intentos del compañero con `Exists` correlacionado sobre tu fila de
  `base_queryset` con el mismo `team_index`; tu fila con la misma cuenta que
  `clutch_conversion`. **2 consultas** (el diseno estimaba 3: los habituales van
  como subconsulta y no como lista).
- `views.teammates`: clave `teammate_clutches` al final.
- `clutchCompaneros.js`: `filasClutchCompaneros` (tu fila primero, `[]` sin
  compañeros con intentos) con un campo `orden` que la tabla usa de
  `initialSort` (patron de `EstadoAlMorir`): sin el, `DataTable` ordena por la
  primera columna y tu fila dejaba de ir arriba.
- `Teammates.jsx`: `<h3>Clutches de tus compañeros</h3>` entre "Clutch por
  operador" y "Clutches ganados", columnas Compañero (enlace al perfil; tu
  fila en negrita sin enlace), Intentos, Ganados, Conversión con `Bar` y `*`;
  nota sin filas; hint del panel extendido.
- `metricas.md`: fila despues de "Clutch por operador" y en `## Muestra minima`.

Desvio del diseno: la fila propia dice **"Tú"** y no "Vos" (revision ciega,
MEDIUM): la UI habla de tú (`resumenPartida.js` usa `'Tú'`, la nota de esta
tabla dice "contigo").

Tests vistos en rojo antes del codigo: backend (10 con `AttributeError:
teammate_clutches`), vitest (`clutchCompaneros.js` inexistente). Criterios ->
tests (`backend/tests/test_clutch_companeros.py`, 13): intentos y ganados por
compañero (`test_cuenta_intentos_y_ganados_por_companero`), rondas sin ganador
(`test_una_ronda_sin_ganador_no_cuenta`); muestra (`test_un_companero_que_no_es_habitual_no_sale`,
`test_marca_muestra_chica_debajo_de_5`); rivales
(`test_un_rival_no_cuenta_aunque_clutchee`, `test_un_habitual_que_clutchea_como_rival_no_cuenta`,
que cae si se quita el `team_index` de la correlacion); filtros
(`test_el_filtro_de_lado_aplica`); agrupado (`test_un_cambio_de_nick_no_parte_la_fila`,
`test_dos_jugadores_con_el_mismo_nick_son_dos_filas`); tu fila
(`test_tu_fila_es_tu_conversion`, `test_tu_fila_sin_intentos_sale_en_cero`);
consultas (`test_consultas_acotadas`, `assertNumQueries(2)` con 1 y 5 rondas);
API (`test_la_api_trae_teammate_clutches`). vitest `clutchCompaneros.test.js`
(3). e2e: `Compañeros muestra los clutches de tus compañeros` (seed_demo: nota
vacia; si la semilla da intentos, tabla con los numeros de la API) y `la tabla
de clutches de compañeros pone tu fila primero` (respuesta interceptada: orden,
enlaces, `*`, consola limpia). Fila en `metricas.md`.

Skills: no aplica.
Skills del repo: statistical-analysis (conversion con su `n`, dos cortes sin ocultar, tu fila con el mismo denominador), testing-strategy (Django, vitest y e2e como dice el diseno, mas el e2e interceptado), ux-copy (tú como el resto de la UI, nota y hint del diseno con tildes), sql-queries (patron vecino de `teammate_synergy` y `by_stack`; `assertNumQueries(2)`), modern-web-guidance no leida (tabla con `DataTable`, `Bar` y markup de `*` ya existentes, sin CSS nuevo).
OMC: plan=— · revisión=5 hallazgos (1 MEDIUM, 4 LOW; 5 arreglados) · verificación=—

## Revision

## QA

## Para el humano

- (arquitecto 2026-11-13, no bloquea) El aviso de 5 intentos por compañero (`CLUTCH_COMPANERO_MIN`) copia el de Clutch por operador, sin calibrar con tu base: mira cuantas filas quedan con `*`.
