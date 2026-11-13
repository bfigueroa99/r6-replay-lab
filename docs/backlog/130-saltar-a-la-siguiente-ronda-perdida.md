# 130. Saltar a la siguiente ronda perdida

estado: entregado
candado: -
rama: claude/equipo-dev/130-saltar-a-la-siguiente-ronda-perdida
tipo: funcionalidad
epica: revision-de-rondas
area: frontend
prioridad: 3
fuente: ALCANCE.md F24
archivos: frontend/src/navegacionRondas.js (siguientePerdida, pideSiguientePerdida), frontend/src/navegacionRondas.test.js, frontend/src/pages/MatchDetail.jsx (DetallePartida: teclado y panel Rondas), frontend/e2e/humo.spec.js
turnos: po 20261113T1858Z-cxQ3TuB, arquitecto 20261113T1926Z-cq9nfTP, dev 20261113T2003Z-c3vr7mZ, revisor 20261113T2157Z-chbMW9r, qa 20261113T2223Z-c24t16L, release 20261113T2223Z-c24t16L

## PR

Titulo: `[equipo-dev][frontend] Saltar a la siguiente ronda perdida`

### Que cambia

En el detalle de partida, el panel Rondas suma el boton "Siguiente ronda perdida" y la tecla `p`: llevan a la proxima ronda que tu equipo perdio desde la elegida, dando la vuelta al final. Sirve para revisar solo lo que salio mal sin recorrer las rondas una por una.

### Por que esto y no otra cosa

Ficha 130 (ALCANCE.md F24, epica revision-de-rondas). Descartado: filtrar las pestañas a solo perdidas (esconde el contexto de la partida) y Shift+p para la anterior (fuera de alcance, ficha aparte si hace falta).

### Como se probo

- `check.sh` (con `verificar.sh`): VERDE cc63536fc, 1284 tests backend, 421 vitest, 114 e2e (QA); se repite sobre el commit final antes del merge.
- vitest `navegacionRondas.test.js`: `describe('siguientePerdida')` (6: salto, vuelta al final, nulo no cuenta, sin perdidas null, unica perdida la misma, fuera de rango) y `describe('pideSiguientePerdida')` (4: p/P, exclusiones, otra tecla, tabla con scroll).
- e2e `humo.spec.js`: `el detalle salta a la siguiente ronda perdida` (boton y tecla contra la regla sobre `/api/matches/<id>/`, hint) y `sin rondas perdidas el boton de la siguiente perdida queda deshabilitado`.
- QA en la app (Playwright sobre `seed_demo`): 609 saltos (boton, `p`, Enter con foco) desde cada ronda de las 29 partidas, todos correctos; bordes con respuesta interceptada (unica perdida, `my_team_won` nulo, una sola ronda); mutaciones 3 de 3 caen; chunk inicial +0.17 %.
- OMC: diseno plan=— · revisión=— · verificación=—
- OMC: implementacion plan=— · revisión=3 hallazgos LOW (2 arreglados) · verificación=—
- OMC: revision plan=— · revisión=4 hallazgos (0 arreglados: 2 decisiones del diseno, 1 descartado, 1 duplicado) · verificación=—
- OMC: qa plan=— · revisión=— · verificación=PASS
- Skills del repo: testing-strategy, ux-copy (diseno e implementacion); accessibility-review (QA: 0 Critical, 0 Major; contraste 12.92:1).

### Riesgos y lo que no entra

Solo frontend: sin migracion, `recompute`, parser ni POST. El salto, como las pestañas y las flechas, no actualiza `#ronda-N`. Con la elegida como unica perdida el boton queda habilitado y no mueve nada (decision del diseno). Fuera: anterior perdida, filtrar pestañas, la misma navegacion en Comparar.

### Como probarlo en 2 minutos

```powershell
cd backend; python manage.py seed_demo; python manage.py runserver
```
Abrir una partida en `http://127.0.0.1:8000/partidas/<id>`, elegir R1 y apretar "Siguiente ronda perdida": la pestaña elegida pasa a la proxima roja; repetir hasta que vuelva al principio. Con `p` igual. El hint del panel dice "P para la siguiente perdida".

### Para el humano

Nada que decidir. Aviso: si se quiere que la URL siga a la ronda elegida (`#ronda-N`), es una ficha aparte que cambia pestañas, flechas y salto juntos.

### Candidatos descubiertos

Ninguno.

## Que gana quien usa la app

Un boton "Siguiente ronda perdida" (y la tecla `p`) en el detalle de partida lleva a la proxima ronda que tu equipo perdio desde la elegida, dando la vuelta al final.

## Criterios de aceptacion

- [x] Logica pura `siguientePerdida` en `navegacionRondas.js`: vuelta al final, `my_team_won` nulo no cuenta, `null` sin perdidas, la misma si es la unica. vitest.
- [x] La tecla `p` con las exclusiones de `pasoDeTecla`. vitest.
- [x] Boton con nombre accesible en el panel Rondas, deshabilitado sin perdidas; el salto se comporta como cambiar de ronda a mano. e2e sobre `seed_demo`, consola limpia.
- [x] El atajo figura en el hint y el `title`, con tildes.

## Diseno

(arquitecto 20261113T1926Z-cq9nfTP) `siguientePerdida(actual, rounds)` y `pideSiguientePerdida(evento)` en `navegacionRondas.js`, con las exclusiones comunes en `teclaLibre`; en `DetallePartida`, la `p` en el `useEffect` del teclado y un `btn small` antes de `.round-tabs`. Sin perdidas: `null` y boton deshabilitado. El salto solo hace `setSelected`, como las pestañas: no toca el hash.

## Implementacion

(dev 20261113T2003Z-c3vr7mZ) Diseno completo. Desvio: `CON_SCROLL` queda solo en `pasoDeTecla` (la `p` no desplaza nada; con el foco en el scoreboard no hacia nada), con test. Revision ciega: 3 LOW, 2 arreglados.

## Revision 2026-11-13 sobre 1b1b2bc

(revisor 20261113T2157Z-chbMW9r) Aprobar -> `revisado`. VERDE 1b1b2bcb5. Sin hallazgos que corregir: unica perdida con boton habilitado y ancla sin actualizar son decisiones del diseno; `isComposing` descartado (los campos ya quedan afuera). El detalle, en `git log`.

## QA 2026-11-13 sobre cc63536

(qa 20261113T2223Z-c24t16L) VERDE cc63536fc (1284 backend, 421 vitest, 114 e2e). En la app sembrada, 609 saltos correctos por boton, `p` y Enter; Shift+P y Alt+p no mueven; URL igual; consola limpia. Bordes interceptados (unica perdida, nulo, una ronda) y base vacia sin errores; `curl` de bordes 200/404 esperados. Chunk inicial +0.17 %. Accesibilidad: rol y nombre, Tab, foco visible, contraste 12.92:1. Mutaciones 3 de 3 caen. `omc-verifier`: PASS. Veredicto `aprobado`; el detalle con comandos, en `git log` (commit "Prueba: 130").

Skills del repo: accessibility-review (0 Critical, 0 Major), testing-strategy (mutaciones 3 de 3).
OMC: plan=— · revisión=— · verificación=PASS

## Para el humano

- (revisor 2026-11-13) Ancla `#ronda-N`: hoy ni las pestañas, ni las flechas, ni este salto la actualizan; si se quiere que la URL siga a la ronda elegida, es una ficha aparte que cambia los tres caminos juntos. Informativo.
