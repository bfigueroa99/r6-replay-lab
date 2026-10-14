# 43. Match point y ronda decisiva

estado: entregado
candado: -
rama: claude/equipo-dev/43-match-point
tipo: funcionalidad
epica: lado-y-marcador
area: fullstack
prioridad: 3
fuente: ALCANCE.md B5, segundo tramo de B2 (rondas bajo presion); el primer tramo (adelante/empatado/atras) entro con la ficha 41
archivos: backend/replays/analytics/reglas_partida.py, backend/replays/analytics/aggregates.py, backend/replays/views.py, backend/tests/test_match_point.py, frontend/src/pages/Trends.jsx, frontend/e2e/humo.spec.js, docs/metricas.md
turnos: po 20261014T0911Z, arquitecto 20261014T1012Z, dev 20261014T1511Z, revisor 20261014T1611Z, qa 20261014T1711Z, release 20261014T1811Z

## PR

**Titulo:** `[equipo-dev][frontend] Match point en Tendencias`

### Que cambia

Tendencias suma el panel **Match point**, justo despues de "Según el
marcador": tus metricas en las rondas donde tu equipo podia cerrar la
partida, donde podia cerrarla el rival, donde podian los dos, las normales
y las sin marcador o sin regla. Las cinco filas suman todas tus rondas.
Por ahora solo ranked tiene regla (gana a 4; con 3-3 prorroga a 5).

### Por que esto y no otra cosa

Ficha 43, segundo tramo de la epica `lado-y-marcador` (ALCANCE.md B5),
sobre el panel "Según el marcador" de la ficha 41. Descartado: inferir la
regla desde las partidas importadas (sesga hacia las terminadas y no ve un
match point perdido); probabilidad de ganar segun el marcador.

### Como se probo

- `./scripts/check.sh`: 561 tests backend, 80 frontend, build ok, 32 e2e,
  `Todo en verde.` sobre la rama con `main` fusionado.
- `backend/tests/test_match_point.py`: reglas puras (3-2 `mine`, 3-3
  `normal` por la prorroga, 4-3 `mine`, 4-4 `both`, 2-3 `theirs`, regla sin
  prorroga, regla por version), tipo sin regla y QuickMatch a `unknown`,
  Y9S3 y marcador vacio a `unknown`, marcador fuera de rango a `normal`,
  equipo 1 leido al reves, las cinco filas en orden que suman todo, API con
  base vacia y filtros raros.
- e2e `Tendencias muestra el match point` con `seed_demo` (sin tocarlo).
- QA manual: base vacia y base sembrada a mano (26 rondas, esperado
  `mine 3, theirs 2, both 2, normal 13, unknown 6`, obtenido igual; suma
  igual a `by_score_state`); mutaciones tumban tests.

### Riesgos y lo que no entra

Sin migracion, sin `recompute`, no toca parser ni Electron. `by_score_state`
se refactorizo para compartir `_marcador_conocido` sin cambiar su salida
(`test_marcador.py` sin tocar, en verde). Fuera: unranked, rapida y custom
(sin regla citable, van a "Sin marcador o sin regla").

### Como probarlo en 2 minutos

```
cd backend; python manage.py seed_demo; python manage.py runserver
```

Abrir `http://127.0.0.1:8000/tendencias`: el panel "Match point" aparece
despues de "Según el marcador" con "Tu match point" y "Sin match point".

**Verificar en el PC:** con la base real, `/tendencias?match_type=Ranked`
marca match point en partidas ranked de 4-x; `?match_type=QuickMatch` manda
todo a "Sin marcador o sin regla".

### Para el humano

Nada que decidir. Aviso: la regla de ranked sale de una guia de Dexerto
(2024), no de una pagina oficial; si sabes la de unranked o rapida, es una
linea en `reglas_partida.py`.

### Candidatos descubiertos

Ninguno.

## Que gana quien usa la app

Ver como rindes en las rondas que pueden cerrar la partida: cuando tu equipo
esta a una ronda de ganarla, cuando el rival esta a una, y cuando pasan las
dos cosas. Completa el panel "Según el marcador" de la ficha 41.

## Criterios de aceptacion

- [x] Tabla de reglas por tipo y `code_version`; tipo sin regla a "sin regla".
- [x] `GET /api/trends/` con `by_match_point` (`mine`, `theirs`, `both`,
  `normal`, `unknown`) que suman todas tus rondas.
- [x] Reusa `score_before` con el corte Y9S4; Y9S3 a `unknown`.
- [x] Panel en Tendencias con banda de muestra chica; e2e con `seed_demo`.
- [x] Fila en `docs/metricas.md`.

## Diseno

(arquitecto 20261014T1012Z) `reglas_partida.py` sin Django con `REGLAS`
(solo `Ranked` desde Y9S4, fuente Dexerto), `regla_para`, `objetivo`,
`cierra`, `estado`, `tramos`; `_marcador_conocido` extraido de
`by_score_state`; `by_match_point` arma `Q` por tipo, version y marcador.
Detalle en `git log` de la rama.

## Implementacion

(dev 20261014T1511Z) Todo el diseno. Desvios: `tramos(regla)` sin
`desde`/`hasta` y sin marcadores de partida terminada; `by_match_point`
ordena las reglas por `desde`; `regla_para` acepta `reglas` opcional.

## Revision

(revisor 20261014T1611Z) Sin hallazgos, aprobar. Menores no bloqueantes:
`regla_para` solo la usan los tests; `metricas.md` no nombra `Standard`.

## QA

(qa 20261014T1711Z) Aprobado: check.sh verde, base vacia y sembrada a mano
con resultados esperados, filtros raros 200, mutaciones tumban tests.

## Para el humano

Aviso, sin pregunta abierta: solo ranked tiene regla (guia de Dexerto de
2024, no pagina oficial). Conviene mirar en el PC el panel con una partida
ranked y una rapida reales.
