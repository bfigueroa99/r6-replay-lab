# 71. La partida dice que version del mapa se jugo

estado: propuesto
candado: -
rama: -
tipo: funcionalidad
epica: temporada-y-modo
area: backend
prioridad: 2
fuente: idea A6 de `ALCANCE.md` ("Implementar despues de #70"; la 70 esta en `dev` desde 0fedc7b, PR #65). Fuera de alcance de la ficha 70: "listado, records, sesiones y detalle de partida". `etiqueta_de_version` (`pydissect/header.py:239`) y `etiquetas_de_version` (`replays/analytics/aggregates.py:481`) ya existen; `match_list` y `match_detail` (`replays/views.py:434` y `:543`) devuelven `map: match.map_name`
archivos: -
turnos: po 20261030T1653Z

## PR

(La escribe el Release manager al final.)

## Que gana quien usa la app

Desde la ficha 70, Mapas separa "Consulate (Y10)" de "Consulate (Y7)", pero
Partidas, el detalle de la partida y el resumen copiado siguen diciendo
"Consulate" a secas: no se sabe a que fila de Mapas suma cada partida. Con
esto la partida lleva el mismo nombre que su fila.

## Criterios de aceptacion

- [ ] `/api/matches/` devuelve en `map` la etiqueta con version para un mapa
      rehecho (`map_id` 418126004176, `ConsulateY10`: "Consulate (Y10)") y el
      nombre sin cambios para un mapa sin sufijo (Kanal) y para `map_id=0`.
      Test en `backend/tests/test_api.py`.
- [ ] `/api/matches/<id>/` devuelve la misma etiqueta en `map`. Test en
      `test_api.py`.
- [ ] Para la misma `(map_slug, map_id)`, la etiqueta del listado y del
      detalle es la misma que la fila de `by_map` (incluido el caso de un id
      que el usuario nombro en Datos igual que una version conocida, donde
      `etiquetas_de_version` le suma "(id N)"). Test que compara las dos
      salidas sobre partidas de dos versiones del mismo mapa.
- [ ] El resumen copiado (`frontend/src/resumenPartida.js:69`) arranca con
      la etiqueta. Hoy toma `match.map` del detalle, asi que alcanza con el
      criterio anterior: QA lo verifica copiando el resumen de una partida
      "(Y10)" sembrada con `factories`.
- [ ] Con `seed_demo` (todo `map_id=0`) el listado, el detalle y el e2e no
      cambian, y `?map=<slug>` y `?map=<map_id>` en `/api/matches/` filtran
      igual que antes.

## Fuera de alcance

- Records, Sesiones, el "mejor y peor mapa" del Inicio, Clutch por mapa y
  sitio, Progreso por mapa y Duelos: siguen por slug (idea A8 de
  `ALCANCE.md`).
- Filtro o etiqueta de temporada (A3).
- IDs de mapa que faltan en `MAPS` (ficha 73).
- Guardar la etiqueta en la base: se calcula al consultar, como en la 70.

## Diseno

## Implementacion

## Revision <fecha> sobre <sha>

## QA <fecha> sobre <sha>

## Verificar en el PC

## Pendiente

## Para el humano

Nada pendiente: la decision de separar versiones la tomaste el 2026-10-28
(ficha 70).
