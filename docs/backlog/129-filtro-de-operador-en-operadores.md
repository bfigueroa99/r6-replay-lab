# 129. Filtro de operador en la pagina Operadores

estado: entregado
candado: -
rama: claude/equipo-dev/129-filtro-de-operador-en-operadores
tipo: funcionalidad
epica: operadores
area: frontend
prioridad: 3
fuente: ALCANCE.md O14 (friccion que vio la QA de la 113)
archivos: frontend/src/operadorElegido.js (nuevo), frontend/src/operadorElegido.test.js (nuevo), frontend/src/pages/Operators.jsx, frontend/e2e/humo.spec.js, docs/metricas.md
turnos: po 20261113T1858Z-cxdASk3, arquitecto 20261113T1926Z-ce4Pmp6, dev 20261113T1954Z-cfZTvvE, revisor 20261113T2003Z-c3vr7mZ, qa 20261113T2156Z-cQ8Kk3s, dev 20261113T2223Z-c24t16L, revisor 20261113T2252Z-cSo9yHH, dev 20261113T2318Z-cpCpgff, revisor 20261113T2345Z-c5J2BqJ, qa 20261113T2345Z-c6MAT6w, release 20261113T2345Z-c6MAT6w

## PR

Titulo: `[equipo-dev][frontend] Filtro de operador en la pagina Operadores`

### Que cambia

La pagina Operadores trae su propio selector de operador. Elegir uno lo pone
en la URL y filtra Por sitio y Repetir o cambiar tras perder; las tablas de
Ataque y Defensa no se vacian: siguen mostrando todo tu pool y resaltan la
fila elegida. Quitarlo (Todos) vuelve a la vista normal, y la vista "sin
rondas" tambien muestra el selector para poder quitarlo.

### Por que esto y no otra cosa

Ficha 129 (ALCANCE.md O14, friccion que vio la QA de la 113): los paneles ya
leian `operator`, pero solo llegaba por la URL. Filtrar tambien Ataque y
Defensa se descarto: quedaban con una sola fila al 100 % de presencia.

### Como se probo

- `check.sh` (con `verificar.sh`): VERDE (ver el comentario de merge; 1321
  tests backend, 435 vitest, 117 e2e sobre 6bb5a18).
- Tests nuevos: vitest `operadorElegido.test.js` (4: sin operador, clase de la
  fila, nota vacia y con operador); e2e `Operadores filtra por operador desde
  su propio selector` (URL, 3 filas por lado, solo Ash con `me` y
  `aria-current`, `/api/operators/` sin `operator=`, Repetir o cambiar igual a
  la API, Todos sin resaltado) y `Operadores sin rondas deja quitar el operador`.
- e2e repetido en paralelo (antes intermitente): 40/40 con `--workers 6`.
- Verificacion manual (QA, Chromium sobre `seed_demo`): recorrido completo con
  la consola limpia, select alcanzable con Tab, contraste de la fila 13.2:1,
  chunk inicial sin cambio (200459 bytes).
- OMC (implementacion): plan=— · revisión=3 hallazgos (3 LOW; 3 arreglados) · verificación=—
- OMC (revisiones): 1 MEDIUM (e2e intermitente) arreglado; LOW restantes no bloquean.
- OMC (QA): plan=— · revisión=— · verificación=PASS (omc-verifier: 5/5 criterios, 0 bloqueos)
- Skills del repo: testing-strategy, accessibility-review (0 Critical, 0 Major; contraste 13.2:1), ux-copy, validate-data (sin numero nuevo)

### Riesgos y lo que no entra

Sin backend, sin migracion ni `recompute`. Fuera: varios operadores a la vez,
cambiar como filtran los endpoints, el resaltado en otras paginas.

### Como probarlo en 2 minutos

```
cd backend; python manage.py seed_demo --force; python manage.py runserver
```
Abrir `http://127.0.0.1:8000/operadores`, elegir Ash en Operador: la URL dice
`?operator=Ash`, Ataque y Defensa siguen con todas sus filas y la de Ash
resaltada; elegir Todos: sin resaltado y sin `operator` en la URL.

### Para el humano

Nada que decidir. LOW que no bloquean, para un Dev despues: la nota nombra
Defensa con `side=Attack`; un `toHaveCount(0)` del e2e corre antes de la
carga; `?operator=NoExiste` muestra "Todos" en el select (comportamiento de
`Filters` en todas las paginas).

### Candidatos descubiertos

Ninguno.

## Que gana quien usa la app

Operadores monta `Filters` con `showOperator={false}`, asi que los paneles
que si usan `operator` (Repetir o cambiar tras perder, A qué operador
cambias, Por sitio) solo lo reciben por la URL o heredado de otra pagina. Un
selector propio deja usar ese filtro sin editar la URL.

## Criterios de aceptacion

- [ ] Operadores muestra el selector de operador de `Filters`; elegir uno
      pone `?operator=<nombre>` en la URL y los paneles que leen `operator`
      recargan con el. e2e: elegir un operador del seed y ver la URL y la
      tabla Repetir o cambiar con solo filas de ese operador (numeros de la API).
- [ ] Las tablas por operador de la pagina (Todos y los grupos por lado) no
      se vacian con el filtro: la fila del operador elegido queda resaltada
      (clase y `aria-current` o equivalente) y las demas siguen. vitest o e2e.
- [ ] Quitar el filtro (opcion "Todos") vuelve a la vista sin resaltado y
      saca `operator` de la URL. e2e.
- [ ] La vista "sin rondas filtradas" de Operadores tambien muestra el
      selector, para poder quitar un operador que deja la pagina vacia. e2e.
- [ ] Consola limpia en todo el recorrido; sin cambios de backend (los
      endpoints ya aceptan `operator`).

## Fuera de alcance

- Selector de varios operadores a la vez.
- Cambiar como filtran `operator` los endpoints.
- El mismo resaltado en otras paginas.

## Implementacion

Resumen (detalle en `git log`): `operadorElegido.js` (`sinOperador`,
`claseFilaOperador`, `textoOperadorElegido`); `Operators.jsx` pide
`/api/operators/` sin `operator`, monta `Filters` con el selector (tambien en
`SinRondasFiltradas`) y resalta la fila con la clase `me` y `aria-current`;
nota de operador elegido solo si hay fila que resaltar; `metricas.md` aclara
Presencia y vs. tu lado. Tres pasadas de Dev (implementacion, e2e intermitente
de la QA, listener antes del `goto` de la segunda revision).

## Revision

Tres pasadas. La 1.a: 3 LOW. La 2.a: 1 MEDIUM (e2e intermitente en paralelo),
arreglado. La 3.a (revisor 20261113T2345Z-c5J2BqJ, sobre 5a72366): aprobar,
2 LOW que no bloquean (a `## Para el humano`).

## QA

Primera QA (20261113T2156Z-cQ8Kk3s): con hallazgos, 1 MEDIUM (e2e
intermitente con `--workers 4`). Segunda QA (20261113T2345Z-c6MAT6w, sobre 6bb5a18):
aprobado. `check.sh` VERDE (1321 backend, 435 vitest, 117 e2e); el e2e antes
intermitente 40/40 en paralelo; recorrido en Chromium sobre `seed_demo` con
la consola limpia (criterios 1 a 5); bordes de URL y de API en 200; chunk
inicial sin cambio; contraste 13.2:1; 3 mutaciones, 3 caen.
OMC: plan=— · revisión=— · verificación=PASS (omc-verifier: 5/5 criterios, 0 bloqueos)
Skills del repo: accessibility-review (0 Critical, 0 Major; contraste 13.2:1), validate-data (sin numero nuevo)

## Para el humano

- (no bloquea) LOW pendientes: la nota nombra Defensa con `side=Attack`; un
  `toHaveCount(0)` del e2e corre antes de la carga; operador sin rondas sin
  aviso; `aria-current` en una celda.
