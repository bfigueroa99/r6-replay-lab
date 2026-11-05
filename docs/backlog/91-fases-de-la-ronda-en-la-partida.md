# 91. Fases de la ronda en el detalle de partida

estado: entregado
candado: -
rama: claude/equipo-dev/91-fases-de-la-ronda-en-la-partida
tipo: funcionalidad
epica: paridad-referencia
area: fullstack
prioridad: 3
fuente: R3 de ALCANCE.md; `replica/features.csv` "Analisis de ronda en fases early, mid y execute" (could, partial: los tramos existen entre partidas en Tendencias, no por partida); [aurelix](https://aurelix.app/blog/how-to-analyse-r6-siege-replays)
archivos: backend/replays/analytics/aggregates.py (fases_de_partida), backend/replays/views.py (match_detail), backend/tests/test_fases_de_la_ronda.py, frontend/e2e/partida-sin-rondas.json, frontend/src/fasesRonda.js, frontend/src/fasesRonda.test.js, frontend/src/pages/MatchDetail.jsx, frontend/e2e/humo.spec.js, docs/metricas.md
turnos: po 20261105T1759Z-cCJ5erc, arquitecto 20261105T1825Z-cVr9Dsg, dev 20261105T1851Z-cz3m6mE, revisor 20261105T1921Z-cP5bnKD, qa 20261105T1920Z-cSTWy1D (fallback del revisor), release 20261105T1920Z-cSTWy1D

## PR

Titulo: `[equipo-dev][frontend] Fases de la ronda en el detalle de partida`

### Que cambia

En el detalle de una partida, un panel "Fases de la ronda" con las bajas de
tu equipo y del rival en temprano (<30 s), medio (30-120 s) y tarde (120 s o
mas), y en cuantas rondas cada equipo domino esa fase y como terminaron: ver
si la partida se decidio en el primer contacto o en el cierre.
`GET /api/matches/<id>/` suma `phases`.

### Por que esto y no otra cosa

Ficha 91 (R3 de `ALCANCE.md`, paridad con analizadores de referencia). Hasta
ahora los tramos solo existian agregados en Tendencias y para tus bajas. Se
descarto alinear con el 90 s de la apertura tardia: ese corte habla de cuando
llega la primera baja, no de en que fase se pelea.

### Como se probo

- `check.sh` (con `verificar.sh`): VERDE (sha y conteos en el commit de entrega; QA: 72b58ef, 978 tests backend, 206 vitest, 65 e2e).
- Tests nuevos: `backend/tests/test_fases_de_la_ronda.py` (15: cortes 29.9/30/119.9/120, reparto, teamkills, autor sin fila, sin reloj, rondas dominadas, resultado desconocido fuera del denominador, equipo por ronda, partida sin bajas); `fasesRonda.test.js` (vitest); e2e "el detalle de una partida muestra las fases de la ronda" con numeros fijos de `seed_demo` (medio 4/2, tarde 1/3) y "una partida sin rondas" con el texto sin bajas.
- QA: runserver con base vacia, con `seed_demo` (las fases suman las bajas del detalle en 3 partidas) y con una base de bordes de `factories.py`; 4 mutantes muertos; chunk inicial sin crecer.
- OMC: Implementacion `revisión=2 hallazgos LOW (2 arreglados)`; Revision `revisión=4 hallazgos (1 MEDIUM cubierto con 3 tests; 1 MEDIUM y 2 LOW anotados)`; QA `verificación=PASS (omc-verifier, 5 de 5 criterios VERIFIED)`.

### Riesgos y lo que no entra

Sin migracion, `recompute` ni parser: se calcula sobre las rondas que
`match_detail` ya arma, cero queries nuevas. Toca `views.py` y
`MatchDetail.jsx` como la ficha 79 (esperando al humano): regiones
distintas, el que mergee segundo puede tener un conflicto de pocas lineas.
Fuera: la vista agregada (ya en Tendencias), fases por plant (el formato no
lo trae), timeline nueva.

### Como probarlo en 2 minutos

```powershell
cd backend; python manage.py test tests.test_fases_de_la_ronda
cd backend; python manage.py runserver
```

Abrir una partida en `/partidas/<id>`: el panel "Fases de la ronda" esta
debajo de "Trades por equipo"; Tu equipo + Rival de las tres filas, mas los
que avisa la nota, suman las bajas de las timelines de la partida.

### Para el humano

Nada. Dos LOW anotados en la revision (la nota no se ve cuando ninguna baja
entra a una fase; "(ganadas)" se puede leer como del rival).

### Candidatos descubiertos

Ninguno.

## Que gana quien usa la app

En el detalle de una partida, las bajas de cada equipo partidas en temprano,
medio y tarde de la ronda, y cuantas rondas gano cada equipo segun quien
saco mas bajas en cada fase: ver si esa partida se decidio en el primer
contacto o en el cierre. Hoy eso existe solo como agregado de tus bajas y
muertes en Tendencias, nunca para una partida y los dos equipos.

## Criterios de aceptacion

- [x] `GET /api/matches/<id>/` trae `phases`: tres filas (temprano < 30 s
      jugados, medio de 30 a 120 s, tarde 120 s o mas, sobre `Event.elapsed`
      de los `Kill`) con las bajas de tu equipo y del rival en cada una,
      teamkills afuera (no cuentan para ningun equipo). Test con una partida
      armada a mano: una baja a los 29.9 s cae en temprano, una a 30.0 s en
      medio, una a 120.0 s en tarde.
- [x] Cada fila trae tambien en cuantas rondas tu equipo saco mas bajas que el
      rival en esa fase y cuantas de esas rondas ganaste (`Round.my_team_won`;
      las rondas con resultado desconocido fuera del denominador). Test.
- [x] Una baja cuyo autor no tiene fila en la ronda (equipo desconocido) no
      suma a ningun equipo ni rompe la respuesta (test).
- [x] En `MatchDetail`, un panel "Fases de la ronda" con las tres filas;
      una partida sin bajas muestra el panel con ceros o un texto, nunca un
      error de consola. Caso en el e2e con un numero de `seed_demo`.
- [x] Fila en `docs/metricas.md` con los cortes (los mismos tramos que
      el Arquitecto alinee con "Cuando matas" y "Cuando mueres" si conviene;
      si cambia los cortes, lo dice el diseno).

## Fuera de alcance

- La misma vista agregada entre partidas: ya esta en Tendencias.
- Fases por plant o post-plant: el formato no trae el plant en temporadas
  nuevas.
- Una timeline grafica nueva: la ronda ya tiene su timeline.

## Diseno

(arquitecto 20261105T1825Z-cVr9Dsg; detalle completo en `git log` de la rama)

Funcion pura `fases_de_partida(rondas, my_team_index)` en `aggregates.py`
sobre las rondas ya armadas de `match_detail` (como Trades por equipo), panel
en `MatchDetail` con la logica en `fasesRonda.js`. Cortes `0 < elapsed < 30`,
`30 <= elapsed < 120`, `>= 120`; `elapsed` 0 es "sin reloj" y va a
`untimed_kills`. El equipo se lee ronda a ronda desde tu fila.

## Implementacion

(dev 20261105T1851Z-cz3m6mE) Diseno completo, sin desvios de fondo; tests
extra para Death sin autor, empate en la fase y lista vacia.
OMC: plan=— · revisión=2 hallazgos LOW (2 arreglados) · verificación=—

## Revision 2026-11-05 sobre 9fb1c05

(revisor 20261105T1921Z-cP5bnKD) Veredicto: aprobar. MEDIUM de
`test_tu_equipo_se_lee_por_ronda` cubierto con 3 tests nuevos del Revisor;
MEDIUM del e2e sin numeros fijos de medio y tarde, atendido en QA; dos LOW
anotados (nota oculta sin bajas en fase, "(ganadas)" ambiguo).
OMC: plan=— · revisión=4 hallazgos (1 MEDIUM cubierto con 3 tests; 1 MEDIUM y 2 LOW anotados) · verificación=—

## QA 2026-11-05 sobre 72b58ef

(qa 20261105T1920Z-cSTWy1D) Aprobado. check.sh VERDE 72b58ef; runserver con base vacia
(404 en ids invalidos), `seed_demo` (fases = bajas del detalle en 3
partidas) y base de bordes de `factories.py` (29.9/30/120, sin reloj,
teamkill, autor sin fila, resultado desconocido); 4 mutantes muertos; chunk
inicial igual a dev; e2e con medio 4/2 y tarde 1/3 de `seed_demo`. Comandos
completos en `git log` (commit `Prueba: 91`).
OMC: plan=— · revisión=— · verificación=PASS (omc-verifier, 5 de 5 criterios VERIFIED)
