# 79. Excluir una partida de los agregados

estado: propuesto
candado: arquitecto 2026-11-05T03:55Z
rama: -
tipo: funcionalidad
epica: datos
area: fullstack
prioridad: 3
fuente: ALCANCE.md G2; decision del humano del 2026-11-05 (POST nuevo permitido, local y con application/json, entra a la lista de CLAUDE.md al disenarse)
archivos: backend/replays/models.py (+ migracion), backend/replays/views.py, backend/replays/analytics/aggregates.py, CLAUDE.md (lista de POST), docs/metricas.md, frontend/src/pages/MatchDetail.jsx, frontend/src/pages/Datos.jsx, frontend/e2e
turnos: po 20261105T0230Z-c8Ahepa, arquitecto 20261105T0349Z-cCqeUqM

## PR

(La escribe el Release manager al final.)

## Que gana quien usa la app

Una custom con amigos, una partida en la que se cayo internet o una de
calentamiento ensucian el K/D, el rating y los winrates, y hoy la unica salida
es borrar el `.rec`. Con "Excluir de mis numeros" en el detalle de partida la
partida sigue visible en Partidas pero deja de contar en todo agregado, y un
clic la vuelve a meter: nada se borra.

## Criterios de aceptacion

- [ ] `POST /api/matches/<id>/exclude/` (nombre final del Arquitecto) con
      `{"excluded": true|false}` y `Content-Type: application/json` marca o
      desmarca la partida; sin `application/json` da 415 como los demas POST (`_es_json`; test), y el docstring de `_es_json` suma la ruta nueva, y
      una partida inexistente da 404.
- [ ] Una partida excluida no cuenta en `/api/overview/`, `/api/coach/`,
      `/api/operators/`, `/api/teammates/`, `/api/trends/` ni en el CSV de
      agregados: test que compara cada uno contra la misma base sin esa
      partida importada.
- [ ] La partida sigue en `/api/matches/` (con `"excluded": true`) y su
      detalle `/api/matches/<id>/` sigue completo; volver a incluirla deja
      los agregados exactamente como antes (test ida y vuelta).
- [ ] Reimportar el `.rec` (`import_replays --force`) no pierde la marca
      (test: `update_or_create` no pisa el campo).
- [ ] UI: boton "Excluir de mis números" / "Volver a contarla" en el detalle,
      chip "excluida" en la fila de Partidas, y Datos lista las excluidas con
      su enlace. e2e: excluir y volver a incluir una partida sembrada sin
      errores de consola.
- [ ] `CLAUDE.md` suma el POST nuevo a la lista de POST permitidos y
      `docs/metricas.md` dice que toda metrica excluye las partidas marcadas.

## Fuera de alcance

- Borrar partidas o `.rec` desde la app.
- Excluir rondas sueltas o excluir por regla (todas las customs): eso seria
  un filtro, otra idea.
- Que el resumen copiado (H4) o el CSV de partidas cambien: la partida sigue
  siendo tuya; solo sale de los agregados.

## Diseno

## Implementacion

## Revision

## QA

## Verificar en el PC

(Trae migracion: `manage.py backup` y `migrate` en el PC.)

## Para el humano

- (po) Variante conservadora elegida: la partida excluida sale de **todos**
  los agregados pero sigue en Partidas, en su detalle y en el CSV de
  partidas. Reversible con un clic; la migracion solo agrega una columna con
  default `False`. Si preferis que tambien salga del listado, decilo.
