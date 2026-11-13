# 111. Copiar las señales del Coach como texto

estado: disenado
candado: -
rama: -
tipo: funcionalidad
epica: exportar
area: frontend
prioridad: 3
fuente: ALCANCE.md H6
archivos: frontend/src/textoCoach.js (nuevo), frontend/src/textoCoach.test.js (nuevo), frontend/src/pages/Coach.jsx (GROUPS y format se mudan; boton Copiar señales), frontend/e2e/humo.spec.js
turnos: po 20261112T1128Z-cKKCvKD, arquitecto 20261113T0003Z-cVnayJ8

## PR

## Que gana quien usa la app

Un boton en Coach copia al portapapeles las señales que se ven (titulo,
numero, muestra y consejo) en texto plano, con los filtros activos en la
primera linea, para pegarlas en el chat del equipo o mandarselas a quien te
entrena. Nada sale de la PC: es el portapapeles, como "Copiar resumen" de la
partida y de la sesion.

## Criterios de aceptacion

- [ ] Funcion pura nueva (p. ej. `frontend/src/textoCoach.js`) que arma el
      texto desde la respuesta de `/api/coach/` y los filtros: primera
      linea con los filtros activos (o "Sin filtros"), una linea o bloque por
      señal en el orden que se muestran, sin HTML. Vitest con dos señales,
      con y sin filtros.
- [ ] Sin señales, el boton no aparece (o queda deshabilitado con la razon
      en `title`). Vitest de la funcion con lista vacia.
- [ ] Sin `navigator.clipboard` (http que no es localhost) el boton avisa
      que no se pudo copiar en vez de romper, igual que el de la partida.
- [ ] e2e: en `/coach` con el seed, el boton copia y el texto copiado
      (leido con `page.evaluate` sobre `navigator.clipboard.readText` con
      el permiso de Chromium, como el e2e que ya prueba "Copiar resumen", o
      espiando `writeText`) contiene el titulo de una señal del seed;
      consola limpia.

## Fuera de alcance

- Exportar a archivo o imagen.
- Copiar las señales del Inicio (el mismo texto puede reusarse despues).
- Backend: `build_insights` ya devuelve todo.

## Diseno

(arquitecto 20261113T0003Z-cVnayJ8) Filtros duros: pasa. Solo frontend, sobre lo que
`/api/coach/` ya devuelve; el portapapeles es local (sin red, sin
dependencias, sin POST, sin migracion). Una forma obvia y chica (~150
lineas), con el patron de "Copiar resumen" de la partida (`MatchDetail.jsx`
`copiarResumen`) y de la sesion (`Trends.jsx` `copiarSesion`): sin arena ni
consenso.

**`frontend/src/textoCoach.js`** (logica pura, nuevo):

- `export const GRUPOS_COACH`: mover aca el arreglo `GROUPS` de `Coach.jsx`
  (clave, titulo, hint) y que `Coach.jsx` lo importe: el texto sale en el
  mismo orden que la pagina sin una segunda lista que se desalinee.
- `export function formatoCoach(value)`: mover aca `format` de `Coach.jsx`
  (misma regla: `—` para nulo, 2 decimales debajo de 10 si no es entero) y que
  la pagina lo importe: el numero copiado es el que se ve.
- `export function lineaDeFiltros(filtros)`: `"Sin filtros"` si
  `hayFiltros(filtros)` (de `tipoPartida.js`) es falso; si no, `"Filtros: "` y
  las partes no vacias unidas por `" · "`, en el orden de `CLAVES_DE_URL`
  (`filtrosUrl.js`): `side` -> `Solo ataque` / `Solo defensa`; `map` ->
  `Mapa: <valor>`; `operator` -> `Operador: <valor>`; `site` ->
  `Sitio: <valor>`; `session` -> `Sesión <valor + 1>`; `days` ->
  `Últimos <n> días`; `since` -> `Desde <valor>`; `until` -> `Hasta <valor>`;
  `match_type` -> `Tipo: <valor>`; `gamemode` -> `Modo: <nombreDeModo(valor)>`
  (`modoDeJuego.js`); `ranked_only` -> `Solo ranked`. El mapa va con el valor
  del filtro tal cual (la barra no expone el nombre fuera de su select): el
  slug se entiende y no hace falta otra request.
- `export function textoCoach(insights, filtros)`: `null` si no hay
  `insights` (lista vacia o indefinida). Si no, lineas:
  1. `Coach · <lineaDeFiltros>`;
  2. por cada grupo de `GRUPOS_COACH` con señales (mismo filtro por
     `severity` que la pagina), una linea en blanco, el titulo del grupo en
     mayusculas (`PRIORIDAD ALTA`) y por señal:
     `- <title>` / `  <detail>` / `  Qué hacer: <action>` / y, si hay algo,
     `  <metric>: <formatoCoach(value)>[ (referencia <formatoCoach(baseline)>)] · muestra: <sample> rondas · alcance: <scope>`
     con las mismas condiciones que `.meta` de la pagina (sin `metric` no va
     esa parte; sin `sample` tampoco; `scope` solo si no es `general`).
  Sin HTML; salto `\n`; sin espacio al final de linea.
- `frontend/src/textoCoach.test.js` (vitest):
  `sin señales no hay texto` (`[]` e `undefined` -> `null`);
  `sin filtros la primera linea lo dice`; `con filtros los nombra en orden`
  (lado, mapa, dias y ranked -> `Filtros: Solo defensa · Mapa: bank · Últimos 30 días · Solo ranked`);
  `dos señales salen en el orden de los grupos` (una `positivo` antes en el
  array y una `alta`: sale primero la alta); `la referencia y la muestra van
  solo si existen`; `el numero se formatea como en la pagina` (0.456 -> `0.46`, 55 -> `55`).

**`frontend/src/pages/Coach.jsx`**:

- Importar `GRUPOS_COACH`, `formatoCoach` y `textoCoach`; borrar `GROUPS` y
  `format` locales (los usos pasan a los importados).
- `const [copia, setCopia] = useState(null)` (importar `useState`), **antes**
  de los returns tempranos. `copiarSenales` igual a `copiarResumen`: sin
  `navigator.clipboard?.writeText` -> `setCopia('error')`; `try` / `catch`
  sin `console`.
- En el `page-head`, a la derecha del titulo (como en la partida), solo si
  `textoCoach(insights, filters)` no es `null`: el aviso `<span className="note">`
  (`Copiado` / `No se pudo copiar: el navegador no dio acceso al
  portapapeles.`, el texto de la partida) y
  `<button type="button" className="btn small" onClick={copiarSenales}>Copiar señales</button>`
  con `title="Copia las señales que ves, con los filtros, en texto plano."`.
  (Identificador sin tilde; el texto del boton, con tilde.)
- Sin señales el boton no aparece (criterio 2, variante "no aparece").

**e2e, `frontend/e2e/humo.spec.js`**, test `el Coach copia sus señales`
junto a `el Coach muestra si repites el sitio tras perderlo`:
`grantPermissions(['clipboard-read', 'clipboard-write'])` como
`Tendencias copia el resumen de una sesion`; leer `/api/coach/` y tomar
`insights[0].title`; `page.goto('/coach')`; clic en `Copiar señales`;
`Copiado` visible; `navigator.clipboard.readText()` empieza con
`Coach · Sin filtros` y contiene `- <title>`; despues
`page.goto('/coach?side=Defense')` (filtros en la URL, ficha 96), copiar otra
vez y el texto empieza con `Coach · Filtros: Solo defensa`. Consola limpia.
El criterio 3 (sin portapapeles) lo cubre el mismo camino que la partida y
su rama no se puede forzar en Chromium sin quitar `navigator.clipboard`:
el e2e no lo prueba, como no lo prueba el de la partida; la logica de la
rama es una linea.

**`docs/metricas.md`**: no hay numero nuevo (copia los de las señales, que ya
tienen definicion). Nada que agregar.

**Orden.** `textoCoach.js` + vitest (mover `GROUPS` y `format`), `Coach.jsx`,
e2e, `npm run build`.

**Que puede romperse.** Mover `GROUPS`/`format` cambia imports de
`Coach.jsx`; el e2e del Coach existente cubre que la pagina siga igual. El
`useState` nuevo tiene que ir antes de `if (error) return`, o React rompe el
orden de hooks al pasar de cargando a datos.

**Archivos ocupados.** La 113 (`revisado`) toca `Operators.jsx`,
`aggregates.py`, `views.py`, `urls.py` y `humo.spec.js` (otro test); la 112
(`implementado`) toca `MatchDetail.jsx`, `ui.jsx`, `records.js`,
`navegacionRondas.js` y `humo.spec.js` (otro test). Ninguna toca `Coach.jsx`
ni `textoCoach.js`; `humo.spec.js` es un test nuevo en otro lugar: merge
trivial. No se frena.

**Verificacion manual.** `seed_demo`, `/coach`, `Copiar señales`, pegar en un
editor: primera linea `Coach · Sin filtros`, grupos en el orden de la pagina;
con `Solo defensa` en la barra la primera linea lo dice.

Skills: no aplica (copiar al portapapeles ya resuelto dos veces en el repo).
Skills del repo: testing-strategy (vitest para el texto, e2e para el boton y el portapapeles; sin test de Django: no toca el backend).
OMC: plan=— · revisión=— · verificación=—

## Implementacion

## Revision

## QA

## Para el humano

(nada)
