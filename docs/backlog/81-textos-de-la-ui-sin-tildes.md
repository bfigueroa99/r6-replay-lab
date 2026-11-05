# 81. Textos de la UI sin tildes en Inicio, Tendencias y otras pantallas

estado: revisado
candado: -
rama: claude/equipo-dev/81-textos-de-la-ui-sin-tildes
tipo: bug
epica: -
area: frontend
prioridad: 4
fuente: QA 20261105T0256Z-cYSSB7z, deriva de docs sobre dev 2da1b7d. `CLAUDE.md` (Estilo): "Los textos que ve el usuario en la UI si llevan tildes y ñ". Varios titulos y hints de `Panel` no las llevan
archivos: frontend/src/App.jsx, frontend/src/components/Filters.jsx, frontend/src/components/ui.jsx, frontend/src/pages/Coach.jsx, frontend/src/pages/Dashboard.jsx, frontend/src/pages/Datos.jsx, frontend/src/pages/Duelos.jsx, frontend/src/pages/Jugador.jsx, frontend/src/pages/MatchDetail.jsx, frontend/src/pages/Matches.jsx, frontend/src/pages/Operators.jsx, frontend/src/pages/Teammates.jsx, frontend/src/pages/Trends.jsx, frontend/e2e/humo.spec.js
turnos: qa 20261105T0256Z-cYSSB7z, arquitecto 20261105T1303Z-cfek47z, dev 20261105T1331Z-c7xSRnu, revisor 20261105T1358Z-caeHwMj, dev 20261105T1429Z-cps2PzJ, revisor 20261105T1455Z-caYiimg, qa 20261105T1521Z-cEexMKJ, dev 20261105T1547Z-ck9KQiv, revisor 20261105T1605Z-csxB8d1, qa 20261105T1613Z-cAimE1D, dev 20261105T1641Z-cY8pL9A, revisor 20261105T1706Z-czYXSXu

## PR

(La escribe el Release manager al final.)

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

- [ ] Los textos listados en el repro llevan sus tildes ("Últimas", "Evolución", "cronológico", "Qué tan completa está", "día", "sesión", "más", "número", "métricas", "página").
- [ ] Un barrido de las demas cadenas visibles de `frontend/src` (atributos `title`, `hint`, `label`, `placeholder` y texto JSX) no deja otras sin tilde; los identificadores, claves y comentarios siguen sin tildes.
- [ ] Ningun test (vitest ni e2e) quedo afirmando el texto viejo; si alguno lo buscaba, se actualiza al nuevo (hoy el e2e no busca ninguno de los titulos del repro).
- [ ] `npm run build` y `check.sh` en verde.

## Fuera de alcance

Reescribir textos (solo tildes); tocar nombres de archivos, rutas, claves de
la API o los CSV (`csvName`); traducir.

## Diseno

(arquitecto 20261105T1303Z-cfek47z, sobre dev 696c79d. Bug de una forma
obvia: sin consenso ni arena. El barrido ya esta hecho aca: el Dev aplica la
lista, no decide palabras.)

**Alcance cerrado:** cadenas visibles de los `.jsx` de `frontend/src`
(atributos `title`, `hint`, `label`, `help`, `sub`, `empty`, `placeholder`,
literales que se pintan y texto JSX). Los `.js` de logica ya llevan sus tildes
(barrido: `importacion.js`, `resumenPartida.js` sin faltas visibles) y los
textos que manda el backend (coach, mensajes de importacion) quedan fuera,
como dice "Fuera de alcance". Identificadores, claves, comentarios, rutas y
`csvName` no se tocan.

**Lo que se deja como esta, a proposito:** "Periodo" (`Filters.jsx`, la RAE
admite periodo y período; el e2e lo busca asi), "solo" (sin tilde desde 2010),
"Cuando salga una temporada" (`Datos.jsx`, conjuncion), "ninguna" (no lleva).

**Prioriza, no bloquea:** comparte `MatchDetail.jsx` con la 79 (en curso) y la
82, `Datos.jsx` y `Matches.jsx` con la 83, y `ui.jsx:241` con la 84 (que
reescribe ese aviso). Son cambios de una palabra: el que mergea segundo
resuelve con P3.

### Lista (lineas de dev 696c79d; buscar el texto, no el numero)

| archivo:linea | hoy | queda |
|---|---|---|
| `App.jsx:107` | No habia partidas nuevas | No había partidas nuevas |
| `App.jsx:187` | Esa pagina no existe | Esa página no existe |
| `components/Filters.jsx:113` | Sesion (label) | Sesión |
| `components/ui.jsx:241` | Revisa que Django este corriendo | Revisa que Django esté corriendo |
| `pages/Coach.jsx:16` | Lo que mas te esta costando | Lo que más te está costando |
| `pages/Coach.jsx:18` | Señales mas debiles | Señales más débiles |
| `pages/Coach.jsx:38-39` | el numero, con que se compara / y cuantas rondas | el número, con qué se compara / y cuántas rondas |
| `pages/Dashboard.jsx:165` | Ultimas partidas | Últimas partidas |
| `pages/Dashboard.jsx:189`, `Matches.jsx:105`, `Operators.jsx:91`, `Trends.jsx:109`, `:215`, `:446`, `:477` | (help) es tu ronda tipica | es tu ronda típica |
| `pages/Dashboard.jsx:229` | Evolucion por partida / en orden cronologico | Evolución por partida / en orden cronológico |
| `pages/Dashboard.jsx:230` | Cargando grafico... | Cargando gráfico... |
| `pages/Dashboard.jsx:237` | Ver todo el analisis | Ver todo el análisis |
| `pages/Dashboard.jsx:249` | Que tan completa esta la data | Qué tan completa está la data |
| `pages/Dashboard.jsx:253` | la condicion de victoria | la condición de victoria |
| `pages/Dashboard.jsx:259` | y despues hay que | y después hay que |
| `pages/Dashboard.jsx:264` | en esta version del juego | en esta versión del juego |
| `pages/Datos.jsx:63` | No habia nada importado | No había nada importado |
| `pages/Datos.jsx:82` | Que tan completa esta tu base | Qué tan completa está tu base |
| `pages/Datos.jsx:117` | asi que delatan cual es: | así que delatan cuál es: |
| `pages/Datos.jsx:127` | Ningun sitio detectado | Ningún sitio detectado |
| `pages/Datos.jsx:150` | 'lo jugaste tu' | 'lo jugaste tú' |
| `pages/Datos.jsx:213` | van a aparecer aca solos | van a aparecer acá solos |
| `pages/Datos.jsx:219` | Importacion (title) | Importación |
| `pages/Datos.jsx:269` | Todavia no hay importaciones | Todavía no hay importaciones |
| `pages/Duelos.jsx:52` | Muestra minima | Muestra mínima |
| `pages/Duelos.jsx:80` | Quien te mata y a quien matas | Quién te mata y a quién matas |
| `pages/Duelos.jsx:106` | Con que operador te estaban matando | Con qué operador te estaban matando |
| `pages/Duelos.jsx:108` | que no estas limpiando, no punteria | que no estás limpiando, no puntería |
| `pages/Duelos.jsx:125` | Ningun operador llega | Ningún operador llega |
| `pages/Duelos.jsx:170` | asi que un cambio de nick | así que un cambio de nick |
| `pages/Jugador.jsx:50` | eres tu | eres tú |
| `pages/Jugador.jsx:83` | asi que la diferencia | así que la diferencia |
| `pages/Jugador.jsx:84` | Tus numeros en las rondas | Tus números en las rondas |
| `pages/Jugador.jsx:144` | Sus numeros (title) | Sus números |
| `pages/Jugador.jsx:145` | asi que no incluye | así que no incluye |
| `pages/MatchDetail.jsx:132` | Condicion: | Condición: |
| `pages/MatchDetail.jsx:205` | con las metricas derivadas | con las métricas derivadas |
| `pages/Teammates.jsx:68` | Con quien ganas y con quien no | Con quién ganas y con quién no |
| `pages/Teammates.jsx:78` | (hint) sube la muestra minima | sube la muestra mínima |
| `pages/Teammates.jsx:81` | Muestra minima | Muestra mínima |
| `pages/Teammates.jsx:370` | Todavia no ganaste | Todavía no ganaste |
| `pages/Trends.jsx:296` | Como se mueven tus numeros ... en que momento | Cómo se mueven tus números ... en qué momento |
| `pages/Trends.jsx:306-308` | es cuanto se mueve / una metrica / solo la direccion | es cuánto se mueve / una métrica / solo la dirección |
| `pages/Trends.jsx:316` | Ultimas {v.label} | Últimas {v.label} |
| `pages/Trends.jsx:327` | Los numeros estan abajo ... que algo cambio | Los números están abajo ... que algo cambió |
| `pages/Trends.jsx:350` | Error estandar ... el tamano tipico | Error estándar ... el tamaño típico |
| `pages/Trends.jsx:379` | Por dia de juego / es una sesion / un buen dia | Por día de juego / es una sesión / un buen día |
| `pages/Trends.jsx:398` | Orden cronologico, de la mas vieja a la mas reciente | Orden cronológico, de la más vieja a la más reciente |
| `pages/Trends.jsx:422` | Curva de la sesion | Curva de la sesión |
| `pages/Trends.jsx:423` | Como rindes segun ... Una sesion se corta despues de | Cómo rindes según ... Una sesión se corta después de |
| `pages/Trends.jsx:433` | partida de la sesion | partida de la sesión |
| `pages/Trends.jsx:465` | de la mas reciente hacia atras | de la más reciente hacia atrás |
| `pages/Trends.jsx:531` | Cuando mueres (title) | Cuándo mueres |
| `pages/Trends.jsx:535` | de fase de accion | de fase de acción |
| `pages/Trends.jsx:563` | primeros 30s de accion | primeros 30s de acción |
| `pages/Trends.jsx:590` | cuantas quedaron sin vengar | cuántas quedaron sin vengar |
| `pages/Trends.jsx:942` | Por numero de ronda | Por número de ronda |

Si al aplicar aparece en la misma cadena otra palabra sin tilde que la tabla
no lista, se corrige igual y se anota en `## Implementacion` (misma regla: solo
tildes, sin reescribir).

### Tests que cambian (afirman el texto viejo)

- `frontend/e2e/humo.spec.js:676`: heading `'Sus numeros'` → `'Sus números'`.
- `frontend/e2e/humo.spec.js:709`: `'No habia partidas nuevas para importar.'`
  → `'No había partidas nuevas para importar.'`.
- `frontend/e2e/humo.spec.js:719`: `'Esa pagina no existe'` → `'Esa página no existe'`.

Ningun vitest afirma estos textos (barrido de `src/*.test.js`). Sin tests
nuevos: es texto, y el e2e ya pasa por cada pantalla con la consola vigilada.

### Verificacion del barrido (la corre el Dev antes de `check.sh`)

```bash
cd frontend/src
grep -rnE "(title|hint|label|help|sub|empty|placeholder)=\"[^\"]*\b(dia|sesion|[Uu]ltim[ao]s?|[Ee]volucion|cronologico|numeros?|metricas?|pagina|aca|todavia|despues|segun|[Nn]ingun|habia|asi|condicion|[Ii]mportacion|minima|tipica|analisis|grafico|version|estandar|accion)\b" --include=*.jsx .
grep -rnE "'[^']*\b(Ultimas|tipica|numeros|pagina|habia|Todavia|Ningun|asi que|mas te|mas debiles|estas limpiando|punteria|jugaste tu|cronologico|sesion|despues|segun)\b[^']*'" --include=*.jsx .
grep -rnE ">\s*[^<{]*\b(Ultimas|Sesion|Importacion|Condicion|Evolucion|numeros|pagina|habia|Todavia)\b" --include=*.jsx .
```

Las tres salen vacias (sobre dev 696c79d dan 29 lineas, todas de la tabla).

### Orden de implementacion

1. Aplicar la tabla archivo por archivo.
2. Los tres cambios de `humo.spec.js`.
3. Los greps de arriba; `npm run build`; `check.sh` completo.

### Que puede romperse

- Un e2e que busque un texto de la tabla que este barrido no vio: el e2e
  falla con el texto exacto y se actualiza igual que los tres de arriba.
- Choques de contexto con 79, 82, 83 y 84 (ver arriba).

### Verificacion manual en el PC

No hace falta. Se ve recorriendo Inicio, Tendencias, Datos y el detalle.

Skills: no aplica (cambio de textos).
Arena: no (una sola forma obvia).

OMC: plan=— · revisión=— · verificación=—

## Implementacion

(dev 20261105T1331Z-c7xSRnu, sobre dev 696c79d.)

Quedo: la tabla del diseno aplicada entera (59 filas, 13 archivos de
`frontend/src`) y los tres textos de `frontend/e2e/humo.spec.js` (676, 709,
719) al texto nuevo. Los tres greps de "Verificacion del barrido" salen
vacios. Identificadores (`etiquetaSesion`, `EvolucionChart`,
`etiquetaImportacion`), claves, rutas, `csvName` y comentarios sin tocar.

Desvios (misma regla del diseno: otra palabra sin tilde en una cadena ya
tocada o vecina, solo tildes):

- `Matches.jsx` y `Operators.jsx`, help de Rating: "la formula" -> "la fórmula".
- `Dashboard.jsx`, lista de salud: "plant probable segun el reloj" -> "según".
- `Duelos.jsx`, hint "Por rival": "anecdota y no patron" -> "anécdota y no patrón".
- `Teammates.jsx:370`: "quedandote" -> "quedándote" (lo marco la revision ciega).

No quedo: nada de la ficha. Un barrido extra de palabras comunes (tambien,
numero, despues, segun, sesion, version, ...) fuera de comentarios solo
encontro identificadores.

Tests: sin tests nuevos (texto); el e2e recorre cada pantalla con la consola
vigilada. `verificar.sh`: VERDE ebb00f844 (953 tests backend, 186 vitest,
59 e2e).

Skills: no aplica (cambio de textos).
OMC: plan=— · revisión=1 hallazgo (1 arreglado) · verificación=—

## Revision 2026-11-05 sobre 9461e04

(revisor 20261105T1358Z-caeHwMj; rama al dia con dev 696c79d.)

Revision a ciegas (`omc-code-reviewer`, eje de estandares; diff de un solo
tema, solo cadenas). Ningun texto cambiado es clave: `csvName`, `label` de
columnas (cabecera del CSV) e identificadores siguen igual; los tres textos
que afirma el e2e se actualizaron; sin tildes en comentarios ni
identificadores; sin `console.log`. `verificar.sh`: VERDE 94f3c93 (953 tests
backend, 186 vitest, 59 e2e).

Hallazgos (confirmados por el Revisor con `grep` sobre la rama):

- [bug] MEDIUM criterio 2 sin cumplir: el barrido dejo textos visibles sin
  tilde.
  Que pasa: quedan cadenas que se pintan, fuera de la tabla del diseno, que
  el criterio "no deja otras sin tilde" cubre.
  Como reproducirlo o por que es cierto: `grep -nE "Ultimos|'7 dias'|'30 dias'|> mato a|> murio|Te gano|presion|Que hacer|Apoyate|· duro |'Duro'" frontend/src -r`
  sobre la rama devuelve:
  - `components/Filters.jsx:11-13`: "Ultimos 7 dias" / "30" / "90" (selector
    de periodo de casi todas las paginas) -> "Últimos 7 días", etc.
  - `pages/Trends.jsx:40-41`: `label: '7 dias'`, `'30 dias'` (se pinta en
    "Últimas {v.label}") -> "7 días", "30 días".
  - `pages/MatchDetail.jsx:313` "mato a" y `:317` "murio" (cada evento de la
    timeline) -> "mató a", "murió". **Ojo:** el e2e `el timeline marca la
    apertura de cada ronda` (`e2e/humo.spec.js`, `hasText: /mato a|murio/`)
    las busca: hay que cambiar la regex a `/mató a|murió/` en el mismo commit.
  - `pages/MatchDetail.jsx:130` "duro {n}s" -> "duró".
  - `pages/Jugador.jsx:123` "Te gano" -> "Te ganó".
  - `pages/Coach.jsx:19` "Apoyate en esto" -> "Apóyate"; `:56` "Que hacer:"
    -> "Qué hacer:".
  - `pages/Trends.jsx:943` "bajo presion" -> "presión".
  Arreglo sugerido: aplicar esas tildes (solo tildes) y el ajuste de la regex
  del e2e; repetir el barrido con verbos en preterito (`-o\b` agudos:
  mato, murio, gano, quedo, duro) que el grep del diseno no miraba.

- [estilo] LOW `label: 'Cuando'` (Dashboard.jsx:192, Matches.jsx:91,
  Jugador.jsx:205, Teammates.jsx:351, Trends.jsx:470, Datos.jsx:253) y
  `label: 'Duro'` (Trends.jsx:474).
  Que pasa: cabeceras de columna sin tilde ("Cuándo", "Duró").
  Por que es cierto: son interrogativo / preterito visibles; pero el `label`
  es tambien la cabecera del CSV descargado, que "Fuera de alcance" deja
  quieto implicitamente (claves y CSV).
  Arreglo sugerido: decision del Dev; la variante conservadora es dejarlas y
  anotarlo en `## Implementacion`. No bloquea.

Veredicto: corregir -> `con hallazgos` (el MEDIUM deja el criterio 2 sin
cumplir; es la razon de ser de la ficha).

OMC: plan=— · revisión=2 hallazgos (0 arreglados; el Revisor no arregla) · verificación=—

### Correccion de hallazgos (dev 20261105T1429Z-cps2PzJ, sobre dev mezclado en 394d368)

P3: la rama chocaba con dev en `MatchDetail.jsx` (la 82 envolvio el panel
Rondas en `{round ? ...}`); resuelto tomando el bloque de dev y reaplicando
"Condición".

MEDIUM del Revisor, aplicado entero (solo tildes):

- `Filters.jsx`: "Últimos 7/30/90 días".
- `Trends.jsx`: `label: '7 días'`, `'30 días'`; hint "bajo presión".
- `MatchDetail.jsx`: timeline "mató a" / "murió"; "duró {n}s".
- `Jugador.jsx`: "Te ganó". `Coach.jsx`: "Apóyate en esto", "Qué hacer:".
- e2e: regex de la timeline a `/mató a|murió/`, y el subtitulo de Tendencias
  del test `un filtro sin rondas deja la barra en todas las páginas` (entro a
  dev con la 85 afirmando el texto viejo; el primer `check.sh` fallo ahi).

Barrido extra de preteritos agudos (mato, murio, gano, quedo, duro, cambio,
paso, bajo, ...) y de palabras comunes en cadenas visibles: solo quedan
sustantivos ("cambio", "bajo" adjetivo) e identificadores.

LOW (cabeceras `label: 'Cuando'`, `'Duro'`, y `'Murio'`/`'Murio a los'` de
la tabla de jugadores de la ronda): se dejan como estan, variante
conservadora. El `label` de una columna es tambien la cabecera del CSV
descargado, y "Fuera de alcance" deja quieto lo del CSV. Si se quiere, va en
una ficha aparte que decida las cabeceras de CSV.

Revision ciega (`omc-code-reviewer`): 1 HIGH (el e2e de la 85), arreglado;
sin tildes mal puestas.

`verificar.sh`: VERDE de1a41e2c (954 tests backend, 190 vitest, 61 e2e).

Skills: no aplica (cambio de textos).
OMC: plan=— · revisión=1 hallazgo (1 arreglado) · verificación=—

## Revision 2026-11-05 sobre 7015c73 (segunda pasada)

(revisor 20261105T1455Z-caYiimg; rama al dia con dev 85009f6.)

Revision a ciegas (`omc-code-reviewer`, eje de estandares; un solo tema,
solo cadenas, sin eje de intencion ni seguridad). Confirmado por el Revisor:
ningun `value`, `key`, ruta, `csvName` ni cabecera de CSV cambio (los `label`
tocados son los del selector de periodo de `Filters.jsx` y de `Trends.jsx`,
solo visibles; en Trends el label tambien es `key` de un `<option>` y sigue
unico); las tildes agregadas son correctas ("solo" sigue sin tilde); ningun
e2e ni vitest afirma un texto viejo. El MEDIUM de la primera pasada quedo
resuelto entero (`grep` sobre la rama: sin "Ultimos", "mato a", "murio",
"Te gano", "Apoyate", "Que hacer", "presion" visibles).

Criterios: 1 cubierto (tabla del diseno aplicada, greps del barrido vacios);
2 cubierto salvo los LOW de abajo; 3 cubierto (`humo.spec.js` actualizado,
e2e verde); 4 `verificar.sh`: VERDE 244da02af (954 tests backend, 190
vitest, 61 e2e).

Hallazgos (todos LOW, no bloquean):

- [estilo] LOW `frontend/src/pages/MatchDetail.jsx:309`
  Que pasa: "Esta ronda no registro eventos en el feed." sigue sin tilde.
  Como reproducirlo: `grep -n "no registro" frontend/src -r` sobre la rama.
  Arreglo sugerido: "registró". Es texto suelto (no `label` ni CSV).
- [estilo] LOW cabeceras `label: 'Jugo de'` (`Jugador.jsx:213`) y
  `label: 'Metrica'` (`Trends.jsx:338`), de la misma familia que `'Cuando'`,
  `'Duro'`, `'Murio'` que el Dev dejo a proposito (el `label` es tambien la
  cabecera del CSV). Coherente con esa decision; van juntas a la ficha de
  cabeceras de CSV si se abre.

Veredicto: aprobar -> `revisado`. Los LOW quedan en `## Para el humano` de
la ficha.

OMC: plan=— · revisión=3 hallazgos LOW (0 arreglados; el Revisor no arregla) · verificación=—

## QA 2026-11-05 sobre d45abbb

(qa 20261105T1521Z-cEexMKJ; rama al dia con dev 85009f6. Base sintetica en
el scratchpad, nunca `.rec` ni `.sqlite3` al repo.)

Evidencia por criterio:

1. Textos del repro con tilde: cubierto. Los tres greps de "Verificacion del
   barrido" sobre `frontend/src` dan 0 lineas. Recorrido en Chromium de 15
   rutas (`/`, `/coach`, `/operadores`, `/companeros`, `/duelos`,
   `/tendencias`, `/partidas`, `/partidas/1`, `/partidas/5`, `/jugadores/1`,
   `/ruleta`, `/datos`, `/ajustes`, `/no-existe`, `/partidas/99999`) con
   `runserver` sobre base vacia y sobre base de `seed_demo`, filtrando
   `body.innerText` por ~40 palabras que suelen llevar tilde: no queda ninguna
   de la tabla. Consola: solo los 404 esperados de partidas inexistentes.
2. Barrido de las demas cadenas visibles: **falla**. Quedan dos textos
   sueltos que se pintan (no son `label` de columna ni CSV, asi que la
   excepcion conservadora del Dev no los cubre):
   - `frontend/src/pages/Dashboard.jsx:77` `sub="referencia solida: 0.8"`
     (Stat "Kills por ronda" de Inicio) -> "referencia sólida: 0.8". Lo
     encontro `omc-verifier`; no estaba en la tabla ni en ninguna revision.
   - `frontend/src/pages/MatchDetail.jsx:309` "Esta ronda no registro eventos
     en el feed." -> "registró" (el LOW de la segunda revision).
   Repro: `git grep -nE "referencia solida|no registro eventos" origin/claude/equipo-dev/81-textos-de-la-ui-sin-tildes -- frontend/src`
   devuelve esas dos lineas. Un barrido mas ancho (solida, rapida, ultima,
   unica, facil, posicion, duracion, tambien, ademas, atras, ... en cadenas,
   fuera de comentarios) no encontro otras: el resto son imports, `csvName`
   e identificadores.
3. Ningun test afirma el texto viejo: cubierto. Mutacion: con "Esa pagina no
   existe" (`App.jsx`) y "mato a" / "murio" (`MatchDetail.jsx`) de vuelta sin
   tilde, `vite build` y
   `E2E_CHROMIUM=/opt/pw-browsers/chromium-1243/chrome-linux64/chrome npx playwright test -g "timeline marca la apertura|ruta que no existe"`:
   2 failed; restaurado: 2 passed.
4. Build y `check.sh`: cubierto. `verificar.sh`: VERDE d45abbbbd (954 tests
   backend, 190 vitest, 61 e2e). Chunk inicial de `vite build`: dev
   191.14 kB -> rama 191.23 kB (+0.05 %).

Fuera de alcance, para otra ficha: la narrativa de la partida que arma el
backend (`backend/replays/analytics/narrative.py:64,80,91`) dice "te mato X.
Nadie la vengo. ... la vengo 3s despues", visible en el detalle de cada
partida.

Veredicto: `con hallazgos`. Arreglo: las dos tildes de arriba (y nada mas);
ningun test las afirma.

OMC: plan=— · revisión=— · verificación=INCOMPLETE (criterio 2 PARTIAL: `Dashboard.jsx:77`)

### Correccion de hallazgos de QA (dev 20261105T1547Z-ck9KQiv, sobre dev 0861b0b mezclado)

Rama mezclada con dev 0861b0b (sin conflictos; trae la 86, cuyos textos ya
llevan tilde). Aplicadas las dos tildes que pidio QA, y nada mas:

- `Dashboard.jsx:77`: `sub="referencia sólida: 0.8"`.
- `MatchDetail.jsx:309`: "Esta ronda no registró eventos en el feed." (cierra
  tambien el LOW de la segunda revision).

Ningun test afirmaba el texto viejo (`grep` en `frontend/e2e`,
`frontend/src/*.test.js` y `backend/tests`). La narrativa del backend
(`narrative.py`) sigue fuera de alcance: es la ficha 88.

Revision ciega (`omc-code-reviewer`): aprobar, 0 hallazgos.

`verificar.sh`: VERDE f40f33f9d (955 tests backend, 197 vitest, 62 e2e).

Skills: no aplica (cambio de textos).
OMC: plan=— · revisión=0 hallazgos · verificación=—

## Revision 2026-11-05 sobre 9f5cabc (tercera pasada)

(revisor 20261105T1605Z-csxB8d1; rama al dia con dev 0861b0b.)

Revision a ciegas (`omc-code-reviewer`, eje de estandares; un solo tema,
solo cadenas, sin eje de intencion ni seguridad): aprobar, 0 hallazgos sobre
las lineas tocadas. Tildes agregadas correctas (interrogativos indirectos,
preteritos, "tú" tonico; "solo" sin tilde); ningun `value`, `key` de estado,
`csvName` ni ruta cambio; los cinco asserts de `humo.spec.js` coinciden con el
texto nuevo y ningun e2e ni vitest busca un texto viejo.

Confirmado por el Revisor: los dos textos que pidio QA quedaron con tilde
(`git grep -nE "referencia solida|no registro eventos" -- frontend/src` vacio).
El delta desde la QA son esas dos lineas.

Criterios: 1 cubierto (tabla del diseno, greps del barrido vacios); 2
cubierto salvo las cabeceras de columna/CSV que el Dev dejo a proposito; 3
cubierto; 4 `verificar.sh`: VERDE 9f5cabc87 (955 tests backend, 197 vitest,
62 e2e).

Hallazgos: solo los LOW ya conocidos (`label: 'Duro'` en `Trends.jsx`,
`'Cuando'` en seis tablas), que el ciego volvio a marcar; son cabecera del CSV
y ya estan en `## Para el humano`. Tercera pasada con solo LOW: `revisado`.

Veredicto: aprobar -> `revisado`.

OMC: plan=— · revisión=2 hallazgos LOW ya conocidos (0 arreglados; el Revisor no arregla) · verificación=—

## QA 2026-11-05 sobre a7b7f5c (segunda QA)

(qa 20261105T1613Z-cAimE1D; rama al dia con dev 0861b0b. Base de
`seed_demo` en el scratchpad; nunca `.rec` ni `.sqlite3` al repo.)

Evidencia por criterio:

1. Textos del repro con tilde: cubierto. Los tres greps de "Verificacion del
   barrido" sobre `frontend/src`: 0 lineas cada uno;
   `git grep -nE "referencia solida|no registro eventos" -- frontend/src`: 0.
2. Barrido de las demas cadenas visibles: **falla**. Lo encontro
   `omc-verifier` y lo confirme leyendo el codigo y `seed_demo`:
   - `frontend/src/pages/MatchDetail.jsx:360` `'eliminacion del equipo rival'`
     y `:363` `'se acabo el tiempo'` (mapa `CONDITIONS`, que pinta
     `translateCondition` en "Condición: ..." del panel de la ronda,
     `MatchDetail.jsx:134`). Se ve en cualquier ronda ganada por eliminacion
     (`seed_demo` las siembra con `win_condition="KilledOpponents"`):
     "Condición: eliminacion del equipo rival" -> "eliminación";
     "se acabó el tiempo".
   - `frontend/src/pages/MatchDetail.jsx:161` `render: (row) => (row.died ? 'si' : 'no')`
     (columna "Murio" de la tabla de jugadores de la ronda): el `render` es
     solo pantalla (el CSV lo arma `ui.jsx:90` aparte), asi que `'si'` ->
     `'sí'`. El `'si'` de `ui.jsx:90` es el valor del CSV y queda como esta
     (fuera de alcance, lo afirma `logica.test.js:139`).
   Repro: `git grep -nE "eliminacion del equipo|se acabo el tiempo|'si' : 'no'" origin/claude/equipo-dev/81-textos-de-la-ui-sin-tildes -- frontend/src/pages`
   devuelve las tres lineas. Mi recorrido en Chromium (14 rutas, ~50
   palabras en `body.innerText`) no las vio porque su lista no tenia
   "eliminacion" ni "acabo": la unica sin tilde que salio fue "mato", de la
   narrativa del backend (ficha 88).
   `label: 'Murio a los'` (`MatchDetail.jsx:165`) es cabecera de columna/CSV:
   misma familia que `'Murio'`, `'Cuando'`, `'Duro'`, que la ficha deja a
   proposito.
3. Ningun test afirma el texto viejo: cubierto. Mutacion: "Sus números" ->
   "Sus numeros" (`Jugador.jsx`) y "No había partidas nuevas" sin tilde
   (`App.jsx`), `vite build`,
   `E2E_CHROMIUM=/opt/pw-browsers/chromium-1243/chrome-linux64/chrome npx playwright test -g "tu perfil enlaza|los POST de la UI mandan JSON"`:
   2 failed; restaurado: 2 passed. Ningun test busca "eliminacion" ni "se acabo".
4. Build y `check.sh`: cubierto. `verificar.sh`: VERDE a7b7f5cd9 (955 tests
   backend, 197 vitest, 62 e2e). Chunk inicial `index-*.js` 191687 bytes
   (sin cambio de tamano relevante: solo texto).

Veredicto: `con hallazgos`. Arreglo: las tres cadenas de arriba (solo tildes,
`'sí'` solo en el `render` de pantalla); repetir el barrido mirando tambien
los mapas de constantes (`CONDITIONS`) y los `render:` de columnas.

Choca con la 84 (que queda `aprobado` en este turno) en `ui.jsx`,
`MatchDetail.jsx`, `Jugador.jsx` y `humo.spec.js`: si la 84 entra a dev
antes, la correccion arranca con P3.

OMC: plan=— · revisión=— · verificación=FAIL (criterio 2 PARTIAL: `MatchDetail.jsx:360,363,161`)

### Correccion de hallazgos de la segunda QA (dev 20261105T1641Z-cY8pL9A, sobre dev 3d89622 mezclado en 687b479)

Rama ya al dia con dev 3d89622 (el merge P3 con la 84 lo hizo QA). Aplicado lo
que pidio la segunda QA, solo tildes:

- `MatchDetail.jsx`, mapa `CONDITIONS`: "eliminación del equipo rival", "se
  acabó el tiempo" (se pintan en "Condición: ..." del panel de la ronda).
- `MatchDetail.jsx`, `render` de pantalla de la columna `died`: `'sí'`. El CSV
  sigue en `'si'`/`'no'` (`celdaCsv` de `ui.jsx` no usa `render`; esa tabla
  ademas no tiene `csvName`).

Barrido de mapas de constantes y `render:` de columnas en todos los `.jsx`:
sin otras cadenas visibles sin tilde. La revision ciega encontro una mas,
aplicada: `Jugador.jsx`, chip de la columna "Jugo de" mostraba el valor crudo
del backend `companero`; ahora pinta "compañero" (el valor de la API, la clase
`win`/`loss` y el CSV no cambian).

Ningun test afirmaba el texto viejo (`grep` en `frontend/e2e` y
`frontend/src/*.test.js`: solo comentarios y nombres de test).

Revision ciega (`omc-code-reviewer`): aprobar, 1 LOW (el chip), arreglado.

`verificar.sh`: VERDE 7a17ba9e3 (960 tests backend, 199 vitest, 64 e2e).

Skills: no aplica (cambio de textos).
OMC: plan=— · revisión=1 hallazgo (1 arreglado) · verificación=—

## Revision 2026-11-05 sobre d668c93 (cuarta pasada)

(revisor 20261105T1706Z-czYXSXu; rama mezclada con dev e7cc919 en d668c93, que trae la 88, sin
conflictos.)

Revision a ciegas (`omc-code-reviewer`, eje de estandares; un solo tema, solo
cadenas): aprobar, 1 LOW. El delta desde la tercera pasada son 5711255 y
7a17ba9 (lo que pidio la segunda QA, mas el chip de "Jugo de").

Confirmado por el Revisor:

- `CONDITIONS` de `MatchDetail.jsx`: cambian solo los valores visibles; las
  claves `KilledOpponents` y `Time` siguen iguales.
- `render` de la columna `died`: `'sí'` solo en pantalla; el CSV sale de
  `celdaCsv` (`ui.jsx:90`), que sigue en `'si'`/`'no'`.
- Chip de `Jugador.jsx:217-218`: la comparacion y la clase siguen sobre el
  valor crudo `'companero'` que manda el backend; solo cambia el texto.
- `git grep -nE "eliminacion del equipo|se acabo el tiempo|'si' : 'no'" -- frontend/src`:
  solo `ui.jsx:90` (el CSV, a proposito).
- Ningun e2e ni vitest busca un texto viejo.

Hallazgo:

- [estilo] LOW `frontend/src/pages/Trends.jsx:321` (y `VENTANAS`, `:41-42`)
  Que pasa: el selector de ventana pinta "Últimas 7 días" / "Últimas 30 días"
  (concordancia de genero).
  Por que es cierto: `Últimas {v.label}` con `label: '7 días'`; en dev ya era
  "Ultimas 7 dias", la ficha solo le puso tildes.
  Arreglo sugerido: llevar el adjetivo al `label` ("últimos 7 días"). Cambia
  palabras, no tildes: "Fuera de alcance" lo deja para otra ficha. No bloquea.

Criterios: 1 cubierto; 2 cubierto (salvo las cabeceras de columna/CSV que la
ficha deja a proposito); 3 cubierto; 4 `verificar.sh`: VERDE d668c93c5 (963
tests backend, 199 vitest, 64 e2e).

Veredicto: aprobar -> `revisado` (cuarta pasada, solo un LOW previo y fuera de
alcance, que va a `## Para el humano`).

OMC: plan=— · revisión=1 hallazgo LOW (0 arreglados; el Revisor no arregla) · verificación=—

## Verificar en el PC

## Pendiente

## Para el humano

- 2026-11-05 (revisor 20261105T1455Z-caYiimg): LOW sin arreglar, no bloquean (el de `MatchDetail.jsx:309` ya quedo arreglado en la correccion de QA): cabeceras `'Jugo de'`, `'Metrica'` (junto a `'Cuando'`, `'Duro'`, `'Murio'`) quedan sin tilde porque son tambien cabecera del CSV: decidir en una ficha de cabeceras de CSV.
- 2026-11-05 (revisor 20261105T1706Z-czYXSXu): LOW fuera de alcance, no bloquea: el selector de ventana de Tendencias dice "Últimas 7 días" / "Últimas 30 días" (`Trends.jsx:321`, concordancia de genero, ya estaba en dev). Arreglarlo cambia palabras, no tildes: va en otra ficha si se quiere.
