# 41. Rondas segun el marcador: adelante, empatado o atras

estado: disenado
candado: -
rama: -
tipo: funcionalidad
epica: lado-y-marcador
area: fullstack
prioridad: 3
fuente: ALCANCE.md B2 (rondas bajo presion), primer tramo; el match point queda para el segundo
archivos: backend/replays/analytics/aggregates.py, backend/replays/views.py, backend/replays/management/commands/seed_demo.py, backend/tests/factories.py, frontend/src/pages/Trends.jsx, docs/metricas.md, backend/tests/test_marcador.py, frontend/e2e/humo.spec.js
turnos: po 20261013T1915Z, arquitecto 20261013T2011Z

## PR

(La escribe el Release manager al final.)

## Que gana quien usa la app

Ver como rindes segun como va la partida antes de la ronda: yendo adelante,
empatado o atras en el marcador. Es la mitad de "rondas bajo presion" que no
depende de las reglas de cada modo, asi que sirve igual en ranked, unranked o
rapida.

## Criterios de aceptacion

- [ ] `GET /api/trends/` devuelve `by_score_state`: cuatro filas en orden fijo
      `ahead`, `tied`, `behind`, `unknown`, con las metricas de `totals()`.
      El estado sale de `Round.score_before` (`[equipo0, equipo1]`, de
      `startingScore` en `ingest.py:208`) comparando tu equipo
      (`RoundPlayer.team_index` de tu fila) contra el otro.
- [ ] Va a `unknown` la ronda con `score_before` vacio o con largo distinto
      de 2. La suma de `rounds` de las cuatro filas es igual a `rounds` de
      `/api/overview/` con los mismos filtros (test).
- [ ] Test con una partida 0-0, 1-0, 1-1, 1-2 desde tu lado, con tu equipo
      como equipo 1 en al menos una partida (el indice del equipo no puede
      darse vuelta sin que el test caiga).
- [ ] Tendencias muestra el panel "Según el marcador" con las filas
      conocidas, CSV y aviso de muestra chica bajo 30 rondas; `unknown` solo
      se muestra si tiene rondas.
- [ ] `docs/metricas.md` tiene la fila. `seed_demo` hoy no llena
      `score_before`: si el diseno lo llena, los numeros del e2e cambian y se
      ajustan en la misma ficha (CLAUDE.md); si no lo llena, el e2e afirma
      el panel con todo en `unknown` oculto y un aviso de "sin marcador".
- [ ] Base vacia y filtros raros devuelven 200.

## Fuera de alcance

- Match point y ronda decisiva: dependen de las reglas de cada modo (a cuanto
  se gana, prorroga). Segundo tramo de B2, como idea en `ALCANCE.md`.
- Inercia de la ronda anterior: ficha 39.

## Diseno

(Arquitecto 20261013T2011Z, sobre main 5d2aecc. Spike en el scratchpad:
`KeyTransform` + `Cast` sobre `score_before` funciona en SQLite y
`[]`/`[1]` caen en unknown.)

**Implementar despues de que #39 se mergee**: usa `_filas_por_tramo`,
`TablaDeCorte` y `muestra.js` que crea la 39 y toca los mismos archivos
(prioriza, no bloquea: si se implementa antes, crear esos ayudantes con los
mismos nombres y firmas que dice el diseno de la 39).

**Decision: `seed_demo` llena `score_before`.** Asi el e2e ve filas reales.
Para la ronda `n` (numerada desde 0, ganas las pares): `score_before=[(n + 1) // 2, n // 2]`
(tu equipo es el 0). Resultado con la semilla: pares -> `tied`, impares ->
`ahead`, `behind` en 0. Ningun otro numero del seed cambia (`score_before`
solo lo lee `MatchDetail`, que pasa de mostrar "marcador " vacio a "0-0";
el e2e no lo afirma). Correr `test_seed_demo.py`.

**Archivos y por que**

- `backend/replays/analytics/aggregates.py`:
  - `MARCADOR = ("ahead", "tied", "behind", "unknown")`.
  - `by_score_state(**filters)`:
    ```python
    s0 = Cast(KeyTransform("0", "round__score_before"), IntegerField())
    s1 = Cast(KeyTransform("1", "round__score_before"), IntegerField())
    qs = base_queryset(**filters).annotate(s0=s0, s1=s1, s2=KeyTransform("2", "round__score_before"))
    qs = qs.annotate(
        mio=Case(When(team_index=0, then=F("s0")), When(team_index=1, then=F("s1"))),
        suyo=Case(When(team_index=0, then=F("s1")), When(team_index=1, then=F("s0"))),
    )
    conocido = qs.filter(mio__isnull=False, suyo__isnull=False, s2__isnull=True)
    ```
    tramos `ahead: conocido.filter(mio__gt=F("suyo"))`, `tied: ...mio=F("suyo")`,
    `behind: ...mio__lt=F("suyo")`, `unknown: qs.exclude(pk__in=conocido.values("pk"))`.
    `team_index` es el de tu `RoundPlayer` (el queryset es `is_me=True`);
    un `team_index` fuera de 0/1 deja `mio` nulo y cae en `unknown`.
    Devuelve `_filas_por_tramo("score_state", tramos)`.
    Comentario de por que `s2`: un marcador de mas de dos equipos no se
    puede leer como tuyo contra el otro.
- `backend/replays/views.py`: `"by_score_state": agg.by_score_state(**filters)` en `trends`.
- `backend/replays/management/commands/seed_demo.py`: `score_before` en
  `Round.objects.create` de `_ronda` como arriba.
- `backend/tests/factories.py`: `make_round(..., score_before: list | None = None)`
  -> `score_before=score_before or []`.
- `frontend/src/pages/Trends.jsx`: panel "Según el marcador" despues del de
  ronda anterior, con `TablaDeCorte`; etiquetas `ahead` "Adelante", `tied`
  "Empatado", `behind` "Atrás", `unknown` "Sin marcador". La fila `unknown`
  se filtra si tiene 0 rondas. Hint: "Cómo rindes según cómo iba la partida
  antes de la ronda." y el aviso de `filasConPocaMuestra` como en la 39.
  `csvName="segun-marcador"`.
- `docs/metricas.md`: en `## Contexto de la ronda` (la crea la 39) la fila
  **Segun el marcador** (marcador al empezar la ronda, de `startingScore`;
  tu equipo contra el otro; sin marcador o con otro largo que 2 va a "Sin
  marcador"; no depende de a cuanto se gana el modo).
- `backend/tests/test_marcador.py` (nuevo):
  - `test_las_cuatro_filas_salen_en_orden_fijo`
  - `test_cero_cero_uno_cero_uno_uno_uno_dos_desde_tu_lado` (equipo 0:
    `[0,0]` tied, `[1,0]` ahead, `[1,1]` tied, `[1,2]` behind)
  - `test_siendo_el_equipo_uno_el_marcador_se_lee_al_reves` (otra partida
    con `make_round_player(team_index=1)` y `[2,1]` -> behind, `[0,3]` -> ahead)
  - `test_marcador_vacio_o_de_otro_largo_va_a_sin_marcador` (`[]`, `[1]`, `[1,2,3]`)
  - `test_las_filas_suman_las_rondas_del_resumen`
  - `test_base_vacia_y_filtros_raros_dan_200_con_cuatro_filas_en_cero`
- `frontend/e2e/humo.spec.js`: `Tendencias muestra las rondas segun el marcador`:
  celdas "Adelante" y "Empatado" visibles, "Sin marcador" ausente
  (`toHaveCount(0)`), consola limpia.

**Orden:** factories + test -> aggregates -> views -> seed_demo ->
Trends.jsx -> e2e -> metricas.md -> `check.sh`.

**Que puede romperse:** `test_seed_demo.py` si afirma campos de `Round`;
el e2e de detalle de partida si en algun lado lee el marcador. Sin migracion.
Con datos reales importados antes de que `startingScore` existiera la fila
`unknown` puede ser grande: es correcto, por eso se muestra si tiene rondas.

**Verificacion manual:** `seed_demo`, `/api/trends/` -> `by_score_state`
con 87 ahead / 116 tied / 0 behind / 0 unknown (sobre la semilla actual de
203 rondas), y el panel en `/tendencias`.

## Para el humano

Nada por ahora.
