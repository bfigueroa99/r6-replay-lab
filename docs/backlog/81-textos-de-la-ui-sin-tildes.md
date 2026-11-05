# 81. Textos de la UI sin tildes en Inicio, Tendencias y otras pantallas

estado: entregado
candado: -
rama: claude/equipo-dev/81-textos-de-la-ui-sin-tildes
tipo: bug
epica: -
area: frontend
prioridad: 4
fuente: QA 20261105T0256Z-cYSSB7z, deriva de docs sobre dev 2da1b7d. `CLAUDE.md` (Estilo): "Los textos que ve el usuario en la UI si llevan tildes y ñ". Varios titulos y hints de `Panel` no las llevan
archivos: frontend/src/App.jsx, frontend/src/components/Filters.jsx, frontend/src/components/ui.jsx, frontend/src/pages/Coach.jsx, frontend/src/pages/Dashboard.jsx, frontend/src/pages/Datos.jsx, frontend/src/pages/Duelos.jsx, frontend/src/pages/Jugador.jsx, frontend/src/pages/MatchDetail.jsx, frontend/src/pages/Matches.jsx, frontend/src/pages/Operators.jsx, frontend/src/pages/Teammates.jsx, frontend/src/pages/Trends.jsx, frontend/e2e/humo.spec.js
turnos: qa 20261105T0256Z-cYSSB7z, arquitecto 20261105T1303Z-cfek47z, dev 20261105T1331Z-c7xSRnu, revisor 20261105T1358Z-caeHwMj, dev 20261105T1429Z-cps2PzJ, revisor 20261105T1455Z-caYiimg, qa 20261105T1521Z-cEexMKJ, dev 20261105T1547Z-ck9KQiv, revisor 20261105T1605Z-csxB8d1, qa 20261105T1613Z-cAimE1D, dev 20261105T1641Z-cY8pL9A, revisor 20261105T1706Z-czYXSXu, qa 20261105T1734Z-cpRZAms, release 20261105T1734Z-cpRZAms

## PR

Titulo: `[equipo-dev][frontend] Los textos de la UI llevan sus tildes`

### Que cambia

Los titulos, hints, avisos y textos visibles de las pantallas llevan sus
tildes y ñ ("Últimas partidas", "Evolución por partida", "Por día de juego",
"Condición: eliminación del equipo rival", "Esa página no existe"), como ya
lo hacian "Compañeros" y "Señales". Solo tildes: no se reescribe ningun texto.

### Por que esto y no otra cosa

Ficha 81, deriva de docs de QA sobre dev 2da1b7d contra la regla de
`CLAUDE.md` (Estilo). Identificadores, claves, rutas, `csvName` y las
cabeceras de columna que son tambien cabecera del CSV (`Cuando`, `Murio`,
`Duro`, `Jugo de`, `Metrica`) quedan como estan a proposito: cambiarlas
cambia los CSV que el usuario ya baja.

### Como se probo

- `check.sh` (con `verificar.sh`): VERDE 613e25e60, 963 tests backend, 199 vitest, 64 e2e.
- Tests: sin tests nuevos (texto); 5 aserciones de `frontend/e2e/humo.spec.js` al texto nuevo. Mutacion: volver "Esa página no existe" y "Cómo se mueven tus números" a sin tilde hace caer 2 e2e.
- Verificacion manual: recorrido en Chromium de 16 rutas sobre `seed_demo` buscando ~50 palabras sin tilde; solo salen conjunciones que no la llevan y las cabeceras de CSV dejadas a proposito.
- OMC: plan=— · revisión=— · verificación=— (Diseno)
- OMC: plan=— · revisión=1 hallazgo (1 arreglado) · verificación=— (Implementacion)
- OMC: plan=— · revisión=1 hallazgo LOW (0 arreglados; el Revisor no arregla) · verificación=— (Revision, cuarta pasada)
- OMC: plan=— · revisión=— · verificación=PASS (QA, tercera)

### Riesgos y lo que no entra

Sin migraciones, sin `recompute`, sin backend. Quedan afuera: las cabeceras
de columna/CSV sin tilde y "Últimas 7 días" en el selector de Tendencias
(concordancia; cambia palabras, no tildes). Los textos del backend los
cubrio la ficha 88, ya en dev.

### Como probarlo en 2 minutos

```powershell
cd backend; python manage.py seed_demo; cd ..\frontend; npm run build; cd ..\backend; python manage.py runserver
```

Abrir `http://127.0.0.1:8000/`: "Últimas partidas" y "Evolución por
partida"; `/tendencias`: "Por día de juego", "Curva de la sesión"; una
partida, una ronda: "Condición: eliminación del equipo rival";
`/no-existe`: "Esa página no existe".

### Para el humano

Nada que bloquee. Dos avisos: una ficha de cabeceras de CSV si se quieren
con tilde, y "Últimas 7 días" -> "últimos 7 días" en Tendencias.

### Candidatos descubiertos

Ninguno.

## Que gana quien usa la app

Los titulos de los paneles se leen bien: "Últimas partidas", "Evolución por
partida", "Por día de juego", en vez de la version sin tildes que hoy
convive con "Compañeros" y "Señales" en la misma app.

## Repro

Sobre dev 2da1b7d:

```bash
cd frontend/src
grep -rnE '(title|hint|label|placeholder|aria-label)="[^"]*\b([Dd]ia|[Ss]esion|[Uu]ltim[ao]s?|[Ee]volucion|cronologico|[Nn]umero|[Mm]etricas?|[Qq]ue tan)\b' --include=*.jsx .
grep -rnE '>[^<{]*\bpagina\b[^<{]*<' --include=*.jsx .
```

Salen, entre otros:

- `pages/Dashboard.jsx:122` "Ultimas partidas"; `:186` "Evolucion por partida" / "orden cronologico"; `:206` "Que tan completa esta la data".
- `pages/Trends.jsx:379` "Por dia de juego" / "Cada punto es una sesion" / "un buen dia"; `:398` "Orden cronologico, de la mas vieja a la mas reciente"; `:422` "Curva de la sesion"; `:465` "de la mas reciente"; `:942` "Por numero de ronda".
- `pages/MatchDetail.jsx:197` "con las metricas derivadas".
- `App.jsx:187` "Esa pagina no existe".

## Criterios de aceptacion

- [x] Los textos listados en el repro llevan sus tildes ("Últimas", "Evolución", "cronológico", "Qué tan completa está", "día", "sesión", "más", "número", "métricas", "página").
- [x] Un barrido de las demas cadenas visibles de `frontend/src` (atributos `title`, `hint`, `label`, `placeholder` y texto JSX) no deja otras sin tilde; los identificadores, claves y comentarios siguen sin tildes.
- [x] Ningun test (vitest ni e2e) quedo afirmando el texto viejo; si alguno lo buscaba, se actualiza al nuevo (hoy el e2e no busca ninguno de los titulos del repro).
- [x] `npm run build` y `check.sh` en verde.

## Fuera de alcance

Reescribir textos (solo tildes); tocar nombres de archivos, rutas, claves de
la API o los CSV (`csvName`); traducir.

## Diseno

(arquitecto 20261105T1303Z-cfek47z, sobre dev 696c79d.) Bug de una forma
obvia: tabla de 59 cadenas en 13 `.jsx` de `frontend/src` (solo tildes), tres
aserciones de `humo.spec.js` al texto nuevo y tres greps de verificacion. Se
dejan a proposito "Periodo", "solo", "Cuando salga" (conjuncion), y todo
identificador, clave, ruta, `csvName` y comentario. La tabla completa esta en
`git log` de esta ficha.

OMC: plan=— · revisión=— · verificación=—

## Implementacion

(dev 20261105T1331Z-c7xSRnu, y correcciones de dev 1429Z-cps2PzJ,
1547Z-ck9KQiv y 1641Z-cY8pL9A.) Tabla aplicada entera; despues, lo que
fueron encontrando revision y QA: "Últimos", "mató a"/"murió" de la
timeline, "Te ganó", "presión", "Apóyate", "Qué hacer", "registró",
"referencia sólida", el mapa `CONDITIONS` ("eliminación", "se acabó el
tiempo"), el `render` de pantalla de la columna de muerte (`'sí'`; el CSV
sigue en `'si'`) y el chip "compañero" de "Jugo de" (el valor de la API no
cambia). Sin tests nuevos; 5 aserciones de `humo.spec.js` al texto nuevo.

Skills: no aplica (cambio de textos).
OMC: plan=— · revisión=1 hallazgo (1 arreglado) · verificación=—

## Revision

Cuatro pasadas (revisor 1358Z-caeHwMj, 1455Z-caYiimg, 1605Z-csxB8d1,
1706Z-czYXSXu), revision a ciegas con `omc-code-reviewer`. La primera dejo un
MEDIUM (cadenas visibles fuera de la tabla), corregido. Las siguientes,
`revisado` con LOW: "registró" (corregido) y dos que no bloquean (ver
`## Para el humano`). Ultimo veredicto, sobre d668c93: aprobar.

OMC: plan=— · revisión=1 hallazgo LOW (0 arreglados; el Revisor no arregla) · verificación=—

## QA

Primera QA (1521Z-cEexMKJ) y segunda (1613Z-cAimE1D): `con hallazgos` por
cadenas visibles sin tilde (`referencia solida`, `no registro eventos`;
`CONDITIONS` y `'si'` de `MatchDetail.jsx`), corregidas.

### Tercera QA 2026-11-05 sobre 613e25e

(qa 20261105T1734Z-cpRZAms; rama al dia con dev e7cc919. Base de `seed_demo`
en el scratchpad; nunca `.rec` ni `.sqlite3` al repo.)

Evidencia por criterio:

1. Textos del repro con tilde: cubierto. Mutacion: "Esa página no existe"
   (`App.jsx`) y "Cómo se mueven tus números" (`Trends.jsx`) vueltos a sin
   tilde, `npx vite build`,
   `E2E_CHROMIUM=/opt/pw-browsers/chromium-1243/chrome-linux64/chrome npx playwright test -g "una ruta que no existe|un filtro sin rondas deja la barra"`:
   2 failed; restaurado y rebuild: 2 passed.
2. Barrido de las demas cadenas visibles: cubierto. `runserver` con
   `SQLITE_PATH` en el scratchpad + `seed_demo` (29 partidas), recorrido en
   Chromium de 16 rutas (`/`, `/coach`, `/operadores`, `/companeros`,
   `/duelos`, `/tendencias`, `/partidas`, `/partidas/1`, `/partidas/29`,
   `/partidas/99999`, `/jugadores/1`, `/jugadores/2`, `/ruleta`, `/datos`,
   `/ajustes`, `/no-existe`) con una regex de ~50 palabras sin tilde sobre
   `body.innerText` y `title`/`placeholder`/`aria-label`. Solo salen
   conjunciones y relativos que no la llevan ("que", "como", "cuando", "esta
   tabla", "sea de quien sea"), la ruta `docs/metricas.md` y las cabeceras de
   columna/CSV que la ficha deja a proposito (`Metrica`, `Jugo de`, `Cuando`,
   `Murio`). Se ve "Condición: eliminación del equipo rival" y la columna de
   muerte pinta "sí". Unico error de consola: el 404 de `/partidas/99999`
   (esperado). `omc-verifier` hizo su propio grep (~100 palabras e
   interrogativas en mayuscula sobre `*.jsx`/`*.js`): nada fuera de las
   excepciones.
3. Ningun test afirma el texto viejo: cubierto (suite verde; los 5 cambios
   de `humo.spec.js` van al texto nuevo, y la mutacion de 1 los hace caer).
4. Build y `check.sh`: cubierto. `verificar.sh`: VERDE 613e25e60 (963 tests
   backend, 199 vitest, 64 e2e). Chunk inicial `index-*.js` 191939 bytes
   (segunda QA: 191687; solo los bytes de las tildes).

Veredicto: `aprobado`. El LOW de "Últimas 7 días" queda en `## Para el
humano` (cambia palabras, fuera de alcance).

OMC: plan=— · revisión=— · verificación=PASS

## Verificar en el PC

## Pendiente

## Para el humano

- 2026-11-05 (revisor 20261105T1455Z-caYiimg): LOW sin arreglar, no bloquean (el de `MatchDetail.jsx:309` ya quedo arreglado en la correccion de QA): cabeceras `'Jugo de'`, `'Metrica'` (junto a `'Cuando'`, `'Duro'`, `'Murio'`) quedan sin tilde porque son tambien cabecera del CSV: decidir en una ficha de cabeceras de CSV.
- 2026-11-05 (revisor 20261105T1706Z-czYXSXu): LOW fuera de alcance, no bloquea: el selector de ventana de Tendencias dice "Últimas 7 días" / "Últimas 30 días" (`Trends.jsx:321`, concordancia de genero, ya estaba en dev). Arreglarlo cambia palabras, no tildes: va en otra ficha si se quiere.
