# 80. Donde quedas fuera de posicion, por sitio y spawn

estado: en curso 2026-11-05
candado: dev 2026-11-05T04:18Z
rama: claude/equipo-dev/80-donde-quedas-fuera-de-posicion
tipo: funcionalidad
epica: posicionamiento
area: fullstack
prioridad: 3
fuente: ALCANCE.md S1, del PR #1 (`claude/loop-lwjbgs`, commit 1ffdb89: pedido del usuario "en que partes del mapa suelo dormir"), cerrado sin merge el 2026-11-05; el humano devolvio la idea a `idea`. La rama queda como referencia, no se mergea
archivos: backend/replays/analytics/aggregates.py (AGGREGATES, derive, positioning), backend/replays/analytics/coach.py (_posicion), backend/replays/views.py (positioning), backend/replays/urls.py, frontend/src/posicion.js, frontend/src/posicion.test.js, frontend/src/pages/Coach.jsx, docs/metricas.md, backend/tests/test_posicion.py, frontend/e2e/humo.spec.js
turnos: po 20261105T0230Z-c8Ahepa, arquitecto 20261105T0349Z-cfLc9Nn, dev 20261105T0418Z-cT3J25j

## PR

(La escribe el Release manager al final.)

## Que gana quien usa la app

Saber en que sitio (defensa) o desde que spawn (ataque) te agarran mal
parado: rondas en que moriste sin sacar ninguna baja y sin que nadie te
vengara. Es "donde duermo" al nivel que el `.rec` permite (zona, no
coordenadas), y el Coach lo dice con una señal cuando una zona se aparta de
tu historial.

## Criterios de aceptacion

- [ ] Metrica nueva `fuera_de_posicion` = rondas con `died=True`, `kills=0` y
      `was_traded=False` sobre rondas jugadas, en `AGGREGATES` (sale en todo
      agregado y en los CSV sin migracion ni `recompute`); test con una base
      de 4 rondas que cubre cada condicion por separado.
- [ ] `by_site` y `by_spawn` traen la tasa por zona y la del **resto** del
      historial (para un spawn, el resto del ataque), no la del total: test
      que fija que la zona no se compara consigo misma.
- [ ] Panel "Dónde quedas fuera de posición" con las dos tablas (sitio por
      lado, spawn de ataque) en Tendencias o en el Coach (decide el
      Arquitecto; **no** una pagina nueva de mapas y sitios: esa sigue
      descartada) con muestra minima y la nota "el .rec no trae
      coordenadas: la zona es el sitio o el spawn".
- [ ] Señales del Coach `zona-dormidero` (zona peor que el resto, fuera de la
      banda de ruido) y `zona-solida` (mejor), con muestra minima; test de
      cada una y de que no salen con poca muestra.
- [ ] Fila en `docs/metricas.md`; e2e: el panel se ve en la base sembrada y
      la consola queda limpia.

## Fuera de alcance

- Posiciones dentro del sitio, angulos o heatmap: el `.rec` no trae
  coordenadas (`CLAUDE.md`).
- Reabrir la pagina de mapas y sitios retirada en 096fd52.
- Salida del spawn y enlaces a peekabooR6: es S2, otra ficha.

## Diseno

Sin migracion y sin `recompute`: la metrica se arma de columnas que ya
existen (`died`, `kills`, `was_traded`). No toca parser, POST ni Electron, asi
que va sin consenso; una forma obvia, sin arena. Referencia: el commit
1ffdb89 de `claude/loop-lwjbgs` (PR #1, cerrado) resolvio lo mismo como
pagina propia; de ahi salen la regla "contra el resto" y la tabla de
`seed_demo`, que **ya trae** las rondas fuera de posicion por sitio
(`PERFIL`) pensadas para este e2e. No se mergea esa rama.

**Decisiones (todas reversibles, ninguna P10):**

1. **Panel en el Coach**, no en Tendencias (ya tiene unos 17 paneles) ni en
   una pagina nueva (descartada en `ALCANCE.md`). El Coach ya es "donde
   fallas" y la señal del criterio 4 vive ahi mismo. La pregunta del PO sigue
   en `## Para el humano`.
2. **Ajuste al criterio 3, "sitio por lado"**: la tabla de sitios junta los
   dos lados y el corte por lado lo da el filtro **Lado** de la barra (el
   Coach la muestra). Con Lado = Defensa la tabla es "tu setup" y el resto es
   el resto de tu defensa, sin codigo aparte. Partir cada sitio en dos filas
   deja la mitad de muestra por fila: con `seed_demo`, 12-17 rondas por fila
   y bandas de 14 puntos. Un sitio se juega mitad y mitad de cada lado, asi
   que compararlo contra el resto de todo no lo sesga por lado; un spawn si
   (solo existe en ataque, y en ataque quedas fuera de posicion mas seguido),
   por eso el spawn va contra el resto del **ataque**.
3. **Ajuste al criterio 2**: la tasa del resto no se agrega a `by_site` ni a
   `by_spawn`, que alimentan las reglas de winrate del Coach (`_sites`,
   `_spawns`) y el CSV, y cuyo "resto" depende de que filas entran. Va en una
   funcion nueva, `positioning()`. `by_site`/`by_spawn` igual ganan
   `caught_out_rounds` y `caught_out_pct` por venir de `AGGREGATES`.
4. **Margen de dos errores estandar.** El veredicto de una zona habla solo si
   `|diferencia| > 2 x _ruido(...)`. Progreso usa uno, pero alla se miran 10
   metricas fijas; aca hay una fila por sitio y spawn (20 o mas en un
   historial real) y con un error estandar un tercio de las zonas saldria
   marcado por azar. El numero que se muestra es ese margen (`margin`), no
   el error estandar, asi la columna y el veredicto dicen lo mismo.
   Calibrar con la base real del PC (ver Verificar en el PC).
5. **Definicion exacta del criterio 1**: `died=True, kills=0,
   was_traded=False`. No se usa `untraded_death` (es lo mismo al importar,
   `metrics.py:106`, pero una fila armada a mano en un test puede no traerla).

### Archivos y por que

1. **`backend/replays/analytics/aggregates.py`**
   - En `AGGREGATES`, despues de `clutch_rounds`:
     `"caught_out_rounds": Count("id", filter=Q(died=True, kills=0, was_traded=False))`,
     con comentario de una linea (moriste, no aportaste y nadie te vengo;
     ver `docs/metricas.md`). El alias no choca con ningun campo.
   - En `derive`: `"caught_out_pct": _pct(row.get("caught_out_rounds") or 0, rounds)`
     (sobre rondas y no sobre muertes: la pregunta es cada cuanto te pasa, y
     las rondas que sobreviviste cuentan). `caught_out_rounds` queda en la
     fila tal cual, como `kst_rounds`. `_fold` no necesita nada: suma los
     conteos y llama a `derive`.
   - Seccion nueva `# ---- posicion` (despues de `by_spawn`):
     - `POSICION_MIN_RONDAS = 5` (filas de la tabla; comentario: con menos,
       el margen se come cualquier diferencia).
     - `POSICION_BANDAS = 2` (comentario con el motivo de la decision 4).
     - `_contra_el_resto(filas, fuera_total, rondas_total) -> list[dict]`:
       por fila, `rest_rounds = rondas_total - rounds`,
       `rest_caught_out_pct = _pct(fuera_total - caught_out_rounds, rest_rounds)`,
       `caught_out_delta = _delta(caught_out_pct, rest_caught_out_pct)`,
       `margin = round(POSICION_BANDAS * se, 1)` con
       `se = _ruido(caught_out_pct, rounds, rest_caught_out_pct, rest_rounds)`
       (`None` si `se` es `None`), y `verdict`: `"dormidero"` si
       `delta > margin`, `"solido"` si `delta < -margin`, si no `"ruido"`
       (tambien con `delta` o `margin` en `None`). Docstring: contra el resto
       y no contra el total porque la zona esta dentro del total y la banda
       supone muestras independientes.
     - `positioning(min_rounds=POSICION_MIN_RONDAS, **filters) -> dict`:
       `qs = base_queryset(**filters)`, `baseline = rating_baseline()`.
       `sitios = _etiquetar(group_by(qs.exclude(round__site=""), *_MAPA,
       "round__site", labels=(*_MAPA_LABELS, "site"), min_rounds=min_rounds,
       baseline=baseline))`. `ataque = qs.filter(side="Attack")`;
       `spawns` igual sobre `ataque.exclude(spawn="")` con `"spawn"`.
       Totales con `qs.aggregate(rounds=Count("id"), caught_out_rounds=...)`
       (el mismo `Q`; sacarlo a una constante `_FUERA_DE_POSICION` y usarla
       tambien en `AGGREGATES`) para todo y para ataque. Devuelve
       `{"overall": {"rounds", "caught_out_rounds", "caught_out_pct"},
       "attack": {...igual...}, "sites": _contra_el_resto(sitios, total),
       "spawns": _contra_el_resto(spawns, ataque), "min_rounds": min_rounds,
       "bands": POSICION_BANDAS}`. Las filas de sitio y spawn **no se
       filtran** por veredicto: la tabla muestra tambien las de ruido.
       Orden: `caught_out_delta` descendente, `None` al final.
       `_ruido` y `_delta` estan mas abajo en el modulo: se resuelven al
       llamar, no hace falta moverlos.
2. **`backend/replays/views.py`**: vista `positioning` con `@require_GET`,
   `_ok(agg.positioning(min_rounds=_min_rounds(request, agg.POSICION_MIN_RONDAS), **_filters(request)))`.
   **`backend/replays/urls.py`**: `path("positioning/", views.positioning, name="positioning")`
   junto a `coach/`. Es GET de lectura: la lista de POST de `CLAUDE.md` no
   cambia.
3. **`backend/replays/analytics/coach.py`**: `POSICION_MIN_RONDAS_COACH = 8`
   (igual que sitio/spawn en la tabla de muestra minima) y
   `_posicion(**filters)`, llamada en `build_insights` despues de
   `_spawns`. Toma `agg.positioning(min_rounds=8, **filters)`, junta sitios
   (alcance `"{map} · {site}"`, zona `"{site} ({map})"`) y spawns (alcance
   `"{map} · {spawn} (ataque)"`, zona `"el spawn {spawn} ({map})"`), y solo
   redacta lo que ya trae `verdict` (la regla vive en `aggregates`):
   - `zona-dormidero`, severidad `media`, la de mayor `caught_out_delta`:
     titulo `"En {zona} te agarran fuera de posición el {pct:.0f}% de las rondas"`;
     detalle `"{rounds} rondas ahí, {delta:+.0f} puntos contra el {resto:.0f}% del resto de tu historial (margen ±{margin:.0f})."`
     (para un spawn: `"... del resto de tu ataque ..."`); accion
     `"Cambia dónde tomas el primer duelo en esa zona y juega más cerca de un compañero: morir sin aportar y sin que nadie te vengue es la muerte más cara."`;
     `metric="caught_out_pct"`, `value`, `baseline=rest_caught_out_pct`,
     `sample=rounds`, `scope`.
   - `zona-solida`, severidad `positivo`, la de menor delta:
     titulo `"En {zona} te sostienes"`; detalle
     `"{rounds} rondas con {pct:.0f}% fuera de posición, {abs(delta):.0f} puntos bajo el resto de tu historial."`;
     accion `"Fíjate qué haces distinto ahí (desde dónde miras, con quién juegas) y llévatelo a las zonas que te cuestan."`.
   - Una señal de cada tipo como mucho, como `_maps`.
4. **`frontend/src/posicion.js`** (nuevo), logica pura:
   - `VEREDICTOS = { dormidero: 'Te agarran más', solido: 'Te sostienes', ruido: 'Sin señal' }`
     y `etiquetaVeredicto(v)` (desconocido o `null` -> `'Sin señal'`).
   - `claseVeredicto(v)` -> `'loss'`, `'win'` o `''` (para el `chip`).
   - `hayZonas(datos)` -> hay alguna fila en `sites` o `spawns`.
   - `notaDeMuestra(datos)` -> `"Solo zonas con 5 rondas o más."` desde
     `min_rounds`.
5. **`frontend/src/posicion.test.js`** (nuevo, vitest):
   - `cada veredicto tiene su etiqueta`
   - `un veredicto desconocido no tiene señal`
   - `dormidero pinta en rojo y solido en verde`
   - `sin filas no hay zonas`
   - `con un spawn solo ya hay zonas`
   - `la nota de muestra usa el minimo de la api`
6. **`frontend/src/pages/Coach.jsx`**: segundo
   `useApi('/positioning/', filters)`; despues de los grupos de insights y
   antes de la nota final, `<Panel title="Dónde quedas fuera de posición"
   hint="Rondas en que moriste sin bajas y sin que nadie te vengara, por zona, contra el resto de tu historial.">`:
   - `<p className="note">El .rec no trae coordenadas: la zona es el sitio de bomba o el spawn de ataque. {notaDeMuestra(...)} Usa el filtro Lado para ver solo tu defensa o tu ataque.</p>`
   - Dos `DataTable` con `<h3>`: **Sitios** (`csvName="fuera-de-posicion-sitios"`)
     y **Spawns de ataque** (`csvName="fuera-de-posicion-spawns"`).
     Columnas: Mapa (`map`, left), Sitio/Spawn (left), Rondas,
     Fuera de posición (`caught_out_pct`, `fmt(v, 0, '%')`), Resto
     (`rest_caught_out_pct`, mismo formato; help "El mismo porcentaje en el
     resto de tus rondas; para un spawn, el resto de tu ataque."),
     Diferencia (`caught_out_delta`, con signo y un decimal: `+33.5`),
     Margen (`margin`, `±13.8`, dim, help "Dos errores estándar de la
     diferencia. Con muchas zonas, una diferencia menor que esto sale sola
     por azar."), Veredicto (`chip` con `claseVeredicto` y
     `etiquetaVeredicto`). `initialSort` por `caught_out_delta` desc.
   - Sin zonas (`!hayZonas`): solo la nota y
     `"Todavía no hay zonas con 5 rondas."`. Error del fetch:
     `<ErrorBox>` dentro del panel; el resto del Coach sigue.
   - De paso, la nota final del Coach suma "5 por zona en la tabla de
     posición". No se tocan otros textos (eso es la 81).
7. **`backend/tests/test_posicion.py`** (nuevo), con `factories`
   (`make_match`, `make_round`, filas `is_me` a mano con `died`, `kills`,
   `was_traded`, `side`, `spawn`, `round.site`):
   - `test_fuera_de_posicion_exige_morir_sin_bajas_y_sin_trade`: 4 rondas,
     una por condicion (muere 0 bajas sin trade; muere con 1 baja; muere 0
     bajas tradeado; sobrevive 0 bajas) -> `caught_out_rounds == 1`,
     `caught_out_pct == 25.0` en `/api/overview/`.
   - `test_fuera_de_posicion_sale_en_el_csv`: `/api/export/?table=sites`
     trae la columna `caught_out_pct`.
   - `test_la_zona_se_compara_contra_el_resto_y_no_contra_el_total`: sitio
     A con 10 rondas y 8 fuera, sitio B con 10 y 2 -> en A
     `rest_caught_out_pct == 20.0` (no 50.0) y `rest_rounds == 10`.
   - `test_el_spawn_se_compara_contra_el_resto_del_ataque`: rondas de
     defensa todas fuera de posicion no cambian el `rest_caught_out_pct` de
     ningun spawn.
   - `test_una_diferencia_dentro_del_margen_es_ruido` y
     `test_dormidero_y_solido_segun_el_signo` (con muestras armadas para que
     el delta pase o no `2 x _ruido`; afirmar `margin` contra el calculo a
     mano).
   - `test_una_zona_bajo_el_minimo_no_sale` (4 rondas, `min_rounds` 5).
   - `test_el_filtro_de_lado_deja_el_resto_del_mismo_lado`:
     `?side=Defense` -> `rest_rounds` cuenta solo rondas de defensa.
   - `test_sin_rondas_no_da_500`: base vacia -> 200, listas vacias,
     `caught_out_pct` `None`.
   - Coach: `test_zona_dormidero_sale_con_muestra`,
     `test_zona_solida_sale_con_muestra`,
     `test_sin_muestra_no_hay_senal_de_zona` (7 rondas por zona),
     `test_una_zona_en_ruido_no_da_senal`.
8. **`frontend/e2e/humo.spec.js`**, test nuevo `el Coach muestra dónde
   quedas fuera de posición`, con `vigilarConsola`. Numeros de `seed_demo`
   (calculados en el diseno replicando `_plan`/`_ronda`; 203 rondas, 118
   fuera de posicion, 116 de ataque con 66 fuera):

   | zona | rondas | fuera | resto | dif. | margen | veredicto |
   |---|---|---|---|---|---|---|
   | Club House · B Church, B Arsenal Room | 40 | 85% | 51.5% | +33.5 | ±13.8 | dormidero |
   | Border · A Ventilation, A Workshop | 28 | 25% | 63.4% | -38.4 | ±18.0 | solido |
   | Club House · A Bedroom, A Gym | 30 | 56.7% | 58.4% | -1.7 | ±19.6 | ruido |
   | Bank · A Vault, A Gold Partition | 4 | - | - | - | - | no sale |
   | spawn Club House · Warehouse | 20 | 80% | 52.1% | +27.9 | ±20.6 | dormidero |
   | spawn Border · Valley | 20 | 40% | 60.4% | -20.4 | ±24.0 | ruido (con 1 error estandar seria solido) |

   El test afirma: el `h2`/titulo del panel; la fila "B Church, B Arsenal
   Room" con `85%` y "Te agarran más"; "A Ventilation, A Workshop" con
   `25%` y "Te sostienes"; "A Vault, A Gold Partition" en 0 filas; en
   spawns, "Warehouse" con `80%` y "Te agarran más" y "Valley" con
   "Sin señal"; las señales del Coach con los titulos
   `En B Church, B Arsenal Room (Club House) te agarran fuera de posición el 85% de las rondas`
   y `En A Ventilation, A Workshop (Border) te sostienes`; consola limpia.
   Si un numero no coincide, el Dev recalcula sobre la base sembrada
   (`manage.py seed_demo` y `/api/positioning/`) antes de tocar el codigo:
   la tabla de arriba es una simulacion, no una corrida.
9. **`docs/metricas.md`**:
   - Fila nueva en la tabla de `## Trades`, debajo de "Muerte sin trade":
     `| **Fuera de posición** | Rondas en que moriste, sin bajas y sin que nadie te vengara / rondas jugadas. Es "te agarraron mal parado": morir peleando (con una baja) o morir y que te venguen no cuenta. |`
   - En `## Sobre la granularidad espacial`, un parrafo: la tabla "Dónde
     quedas fuera de posición" del Coach compara cada sitio contra el resto
     de tus rondas y cada spawn contra el resto de tu ataque; el veredicto
     solo habla si la diferencia pasa dos errores estandar (y por que dos).
   - En `## Muestra minima`: fila `| Zona fuera de posición | 5 rondas en la tabla, 8 para la señal del Coach |`.

### Orden de implementacion

1. `AGGREGATES`/`derive` + test de las cuatro condiciones; correr la suite
   (ver "Que puede romperse").
2. `positioning`, vista y url, con los tests de zona.
3. `coach._posicion` y sus tests.
4. `posicion.js` + vitest; `Coach.jsx`; `npm run build`.
5. `seed_demo` + `runserver`: comparar `/api/positioning/` con la tabla de
   arriba; e2e; `docs/metricas.md`; `check.sh` con `verificar.sh`.

### Que puede romperse

- **Columnas de los CSV**: `AGGREGATES` suma `caught_out_rounds` y
  `caught_out_pct` a todo export por agregado. `test_export.py:130` lee la
  cabecera: si compara una lista exacta, se actualiza sumando las dos
  columnas (no se saca ninguna).
- **Tests del Coach**: una base de test con zonas muy distintas puede ganar
  una señal nueva; los tests buscan por `key`, asi que no deberian romper.
  `test_coach.py:205` mira el orden por severidad, que se mantiene.
- **Rendimiento del Coach**: `positioning` hace tres consultas mas por
  request (dos `group_by` y dos `aggregate`); en el orden de las que ya hace.
- **Choque con otras fichas**: la 78 agrega `match_queryset` en
  `aggregates.py` y toca `match_list`; la 79 toca `base_queryset` y
  `views.py`. Son zonas distintas del archivo: si alguna entra antes, el
  merge con `dev` es mecanico. Ninguna agrega migracion por esta ficha.

### Verificacion manual

`seed_demo`, `runserver`, Coach: el panel con las dos tablas y la tabla de
arriba; Lado = Defensa en la barra: la fila de B Church sigue dormidero (88%,
17 rondas) y Valley desaparece de spawns (no hay ataque); Lado = Ataque: los
sitios se comparan contra el resto del ataque.

Skills: no aplica (tablas, `DataTable` y señales del Coach ya existen; no es
un dominio nuevo).
OMC: plan=— · revisión=— · verificación=— (sin parser, migracion, recompute ni POST: sin consenso)

## Verificar en el PC

- Con la base real: cuantas zonas salen `dormidero`/`solido` con
  `POSICION_BANDAS = 2`. Si no sale ninguna con cientos de rondas, bajar a
  1.5 es cambiar una constante; si salen mas de un tercio, el margen es poco.

## Implementacion

## Revision

## QA

## Para el humano

- (po) El PR #1 lo hacia como pagina propia "Posicionamiento". La variante
  conservadora es un panel en una pagina existente, porque "Pagina de mapas y
  sitios" esta descartada en `ALCANCE.md` desde que se retiro (096fd52). Si
  queres la pagina propia, decilo en la ficha.
- (arquitecto) Disenado como panel del Coach. Dos ajustes reversibles: el
  corte por lado de los sitios lo da el filtro Lado de la barra (no dos filas
  por sitio, que parten la muestra), y el veredicto exige dos errores
  estandar (con 20 zonas, uno marca un tercio por azar). Si preferis otra
  cosa, es tocar `Coach.jsx` o la constante `POSICION_BANDAS`.
