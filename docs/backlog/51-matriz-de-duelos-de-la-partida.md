# 51. Matriz de duelos de la partida

estado: entregado
candado: -
rama: claude/equipo-dev/51-matriz-de-duelos-de-la-partida
tipo: funcionalidad
epica: revision-de-rondas
area: frontend
prioridad: 3
fuente: ALCANCE.md F7 ([CS Demo Manager v3.5.0](https://cs-demo-manager.com/changelog), "players duels matrix"; selector de aperturas de [vlr.gg](https://www.vlr.gg/188013/velaris-vs-clg-red-complexity-paradox-invitational-playoffs-lr3/?game=all&tab=performance))
archivos: frontend/src/matrizDuelos.js, frontend/src/matrizDuelos.test.js, frontend/src/components/MatrizDuelos.jsx, frontend/src/pages/MatchDetail.jsx, frontend/src/styles.css, frontend/e2e/humo.spec.js, docs/metricas.md
turnos: po 20261015T1711Z, arquitecto 20261015T1811Z, dev 20261015T2004Z, revisor 20261016T0004Z, dev 20261016T0404Z, revisor 20261016T0805Z, dev 20261016T2004Z, revisor 20261017T0004Z, qa 20261017T0404Z, release 20261017T0804Z

## PR

Titulo: `[equipo-dev][frontend] Matriz de duelos de la partida`

### Que cambia

El detalle de una partida suma el panel "Matriz de duelos": dos tablas de
quién mató a quién (tu equipo contra el rival y al revés), con headshots, y
un selector "Todas / Solo aperturas". De un vistazo se ve qué rival te pasó
por encima esa partida y a quién le ganaste todos los duelos. Todo se arma en
el navegador con lo que ya trae `/api/matches/<id>/`: sin backend nuevo.

### Por que esto y no otra cosa

Ficha 51, epica `revision-de-rondas` (ALCANCE.md F7, "players duels matrix"
de CS Demo Manager). Duelos agrega entre partidas; esto es una sola. El lado
de cada baja se decide ronda por ronda (tu fila, si no `teams[].mine`, si no
el equipo de la partida) porque el parser puede repartir un nick en otro
equipo entre rondas. "Solo aperturas" usa la misma apertura que la columna
Aperturas del scoreboard (primer `Kill` o `Death` de la ronda), para que los
dos números de la misma pantalla cuadren.

### Como se probo

- `./scripts/check.sh`: `Todo en verde.` (644 tests backend, 99 vitest, build ok, 39 e2e) sobre la rama con `origin/main` 06e3351 fusionado.
- `src/matrizDuelos.test.js` (9): matriz de dos rondas con HS; teamkills y bajas sin autor fuera; solo aperturas en orden del feed; ronda que abre con teamkill o con muerte sin asesino no suma; sin eventos da total 0; nick que cambia de equipo; ronda sin tu fila usa `teams[].mine` o el equipo de la partida. E2e `el detalle de una partida muestra la matriz de duelos`.
- QA con base sembrada (partida sin bajas, solo teamkill, 3 rondas con cambio de equipo y ronda sin tu fila): celdas contadas a mano, texto vacío correcto, 375 px sin scroll horizontal, consola limpia; mutaciones en `matrizDuelos.js` hacen caer los tests que corresponden.

### Riesgos y lo que no entra

Sin migración, `recompute`, parser ni Electron. Chunk inicial +0,02 %; el de
MatchDetail (lazy) pasa de 6,45 a 9,24 kB. Fuera: matriz entre partidas (es
Duelos), endpoint nuevo, flechas de ronda del PR #14.

### Como probarlo en 2 minutos

```
cd backend; python manage.py seed_demo; python manage.py runserver
```
Abrir `http://localhost:8000/partidas`, entrar a cualquier partida: entre
"Rondas" y "Scoreboard de la partida" aparece "Matriz de duelos" con las dos
tablas; "Solo aperturas" deja menos bajas.

### Para el humano

Nada que decidir. Avisos: el e2e no distingue "Todas" de "Solo aperturas"
(cabe en una ficha `tests`); una partida sin rondas (solo con datos armados a
mano) rompe el detalle en `MatchDetail.jsx:93`, código de main.

### Candidatos descubiertos

Ninguno.

## Que gana quien usa la app


En el detalle de una partida, una tabla 5x5 de quien mato a quien (filas tu
equipo, columnas el rival, y al reves), con los headshots: de un vistazo se
ve que rival te paso por encima esa partida y a quien le ganaste todos los
duelos. Duelos agrega entre partidas; esto es una sola, y no necesita
backend: `/api/matches/<id>/` ya trae el feed de cada ronda.

## Criterios de aceptacion

- [ ] Funcion pura en `frontend/src/` que recibe las rondas de
      `/api/matches/<id>/` y devuelve la matriz: por par (autor, victima)
      bajas y headshots, con el equipo de cada uno sacado de las filas de
      jugadores de la ronda (`team_index`); test vitest con una partida de 2
      rondas.
- [ ] Las bajas entre compañeros (teamkills) y las que no tienen autor no
      entran en la matriz (test).
- [ ] Selector "Todas / Solo aperturas": con aperturas, solo cuenta la
      primera baja de cada ronda (test).
- [ ] Una partida sin eventos de baja muestra un texto vacio, no una tabla
      de ceros ni un error.
- [ ] La tabla aparece en `MatchDetail.jsx` y el e2e (`frontend/e2e/`) la
      ve en una partida de `seed_demo` sin errores de consola.

## Fuera de alcance

- Matriz entre partidas (eso es Duelos).
- Endpoint nuevo o columnas nuevas: se arma en el navegador.
- Flechas de ronda y navegacion de PR #14: disenar sin pisar ese diff.

## Diseno

(Arquitecto 20261015T1811Z) Todo en el navegador: `matrizDuelos.js`
(`matrizDeDuelos(rondas, { soloAperturas, miEquipo })` y `celda`), componente
`MatrizDuelos.jsx`, un panel en `MatchDetail.jsx` entre "Rondas" y
"Scoreboard", `.matriz` al final de `styles.css`, e2e y fila en
`docs/metricas.md` (## Duelos). Detalle completo en `git log` de esta ficha.

## Implementacion

(Dev 20261015T2004Z, correcciones 20261016T0404Z y 20261016T2004Z) Quedo todo
el diseno. Desvio: el lado de cada baja se decide ronda por ronda y la matriz
guarda `aFavor` y `enContra` (un nick puede saltar de equipo entre rondas).

## Revision

(Revisor 20261016T0004Z, 20261016T0805Z, 20261017T0004Z) Veredicto final:
aprobar. Hallazgos corregidos: ronda sin tu fila usaba el equipo de la
partida en vez de `teams[].mine` (2d555ed); "Solo aperturas" no usaba la misma
apertura que el scoreboard (51f4d53); fixture de `Death` con la victima en el
campo equivocado. Menor abierto: el e2e no distingue los dos modos.

## QA

(QA 20261017T0404Z sobre f0d410b) `check.sh` en verde; base sembrada con
`factories.py`, `runserver` y Chromium sobre tres partidas armadas: los 5
criterios con evidencia, 375 px sin scroll, consola limpia, mutaciones caen.
Veredicto: aprobado.

## Para el humano

- (Revisor 20261017T0004Z) El e2e de la matriz no distingue "Todas" de "Solo
  aperturas"; no bloquea.
- (QA 20261017T0404Z) Informativo: una partida sin rondas rompe el detalle
  (`MatchDetail.jsx:93`, codigo de main, no de esta ficha).
