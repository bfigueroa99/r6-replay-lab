# 127. Partidas que van a prorroga: cuantas ganas

estado: entregado
candado: -
rama: claude/equipo-dev/127-partidas-que-van-a-prorroga
tipo: funcionalidad
epica: lado-y-marcador
area: fullstack
prioridad: 3
fuente: ALCANCE.md B22 (salio del Fuera de alcance de la 115)
archivos: backend/replays/analytics/aggregates.py, backend/replays/views.py, backend/tests/test_prorroga_por_lado.py, frontend/src/prorrogaPorLado.js, frontend/src/prorrogaPorLado.test.js, frontend/src/pages/Trends.jsx, frontend/e2e/humo.spec.js, docs/metricas.md
turnos: po 20261113T1858Z-cxdASk3, arquitecto 20261113T2157Z-cG2vDSe, dev 20261113T2252Z-cQac5RQ, revisor 20261113T2318Z-cpCpgff, qa 20261113T2317Z-cBbsozQ, release 20261113T2317Z-cBbsozQ

## PR

Titulo: `[equipo-dev][fullstack] Partidas que van a prorroga: cuantas ganas por lado`

### Que cambia

En Tendencias, la tabla "Prórroga por lado" suma dos columnas: Partidas (las que llegaron a prórroga, por el lado con el que la arrancaste) y Partidas ganadas (% sobre las que tienen resultado). Responde "cuando llego a prórroga en defensa, ¿la gano?", que el winrate de ronda de la 115 no contesta.

### Por que esto y no otra cosa

Ficha 127, del Fuera de alcance de la 115 (ALCANCE.md B22). Sin tarjeta nueva porque Tendencias esta saturada; no duplica "Margen final", que junta todas las prorrogas.

### Como se probo

- `check.sh` (con `verificar.sh`): VERDE 6920b8eca, 1293 tests backend, 425 vitest, 114 e2e.
- Tests nuevos: `PartidasAProrrogaPorLadoTests` en `backend/tests/test_prorroga_por_lado.py` (caso 2/1 del criterio, primera ronda de prorroga y no la mayoria, sin prorroga no entra, `won` nulo, filtro de lado, de mapa, de operador que deja solo rondas normales, sin prorrogas, clave en `/api/trends/`); vitest de `prorrogaPorLado.js` (union por lado, lado sin partidas, compatibilidad, `conPocasPartidas`); e2e de humo de la clave.
- Verificacion manual (QA): base sembrada con 3 partidas a prorroga; API y SQL a mano coinciden (Defensa 2 partidas, 50 %; Ataque 1 sin resultado, `—`); tabla vista en Chromium con avisos y consola limpia; 4 mutaciones atrapadas.
- OMC: Diseno `plan=— · revisión=— · verificación=—`; Implementacion `plan=— · revisión=2 hallazgos LOW (1 arreglado) · verificación=—`; Revision `plan=— · revisión=3 hallazgos (0 arreglados; 0 CRITICAL/HIGH) · verificación=—`; QA `plan=— · revisión=— · verificación=PASS`.
- Skills del repo: statistical-analysis, testing-strategy (diseno e implementacion); ux-copy (implementacion); accessibility-review y validate-data (QA).

### Riesgos y lo que no entra

Sin migracion ni `recompute`. `seed_demo` no trae prorrogas: el e2e no dibuja las columnas (cubierto por la QA manual). Fuera: winrate de ronda en prorroga (ya esta), partir por cantidad de prorrogas, señal del Coach.

### Como probarlo en 2 minutos

```
cd backend; python manage.py test tests.test_prorroga_por_lado
cd frontend; npm test -- prorrogaPorLado
cd backend; python manage.py runserver   # abrir /tendencias con replays que tengan prorroga
```
Tiene que verse en "Prórroga por lado" las columnas Partidas y Partidas ganadas; con Lado = Defensa, una sola fila.

### Para el humano

Nada.

### Candidatos descubiertos

Ninguno.

## Que gana quien usa la app

En Tendencias, junto a la prorroga por lado de la 115 (winrate de ronda), el
winrate de partida de las que llegaron a prorroga, en la misma tabla,, partido por el lado con el
que la arrancaste: lo que se juega en la prorroga es la partida, no una ronda.
Responde "cuando llego a prorroga en defensa, ¿la gano?".

## Criterios de aceptacion

- [ ] Un agregado nuevo en `replays/analytics/aggregates.py` devuelve, por
      lado de tu primera ronda de prorroga (`Round.overtime_number` mas bajo
      `> 0` de la partida, su `Round.my_side`), `matches`, `wins`,
      `decided` y `winrate` (claves de `by_start_side`) (sobre las partidas con `Match.won` no nulo).
      Test con tres partidas a prorroga (dos arrancadas en defensa, una
      ganada; una en ataque, ganada) -> defensa 2 partidas 50 %, ataque 1
      partida 100 %.
- [ ] Una partida sin prorroga no entra; una con `won` nulo cuenta en
      `matches` y no en `decided` ni en el winrate. Test.
- [ ] Los filtros globales de partida (mapa, tipo, modo, fechas) aplican; con
      `?side=` solo sale la fila de ese lado (como `by_overtime_side`). Test.
- [ ] Se ve en Tendencias como columnas nuevas (Partidas, % ganadas) de la
      tabla de prorroga por lado de la 115, sin tarjeta nueva (la pagina esta
      en `saturadas` de `ROTACION`), con el aviso de muestra de la pagina (se
      avisa, no se oculta); un lado sin partidas a prorroga muestra `—`. e2e
      de humo pasa por ahi con la consola limpia.
- [ ] Fila nueva en `docs/metricas.md` ("Partidas a prorroga por lado").

## Fuera de alcance

- Winrate de ronda en prorroga (ya lo da la 115).
- Partir por cuantas prorrogas hubo o por el marcador al llegar.
- Sumarlo al Coach como señal.

## Diseno

(arquitecto 20261113T2157Z-cG2vDSe) Una sola forma: `by_start_side` leyendo la primera ronda de prorroga. `_lado_de_prorroga` (Subquery, menor `overtime_number` y despues `number`) y `by_overtime_start_side` en `aggregates.py` (`matches`, `decided`, `wins`, `winrate`; con `?side=` solo esa fila); clave `by_overtime_start_side` en `/api/trends/`; `filasProrrogaPorLado(rows, partidas)` y `conPocasPartidas` (corte 10, el de Margen final) en `prorrogaPorLado.js`; `COLUMNAS_PRORROGA_POR_LADO` en `Trends.jsx` sin tocar `COLUMNAS_POR_TRAMO`; fila en `metricas.md`. Detalle completo en `git log` de esta ficha.

Skills del repo: statistical-analysis, testing-strategy; dataviz no aplica.
OMC: plan=— · revisión=— · verificación=—

## Implementacion

(dev 20261113T2252Z-cQac5RQ) Diseno completo sobre `origin/dev@39e22c0`, sin desvios; tests vistos en rojo antes del codigo. Revision ciega: 2 LOW, arreglado uno con `test_con_un_filtro_que_solo_deja_rondas_normales_la_partida_no_entra`. verificar.sh: VERDE c7f2142b1.

Skills del repo: statistical-analysis, testing-strategy, ux-copy.
OMC: plan=— · revisión=2 hallazgos LOW (1 arreglado) · verificación=—

## Revision 2026-11-13 sobre 45551f5

(revisor 20261113T2318Z-cpCpgff) Dos ejes, sin seguridad. Estandares: 0 hallazgos. Intencion: MEDIUM confirmado, el e2e no dibuja las columnas porque `seed_demo` no tiene prorrogas (no bloquea; lo cubrio la QA a mano); 2 LOW sin cambio (rotulo "Partidas ganadas", corte 10 duplicado de `margen.js`). verificar.sh: VERDE d0f606a86. Veredicto: aprobar -> `revisado`.

OMC: plan=— · revisión=3 hallazgos (0 arreglados; 0 CRITICAL/HIGH) · verificación=—
Skills del repo: ninguna

## QA 2026-11-13 sobre 6920b8e

(qa 20261113T2317Z-cBbsozQ) Rama al dia con `origin/dev@39e22c0`.

- **check.sh**: verificar.sh VERDE 6920b8eca (1293 backend, 425 vitest, 114 e2e).
- **Base vacia** (`R6_ENV_FILE` y `SQLITE_PATH` en el scratchpad, `migrate`, `runserver 8761`): `GET /api/trends/` -> `by_overtime_start_side` con Attack y Defense en 0 y `winrate: null`; `/tendencias` en Chromium muestra "Todavía no hay replays importados", 0 errores de consola.
- **Base sembrada** (`seed_demo`, sin prorrogas, mas 3 partidas con `tests/factories.py` por `manage.py shell`: Oregon con OT [Defense, Attack] ganada, Oregon OT [Defense] perdida, Bank OT [Attack] `won=None`; `runserver 8762`):
  - `/api/trends/` -> Attack 1 partida, 0 decididas, `winrate null`; Defense 2 partidas, 2 decididas, 1 ganada, 50.0.
  - `?side=Defense` y `?side=Attack` -> solo esa fila; `?map=bank` -> Attack 1, Defense 0; `?map=oregon` -> Defense 2 (50.0); `?map=oregon&side=Attack` -> solo Attack en 0; `?until=foo`, `?page=-1`, `?match_type=` -> 200 con los mismos numeros; `?side=foo` y `?days=-1` -> 200 y todo en 0, igual que la tabla vecina `by_overtime_side` (115).
  - **Recalculado a mano** (SQL directo: por partida, lado de la ronda con `overtime_number` minimo > 0): Attack 1 partida / 0 decididas; Defense 2 / 2 decididas / 1 ganada = API.
- **UI** (Playwright en Chromium, `/tendencias` sobre la sembrada): tabla "Prórroga por lado" con Partidas y Partidas ganadas; "Prórroga en ataque ... 1 | —", "Prórroga en defensa ... 2 | 50%"; avisos de 30 rondas y de "menos de 10 partidas a prórroga"; sin tarjeta nueva; 0 errores de consola.
- **accessibility-review** (lo que agrego la ficha son dos columnas de una tabla existente): contraste minimo medido en las celdas 5.71:1 (AA); sin controles nuevos, el boton Descargar CSV ya estaba; encabezados no ordenables como el resto de la tabla. Sin Critical ni Major.
- **validate-data** sobre la fila "Partidas a prórroga por lado" de `metricas.md`: el porcentaje es sobre `decided` y sin decididas da `—` (sin division por cero); cuenta de partidas, no promedio de promedios; el `n` va en la columna Partidas y el aviso corta en 10.
- **Mutacion** (`tests.test_prorroga_por_lado`, 17 tests): ultima prorroga en vez de la primera -> 2 fallan; sin excluir `won` nulo -> 1; ignorar `?side=` -> 1; `overtime_number__gte=0` -> 1. Revertidas, arbol limpio.
- **Chunk inicial**: el diff de `frontend/src` vive en `Trends.jsx` (lazy) y `prorrogaPorLado.js`, que solo importa `Trends.jsx`; `index-*.js` no crece por la ficha.
- Sin migracion, `recompute`, parser, Electron ni `.ps1`: nada para `## Verificar en el PC`.

Limite que ya marco la revision: `seed_demo` no trae prorrogas y el e2e no dibuja las columnas nuevas; cubierto aca con la base sembrada. No bloquea.

Veredicto: `aprobado`.

Skills del repo: accessibility-review (0 Critical, 0 Major; contraste 5.71:1), validate-data (sin hallazgos; 2 valores recalculados a mano = API).
OMC: plan=— · revisión=— · verificación=PASS (omc-verifier: 5 criterios PASS, 2 huecos menores declarados)

## Para el humano

(nada)
