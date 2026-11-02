# 71. La partida dice que version del mapa se jugo

estado: entregado
candado: -
rama: claude/equipo-dev/71-version-del-mapa-en-la-partida
tipo: funcionalidad
epica: temporada-y-modo
area: backend
prioridad: 2
fuente: idea A6 de `ALCANCE.md` ("Implementar despues de #70"; la 70 esta en `dev` desde 0fedc7b, PR #65). Fuera de alcance de la ficha 70: "listado, records, sesiones y detalle de partida". `etiqueta_de_version` (`pydissect/header.py:239`) y `etiquetas_de_version` (`replays/analytics/aggregates.py:481`) ya existen; `match_list` y `match_detail` (`replays/views.py:434` y `:543`) devuelven `map: match.map_name`
archivos: backend/replays/analytics/aggregates.py, backend/replays/views.py, backend/tests/test_mapa_de_la_partida.py, docs/metricas.md
turnos: po 20261030T1653Z, arquitecto 20261030T1652Z, dev 20261031T2135Z, revisor 20261102T0805Z-cD882za, qa 20261102T1206Z-cLhn4iG, release 20261102T1206Z-cLhn4iG

## PR

Titulo: `[equipo-dev][backend] Partidas y el detalle dicen que version del mapa se jugo`

### Que cambia

Desde la ficha 70, Mapas separa "Consulate (Y10)" de "Consulate (Y7)", pero
Partidas, el detalle de la partida y el resumen copiado decian "Consulate" a
secas. Ahora `map` en `/api/matches/` y `/api/matches/<id>/` lleva la misma
etiqueta que la fila de Mapas, y se sabe a que fila suma cada partida.

### Por que esto y no otra cosa

Ficha 71, idea A6 de `ALCANCE.md`. La etiqueta sale de la misma funcion que
Mapas y el selector (`etiquetas_de_version`), mirando todas las partidas del
slug: etiquetar solo la fila o la pagina perdia el "(id N)". Guardar la
etiqueta en la base se descarto: pedia migracion y se desactualiza con Datos.

### Como se probo

- `check.sh` (con `verificar.sh`): VERDE, 858 tests backend, 133 vitest, 53 e2e.
- Tests nuevos (`backend/tests/test_mapa_de_la_partida.py`):
  `test_el_listado_dice_la_version_del_mapa` (Y7, Y10, sin sufijo, `map_id=0`),
  `test_el_detalle_dice_la_version_del_mapa`,
  `test_listado_y_detalle_dicen_lo_mismo_que_mapas` (con "(id 999)"),
  `test_la_etiqueta_no_cambia_con_la_pagina` (`limit=1`),
  `test_el_filtro_del_listado_sigue_igual` (`?map=<slug>` y `?map=<map_id>`),
  `test_el_listado_no_hace_una_consulta_por_partida`.
- Manual (QA): `runserver` con base vacia y con base de `factories`; curl a
  listado, detalle, filtros y paginacion con bordes, sin 500; `by_map` y el
  listado dan el mismo conjunto de etiquetas; `textoResumenPartida` sobre el
  detalle real arranca con `Consulate (Y10) · 4-2 · victoria`.
- OMC: plan=— (diseno sin OMC) · Dev: no disponible (sin herramienta Agent)
  · Revision: revisión=2 hallazgos (0 arreglados, LOW) · QA: verificación=PASS (5 de 5 VERIFIED)

### Riesgos y lo que no entra

Sin migracion ni `recompute`. Una consulta mas por pagina del listado. Fuera:
Records, Sesiones, Inicio, Clutch, Progreso y Duelos siguen por slug (A8);
la tabla `matches` de Exportar sigue sin version (idea anotada); con filtros
que esconden una version, Mapas puede perder un "(id N)" que Partidas
conserva (A8).

### Como probarlo en 2 minutos

```
cd backend; python manage.py test tests.test_mapa_de_la_partida
python manage.py runserver
```
Con una base que tenga partidas de Consulate de dos versiones: Partidas dice
"Consulate (Y10)" / "Consulate (Y7)", igual que la fila de Mapas; el detalle
lo repite y "Copiar resumen" arranca con esa etiqueta. Con `seed_demo` todo
sigue igual (`map_id=0`).

### Para el humano

Nada.

### Candidatos descubiertos

Ninguno (la tabla `matches` de Exportar sin version va como idea, no ficha).

## Que gana quien usa la app

Partidas, el detalle y el resumen copiado llevan el mismo nombre que su fila
de Mapas ("Consulate (Y10)").

## Criterios de aceptacion

- [x] `/api/matches/` con etiqueta de version (Y10), nombre tal cual para
      Kanal y `map_id=0`.
- [x] `/api/matches/<id>/` con la misma etiqueta.
- [x] Misma etiqueta que `by_map`, incluido "(id N)".
- [x] Resumen copiado arranca con la etiqueta (verificado por QA).
- [x] `seed_demo`, e2e y filtros `?map=` sin cambios.

## Resumen de etapas

- Diseno (arquitecto 20261030T1652Z): `aggregates.etiquetas_de_mapas(slugs)`
  sobre todas las partidas del slug; `match_list` (una consulta por pagina) y
  `match_detail` la usan; frontend sin tocar; frase en `metricas.md` (Mapa).
- Implementacion (dev 20261031T2135Z): todo el diseno; test extra de
  paginacion; test de consultas comparativo en vez de `assertNumQueries(5)`.
- Revision 2026-11-02 (revisor 20261102T0805Z-cD882za): aprobar. Dos LOW sin
  arreglar, para A8: el docstring de `etiquetas_de_mapas` dice "la misma que
  usa Mapas" (es la del selector, y Mapas sin filtros); `_opciones_de_mapa`
  repite la consulta de `etiquetas_de_mapas`.
- QA 2026-11-02 sobre 0c7be44 (qa 20261102T1206Z-cLhn4iG): aprobado.
  Evidencia completa (curl, resumen copiado, mutaciones) en el commit
  `Prueba: 71`. OMC verificación=PASS.

## Verificar en el PC

Nada: sin migracion, parser ni Electron.

## Para el humano

Nada pendiente: la decision de separar versiones la tomaste el 2026-10-28
(ficha 70).
