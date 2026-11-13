# 114. Qué operadores te abren

estado: entregado
candado: -
rama: claude/equipo-dev/114-que-operadores-te-abren
tipo: funcionalidad
epica: rivales
area: fullstack
prioridad: 3
fuente: ALCANCE.md D7
archivos: backend/replays/analytics/aggregates.py (openings_by_operator), backend/replays/views.py (duels), backend/tests/test_duels.py, frontend/src/operadoresQueTeAbren.js (nuevo), frontend/src/operadoresQueTeAbren.test.js (nuevo), frontend/src/pages/Duelos.jsx, frontend/e2e/humo.spec.js, docs/metricas.md
turnos: po 20261112T1204Z-chGLrtC, arquitecto 20261113T1203Z-cWfR3tT, dev 20261113T1643Z-c4P1LiD, revisor 20261113T1703Z-ctZvzXQ, qa 20261113T1732Z-cdpsq83, release 20261113T1732Z-cdpsq83

## PR

Titulo: `[equipo-dev][fullstack] Qué operadores te abren, en Duelos`

### Que cambia

Duelos suma el panel "Operadores que te abren": por operador rival y por tu
lado, cuántas veces te sacó en el primer duelo de la ronda (Te abre), cuántas
lo sacaste tú (Le abres), el balance, cuánto ganas esas aperturas y qué parte
de tus aperturas perdidas de ese lado se lleva. `/api/duels/` trae la clave
nueva `opening_operators`.

### Por que esto y no otra cosa

Ficha 114 (ALCANCE.md D7). "Por operador rival" cuenta todos los duelos;
la apertura por persona ya estaba en "Por rival" (ficha 108, descartada).
Por mapa o sitio queda fuera (D2).

### Como se probo

- `check.sh` (con `verificar.sh`): VERDE sobre la rama fusionada con dev
  (1211 tests backend, 365 vitest, 100 e2e).
- Tests nuevos: `OperadoresQueTeAbrenTests` (11: Ash 2/1 con share 100 y
  winrate 33.3; solo la primera baja; teamkill y muerte sin autor no suman;
  teamkill de apertura no pesa en el share; operador vacío o `Unknown(...)`
  sin fila pero en el share; separa por lado; filtro de lado y de mapa;
  muestra mínima y orden; la API con la muestra del selector), vitest
  `operadoresQueTeAbren.test.js` (3), e2e `Duelos muestra los operadores que
  te abren`.
- QA: API en base vacía y sembrada con valores recalculados a mano (share
  Ash 66.7, winrate 33.3), bordes sin tracebacks, accesibilidad del panel en
  Chromium (contraste, teclado, `aria-sort`, vacío), mutación de 3 tests.
- OMC: plan=— · revisión=3 hallazgos (3 arreglados; 0 CRITICAL/HIGH) · verificación=— (implementacion)
- OMC: plan=— · revisión=4 hallazgos LOW (1 cubierto con test; 3 no son hallazgo) · verificación=— (revision)
- OMC: plan=— · revisión=— · verificación=PASS (qa)
- Skills del repo: statistical-analysis, testing-strategy (diseno); modern-web-guidance, ux-copy (implementacion); accessibility-review, validate-data (qa).

### Riesgos y lo que no entra

Dos consultas más en `/api/duels/` con la subquery de primer evento (las
mismas que ya corre `nemesis`). Sin migración, sin `recompute`. Fuera:
por persona (ya existe), por mapa o sitio, aperturas entre compañeros.

### Como probarlo en 2 minutos

```powershell
cd backend; python manage.py seed_demo; python manage.py runserver
```

Abrir `http://127.0.0.1:8000/duelos`: debajo de "Por operador rival" está
"Operadores que te abren" con filas (operador, lado, te abre). Filtro de lado
Defensa: solo filas de defensa. Muestra mínima 1: suma filas en las dos
tablas de operador.

### Para el humano

Nada.

### Candidatos descubiertos

Ninguno.

## Que gana quien usa la app

En Duelos, por lado, qué operadores rivales te sacan en el primer duelo de la
ronda y a cuáles abres tú, con cuántas veces y en qué proporción de tus
aperturas perdidas: a qué operador tienes que aprender a jugarle la entrada.

## Criterios de aceptacion

- [x] `/api/duels/` devuelve `opening_operators` (operador rival y tu lado:
      `opened_you`, `you_opened`, `share`, balance). Test Ash 2/1.
- [x] Teamkill, baja sin autor, operador vacío o `Unknown(...)` no suman. Tests.
- [x] Respeta filtros globales, separa por lado, muestra mínima documentada,
      orden por `opened_you` descendente.
- [x] Tabla en Duelos, vacío con texto; e2e de humo con consola limpia.
- [x] Fila "Operadores que te abren" en `docs/metricas.md`.

## Diseno, Implementacion y Revision

(arquitecto 20261113T1203Z-cWfR3tT; dev 20261113T1643Z-c4P1LiD; revisor
20261113T1703Z-ctZvzXQ) `openings_by_operator` sobre `_duelos` +
`_PRIMER_EVENTO` como `nemesis`; `share` sobre todas tus muertes de apertura
contra rivales del lado (incluidas las sin fila). Revision: aprobar; el
hallazgo L3 (teamkill de apertura en el share) quedo cubierto con
`test_un_teamkill_de_apertura_no_pesa_en_el_share`. Detalle en `git log`.

## QA 2026-11-13 sobre 30dbc7e

(qa 20261113T1732Z-cdpsq83) Aprobado: verificar.sh VERDE 30dbc7e1b; API en
base vacia y sembrada (Ash/Attack 2/1, share 66.7 y winrate 33.3
recalculados a mano; Thorn/Defense 1/0, 100); bordes `until=foo`,
`page=-1`, `min_duels=foo|0|-1|enorme`, `side=Banana` sin tracebacks; chunk
inicial sin cambio (199.91 kB); accesibilidad del panel sin Critical ni
Major; 3 mutaciones caen. Detalle en `git log`.

Skills del repo: accessibility-review (0 Critical, 0 Major), validate-data (share 66.7 y winrate 33.3 recalculados).
OMC: plan=— · revisión=— · verificación=PASS

## Para el humano

(nada)
