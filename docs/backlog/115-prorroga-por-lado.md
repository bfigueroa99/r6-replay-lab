# 115. Prorroga por lado

estado: entregado
candado: -
rama: claude/equipo-dev/115-prorroga-por-lado
tipo: funcionalidad
epica: lado-y-marcador
area: fullstack
prioridad: 3
fuente: ALCANCE.md B18
archivos: backend/replays/analytics/aggregates.py (by_overtime_side, PRORROGA_LADOS), backend/replays/views.py (trends), backend/tests/test_prorroga_por_lado.py, frontend/src/prorrogaPorLado.js, frontend/src/prorrogaPorLado.test.js, frontend/src/pages/Trends.jsx, frontend/e2e/humo.spec.js, docs/metricas.md
turnos: po 20261112T1603Z-cor3JBP, arquitecto 20261112T2004Z-cbaTGDt, dev 20261113T1203Z-cWfR3tT, revisor 20261113T1603Z-cHj1H4k, qa 20261113T1643Z-c4P1LiD, release 20261113T1651Z-cxTme8t


## PR

Titulo: `[equipo-dev][frontend] Prórroga por lado en Tendencias`

### Que cambia

En Tendencias, el panel "Por mitad de la partida" suma la tabla "Prórroga
por lado": rondas, winrate y rating de tus rondas de prórroga en ataque y en
defensa. La fila única de prórroga de hoy no cambia. Con el filtro de lado
sale solo esa fila; sin prórrogas, una nota en vez de una tabla de ceros.

### Por que esto y no otra cosa

Ficha 115 (ALCANCE.md B18, épica lado-y-marcador). Partir la fila
`overtime` de `by_half` se descartó: cambiaba una métrica que ya se muestra.
El lado inicial de la prórroga no lo trae el `.rec`.

### Como se probo

- `check.sh` (con `verificar.sh`): VERDE fd2df6c07, 1181 tests backend, 344 vitest, 97 e2e.
- Tests nuevos: `backend/tests/test_prorroga_por_lado.py` (8: partir por lado con 100 % y 0 %, rondas sin prórroga fuera, `by_half` intacto en rondas, winrate y rating, filtro de lado, filtro de mapa, sin prórroga en cero); `frontend/src/prorrogaPorLado.test.js` (4); e2e `Tendencias muestra la prórroga por lado` en `humo.spec.js`.
- Verificacion manual (QA): base sembrada con prórrogas en Club House y Border, `curl /api/trends/` con `side`, `map` y filtros raros; Chromium claro y oscuro, contrastes 14.17:1 y 5.71:1, consola limpia; mutaciones caen en sus tests.
- OMC: plan=— · revisión=— · verificación=—
- OMC: plan=— · revisión=2 hallazgos (1 arreglado, 1 LOW de comentario sin cambio; 0 CRITICAL/HIGH) · verificación=—
- OMC: plan=— · revisión=4 hallazgos (1 arreglado; 0 CRITICAL/HIGH) · verificación=—
- OMC: plan=— · revisión=— · verificación=PASS
- Skills del repo: modern-web-guidance (leida; ninguna guia aplica: tabla con `DataTable` y `h3` existentes, sin CSS ni componente nuevo), ux-copy no leida (los dos textos nuevos son los del diseno y siguen a "Primera ronda de cada lado").
- Skills del repo: accessibility-review (qa: 0 Critical/Major, contrastes 14.17 y 5.71), validate-data (qa: 3 valores recalculados coinciden), design-critique no aplica (tabla dentro de un panel existente).

### Riesgos y lo que no entra

Sin migración ni `recompute`: agrega sobre columnas que ya existen. Dos
`totals()` más por request de Tendencias, solo sobre rondas de prórroga.
Fuera: winrate de partida de las que fueron a prórroga según el lado.

### Como probarlo en 2 minutos

```powershell
cd backend; python manage.py test tests.test_prorroga_por_lado
cd frontend; npm run build; cd ..\backend; python manage.py runserver
```

Abrir `/tendencias`: bajo la tabla de mitades, "Prórroga por lado" con dos
filas (o la nota si tu base no tiene prórrogas); `?side=Defense` deja una.

### Para el humano

Nada

### Candidatos descubiertos

Ninguno

## Que gana quien usa la app

En Tendencias, la fila de prorroga se parte en ataque y defensa: winrate de
ronda y rating en las rondas de prorroga segun el lado que te toco. Responde
si en la prorroga defiendes mejor de lo que atacas, que la fila unica de hoy
no separa.

## Criterios de aceptacion

- [ ] El corte por mitad (`by_half` o una clave nueva de la misma respuesta)
      devuelve, para `overtime`, una fila por lado (`Attack`, `Defense`)
      con `rounds`, `winrate` y `rating` de las rondas con
      `Round.overtime_number > 0`. Test con una partida armada: dos rondas
      de prorroga en ataque ganadas y una en defensa perdida dan 100 % y 0 %.
- [ ] Las filas de primera y segunda mitad no cambian (test que compara la
      respuesta de esas filas antes y despues).
- [ ] Los filtros globales aplican; con el filtro de lado solo sale la fila
      de ese lado. Test.
- [ ] Se ve en Tendencias junto a la fila de prorroga actual, con el aviso
      de muestra minima de los cortes de Tendencias (30 rondas: se avisa,
      no se oculta); sin prorrogas, un texto y no un error. El e2e de humo
      pasa por Tendencias con la consola limpia.
- [ ] `docs/metricas.md` actualiza la fila de mitades y prorroga con el
      corte por lado.

## Fuera de alcance

- Winrate de partida de las que fueron a prorroga segun el lado (otro tramo).
- Lado inicial de la prorroga o quien la elige: el `.rec` no lo dice.
- Prorroga en modos sin regla de partida (A9).

## Diseno

(arquitecto 20261112T2004Z-cbaTGDt) Clave nueva `by_overtime_side` en
`/api/trends/` con `_filas_por_tramo("side", ...)` sobre `round__my_side` y
`overtime_number > 0`; `by_half` no se toca. Tabla en Tendencias con
`COLUMNAS_POR_TRAMO` y aviso de `MUESTRA_CORTE`. Detalle en `git log`.
OMC: plan=— · revisión=— · verificación=—

## Implementacion

(dev 20261113T1203Z-cWfR3tT) Diseno completo, sin desvios: `PRORROGA_LADOS`
y `by_overtime_side` en `aggregates.py`, clave en `views.trends`,
`prorrogaPorLado.js`, tabla en `Trends.jsx`, fila en `metricas.md` (las
rondas de prorroga sin lado no entran en ninguna). Tests vistos en rojo
antes del codigo. verificar.sh: VERDE 21b599c79.
Skills: no aplica.
Skills del repo: modern-web-guidance (leida; ninguna guia aplica: tabla con `DataTable` y `h3` existentes, sin CSS ni componente nuevo), ux-copy no leida (los dos textos nuevos son los del diseno y siguen a "Primera ronda de cada lado").
OMC: plan=— · revisión=2 hallazgos (1 arreglado, 1 LOW de comentario sin cambio; 0 CRITICAL/HIGH) · verificación=—

## Revision 2026-11-13 sobre 85d4b1d

(20261113T1603Z-cHj1H4k) Dos ejes de `omc-code-reviewer`: aprobar, 0
CRITICAL/HIGH/MEDIUM. Corregido por el Revisor: `test_by_half_no_cambia_ni_winrate_ni_rating`
y `rating` no nulo en `test_parte_la_prorroga_por_lado`. LOW sin cambio: el
seed no tiene prórroga, el e2e solo ve la nota vacía. Veredicto: `revisado`.
OMC: plan=— · revisión=4 hallazgos (1 arreglado; 0 CRITICAL/HIGH) · verificación=—

## QA 2026-11-13 sobre 5b06539

(qa 20261113T1643Z-c4P1LiD) verificar.sh VERDE 5b0653965. API con base
sembrada (vacía, filtros de lado y mapa, filtros raros) recalculada a mano;
Chromium claro y oscuro, 0 Critical/Major; cuatro mutaciones caen en sus
tests. Nada para verificar en el PC. Veredicto: `aprobado`.
OMC: plan=— · revisión=— · verificación=PASS

## Para el humano

(nada)
