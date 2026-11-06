# 89. Salida del spawn por mapa

estado: entregado
candado: -
rama: claude/equipo-dev/89-salida-del-spawn-por-mapa
tipo: funcionalidad
epica: posicionamiento
area: fullstack
prioridad: 2
fuente: S2 de ALCANCE.md (idea del PR #22 que el humano cerro sin merge el 2026-11-05, rama `ccr-ec8265ab-4qn7k2`, commit c994090)
archivos: backend/replays/analytics/aggregates.py (spawn_exits, positioning), backend/tests/test_salida_del_spawn.py, frontend/src/posicion.js, frontend/src/posicion.test.js, frontend/src/pages/Coach.jsx, frontend/e2e/humo.spec.js, docs/metricas.md
turnos: po 20261105T1759Z-cCJ5erc, arquitecto 20261105T1825Z-cVr9Dsg, dev 20261105T1851Z-cBJfgUn, revisor 20261105T1920Z-cSTWy1D, qa 20261105T1945Z-cLLCG3x, release 20261105T1945Z-cLLCG3x

## PR

Titulo: `[equipo-dev][frontend] Salida del spawn por mapa en el Coach`

## Que cambia

El Coach suma el panel "Salida del spawn": por mapa (con su version) y spawn de ataque, en cuantas rondas moriste en los primeros 15 s de acción y cuantas bajas sacaste en esa ventana, comparado contra el resto de tu ataque con la misma banda de ruido que "Dónde quedas fuera de posición". Marca "Caes temprano" o "Sales bien" solo si la diferencia pasa el margen.

## Por que esto y no otra cosa

Ficha 89, idea S2 de `ALCANCE.md` (PR #22 cerrado por el humano). Va dentro de `/api/positioning/`: mismos filtros, misma muestra minima, cero requests nuevos. Sin migracion ni `recompute`: sale de `death_elapsed` y `Event.elapsed`, que ya se guardan. El enlace a peekabooR6 queda afuera (sitio de terceros nuevo).

## Como se probo

- `check.sh` (con `verificar.sh`): VERDE ff44ebd (rama fusionada con dev), 990 tests backend, 210 vitest, 66 e2e.
- Tests nuevos (`test_salida_del_spawn.py`, 12): borde 14.9 / 15.0 en muertes y bajas, sin reloj (`None` y 0.0), defensa y sin spawn afuera, muestra minima, solo rivales, cada baja en el spawn de su ronda, contra el resto del ataque, un solo spawn es ruido, etiqueta de version, filtros de mapa y de defensa. Vitest en `posicion.test.js`; e2e "el Coach muestra la salida del spawn".
- QA: API con base vacia y sembrada (parametros borde), panel en Chromium con chips con señal y los dos textos de vacio, chunk inicial sin cambios, 4 mutaciones detectadas.
- OMC: plan=— · revisión=— · verificación=—
- OMC: plan=— · revisión=3 hallazgos LOW (2 arreglados) · verificación=—
- OMC: plan=— · revisión=4 hallazgos (1 MEDIUM, 3 LOW; 1 arreglado con test) · verificación=—
- OMC: plan=— · revisión=— · verificación=PASS (5 de 5 criterios VERIFIED)

## Riesgos y lo que no entra

Sin migraciones, `recompute`, parser ni instalador. El e2e solo ve el panel neutro (`seed_demo` no tiene muertes antes de 35 s); los chips con señal los cubren backend, vitest y la QA manual. Fuera: enlace a peekabooR6, señal del Coach, defensa (el `.rec` no trae spawn de defensa).

## Como probarlo en 2 minutos

```powershell
cd backend; python manage.py test tests.test_salida_del_spawn   # 12 OK
python manage.py runserver   # abrir http://localhost:8000/coach
```

Bajo "Dónde quedas fuera de posición" aparece "Salida del spawn" con la nota del ataque entero y una fila por mapa y spawn. Lado = Solo defensa: "Todavía no hay rondas de ataque con spawn con estos filtros."

Verificar en el PC: calibrar el corte de 15 s con la base real (si la nota da ~0 % en todo, conviene 20 s).

## Para el humano

Nada que bloquee. Pregunta para un tramo aparte (en `ESTADO.md`): ¿enlace por mapa a peekabooR6?

## Candidatos descubiertos

Ninguno.

## Que gana quien usa la app

En el Coach, junto a "Dónde quedas fuera de posición", ver por mapa y spawn de ataque si salir a pelear antes de tiempo te cuesta rondas o si ese arranque te rinde.

## Criterios de aceptacion

- [x] `/api/positioning/` trae `spawn_exits`, `spawn_exit_attack` y `spawn_exit_seconds`; 14.9 s cuenta, 15.0 no.
- [x] Filtros globales y `POSICION_MIN_RONDAS`; defensa y sin spawn no cuentan.
- [x] Muerte sin reloj no cuenta ni rompe la fila.
- [x] Panel "Salida del spawn" ordenado, con veredicto y textos de vacio.
- [x] Filas en `docs/metricas.md` y caso e2e.

## Diseno

(arquitecto 20261105T1825Z-cVr9Dsg) `SALIDA_SPAWN_SEGUNDOS = 15`, `_temprano` (0 y `None` no cuentan), `spawn_exits(ataque, min_rounds)` dentro de `positioning()`, total del ataque antes del minimo, comparacion contra el resto con `POSICION_BANDAS`. Detalle en `git log`.

## Implementacion

(dev 20261105T1851Z-cBJfgUn) Diseno completo; margen y veredicto extraidos a `_margen_y_veredicto` (tambien lo usa `_contra_el_resto`, sin cambiar claves). Las bajas tempranas se agrupan con la clave entera de la fila. VERDE 6be48da.

## Revision

(revisor 20261105T1920Z-cSTWy1D) Aprobar. MEDIUM aceptado: el e2e solo ve el panel neutro. LOW arreglado: test del borde 14.9 / 15.0 para bajas. VERDE bcfe83a.

## QA 2026-11-05 sobre ff44ebd

(qa 20261105T1945Z-cLLCG3x) `aprobado`. VERDE ff44ebd (990 / 210 / 66). Base sembrada con `factories.py`: Warehouse 8/10 tempranas (15.0 no cuenta, teamkill no suma) "Caes temprano", Shipping 0/10 "Sales bien", Garage sin reloj "Sin señal"; filtros de mapa y defensa, parametros borde y base vacia en 200; Playwright sin errores de consola; chunk inicial igual; 4 mutaciones detectadas. Detalle y comandos en el commit "Prueba: 89 salida del spawn por mapa".

## Verificar en el PC

- Calibrar con la base real la nota de "Salida del spawn"; si da ~0 % en todo, subir `SALIDA_SPAWN_SEGUNDOS` a 20. No bloquea.

## Para el humano

- Aviso, no bloquea este tramo: queda para un tramo aparte decidir si se suma un enlace por mapa a la biblioteca de spawn peeks de peekabooR6 (lo abriria el navegador; la app no le pide nada). La pregunta esta en `ESTADO.md`.
