# 90. Stacks rivales repetidos

estado: en curso 2026-11-05
candado: dev 2026-11-05T19:45Z
rama: claude/equipo-dev/90-stacks-rivales-repetidos
tipo: funcionalidad
epica: rivales
area: fullstack
prioridad: 3
fuente: D4 de ALCANCE.md; `replica/features.csv` "Historial contra un equipo rival concreto" (should, partial: la referencia lo tiene por equipo y la app solo por persona, D1 en dev)
archivos: backend/replays/analytics/aggregates.py (repeated_rivals, rival_stacks nueva), backend/replays/views.py (duels), frontend/src/pages/Duelos.jsx, backend/tests/test_stacks_rivales.py, frontend/e2e/stacks-rivales.spec.js, docs/metricas.md
turnos: po 20261105T1759Z-cCJ5erc, arquitecto 20261105T1920Z-cAaALb8, dev 20261105T1945Z-ceRZh1z

## PR

(La escribe el Release manager al final.)

## Que gana quien usa la app

En Duelos, debajo de "Rivales repetidos", los grupos de 2 o mas rivales que
te tocaron juntos en el mismo equipo en 2 o mas partidas, con tu record
contra cada grupo: reconocer al stack que ya te gano, no solo a la persona.
Solo gente de tus replays; no es scouting ni consulta a nadie.

## Criterios de aceptacion

- [ ] `GET /api/duels/` trae `rival_stacks`: una fila por conjunto de
      jugadores rivales (agrupados por `Player`, no por nick, como
      `repeated_rivals`) que estuvieron juntos en el equipo contrario en al
      menos `min_matches` (2 por defecto) de tus partidas filtradas, con
      `players` (id y nick), `matches`, `wins`, `losses` y `winrate` (las
      partidas sin resultado fuera del winrate). Test con tres partidas
      armadas a mano.
- [ ] El grupo es el mas grande que se repite: si A, B y C te tocaron juntos
      en dos partidas, sale la fila A+B+C y no tambien A+B, A+C y B+C con las
      mismas partidas; A+B sale aparte solo si suma partidas que A+B+C no
      tiene. Test.
- [ ] El equipo se lee por ronda como en `repeated_rivals`: un jugador que
      fue companero en una partida y rival en otra solo cuenta en la segunda.
      Respeta los filtros globales (test con filtro de mapa).
- [ ] En Duelos, un panel "Stacks rivales repetidos" con los nicks enlazados
      al perfil de cada jugador y el record; sin filas, dice que ningun grupo
      se repitio con esos filtros.
- [ ] Fila en `docs/metricas.md` y caso en el e2e (`frontend/e2e/`) con un
      numero de `seed_demo` afirmado (si el seed no tiene ningun stack
      repetido, el Arquitecto decide si el seed suma uno y que numeros del e2e
      cambian).

## Fuera de alcance

- Nombres de equipo o clan: el `.rec` no los trae.
- Stats de esos rivales fuera de tus partidas (API de Ubisoft): no.
- Stacks de tus companeros (eso es C1, otra idea).

## Diseno

(Arquitecto 20261105T1920Z-cAaALb8, sobre `origin/dev@4a1aa8e`.)

**Implementar despues de que #89 y #91 se mergeen** (prioriza, no bloquea):
las dos tocan `aggregates.py` y la 91 tambien `views.py`. Los choques serian
de contexto, no de logica: esta ficha agrega una funcion al lado de
`repeated_rivals` y una clave al dict de `duels`. Para no pelear por
`frontend/e2e/humo.spec.js` (lo tocan 89 y 91), el e2e va en un archivo
nuevo. La 79 (excluir partidas) no se pisa: `base_queryset` filtra lo
excluido y esta ficha lo hereda sin tocar nada.

**Ajuste al criterio del panel:** el titulo es **"Stacks rivales que se
repiten"**, no "Stacks rivales repetidos". En Playwright `hasText` con string
es substring sin distinguir mayusculas: `section.panel` con
`hasText: 'Rivales repetidos'` (dos tests de `humo.spec.js`) encontraria dos
paneles y `expect(panel).toBeVisible()` fallaria por modo estricto. Con este
titulo los locators viejos siguen unicos y no hay que tocar `humo.spec.js`.

### Backend: `backend/replays/analytics/aggregates.py`

1. Extraer de `repeated_rivals` (hoy `aggregates.py:2250`) el cruce a un
   helper privado, sin cambiar su comportamiento:

   ```python
   def _rivales_por_partida(me_ids: list[int], **filters) -> dict[int, set[int]]:
       """match_id -> Player.id de quienes estuvieron en el equipo contrario
       en al menos una de tus rondas filtradas de esa partida."""
   ```

   Es el mismo queryset `cruces` (`Exists(mine...)`,
   `exclude(player_id__in=me_ids)`, `_MI_EQUIPO`,
   `exclude(team_index=F("mi_equipo"))`,
   `values_list("player_id", "round__match_id").distinct()`), acumulado por
   partida. `repeated_rivals` lo invierte (`pid -> set(match_ids)`) y
   devuelve exactamente lo mismo que hoy: `test_duels.py` es la red de ese
   refactor y no se toca.

2. Funcion nueva, justo debajo de `repeated_rivals`:

   ```python
   def rival_stacks(min_matches: int = 2, **filters) -> list[dict]:
   ```

   Algoritmo (conjuntos cerrados; spike en el scratchpad con los casos de
   los tests, da lo esperado):

   - `por_partida = _rivales_por_partida(me_ids, **filters)`; sin `me_ids`
     o sin partidas, `[]`.
   - Para cada partida, cada subconjunto de 2 o mas de sus rivales
     (`itertools.combinations(sorted(rivales), k)`, k de 2 a len) suma esa
     partida a `soporte[frozenset(subconjunto)]`. Una partida tiene 5
     rivales (algo mas si entra un reemplazo): 26 subconjuntos, ~250 en el
     peor caso real; no hace falta poda.
   - Quedan los subconjuntos con `len(soporte[s]) >= min_matches`.
   - **El grupo es el mas grande que se repite:** por cada conjunto de
     partidas (`frozenset(soporte[s])`) queda solo el subconjunto mas grande
     con exactamente esas partidas. Es unico (es la interseccion de los
     rivales de esas partidas), asi que
     `mejor[frozenset(partidas)] = max(actual, s, key=len)` lo resuelve en
     una pasada. Con A+B+C en las partidas 1 y 2 y A+B tambien en la 3 salen
     dos filas (A+B suma la 3); con A+B+C en 1 y 2 y nada mas, solo A+B+C.
   - Resultado de cada partida:
     `dict(Match.objects.filter(id__in=...).values_list("id", "won"))`, una
     consulta como en `repeated_rivals`. Nicks: `Player.username`, una
     consulta.
   - Fila:

     ```python
     {
         "players": [{"player_id": pid, "username": nick}, ...],  # por username
         "size": len(grupo),
         "matches": len(partidas),
         "wins": ..., "losses": ...,
         # las partidas sin resultado no ensucian el winrate
         "winrate": _pct(wins, wins + losses),
     }
     ```

   - Orden: `(-matches, -size, -losses, ", ".join(nicks))`. Determinista,
     asi el e2e no depende del orden de un dict.

### Vista: `backend/replays/views.py`, `duels`

Leer `min_matches` una vez en una variable (`_int_param(request,
"min_matches", 2, minimum=1, maximum=1000)`) y pasarla a `repeated_rivals` y
a la clave nueva, al lado de `"rivals"`:

```python
"rival_stacks": agg.rival_stacks(min_matches=min_matches, **filters),
```

Ni URL nueva ni POST.

### Frontend: `frontend/src/pages/Duelos.jsx`

- `const stacks = data.rival_stacks ?? []` junto a `rivals`.
- Panel nuevo **debajo** de "Rivales repetidos", mismo patron:
  `title="Stacks rivales que se repiten"`, `hint`: "Grupos de 2 o más
  rivales que te tocaron juntos en el equipo contrario en 2 o más partidas.
  Si el grupo entero se repite, sale una sola fila con todos; un grupo más
  chico sale aparte solo si suma partidas propias. El replay no trae nombres
  de equipo: es solo coincidencia de personas."
- `DataTable` con columnas:
  - `players`, label `Rivales`, `left`, `sortable: false`: los nicks como
    `<Link to={`/jugadores/${p.player_id}`}>` separados por ` · ` (un
    `React.Fragment` con `key={p.player_id}`); `csv: (row) =>
    row.players.map((p) => p.username).join(' + ')` (sin `csv:` la celda
    sale vacia, como paso con `record`).
  - `size` (`Juntos`), `matches` (`Partidas`), `wins` (`Ganadas`),
    `losses` (`Perdidas`), `record` (`Récord`, igual que en Rivales
    repetidos, con `render`, `csv` y `sortable: false`), `winrate`
    (`Winrate`, mismo `help` que el panel de arriba).
  - `rowKey={(row) => row.players.map((p) => p.player_id).join('-')}`,
    `initialSort={{ key: 'matches', dir: 'desc' }}`,
    `csvName="stacks-rivales"`,
    `empty="Ningún grupo de rivales se repitió en 2 o más partidas con estos filtros."`
- Textos de la UI con tildes; codigo y comentarios sin.

### Tests: `backend/tests/test_stacks_rivales.py` (nuevo)

Con `tests/factories.py` y el mismo armado de rondas con rivales en
`team_index` contrario que ya usa `test_duels.py` para `repeated_rivals`.

- `test_tres_rivales_juntos_en_dos_partidas_dan_una_sola_fila`: A, B, C
  rivales en las partidas 1 y 2 (mas un rival distinto en cada una): sale
  solo A+B+C con `matches=2` y `size=3`; ni A+B, ni A+C, ni B+C.
- `test_un_grupo_mas_chico_sale_aparte_si_suma_partidas_propias`: A+B+C en
  1 y 2, A+B (sin C) en la 3: dos filas, A+B con 3 primero, A+B+C con 2.
- `test_el_record_deja_las_partidas_sin_resultado_fuera_del_winrate`: el
  mismo grupo en tres partidas con `won` True, False y None: `matches=3`,
  `wins=1`, `losses=1`, `winrate=50.0`.
- `test_un_companero_que_fue_rival_solo_cuenta_donde_fue_rival`: A y B
  rivales en 1 y 2; en la 3 A es companero (tu `team_index`) y B rival: la
  fila A+B tiene `matches=2`.
- `test_respeta_el_filtro_de_mapa`: el grupo en dos partidas de un mapa y
  una de otro; filtrando por el primero sale con `matches=2`, por el
  segundo no sale.
- `test_sin_grupos_repetidos_devuelve_lista_vacia`: rivales distintos en
  cada partida.
- `test_la_api_de_duelos_trae_rival_stacks`: `GET /api/duels/` con el caso
  del primer test trae la fila; con `min_matches=3`, lista vacia.

Si `grep -n repeated_rivals backend/tests` no muestra cobertura directa de
`repeated_rivals` (hoy la hay en `test_duels.py`), el Dev agrega un test que
fije su salida antes del refactor.

### e2e: `frontend/e2e/stacks-rivales.spec.js` (nuevo)

`seed_demo` ya trae un stack: `_ronda` pone `rivales[:3]` (Thorn.exe, Kaid_ y
Mozzie99) en el equipo contrario de **todas** las rondas, y las 29 partidas
las ganas (medido sobre `origin/dev` con el seed en una base del
scratchpad: `repeated_rivals` da los tres con 29 partidas y 29-0, 29 `won`
True). El seed no cambia y ningun numero de otros e2e se mueve.

- `test('Duelos muestra el stack rival del seed con su récord')`:
  `vigilarConsola`, `/duelos`, `section.panel` con
  `hasText: 'Stacks rivales que se repiten'`, **una** fila en `tbody`; tres
  enlaces con `href` `/jugadores/\d+` y textos `Kaid_`, `Mozzie99`,
  `Thorn.exe`; la fila contiene `29` y `29-0`; click en el primer enlace
  lleva a `/jugadores/\d+`. `errores` vacio.
- Fila esperada del endpoint: `size=3`, `matches=29`, `wins=29`,
  `losses=0`, `winrate=100.0`.

### `docs/metricas.md`, tabla de `## Duelos`

Fila nueva despues de **Récord contra un rival**:

| **Stack rival repetido** | Grupo de 2 o mas personas (por profileID) que estuvieron juntas en el equipo contrario en al menos una de tus rondas filtradas de N partidas distintas, desde 2. Se muestra el grupo mas grande con esas partidas: si A, B y C se repiten juntos, no salen tambien A+B, A+C y B+C con las mismas partidas; un grupo mas chico sale aparte solo si suma alguna partida que el grande no tiene. Record y winrate como en **Récord contra un rival**. El `.rec` no trae nombre de equipo ni de clan: el grupo es solo coincidencia de personas. Página Duelos, panel *Stacks rivales que se repiten*. |

### Orden de implementacion

1. Helper `_rivales_por_partida` y `repeated_rivals` encima de el; correr
   `test_duels`.
2. `rival_stacks` y `test_stacks_rivales.py`.
3. Clave en `duels` y su test de API.
4. Panel en `Duelos.jsx`, `npm run build`.
5. e2e nuevo, fila de `metricas.md`, `verificar.sh`.

### Que puede romperse

- El refactor de `repeated_rivals`: si cambia el `distinct()` o el orden,
  cambia el panel que ya existe. Por eso va primero y con su test en verde.
- Los locators de `humo.spec.js` sobre "Rivales repetidos" si el titulo
  nuevo contuviera ese texto (ver el ajuste de arriba).
- `DataTable` con una celda que es lista de enlaces: `sortable: false` y
  `csv:` obligatorios.
- Volumen: ~26 subconjuntos por partida en memoria; con mil partidas, unas
  decenas de miles de claves. No hace falta SQL.

### Verificacion manual

Con `seed_demo`: Duelos muestra una fila "Kaid_ · Mozzie99 · Thorn.exe",
Juntos 3, Partidas 29, Récord 29-0. Con el filtro de un mapa, Partidas baja
a las partidas de ese mapa. Con la base real: en ranked casi no hay stacks
repetidos; con amigos de rival o en partidas sin ranked, si.

Sin umbral que calibrar: el minimo de 2 partidas es el de Rivales repetidos
y comparte su `min_matches`.

Skills: no aplica (tabla nueva en un `Panel` con `DataTable`, patron que el
repo ya resuelve; sin dominio nuevo, no se busco skill de afuera).

OMC: plan=— · revisión=— · verificación=— (ficha chica y de una forma obvia:
sin plan por consenso, segun `roles/arquitecto.md`)

## Implementacion

(Dev)
