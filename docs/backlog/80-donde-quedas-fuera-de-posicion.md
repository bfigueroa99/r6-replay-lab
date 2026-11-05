# 80. Donde quedas fuera de posicion, por sitio y spawn

estado: propuesto
candado: -
rama: -
tipo: funcionalidad
epica: posicionamiento
area: fullstack
prioridad: 3
fuente: ALCANCE.md S1, del PR #1 (`claude/loop-lwjbgs`, commit 1ffdb89: pedido del usuario "en que partes del mapa suelo dormir"), cerrado sin merge el 2026-11-05; el humano devolvio la idea a `idea`. La rama queda como referencia, no se mergea
archivos: backend/replays/analytics/aggregates.py (AGGREGATES, by_site, by_spawn), backend/replays/analytics/coach.py, backend/replays/views.py, frontend/src/pages/Trends.jsx o Coach.jsx, docs/metricas.md, backend/tests, frontend/e2e/humo.spec.js
turnos: po 20261105T0230Z-c8Ahepa

## PR

(La escribe el Release manager al final.)

## Que gana quien usa la app

Saber en que sitio (defensa) o desde que spawn (ataque) te agarran mal
parado: rondas en que moriste sin sacar ninguna baja y sin que nadie te
vengara. Es "donde duermo" al nivel que el `.rec` permite (zona, no
coordenadas), y el Coach lo dice con una señal cuando una zona se aparta de
tu historial.

## Criterios de aceptacion

- [ ] Metrica nueva `fuera_de_posicion` = rondas con `died=True`, `kills=0` y
      `was_traded=False` sobre rondas jugadas, en `AGGREGATES` (sale en todo
      agregado y en los CSV sin migracion ni `recompute`); test con una base
      de 4 rondas que cubre cada condicion por separado.
- [ ] `by_site` y `by_spawn` traen la tasa por zona y la del **resto** del
      historial (para un spawn, el resto del ataque), no la del total: test
      que fija que la zona no se compara consigo misma.
- [ ] Panel "Dónde quedas fuera de posición" con las dos tablas (sitio por
      lado, spawn de ataque) en Tendencias o en el Coach (decide el
      Arquitecto; **no** una pagina nueva de mapas y sitios: esa sigue
      descartada) con muestra minima y la nota "el .rec no trae
      coordenadas: la zona es el sitio o el spawn".
- [ ] Señales del Coach `zona-dormidero` (zona peor que el resto, fuera de la
      banda de ruido) y `zona-solida` (mejor), con muestra minima; test de
      cada una y de que no salen con poca muestra.
- [ ] Fila en `docs/metricas.md`; e2e: el panel se ve en la base sembrada y
      la consola queda limpia.

## Fuera de alcance

- Posiciones dentro del sitio, angulos o heatmap: el `.rec` no trae
  coordenadas (`CLAUDE.md`).
- Reabrir la pagina de mapas y sitios retirada en 096fd52.
- Salida del spawn y enlaces a peekabooR6: es S2, otra ficha.

## Diseno

## Implementacion

## Revision

## QA

## Para el humano

- (po) El PR #1 lo hacia como pagina propia "Posicionamiento". La variante
  conservadora es un panel en una pagina existente, porque "Pagina de mapas y
  sitios" esta descartada en `ALCANCE.md` desde que se retiro (096fd52). Si
  queres la pagina propia, decilo en la ficha.
