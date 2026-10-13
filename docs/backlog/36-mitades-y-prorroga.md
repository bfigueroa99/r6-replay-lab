# 36. Primera mitad, segunda mitad y prorroga

estado: entregado
candado: -
rama: claude/equipo-dev/36-mitades-y-prorroga
tipo: funcionalidad
epica: lado-y-marcador
area: fullstack
prioridad: 2
fuente: ALCANCE.md B1; `Round.overtime_number` (`backend/replays/models.py:89`) se guarda en `ingest.py:201` y ninguna vista lo usa
archivos: backend/replays/analytics/aggregates.py, backend/replays/views.py, frontend/src/pages/Trends.jsx, docs/metricas.md, backend/tests/, frontend/e2e/, backend/tests/factories.py
turnos: po 20261013T0511Z, arquitecto 20261013T0611Z, dev 20261013T0711Z, revisor 20261013T0811Z, qa 20261013T0911Z, release 20261013T1011Z

## PR

**Titulo:** `[equipo-dev][fullstack] Tendencias por mitad de la partida, prorroga y lado inicial`

### Que cambia

Tendencias suma el panel "Por mitad de la partida": winrate de ronda, rating, KPR y aperturas en la primera mitad, la segunda y la prórroga, y debajo el winrate de partida según el lado con que arrancaste. Responde si te cuesta cerrar una partida o si rindes peor cuando se alarga, algo que "por número de ronda" no muestra. `GET /api/trends/` gana dos claves, `by_half` y `by_start_side`.

### Por que esto y no otra cosa

Ficha 36, primer tramo de la epica `lado-y-marcador` (ALCANCE.md B1): `Round.overtime_number` se guardaba y ninguna vista lo usaba. La mitad se deduce de los datos (lado de la ronda mas baja sin prorroga), no de un numero fijo de rondas por modo, porque cambia entre ranked, unranked y temporadas. Se descarto un grafico nuevo: tres barras no agregan sobre la tabla.

### Como se probo

- `./scripts/check.sh` sobre el commit final: `Todo en verde.` (ruff, 478 tests backend con 4 saltados, 65 vitest, build, 24 e2e).
- Tests nuevos en `backend/tests/test_mitades.py` (10): `test_seis_rondas_y_dos_de_prorroga_dan_tres_tres_y_dos`, `test_el_lado_inicial_sale_de_la_ronda_mas_baja_aunque_no_sea_la_uno`, `test_una_mitad_sin_rondas_sale_con_cero_y_metricas_nulas`, `test_lado_inicial_cuenta_partidas_y_winrate_de_partida`, `test_partida_sin_lado_en_la_primera_ronda_no_cuenta_para_el_lado_inicial`, `test_el_filtro_de_mapa_cambia_el_conteo_por_mitad`, `test_trends_sin_datos_devuelve_las_filas_vacias_sin_500`, `test_ronda_sin_lado_no_cae_en_la_segunda_mitad`, `test_el_filtro_de_lado_no_cambia_el_lado_inicial`, `test_partida_sin_resultado_cuenta_pero_no_entra_al_winrate`.
- e2e `Tendencias muestra la tabla por mitad` en `frontend/e2e/humo.spec.js`.
- Revision ciega y QA en sesiones distintas; 8 mutaciones sobre `aggregates.py` caen en `test_mitades` (una de QA sobrevive por ser equivalente).
- QA con `curl` sobre base vacia y sembrada con `factories.py`: 3/3/2 en una partida 3+3+2, numeracion desde 0, ronda mas baja sin lado, parametros basura -> 200. Chunk inicial sin cambio (185.47 kB).

### Riesgos y lo que no entra

Sin migracion, sin `recompute`, sin parser. El lado inicial es un Subquery por fila de `RoundPlayer`: barato con `Round` indexado por `match`, pero si `/api/trends/` se pone lento en una base de miles de rondas, avisar. Si faltan los `.rec` del inicio de una partida, la segunda mitad se lee como primera (documentado en `docs/metricas.md`). Fuera: rendimiento bajo presion (B2, tramo siguiente) y cambios a `by_round_number`.

### Como probarlo en 2 minutos

```powershell
cd backend; python manage.py test tests.test_mitades     # 10 tests OK
python manage.py runserver
```

Abrir `http://127.0.0.1:8000/tendencias`: arriba de "Por número de ronda" aparece "Por mitad de la partida" con filas Primera mitad, Segunda mitad, Prórroga y la tabla "Según el lado con que arrancas" (Ataque / Defensa). `curl http://127.0.0.1:8000/api/trends/` trae `by_half` (3 filas) y `by_start_side` (2 filas). Con la base de `seed_demo` la primera mitad sale 100 % y la segunda 0 %: es el seed, que gana todas las de ataque.

### Para el humano

Nada que decidir. Aviso: tomar el lado inicial solo de una ronda con `score_before == [0, 0]` evitaria confundir mitades cuando faltan `.rec`; queda como mejora posible para el tramo siguiente.

### Candidatos descubiertos

Ninguno.

## Que gana quien usa la app

En Tendencias ve su winrate de ronda y su rating en la primera mitad, en la segunda y en la prorroga, y el winrate de partida segun si arranco atacando o defendiendo.

## Criterios de aceptacion

- [x] `GET /api/trends/` devuelve `by_half` con `first`, `second`, `overtime`; fila vacia con `rounds: 0` y metricas `null`, sin 500.
- [x] La mitad se deduce de los datos (lado de la ronda mas baja sin prorroga); test 3/3/2.
- [x] `by_start_side` con `Attack` y `Defense`; partida sin lado no cuenta.
- [x] Los filtros comunes aplican; test con `?map=`.
- [x] Tendencias muestra las tablas en español; e2e sin errores de consola.
- [x] `docs/metricas.md` con fila por cada numero nuevo.

## Fuera de alcance

Rendimiento bajo presion (B2), cambios a `by_round_number`, reglas del coach sobre mitades.

## Diseno

(Arquitecto 20261013T0611Z) `_lado_inicial` como Subquery sobre `Round` (ronda de menor `number` con `overtime_number=0`), `by_half` y `by_start_side` en `aggregates.py`, dos claves en `views.trends`, `make_round(overtime_number=0)` en `factories.py`, Panel en `Trends.jsx` antes de "Por numero de ronda", e2e en `humo.spec.js`, seccion `## Mitades y prorroga` en `metricas.md`. `seed_demo` no se toca. Detalle en `git log`.

## Implementacion

(Dev 20261013T0711Z) Todo el diseno. Desvios: `by_start_side` devuelve ademas `decided` y `wins`; primera y segunda mitad excluyen rondas con `my_side` vacio.

## Revision 2026-10-13 sobre c46b3e8

(Revisor 20261013T0811Z) Veredicto: aprobar. Un hallazgo menor y preexistente, no bloqueante: el tooltip "ronda tipica" sin tilde (Trends.jsx:350, copiado de otras cinco lineas en main).

## QA 2026-10-13 sobre 7319395

(QA 20261013T0911Z) Veredicto: aprobado. Los 6 criterios con evidencia (`curl` en base vacia y sembrada, Chromium sin errores de consola, `check.sh` verde). Detalle en `git log`.

## Para el humano

- (Dev, aviso) Si faltan los `.rec` del inicio de una partida, la segunda mitad se lee como primera; mejora posible con `score_before == [0, 0]`. No bloquea.
