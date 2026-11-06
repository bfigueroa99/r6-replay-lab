# 92. El stack rival en el detalle de la partida

estado: entregado
candado: -
rama: claude/equipo-dev/92-stack-rival-en-la-partida
tipo: funcionalidad
epica: rivales
area: fullstack
prioridad: 3
fuente: D9 de ALCANCE.md (idea del arquitecto 20261105T1920Z-cAaALb8 al disenar la 90); tramo siguiente de la ficha 90
archivos: backend/replays/analytics/aggregates.py, backend/replays/views.py, frontend/src/stacksRivales.js, frontend/src/stacksRivales.test.js, frontend/src/pages/MatchDetail.jsx, backend/tests/test_stacks_rivales.py, frontend/e2e/stacks-rivales.spec.js, docs/metricas.md
turnos: po 20261105T1945Z-cvqUYh1, arquitecto 20261106T0015Z-cR6uHk3, dev 20261106T0041Z-cqfAePA, revisor 20261106T0109Z-cSomhFc, qa 20261106T0135Z-cpWzYqk, release 20261106T0135Z-cpWzYqk

## PR

Titulo: `[equipo-dev][frontend] El stack rival en el detalle de la partida`

### Que cambia

Al abrir una partida, arriba de las rondas aparece una linea por cada grupo
del equipo rival que ya te toco junto en otras partidas ("Kaid_, Mozzie99 y
Thorn.exe ya te tocaron juntos en 29 partidas, récord 29-0 · Ver en Duelos"),
con los nicks enlazados a su perfil. Sin grupos repetidos no se muestra nada.

### Por que esto y no otra cosa

Ficha 92, segundo tramo de la epica de rivales despues de la tabla de stacks
de Duelos (ficha 90). Reusa el mismo calculo para que los numeros coincidan
con Duelos; descartado recalcular con los filtros globales (el aviso habla de
todo tu historial) y mostrar subgrupos ya contenidos en uno mas grande.

### Como se probo

- `check.sh` (con `verificar.sh`): VERDE 6147c5003 (QA), 1005 tests backend, 216 vitest, 68 e2e; de nuevo sobre el commit final de la rama.
- Tests nuevos: `test_el_detalle_trae_el_stack_con_el_mismo_record_que_duelos`, `test_el_detalle_muestra_solo_el_grupo_mas_grande_que_aplica`, `test_una_partida_sin_stack_trae_lista_vacia`, `test_el_detalle_no_aplica_los_filtros`, `test_una_partida_sin_rondas_trae_lista_vacia`; 6 vitest en `stacksRivales.test.js`; e2e `el detalle de la partida avisa del stack rival repetido`.
- QA: base sintetica con nick repetido, grupo anidado, partida sin resultado y sin rondas; `curl` contra `/api/duels/` (mismos records); Chromium con consola limpia; 5 mutaciones, todas detectadas.
- OMC: diseno plan=— · implementacion revisión=4 hallazgos (3 arreglados) · revision revisión=3 hallazgos (0 arreglados; 2 LOW, 1 MEDIUM) · QA verificación=PASS.

### Riesgos y lo que no entra

Sin migracion ni `recompute`. Costo: cada apertura del detalle recorre los
stacks de todo el historial, como Duelos; con 1000 partidas, 0.24 s contra
0.017 s antes. Afuera: columna "Última vez" (D10), stacks de compañeros (C1).

### Como probarlo en 2 minutos

```powershell
cd backend; python manage.py seed_demo; python manage.py runserver
```

Abrir `http://127.0.0.1:8000/partidas`, entrar a cualquier partida: arriba de
Rondas, "Kaid_, Mozzie99 y Thorn.exe ya te tocaron juntos en 29 partidas,
récord 29-0 · Ver en Duelos". Clic en un nick abre su perfil; Duelos dice lo mismo.

### Para el humano

Nada.

### Candidatos descubiertos

Ninguno.

## Que gana quien usa la app

Al abrir una partida ves si en el equipo rival venia un grupo que ya te toco
junto, con su record y enlace a Duelos, sin ir a buscarlo a otra pagina.

## Criterios de aceptacion

- [x] `GET /api/matches/<id>/` trae `rival_stacks` (sin filtros, lista vacia si no hay, nunca ausente).
- [x] El record de cada grupo es el mismo numero que la fila de Duelos.
- [x] Si un grupo esta contenido en otro mas grande que aplica a la partida, sale solo el mas grande.
- [x] Aviso sobre el scoreboard con nicks enlazados y enlace a Duelos; sin grupos, nada.
- [x] Partida sin rondas o sin rivales identificados: `rival_stacks: []` y el detalle no se rompe.
- [x] e2e sobre `seed_demo` (29 partidas, récord 29-0).

## Diseno

(arquitecto 20261106T0015Z-cR6uHk3.) `rival_stacks` partida en `_stacks_rivales` y `_filas_de_stacks`;
`rival_stacks_de_partida(match_id)` sin filtros, maximalidad por conjunto de jugadores dentro de la
partida; clave en `match_detail`; `StacksRivales` entre las kpis y Rondas. Detalle en `git log`.
OMC: plan=— (ficha chica, una forma obvia) · revisión=— · verificación=—

## Implementacion

(dev 20261106T0041Z-cqfAePA.) Diseno completo, mas `separadorAntes` para los enlaces y
`rival_stacks: []` en `frontend/e2e/partida-sin-rondas.json` (lo exige `test_partida_sin_rondas`).
OMC: plan=— · revisión=4 hallazgos (3 arreglados) · verificación=—

## Revision 2026-11-06 sobre bd23b14

(revisor 20261106T0109Z-cSomhFc.) Aprobar. Sin CRITICAL ni HIGH; 2 LOW de tests y 1 MEDIUM de
costo sin confirmar (medido en QA: 0.24 s con 1000 partidas). Ninguno bloquea.
OMC: plan=— · revisión=3 hallazgos (0 arreglados; 2 LOW, 1 MEDIUM sin confirmar) · verificación=—

## QA 2026-11-06 sobre 6147c5003

(qa 20261106T0135Z-cpWzYqk.) Seis criterios con evidencia: `curl` sobre base sintetica (grupo
anidado, `won=None`, nick repetido con otro `profile_id`, partida sin rondas, bordes 404/200),
Chromium sin errores de consola, 5 mutaciones detectadas, chunk inicial igual que dev (191.85 kB).
Comandos y salidas en el commit `Prueba: 92 stack rival en la partida` (d93aaeb).
OMC: plan=— · revisión=— · verificación=PASS

## Pendiente

## Para el humano
