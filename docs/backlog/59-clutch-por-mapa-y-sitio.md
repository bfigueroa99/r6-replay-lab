# 59. Clutch por mapa y sitio

estado: entregado
candado: -
rama: claude/equipo-dev/59-clutch-por-mapa-y-sitio
tipo: funcionalidad
epica: impacto
area: fullstack
prioridad: 3
fuente: ALCANCE.md K5
archivos: backend/replays/analytics/aggregates.py, backend/replays/views.py, backend/tests/test_clutch.py, frontend/src/pages/Teammates.jsx, frontend/e2e/humo.spec.js, docs/metricas.md
turnos: po 20261019T0325Z, arquitecto 20261022T0804Z, dev 20261023T2003Z, revisor 20261024T0004Z, qa 20261024T0404Z, release 20261024T0804Z

Implementar despues de #55: usa la columna `RoundPlayer.clutch_vs` que esa
ficha agrega con su migracion.

## PR

Titulo: `[equipo-dev][fullstack] Clutch por mapa y sitio en Compañeros`

### Que cambia

El panel "Clutches" de Compañeros suma la tabla "Clutch por mapa y sitio":
por cada mapa una fila total y una por sitio de bomba con intentos, ganados
y conversion; los sitios con menos de 5 intentos llevan `*` de muestra
chica, y las rondas sin sitio van a "Sin sitio". Respeta los filtros de la
barra y exporta a CSV (`clutch-por-sitio`). `/api/teammates/` trae la clave
nueva `clutch_by_site`.

### Por que esto y no otra cosa

Ficha 59, tramo de la epica `impacto` (ALCANCE.md K5), sobre la columna
`RoundPlayer.clutch_vs` de la ficha 55: sin migracion. Clutch por operador
(O6) y "cuantos se esperaban" (K3) quedan para otras fichas.

### Como se probo

- `./scripts/check.sh` sobre la rama con `main` (9554a30) ya incluido:
  `Todo en verde.` (763 tests backend, 120 frontend, build ok, 47 e2e).
- `backend/tests/test_clutch.py`, clase `ClutchPorSitioTests` (6): agrupa
  por mapa y sitio con totales, sin sitio, borde 4/5 de muestra chica,
  ronda sin ganador no cuenta, filtro de lado via API, base vacia 200 `[]`.
- e2e `Compañeros muestra el clutch por mapa y sitio` sobre `seed_demo`.
- QA: base vacia y sembrada con filtros borde (`side`, `ranked_only`,
  `operator`, `since`, `until=foo`, `days=-3`), cero 500; la suma de totales
  coincide con `clutch_conversion`; 3 mutaciones, todas caen.

### Riesgos y lo que no entra

Sin migracion, sin `recompute`, sin parser. Chunk inicial igual (187,83 kB);
solo crece el perezoso de Compañeros (8,22 -> 9,33 kB).

### Como probarlo en 2 minutos

```powershell
cd backend; python manage.py seed_demo --force; python manage.py runserver
```

Abrir http://127.0.0.1:8000/companeros, panel "Clutches": debajo de la tabla
de conversion, "Clutch por mapa y sitio" con `Border Total 5 1 20%` sin
marca y `B Armory, B Archives 3 1 33%` con `*`. Con el filtro de lado en
Ataque los numeros bajan y siguen sumando lo mismo que la tabla de arriba.

### Para el humano

Aviso, no bloquea: calibrar `CLUTCH_SITIO_MIN = 5` con la base real.

### Candidatos descubiertos

Ninguno.

## Que gana quien usa la app


La ficha 55 da la conversion de clutch por X y lado; esta la parte por mapa
y por sitio de bomba. Se ve en que sitio cierras las rondas que quedan en tus
manos y en cual te quedas solo y pierdes siempre, que es donde conviene
revisar como se juega el final de ronda.

## Criterios de aceptacion

- [x] Agregado nuevo `clutch_by_site` en `replays/analytics/aggregates.py`:
  una fila por mapa y sitio (`Match.map_slug`, `map_name`, `Round.site`) y
  otra de total por mapa, con intentos (`clutch_vs > 0`), ganados
  (`clutch_vs > 0` y `won`) y %. Respeta los filtros de la barra (lado,
  fechas, ranked, operador). Rondas sin sitio van a una fila "Sin sitio" del
  mapa, no se pierden. Test de Django con dos mapas y tres sitios armados.
- [x] Muestra minima: un sitio con menos de 5 intentos sale igual pero con
  `low_sample: true`, para que la UI lo marque; el umbral es una constante
  con nombre. Test del borde (4 y 5 intentos).
- [x] Se sirve en el mismo endpoint que la tabla de conversion de la ficha
  55, como `clutch_by_site`; con base vacia devuelve lista vacia sin 500.
- [x] En la pagina donde la ficha 55 deja la tabla de conversion, una tabla
  "Clutch por mapa y sitio" debajo, ordenada por mapa y con el % de cada
  sitio, boton CSV y la marca de muestra chica. Sin intentos dice
  "Todavía no quedaste último en ninguna ronda". Entra al e2e con
  `seed_demo`.
- [x] Fila nueva en `docs/metricas.md` ("Clutch por mapa y sitio") que remite
  a la definicion de intento y ganado de la ficha 55.

## Fuera de alcance

- Clutch por operador (idea O6): otra ficha, misma columna.
- La parte "cuantos se esperaban" de K3, que necesita la tabla de K1.
- Cambiar `one_vx`, el Rating o la tabla de la ficha 55.

## Implementacion

Dev 20261023T2003Z, sin desvios de alcance: `CLUTCH_SITIO_MIN` y
`clutch_by_site` en `aggregates.py`, clave en `views.teammates`, seis tests,
tabla en `Teammates.jsx` despues de la de conversion (CSV con "Total" en las
filas de mapa), e2e y fila en `docs/metricas.md`. Desvio menor: el vacio usa
`empty=` del `DataTable`, mismo texto. Detalle en `git log`.

## Revision 2026-10-24 sobre c7b7964

Revisor 20261024T0004Z, a ciegas y confirmado: sin hallazgos, los cinco
criterios cubiertos. Veredicto: aprobar -> revisado.

## QA 2026-10-24 sobre c7b7964

QA 20261024T0404Z: `check.sh` en verde, base vacia y sembrada sin 500,
totales = conversion, bundle inicial sin cambio, 3 mutaciones caen.
Veredicto: aprobado.

## Entrega 2026-10-24

Release 20261024T0804Z: `turnos:` con dev, revisor y qa de sesiones distintas;
main (9554a30) ya incluido en la rama; `check.sh` en verde sobre el commit
entregado. Entorno: Chromium de la nube con alias 1194 -> 1243 en el
scratchpad (nota de la revision).

## Para el humano
`.

Criterios: los cinco con evidencia arriba. Veredicto: aprobado.

## Para el humano

- Calibrar con la base real: `CLUTCH_SITIO_MIN = 5` marca como muestra
  chica los sitios con menos de 5 clutches; con tu base, mirar en
  `/companeros` si deja demasiadas filas marcadas.
