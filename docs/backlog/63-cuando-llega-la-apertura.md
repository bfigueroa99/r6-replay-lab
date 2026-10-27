# 63. Cuando llega la apertura

estado: entregado
candado: -
rama: claude/equipo-dev/63-cuando-llega-la-apertura
tipo: funcionalidad
epica: lado-y-marcador
area: fullstack
prioridad: 3
fuente: ALCANCE.md B14
archivos: backend/replays/analytics/aggregates.py, backend/replays/views.py, backend/tests/test_deaths.py, frontend/src/pages/Trends.jsx, frontend/e2e/humo.spec.js, docs/metricas.md
turnos: po 20261024T1204Z, arquitecto 20261024T1605Z, dev 20261027T0004Z, revisor 20261027T0404Z, qa 20261027T0810Z, release 20261027T0810Z

## PR

Titulo: `[equipo-dev][fullstack] Cuándo llega la apertura en Tendencias`

### Que cambia

Tendencias suma la tabla "Cuándo llega la apertura": por lado, en que segundo
de la fase de accion cae la primera baja de la ronda (temprano < 30 s, medio
30-90 s, tarde 90 s o mas, sin bajas) y tu winrate y "Primera baja tuya %" en
cada tramo, con CSV `apertura-por-tiempo`. `/api/trends/` trae la clave
`opening_timing`.

### Por que esto y no otra cosa

Ficha 63 (ALCANCE B14, epica lado-y-marcador). Las aperturas de hoy dicen
quien gana el primer duelo, no cuando llega. "Primera baja tuya" sale de
`opening_kill` de tu equipo para cuadrar con Duelos de apertura. Sin
migracion: una consulta con Subquery + Exists al consultar.

### Como se probo

- `./scripts/check.sh`: Todo en verde (788 tests backend, 120 frontend, build, 50 e2e).
- `AperturaPorTiempoTests` (8 tests): tramos 10/60/120 s, bordes 29.9/30/90,
  primera baja por `order` y no por `elapsed`, ronda sin ganador afuera, sin
  bajas, apertura de un companero, `side=Attack`, base vacia en la API.
- e2e `Tendencias muestra cuando llega la apertura` sobre `seed_demo`.
- QA: base vacia y sembrada con filtros borde, UI en Chromium con CSV, chunk
  inicial sin cambio, 4 mutaciones que caen en su test.

### Riesgos y lo que no entra

Sin migracion ni `recompute`. Un evento sin reloj (0.0 s) cae en Temprano,
como en "Cuando mueres". Afuera: el corte por mapa y todo lo anclado al plant.

### Como probarlo en 2 minutos

```
cd frontend; npm run build
cd ../backend; python manage.py runserver
```

Abrir `/tendencias`: la tabla "Cuándo llega la apertura" aparece debajo de
"Cuando mueres" con 8 filas. `curl -s 'localhost:8000/api/trends/?side=Attack'`
trae `opening_timing.defense` con `rounds: 0` en las 4 filas.

### Para el humano

- Calibrar con la base real los cortes 30/90 s (`APERTURA_TEMPRANA`,
  `APERTURA_TARDIA` en `aggregates.py`).
- Aviso: una apertura que es teamkill de tu equipo cuenta como "Primera baja
  tuya", igual que en Duelos de apertura. Corregirlo en `metrics.py` cambia un
  numero que ya se muestra: pedilo en `## Para el equipo` si lo queres.

### Candidatos descubiertos

Ninguno (el corte por mapa queda como tramo posible en ALCANCE).

## Que gana quien usa la app

El segundo de la fase de accion en que cae la primera baja de la ronda y tu
winrate segun si llego temprano, al medio o tarde.

## Implementacion

(dev 20261027T0004Z) Diseno completo, sin migracion. `opening_timing` en
`aggregates.py` (Subquery del `elapsed` del primer `Kill`/`Death` por `order`
+ Exists de `opening_kill` en tu `team_index`, plegado en Python), expuesta en
`views.trends`; panel en `Trends.jsx`; 8 tests; e2e; fila en `metricas.md`.
Desvio: en "Sin bajas" `opening_won_pct` es `None` (un 0 % se leia como
aperturas perdidas).

## Revision 2026-10-27 sobre 093fffc

(revisor 20261027T0404Z) Aprobar. Hallazgos menores a `## Para el humano`:
teamkill como apertura tuya (heredado de Duelos de apertura) y evento sin reloj
en Temprano (documentado).

## QA 2026-10-27 sobre fbbc073

(qa 20261027T0810Z) Aprobado. check.sh verde; base vacia 200 con tramos en
cero en todos los filtros borde; base sembrada con plant como primer evento,
ronda sin ganador, sin bajas, teamkill, 0.0 s, partida de un jugador, nick
repetido y lado `Unknown`: numeros iguales a los esperados a mano; UI y CSV en
Chromium sin errores de consola; chunk inicial 187.83 kB igual que main;
mutaciones de `order`, filtro de ganador, borde y `team_index` caen. Detalle
en `git log` de la rama.

## Para el humano

- Calibrar con la base real: los cortes 30/90 s solo se probaron con datos sinteticos.
- Teamkill como apertura tuya (aviso del Revisor, no bloquea), ver `## PR`.
