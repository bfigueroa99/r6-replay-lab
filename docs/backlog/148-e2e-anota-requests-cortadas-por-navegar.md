# 148. El e2e anota como error las requests que corta una navegacion

estado: propuesto
candado: -
rama: -
tipo: bug
epica: -
area: tests
prioridad: 2
fuente: QA 138 (20261121T0136Z-s7f07u7), y la implementacion de la 138 (dev 20261115T0219Z-i32143169)
archivos: frontend/e2e/consola.js, frontend/e2e/humo.spec.js, frontend/e2e/accesibilidad.spec.js
turnos: qa 20261121T0136Z-s7f07u7

## PR

## Que gana quien usa la app

Trabajo interno: `check.sh` deja de salir rojo por un e2e que no fallo. Con
el contenedor cargado, un test que hace `page.goto` mientras la pagina
anterior todavia espera sus `/api/...` corta esas requests, y
`vigilarConsola` (`frontend/e2e/consola.js`, evento `requestfailed`) las
anota como `request fallida: ... (net::ERR_ABORTED)`: la puerta cae, se
repite entera (unos 7 minutos) y un rojo de verdad se confunde con este.

## Repro

- QA 138, `verificar.sh` sobre 143ec6a5e (2026-11-21, 3 de 3 cupos del
  contenedor ocupados): `humo.spec.js:181` "Operadores muestra si repites o
  cambias de operador" cae en `expect(errores).toEqual([])` con
  `request fallida: http://127.0.0.1:21299/api/filters/ (net::ERR_ABORTED)` y
  `.../api/operators/pool/?side=Defense (net::ERR_ABORTED)`; el test navega
  tres veces seguidas (`/operadores`, `?side=Defense`, `?operator=Ash`). 122
  e2e pasaron; la corrida siguiente sobre el mismo commit salio verde.
- Dev 138 (2026-11-15, sobre 390993bd9): `accesibilidad.spec.js` "ninguna
  tabla deja una columna sin nombre" cayo por una request abortada de
  `/api/trends/?limit=25` en `/tendencias`; al repetir, verde.

## Criterios de aceptacion

- [ ] Una request a `/api/` o `/assets/` cortada por una navegacion de la
      propia prueba (`net::ERR_ABORTED` con la pagina ya navegando a otra
      URL) no cuenta como error; cualquier otra falla de request sigue
      contando. Test del criterio (p. ej. un e2e que navega con una request
      demorada por `page.route` y otro que la aborta sin navegar).
- [ ] Un 404 o un 500 de `/api/` sigue haciendo caer el test que lo ve.
- [ ] `check.sh` en verde.

## Fuera de alcance

- Reintentos de Playwright (la config los prohibe a proposito).
- Cambiar los numeros que afirma algun test.

## Para el humano
