# 68. Partidas con marcador que no cierra quedan sin resultado

estado: entregado
candado: -
rama: claude/equipo-dev/68-partidas-sin-cerrar-sin-resultado
tipo: bug
epica: -
area: backend
prioridad: 2
fuente: decision del humano 2026-10-28 en `## Para el equipo` de `ESTADO.md` (aviso de la ficha 50, idea G7 de `ALCANCE.md`); `ingest.py:169` decide `won` solo por quien tiene mas rondas
archivos: backend/replays/analytics/reglas_partida.py, backend/replays/ingest.py, backend/replays/recompute.py, backend/replays/management/commands/recompute.py, backend/tests/test_match_point.py, backend/tests/test_ingest.py, backend/tests/test_recompute.py, backend/tests/test_api.py, docs/metricas.md
turnos: po 20261029T0004Z, arquitecto 20261029T0404Z, dev 20261030T1604Z, revisor 20261030T1653Z, qa 20261030T2004Z, release 20261030T2004Z

## PR

Titulo: `[equipo-dev][backend] Partidas con marcador que no cierra quedan sin resultado`

### Que cambia

Si falta el `.rec` de la ultima ronda, una Ranked que iba 3-2 entraba como
victoria y movia el winrate de partidas. Ahora una partida cuyo marcador
final no la cierra segun la regla de su tipo (Ranked desde Y9S4: primero a 4,
prorroga a 5) queda `incompleta`: sigue en Partidas, pero sale de los
winrates de partida. `manage.py recompute` corrige lo ya importado sin
reparsear.

### Por que esto y no otra cosa

Ficha 68, decision del humano del 2026-10-28 (aviso de la ficha 50, idea G7).
Se reusa `cierra()` de `reglas_partida.py` (match point) en vez de una regla
nueva; sin migracion porque marcador, tipo y version ya estan en `Match`. Un
tipo sin regla (Unranked, Quick Match, Custom) sigue decidiendose por mas
rondas.

### Como se probo

- `./scripts/check.sh`: ruff ok, 852 tests backend (4 omitidos), 133 vitest,
  build ok, 53 e2e.
- Tests nuevos: `ReglasTests` (3-2 y 4-3 sin resultado, 4-2/2-4, 5-4 en
  prorroga, empate, sin regla), `ResultadoAlImportarTests` (ingest real con
  `MatchReader` simulado: 3-2 incompleta, 4-2 victoria),
  `ResultadoDePartidaTests` (recompute, dry-run, idempotencia, comando,
  Ranked anterior a Y9S4 intacta), `test_la_ranked_incompleta_sale_del_winrate_de_partidas`.
- QA: base sembrada con 12 partidas borde; `recompute --dry-run` cuenta 2,
  `recompute` deja 3-2 y 4-3 Ranked Y9S4 en `incompleta` y no toca Unranked,
  Y9S3 ni Quick Match; segunda corrida "Nada que recalcular";
  `/api/overview/` y `/api/matches/` cuadran a mano; 200 con JSON en los
  bordes; mutaciones caen en los tests nuevos.

### Riesgos y lo que no entra

- `recompute` ahora tambien reescribe `Match.won` (nada mas lo escribe).
- Una Ranked que termina por rendicion antes de 4 tambien queda incompleta
  (limite en `metricas.md`).
- `seed_demo` siembra Ranked 4-3 como victorias: tras `recompute` la base
  demo queda toda incompleta. El e2e no corre `recompute`; ficha aparte si se
  quiere coherencia.
- Fuera: la lista de partidas dudosas en Datos (resto de G7).

### Como probarlo en 2 minutos

```bash
cd backend
python manage.py test tests.test_match_point tests.test_recompute tests.test_ingest tests.test_api
```

### Verificar en el PC

```powershell
cd backend
..\.venv\Scripts\python.exe manage.py recompute --dry-run   # "... y N partidas (resultado)"
..\.venv\Scripts\python.exe manage.py recompute
```

Despues, en Partidas, esas N salen como incompletas y el winrate del
Dashboard deja de contarlas.

### Para el humano

Nada que decidir. Si tus ranked terminan seguido por rendicion antes de 4,
avisa y se busca otra señal.

### Candidatos descubiertos

Ninguno.

## Que gana quien usa la app

Si falta el `.rec` de la ultima ronda, hoy una ranked que iba 3-2 entra como
victoria (o derrota) por 1 y mueve tu winrate de partidas. Con el arreglo esa
partida queda "incompleta": sigue en el listado, pero no suma ni resta en los
winrates de partida.

## Criterios de aceptacion

- [x] Ranked 3-2 y 4-3 -> `won = None`, `incompleta`; 4-2, 2-4, 5-4 siguen
      `True`/`False`. Vive en `reglas_partida.resultado` (sin Django).
- [x] Tipo sin regla: gana el que tiene mas rondas, empate `None`.
- [x] `manage.py recompute` corrige lo importado sin migracion; `--dry-run`
      cuenta, segunda corrida no cambia nada.
- [x] Ranked 3-2 + Ranked 4-1 ganada -> winrate 100 % sobre 1;
      `/api/matches/` muestra la 3-2 incompleta.
- [x] `docs/metricas.md`, fila **Partidas ganadas**, dice cuando queda
      incompleta.

## Fuera de alcance

Lista de partidas dudosas en Datos (resto de G7); reglas para otros tipos
sin fuente; rendiciones antes de tiempo (limite en `metricas.md`); winrate de
rondas.

## Diseno

Arquitecto 20261029T0404Z: cerrada si `cierra(max - 1, min, regla)`;
`resultado()` en `reglas_partida.py`, usado por `ingest.py` y por
`_recompute_resultados` en `recompute.py`. Sin migracion. Detalle en `git log`.

## Implementacion

Dev 20261030T1604Z, sobre `origin/dev@0fedc7b`, segun el diseno. Tests:
`ReglasTests` (6), `ResultadoAlImportarTests` (2), `ResultadoDePartidaTests`
(4 + 1 del Revisor), `test_la_ranked_incompleta_sale_del_winrate_de_partidas`.

## Revision 2026-10-30 sobre f0b3782

Revisor 20261030T1653Z: aprobar, sin bloqueantes. Agrego
`test_recompute_no_toca_una_ranked_anterior_a_y9s4`. Menor fuera de alcance:
`seed_demo` siembra Ranked 4-3 como victorias (ficha aparte si se quiere).

## QA 2026-10-30 sobre 2512e59

QA 20261030T2004Z: `check.sh` verde (852 backend, 133 vitest, build, 53
e2e); base sembrada con 12 partidas borde, `recompute` cambia exactamente 2
(Ranked Y9S4 3-2 y 4-3), idempotente; `/api/overview/` y `/api/matches/`
cuadran a mano con y sin `?match_type=Ranked`; bordes 200 con JSON; base
vacia sin division por cero; 3 mutaciones caen en los tests nuevos.
Veredicto: `aprobado`. Detalle completo en el commit `44baf66`.

## Verificar en el PC

Toca `recompute`. Desde `backend/`:

```powershell
..\.venv\Scripts\python.exe manage.py recompute --dry-run
..\.venv\Scripts\python.exe manage.py recompute
```

El dry-run dice `y N partidas (resultado)`: deberian ser pocas. Despues, en
Partidas, salen como incompletas y el winrate del Dashboard deja de contarlas.

## Pendiente

## Para el humano

Sin decision pendiente (la tomaste el 2026-10-28). Aviso: una ranked que
termino por rendicion del rival (sin llegar a 4) tambien queda incompleta;
si eso pasa seguido en tus replays, avisa y se busca otra señal.
