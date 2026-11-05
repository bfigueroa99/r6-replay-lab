# 80. Donde quedas fuera de posicion, por sitio y spawn

estado: aprobado
candado: -
rama: claude/equipo-dev/80-donde-quedas-fuera-de-posicion
tipo: funcionalidad
epica: posicionamiento
area: fullstack
prioridad: 3
fuente: ALCANCE.md S1, del PR #1 (`claude/loop-lwjbgs`, commit 1ffdb89: pedido del usuario "en que partes del mapa suelo dormir"), cerrado sin merge el 2026-11-05; el humano devolvio la idea a `idea`. La rama queda como referencia, no se mergea
archivos: backend/replays/analytics/aggregates.py (AGGREGATES, derive, positioning), backend/replays/analytics/coach.py (_posicion), backend/replays/views.py (positioning), backend/replays/urls.py, frontend/src/posicion.js, frontend/src/posicion.test.js, frontend/src/pages/Coach.jsx, docs/metricas.md, backend/tests/test_posicion.py, frontend/e2e/humo.spec.js
turnos: po 20261105T0230Z-c8Ahepa, arquitecto 20261105T0349Z-cfLc9Nn, dev 20261105T0418Z-cT3J25j, revisor 20261105T0804Z-cuHheZT, qa 20261105T1205Z-cUisFZX, release 20261105T1205Z-cUisFZX

## PR

Titulo: `[equipo-dev][fullstack] Dónde quedas fuera de posición, por sitio y spawn`

### Que cambia

El Coach gana el panel "Dónde quedas fuera de posición": por sitio de bomba y por spawn de ataque, el porcentaje de rondas en que moriste sin bajas y sin que nadie te vengara, contra el resto de tu historial (para un spawn, el resto de tu ataque), con margen y veredicto. Dos señales nuevas del Coach, `zona-dormidero` y `zona-solida`, salen solo cuando la diferencia pasa dos errores estandar y hay muestra. La metrica `caught_out_pct` entra a todo agregado y a los CSV.

### Por que esto y no otra cosa

Ficha 80 (ALCANCE.md S1, idea del PR #1 cerrado). Es "donde duermo" al nivel que el `.rec` permite (zona, no coordenadas). Panel en el Coach y no pagina propia (la de mapas y sitios sigue descartada). El corte por lado de los sitios lo da el filtro Lado (dos filas por sitio partian la muestra). Margen con la proporcion combinada (Wald daba margen casi nulo en zonas con 0 % o 100 %).

### Como se probo

- verificar.sh: VERDE 0f2847017 (QA, antes de fusionar dev) y sobre el commit de entrega con la 78 ya fusionada; conteos en la seccion QA.
- Tests nuevos: `test_posicion.py` (17: las cuatro condiciones, CSV, contra el resto y no el total, spawn contra el resto del ataque, ruido, dormidero y solido, zona chica, una sola zona, `min_rounds`, filtro de lado, base vacia, señales del Coach); `posicion.test.js` (7); e2e `el Coach muestra dónde quedas fuera de posición` (numeros de seed_demo).
- QA: runserver con base vacia y sembrada, curl a `/api/positioning/`, `/api/coach/` y `/api/export/` con bordes (todo 200), 4 mutaciones que caen.
- OMC: diseno plan=— · revisión=— · verificación=—
- OMC: implementacion plan=— · revisión=7 hallazgos (4 arreglados) · verificación=—
- OMC: revision plan=— · revisión=6 hallazgos (HIGH bajado a MEDIUM por decision de diseno anotada; 0 arreglados) · verificación=—
- OMC: QA plan=— · revisión=— · verificación=PASS

### Riesgos y lo que no entra

Sin migracion ni `recompute` (sale de `died`, `kills`, `was_traded`). Tres consultas mas por carga del Coach. Afuera: posiciones dentro del sitio (el `.rec` no trae coordenadas), pagina de mapas y sitios, salida del spawn (S2).

### Como probarlo en 2 minutos

```
cd backend; python manage.py runserver
```
Abrir el Coach: panel "Dónde quedas fuera de posición" con Sitios y Spawns de ataque. Elegir Lado = Defensa: la tabla de spawns queda vacia y los sitios se comparan contra el resto de tu defensa.

### Para el humano

- Verificar en el PC: con la base real, cuantas zonas salen "Te agarran más" o "Te sostienes" con `POSICION_BANDAS = 2`. Ninguna con cientos de rondas: bajar a 1.5 es una constante; mas de un tercio: el margen es poco.
- Aviso: el detalle de la señal redondea por separado la diferencia y el resto (seed_demo: "+34 puntos contra el 52%" con 85 %). LOW del Revisor, sin cambio.

### Candidatos descubiertos

Ninguno.

## Que gana quien usa la app

Saber en que sitio (defensa) o desde que spawn (ataque) te agarran mal parado, y que el Coach lo diga cuando una zona se aparta de tu historial.

## Criterios de aceptacion

- [x] Metrica `fuera_de_posicion` (`died`, `kills=0`, sin trade) en `AGGREGATES` y en los CSV, sin migracion.
- [x] Tasa por zona contra el **resto** (spawn: resto del ataque), no contra el total. (Ajuste del diseno: vive en `positioning()`, no en `by_site`/`by_spawn`.)
- [x] Panel en el Coach con sitios y spawns, muestra minima y la nota del `.rec`. (Ajuste: "sitio por lado" con el filtro Lado.)
- [x] Señales `zona-dormidero` y `zona-solida` con muestra minima.
- [x] Fila en `docs/metricas.md`; e2e con la consola limpia.

## Diseno (resumen)

`_FUERA_DE_POSICION = Q(died=True, kills=0, was_traded=False)` en `AGGREGATES` y `caught_out_pct` en `derive`. `positioning()` con `_contra_el_resto` (margen = 2 x error estandar, veredicto dormidero/solido/ruido), `GET /api/positioning/`, `coach._posicion` (minimo 8 rondas; una señal de cada tipo). Panel con dos `DataTable` en `Coach.jsx`. Detalle completo en `git log` de esta ficha.

## Implementacion (resumen)

dev 20261105T0418Z-cT3J25j. Diseno completo. Desvio: margen con proporcion combinada (`_ruido_combinado`); margenes de seed_demo B Church ±17.4, A Ventilation ±20.0, Warehouse y Valley ±24.4 (veredictos sin cambio).

## Revision 2026-11-05 sobre 577cf8a

Revisor 20261105T0804Z-cuHheZT. Veredicto: aprobar. MEDIUM: sitios mezclan lados (decision 2 del Arquitecto, reversible). LOW sin cambio: redondeo del detalle, parametro `parte` sin uso en `_ruido_combinado`, `and resto` sobrante, frase de `metricas.md` sin referente.

## QA 2026-11-05 sobre 0f28470

QA 20261105T1205Z-cUisFZX. Base: `tests/factories.py` en un script del scratchpad (Bank: sitio X 12 rondas con 11 fuera, Y 12 con 1, Z 3, 4 rondas sin sitio ni spawn; Oregon: una ronda sin bajas con otro nick).

- `verificar.sh` -> VERDE 0f2847017 (939 backend, 177 vitest, 58 e2e).
- Base vacia, `SQLITE_PATH=<tmp> python3 manage.py runserver 8781`: `curl /api/positioning/`, `?side=Defense`, `?min_rounds=-1` (acotado a 1), `?min_rounds=foo` (5) -> 200, listas vacias, `caught_out_pct` null; `/api/coach/` sin señales de zona.
- Base sembrada: X 91.7 % contra 40.0 % del resto (20 rondas), +51.7 ±35.8 dormidero; Y solido; Z fuera (min 5), con `?min_rounds=1` sale como ruido; spawns Front ruido (6 rondas, ±51.2), Back solido. `?side=Defense`: spawns vacios, resto solo de defensa. `?site=X`: resto 0, margen null, ruido. `?map=noexiste`, `?session=abc`, `?operator=Ash` -> 200 vacio. `?min_rounds=99999999999999999999` -> 10000, 200. `/api/coach/`: "En X (Bank) te agarran fuera de posición el 92% de las rondas" y "En Y (Bank) te sostienes"; con `?side=Defense` (6 rondas por zona < 8) ninguna. `/api/export/?table=sites` trae `caught_out_rounds` y `caught_out_pct`.
- Chunk inicial 190.75 kB (dev 190.68); chunk del Coach 2.1 -> 4.7 kB (lazy).
- Mutaciones en `tests.test_posicion`: sin `was_traded` en `_FUERA_DE_POSICION` -> cae 1; spawn contra el total -> cae 1; `POSICION_MIN_RONDAS_COACH = 1` -> cae 1; dormidero con `delta > 0` -> caen 2.
- `omc-verifier`: PASS (los dos ajustes de criterio estan documentados).

Veredicto: `aprobado`. Release: fusionado `origin/dev` (con la 78): conflicto solo en `humo.spec.js`, dos tests nuevos al final; se quedan los dos.

OMC: plan=— · revisión=— · verificación=PASS

## Verificar en el PC

- Con la base real: cuantas zonas salen `dormidero`/`solido` con `POSICION_BANDAS = 2` (ver `## PR`). Calibrar con la base real.

## Para el humano

- (po/arquitecto, aviso) Panel del Coach y no pagina propia; corte por lado con el filtro Lado; dos errores estandar. Cambiar cualquiera es tocar `Coach.jsx` o `POSICION_BANDAS`.
