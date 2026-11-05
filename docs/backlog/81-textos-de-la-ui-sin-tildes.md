# 81. Textos de la UI sin tildes en Inicio, Tendencias y otras pantallas

estado: disenado
candado: -
rama: -
tipo: bug
epica: -
area: frontend
prioridad: 4
fuente: QA 20261105T0256Z-cYSSB7z, deriva de docs sobre dev 2da1b7d. `CLAUDE.md` (Estilo): "Los textos que ve el usuario en la UI si llevan tildes y ñ". Varios titulos y hints de `Panel` no las llevan
archivos: frontend/src/App.jsx, frontend/src/components/Filters.jsx, frontend/src/components/ui.jsx, frontend/src/pages/Coach.jsx, frontend/src/pages/Dashboard.jsx, frontend/src/pages/Datos.jsx, frontend/src/pages/Duelos.jsx, frontend/src/pages/Jugador.jsx, frontend/src/pages/MatchDetail.jsx, frontend/src/pages/Matches.jsx, frontend/src/pages/Operators.jsx, frontend/src/pages/Teammates.jsx, frontend/src/pages/Trends.jsx, frontend/e2e/humo.spec.js
turnos: qa 20261105T0256Z-cYSSB7z, arquitecto 20261105T1303Z-cfek47z

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

## Revision

## QA

## Verificar en el PC

## Pendiente

## Para el humano
