# 37. Rivales repetidos con tu record contra cada uno

estado: propuesto
candado: -
rama: -
tipo: funcionalidad
epica: rivales
area: fullstack
prioridad: 3
fuente: ALCANCE.md D1; `nemesis` (`backend/replays/analytics/aggregates.py:640`) cuenta duelos pero no partidas ganadas o perdidas contra cada rival
archivos: backend/replays/analytics/aggregates.py, backend/replays/views.py, frontend/src/pages/Duelos.jsx, docs/metricas.md, backend/tests/, frontend/e2e/
turnos: po 20261013T0511Z

## PR

(La escribe el Release manager al final: titulo `[equipo-dev][area] Titulo`,
cuerpo segun `.claude/skills/equipo-dev/plantilla-pr.md` y una seccion
"Como probarlo en 2 minutos" con comandos exactos.)

## Que gana quien usa la app

En Duelos ve la lista de rivales que le tocaron en 2 o mas partidas, con
cuantas les gano y cuantas perdio, y entra al perfil de cada uno con un
clic. Hoy solo sabe a quien mata o quien lo mata, no contra quien pierde
partidas.

## Criterios de aceptacion

- [ ] `GET /api/duels/` devuelve una clave nueva `rivals`: una fila por
      jugador que estuvo en el equipo contrario en al menos `min_matches`
      partidas (por defecto 2), con `player_id`, `username`, `matches`,
      `wins`, `losses` y `winrate` de partida. Se agrupa por jugador
      (`Player`, es decir `profileID`), no por nick: un rival que se cambio
      el nick sigue siendo una fila.
- [ ] Un jugador que en una partida fue compañero y en otra rival cuenta
      solo las partidas en que fue rival. Test con dos partidas armadas a
      mano que lo afirma.
- [ ] Las partidas sin resultado (`Match.won` nulo) cuentan en `matches` y
      no en `wins` ni `losses`; el `winrate` se calcula sobre las que tienen
      resultado.
- [ ] Los filtros comunes aplican y `?min_matches=` acepta 1 a 1000; un
      valor fuera de rango o no numerico no da 500 (mismo helper que
      `min_duels`).
- [ ] La pagina Duelos muestra la tabla "Rivales repetidos" con enlace a
      `/jugadores/<id>` (la ruta del perfil que ya existe, `App.jsx:140`), y el e2e la
      renderiza sin errores de consola. Con `seed_demo` la tabla no queda
      vacia o, si queda, muestra un texto de vacio en vez de nada.
- [ ] `docs/metricas.md` tiene la fila de "record contra un rival".

## Fuera de alcance

- Cualquier dato de rivales que no salga de tus replays (Ubisoft, trackers):
  esto no es scouting.
- Operadores o mapas por rival: ya estan en el perfil del jugador.
- Avisos del coach sobre rivales.

## Diseno

(Arquitecto) Nota del PO: `player_profile` ya calcula "contra" con
`Exists` sobre `team_index` (`aggregates.py:1093`); reusar esa forma para no
tener dos definiciones de "rival". Revisar como se llama la ruta del perfil
en `App.jsx` antes de escribir el enlace.

## Implementacion

(Dev) Que quedo, que no, desvios del diseno y por que.

## Revision <fecha> sobre <sha>

(Revisor) Formato de `revision.md`. Veredicto al final.

## QA <fecha> sobre <sha>

(QA) Un comando y un resultado por criterio de aceptacion.

## Verificar en el PC

(QA, solo si toca migraciones, recompute, parser, Electron o `.ps1`.)

## Pendiente

## Para el humano
