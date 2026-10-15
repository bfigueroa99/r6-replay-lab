# 45. Remontadas y derrumbes

estado: entregado
candado: -
rama: claude/equipo-dev/45-remontadas-y-derrumbes
tipo: funcionalidad
epica: lado-y-marcador
area: fullstack
prioridad: 3
fuente: ALCANCE.md B7 (idea del PO); cierra la epica lado-y-marcador despues de las fichas 36, 41 y 43
archivos: backend/replays/analytics/aggregates.py, backend/replays/views.py, backend/tests/test_remontadas.py, frontend/src/remontadas.js, frontend/src/remontadas.test.js, frontend/src/pages/Trends.jsx, frontend/e2e/humo.spec.js, docs/metricas.md
turnos: po 20261014T1911Z, arquitecto 20261014T2311Z, dev 20261015T0011Z, revisor 20261015T0110Z, dev 20261015T0211Z, revisor 20261015T0310Z, qa 20261015T0411Z, release 20261015T0511Z

## PR

Titulo: `[equipo-dev][fullstack] Remontadas y derrumbes en Tendencias`

### Que cambia

Tendencias suma el panel "Remontadas y derrumbes": las partidas que ganaste
yendo 2 o mas rondas abajo y las que perdiste yendo 2 o mas arriba, cada una
con enlace a su detalle, y tu winrate de partida segun la diferencia de
rondas al cambio de lado (`+2 o más` a `-2 o menos`). `/api/trends/` trae la
clave nueva `comebacks`. Cierra la epica lado-y-marcador.

### Por que esto y no otra cosa

Ficha 45 (ALCANCE.md B7), ultimo tramo de lado-y-marcador despues de 36, 41
y 43. Usa solo `Round.score_before`, `my_side`, `number` y `Match.won`, ya
importados: sin migracion ni recompute. Umbral fijo en 2 (configurable desde
la UI quedo fuera de alcance).

### Como se probo

- `./scripts/check.sh` -> `Todo en verde.`: ruff ok, 585 tests backend, 86
  vitest, build ok, 33 e2e (sobre la rama con `origin/main@f74a16f`).
- `backend/tests/test_remontadas.py` (24 tests): remontada 1-3, derrumbe 3-1,
  marcador antes de la ultima ronda, corte Y9S4, tres equipos, `team_index`
  1, `won` nulo, tramos (+3 en +2, -4 en -2), sin segunda mitad, ronda
  faltante, faltan las primeras rondas, filtro de mapa, base vacia, filtros
  raros. `frontend/src/remontadas.test.js` (6). e2e `Tendencias muestra
  remontadas y derrumbes`.
- QA: base vacia y sembrada con `factories.py` (31 partidas, 4 trampa),
  `curl` con filtros borde (todos 200), UI en Chromium sin errores de consola,
  chunk inicial sin cambio (186.80 kB), 5 mutaciones detectadas.

### Riesgos y lo que no entra

Sin migracion, sin recompute, sin parser. Una query por request (~10.000
filas en Python con 1000 partidas). Partidas con rondas faltantes (al
principio o en el medio) quedan fuera para no dar numeros falsos. Fuera:
grafico ronda a ronda (F4), umbral configurable, modelo de probabilidad.

### Como probarlo en 2 minutos

```
cd backend; python manage.py seed_demo; python manage.py runserver
curl -s localhost:8000/api/trends/ | python -m json.tool | findstr /C:"remontadas_total" /C:"matches_known"
```

Abrir `http://localhost:8000/tendencias`: panel "Remontadas y derrumbes" con
"Ninguna remontada de 2 o más rondas todavía." y la tabla con `+1` en 29
partidas, 100 %. Con la base real: abrir una remontada y confirmar en el
detalle que el marcador estuvo 2 abajo.

### Para el humano

Nada que decidir. Aviso: el texto de vacio (Trends.jsx, `matches_known === 0`)
nombra solo Y9S4, aunque tambien quedan afuera partidas con rondas faltantes;
cambio de una linea para un turno futuro.

### Candidatos descubiertos

Ninguno.

## Que gana quien usa la app

En Tendencias aparece un panel que lista las partidas que ganaste yendo
abajo por 2 o mas rondas (remontadas) y las que perdiste yendo arriba por 2
o mas (derrumbes), cada una con enlace a su detalle. Debajo, tu winrate de
partida segun la diferencia de rondas que llevabas al cambio de lado: si
sueltas las partidas que tienes ganadas o si das vuelta las perdidas.

## Criterios de aceptacion

- [x] `/api/trends/` devuelve una clave nueva (p. ej. `comebacks`) con dos
      listas, `remontadas` y `derrumbes`, cada item con `match_id`, mapa,
      fecha, marcador final y la maxima desventaja (o ventaja) en rondas
      que hubo antes de la ultima ronda. Una partida ganada que estuvo 1-3
      entra en `remontadas` con desventaja 2; una ganada que nunca estuvo
      abajo por 2 no entra.
- [x] Una partida perdida que estuvo 3-1 a favor entra en `derrumbes`; una
      perdida que nunca estuvo arriba por 2 no entra.
- [x] Solo cuentan partidas con marcador conocido: mismo corte que
      `by_score_state` (`code_version >= Y9S4`, marcador de dos equipos,
      `_marcador_conocido` en `aggregates.py`). Una partida anterior a Y9S4
      no aparece en ninguna lista ni en la tabla de diferencia. Test con
      una partida de cada lado del corte.
- [x] Tabla de winrate de partida por diferencia de rondas al cambio de
      lado (primera ronda de la segunda mitad, la misma frontera que usa
      `by_half`): tramos `+2 o mas`, `+1`, `0`, `-1`, `-2 o menos`, con
      partidas y winrate por tramo. Respeta los filtros de la barra (mapa,
      fechas, sesion) como el resto de `/api/trends/`.
- [x] Tendencias muestra el panel "Remontadas y derrumbes" con las dos
      listas (enlace al detalle de cada partida) y la tabla; con base vacia
      o sin partidas con marcador conocido muestra un texto de vacio, no un
      error. El e2e (`frontend/e2e/`) lo afirma sobre `seed_demo`.
- [x] Fila en `docs/metricas.md` para la desventaja maxima y el winrate por
      diferencia al cambio de lado.

## Fuera de alcance

- Grafico del marcador ronda a ronda de cada partida (eso es F4, tira de
  rondas en el listado de Partidas).
- Umbral configurable desde la UI: el 2 queda fijo en el diseno.
- Probabilidad de ganar segun el marcador (modelo estadistico): solo
  conteos.

## Diseno

Arquitecto 20261014T2311Z: `aggregates.comebacks()` debajo de
`by_match_point`, corte de version de `_marcador_conocido`, umbral 2, tope 20
por lista, tramos al cambio de lado con la frontera de `by_half`. Detalle
completo en `git log` de esta rama.

## Implementacion

Dev 20261015T0011Z y 20261015T0211Z: todo el diseno. Desvios: una ronda
faltante (en el medio o al principio: primera ronda presente distinta de
0-0) saca la partida; test del marcador final reemplazado por
`test_el_marcador_antes_de_la_ultima_ronda_cuenta`; subtitulo "Por
diferencia al cambio de lado" para no chocar con el e2e de match point.

## Revision

Revisor 20261015T0110Z: corregir (faltan las primeras rondas), corregido en
822da4f. Revisor 20261015T0310Z sobre 822da4f: aprobar; queda un hallazgo
menor de texto de vacio (ver Para el humano).

## QA

QA 20261015T0411Z sobre d98db16: aprobado. Los seis criterios con evidencia;
script de siembra y comandos en `git log` de esta rama (commit 2613d9e).

## Para el humano

- Texto de vacio del panel (Trends.jsx, `matches_known === 0`) menciona solo
  Y9S4; tambien saca partidas con rondas faltantes. Informativo, no bloquea.
