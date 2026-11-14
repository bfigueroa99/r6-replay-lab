# 132. Rivales que se repiten en la misma noche

estado: entregado
candado: -
rama: claude/equipo-dev/132-rivales-que-se-repiten-en-la-misma-noche
tipo: funcionalidad
epica: rivales
area: fullstack
prioridad: 3
fuente: ALCANCE.md D13
archivos: backend/replays/analytics/aggregates.py, backend/tests/test_duels.py, frontend/src/pages/Duelos.jsx, frontend/e2e/humo.spec.js, docs/metricas.md
turnos: po 20261113T1926Z-ce4Pmp6, arquitecto 20261113T2318Z-chc2kiA, dev 20261114T0012Z-crDhgd7, revisor 20261114T0012Z-ccgaH14, qa 20261114T0040Z-c3LsMAo, release 20261114T0040Z-c3LsMAo

## PR

Titulo: `[equipo-dev][fullstack] Revanchas de la misma noche en Rivales repetidos`

### Que cambia

En Duelos, la tabla *Rivales repetidos* suma la columna **Revanchas esa
noche**: cuantas veces te volvio a tocar ese rival en una sesion en la que ya
lo habias enfrentado, con el record de esas revanchas (`3 (2-1)`, `—` sin
revanchas). Separa al lobby que vuelve a la cola contigo esa noche del rival
que reencuentras por casualidad semanas despues.

### Por que esto y no otra cosa

Ficha 132 (ALCANCE D13, epica rivales). Columna en la tabla existente y no
panel aparte; conteo y record sin winrate porque el `n` por rival es 0 a 3.

### Como se probo

- `check.sh` (con `verificar.sh`): VERDE 6ebf346, 1357 tests backend, 443 vitest, 119 e2e.
- Tests nuevos en `RivalesRepetidosTests` (`test_duels.py`): misma noche suma
  una revancha; noches distintas suman 0; record de las partidas despues de la
  primera; sin resultado fuera del record; filtro de mapa que parte la noche;
  la primera es la mas temprana aunque se importe despues; cada noche tiene su
  primera; a igual hora gana el menor id; el endpoint trae las tres claves.
- e2e: `Duelos muestra rivales repetidos con enlace al perfil` afirma la
  cabecera y la celda contra `/api/duels/`.
- QA manual: base sembrada desde `factories.py`, `curl` con filtros borde
  (mapa, sesion, `until=foo`, base vacia) y dos valores recalculados a mano;
  Playwright: teclado, `aria-sort`, contraste 14.17:1 y 5.71:1, CSV, consola
  limpia; 4 mutaciones en `_revanchas`, todas muertas.
- OMC: plan=— · revisión=— · verificación=— (diseno)
- OMC: plan=— · revisión=3 LOW (2 arreglados) · verificación=— (implementacion)
- OMC: plan=— · revisión=1 LOW (0 arreglados, confirmado) · verificación=— (revision)
- OMC: plan=— · revisión=— · verificación=PASS (QA)
- Skills del repo: statistical-analysis, testing-strategy (diseno); test-driven-development, statistical-analysis, ux-copy (implementacion); ninguna (revision); accessibility-review, validate-data (QA).

### Riesgos y lo que no entra

Sin migracion ni `recompute`: se calcula al consultar sobre `Match.played_at`
y `Match.won`, con una sola pasada de `_sessions_raw()` por request. Fuera:
stacks rivales en la misma noche y señales del Coach.

### Como probarlo en 2 minutos

```
cd backend; python manage.py seed_demo; python manage.py runserver
```
Abrir `/duelos`, panel *Rivales repetidos*: columna "Revanchas esa noche" con
su ayuda; con `seed_demo` todas valen `—` (separa sus partidas 3 h). Con
datos reales, un rival que te toco dos veces seguidas una noche muestra
`1 (1-0)` o `1 (0-1)`.

### Para el humano

Nada.

### Candidatos descubiertos

Ninguno.

## Que gana quien usa la app

La tabla de Rivales repetidos marca a los rivales que te tocaron dos o mas
veces dentro de una misma sesion y tu record en esas revanchas.

## Criterios de aceptacion

- [x] `repeated_rivals` suma `same_session` y su record; `won` nulo fuera.
- [x] La primera partida de la sesion no es revancha.
- [x] Los filtros globales aplican (sesion sobre todas las partidas, revanchas sobre las filtradas).
- [x] Columna "Revanchas esa noche" en Duelos con ayuda; e2e contra la API.
- [x] Fila en `docs/metricas.md`.

## Diseno, Implementacion

Detalle en `git log` de la rama. `_session_index_map()` y `_revanchas()` en
`aggregates.py`; `_record` sin tocar (lo comparten los stacks).

## Revision 2026-11-14 sobre 24720ce

Aprobar. 1 LOW: el e2e solo ve la rama `—` (seed_demo); la rama `N (G-P)`
la cubren los tests Django y la QA la vio en el navegador.

## QA 2026-11-14 sobre 6ebf346

Aprobado. Evidencia completa en el commit `Prueba: 132` de la rama.
Menor, no frena: `Récord` usa guion largo (`3–2`) y la columna nueva corto (`2-1`).

## Para el humano

(nada)
