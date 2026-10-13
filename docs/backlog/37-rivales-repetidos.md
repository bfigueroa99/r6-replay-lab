# 37. Rivales repetidos con tu record contra cada uno

estado: entregado
candado: -
rama: claude/equipo-dev/37-rivales-repetidos
tipo: funcionalidad
epica: rivales
area: fullstack
prioridad: 3
fuente: ALCANCE.md D1; `nemesis` (`backend/replays/analytics/aggregates.py:640`) cuenta duelos pero no partidas ganadas o perdidas contra cada rival
archivos: backend/replays/analytics/aggregates.py, backend/replays/views.py, frontend/src/pages/Duelos.jsx, docs/metricas.md, backend/tests/, frontend/e2e/
turnos: po 20261013T0511Z, arquitecto 20261013T0611Z, dev 20261013T1111Z, revisor 20261013T1213Z, dev 20261013T1511Z, revisor 20261013T1612Z, qa 20261013T1712Z, release 20261013T1811Z

## PR

Titulo: `[equipo-dev][fullstack] Rivales repetidos con tu record contra cada uno`

### Que cambia

La pagina Duelos suma la tabla "Rivales repetidos": las personas que te
tocaron en el equipo contrario en 2 o más partidas, con cuantas les ganaste,
cuantas perdiste y el winrate, y un enlace a su perfil. `GET /api/duels/`
trae la clave nueva `rivals` y acepta `?min_matches=` (1 a 1000, default 2).

### Por que esto y no otra cosa

Ficha 37, idea D1 de `ALCANCE.md` (epica rivales). `nemesis` ya contaba
duelos por rival pero no partidas ganadas o perdidas contra cada uno. Se
agrupa por `Player` (profileID) y no por nick, como el perfil; los datos de
Ubisoft o de trackers quedan afuera a proposito: esto no es scouting.

### Como se probo

- `./scripts/check.sh` en el Release, sobre la rama con `origin/main`
  fusionado: `Todo en verde.` (ruff ok, 493 tests backend con 4 skip, 65
  frontend, build, 26 e2e).
- Tests nuevos (`backend/tests/test_duels.py`, `RivalesRepetidosTests`):
  record ganadas/perdidas, minimo por defecto, compañero en una partida y
  rival en otra, partida sin resultado fuera del winrate, cambio de nick sin
  partir la fila, `min_matches` fuera de rango o texto sin 500, filtro de
  mapa, base vacia y endpoint con enlace al jugador.
- e2e (`frontend/e2e/humo.spec.js`): `Duelos muestra rivales repetidos con
  enlace al perfil` y `el CSV de rivales repetidos trae el récord de cada
  rival`.
- QA manual con base armada a mano y `runserver`: los 6 criterios por
  `curl`, mutaciones sobre `repeated_rivals` que tumban el test que
  corresponde, bundle inicial sin cambio (Duelos lazy +0,9 KB).

### Riesgos y lo que no entra

Sin migracion, sin `recompute`, sin parser. La consulta usa `Exists` +
`Subquery` por fila de `RoundPlayer` en tus rondas, el mismo orden de costo
que el perfil de jugador. Fuera: operadores o mapas por rival (ya estan en el
perfil) y avisos del coach sobre rivales.

### Como probarlo en 2 minutos

```powershell
cd backend; python manage.py seed_demo; python manage.py runserver
```

Abrir `http://127.0.0.1:8000/duelos`: debajo de "Por rival" aparece
"Rivales repetidos" con 3 filas (record 29-0, porque el seed gana todo).
Clic en un nick abre `/jugadores/<id>`. El boton CSV baja la tabla con la
columna "Récord". `http://127.0.0.1:8000/api/duels/?min_matches=abc` -> 200.

### Para el humano

Nada que decidir. Aviso: en `seed_demo` todas las partidas son ganadas, asi
que la demo muestra records 29-0; cambiar el seed movera numeros del e2e.

### Candidatos descubiertos

Ninguno.

## Que gana quien usa la app

En Duelos ve la lista de rivales que le tocaron en 2 o mas partidas, con
cuantas les gano y cuantas perdio, y entra al perfil de cada uno con un clic.

## Criterios de aceptacion

- [x] `GET /api/duels/` trae `rivals` por profileID con `matches`, `wins`,
      `losses`, `winrate`; minimo `min_matches` (default 2).
- [x] Compañero en una partida y rival en otra cuenta solo la de rival.
- [x] Partidas sin resultado cuentan en `matches`, no en el winrate.
- [x] Filtros comunes aplican; `?min_matches=` 1 a 1000 sin 500.
- [x] Tabla "Rivales repetidos" en Duelos con enlace a `/jugadores/<id>` y e2e.
- [x] Filas en `docs/metricas.md`.

## Diseno

(Arquitecto 20261013T0611Z) `repeated_rivals(min_matches, **filters)` en
`aggregates.py` debajo de `nemesis`: rival = fila de `RoundPlayer` con
`team_index` distinto del mio en alguna de mis rondas filtradas, agrupada
por `player_id`; `won` y nick en dos consultas planas; orden
`(-matches, -losses, username)`. Detalle completo en `git log`.

## Implementacion

(Dev 20261013T1111Z, correccion 20261013T1511Z) Backend, vista, panel en
`Duelos.jsx`, 9 tests backend, 2 e2e, filas de metricas. La correccion le
dio `csv:` a la columna "Récord" (salia vacia en el CSV).

## Revision

(Revisor 20261013T1213Z) Corregir: "Récord" vacio en el CSV. (Revisor
20261013T1612Z) Corregido en c71b7c6 con e2e que lo afirma; aprobar.

## QA

(QA 20261013T1712Z) Aprobado: 6 criterios verificados con base propia y
`curl`, base vacia, mutaciones, bundle. No hace falta "Verificar en el PC".

## Pendiente

## Para el humano

- Aviso: en `seed_demo` todas las partidas son ganadas (records 29-0).
