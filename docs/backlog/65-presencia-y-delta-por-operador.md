# 65. Presencia y delta de winrate por operador

estado: entregado
candado: -
rama: claude/equipo-dev/65-presencia-y-delta-por-operador
tipo: funcionalidad
epica: operadores
area: fullstack
prioridad: 3
fuente: ALCANCE.md O5 (replica/features.csv fila 26, must, clone partial; [r6tv](https://r6tv.online/how-it-works), [aurelix](https://aurelix.app/blog/how-to-analyse-r6-siege-replays))
archivos: backend/replays/analytics/aggregates.py, frontend/src/pages/Operators.jsx, backend/tests/test_operadores_presencia.py, frontend/e2e/humo.spec.js, docs/metricas.md
turnos: po 20261027T1205Z, arquitecto 20261027T1605Z, dev 20261028T0804Z, revisor 20261028T1209Z, qa 20261028T1432Z, release 20261028T1432Z

## PR

Titulo: `[equipo-dev][frontend] Operadores: presencia y winrate contra tu lado`

### Que cambia

La tabla de Operadores suma dos columnas por operador y lado: **Presencia**
(% de tus rondas de ese lado jugadas con el) y **vs. tu lado** (su winrate
menos tu winrate de ese lado, en puntos, con signo y color). Se ve de un
vistazo que operador te sube, cual te baja y si el numero se apoya en muchas
rondas o en pocas. `GET /api/operators/`, el CSV de la tabla y
`/api/export/?table=operators` traen `presence_pct` y `winrate_delta`.

### Por que esto y no otra cosa

Ficha 65, epica `operadores` (O5 de `ALCANCE.md`, un `must` de la referencia
que la app tenia a medias). La base del lado se cuenta antes de `min_rounds`
para que ocultar filas no mueva las demas. Sin banda de ruido: la fila es
parte de la base, no una muestra independiente; la Presencia dice cuanto pesa.

### Como se probo

- `./scripts/check.sh`: 811 tests backend, 120 frontend, build ok, 52 e2e.
- `backend/tests/test_operadores_presencia.py` (9): presencia y delta contra
  el lado (40 % y +25), `min_rounds` no mueve la base, cada lado con su base,
  presencias que suman 100, filtro de lado, fila sin rondas decididas ->
  `null`, base vacia, API y export con las columnas.
- e2e `Operadores muestra presencia y delta` (`seed_demo`: Ash 34 % y 0).
- QA: `curl` con base vacia y sembrada y 13 parametros borde (todo 200);
  Chromium (signo y color, orden con nulos al final, CSV, filtro de lado,
  390 px, consola limpia); tres mutaciones, las tres caen. Chunk inicial igual.

### Riesgos y lo que no entra

Sin migracion, sin `recompute`, sin parser. `coach.py` recibe dos claves que
no lee. Fuera: el corte por mapa y sitio (O1), la señal del Coach y el rating
relativo al operador (O3).

### Como probarlo en 2 minutos

```powershell
cd frontend; npm run build; cd ..\backend
..\.venv\Scripts\python.exe manage.py runserver
```

Abrir `http://localhost:8000/operadores`: columnas "Presencia" y "vs. tu
lado" en Ataque y Defensa; las presencias de cada lado suman 100; ordenar
por "vs. tu lado" deja los `—` al final; "Descargar CSV" trae las dos.

### Para el humano

Aviso, no bloquea: cuatro detalles menores para una ficha chica (abajo).

### Candidatos descubiertos

Ninguno.

## Que gana quien usa la app

En Operadores se veia el winrate de cada operador, pero no si es mejor o
peor que tu winrate normal en ese lado ni cuanto lo juegas.

## Criterios de aceptacion

- [x] Cada fila trae `presence_pct` y `winrate_delta` (Ash 4 de 10 rondas de
      ataque, 3 ganadas, base 5 de 10: 40 % y +25; el Arquitecto corrigio el
      ejemplo a 2 ganadas para el otro operador).
- [x] La base del lado no depende de `min_rounds`.
- [x] Filtros de lado y operador recortan la base; sin rondas decididas ->
      `null`; base vacia: `[]` y 200.
- [x] Columnas "Presencia" y "vs. tu lado" ordenables, con ayuda, en el CSV y
      en el e2e.
- [x] Filas en `docs/metricas.md` (sin banda de ruido, y dice por que).

## Diseno

(Arquitecto 20261027T1605Z.) Todo en `agg.by_operator`: base por lado sobre
el queryset entero, query aparte de rondas con ganador, `_pct` y `_delta`.
Columnas en `Operators.jsx` con un `DeltaLado` que redondea antes de elegir
signo y color. Skills: no aplica; sin arena.

## Implementacion

(Dev 20261028T0804Z.) Todo el diseno, mas `test_la_api_trae_las_columnas`.
Desvio: se quito la rama "lado sin rondas decididas", inalcanzable.

## Revision 2026-10-28 sobre 5356084

(Revisor 20261028T1209Z.) Aprobar. Cuatro hallazgos menores, abajo.

## QA 2026-10-28 sobre bfff25a

(QA 20261028T1432Z.) Aprobado. Los cinco criterios con `curl` y Chromium
sobre base sembrada y vacia; detalle en `git log` (commit `Prueba: 65`).

## Para el humano

- Aviso, no bloquea (Revisor y QA): cuatro detalles menores confirmados que
  caben en una ficha chica: redondeo simetrico en `DeltaLado`
  (`Operators.jsx`: 1.5 se ve `+2` y -1.5 `-1`), delta calculado con los
  conteos crudos (`aggregates.py`, hoy puede correrse 0.1), "con operador
  conocido" en las dos filas de `metricas.md` (la base excluye las rondas
  sin operador), y un vitest de `DeltaLado` con 0.5, -0.5, -0.4 y null.
