# 77. Selector de tipo de partida en la barra de filtros

estado: propuesto
candado: arquitecto 2026-11-05T02:48Z
rama: -
tipo: funcionalidad
epica: temporada-y-modo
area: frontend
prioridad: 2
fuente: ALCANCE.md A1; replica/features.csv ("Soporte de ranked, unranked y custom", must, clone partial: falta el selector en Filters.jsx); PR #14 cerrado sin merge el 2026-11-05 ya no lo cubre
archivos: frontend/src/components/Filters.jsx, frontend/src/filtros o api.js si hace falta, frontend/e2e/humo.spec.js
turnos: po 20261105T0230Z-c8Ahepa

## PR

(La escribe el Release manager al final.)

## Que gana quien usa la app

Hoy la barra de filtros solo deja elegir "Solo ranked": quien juega unranked,
rapidas o customs no puede ver sus numeros de ese tipo sin mezclarlos con el
resto. Con un selector "Tipo" (Todos, Ranked, Unranked, la que haya en la base)
todo lo que usa la barra (Inicio, Coach, Operadores, Compañeros, Tendencias...)
se filtra por tipo de partida, y la app cierra un `must` de la referencia que
estaba en `partial`.

## Criterios de aceptacion

- [ ] La barra de filtros muestra un `<select>` "Tipo" con "Todos" y una opcion
      por cada valor de `match_types` de `/api/filters/` (sembrado: al menos
      Ranked y uno mas); elegir uno manda `match_type=<valor>` a la API (vitest
      sobre la funcion que arma los parametros, o e2e mirando la request).
- [ ] Con `match_type=Ranked`, `/api/overview/` da los mismos numeros que con
      `ranked_only=1` sobre la base sembrada (test backend: los dos caminos ya
      existen en `base_queryset`; el test fija que coinciden).
- [ ] "Solo ranked" y el selector no se contradicen: o el checkbox desaparece
      reemplazado por el selector, o marcarlo fija el selector en Ranked y
      elegir otro tipo lo desmarca (la eleccion es del Arquitecto; la variante
      conservadora es reemplazar el checkbox y aceptar `ranked_only` en la
      API como hasta ahora).
- [ ] "Limpiar" vuelve el selector a "Todos".
- [ ] e2e: en Chromium, elegir un tipo en el Inicio cambia el total de rondas
      que muestra y la consola queda limpia.

## Fuera de alcance

- Filtro por modo de juego (bomba, rehenes...): es A7, otra ficha.
- Filtros en la URL (A10) y filtros en el listado de Partidas (F16, ficha 78).
- Etiquetas legibles para tipos desconocidos: ya las da Datos (A2).

## Diseno

## Implementacion

## Revision

## QA

## Para el humano
