# 53. Multikills por tamaño: 2K, 3K, 4K y ace

estado: entregado
candado: -
rama: claude/equipo-dev/53-multikills-por-tamano
tipo: funcionalidad
epica: revision-de-rondas
area: fullstack
prioridad: 3
fuente: ALCANCE.md F10 ([CS Demo Manager](https://cs-demo-manager.com/changelog), [vlr.gg](https://www.vlr.gg/188013/velaris-vs-clg-red-complexity-paradox-invitational-playoffs-lr3/?game=all&tab=performance))
archivos: backend/replays/analytics/aggregates.py, backend/replays/views.py, backend/tests/test_multikills.py, backend/tests/test_player_stats.py, backend/tests/test_api.py, frontend/src/multikills.js, frontend/src/multikills.test.js, frontend/src/pages/MatchDetail.jsx, frontend/src/pages/Jugador.jsx, frontend/src/pages/Dashboard.jsx, frontend/e2e/humo.spec.js, docs/metricas.md
turnos: po 20261017T1204Z, arquitecto 20261017T1603Z, dev 20261017T2004Z, revisor 20261018T1205Z, qa 20261018T1603Z, release 20261018T2003Z

## PR

Titulo: `[equipo-dev][fullstack] Multikills por tamaño: 2K, 3K, 4K y ace`

### Que cambia

El scoreboard de cada partida suma la columna **Multikills** (`2×2K · 1×3K · 1×ACE`:
rondas por tamaño, solo los tamaños con alguna ronda, ordenable por el total), y el
Resumen y la pagina de un jugador muestran los mismos conteos. Toda fila agregada de la
API (`totals`, `group_by`, `overview`, `player_profile`, sesiones, CSV de export) trae
`k2`, `k3`, `k4` y `aces`.

### Por que esto y no otra cosa

Ficha 53, epica `revision-de-rondas` (ALCANCE.md F10, como CS Demo Manager y vlr.gg).
`multikill_rounds` ya existia y ninguna pantalla lo mostraba. Descartado: duracion del
multikill (F8), records por tamaño (E4 ya tiene "mas bajas en una ronda"), filtro de
rondas por tamaño (va con F1) y tocar `multikill_pct` o el rating.

### Como se probo

- `./scripts/check.sh` sobre la rama con main fusionado: ver la linea de abajo.
- Tests nuevos: `test_multikills.py` (10: tamaños, ace = 5 o mas, jugadores separados,
  totals, overview por lado, perfil, filtro de lado, group_by, derive, `multikill_pct`),
  `test_un_teamkill_suma_a_las_bajas_del_autor`, `test_detalle_de_partida_trae_multikills_en_scoreboard_y_my_totals`,
  `multikills.test.js` (5) y tres e2e (scoreboard de `demo-17`, Resumen, perfil).
- QA: base sembrada con rondas de 0 a 6 bajas; API, CSV de export y UI a 1280 y 375 px
  cuadran a mano; bordes sin 500; mutacion: 4 de 4 caen.

### Riesgos y lo que no entra

Sin migracion ni recompute: sale de `RoundPlayer.kills`. Los CSV de `/api/export/`
suman 4 columnas al final. `_match_scoreboard` necesita el annotate de `MULTIKILLS`
antes del alias `kills` (SQLite: `misuse of aggregate function`); un test lo fija.

### Como probarlo en 2 minutos

```powershell
cd backend; python manage.py seed_demo; python manage.py runserver
```

Resumen: KPI **Multikills** 14 (`14×2K · 7% de tus rondas`). Partidas -> `demo-17`
(Border): columna Multikills con `2×2K` solo en BearF99. Tu perfil: "Sus números" con `14×2K`.

### Para el humano

`kills` incluye teamkills (`pydissect/stats.py:81-85`): un teamkill suma a 2K/3K/ace
igual que a Bajas, y esta documentado. Excluirlos cambiaria K/D, KPR y rating de todo
el historial: otra ficha, decision tuya.

### Candidatos descubiertos

Ninguno.

## Que gana quien usa la app

Ver cuantas rondas de 2, 3 y 4 bajas hiciste y cuantos aces, en el scoreboard de cada
partida, en el Resumen y en la pagina de un jugador.

## Criterios de aceptacion

- [x] `_match_scoreboard` agrega `k2`, `k3`, `k4`, `aces` (exactos; ace = 5 o mas).
- [x] `/api/matches/<id>/` los trae en `scoreboard` y `my_totals`; columna "Multikills".
- [x] Jugador y Resumen muestran los conteos; las claves salen de `AGGREGATES`/`derive`.
- [x] Teamkills: el test fija que hoy suman y `metricas.md` lo dice.
- [x] `docs/metricas.md` define Multikill por tamaño sin cambiar `multikill_pct`.
- [x] e2e con la columna "Multikills" y consola limpia.

## Diseno, implementacion, revision y QA (condensado; el detalle esta en `git log`)

- Arquitecto 20261017T1603Z: dict `MULTIKILLS` en `aggregates.py` dentro de
  `AGGREGATES`; `.annotate(**agg.MULTIKILLS)` previo en `_match_scoreboard`;
  `multikills.js` puro; `seed_demo` sin tocar (BearF99: 14×2K en 203 rondas).
- Dev 20261017T2004Z: diseno completo. Desvios: el e2e prueba el orden con dos clics;
  se saco "con revives" (un revive no suma baja en Siege).
- Revisor 20261018T1205Z sobre ff60754: aprobar, sin hallazgos.
- QA 20261018T1603Z sobre 97b933e: aprobado (656 backend, 104 vitest, 41 e2e; chunk
  inicial +0,4 %).

## Para el humano

- Arquitecto 2026-10-17: `RoundPlayer.kills` **incluye** teamkills (`pydissect/stats.py:81-85`). El diseno lo mantiene para que 2K/3K cuadren con la columna Bajas y lo documenta. Excluirlos de `kills` cambiaria K/D, KPR y rating de todo el historial (P10, decision tuya; seria otra ficha).
