# 83. Partidas excluidas a la vista en Partidas y en Datos

estado: propuesto
candado: arquitecto 2026-11-05T13:03Z
rama: -
tipo: funcionalidad
epica: datos
area: fullstack
prioridad: 3
fuente: tramo 2 de la ficha 79 (G2 de ALCANCE.md), partida por el arquitecto 20261105T0349Z-cCqeUqM porque el total (~630 lineas) no entra en un turno de Dev
archivos: frontend/src/pages/Matches.jsx, backend/replays/views.py (import_status), frontend/src/pages/Datos.jsx, backend/tests/test_excluir_partida.py, frontend/e2e/partidas-excluidas.spec.js
turnos: arquitecto 20261105T0349Z-cCqeUqM

**Implementar despues de que #79 se mergee**: usa su columna `Match.excluded`,
el campo `"excluded"` de `/api/matches/`, el POST y el e2e
`partidas-excluidas.spec.js`.

## PR

(La escribe el Release manager al final.)

## Que gana quien usa la app

Con la 79, una partida excluida deja de contar, pero solo se nota desde su
detalle. Con este tramo, la fila de Partidas lleva el chip "excluida" y Datos
lista todas las que sacaste, cada una con su enlace para volver a contarla.
Asi ninguna queda olvidada fuera de tus números.

## Criterios de aceptacion

- [ ] La fila de una partida excluida en Partidas muestra el chip "excluida"
      junto a la fecha, dentro del `render` de `played_at`. El CSV del boton de
      Partidas queda byte a byte igual, porque `celdaCsv` (ui.jsx:85) exporta
      `row[col.key]`.
- [ ] `GET /api/import/status/` suma
      `"excluded": [{"id", "played_at", "map", "score"}]`, ordenado por
      `-played_at` y con la etiqueta de version (`etiquetas_de_mapas(...,
      incluir_excluidas=True)`). Lleva el test
      `test_import_status_lista_las_excluidas` en `test_excluir_partida.py`.
- [ ] En Datos, el panel "Fuera de tus números" (hint: "No cuentan en ningún
      agregado; se vuelven a contar desde su detalle.") muestra Cuándo (link a
      `/partidas/<id>`), Mapa y Marcador. Si no hay ninguna, dice "Ninguna
      partida excluida.".
- [ ] El e2e `partidas-excluidas.spec.js` suma dos pasos con la partida
      excluida: el chip en `/partidas` y el link en `/datos`. La consola tiene
      que quedar limpia.

## Fuera de alcance

- Excluir desde Partidas o desde Datos: el boton vive en el detalle.
- Un filtro `?excluded=` en el listado.
- Que la topbar diga "· N excluidas".

## Diseno

## Implementacion

## Revision

## QA

## Verificar en el PC

## Para el humano
