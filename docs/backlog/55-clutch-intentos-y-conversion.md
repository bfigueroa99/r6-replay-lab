# 55. Clutch: intentos y conversion por X

estado: implementado
candado: revisor 2026-10-20T00:04Z
rama: claude/equipo-dev/55-clutch-intentos-y-conversion
tipo: funcionalidad
epica: impacto
area: fullstack
prioridad: 2
fuente: ALCANCE.md K3 ([Siege.GG](https://siege.gg/blog/946-player-rating-rebalance), [vlr.gg](https://www.vlr.gg/713548/vlr-cl-knowers-come))
archivos: backend/replays/analytics/metrics.py, backend/replays/models.py, backend/replays/migrations/0003_roundplayer_clutch_vs.py, backend/replays/ingest.py, backend/replays/recompute.py, backend/replays/analytics/aggregates.py, backend/replays/views.py, backend/replays/management/commands/seed_demo.py, backend/tests/test_clutch.py, backend/tests/test_recompute.py, backend/tests/factories.py, frontend/src/pages/Teammates.jsx, frontend/e2e/humo.spec.js, docs/metricas.md
turnos: po 20261019T0004Z, arquitecto 20261019T0404Z, dev 20261019T0804Z, revisor 20261019T1604Z, dev 20261019T2004Z

## PR

(La escribe el Release manager al final.)

## Que gana quien usa la app

Hoy la app solo cuenta los clutches que ganaste (`one_vx`): no sabes cuantas
veces quedaste ultimo y la perdiste. Con los intentos se ve el % real de
conversion en 1v1, 1v2, 1v3... por lado, que es lo que dice si cierras bien
las rondas o solo te acuerdas de las buenas.

## Criterios de aceptacion

- [ ] Columna nueva `clutch_vs` en `RoundPlayer`, calculada al importar en
  `replays/analytics/metrics.py`: si en algun momento de la ronda quedaste
  como unico vivo de tu equipo, vale la cantidad de rivales vivos en ese
  instante (bajas `Kill`, `Death` y `PLAYER_LEAVE` cuentan como muerte, igual
  que el resto de `metrics.py`); si no, 0. Gane o pierda la ronda. Test con
  feed sintetico: quedar solo frente a 3 y perder da `clutch_vs = 3`; quedar
  solo frente a 2 y ganar da `clutch_vs = 2` y el `one_vx` de siempre.
- [ ] Migracion nueva y `manage.py recompute` llenan la columna en partidas ya
  importadas (test: una partida importada antes de la columna, `recompute`,
  la columna queda con el valor esperado).
- [ ] Endpoint (en el agregado que ya devuelve los clutches, o uno nuevo de
  lectura) con una fila por X (1 a 5; `5+` agrupado si aparece mas) y por
  lado: intentos, ganados y %. Ganado = `clutch_vs > 0` y `won`. Con filtros
  de la barra (mapa, fechas, ranked). Test por `curl` o test de Django con
  `?side=attack`.
- [ ] La pagina donde hoy esta la tabla "Clutches" muestra la tabla de
  conversion por X arriba de la lista; sin intentos dice "Todavía no quedaste
  último en ninguna ronda". Entra al e2e con los datos de `seed_demo`.
- [ ] Fila nueva en `docs/metricas.md` ("Clutch: intentos y conversión") con
  la definicion exacta y la diferencia contra `one_vx`.

## Fuera de alcance

- La parte "cuantos se esperaban" de K3: necesita la tabla de K1 primero.
- Cambiar `one_vx`, el Rating, el record "Clutch mas grande" o la regla
  `sin-clutches` del Coach: siguen leyendo `one_vx`.
- Clutches de compañeros o rivales en una pantalla nueva.

## Diseno

Arquitecto 20261019T0404Z. Cabe en un turno de Dev (~350 lineas con tests).
Sin ramas de trabajo abiertas: no pisa a nadie. Agrega la migracion `0003`;
la ficha 59 depende de esta columna y va despues.

**Nota sobre el criterio 1.** `metrics.py` hoy solo cuenta `Kill` y `Death`
como muerte; `PlayerLeave` lo cuenta `pydissect/stats.py` para el `1vX`. Para
`clutch_vs` se cuentan los tres (`Kill` -> `target`, `Death` y `PlayerLeave`
-> `actor`): alguien que se fue no esta vivo. No cambia `died` ni ningun otro
campo existente.

### Regla (unica implementacion)

Funcion pura nueva en `backend/replays/analytics/metrics.py`, debajo de
`annotate_trades` y con la misma idea (la usan el import, `recompute` y la
migracion; duplicarla daria numeros distintos segun el camino):

```python
PLAYER_LEAVE = "PlayerLeave"

def clutch_vs(eventos: list[dict], team_of: dict[str, int]) -> dict[str, int]:
    """Rivales vivos cuando cada jugador quedo como unico vivo de su equipo."""
```

- `eventos`: dicts con `kind`, `actor`, `target`, en el orden del feed.
  `team_of`: nick -> `team_index` de todos los jugadores de la ronda.
- Vivos al arrancar = todos los de `team_of`. Se recorre el feed; cada
  `Kill` mata a `target`, cada `Death`/`PlayerLeave` a `actor`. Un nick que
  no esta en `team_of` o que ya estaba muerto se ignora.
- Despues de cada muerte, por cada equipo con exactamente 1 vivo y al menos
  1 rival vivo: si ese jugador no tiene valor todavia, vale la cantidad de
  rivales vivos en ese instante. Se queda con el primero (no se pisa si
  despues mata a alguien). Un 1v1 simultaneo le da 1 a los dos.
- Devuelve un dict con **todos** los nicks de `team_of` (0 si nunca quedo
  solo). No mira quien gano.

### Archivos

- `backend/replays/models.py`: `RoundPlayer.clutch_vs = models.IntegerField(default=0)`
  debajo de `one_vx`, con comentario de una linea ("rivales vivos cuando
  quedaste solo; 0 si nunca", gane o pierda).
- `backend/replays/migrations/0003_roundplayer_clutch_vs.py`: `AddField` +
  `RunPython(llenar, migrations.RunPython.noop)`. `llenar` usa
  `apps.get_model` para `Round`, `RoundPlayer` y `Event`, arma `team_of` y
  la lista de eventos por ronda (`order_by("order")`, `actor_name`,
  `target_name`, `kind`) y llama a `metrics.clutch_vs` (funcion pura: se
  puede importar desde la migracion sin acoplarla a modelos). `bulk_update`
  solo de las filas con valor distinto de 0, en tandas (`iterator(chunk_size=200)`).
- `backend/replays/analytics/metrics.py`: `analyse_round` agrega
  `"clutch_vs"` a cada jugador de `metrics` llamando a `clutch_vs(events, team_of)`
  despues del bloque de muertes. Linea nueva en el docstring de definiciones.
- `backend/replays/ingest.py` (~linea 255): `clutch_vs=m["clutch_vs"]`.
- `backend/replays/recompute.py`: en `_recompute_round`, despues de
  `annotate_trades`, calcular `clutch_vs(eventos_dict, team_of)` con todos
  los eventos de la ronda (no solo kills) y comparar/actualizar `clutch_vs`
  junto con `CAMPOS` (agregarlo a la tupla y al dict `nuevo`). Actualizar el
  docstring del modulo: ya no recalcula solo trades.
- `backend/replays/analytics/aggregates.py`: `clutch_conversion(**filters)`
  justo arriba de `clutch_detail`. `base_queryset(**filters).filter(clutch_vs__gt=0)`;
  `values("clutch_vs", "side").annotate(attempts=Count("id"), won=Count("id", filter=Q(won=True)))`
  y se arma en Python: una fila por X presente, X >= 5 se agrupa en 5.
  Forma: `{"vs": 3, "label": "1v3", "attempts", "won", "pct", "attack": {"attempts", "won", "pct"}, "defense": {...}}`
  (`label` "1v5+" para el grupo de 5; `pct` con `_pct`, `None` sin intentos).
  Orden por `vs` ascendente. Sin intentos, `[]`. Constante `CLUTCH_X_MAX = 5`.
- `backend/replays/views.py`, `teammates`: `"clutch_conversion": agg.clutch_conversion(**filters)`.
- `backend/replays/management/commands/seed_demo.py`, en `_ronda`:
  `clutch_vs=1 if (gane and not murio and indice % 17 == 0) else (2 if (not gane and murio and not fuera and indice % 7 == 3) else 0)`.
  La primera rama es exactamente la de `one_vx` (los ganados coinciden); la
  segunda agrega intentos perdidos. Ningun numero existente cambia: nada lee
  `clutch_vs` salvo esta ficha.
- `frontend/src/pages/Teammates.jsx`: en el Panel "Clutches", arriba de la
  tabla actual, `<h3>Conversión por rivales</h3>` y un `DataTable` con
  `rows={data?.clutch_conversion || []}`, columnas `label` ("Situación"),
  `attempts` ("Intentos"), `won` ("Ganados"), `pct` ("Conversión", `%`, 0
  digitos), `attack.pct` y `defense.pct` ("Ataque", "Defensa": `render` con
  `fmt`, porque `DataTable` no lee claves anidadas; mirar como lo resuelve el
  resto de la pagina), `csvName="clutch-conversion"`,
  `rowKey={(row) => row.vs}`, `empty="Todavía no quedaste último en ninguna ronda."`.
  Debajo, `<h3>Clutches ganados</h3>` antes de la tabla vieja. Cambiar el
  `hint` del panel: el `1vX` de la lista sigue siendo el del scoreboard; la
  conversion cuenta cada vez que quedaste ultimo, ganes o pierdas.
- `docs/metricas.md`, seccion `## Impacto`, debajo de la fila **1vX
  (clutch)**: fila **Clutch: intentos y conversión** (intento = quedaste como
  unico vivo de tu equipo con rivales vivos, contando `Kill`, `Death` y
  `PlayerLeave`; X = rivales vivos en ese instante; ganado = intento en una
  ronda que tu equipo gano; conversion = ganados / intentos; puede diferir
  del X de `one_vx`, que r6-dissect calcula desde el final de la ronda).
- `frontend/e2e/humo.spec.js`: test `Compañeros muestra la conversion de clutch`
  junto a los otros de Compañeros: el panel "Clutches" tiene la celda
  `1v1` y la celda `1v2` (las dos ramas del seed) y la consola limpia.

### Tests (Django, `backend/tests/test_clutch.py`, nuevo)

- `ClutchVsTests` (funcion pura, sin base):
  `test_quedar_solo_frente_a_tres_da_tres`,
  `test_un_uno_contra_uno_le_da_uno_a_los_dos`,
  `test_el_player_leave_cuenta_como_muerte`,
  `test_matar_despues_de_quedar_solo_no_cambia_el_valor`,
  `test_nadie_queda_solo_da_cero_a_todos`,
  `test_un_nick_desconocido_en_el_feed_se_ignora`.
- `ImportClutchTests` (con `analyse_round` sobre un `round_data` sintetico
  como en `test_metrics.py`): `test_quedar_solo_frente_a_tres_y_perder_da_tres`,
  `test_quedar_solo_frente_a_dos_y_ganar_da_dos_y_el_one_vx_de_siempre`.
- `ConversionTests` (factories): `test_una_fila_por_x_con_intentos_y_ganados`,
  `test_el_lado_se_separa_y_filtra_con_side`, `test_x_de_seis_se_agrupa_en_cinco_mas`,
  `test_sin_intentos_devuelve_lista_vacia`, y uno por API
  (`/api/teammates/?side=attack` trae `clutch_conversion`).
- En `backend/tests/test_recompute.py`:
  `test_recompute_llena_clutch_vs_de_una_partida_vieja` (fila con
  `clutch_vs=0` y eventos que la dejan sola frente a 3 -> `recompute` la deja
  en 3) y `test_dry_run_no_escribe_clutch_vs`.
- La migracion se prueba con la funcion `llenar` importada y llamada con
  `django.apps.apps` sobre una ronda armada (sin `MigrationExecutor`):
  `test_la_migracion_llena_lo_ya_importado`.
- `make_round_player` en `tests/factories.py` acepta `clutch_vs: int = 0`.

### Orden

1. `clutch_vs` pura + `ClutchVsTests`. 2. Modelo, migracion, ingest,
recompute + sus tests. 3. `clutch_conversion` + vista + tests. 4. Seed, UI,
e2e. 5. `docs/metricas.md`. `check.sh`.

### Que puede romperse

- `recompute` hoy compara solo `CAMPOS`: si `clutch_vs` no entra al
  `bulk_update`, el comando dice "sin cambios" y no escribe.
- La migracion corre en la base real del usuario al primer `runserver`: tiene
  que tolerar rondas sin jugadores y eventos sin `actor_name` (no revienta).
- `test_seed_demo` y el e2e no deberian moverse; si algun numero de
  Compañeros cambia, el seed toco algo que no era `clutch_vs`.
- `RoundPlayer` tiene `Meta.indexes`: no hace falta indice nuevo.

### Verificacion manual

`manage.py seed_demo --force`, `/api/teammates/` trae `clutch_conversion`
con filas `1v1` y `1v2`; `?side=defense` cambia los numeros; en la UI,
Compañeros -> Clutches muestra la tabla nueva arriba. Con base real:
`manage.py migrate` y despues `manage.py recompute --dry-run` no deberia
reportar cambios de `clutch_vs` (la migracion ya los lleno).

## Implementacion

Dev 20261019T0804Z. Todo el diseno, sin desvios de alcance.

- `metrics.clutch_vs` pura (unica regla) la usan `analyse_round`, `recompute`
  y la migracion `0003_roundplayer_clutch_vs` (`AddField` + `RunPython`
  `llenar`, tolera rondas sin jugadores y eventos sin nick).
- `recompute`: `clutch_vs` entra a `CAMPOS`, asi que `--dry-run` y el
  conteo de filas lo incluyen.
- `aggregates.clutch_conversion` + `/api/teammates/` -> `clutch_conversion`.
- Compañeros -> Clutches: tabla "Conversión por rivales" arriba y
  "Clutches ganados" debajo; hint nuevo. Las columnas de lado se aplanan en
  la pagina (`attack_pct`, `defense_pct`) para que ordenen y salgan al CSV.
- `seed_demo`: segunda rama de `clutch_vs = 2` en intentos perdidos; ningun
  otro campo cambia.
- `docs/metricas.md`: fila "Clutch: intentos y conversión".

Tests: `tests/test_clutch.py` (15: funcion pura, import, conversion, API con
`?side=Attack`, migracion) y `RecomputeClutchTests` en `test_recompute.py`.
Desvio: `ComandoTests.setUp` de `test_recompute.py` ahora crea a `amigo` y
`rival` con `clutch_vs=1`, que es lo que el import de hoy deja en esa ronda
(tras la primera baja quedan 1v1). Sin eso `test_sin_cambios_lo_dice`
reportaba el clutch como cambio pendiente: el fixture representaba una
importacion sin la columna.

Revision ciega (subagente) antes del push, corregido: el e2e chocaba en modo
estricto con las celdas `1v1` de la tabla de ganados (ahora afirma las filas
de la primera tabla); `clutch_conversion` excluye rondas con
`my_team_won = None` y cuenta ganados por `round__my_team_won` (test
`test_una_ronda_sin_ganador_conocido_no_cuenta_como_intento`, aclarado en
`metricas.md`); docstring, `help` y README de `recompute` mencionan
`clutch_vs` (desvio de `archivos:`: `management/commands/recompute.py` y
`README.md`).

`check.sh`: Todo en verde (708 tests backend, 115 frontend, build, 44 e2e).

Nota para la Revision: el criterio 1 del diseno dice "Un 1v1 simultaneo le
da 1 a los dos"; el test lo cubre como "cae el tercero y quedan uno frente a
otro".

## Revision 2026-10-19 sobre 2b44e75

Revisor 20261019T1604Z. Rama al dia con `origin/main`; `check.sh` en verde
antes de revisar (708 tests backend, 115 frontend, build, 44 e2e). Revision
ciega por subagente y cada hallazgo reproducido por el lider.

Criterios: los 5 cubiertos. (1) `ClutchVsTests` e `ImportClutchTests`; (2)
`RecomputeClutchTests` y `test_la_migracion_llena_lo_ya_importado`, ademas la
migracion se aplico sin error sobre una base sembrada (`migrate replays 0002`
y `migrate` de nuevo); (3) `ConversionTests` + API con `?side=`; filtros por
`base_queryset` (`is_me=True`, mapa, fechas, ranked, sesion); (4) e2e
`Compañeros muestra la conversion de clutch` (seed: 1v1 2/2 100 %, 1v2 8/0 0 %);
(5) fila en `docs/metricas.md`. Desvios de `archivos:` (`recompute.py` del
comando, README) explicados en Implementacion. Sin `print` ni `console.log`;
UI con tildes, identificadores sin.

Hallazgos:

- [regla] README.md (todo el archivo)
  Que pasa: la rama convierte los finales de linea del README de CRLF a LF;
  el diff muestra 932 lineas cambiadas para un cambio de una linea.
  Como reproducirlo: `git show origin/main:README.md | grep -c $'\r'` da 466;
  en la rama da 0. `git diff --stat origin/main...<rama> --ignore-cr-at-eol -- README.md`
  da 1 linea. Cualquier otra rama que toque el README choca contra esta, el PR
  es ilegible y `git blame` pierde la historia del archivo.
  Arreglo sugerido: restaurar el README de main con sus CRLF y reaplicar solo
  la linea de `recompute` (`git checkout origin/main -- README.md`, editar
  conservando `\r\n`, confirmar con `--stat` que el diff es de 1 linea).
- [bug] backend/replays/analytics/metrics.py:98 (`clutch_vs`)
  Que pasa: la condicion "quede solo" se evalua solo despues de una muerte,
  nunca sobre los vivos iniciales.
  Como reproducirlo: `clutch_vs([kill("yo","r1")], {"yo":0,"r1":1,"r2":1,"r3":1})`
  da `{"yo": 2}` (esperado 3: arranco 1v3); con `kill("r1","yo")` primero da 0
  (esperado 3, un 1v3 perdido). Pasa en rondas donde un equipo ya arranca con
  uno (abandonos de rondas previas, custom).
  Arreglo sugerido: evaluar la misma condicion una vez antes del loop; test
  `test_solo_desde_el_inicio_cuenta_todos_los_rivales`. Menor, pero es un
  numero mal y el arreglo son tres lineas.

Duda sin verificar (va a `## Correccion 2026-10-19

Dev 20261019T2004Z, sobre los dos hallazgos de la Revision 2b44e75:

- [regla] README: restaurado desde `origin/main` con sus CRLF y reaplicada
  solo la linea de `recompute`; `git diff --stat origin/main -- README.md`
  da 1 linea. Ningun otro archivo de la rama cambio finales de linea
  (comparado `--numstat` con y sin `--ignore-cr-at-eol`).
- [bug] `clutch_vs`: la condicion "quede solo" se evalua tambien antes del
  primer evento (`marcar_solos()` antes del loop). Tests nuevos
  `test_solo_desde_el_inicio_cuenta_todos_los_rivales` y
  `test_solo_desde_el_inicio_y_caer_primero_es_un_intento_perdido`.
  Dos fixtures que tenian un equipo de un solo jugador cambian de valor con
  la regla corregida: `test_un_uno_contra_uno_le_da_uno_a_los_dos` ahora usa
  un 1v1 real desde el inicio, y el caso viejo (r1 arranca 1v2) quedo como
  `test_quien_ya_estaba_solo_conserva_su_primer_valor`; en
  `ComandoTests.setUp` de `test_recompute.py` el rival arranca solo frente a
  dos y su `clutch_vs` esperado pasa de 1 a 2. `docs/metricas.md` lo aclara.
  `seed_demo` asigna `clutch_vs` a mano y no se mueve.

Revision ciega (subagente) sobre la correccion: sin hallazgos (casos borde
probados: `team_of` vacio, equipo sin rivales, tres equipos, actor
desconocido). `check.sh`: Todo en verde (711 tests backend, 115 frontend,
build, 44 e2e).

## Para el humano`): antes de Y9S1 `PlayerLeave`
sale de mensajes de texto (`pydissect/events.py:300`); si el `.rec` registra
abandonos despues del final de la ronda, un compañero que se va tras ganar
por tiempo deja a otro "solo con rivales vivos" y suma un intento falso. El
`1vX` de `pydissect/stats.py` comparte el supuesto. No se puede confirmar sin
`.rec` reales; no bloquea.

Veredicto: corregir (los dos hallazgos).

## Para el humano

Si `clutch_vs` y `one_vx` difieren en el X de una misma ronda ganada (la
logica de r6-dissect cuenta los rivales de otra forma), la tabla usa
`clutch_vs` para agrupar y `one_vx` queda como estaba. Es reversible; avisar
si se prefiere unificarlas.

Revisor 2026-10-19: verificar con `.rec` reales de temporadas anteriores a
Y9S1 si aparecen `PlayerLeave` despues del final de la ronda (ver Revision);
si aparecen, `clutch_vs` cuenta intentos falsos y convendria ignorar eventos
posteriores a `Round.clock_end`.
