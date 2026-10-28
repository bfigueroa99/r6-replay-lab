# 64. Partidas en el Inicio: ganadas, rondas por partida y mejor y peor mapa

estado: entregado
candado: -
rama: claude/equipo-dev/64-partidas-en-el-inicio
tipo: funcionalidad
epica: paridad-referencia
area: fullstack
prioridad: 3
fuente: ALCANCE.md R1 (replica/features.csv fila 11, must, clone partial; [aurelix](https://aurelix.app/))
archivos: backend/replays/analytics/aggregates.py, backend/replays/views.py, frontend/src/pages/Dashboard.jsx, backend/tests/test_resumen_partidas.py, frontend/e2e/humo.spec.js, docs/metricas.md
turnos: po 20261027T1205Z, arquitecto 20261027T1605Z, dev 20261027T2005Z, revisor 20261028T0004Z, qa 20261028T0404Z, release 20261028T0404Z

## PR

Titulo: `[equipo-dev][frontend] Partidas en el Inicio: ganadas, rondas por partida y mejor y peor mapa`

### Que cambia

El Inicio suma una fila de partida bajo los KPI: **Partidas ganadas**
(ganadas sobre decididas, con las sin resultado aparte), **Rondas por
partida**, y tu **Mejor** y **Peor mapa** por winrate de partida (3+
partidas decididas). Respeta los filtros de la pagina menos el lado.
`GET /api/overview/` trae la clave nueva `matches_summary`.

### Por que esto y no otra cosa

Ficha 64, epica `paridad-referencia` (R1 de `ALCANCE.md`: la referencia
cuenta partidas y la app solo rondas). Va en la vista y no en
`agg.overview` porque el coach llama a `overview` y no la usa. El peor mapa
sale `null` si no esta por debajo del mejor (un solo mapa o todos
empatados), en vez de repetir el mismo numero.

### Como se probo

- `./scripts/check.sh`: 802 tests backend, 120 frontend, build ok, 51 e2e.
- `backend/tests/test_resumen_partidas.py` (14): ganadas/decididas 75 %,
  rondas por partida 8.0 y 7.5 con una sin resultado, mejor y peor mapa,
  muestra minima, sin resultado fuera de la muestra, un solo mapa, empate,
  variantes de temporada juntas, el lado no parte la partida (tambien una
  partida sin rondas del lado), filtros, base vacia y filtro sin partidas.
- e2e `el Resumen muestra tus partidas` con `seed_demo` (29 de 29, 7.0,
  Bank 100 % en 10, peor "—").
- QA: `curl` con base sembrada y vacia y 15 filtros borde (todo 200);
  Chromium por mapa y a 390 px; mutacion sobre 5 lineas (una sobrevivia y
  ahora tiene test). Bundle inicial +0.5 %.

### Riesgos y lo que no entra

Sin migracion, sin `recompute`, sin parser. Fuera: cambiar `Match.won` o el
empate que hoy se ve como "incompleta" (aviso de la ficha 54); winrate de
partida por lado, operador o compañero.

### Como probarlo en 2 minutos

```powershell
cd frontend; npm run build; cd ..\backend
..\.venv\Scripts\python.exe manage.py runserver
```

Abrir `http://localhost:8000/`: bajo los KPI, la fila "Partidas ganadas /
Rondas por partida / Mejor mapa / Peor mapa". Cambiar el selector Mapa: los
numeros se recalculan. `curl "localhost:8000/api/overview/?since=2030-01-01"`
-> `matches_summary` con nulos y 200.

### Para el humano

Aviso, no bloquea: `MIN_PARTIDAS_MAPA = 3` solo se probo con datos
sinteticos; con tu base puede convenir 5.

### Candidatos descubiertos

Ninguno.

## Que gana quien usa la app

El Inicio contaba todo en rondas; lo primero que uno quiere saber es cuantas
partidas gano, y en que mapa le va mejor y peor.

## Criterios de aceptacion

- [x] `matches_summary` con ganadas, perdidas, decididas, sin resultado y
      `match_winrate` = ganadas / decididas (75 % con 3-1-1).
- [x] `rounds_per_match` = rondas / partidas, un decimal (7 y 9 -> 8.0).
- [x] `best_map` y `worst_map` con muestra minima 3; un solo mapa o empate
      -> peor `null`; sin mapas -> los dos `null`.
- [x] Base vacia y filtros sin partidas: 200, nulos, sin dividir por cero.
- [x] Fila en `Dashboard.jsx` con textos en castellano y e2e con `seed_demo`.
- [x] Filas en `docs/metricas.md` con la muestra minima.

## Diseno

(Arquitecto 20261027T1605Z.) `matches_summary(**filters)` en
`aggregates.py`: partidas de `base_queryset` sin `side`, una query de
partidas y un `count()` de rondas; mapas por `map_slug` con el nombre de la
mas reciente, `MIN_PARTIDAS_MAPA = 3`. Clave puesta en la vista. Fila de
cuatro `Stat3` en el Inicio que no se pinta si el backend no trae la clave.

## Implementacion

(Dev 20261027T2005Z.) Todo el diseno. Desvios menores: el payload suma
`min_matches_map` (el texto "Ningún mapa con 3+ partidas" no repite la
constante) y "1 partida" en singular.

## Revision 2026-10-28 sobre 19b6759

(Revisor 20261028T0004Z.) Aprobar. Hallazgo corregido con test: sacar `side`
de los filtros no estaba cubierto (`test_una_partida_sin_rondas_del_lado_filtrado_igual_cuenta`).

## QA 2026-10-28 sobre 1a24d91

(QA 20261028T0404Z.) Aprobado. Los seis criterios con `curl` y Chromium
sobre base sembrada y vacia; detalle en `git log` (commit `Prueba: 64`).
Mutacion: `rounds_per_match` sobre decididas sobrevivia; agregado
`test_las_sin_resultado_cuentan_en_rondas_por_partida`. Preexistente en
dev, no bloquea: el Inicio no lee los filtros de la URL.

## Para el humano

- Calibrar con la base real: `MIN_PARTIDAS_MAPA = 3` (aviso, no bloquea).
