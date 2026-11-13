# 116. En que estado de vivos mueres

estado: entregado
candado: -
rama: claude/equipo-dev/116-en-que-estado-de-vivos-mueres
tipo: funcionalidad
epica: impacto
area: fullstack
prioridad: 3
fuente: ALCANCE.md K6
archivos: backend/replays/analytics/metrics.py (estado_al_morir), backend/replays/analytics/aggregates.py (death_state), backend/replays/views.py (death_state), backend/replays/urls.py, backend/tests/test_estado_al_morir.py (nuevo), frontend/src/estadoAlMorir.js (nuevo), frontend/src/estadoAlMorir.test.js (nuevo), frontend/src/components/EstadoAlMorir.jsx (nuevo), frontend/src/pages/Duelos.jsx, frontend/e2e/humo.spec.js, docs/metricas.md
turnos: po 20261112T1603Z-cor3JBP, arquitecto 20261113T1649Z-ccPezGq, dev 20261113T1703Z-c66ztji, revisor 20261113T1651Z-cxTme8t, qa 20261113T1733Z-cudo1Sw, release 20261113T1733Z-cudo1Sw

## PR

Titulo: `[equipo-dev][frontend] Estado de vivos al morir en Duelos`

### Que cambia

Duelos suma el panel "Estado al morir": tus muertes repartidas por cuántos
quedaban vivos de cada lado justo antes de caer (5v5, 5v4, 4v5...), agrupadas
en con ventaja, en paridad y en desventaja, con el winrate de esas rondas.
Dice si mueres regalando una ventaja o con la ronda ya perdida.

### Por que esto y no otra cosa

Ficha 116 (ALCANCE.md K6, épica impacto). Se calcula al consultar sobre el
feed, como `nemesis`: guardarlo en `RoundPlayer` pedía migración y
`recompute` y la dejaba detrás de la 79. El algoritmo vive en
`metrics.estado_al_morir`, así pasarlo a columna es mecánico. Endpoint
propio (`/api/duels/death-state/`) para no pisarse con la 114 en `views.duels`.

### Como se probo

- `check.sh` (con `verificar.sh`): VERDE 16066a14c (QA, mismo codigo que la entrega), 1219 tests backend, 367 vitest, 100 e2e.
- Tests nuevos: `backend/tests/test_estado_al_morir.py` (19: 5v4 tras baja rival, abandono y teamkill restan, muerte sin evento y tras irte no entran, solo la primera muerte del feed, grupos con winrate, winrate por estado exacto, orden, sin normalizar a 5v5, filtros de lado en agregado y endpoint, base vacía, 3 consultas fijas, y la función pura); `frontend/src/estadoAlMorir.test.js`; e2e `Duelos muestra el estado de vivos al morir` en `humo.spec.js`.
- Verificacion manual (QA): base sembrada con siete rondas armadas, números recalculados a mano iguales a la API; bordes de filtros sin 500; Chromium con teclado, contraste 5.71-14.17 y consola limpia; 4 mutaciones caen en sus tests.
- OMC: plan=— · revisión=— · verificación=—
- OMC: plan=— · revisión=2 hallazgos LOW (2 arreglados) · verificación=—
- OMC: plan=— · revisión=7 hallazgos (1 arreglado, test; 0 CRITICAL/HIGH) · verificación=—
- OMC: plan=— · revisión=— · verificación=PASS (omc-verifier, 5/5 criterios)
- Skills del repo: statistical-analysis (denominador = rondas con ganador, `n` visible por fila, sin promedio de promedios), testing-strategy (Django para algoritmo y agregado, vitest para etiquetas y avisos, humo e2e).
- Skills del repo: accessibility-review (0 Critical, 0 Major; contraste 5.71-14.17), design-critique (0 nuevos; repite el LOW del Revisor), validate-data (sin hallazgos; 2 valores recalculados a mano iguales a la API).

### Riesgos y lo que no entra

Sin migración ni `recompute`. Tres consultas por request (fijadas en un
test), con el feed de las rondas en que moriste, como `nemesis`. Fuera: el
reverso (tus bajas por estado, K8) y probabilidad de ganar por estado (K1, K2).
LOW conocido: con cero duelos contra rivales la página muestra su vista
vacía y no el panel.

### Como probarlo en 2 minutos

```powershell
cd backend; python manage.py test tests.test_estado_al_morir
cd frontend; npm run build; cd ..\backend; python manage.py runserver
```

Abrir `/duelos`: al final, "Estado al morir" con la tabla por situación y la
del estado exacto; `?side=Defense` cambia los números.

### Para el humano

Aviso, no frena: el estado se calcula al consultar y no en columnas al
importar (ver `## Para el humano` de la ficha).

### Candidatos descubiertos

Ninguno

## Que gana quien usa la app

Tus muertes repartidas por el estado de vivos de la ronda en el instante en
que caes (5v5, 5v4, 4v5, 3v3...) y el winrate de la ronda en cada caso. Dice
si mueres regalando una ventaja o cuando la ronda ya estaba perdida, que el
K/D y las aperturas no separan.

## Criterios de aceptacion

- [ ] Un agregado devuelve, por estado `tuyos vivos v rivales vivos` justo
      antes de tu muerte, `deaths` y `winrate` de esas rondas (sobre las
      que tienen ganador). Test con una ronda armada: caes cuando ya habia
      caido un rival y ninguno de los tuyos cuenta en `5v4`.
- [ ] Un `PlayerLeave` cuenta como baja para el estado (como
      `pydissect/stats.py`), un teamkill tambien resta un vivo de tu equipo,
      y una muerte tuya sin evento en el feed no entra. Test de los tres.
- [ ] Ventaja, paridad y desventaja agregadas (`ahead`, `even`, `behind`)
      ademas del estado exacto, con su winrate. Test.
- [ ] Los filtros globales aplican (lado, mapa, operador, tipo, fechas,
      sesion). Test de lado.
- [ ] Se ve en la UI con la muestra minima de `metricas.md` como aviso; sin
      muertes, un texto y no un error; e2e de humo por esa pagina con la
      consola limpia. Fila nueva en `docs/metricas.md` ("Estado al morir").

## Fuera de alcance

- El reverso, tus bajas por estado (K8): otro tramo de la epica.
- Probabilidad de ganar por estado o impacto por baja (K1, K2).
- Partidas con menos de 5 por lado: el estado se cuenta con los jugadores
  que hay, sin normalizar a 5v5.

## Diseno

(arquitecto 20261113T1649Z-ccPezGq) `metrics.estado_al_morir(eventos, team_of)`
recorre el feed como `_quedar_solo` y anota `(aliados, rivales)` contando a la
victima en su primera muerte; `PlayerLeave` y teamkill restan antes.
`aggregates.death_state` con `Exists` correlacionado (sin `round_id__in`),
`GET /api/duels/death-state/`, panel `EstadoAlMorir.jsx` al final de Duelos,
fila en `metricas.md`. Detalle en `git log`.
OMC: plan=— · revisión=— · verificación=—

## Implementacion

(dev 20261113T1703Z-c66ztji) Diseno completo; desvios menores: orden de filas
por indice de la API y nota de `sin_feed` que nombra tambien la muerte
posterior a irte. verificar.sh: VERDE c8d3560.
Skills del repo: statistical-analysis, testing-strategy.
OMC: plan=— · revisión=2 hallazgos LOW (2 arreglados) · verificación=—

## Revision 2026-11-13 sobre 6fc0a6b

(revisor 20261113T1651Z-cxTme8t) Aprobar, 0 CRITICAL/HIGH. Arreglado por el
Revisor: `test_cada_estado_exacto_trae_su_winrate` (ningun test miraba el
winrate por estado exacto). Sin cambio: MEDIUM de regla (al consultar y no al
importar, decision del Diseno), LOW de texto en `metricas.md`, LOW de la
vista sin-duelos que esconde el panel, LOW del texto "con estos filtros" sin
filtros, LOW del nombre `rounds`. Detalle en `git log`.
OMC: plan=— · revisión=7 hallazgos (1 arreglado, test; 0 CRITICAL/HIGH) · verificación=—

## QA 2026-11-13 sobre 16066a1

(qa 20261113T1733Z-cudo1Sw) verificar.sh VERDE 16066a14c (1219, 367, 100).
Base sembrada de siete rondas: 4 muertes (5v3, 5v4, 5v5, 3v5), `sin_feed` 2,
ahead 100 %, even 0 %, behind 0 %, recalculado a mano igual a la API. Bordes
(`until=foo`, `page=-1`, `side=foo`, `days` enorme, `session=abc`) sin 500.
Chunk inicial 199.91 -> 200.10 kB. Chromium: teclado, `aria-sort`, CSV,
contraste 5.71-14.17, consola limpia, texto sin muertes. 4 mutaciones caen.
Veredicto: `aprobado`. Comandos completos en `git log`.
Skills del repo: accessibility-review (0 Critical, 0 Major), design-critique (0 nuevos), validate-data (2 valores recalculados).
OMC: plan=— · revisión=— · verificación=PASS (omc-verifier, 5/5 criterios)

## Para el humano

- 2026-11-13 (arquitecto): el estado se calcula al consultar, sobre el feed, y no
  en columnas de `RoundPlayer` al importar (lo que pide `CLAUDE.md` para las
  metricas) para no frenarla detras de la migracion de la 79. Si preferis la
  columna, es mecanico: la funcion ya vive en `metrics.py`. No frena nada.
