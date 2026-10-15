# 46. Primero de tu equipo en caer

estado: en curso 2026-10-15
candado: dev 2026-10-15T06:11Z
rama: claude/equipo-dev/46-primero-de-tu-equipo-en-caer
tipo: funcionalidad
epica: escuadra
area: fullstack
prioridad: 3
fuente: ALCANCE.md C4 (idea del PO); abre la epica escuadra (C1-C5 libres)
archivos: backend/replays/analytics/aggregates.py, backend/replays/views.py, backend/tests/test_primero_en_caer.py, frontend/src/pages/Teammates.jsx, frontend/e2e/humo.spec.js, docs/metricas.md
turnos: po 20261014T1911Z, arquitecto 20261014T2311Z, dev 20261015T0611Z

## PR

(La escribe el Release manager al final.)

## Que gana quien usa la app

Hoy la app cuenta tu "primera muerte" solo cuando eres la primera baja de
toda la ronda. Con esto ves cuantas rondas eres el primero de tu equipo en
caer (aunque ya haya muerto un rival) y el winrate de esas rondas contra
las que cae primero un compañero, por lado: si tu forma de abrir le cuesta
rondas al equipo.

## Criterios de aceptacion

- [ ] Agregado nuevo (p. ej. `first_teammate_death` en `aggregates.py`)
      que, por ronda con al menos una muerte de tu equipo, decide quien
      cayo primero de tu equipo comparando `RoundPlayer.death_elapsed` de
      las filas con tu `team_index`. Devuelve por lado (`Attack`,
      `Defense`, total): rondas en que caiste primero, rondas en que cayo
      primero un compañero, rondas sin muertes de tu equipo, y el winrate
      de ronda de cada grupo.
- [ ] Una ronda donde murio primero un rival y despues tu, antes que tus
      compañeros, cuenta como "caiste primero" aunque `opening_death` sea
      falso. Test con esa ronda exacta.
- [ ] Empate de `death_elapsed` entre tu y un compañero (mismo segundo):
      la regla queda escrita en el diseno y tiene test. Filas con
      `death_elapsed` nulo (no moriste) nunca cuentan como primera muerte.
- [ ] Sale en `/api/teammates/` (o el endpoint que fije el diseno) y
      respeta los filtros de la barra; base vacia y filtros raros dan 200.
- [ ] La pagina Compañeros muestra un panel "Primero en caer" con la tabla
      por lado; el e2e lo afirma sobre `seed_demo`.
- [ ] Fila en `docs/metricas.md` ("Primero de tu equipo en caer" y su
      winrate), distinguiendola de "Primera muerte" de la ronda.

## Fuera de alcance

- Desglose por compañero (quien cae primero mas seguido): puede ser el
  siguiente tramo de la epica escuadra.
- Cambiar la definicion de `opening_death`: se queda como esta (P10).
- Abandonos (`PLAYER_LEAVE`) como caso aparte: cuentan como muerte, igual
  que en `stats.py`, sin desglose (eso es D3).

## Diseno

Arquitecto 20261014T2311Z, sobre `origin/main@f74a16f`. Pasa los filtros
duros: usa `RoundPlayer.death_elapsed`, `team_index`, `side`, `won` e
`is_me` (ya calculados al importar por `metrics.analyse_round`) y, solo
para desempatar, `Event.order`. Sin migracion, sin recompute, sin cambiar
`opening_death` (P10 respetado).

**Regla** (va igual en el docstring y en `docs/metricas.md`): en cada
ronda tuya, se miran las filas de tu equipo (misma `round_id` y
`team_index` que tu fila) con `death_elapsed` no nulo.
- Ninguna: la ronda va a `sin_muertes` ("tu equipo no perdio a nadie" o
  no hay tiempo registrado).
- La menor `death_elapsed` es la tuya y nadie de tu equipo la tiene igual:
  `caiste_primero`.
- La menor es de un compañero (estrictamente menor que la tuya, o vos no
  moriste): `cayo_companero`.
- **Empate** (tu `death_elapsed` igual a la menor de un compañero): decide
  el orden del feed. Se busca el primer evento de muerte de cada uno
  (`Event.kind == "Kill"` con `target_id` = jugador, o `kind == "Death"`
  con `actor_id` = jugador; el de menor `order`), igual que
  `metrics.analyse_round` elige la muerte de cada jugador. Menor `order`
  cayo primero. Si falta el evento de alguno, el empate se resuelve a
  favor del compañero (`cayo_companero`): la regla conservadora no te
  carga una muerte que no se puede probar. Solo se consultan eventos de
  las rondas empatadas (el elapsed sale del reloj en segundos y los
  dobles kills empatan seguido, asi que no es un caso raro, pero son
  pocas rondas).

**Backend: `backend/replays/analytics/aggregates.py`**, funcion nueva
`first_teammate_death(**filters) -> list[dict]` debajo de
`teammate_synergy`:
1. `mias = base_queryset(**filters)` y una query de tu equipo en esas
   rondas: `RoundPlayer.objects.filter(Exists(mias.filter(round_id=
   OuterRef("round_id"), team_index=OuterRef("team_index"))))
   .values("round_id", "player_id", "is_me", "death_elapsed")` (el mismo
   `Exists` correlacionado que `teammate_synergy`, por el tope de
   parametros de SQLite). Tus filas: `mias.values("round_id", "side",
   "won")`.
2. Agrupar en Python por `round_id`; clasificar con la regla de arriba en
   un helper puro `_quien_cae_primero(mi_elapsed, elapsed_companeros) ->
   "me" | "mate" | "none" | "tie"`; los `"tie"` se resuelven con una
   query de `Event` filtrada por esos `round_id` (`kind__in=(Event.KILL,
   Event.DEATH)`, `.values("round_id", "order", "kind", "actor_id",
   "target_id")`).
3. Salida, filas en orden fijo `LADOS_PRIMERA_CAIDA = ("Attack",
   "Defense", "total")`, cada una: `{"side", "rounds", "me_first",
   "me_first_won", "me_first_winrate", "mate_first", "mate_first_won",
   "mate_first_winrate", "no_deaths", "no_deaths_won",
   "no_deaths_winrate"}` con `_pct`. El lado es el de tu fila
   (`RoundPlayer.side`, el mismo que usa `?side=`); una fila sin lado
   cuenta solo en `total`. Ganada = `RoundPlayer.won` de tu fila, como
   `teammate_synergy`.

**`backend/replays/views.py`**: `"first_down": agg.first_teammate_death(
**filters)` en `teammates`. No respeta `min_rounds` (es un total tuyo, no
por compañero).

**Frontend: `frontend/src/pages/Teammates.jsx`**: `Panel` "Primero en
caer" despues de "Sinergia", con `DataTable` de tres filas (Ataque,
Defensa, Total; `SideChip` en las dos primeras) y columnas "Rondas",
"Caíste primero" (n y % de las rondas), "Winrate", "Cayó un compañero",
"Winrate", "Sin bajas", "Winrate". Hint: "Primero de tu equipo, no de la
ronda: si ya había caído un rival, sigue contando. Distinto de «Primera
muerte» de Duelos." Sin rondas (`total.rounds === 0`): texto "Sin rondas
con estos filtros." El % de "Caíste primero" sobre las rondas se calcula
en el componente con `pct` de `ui.jsx`; no hace falta modulo de logica
aparte.

**Tests nuevos** en `backend/tests/test_primero_en_caer.py`:
- `test_caiste_primero_aunque_antes_muriera_un_rival` (rival muere a los
  20 s, vos a los 30, compañero a los 50; `opening_death=False`: cuenta
  `me_first`)
- `test_cayo_primero_un_companero`
- `test_ronda_sin_muertes_de_tu_equipo`
- `test_no_moriste_y_murio_un_companero_es_companero`
- `test_elapsed_nulo_nunca_es_primera_muerte` (tu `death_elapsed=None`
  con `died=True`, compañero con tiempo: `mate_first`)
- `test_empate_lo_decide_el_orden_del_feed` (dos casos: tu evento con
  menor `order` -> `me_first`; mayor -> `mate_first`)
- `test_empate_sin_eventos_va_al_companero`
- `test_los_rivales_no_cuentan_como_companeros` (fila con otro
  `team_index` y menor elapsed)
- `test_separa_por_lado_y_suma_el_total`
- `test_winrate_por_grupo`
- `test_teammates_trae_first_down_con_base_vacia` (200, tres filas en 0)
  y `test_teammates_con_filtros_raros_da_200` (`until=foo`, `session=-1`,
  `side=Attack`).
Ojo con `make_round_player`: `death_elapsed` por defecto es `60.0`, hay
que pasar `None` explicito para "no murio".

**e2e** (`frontend/e2e/humo.spec.js`): `test('Compañeros muestra quien cae
primero', ...)` sobre `/companeros`: titulo del panel y la fila Total con
el numero de rondas que de `curl /api/teammates/ | jq .first_down` sobre
`seed_demo` (sembrado tiene compañeros con `death_elapsed` y eventos). No
tocar `seed_demo`.

**`docs/metricas.md`**: dos filas en `## Duelos de apertura`, debajo de
"Entry kill": **Primero de tu equipo en caer** (la regla de arriba,
incluido el empate, y la diferencia con la primera muerte de la ronda) y
**Winrate cuando caes primero / cuando cae un compañero**.

**Orden:** helper puro + tests -> agregado -> vista -> panel -> e2e ->
metricas.md -> `check.sh`.

**Que puede romperse:** nada persistente. Abandonos (`PLAYER_LEAVE`)
entran como muerte si `metrics` les puso `death_elapsed`; sin desglose
(fuera de alcance). Si la ficha 45 se mergea antes, conflicto trivial en
`aggregates.py`/`views.py`/`humo.spec.js` (funciones distintas, mismo
archivo): lo resuelve P3.

**Verificacion manual:** `seed_demo`, `runserver`, `/companeros`; en la
base real, abrir una ronda contada como "caiste primero" en el detalle de
la partida y confirmar en el feed que fuiste la primera baja de tu equipo.

## Implementacion

## Revision

## QA

## Para el humano
