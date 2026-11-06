# 96. Filtros en la URL

estado: disenado
candado: -
rama: -
tipo: funcionalidad
epica: temporada-y-modo
area: frontend
prioridad: 3
fuente: A10 de ALCANCE.md; idea del PR #14 (cerrado sin merge el 2026-11-05; la rama `claude/dazzling-einstein-w3qcyq` sigue y trae `frontend/src/filtros.js` como referencia, no para copiar a ciegas)
archivos: frontend/src/filtrosUrl.js, frontend/src/filtrosUrl.test.js, frontend/src/App.jsx, frontend/src/components/Filters.jsx, frontend/e2e/filtros-url.spec.js
turnos: po 20261106T0041Z-cSxDY1g, arquitecto 20261106T0200Z-ct6rosE

## PR

(La escribe el Release manager al final.)

## Que gana quien usa la app

Hoy los filtros globales viven en un `useState` de `App.jsx`: recargar la
pagina (o reabrir la app de escritorio) los pierde, y una vista filtrada
("Ranked, Oregon, ultimos 30 dias, en defensa") no se puede guardar como
marcador ni volver a ella con el boton Atras. Con esto los filtros viajan en
la query de la URL y sobreviven a todo eso.

## Criterios de aceptacion

- [ ] Una funcion pura (p. ej. `frontend/src/filtrosUrl.js`) convierte
      filtros en query y query en filtros, ida y vuelta sin perdida, con
      tests de vitest: claves vacias no se escriben, claves desconocidas de la
      URL se ignoran, y valores raros (`days=abc`) se descartan en vez de
      llegar a la API.
- [ ] Elegir un filtro en cualquier pagina con barra de filtros actualiza la
      query de la URL (`replace`, no una entrada de historial por cada
      cambio de select); recargar la pagina deja los mismos filtros elegidos
      y los mismos numeros.
- [ ] Cambiar de pagina desde el menu conserva los filtros (como hoy) y la
      URL de destino los lleva en su query.
- [ ] Abrir directo una URL con filtros (por ejemplo
      `/tendencias?side=Defense&days=30`) muestra la barra con esos valores y
      la API recibe esos parametros.
- [ ] El e2e elige un filtro, recarga la pagina y comprueba que el select
      sigue con el valor y que un numero visible coincide con el de antes de
      recargar, sin errores en la consola.

## Fuera de alcance

- Filtros propios de una pagina (los de Partidas de la ficha 78, la pestaña
  elegida, la ronda seleccionada del detalle): solo los filtros globales de
  `Filters.jsx`. Si el diseno ve que los de Partidas salen gratis, se
  anota como siguiente tramo, no se mete aca.
- Guardar vistas con nombre, o cualquier persistencia en el backend o en
  `localStorage`: la URL es el unico lugar.
- Cambios a la API: ya entiende todos esos parametros.

## Diseno

(Arquitecto 20261106T0200Z-ct6rosE, sobre `origin/dev@8f3fb74`.)

Solo frontend, sin API, sin dependencias, sin `localStorage`. El estado
`filters` de `App.jsx` se queda (las paginas siguen recibiendo
`filters`/`setFilters` igual que hoy, ninguna pagina cambia), pero se
sincroniza con la query de la URL en los dos sentidos. La URL manda cuando la
navegacion es del navegador (carga, recarga, Atras/Adelante, URL pegada); el
estado manda cuando la navegacion es interna y llega sin query (un `<Link>`
cualquiera, como "Ver en Duelos" o volver del detalle de una partida), que es
lo que hoy hace que los filtros "se mantengan al cambiar de pagina".

### Archivos y por que esos

1. **`frontend/src/filtrosUrl.js` (nuevo)**, logica pura, sin React, para
   probarla en node como `partidas.js` y `tipoPartida.js`. Exporta:
   - `CLAVES_DE_URL = ['side', 'map', 'operator', 'site', 'session', 'days', 'since', 'until', 'match_type', 'ranked_only']`:
     las de `_filters` de `backend/replays/views.py`, en orden fijo (asi la
     query es canonica y dos filtros iguales dan el mismo texto).
   - `RUTAS_CON_FILTROS = ['/', '/coach', '/operadores', '/companeros', '/duelos', '/tendencias', '/partidas']`
     y `usaFiltros(pathname)`: coincidencia exacta (con o sin `/` final), asi
     `/partidas/12`, `/jugadores/3`, `/ruleta`, `/datos` y `/ajustes` no
     tocan ni leen la query.
   - `filtrosDeUrl(search)`: acepta `'?a=b'`, `'a=b'` o `URLSearchParams`;
     devuelve solo claves conocidas con valor valido. Reglas (cada una con su
     test):
     - `side`: solo `Attack` o `Defense`.
     - `days`: entero positivo de hasta 4 digitos (`/^[1-9]\d{0,3}$/`); `abc`,
       `-3`, `0` o `99999` se descartan (el backend ya los ignora, pero el
       select mostraria "Todo el historial" filtrando otra cosa).
     - `since`/`until`: `AAAA-MM-DD` que `Date` entiende y que redondea a la
       misma fecha (`2026-02-31` se descarta). Si queda alguno de los dos,
       `days` se descarta: es lo que hace `elegirPeriodo` de `Filters.jsx`, y
       el backend ignora `days` cuando hay `since`.
     - `session`: entero >= 0 (`/^\d{1,5}$/`); `"0"` es valido y no se pierde.
     - `ranked_only`: `1` o `true` -> `true`; otro valor se descarta. Se lee
       para que un enlace viejo muestre Ranked (`tipoElegido` ya lo espera),
       y se escribe como `1`.
     - `map`, `operator`, `site`, `match_type`: texto recortado, no vacio, de
       hasta 64 caracteres. El mapa puede ser slug (`bank`) o `map_id`
       (`"7"`), los dos van tal cual (`mapas.js`).
   - `queryDeFiltros(filtros)`: texto sin `?`, solo claves de
     `CLAVES_DE_URL` en ese orden, sin `''`, `null`, `undefined` ni `false`;
     `true` -> `'1'`. Pasa el valor por la misma validacion (un `setFilters`
     con `days: 'abc'` no lo escribe).
   - `conFiltros(pathname, filtros)`: `{ pathname, search }` para el `to` de
     un `NavLink`/`navigate`; `search` es `''` sin filtros, o `?` + query.
   - `mismosFiltros(a, b)`: `queryDeFiltros(a) === queryDeFiltros(b)`. Es la
     comparacion que corta los bucles de sincronizacion.
   No reusar `qs()` de `api.js` para escribir: `qs()` manda cualquier clave
   (tambien `limit`, `min_rounds`) y no valida; `filtrosUrl.js` no
   necesita importar nada de `api.js`.

2. **`frontend/src/App.jsx`**: tres cambios, unas 35 lineas.
   - `useLocation`, `useNavigate` y `useNavigationType` de
     `react-router-dom` (ya es dependencia, 6.30.0).
   - Estado inicial perezoso:
     `useState(() => (usaFiltros(location.pathname) ? filtrosDeUrl(location.search) : {}))`.
     Que el primer render ya tenga los filtros de la URL importa: `Filters`
     calcula `rangoAbierto` al montarse y las paginas piden a la API en el
     primer render; leerlos en un efecto haria una request de mas sin filtros.
   - `cambiarFiltros(nuevos)` reemplaza a `setFilters` en `context`:
     `setFilters(nuevos)` y, si `usaFiltros(location.pathname)`,
     `navigate(conFiltros(location.pathname, nuevos), { replace: true })`.
     `replace` siempre: un select no deja una entrada de historial por cambio.
     `Matches.jsx` sigue llamando a `setFilters({})` desde su "Limpiar"
     (`cambiarFiltros` local) y funciona igual porque recibe el nuevo.
   - Un `useEffect` sobre `[location.pathname, location.search, navigationType]`:
     si `!usaFiltros(pathname)`, nada. Si no, `desdeUrl = filtrosDeUrl(search)`:
     - si `navigationType === 'POP'` o `queryDeFiltros(desdeUrl) !== ''`: la
       URL manda; `if (!mismosFiltros(desdeUrl, filters)) setFilters(desdeUrl)`.
       Ademas, si la query que trae la URL no es la canonica (claves
       desconocidas o valores raros, `?days=abc&x=1`), se reescribe con
       `navigate(conFiltros(pathname, desdeUrl), { replace: true })` para que
       la barra de direcciones no diga algo que la pagina no hace.
     - si no (PUSH/REPLACE interno y sin query) y `queryDeFiltros(filters) !== ''`:
       el estado manda; `navigate(conFiltros(pathname, filters), { replace: true })`.
     `filters` va leido por ref (`useRef` actualizado en cada render) o en
     las dependencias con la guarda `mismosFiltros`; cualquiera de las dos,
     pero sin bucle: el test e2e de consola lo veria como "Maximum update depth".
   - Los `NavLink` del menu: `to={conFiltros(link.to, filters)}` solo para
     las rutas de `RUTAS_CON_FILTROS` (Ruleta, Datos y Ajustes van sin
     query, como hoy). `end` y el resaltado de la activa siguen andando:
     `NavLink` compara solo el pathname.

3. **`frontend/src/components/Filters.jsx`**: una linea. Hoy `rangoAbierto`
   se calcula una sola vez al montar; con Atras/Adelante el `value` puede
   traer `since`/`until` sin que la barra se vuelva a montar. Usar
   `const abierto = rangoAbierto || Boolean(value.since || value.until)` en
   el `<select>` de Periodo y en el `{rangoAbierto ? ...}` de las fechas.
   Actualizar el docstring ("El estado vive en App y en la URL...") y el de
   `tipoElegido` en `tipoPartida.js` no hace falta tocarlo (ya habla de A10).

4. **`frontend/src/filtrosUrl.test.js` (nuevo)**, vitest en node:
   - `ida y vuelta sin perdida`: `filtrosDeUrl(queryDeFiltros(f))` da
     `f` para un `f` con las 10 claves (con `since`/`until` y sin `days`).
   - `las claves vacias y false no se escriben` (`{ map: '', ranked_only: false, side: 'Attack' }` -> `side=Attack`).
   - `las claves desconocidas de la url se ignoran` (`?limit=5&foo=1&map=bank`).
   - `days invalido se descarta` (`abc`, `0`, `-3`, `99999`, `1.5`).
   - `una fecha invalida se descarta y una valida saca a days` (`2026-02-31`, `ayer`; `?days=30&since=2026-01-01`).
   - `session cero es un filtro valido`.
   - `ranked_only de un enlace viejo se lee como true` y `tipoElegido` da `Ranked`.
   - `side solo acepta attack o defense`.
   - `el orden de la query es fijo` (`mismosFiltros` de dos objetos con las claves en otro orden).
   - `usaFiltros distingue partidas de su detalle` (`/partidas` y `/partidas/` si, `/partidas/12` no, `/ruleta` no).
   - `conFiltros sin filtros no deja un signo de pregunta suelto`.
   (Nombres en espanol, en `it(...)`, como el resto de `*.test.js`.)

5. **`frontend/e2e/filtros-url.spec.js` (nuevo)**, con `vigilarConsola`
   como los demas specs:
   - **recargar conserva el filtro**: `goto('/')`, leer el subtitulo
     (`.page-head p`, "N partidas · M rondas analizadas") sin filtros; elegir
     Lado = "Solo defensa"; esperar que el subtitulo cambie y que la URL
     tenga `side=Defense`; guardar el texto; `page.reload()`; el select de
     Lado tiene `Defense` y el subtitulo es el mismo texto guardado.
   - **el menu lleva los filtros**: con el filtro puesto, clic en "Tendencias"
     del menu; la URL es `/tendencias?side=Defense` y el select sigue en
     `Defense`.
   - **una url directa llega a la api**: `page.waitForRequest` sobre
     `/api/trends/` mientras `goto('/tendencias?side=Defense&days=abc&foo=1')`;
     la request lleva `side=Defense` y no lleva `days` ni `foo`; el select de
     Lado muestra `Defense`, el de Periodo "Todo el historial", y la URL
     queda reescrita sin `days` ni `foo`.
   - **volver del detalle no pierde los filtros**: en `/partidas` elegir un
     mapa del seed, entrar a la primera partida, clic en "Partidas" del menu:
     la URL trae `map=` y el select tiene el mapa.
   - **Limpiar deja la url sin query**.
   - La consola sin errores en todos (`expect(errores).toEqual([])`).
   No afirma numeros exactos del seed (compara antes y despues de recargar),
   asi no depende de `seed_demo`.

### Orden de implementacion

1. `filtrosUrl.js` + `filtrosUrl.test.js` (`npm test` en verde).
2. `App.jsx` (estado inicial, `cambiarFiltros`, efecto, `NavLink`).
3. `Filters.jsx` (`abierto`).
4. `npm run build` y el spec e2e; despues `check.sh` completo.

### Que puede romperse

- **Bucle de navegacion**: efecto que navega -> cambia `location` -> efecto.
  La guarda es `mismosFiltros` y que solo se navega con `replace` cuando la
  query canonica difiere de la actual. Si la consola dice "Maximum update
  depth" o "Throttling navigation", es esto.
- **StrictMode** (`main.jsx`) corre los efectos dos veces en dev: el efecto
  tiene que ser idempotente (lo es si solo navega cuando difiere).
- **Partidas**: `Matches.jsx` usa `resultado` local y pagina con
  `claveDeFiltros(filters, ...)`: no cambia. Lado y operador puestos desde
  otra pagina siguen viajando en la URL de `/partidas` aunque esa barra no
  los muestre (hoy tambien estan en el estado); no se mandan a la API
  (`filtrosDePartida`). Es lo esperado: volver al Resumen los conserva.
- **Ventana de "Entre dos fechas" vacia**: elegir "Entre dos fechas..." sin
  escribir fechas deja la URL sin `days` ni fechas; al recargar ahi, el
  select vuelve a "Todo el historial". Es correcto (no hay filtro).
- **`session` es posicional** (`_sessions_raw` en `aggregates.py`): un
  marcador con `session=2` puede apuntar a otra sesion despues de importar
  partidas nuevas. Se acepta: la barra muestra cual es. Anotado aca, no
  bloquea.
- **App de escritorio**: recargar (Ctrl+R) conserva los filtros; *reabrir*
  la app no, porque `electron/main.cjs` carga siempre `APP_URL`. Recordar la
  ultima URL al reabrir es persistencia fuera de la URL y queda fuera de
  esta ficha (no se toca Electron).
- **Archivos ocupados**: ninguna rama abierta toca `App.jsx`,
  `Filters.jsx` ni `filtrosUrl*`. La 79 toca `MatchDetail.jsx` y la 93
  `humo.spec.js`; este diseno no toca ninguno de los dos. Se implementa en
  cualquier orden.

### Verificacion manual

`npm run dev` (o el build en `runserver`): elegir Lado y Mapa en el Resumen,
ver la query en la barra de direcciones, recargar, pasar a Coach y Duelos
por el menu, entrar a una partida y volver por el menu, usar Atras despues
de cambiar de pagina, pegar `/tendencias?side=Defense&days=30` en otra
pestaña y ver la barra con esos valores.

### Siguiente tramo posible (no es esta ficha)

El `resultado` de Partidas (ficha 78) en la URL no sale gratis: es estado
local de `Matches.jsx` y hoy "Limpiar" lo borra a mano. Si se quiere, es un
tramo aparte de la epica `temporada-y-modo` que reusa `filtrosUrl.js` con
una clave `result` solo en `/partidas`. Lo mismo un enlace desde las Señales
del Coach a "esas rondas" (F15 de `ALCANCE.md`), que con esto pasa a ser
un `<Link to={conFiltros('/', {...})}>`.

### Metricas

Ningun numero nuevo: no hay fila de `docs/metricas.md`.

Skills: no aplica (react-router y vitest de logica pura ya estan resueltos en el repo; ningun dominio nuevo).
Arena: no (una sola forma razonable: estado en App sincronizado con la query).
OMC: plan=— (ficha chica, solo frontend, de una forma obvia) · revisión=— · verificación=—

## Implementacion

## Para el humano

(Nada por ahora.)
