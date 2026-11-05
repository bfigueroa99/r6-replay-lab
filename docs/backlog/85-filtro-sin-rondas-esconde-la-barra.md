# 85. Un filtro sin rondas esconde la barra en Coach, Operadores, Compañeros, Duelos y Tendencias

estado: entregado
candado: -
rama: claude/equipo-dev/85-filtro-sin-rondas-esconde-la-barra
tipo: bug
epica: -
area: frontend
prioridad: 3
fuente: idea anotada en ESTADO.md por la sesion de la 77 ("Coach, Operadores, Compañeros, Duelos y Tendencias con 0 rondas filtradas muestran 'Todavía no hay replays importados' y esconden la barra de filtros"); el Inicio ya se arreglo en la 77
archivos: frontend/src/tipoPartida.js, frontend/src/tipoPartida.test.js, frontend/src/components/ui.jsx, frontend/src/pages/Coach.jsx, frontend/src/pages/Operators.jsx, frontend/src/pages/Teammates.jsx, frontend/src/pages/Duelos.jsx, frontend/src/pages/Trends.jsx, frontend/e2e/humo.spec.js
turnos: dev 20261105T1303Z-c1PA8YY, revisor 20261105T1330Z-cTQKqvr, qa 20261105T1358Z-cxcyM5F, release 20261105T1358Z-cxcyM5F

## PR

Titulo: `[equipo-dev][frontend] Un filtro sin rondas ya no esconde la barra en cinco paginas`

### Que cambia

Con un filtro que deja 0 rondas, Coach, Operadores, Compañeros, Duelos y
Tendencias decian "Todavía no hay replays importados", ofrecian importar y
escondian la barra de filtros: no habia como apretar Limpiar sin volver al
Inicio. Ahora muestran su titulo, la barra y "0 rondas con estos filtros",
como el Inicio desde la 77. Con la base vacia de verdad y sin filtros sigue
el EmptyState de siempre.

### Por que esto y no otra cosa

Ficha 85, bug anotado por la sesion de la 77. Se reusa el criterio del
Inicio (`hayFiltros`) en una funcion pura, `vistaSinRondas`, que tambien
cubre el instante de carga despues de Limpiar (si no, la barra se
desmontaba). Descartado: importar `Filters` en `ui.jsx` (cada pagina arma
su barra con props distintas y se la pasa a `SinRondasFiltradas`).

### Como se probo

- `check.sh` (con `verificar.sh`): VERDE bd0ed8118, 953 tests backend, 190 vitest, 60 e2e.
- Tests nuevos: 4 vitest `vistaSinRondas (ficha 85)` (con rondas, filtrado,
  base vacia, cargando tras limpiar); e2e `un filtro sin rondas deja la barra
  en todas las páginas` (falla sin el arreglo en `humo.spec.js:846`).
- Manual (QA): app real con `seed_demo`, rango 2000-01-01 a 2000-01-02 por la
  UI, las cinco paginas con barra y nota, Limpiar vuelve a los numeros;
  base vacia, EmptyState en las cinco; consola limpia. 3 mutaciones, las 3
  caen. Chunk inicial +0,3 %.
- OMC: plan=— · revisión=3 hallazgos (0 arreglados, todos LOW) · verificación=—
- OMC: plan=— · revisión=3 hallazgos (0 arreglados; 1 MEDIUM, 2 LOW) · verificación=—
- OMC: plan=— · revisión=— · verificación=PASS (omc-verifier: 4 criterios VERIFIED, 0 bloqueantes)

### Riesgos y lo que no entra

Sin migraciones, sin backend. Duelos decide por duelos y no por rondas: un
filtro con rondas pero sin duelos dice "0 rondas con estos filtros" (antes
decia "Todavía no hay replays importados"); queda en la ficha 86
(`propuesto`). Partidas, Datos, Jugador y el detalle no usan este EmptyState.

### Como probarlo en 2 minutos

1. `cd backend; python manage.py seed_demo; python manage.py runserver`
2. En el Resumen, Periodo = "Entre dos fechas", 2000-01-01 a 2000-01-02.
3. Menu -> Coach, Operadores, Compañeros, Duelos, Tendencias: cada una con su
   titulo, la barra y "0 rondas con estos filtros".
4. Limpiar en cualquiera: vuelven los numeros.

### Para el humano

Nada.

### Candidatos descubiertos

Ficha 86 (bug, `propuesto`): Duelos dice "0 rondas" con un filtro que tiene
rondas pero no duelos.

## Revision 2026-11-05 sobre 6658a30

Revisor 20261105T1330Z-cTQKqvr: aprobar -> `revisado`. Criterios cumplidos.
Hallazgos sin arreglo obligatorio: [bug] MEDIUM `Duelos.jsx:43` decide por
`totals.duels` (ficha 86); [estilo] LOW la nota dice "usa Limpiar" durante
la carga posterior a Limpiar; [bug] LOW un filtro `session` puesto en
Tendencias no se ve en la barra de las otras paginas (ya pasaba).

## QA 2026-11-05 sobre bd0ed81

QA 20261105T1358Z-cxcyM5F: `aprobado`. Los 4 criterios con evidencia en la
app real (`seed_demo`, rango por la UI, base vacia), 3 mutaciones que caen,
chunk +0,3 %, omc-verifier PASS. Hallazgo MEDIUM del revisor reproducido con
`factories.py` (Bank con 1 ronda y 0 duelos): ficha 86. Detalle en `git log`
de la rama (commit `Prueba: 85`).

## Para el humano
