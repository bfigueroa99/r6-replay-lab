# 36. Primera mitad, segunda mitad y prorroga

estado: propuesto
candado: -
rama: -
tipo: funcionalidad
epica: lado-y-marcador
area: fullstack
prioridad: 2
fuente: ALCANCE.md B1; `Round.overtime_number` (`backend/replays/models.py:89`) se guarda en `ingest.py:201` y ninguna vista lo usa
archivos: backend/replays/analytics/aggregates.py, backend/replays/views.py, frontend/src/pages/Trends.jsx, docs/metricas.md, backend/tests/, frontend/e2e/
turnos: po 20261013T0511Z

## PR

(La escribe el Release manager al final: titulo `[equipo-dev][area] Titulo`,
cuerpo segun `.claude/skills/equipo-dev/plantilla-pr.md` y una seccion
"Como probarlo en 2 minutos" con comandos exactos.)

## Que gana quien usa la app

En Tendencias ve su winrate de ronda y su rating en la primera mitad, en la
segunda y en la prorroga, y el winrate de partida segun si arranco atacando o
defendiendo. Hoy solo hay "por numero de ronda", que no dice si te cuesta
cerrar ni como rindes cuando la partida se alarga.

## Criterios de aceptacion

- [ ] `GET /api/trends/` devuelve una clave nueva `by_half` con tres filas
      (`first`, `second`, `overtime`), cada una con los mismos campos que una
      fila de `by_round_number` (`rounds`, `winrate`, rating, etc.). Una fila
      sin rondas sale con `rounds: 0` y metricas `null`, nunca da 500.
- [ ] La mitad se deduce de los datos, no de un numero fijo de rondas por
      modo: `overtime` = rondas con `overtime_number > 0`; `first` = rondas
      sin prorroga cuyo `my_side` es el de la ronda 1 de esa partida;
      `second` = el resto sin prorroga. Test con una partida armada a mano de
      6 rondas (3 y 3) mas 2 de prorroga que afirma 3/3/2.
- [ ] `GET /api/trends/` devuelve `by_start_side` con dos filas
      (`Attack`, `Defense`): partidas y winrate de partida segun el `my_side`
      de su ronda 1. Una partida sin `my_side` en la ronda 1 no cuenta.
- [ ] Los filtros comunes (`map`, `days`, `ranked_only`, `session`...)
      aplican igual que a `by_round_number`; test con `?map=` que cambia el
      conteo.
- [ ] La pagina Tendencias muestra las dos tablas (o barras) con su titulo
      en español, y el e2e la renderiza sin errores de consola.
- [ ] `docs/metricas.md` tiene una fila por cada numero nuevo (mitad,
      prorroga, lado inicial).

## Fuera de alcance

- Rendimiento bajo presion (match point, ir abajo o arriba): es B2, el tramo
  siguiente de la epica.
- Cambiar `by_round_number` o su grafico.
- Reglas del coach sobre mitades: si el Arquitecto ve una obvia, la anota
  como idea en `ALCANCE.md`, no aca.

## Diseno

(Arquitecto) Nota del PO: `seed_demo` hoy no genera rondas de prorroga. Si
se extiende para que el e2e vea la fila `overtime`, cambian los numeros que
afirman otros e2e: agregar la prorroga en partidas nuevas al final del seed
en vez de tocar las existentes, o dejar la fila vacia en el e2e.

## Implementacion

(Dev) Que quedo, que no, desvios del diseno y por que.

## Revision <fecha> sobre <sha>

(Revisor) Formato de `revision.md`. Veredicto al final.

## QA <fecha> sobre <sha>

(QA) Un comando y un resultado por criterio de aceptacion.

## Verificar en el PC

(QA, solo si toca migraciones, recompute, parser, Electron o `.ps1`.)

## Pendiente

## Para el humano
