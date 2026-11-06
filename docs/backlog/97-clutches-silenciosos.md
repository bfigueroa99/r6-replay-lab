# 97. Clutches silenciosos

estado: revisado
candado: qa 2026-11-06T04:04Z
rama: claude/equipo-dev/97-clutches-silenciosos
tipo: funcionalidad
epica: impacto
area: fullstack
prioridad: 3
fuente: K11 de ALCANCE.md; [Siege.GG, rating rebalance](https://siege.gg/blog/946-player-rating-rebalance) (2026-08-11: "It also allows for 'quiet' clutches to have an impact on rating"); investigador 2026-11-03
archivos: backend/replays/analytics/metrics.py, backend/replays/models.py, backend/replays/migrations/0005_roundplayer_clutch_kills.py, backend/replays/ingest.py, backend/replays/recompute.py, backend/replays/management/commands/recompute.py, backend/replays/analytics/aggregates.py, backend/replays/views.py, backend/replays/management/commands/seed_demo.py, backend/tests/test_clutch.py, backend/tests/test_recompute.py, backend/tests/test_seed_demo.py, frontend/src/clutchSilencioso.js, frontend/src/clutchSilencioso.test.js, frontend/src/pages/Teammates.jsx, frontend/e2e/humo.spec.js, docs/metricas.md
turnos: po 20261106T0041Z-cSxDY1g, arquitecto 20261106T0200Z-ct6rosE, dev 20261106T0319Z-csweoG8, revisor 20261106T0345Z-cTsg2Tv

## PR

(La escribe el Release manager al final.)

## Que gana quien usa la app

La tabla de clutches de Compañeros (intentos y ganados por 1vX, ficha 55)
no distingue un 1v2 ganado matando a los dos de uno ganado sin disparar
(aguantando el reloj en defensa, o esperando el plant/defuse). Con esto se
ve cuantos de tus clutches ganados fueron "silenciosos", por lado y por
condicion de victoria: si cuando quedas solo ganas peleando o ganas
escondiendote.

## Criterios de aceptacion

- [ ] Al importar, cada `RoundPlayer` con `clutch_vs > 0` guarda cuantas
      bajas hizo desde el instante en que quedo como unico vivo de su equipo
      (columna nueva, p. ej. `clutch_kills`, calculada en
      `analytics/metrics.py` con la misma recorrida del feed que
      `clutch_vs`; los teamkills no cuentan, como en `kills` desde la
      ficha 67). `recompute` la llena en la base existente. Tests de
      `metrics.py`: un 1v2 ganado con dos bajas da 2, un 1v1 ganado por
      tiempo da 0, una baja hecha antes de quedar solo no cuenta.
- [ ] La API que ya sirve `clutch_conversion` agrega, por cada fila 1vX y
      por lado, los ganados silenciosos (ganados con `clutch_kills = 0`) y
      el total de ganados silenciosos por condicion de victoria
      (`Round.win_condition`, con las inferidas del reloj marcadas aparte,
      como dice `docs/formato-rec.md`). Test de Django con datos sinteticos.
- [ ] La tabla de clutches de `Teammates.jsx` muestra la columna
      "Silenciosos" (cantidad y % de los ganados) y una nota con el reparto
      por condicion de victoria; con muestra chica se marca como las otras
      filas.
- [ ] `docs/metricas.md` tiene la fila de "Clutch silencioso" con su
      definicion exacta (que cuenta como baja, desde que instante).
- [ ] El e2e ve la columna en la pagina de Compañeros con los datos de
      `seed_demo` sin errores en la consola (si `seed_demo` necesita un
      clutch silencioso, se agrega y se ajustan los numeros que afirme el e2e).

## Fuera de alcance

- Tocar el Rating: la Siege.GG premia el clutch silencioso, pero cambiar la
  formula del Rating que ya se muestra es una decision del humano (P10). Si
  el diseno lo cree util, va a `## Revision 2026-11-06 sobre c3c753c

(Revisor 20261106T0345Z-cTsg2Tv. Revision a ciegas en dos ejes, receta 2 de
OMC: dos `omc-code-reviewer` en paralelo, estandares e intencion; los dos
"aprobar". Cada hallazgo de abajo lo confirme en el codigo.)

Partida en verde: `verificar.sh` VERDE 1995ec0 (1069 tests backend, 257
vitest, 76 e2e); dev no se movio desde la implementacion.

Hallazgos:

- [intencion] MEDIUM `frontend/src/pages/Teammates.jsx:54-58, 264-281`
  Que pasa: la API manda `attack.silent` y `defense.silent` por fila
  (criterio 2), pero la pagina no los muestra ni los exporta en el CSV; el
  reparto por lado de los silenciosos solo se ve cambiando el filtro de lado
  de la barra. Arreglo sugerido: aplanar `attack_silent`/`defense_silent` en
  el `map` y mostrarlos en el `title` de la celda o en el CSV, o decir en el
  hint que el lado sale con el filtro. No bloquea: el criterio 3 pide
  cantidad y % de los ganados, y eso esta.
- [estilo] LOW `frontend/src/clutchSilencioso.test.js:1`
  Que pasa: el comentario de cabecera dice "Compañeros" con ñ (CLAUDE.md:
  comentarios sin tildes ni ñ). Arreglo: "Companeros".
- [estilo] LOW `frontend/src/pages/Teammates.jsx:289`
  Que pasa: `notaSilenciosos(data?.clutch_silent)` se llama dos veces en el
  mismo render. Arreglo: una constante junto a `conversion`.

Notas sin hallazgo: el `*` de Silenciosos corta sobre ganados y no sobre
intentos como sitio y operador; es deliberado y esta documentado en el
comentario, en `metricas.md` y en el `title`. La ronda 153 del seed (ataque
ganado `ObjectiveOrTime` con `possible_plant=False`) no la produciria el
import real; es deliberada y comentada para no mover los tests de plant.

Criterios: 1 (`ClutchKillsTests`, `ImportClutchTests`,
`MigracionClutchKillsTests`, `RecomputeClutchKillsTests`), 2
(`ConversionTests`, `ClutchSilenciosoTests`), 3 (columna, `*`, nota; e2e y
vitest), 4 (fila "Clutch silencioso" en `metricas.md`) y 5 (seed + e2e de
Compañeros) cubiertos. El diff no sale de `archivos:` (el factory
`make_round_player` esta explicado en Implementacion). Sin `print` ni
`console.log`; identificadores sin tildes, UI con tildes.

Seguridad: no se sumo `omc-security-reviewer`; el unico cambio en
`ingest.py` es asignar `clutch_kills=m["clutch_kills"]` al crear el
`RoundPlayer`, sin lectura nueva del `.rec`.

Veredicto: aprobar -> `revisado`. Los tres hallazgos los puede tomar el Dev
si vuelve la ficha; no frenan la QA.

Skills: no aplica.
OMC: plan=— · revisión=3 hallazgos (0 arreglados: 1 MEDIUM, 2 LOW, ninguno bloquea) · verificación=—

## Para el humano` como pregunta.
- Señal del Coach sobre clutches (es K9, otra idea).
- Clutches perdidos: un 1vX perdido sin bajas no es "silencioso", es perdido.

## Diseno

(Arquitecto 20261106T0200Z-ct6rosE, sobre `origin/dev@8f3fb74`. Plan por
consenso, receta 1 de OMC: planner, architect y critic en dos rondas; APPROVE
en la segunda.)

**Implementar despues de que #81 (ficha 79) se mergee**, si se puede: las
dos agregan una migracion `0005`. Prioriza, no bloquea: si la 79 sigue
esperando al humano, se implementa con `0005` y gana la que entra primero a
`dev` (ver paso 2). Tambien comparte `aggregates.py`, `views.py` y
`metricas.md` con la 79 y la 93, y `humo.spec.js` con la 93: conflictos de
contexto, se conservan los dos lados.

### Definicion de `clutch_kills` (la regla, una sola vez)

- **Instante**: el evento del feed (por `order`) cuya muerte deja al jugador
  como unico vivo de su equipo con al menos un rival vivo: el mismo instante
  de `clutch_vs` (`Kill` mata al `target`, `Death` y `PlayerLeave` matan al
  `actor`). Se cuentan los eventos **estrictamente posteriores**. Si su equipo
  arranca la ronda con uno solo, cuenta todo el feed.
- **Baja** = la regla de `bajas_a_rivales` (ficha 67): `Kill` con `actor` en
  `team_of` y `target` que no es de su equipo. Teamkills y suicidios no
  cuentan; una victima con nick desconocido si; un autor desconocido no le
  suma a nadie. Una baja que el feed le atribuye despues de morir (gadget)
  cuenta.
- Vale el primer instante (mismo guard de `clutch_vs`). Con `clutch_vs = 0`,
  `clutch_kills = 0`.
- Se cuenta desde el instante de `clutch_vs`, **no** desde el final de la
  ronda como `one_vx`: con abandonos estas bajas y el X del 1vX pueden no
  cuadrar.
- **Silencioso** = intento ganado (`clutch_vs > 0`, `round.my_team_won = True`)
  con `clutch_kills = 0`. Un perdido nunca es silencioso. Se mantiene la
  definicion de la ficha: quedar solo, plantar, morir y ganar sin bajas
  **es** silencioso (va documentado; separar muerto de vivo es pregunta en
  `## Para el humano`).

### Paso 1: `backend/replays/analytics/metrics.py`

- Extraer el cuerpo de `clutch_vs` a
  `_quedar_solo(eventos, team_of) -> tuple[dict[str, int], dict[str, int]]`
  que devuelve `(rivales, desde)`: mismo algoritmo sin cambios; el loop pasa
  a `for i, e in enumerate(eventos)` y `marcar_solos(i)` guarda
  `desde[nick] = i` cuando escribe `valor[nick]`; la llamada inicial es
  `marcar_solos(-1)`.
- `clutch_vs(eventos, team_of)` queda `return _quedar_solo(eventos, team_of)[0]`:
  **firma y salida identicas** (la importa la migracion 0003). Docstring:
  "La importan las migraciones 0003 y 0005: su firma no cambia."
- Nueva `clutch_kills(eventos, team_of) -> dict[str, int]`:
  ```python
  rivales, desde = _quedar_solo(eventos, team_of)
  valor = dict.fromkeys(team_of, 0)
  for nick, i in desde.items():
      valor[nick] = bajas_a_rivales(eventos[i + 1:], team_of)[nick]["kills"]
  return valor
  ```
  Devuelve **una clave por cada nick de `team_of`**, tambien para quien
  nunca quedo solo (misma forma que `clutch_vs`): `_recompute_round` compara
  todos los `CAMPOS` y sin esto revienta con `KeyError`. Docstring: unica
  implementacion (import, `recompute`, migracion) y la definicion de arriba.
- Docstring del modulo: linea `clutch_kills   bajas a rivales desde que quedo como unico vivo de su equipo (0 si nunca)`.
- `analyse_round`: `"clutch_kills": 0` en el dict inicial junto a
  `clutch_vs`, y despues del loop de `clutch_vs` el mismo loop con
  `clutch_kills(events, team_of)` (guard `if nick in metrics`).

### Paso 2: modelo, migracion, import y `recompute`

- `backend/replays/models.py`, `RoundPlayer`, debajo de `clutch_vs`:
  `clutch_kills = models.IntegerField(default=0)`, con comentario: el
  default 0 se leeria como "silencioso", por eso la migracion llena lo ya
  importado.
- `backend/replays/migrations/0005_roundplayer_clutch_kills.py`, depende de
  `0004_roundplayer_opening_kill_traded`: `AddField` + `RunPython(llenar,
  RunPython.noop)`, copiando el patron de `0003`, con
  `from replays.analytics.metrics import clutch_kills`. Recorre solo las
  rondas con intento (`RoundPlayer.objects.filter(clutch_vs__gt=0)
  .values_list("round_id", flat=True).distinct()`); por ronda, `team_of` de
  sus jugadores y eventos de `Event` (`kind`, `actor_name`, `target_name`)
  por `order`; guarda solo lo que cambia con `bulk_update(..., ["clutch_kills"])`
  cada 200. Una ronda sin jugadores o un evento sin nick no la tumban.
- **Numeracion**: si al implementar o al mergear `dev` ya trae
  `0005_match_excluded.py` (la 79), este archivo pasa a
  `0006_roundplayer_clutch_kills.py` con dependencia
  `("replays", "0005_match_excluded")`, sin migracion de merge, y en el mismo
  commit cambia el `import_module` del test; `git grep -n
  "0005_roundplayer_clutch_kills"` tiene que dar vacio. Si esta entra
  primero, la 79 renumera la suya a `0006`: el Dev lo deja en `## Para el
  humano` y en el PR. `python manage.py makemigrations --check --dry-run`
  sin cambios ni "Conflicting migrations".
- `backend/replays/ingest.py:~260`: `clutch_kills=m["clutch_kills"],`.
- `backend/replays/recompute.py`: importar `clutch_kills`, agregar
  `"clutch_kills"` al final de `CAMPOS`, y en `_recompute_round`, despues de
  `clutch_vs`, `for nick, k in clutch_kills(planos, team_of).items():
  metrics[nick]["clutch_kills"] = k`. Docstrings del modulo y de
  `recompute()`.
- `backend/replays/management/commands/recompute.py`: docstring y `help`
  nombran `clutch_kills` junto a `clutch_vs`.

### Paso 3: agregados y API

En `backend/replays/analytics/aggregates.py`:

- Junto a `CLUTCH_X_MAX`: `CLUTCH_SILENCIOSO_MIN = 5`, con comentario: el
  corte se mide sobre los **ganados** de la fila (el % es sobre ganados), a
  diferencia de sitio y operador, que cortan sobre intentos; es semantica
  nueva en esta tabla, que hoy no marca muestra chica.
- `clutch_conversion`: al `annotate` se suma
  `silent=Count("id", filter=Q(round__my_team_won=True, clutch_kills=0))`;
  acumuladores `{"attempts", "won", "silent", "Attack": [0, 0, 0], "Defense": [0, 0, 0]}`;
  `_lado` devuelve `{"attempts", "won", "silent", "pct"}`; cada fila suma
  `"silent"` (int), `"silent_pct"` (`_pct(silent, won)`, `None` sin
  ganados) y `"silent_low_sample"` (`0 < won < CLUTCH_SILENCIOSO_MIN`).
  Ejemplo:
  `{"vs":1,"label":"1v1","attempts":2,"won":2,"pct":100.0,"silent":1,"silent_pct":50.0,"silent_low_sample":true,"attack":{"attempts":2,"won":2,"silent":1,"pct":100.0},"defense":{"attempts":0,"won":0,"silent":0,"pct":null}}`.
- Nueva `clutch_silent(**filters) -> dict`:
  `base_queryset(**filters).filter(clutch_vs__gt=0, round__my_team_won=True).aggregate(...)`
  con `won=Count("id")`, `silent=Count("id", filter=Q(clutch_kills=0))`,
  `elimination=... Q(clutch_kills=0, round__win_condition="KilledOpponents")`,
  `other=... Q(clutch_kills=0, round__win_condition="ObjectiveOrTime")`;
  `unknown = silent - elimination - other` (por resta, como
  `round_endings`). Devuelve
  `{"won", "silent", "silent_pct", "by_condition": {"elimination", "other", "unknown"}}`.
  Docstring: `other` es `ObjectiveOrTime`, que en temporadas nuevas se infiere
  del reloj (`docs/formato-rec.md`) y no se parte en plant, defuse o tiempo;
  se usa `win_condition` y no `win_condition_certain` para cuadrar con
  "Como se cierran tus rondas" (hoy son equivalentes); una condicion certera
  nueva del parser caeria en `unknown` hasta decidir.
- `backend/replays/views.py`, en `teammates`, despues de
  `clutch_conversion`: `"clutch_silent": agg.clutch_silent(**filters),`.

### Paso 4: frontend

- `frontend/src/clutchSilencioso.js` (nuevo, puro, sin importar `ui.jsx`):
  - `celdaSilenciosos(row)`: `'—'` si `!row.won`; si no
    `` `${row.silent} (${Math.round(row.silent_pct)}%)` `` -> `"1 (50%)"`.
  - `notaSilenciosos(resumen)`: `null` si `!resumen?.won`; si no:
    `De tus ${won} clutches ganados, ${silent} fueron silenciosos (sin bajas tuyas desde que quedaste solo): ${elimination} por eliminación, ${other} sin eliminación (plant, defuse o tiempo; inferido del reloj)`
    + (`unknown` ? `, ${unknown} sin dato` : '') + `.`; con `won === 1`
    "clutch ganado", con `silent === 1` "fue silencioso".
- `frontend/src/pages/Teammates.jsx`, tabla "Conversión por rivales":
  columna nueva **al final** (los e2e afirman prefijos de fila):
  `{ key: 'silent', label: 'Silenciosos', help: 'Clutches ganados sin ninguna baja tuya desde que quedaste solo. Un * marca menos de 5 ganados: con tan poca muestra el % todavía no dice mucho.', csv: (row) => row.silent, render: (row) => <>{celdaSilenciosos(row)}{row.silent_low_sample ? <span className="dim muestra-chica" title="Menos de 5 ganados">*</span> : null}</> }`.
  El CSV lleva el numero; no hay columna `silent_pct` en el CSV
  (`DataTable` no admite columnas solo de CSV). Debajo de la tabla:
  `notaSilenciosos(data?.clutch_silent)` en un `<p className="note">` (o el
  elemento de nota que ya use la pagina), solo si no es `null`. El `hint`
  del panel suma: "Silenciosos son los ganados sin bajas tuyas desde que
  quedaste solo."

### Paso 5: seed, docs, e2e

- `backend/replays/management/commands/seed_demo.py`: constante
  `CLUTCH_SILENCIOSO = 153` (el `indice` de `demo-21`, ronda 6, Bank, Attack,
  sobrevive, `kills=1`). Los dos clutches ganados del seed son los indices
  102 (Border) y 153 (Bank).
  - En el `RoundPlayer` de `yo`:
    `clutch_kills=1 if (gane and not murio and indice % 17 == 0 and indice != CLUTCH_SILENCIOSO) else 0`
    (la baja del 153 fue antes de quedar solo).
  - La `Round` del indice 153 se crea con `win_condition="ObjectiveOrTime"`
    y `win_condition_certain=False`; el resto sigue `KilledOpponents`.
    `possible_plant` **no** se toca (queda False), aunque un ataque que gana
    sin eliminar implica plant: comentario junto a la constante diciendo que
    la combinacion es deliberada, porque `test_seed_demo.py:66` y
    `humo.spec.js:246` afirman que ninguna ronda del seed es plant probable.
    El comentario dice tambien que es el caso que motiva la ficha (ganado
    sin bajas, cierre inferido del reloj).
  - Lo que mueve (verificado por grep, nadie lo afirma): "Como se cierran tus
    rondas" en Ataque (1 `won_other`), el contador de inferidas del Inicio
    (0 -> 1; se lee "1 rondas", plural preexistente, no se toca aca), el
    "(inferida)" y la narrativa de `demo-21` ronda 6 (los e2e de detalle abren
    `demo-28`). Correr suite y e2e completos igual.
- `frontend/e2e/humo.spec.js`:
  - linea 199: el comentario pasa a "seed_demo cierra todo por eliminacion
    salvo una ronda de Bank en ataque (el clutch silencioso, cierre
    inferido)...".
  - test `'Compañeros muestra la conversion de clutch'` (~620): las dos
    aserciones actuales quedan; se agregan el `columnheader` "Silenciosos",
    la fila `/^1v1 2 2 100%.* 1 \(50%\)/` (si el texto accesible no calza
    por el `*` o el `help`, `getByRole('cell', { name: /1 \(50%\)/ })` dentro
    de la fila 1v1), y la nota: `/De tus 2 clutches ganados, 1 fue silencioso/`
    y `/0 por eliminación, 1 sin eliminación/`.
- `docs/metricas.md`: fila nueva despues de "Clutch: intentos y
  conversión" (y en esa fila, al final: "La columna Silenciosos se define en
  Clutch silencioso."):

  | **Clutch silencioso** | Clutch ganado (intento de la fila de arriba en una ronda que tu equipo gano) sin ninguna baja tuya desde que quedaste solo (`clutch_kills = 0`). `clutch_kills` se calcula al importar desde el feed (`metrics.clutch_kills`): cuenta las bajas a rivales (la regla de `kills`: sin teamkills ni suicidios; una victima sin nick conocido cuenta) de los eventos posteriores al que te dejo como unico vivo de tu equipo, el mismo instante de `clutch_vs` (no desde el final de la ronda como `one_vx`: con abandonos el X y estas bajas pueden no cuadrar con el 1vX); la baja que hiciste antes de quedar solo no cuenta, y si tu equipo arranca la ronda con uno solo cuenta desde el primer segundo. Un clutch perdido sin bajas no es silencioso; uno ganado en el que moriste despues de quedar solo (plantaste y la defensa no desactivo) si, si no hiciste bajas. Columna Silenciosos = cantidad y % sobre los ganados de esa fila (`—` sin ganados); un `*` marca menos de 5 ganados (`CLUTCH_SILENCIOSO_MIN`; a diferencia de las tablas por sitio y por operador, el corte es sobre ganados, no sobre intentos). La nota reparte los silenciosos por condicion de victoria de la ronda (`Round.win_condition`): por eliminacion (`KilledOpponents`: los rivales cayeron sin bajas tuyas, por caidas, sus gadgets o teamkills), sin eliminacion (`ObjectiveOrTime`: plant, defuse o tiempo, inferido del reloj en temporadas nuevas y nunca separado) y sin dato; en temporadas nuevas casi todo silencioso cae en sin eliminacion. No entra al Rating. Partidas importadas antes se llenan con la migracion o con `manage.py recompute`. Respeta los filtros de la barra. |

### Tests nuevos

`backend/tests/test_clutch.py`:
- `ClutchKillsTests` (feed plano como `ClutchVsTests`):
  `test_un_1v2_ganado_con_dos_bajas_da_2`,
  `test_un_1v1_ganado_por_tiempo_da_0`,
  `test_una_baja_antes_de_quedar_solo_no_cuenta`,
  `test_un_suicidio_despues_de_quedar_solo_no_cuenta`,
  `test_quien_arranca_solo_cuenta_desde_el_primer_evento`,
  `test_una_baja_a_un_nick_desconocido_cuenta`,
  `test_un_autor_desconocido_no_le_suma_a_nadie`,
  `test_sin_clutch_da_cero_a_todos`,
  `test_quien_nunca_quedo_solo_da_cero_y_esta_en_el_dict` (`set(resultado) == set(team_of)`),
  `test_un_rival_que_se_va_no_es_una_baja`,
  `test_el_atacante_que_muere_tras_quedar_solo_y_gana_da_cero`,
  `test_clutch_vs_devuelve_lo_mismo_que_antes` (valor literal sobre un feed mixto).
- `ImportClutchTests`: `test_el_import_guarda_las_bajas_desde_que_quedo_solo`,
  `test_el_import_de_un_clutch_ganado_sin_bajas_da_cero`.
- `MigracionClutchKillsTests` (`import_module("replays.migrations.0005_roundplayer_clutch_kills").llenar`):
  `test_la_migracion_llena_clutch_kills_de_lo_ya_importado` (con una ronda
  sin jugadores que no la tumba), `test_la_migracion_no_toca_rondas_sin_intento`.
- `ConversionTests`: ajustar el dict exacto de
  `test_el_lado_se_separa_y_filtra_con_side` (suma `"silent"`); el helper
  `_ronda` gana `kills_solo: int = 0`;
  `test_la_fila_cuenta_los_ganados_silenciosos_por_lado` (Attack ganado con 0
  y con 2, Defense ganado con 0, Defense perdido con 0 -> `silent=2`,
  `attack.silent=1`, `defense.silent=1`, `silent_pct=66.7`),
  `test_un_clutch_perdido_sin_bajas_no_es_silencioso`,
  `test_cuatro_ganados_son_muestra_chica_y_cinco_no`,
  `test_sin_ganados_el_pct_de_silenciosos_es_none`,
  `test_los_silenciosos_de_las_filas_suman_lo_mismo_que_clutch_silent` (con
  una ronda `my_team_won=None` y una perdida, sin filtro y con `side="Attack"`).
- `ClutchSilenciosoTests` (`agg.clutch_silent`):
  `test_reparte_los_silenciosos_por_condicion_de_victoria` (`KilledOpponents`
  -> elimination, `ObjectiveOrTime` -> other, `''` -> unknown),
  `test_una_ronda_sin_ganador_no_cuenta`, `test_respeta_el_filtro_de_lado`,
  `test_con_base_vacia_da_ceros`, `test_la_api_de_companeros_trae_clutch_silent`
  (`/api/teammates/?side=Attack`).

`backend/tests/test_recompute.py`:
- `test_recompute_llena_clutch_kills_de_una_partida_vieja`,
  `test_dry_run_no_escribe_clutch_kills`,
  `test_recompute_de_clutch_kills_es_idempotente`,
  `test_recompute_con_un_jugador_que_nunca_quedo_solo_no_revienta`.
- Ajuste de `ComandoTests.setUp` (154-169): `clutch_kills=1` en "amigo" y en
  "rival" (es lo que da el feed); sin eso `test_sin_cambios_lo_dice` falla.
  Otro fixture que se ponga rojo se corrige con el valor del feed, nunca
  cambiando la regla.

`backend/tests/test_seed_demo.py`:
- `test_de_los_dos_clutches_ganados_uno_es_silencioso` (por mapa: Border 1,
  Bank 0), `test_la_api_del_seed_da_un_silencioso_inferido_del_reloj`
  (`{"won": 2, "silent": 1, "silent_pct": 50.0, "by_condition": {"elimination": 0, "other": 1, "unknown": 0}}`),
  `test_la_ronda_del_clutch_silencioso_es_la_unica_inferida`
  (`win_condition_certain=False` da 1, de Bank en ataque; comentario: una
  ficha futura que siembre otra inferida ajusta este numero).

`frontend/src/clutchSilencioso.test.js` (vitest):
`celdaSilenciosos da guion sin ganados`, `celdaSilenciosos da cantidad y porcentaje`,
`notaSilenciosos es null sin ganados`,
`notaSilenciosos usa singular con un ganado y un silencioso`,
`notaSilenciosos agrega sin dato solo si hay`.

### Orden de implementacion

1. `metrics.py` + `ClutchKillsTests` (y que `ClutchVsTests` siga verde sin tocarlo).
2. Modelo, migracion, `ingest.py`, `recompute.py` + sus tests y el ajuste de `ComandoTests`.
3. `aggregates.py`, `views.py` + `ConversionTests`/`ClutchSilenciosoTests`.
4. `seed_demo.py` + `test_seed_demo.py`; suite completa.
5. Frontend (`clutchSilencioso.js` + vitest, `Teammates.jsx`), e2e, `metricas.md`; `check.sh` completo.

### Criterios comprobables

- `python manage.py test tests` verde; `ClutchVsTests` y los tests de la 0003 sin tocar.
- `python manage.py makemigrations --check --dry-run` -> "No changes detected".
- `python manage.py test tests.test_clutch tests.test_recompute tests.test_seed_demo tests.test_cierres` verde.
- Base temporal: `migrate`, `seed_demo`, `recompute --dry-run`: el numero de
  filas que reporta es el mismo antes y despues de la ficha (el seed escribe
  `clutch_vs` a mano y su feed ya difiere; anotar las dos cifras en
  `## Implementacion`).
- `/api/teammates/` sobre el seed: `clutch_silent` = el de arriba y
  `[(f["label"], f["silent"]) for f in clutch_conversion] == [("1v1", 1), ("1v2", 0)]`.
- `npm test`, `npm run build`, e2e verdes.

### Que puede romperse

- **Migracion sobre la base real**: corre en el primer `runserver`. Indices
  solo de `team_of` (`desde` sale de `vivos`), test con ronda sin jugadores.
  Si no corriera, todo ganado se veria silencioso (100 %): por eso el
  default 0 lleva comentario y la QA mira numeros creibles.
- **`recompute` con cambios eternos**: misma funcion y mismos `planos` que
  el import; test de idempotencia.
- **Numeracion contra la 79** (paso 2) y conflictos de contexto en
  `aggregates.py` (la 79 toca cerca de `clutch_conversion`), `views.py`,
  `metricas.md` y `humo.spec.js` (93).
- Tests que comparan dicts completos de `clutch_conversion`; el CSV
  `clutch-conversion` gana una columna al final.

### Verificar en el PC

Respaldo (`manage.py backup`); `migrate` (0005 o 0006, segundos);
`recompute --dry-run` sin filas de `clutch_kills` (si aparecen, migracion y
`recompute` no coinciden: no mergear); en Compañeros, Silenciosos con
numeros creibles (no 100 % en todas las filas), abrir dos rondas contadas
como silenciosas y ver en el feed que no hubo bajas tuyas despues de caer tu
ultimo compañero; un ganado de ataque con muerte post-plant figura como
silencioso; importar un replay con un clutch peleado y ver que no entra
como silencioso.

Skills: no aplica (tabla existente que gana una columna; migracion con llenado ya resuelta por la 0003; ningun dominio nuevo).
Arena: no (una forma razonable; las alternativas, booleano `clutch_silent` y calcular al consultar desde `Event`, quedaron descartadas en el consenso por denormalizar el resultado y por la regla "las metricas se calculan al importar").
OMC: plan=APPROVE (2 rondas; ronda 1 ITERATE: 1 MAJOR, el contrato de `clutch_kills` con todas las claves, y 4 MINOR; architect: el seed mostraba el caso raro, ahora el silencioso del seed es inferido del reloj) · revisión=— · verificación=—

## Implementacion

(Dev 20261106T0319Z-csweoG8, sobre `origin/dev@9ca7562`.)

Quedo el diseno completo, en el orden del plan:

- `metrics.py`: `_quedar_solo` (algoritmo de `clutch_vs` sin cambios, mas el
  indice del evento que deja solo), `clutch_vs` delega en el (firma y salida
  identicas; `test_clutch_vs_devuelve_lo_mismo_que_antes` y `ClutchVsTests`
  intactos) y `clutch_kills` nuevo, con una clave por nick de `team_of`.
- `RoundPlayer.clutch_kills`, migracion `0005_roundplayer_clutch_kills` (dev
  no trae todavia `0005_match_excluded`: queda `0005`; si la 79 entra antes,
  esta renumera a `0006`, y si entra despues, renumera la 79), `ingest.py`,
  `recompute.py` (`CAMPOS`) y el comando.
- `aggregates.py`: `silent`, `silent_pct`, `silent_low_sample` por fila y
  `silent` por lado en `clutch_conversion`; `clutch_silent` con el reparto por
  `win_condition`; `views.teammates` lo sirve.
- `seed_demo`: `CLUTCH_SILENCIOSO = 153` (demo-21 ronda 6, Bank, ataque,
  `ObjectiveOrTime` inferido). `/api/teammates/` sobre el seed:
  `clutch_silent = {"won": 2, "silent": 1, "silent_pct": 50.0, "by_condition": {"elimination": 0, "other": 1, "unknown": 0}}`
  y `[("1v1", 1), ("1v2", 0)]`.
- `recompute --dry-run` sobre el seed: 981 filas de jugador antes (dev) y
  despues (rama): el seed llena `clutch_kills` igual que el feed.
- `makemigrations --check --dry-run`: "No changes detected".
- Frontend: `clutchSilencioso.js` (+ vitest), columna "Silenciosos" al final
  de "Conversión por rivales" con `*` bajo 5 ganados, nota debajo y frase en
  el hint. e2e de Compañeros afirma la celda `1 (50%)` y la nota.
- `docs/metricas.md`: fila "Clutch silencioso" y la remision en la de
  conversion.

Tests con nombre por criterio: `ClutchKillsTests` (12), `ImportClutchTests`
(2 nuevos), `MigracionClutchKillsTests` (2), `ConversionTests` (5 nuevos y el
dict ajustado), `ClutchSilenciosoTests` (5), `RecomputeClutchKillsTests` (4) y
el ajuste de `ComandoTests.setUp` (`clutch_kills=1` en amigo y rival, el valor
del feed), 3 en `test_seed_demo.py`, 6 vitest.

Desvios del diseno:
- La nota usa "De tu único clutch ganado" con un solo ganado (en vez de "De
  tus 1 clutch ganado") y dice "en temporadas nuevas, inferido del reloj",
  como `metricas.md` (hallazgos LOW de la revision ciega).
- En el e2e el encabezado se busca como `cell` (el `DataTable` no expone
  `columnheader`).
- El factory `make_round_player` gana `clutch_kills` (default 0).

Revision ciega (`omc-code-reviewer`): 1 HIGH (dos E501 de ruff, ya
corregidos antes del informe) y 3 LOW: dos textos de la nota (arreglados) y la
migracion que da por bueno el `clutch_vs` guardado (documentado en su
docstring; `recompute` rehace los dos juntos).

Verificacion: `verificar.sh` VERDE d2809d2 (1069 tests backend, 257 vitest, 76 e2e).

Skills: no aplica (el diseno resolvia todo; ningun dominio nuevo).
Arena: no (sin puntos abiertos).
OMC: plan=— · revisión=4 hallazgos (4 arreglados o documentados) · verificación=—

## Para el humano

- (arquitecto ct6rosE, no bloquea) Un clutch ganado en el que moriste despues de quedar solo (plantaste y la defensa no desactivo) cuenta como silencioso, como dice la ficha. ¿Lo separamos del silencioso en el que sobreviviste? Hoy no; seria otra ficha.
- (arquitecto ct6rosE, P10, no bloquea) Siege.GG premia el clutch silencioso en su Rating. ¿Queres que pese en el nuestro? Cambiaria la formula de un numero que ya se muestra: no se toca sin tu decision.
- Si la 79 (PR #81) entra despues de esta, su migracion pasa a `0006_match_excluded` con dependencia `0005_roundplayer_clutch_kills` (o al reves si entra antes).
