# 96. Filtros en la URL

estado: entregado
candado: -
rama: claude/equipo-dev/96-filtros-en-la-url
tipo: funcionalidad
epica: temporada-y-modo
area: frontend
prioridad: 3
fuente: A10 de ALCANCE.md; idea del PR #14 (cerrado sin merge el 2026-11-05; la rama `claude/dazzling-einstein-w3qcyq` sigue y trae `frontend/src/filtros.js` como referencia, no para copiar a ciegas)
archivos: frontend/src/filtrosUrl.js, frontend/src/filtrosUrl.test.js, frontend/src/App.jsx, frontend/src/components/Filters.jsx, frontend/e2e/filtros-url.spec.js, frontend/e2e/humo.spec.js
turnos: po 20261106T0041Z-cSxDY1g, arquitecto 20261106T0200Z-ct6rosE, dev 20261106T0228Z-cCNBxR6, revisor 20261106T0252Z-cPqrt5E, qa 20261106T0252Z-cf6G6Cs, release 20261106T0252Z-cf6G6Cs

## PR

Titulo: `[equipo-dev][frontend] Filtros en la URL`

### Que cambia

Los filtros globales (lado, mapa, operador, sitio, sesion, periodo, tipo) viajan en la query de la URL: recargar la pagina, el boton Atras y un marcador devuelven la misma vista filtrada, y una URL pegada con filtros abre la pagina con la barra puesta. Los enlaces del menu llevan los filtros; los valores que la barra no sabria mostrar (`days=abc`, fechas inexistentes, claves desconocidas) se descartan antes de llegar a la API.

### Por que esto y no otra cosa

Ficha 96 (A10 de `ALCANCE.md`, idea del PR #14 que el humano cerro y devolvio a idea). Sin `localStorage` ni backend: la URL es el unico lugar. Los filtros propios de Partidas y la ronda elegida quedan fuera (tramo aparte).

### Como se probo

- `check.sh` (con `verificar.sh`): VERDE db1ada553 (1022 tests backend, 245 vitest, 75 e2e) con la 95 mezclada; repetido sobre la entrega, con la 93 mezclada.
- Tests nuevos: `filtrosUrl.test.js` (13: ida y vuelta, vacias, desconocidas, `days` solo 7/30/90, fechas invalidas, `session=0`, `ranked_only` viejo, `side`, texto largo, orden fijo, rutas con barra); e2e `filtros-url.spec.js` (recargar conserva filtro y numeros sin entrada de historial, el menu lleva los filtros, URL directa llega a la API sin valores raros, volver del detalle, enlace interno sin query hereda, Limpiar deja la URL sin query). `humo.spec.js` busca el enlace del menu por prefijo.
- QA en Chromium con `seed_demo`: URLs con basura, fechas y `days` a la vez, `ranked_only=true`, pagina sin barra, menu, Atras desde el detalle, pestaña nueva con la misma vista; 3 mutaciones detectadas.
- OMC: plan=— (ficha chica, solo frontend, de una forma obvia) · revisión=— · verificación=— (diseno)
- OMC: plan=— · revisión=3 hallazgos (3 arreglados) · verificación=— (implementacion)
- OMC: plan=— · revisión=2 hallazgos LOW + 1 LOW de intencion (0 arreglados, no bloquean) · verificación=— (revision)
- OMC: plan=— · revisión=— · verificación=PASS (QA)

### Riesgos y lo que no entra

Solo frontend, sin migraciones. Reabrir la app de escritorio no conserva los filtros (Electron carga siempre la URL base); Ctrl+R si. LOW abiertos, sin bloqueo: `map`/`operator`/`site`/`session` inexistentes en la URL llegan a la API y la barra muestra "Todos" con 0 rondas; con dos entradas de historial de la misma ruta con periodos distintos, el modo "Entre dos fechas" puede desfasarse al editar; un año de 5 digitos escrito a mano en la fecha llega a la API pero no a la URL. Chunk inicial +1 %.

### Como probarlo en 2 minutos

```powershell
cd frontend; npm run build; cd ..\backend; python manage.py runserver
```
Abrir `http://127.0.0.1:8000/tendencias?side=Defense&days=30`: la barra muestra Solo defensa y Ultimos 30 dias. Elegir un mapa: la URL cambia; F5 deja la misma vista. Ir a otra pagina del menu: la URL lleva los filtros. `?days=abc` se borra solo de la URL.

### Para el humano

Nada.

### Candidatos descubiertos

Ninguno.

## Que gana quien usa la app

Hoy los filtros globales viven en un `useState` de `App.jsx`: recargar la
pagina (o reabrir la app de escritorio) los pierde, y una vista filtrada
("Ranked, Oregon, ultimos 30 dias, en defensa") no se puede guardar como
marcador ni volver a ella con el boton Atras. Con esto los filtros viajan en
la query de la URL y sobreviven a todo eso.

## Criterios de aceptacion

- [x] Una funcion pura (p. ej. `frontend/src/filtrosUrl.js`) convierte
      filtros en query y query en filtros, ida y vuelta sin perdida, con
      tests de vitest: claves vacias no se escriben, claves desconocidas de la
      URL se ignoran, y valores raros (`days=abc`) se descartan en vez de
      llegar a la API.
- [x] Elegir un filtro en cualquier pagina con barra de filtros actualiza la
      query de la URL (`replace`, no una entrada de historial por cada
      cambio de select); recargar la pagina deja los mismos filtros elegidos
      y los mismos numeros.
- [x] Cambiar de pagina desde el menu conserva los filtros (como hoy) y la
      URL de destino los lleva en su query.
- [x] Abrir directo una URL con filtros (por ejemplo
      `/tendencias?side=Defense&days=30`) muestra la barra con esos valores y
      la API recibe esos parametros.
- [x] El e2e elige un filtro, recarga la pagina y comprueba que el select
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

(arquitecto 20261106T0200Z-ct6rosE) Solo frontend. El estado `filters` de `App.jsx` se queda y se sincroniza con la query: manda la URL en navegacion del navegador (carga, recarga, Atras, URL pegada) o si trae filtros; manda el estado en un Link interno sin query. `filtrosUrl.js` puro valida por clave; `replace` siempre; `mismosFiltros` corta el bucle; `NavLink` con la query; `Filters.jsx` deriva el modo rango del valor. Detalle en `git log`.

OMC: plan=— (ficha chica, solo frontend, de una forma obvia) · revisión=— · verificación=—

## Implementacion

(dev 20261106T0228Z-cCNBxR6) Todo el diseno. Desvios: `days` solo 7/30/90 (MEDIUM de la revision ciega); una query sin ningun filtro valido se reescribe sin query; `session` fuera de rango pasa (posicional, no validable sin la lista); e2e espera `networkidle` antes de recargar. `humo.spec.js`: selector del menu por prefijo. Revision ciega: 3 hallazgos, 3 arreglados.

OMC: plan=— · revisión=3 hallazgos (3 arreglados) · verificación=—

## Revision 2026-11-06 sobre a60d84b

(revisor 20261106T0252Z-cPqrt5E) Aprobar, dos ejes a ciegas. LOW sin bloqueo: `abierto` de `Filters.jsx` puede desfasarse con Atras entre dos entradas de la misma ruta con periodos distintos; `cambiarFiltros` guarda el valor sin validar (año de 5 digitos llega a la API y no a la URL); "Que gana" promete sobrevivir a reabrir Electron y no pasa (el PR lo aclara).

OMC: plan=— · revisión=2 hallazgos LOW + 1 LOW de intencion (0 arreglados, no bloquean) · verificación=—

## QA 2026-11-06 sobre db1ada5

(qa 20261106T0252Z-cf6G6Cs; rama con dev 8ebdeca (la 95) mezclado, sin conflictos)

- **check.sh completo**: `verificar.sh` -> `VERDE db1ada553 en 103s: 1022 tests
  backend, 245 vitest, 75 e2e. Todo en verde.`
- **App real**: `SQLITE_PATH=<scratchpad>/qa96.sqlite3`, `migrate`, `seed_demo`
  (29 partidas), `runserver 127.0.0.1:8796 --noreload`, Chromium (playwright)
  anotando cada request a `/api/`. Consola limpia y ningun 500 en todos los casos:
  - `/tendencias?side=Defense&days=30`: URL igual, barra Lado=Defense y
    Periodo=30; API `/api/trends/?side=Defense&days=30`, `/api/sessions/?side=Defense&days=30`.
  - `/tendencias?days=abc&x=1&since=2026-02-31&side=foo&session=-1`: URL
    `/tendencias`, barra vacia, API sin parametros.
  - `/?days=45`: URL `/`, sin `days`. `/coach?since=2026-01-01&until=2026-12-31&days=7`:
    `days` quitado, Periodo "rango" con las dos fechas, API con `since`/`until`.
  - `/operadores?ranked_only=true&session=0`: URL `?session=0&ranked_only=1`,
    Tipo=Ranked, la API recibe los dos.
  - `map` de 65 caracteres: descartado. `/ajustes?side=Defense`: la query no
    se toca y solo pide `/api/settings/`.
  - Con `?side=Attack`, los 7 enlaces del menu con barra llevan la query
    (Ruleta, Datos y Ajustes no); clic en Duelos -> `/duelos?side=Attack`;
    elegir Defensa -> `/duelos?side=Defense` sin entrada de historial nueva
    (`history.length` 11 -> 11).
  - Elegir Bank en el Resumen -> `/?map=bank`; esa URL en otra pestaña: select
    `bank` y el mismo texto de la pagina.
  - `/partidas?side=Defense` -> detalle -> Atras vuelve a `/partidas?side=Defense`.
- **Mutaciones** en `filtrosUrl.js` (restauradas), `npx vitest run
  src/filtrosUrl.test.js`: `days` sin validar contra 7/30/90 -> 1 falla; fechas
  sin borrar `days` -> 1 falla; `2026-02-31` aceptada -> 1 falla.
- **Bundle**: chunk inicial ~192,6 kB (dev con la 95) -> 194,55 kB (+1 %).
- Sin migraciones, `recompute`, parser, Electron ni `.ps1`.

Hallazgo LOW, no bloquea (por diseno: `map`, `operator` y `site` son texto de
hasta 64): `/?map=noexiste` llega a la API, la pagina dice "0 rondas con estos
filtros" y el select de Mapa muestra "Todos". Mismo caso que `session=99999`,
anotado por el Dev. Validarlo contra las opciones cargadas seria un tramo aparte.

Veredicto: los cinco criterios con evidencia -> `aprobado`.

OMC: plan=— · revisión=— · verificación=PASS

## Para el humano

(Nada por ahora.)
