# 133. Ventaja numerica tirada

estado: entregado
candado: -
rama: claude/equipo-dev/133-ventaja-numerica-tirada
tipo: funcionalidad
epica: revision-de-rondas
area: backend
prioridad: 3
fuente: ALCANCE.md F5
archivos: backend/replays/analytics/metrics.py (ventaja_maxima), backend/replays/analytics/aggregates.py (thrown_advantage), backend/replays/views.py, backend/replays/urls.py, backend/tests/test_ventaja_tirada.py (nuevo), frontend/src/ventajaTirada.js (nuevo), frontend/src/ventajaTirada.test.js (nuevo), frontend/src/components/VentajaTirada.jsx (nuevo), frontend/src/pages/Duelos.jsx, frontend/e2e/humo.spec.js, docs/metricas.md
turnos: po 20261113T1926Z-ce4Pmp6, arquitecto 20261113T1926Z-cq9nfTP, dev 20261113T2157Z-chbMW9r, revisor 20261113T2156Z-cQ8Kk3s, dev 20261113T2252Z-czjsKrH, revisor 20261113T2317Z-cBbsozQ, qa 20261113T2318Z-cpCpgff, release 20261113T2318Z-cpCpgff


## PR

**Titulo:** [equipo-dev][backend] Ventaja numérica tirada en Duelos

### Que cambia

Duelos suma el panel "Ventaja numérica tirada": cuántas rondas perdió tu equipo después de quedar con uno más (o con dos o más), por lado y por mapa, y las 20 tiradas más recientes con enlace a la partida parada en esa ronda. Es el error que más duele y hasta ahora solo lo contaba la narrativa de una ronda suelta.

### Por que esto y no otra cosa

Ficha 133 (ALCANCE.md F5). Se calcula al consultar sobre el feed, como `death_state` (sin migración ni `recompute`). Descartado: agrupar mapas por nombre (se juntaban las versiones de un rework) y medir cada baja sola (un trade del mismo segundo inventaba un +1).

### Como se probo

- `check.sh` (con `verificar.sh`): VERDE f8baaae, 1312 tests backend, 427 vitest, 115 e2e.
- Tests nuevos: `backend/tests/test_ventaja_tirada.py` (28: regla `ventaja_maxima` con eliminación, clutch, trade del mismo segundo, post-plant, abandono y 5v4 de arranque; agregado con tiradas, grupos, lado, mapa por versión, sin ganador, lista con orden y tope, filtros, consultas fijas), `ventajaTirada.test.js` (etiquetas y enlace), e2e `Duelos muestra la ventaja numerica tirada` (números de la API, enlace que abre la ronda).
- QA: base sembrada con 8 escenarios, recalculados a mano y comparados con la API; bordes de filtros por `curl`; Chromium claro y oscuro con consola limpia, teclado y contraste; 4 mutaciones, todas caen.
- OMC: diseño plan=— · implementación revisión=2+2 hallazgos (4 arreglados) · revisión 1 = 8 hallazgos (1 HIGH, 1 MEDIUM arreglados) · revisión 2 = 6 hallazgos (0 HIGH) · QA verificación=PASS
- Skills del repo: statistical-analysis, testing-strategy, ux-copy, systematic-debugging (Dev); accessibility-review, validate-data y design-critique no disponibles en la QA, equivalentes a mano.

### Riesgos y lo que no entra

Sin migración ni `recompute`. Dos consultas correlacionadas como `death_state`, constantes por número de rondas (`assertNumQueries`). Costo documentado en `metricas.md`: las bajas del último reloj de la ronda se miden de a una (por el reloj congelado tras el plant), así que un trade simultáneo que cierra una ronda sin plant cuenta +1. Fuera: rondas dadas vuelta en inferioridad (F12), quién murió después de la ventaja, señales del Coach.

### Como probarlo en 2 minutos

```powershell
cd backend; python manage.py seed_demo; python manage.py runserver
```

Abrir `http://127.0.0.1:8000/duelos`: panel "Ventaja numérica tirada" con el total, las tablas por ventaja, lado y mapa, y "Últimas tiradas". Filtrar por lado cambia los números; un clic en una fecha de "Últimas tiradas" abre la partida en esa ronda.

### Para el humano

- Calibrar con la base real el aviso de muestra (30 rondas con ventaja por fila).
- Se calcula al consultar, no al importar (precedente `death_state`); si se quiere columna en `RoundPlayer`, ficha propia.

### Candidatos descubiertos

Ninguno.

## Que gana quien usa la app

Cuantas rondas perdio tu equipo despues de quedar con un jugador mas (o
dos), por lado y por mapa, con enlace a cada una para volver a verla. Es el
error que mas duele y el marcador no lo muestra; hoy solo lo cuenta la
narrativa de una ronda suelta en el detalle de partida.

## Criterios de aceptacion

- [ ] Agregado nuevo en `aggregates.py`: recorre las bajas de cada ronda en
      orden de reloj (`Event` de baja con el `team_index` de la victima;
      los abandonos cuentan como baja, igual que en `stats.py`) y marca la
      ronda si tu equipo llego a tener mas vivos que el rival y la perdio
      (`Round.my_team_won = False`). Rondas sin ganador no cuentan. Devuelve
      el total de rondas con ventaja, cuantas se tiraron y el %, por lado y
      por mapa. Test con una ronda 5v4 ganada, una 5v4 perdida y una sin
      ventaja.
- [ ] Separa ventaja de uno y de dos o mas (la maxima de la ronda). Test con
      una ronda que llego a 5v3.
- [ ] Lista de las rondas tiradas (partida, numero de ronda, mapa, lado,
      ventaja maxima) con enlace al detalle de la ronda, mas recientes
      primero y con tope; test del orden y del tope.
- [ ] Los filtros globales aplican sobre tu fila de la ronda; test con
      filtro de lado.
- [ ] Panel en una pagina que no este en `saturadas` de `ROTACION` (hoy
      Tendencias lo esta), con su nota sin rondas; e2e sobre `seed_demo`
      con los numeros de la API y consola limpia.
- [ ] Fila nueva en `docs/metricas.md` (y en `## Muestra minima` si avisa
      muestra chica).

## Fuera de alcance

- El reverso, rondas dadas vuelta en inferioridad (F12).
- Quien murio despues de la ventaja.
- Señales del Coach sobre esto.

## Diseno

(arquitecto 20261113T1926Z-cq9nfTP) Regla pura `metrics.ventaja_maxima(eventos, team_of, equipo)` con el recorrido de `estado_al_morir`; agregado `aggregates.thrown_advantage(**filters)` sobre tu fila filtrada, con feeds y equipos por `Exists` correlacionado como `death_state`; vista GET `duels/thrown-advantage/`; panel `VentajaTirada.jsx` en Duelos con lógica pura en `ventajaTirada.js`; e2e con números de la API; fila y muestra mínima en `metricas.md`. Detalle en `git log` de la rama.
OMC: plan=— · revisión=— · verificación=—

## Implementacion

(dev 20261113T2157Z-chbMW9r y 20261113T2252Z-czjsKrH) Diseño completo. Desvíos: mapas por versión (`map_slug`, `map_id`) con `etiquetas_de_mapas`; tras la primera revisión, la diferencia que deja a un equipo sin vivos no cuenta (eliminación y clutch ganado), las bajas del mismo segundo se miden juntas salvo las del último reloj (post-plant congelado, `pydissect/events.py`), y el 5v4 de arranque cuenta desde la primera salida. Tests vistos en rojo antes del código.
OMC: plan=— · revisión=4 hallazgos (4 arreglados) · verificación=—

## Revision

- 2026-11-13 sobre e1e70af (revisor 20261113T2156Z-cQ8Kk3s): corregir. HIGH (eliminación ganada contaba la ventaja del cierre) y MEDIUM (trade del mismo segundo daba +1), ambos arreglados con tests; LOW del e2e arreglado.
- 2026-11-13 sobre 4548f0f (revisor 20261113T2317Z-cBbsozQ): aprobar. MEDIUM aceptado y documentado (trade final sin plant da +1); LOW: cálculo al consultar con precedente.
OMC: plan=— · revisión=6 hallazgos (0 HIGH) · verificación=—

## QA 2026-11-13 sobre f8baaae

(qa 20261113T2318Z-cpCpgff) `check.sh` VERDE f8baaae (1312 backend, 427 vitest, 115 e2e). Base temporal (`SQLITE_PATH`, `migrate`, `tests/factories.py`) con R0 eliminación ganada, R1 5v4 perdida, R2 5v3 perdida, R3 trade del mismo segundo, R4 sin ganador, R5 abandono rival, R6 sin bajas, R7 post-plant congelado y una partida de un jugador: la API da 5 con ventaja, 4 tiradas (80 %), uno 3/3, dos o más 2/1, Ataque 2/1, Defensa 3/3, recientes R8, R6, R3, R2, igual que a mano. `curl` con `side=`, `map=zzz`, `until=foo`, `page=-1`, `days=99999999999`, `x=%00`: 200 sin errores; POST 403; base vacía en ceros. Chromium claro y oscuro: consola limpia, contraste mínimo 5,71:1, Tab y Enter abren `/partidas/1#ronda-8`, nota sin rondas con `?map=oregon`. Chunk inicial +8 B. Mutaciones (sin cierre, sin reloj final, orden invertido, sin ganador): las 4 caen. Minor de accesibilidad: los enlaces de "Últimas tiradas" se llaman por la fecha; la fila da el contexto.
OMC: plan=— · revisión=— · verificación=PASS
Skills del repo: accessibility-review, validate-data y design-critique no disponibles en esta sesion; equivalentes a mano (0 Critical, 0 Major, 1 Minor; 2 valores recalculados)

## Para el humano

- (arquitecto, no bloquea) Calibrar con la base real el aviso de muestra de 30 rondas con ventaja por fila.
- (qa, no bloquea) Se calcula al consultar, como `death_state`, y no al importar; columna en `RoundPlayer` iria en ficha propia.
